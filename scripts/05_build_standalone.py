"""
Etapa 5 do pipeline: gera um dashboard de ARQUIVO UNICO.

Junta HTML + CSS + ECharts + os modulos JS + os dados num unico .html autocontido,
que abre por duplo clique, funciona offline e pode ser enviado por e-mail ou publicado.

O que entra:
  - todos os cubos historicos (10 anos) -> as visoes de evolucao ficam completas
  - o detalhe por IES apenas do ano mais recente -> mantem o arquivo em ~5 MB
    (os 10 anos de detalhe somariam +8 MB, sem ganho proporcional)

Os modulos ES sao concatenados em escopo unico: as diretivas `import`/`export` sao
removidas, o que funciona porque nao ha colisao de nomes entre os arquivos. A ordem
de concatenacao respeita a dependencia (dados -> ui -> views -> comparacao -> app).

Uso:
  python scripts/05_build_standalone.py
  python scripts/05_build_standalone.py --todos-os-anos   # embute o detalhe de todos
"""
import argparse
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "dashboard")
DATA = os.path.join(WEB, "data")
SAIDA = os.path.join(ROOT, "outputs", "dashboard_standalone.html")

# ordem de dependencia dos modulos
# i18n vem primeiro: dados.js depende dele para formatar numero no locale certo
MODULOS = ["i18n.js", "en.js", "dados.js", "ui.js", "xlsx.js", "views.js", "grupos.js",
           "precos.js", "mensalidades.js", "regulatorio.js", "app.js"]

# arquivos de dados sempre embutidos (cubos historicos + dimensoes + precos + mensalidades).
# ⚠️ Estas duas listas sao explicitas: bloco novo que nao entre aqui simplesmente nao existe
# na versao offline nem no artifact, e o app quebra no import.
CORE = ["meta.json", "dim.json", "c_ies_mod.json", "c_cine_mod.json",
        "c_mun_mod.json", "c_ies_ano.json", "precos.json", "mensalidades.json",
        "regulatorio.json", "emec.json", "dou_diario.json"]


def desmodulariza(codigo):
    """Remove import/export para que o modulo funcione concatenado em escopo unico."""
    # remove blocos `import { ... } from '...';` (inclusive multilinha) e `import x from`
    codigo = re.sub(r"^\s*import\s+[^;]*?from\s*['\"][^'\"]+['\"]\s*;\s*$",
                    "", codigo, flags=re.M | re.S)
    # remove import só por efeito colateral: `import './en.js';` (sem clausula `from`)
    codigo = re.sub(r"^\s*import\s*['\"][^'\"]+['\"]\s*;\s*$", "", codigo, flags=re.M)
    # remove a palavra-chave export mantendo a declaracao
    codigo = re.sub(r"^\s*export\s+(?=(const|let|var|function|async|class)\b)",
                    "", codigo, flags=re.M)
    # remove `export { ... };` isolados
    codigo = re.sub(r"^\s*export\s*\{[^}]*\}\s*;?\s*$", "", codigo, flags=re.M)
    return codigo


# Declaracao de topo de cada modulo. Serve para o checa_colisoes(): num escopo unico,
# dois `const x` no arquivo final sao SyntaxError e o dashboard nao inicia.
_RE_TOPO = re.compile(r"^(?:export\s+)?(?:async\s+)?(?:function|const|let|var|class)\s+"
                      r"([A-Za-z_$][\w$]*)", re.M)
_RE_ALIAS = re.compile(r"import\s*\{([^}]*)\}")


def checa_colisoes(fontes):
    """Falha cedo em nome de topo repetido e em import com alias.

    Concatenar os modulos num escopo unico tem dois efeitos que so aparecem na versao
    standalone/artifact — a servida por modulos ES continua funcionando, o que faz o
    problema passar despercebido:
      * dois modulos declarando o mesmo nome viram `SyntaxError: already been declared`
        e a pagina fica presa no "Carregando...". Aconteceu com `dataLegivel` e `serie`,
        que precos.js e mensalidades.js declaravam cada um por sua conta;
      * `import { n as fmtN }` perde o apelido, porque nao ha mais import: sobra uma
        referencia a um `fmtN` que nao existe.
    """
    dono, problemas = {}, []
    for nome_mod, codigo in fontes.items():
        for ident in sorted(set(_RE_TOPO.findall(codigo))):
            if ident in dono:
                problemas.append(f"nome '{ident}' declarado em {dono[ident]} e {nome_mod}")
            else:
                dono[ident] = nome_mod
        for m in _RE_ALIAS.finditer(codigo):
            for parte in m.group(1).split(","):
                if " as " in parte:
                    problemas.append(f"{nome_mod}: import com alias ({parte.strip()})")
    if problemas:
        print("Colisões que quebrariam a versão de arquivo único:")
        for p in problemas:
            print("  -", p)
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--todos-os-anos", action="store_true",
                    help="embute o detalhe por IES de todos os anos (arquivo bem maior)")
    ap.add_argument("--artifact", action="store_true",
                    help="emite fragmento sem <!doctype>/<html>/<head>/<body>, para publicar como Artifact")
    args = ap.parse_args()
    saida = (os.path.join(ROOT, "outputs", "dashboard_artifact.html")
             if args.artifact else SAIDA)

    if not os.path.exists(os.path.join(DATA, "meta.json")):
        print("Dados nao gerados. Rode scripts/04_export_web.py antes.")
        sys.exit(1)

    meta = json.load(open(os.path.join(DATA, "meta.json"), encoding="utf-8"))
    anos = meta["anos"]
    ano_det = meta["ano_atual"]
    anos_detalhe = anos if args.todos_os_anos else [ano_det]

    # ------------------------------------------------------------- dados
    embed, tam = {}, {}
    for nome in CORE:
        p = os.path.join(DATA, nome)
        # precos.json e mensalidades.json dependem de coleta que pode nao ter rodado nesta
        # copia; os dois blocos avisam na tela em vez de quebrar, entao faltar aqui nao
        # pode derrubar o build. Cubo do Censo faltando, sim — dai o erro explicito.
        if not os.path.exists(p):
            if nome in ("precos.json", "mensalidades.json", "regulatorio.json"):
                print(f"  [aviso] {nome} não existe; o bloco vai avisar na tela")
                continue
            raise SystemExit(f"{nome} não encontrado — rode scripts/04_export_web.py")
        embed[f"data/{nome}"] = json.load(open(p, encoding="utf-8"))
        tam[nome] = os.path.getsize(p) / 1024

    geo = os.path.join(DATA, "geo", "uf.geojson")
    if os.path.exists(geo):
        embed["data/geo/uf.geojson"] = json.load(open(geo, encoding="utf-8"))
        tam["uf.geojson"] = os.path.getsize(geo) / 1024

    for a in anos_detalhe:
        for suf in ("ies_cine", "ies_mun"):
            p = os.path.join(DATA, "ano", f"{a}_{suf}.json")
            if os.path.exists(p):
                embed[f"data/ano/{a}_{suf}.json"] = json.load(open(p, encoding="utf-8"))
                tam[f"{a}_{suf}"] = os.path.getsize(p) / 1024

    # ------------------------------------------------------------- codigo
    css = open(os.path.join(WEB, "css", "app.css"), encoding="utf-8").read()
    echarts = open(os.path.join(WEB, "vendor", "echarts.min.js"), encoding="utf-8").read()
    fontes = {m: open(os.path.join(WEB, "js", m), encoding="utf-8").read() for m in MODULOS}
    checa_colisoes(fontes)
    js = "\n\n".join(
        f"/* ==================== {m} ==================== */\n" + desmodulariza(fontes[m])
        for m in MODULOS
    )

    html = open(os.path.join(WEB, "index.html"), encoding="utf-8").read()
    # troca as tags externas pelos blocos embutidos
    html = html.replace('<link rel="stylesheet" href="css/app.css">',
                        f"<style>\n{css}\n</style>")
    html = html.replace('<script src="vendor/echarts.min.js"></script>', "")
    html = html.replace('<script type="module" src="js/app.js"></script>', "")

    dados_js = json.dumps(embed, ensure_ascii=False, separators=(",", ":"))
    faltando = [a for a in anos if a not in anos_detalhe]
    aviso = (f"\n<!-- detalhe por IES embutido apenas para {ano_det}; "
             f"anos sem detalhe: {faltando} -->") if faltando else ""

    # os scripts vao no fim: o bloco de dados e grande e o titulo precisa ficar
    # nos primeiros KB do arquivo para ser detectado na publicacao
    bloco = f"""{aviso}
<script>window.__EMBED = {dados_js};</script>
<script>{echarts}</script>
<script>
{js}
</script>"""

    if args.artifact:
        # o publicador envolve o conteudo em <!doctype><head></head><body>,
        # entao aqui sai apenas o miolo: title, style, conteudo e scripts.
        titulo = re.search(r"<title>(.*?)</title>", html, re.S)
        titulo = titulo.group(1).strip() if titulo else "Dashboard"
        corpo = re.search(r"<body>(.*?)</body>", html, re.S)
        corpo = corpo.group(1) if corpo else html
        estilo = re.search(r"<style>.*?</style>", html, re.S)
        estilo = estilo.group(0) if estilo else ""
        html = f"<title>{titulo}</title>\n{estilo}\n{corpo}\n{bloco}\n"
    else:
        html = html.replace("</body>", bloco + "\n</body>")

    os.makedirs(os.path.dirname(saida), exist_ok=True)
    with open(saida, "w", encoding="utf-8") as f:
        f.write(html)

    mb = os.path.getsize(saida) / 1024 / 1024
    print(f"Escrito: {saida}\n")
    print(f"{'COMPONENTE':<26} {'KB':>10}")
    print("-" * 38)
    for k, v in tam.items():
        print(f"{k:<26} {v:>10,.0f}")
    print(f"{'ECharts (vendor)':<26} {len(echarts)/1024:>10,.0f}")
    print(f"{'CSS + JS da aplicacao':<26} {(len(css)+len(js))/1024:>10,.0f}")
    print("-" * 38)
    print(f"{'ARQUIVO FINAL':<26} {mb*1024:>10,.0f}  ({mb:.1f} MB)")
    print(f"\nAnos com serie historica completa: {anos[0]}–{anos[-1]}")
    print(f"Anos com detalhe por IES        : {anos_detalhe}")
    if mb > 16:
        print("\n[AVISO] acima de 16 MB — grande demais para publicar como artifact.")


if __name__ == "__main__":
    main()
