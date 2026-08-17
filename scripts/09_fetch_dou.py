# -*- coding: utf-8 -*-
"""
Varredura do Diario Oficial da Uniao em busca de atos do MEC relevantes para o setor.

O QUE ESTE SCRIPT FAZ E O QUE ELE DELIBERADAMENTE NAO FAZ
---------------------------------------------------------
Ele COLETA e TRIA candidatos. Ele NAO escreve em `config/regulatorio.json`.

O motivo esta na regra do modulo Ambiente Regulatorio: nada entra no feed sem fonte
primaria E sem alguem ter decidido que aquilo e relevante. A busca do DOU por
"educacao a distancia" nos ultimos 5 anos devolve **13.136 resultados**; "curso de
medicina", 6.935. A esmagadora maioria e ato de uma instituicao especifica — autorizar
o curso X na faculdade Y, recredenciar o campus Z. Despejar isso no feed nao daria ao
usuario um feed, daria um deposito, e destruiria justamente o que o modulo tem de util.

Por isso a saida e uma LISTA DE CANDIDATOS para curadoria humana:

    data_processed/dou_candidatos.jsonl   bruto, append-only, deduplicado por URL
    outputs/dou_candidatos.md             relatorio para leitura e decisao

Depois de escolher, as entradas aprovadas vao a mao para `config/regulatorio.json` e
passam pelo gate do `08_build_regulatorio.py`.

COMO A TRIAGEM FUNCIONA
-----------------------
Quatro cortes, nesta ordem (os dois ultimos so apareceram depois de rodar de verdade):

1. **Orgao subordinado.** O resultado da busca diz qual orgao publicou. Ato que interessa
   ao setor privado sai do Gabinete do Ministro, da SERES, do CNE, do Inep ou do FNDE.
   Resolucao do CONSUP do IF de Mato Grosso, nao. Este corte sozinho elimina a maior
   parte do ruido, e e por isso que ele vem primeiro.

2. **Tipo e alcance do ato.** Lei, decreto, portaria normativa e resolucao passam.
   "Portaria" simples so passa se a ementa nao parecer ato de uma IES individual
   (o padrao "autoriza o funcionamento do curso ... da Faculdade ..." e o descarte).

ACESSO
------
`WebFetch` no in.gov.br derruba a conexao ("socket hang up"), mas Playwright com
`channel="chrome"` abre normalmente, headless. A paginacao NAO e por parametro de URL —
`&currentPage=2` devolve a mesma pagina 1 —, e sim pelo botao `#rightArrow`, que e JS.

ARMADILHAS DE BUSCA JA PAGAS (ver docs/00_HANDOFF.md)
-----------------------------------------------------
- Ato do Inep sai como "PORTARIA Nº 413", **sem a sigla no titulo**. Nao procure pela sigla.
- **Zero resultado nao prova ausencia.** A Portaria MEC nº 129/2026 existe, esta no
  comunicado oficial do MEC e nao aparece em nenhuma variacao de busca.

USO
---
    python scripts/09_fetch_dou.py                      # 5 anos, todos os termos
    python scripts/09_fetch_dou.py --anos 2             # janela menor
    python scripts/09_fetch_dou.py --termo Fies         # so um termo
    python scripts/09_fetch_dou.py --max-paginas 3      # limita a varredura
"""
import argparse
import json
import os
import re
import sys
import unicodedata
import urllib.parse
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRUTO = os.path.join(ROOT, "data_processed", "dou_candidatos.jsonl")
RELATORIO = os.path.join(ROOT, "outputs", "dou_candidatos.md")

BUSCA = "https://www.in.gov.br/consulta/-/buscar/dou"

# Termos de busca por tema. Sao os assuntos que o modulo cobre; acrescentar tema novo aqui
# e o caminho para ampliar a varredura sem mexer no resto.
TERMOS = {
    "ead": ['"educação a distância"', '"polo de educação a distância"', '"oferta de cursos superiores"'],
    "medicina": ['"curso de medicina"', '"chamamento público" medicina', '"Enamed"'],
    "fies": ['"Fies"', '"Fundo de Financiamento Estudantil"', '"Fies Social"'],
    "regulacao": ['"credenciamento" "educação superior"', '"supervisão" "educação superior"',
                  '"avaliação" "educação superior"', '"Prouni"'],
}

# Corte 1: orgaos cujo ato tem alcance setorial. O resto do MEC (IFs, universidades
# federais, seus conselhos) publica ato de administracao propria, que nao e regulacao.
ORGAOS_SETORIAIS = [
    "gabinete do ministro",
    "secretaria de regulacao e supervisao da educacao superior",
    "secretaria de educacao superior",
    "conselho nacional de educacao",
    "instituto nacional de estudos e pesquisas educacionais",
    "fundo nacional de desenvolvimento da educacao",
]

# Corte 2: tipos de ato que sempre passam — sao normativos por natureza.
TIPOS_NORMATIVOS = re.compile(
    r"^\s*(lei|lei\s+complementar|decreto|medida\s+provisoria|portaria\s+normativa|resolucao)\b",
    re.I)
# "Portaria" simples e ambigua: pode ser normativa ou ato de uma IES. Passa no tipo...
TIPO_PORTARIA = re.compile(r"^\s*portaria\b", re.I)
# ...e cai fora se a ementa tiver cheiro de ato individual.
ATO_INDIVIDUAL = re.compile(
    r"(autoriza|reconhece|renova o reconhecimento|credencia|recredencia|descredencia)\b"
    r".{0,120}\b(curso|campus|polo|faculdade|centro universitario|universidade|instituto)\b",
    re.I)

# Corte 3: ruido administrativo. Sao atos normativos de verdade — o tipo esta certo, o
# orgao esta certo —, mas tratam da casa do proprio orgao, nao do setor regulado. Sem este
# corte a lista de Fies vinha com 63 candidatos, dos quais a maioria era empenho
# orcamentario do FNDE, regimento interno e medida de supervisao sobre UMA mantenedora.
# Cada padrao aqui saiu de um falso positivo observado, nao de suposicao.
RUIDO_ADMIN = re.compile(
    r"("
    r"orcamentari|empenho|dotacao|credito (suplementar|especial)|"       # orcamento
    r"regimento interno|estrutura (organizacional|regimental)|"          # organizacao da casa
    r"divisao de |coordenacao-geral de |compete a |"
    r"designa|exonera|nomeia|substituto|"                                # pessoal
    r"nota tecnica n|mantenedora;"                                       # supervisao de uma IES
    r")", re.I)


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", str(s or ""))
                   if unicodedata.category(c) != "Mn").lower().strip()


def url_busca(termo, ini, fim):
    q = urllib.parse.urlencode({
        "q": termo, "s": "do1", "exactDate": "personalizado",
        "publishFrom": ini.strftime("%d-%m-%Y"), "publishTo": fim.strftime("%d-%m-%Y"),
        "orgPrin": "Ministério da Educação",
    })
    return f"{BUSCA}?{q}"


# JS de extracao. Roda dentro da pagina porque cada resultado e um bloco solto: o titulo
# esta num <a>, e orgao/edicao/data/pagina vem nos irmaos anteriores. Subir a arvore no
# proprio DOM e mais estavel do que tentar fatiar o innerText da pagina inteira.
JS_EXTRAI = r"""
() => {
  const out = [];
  document.querySelectorAll('a.title-marker, h5 a').forEach(a => {
    const titulo = (a.innerText || '').trim();
    if (!titulo) return;
    let bloco = a.closest('div');
    for (let i = 0; i < 4 && bloco && !/Seção|Edição/.test(bloco.innerText || ''); i++) {
      bloco = bloco.parentElement;
    }
    const txt = (bloco ? bloco.innerText : '') || '';
    const linhas = txt.split('\n').map(s => s.trim()).filter(Boolean);
    const iTit = linhas.findIndex(l => l === titulo);
    // orgao subordinado = ultima linha antes de "Edição Nº ..." que nao seja o titulo
    const iEd = linhas.findIndex(l => /^Edição Nº/.test(l));
    const orgaos = iEd > 0 ? linhas.slice(0, iEd).filter(l => !/^Seção/.test(l)) : [];
    const ed = iEd >= 0 ? linhas[iEd] : '';
    const ementa = iTit >= 0 ? linhas.slice(iTit + 1).join(' ') : '';
    out.push({
      titulo,
      url: a.getAttribute('href') || '',
      orgao: orgaos.length ? orgaos[orgaos.length - 1] : '',
      orgao_raiz: orgaos.length ? orgaos[0] : '',
      edicao_linha: ed,
      ementa: ementa.slice(0, 600),
    });
  });
  return out;
}
"""

RE_EDICAO = re.compile(r"Edição Nº\s*([\d\-A-Za-z]+)\s*de\s*(\d{2}/\d{2}/\d{4})\s*-\s*Pág\.\s*(\d+)")


def normaliza(item, termo, tema):
    """Converte o item cru da pagina no registro que vai para o JSONL."""
    m = RE_EDICAO.search(item.get("edicao_linha", "") or "")
    edicao = pagina = data_iso = None
    if m:
        edicao, dbr, pagina = m.group(1), m.group(2), m.group(3)
        d, mth, y = dbr.split("/")
        data_iso = f"{y}-{mth}-{d}"
    url = item.get("url") or ""
    if url.startswith("/"):
        url = "https://www.in.gov.br" + url
    return {
        "titulo": item["titulo"], "url": url, "data": data_iso,
        "edicao": edicao, "pagina": pagina,
        "orgao": item.get("orgao", ""), "orgao_raiz": item.get("orgao_raiz", ""),
        "ementa": (item.get("ementa") or "").strip(),
        "termo": termo, "tema": tema,
    }


def setorial(reg):
    """Corte 1 — o ato veio de um orgao com alcance setorial?"""
    o = sem_acento(reg.get("orgao"))
    return any(x in o for x in ORGAOS_SETORIAIS)


def normativo(reg):
    """Corte 2 — o ato parece norma, e nao despacho sobre uma IES especifica?"""
    t = sem_acento(reg.get("titulo"))
    if TIPOS_NORMATIVOS.match(t):
        return True
    if TIPO_PORTARIA.match(t):
        return not ATO_INDIVIDUAL.search(sem_acento(reg.get("ementa")))
    return False


def administrativo(reg):
    """Corte 3 — o ato e sobre a casa do orgao, e nao sobre o setor regulado?"""
    return bool(RUIDO_ADMIN.search(sem_acento(reg.get("ementa"))))


# Corte 4: ato EM LOTE sobre IES individuais. Este e o mais importante dos quatro e o que
# so apareceu depois de rodar de verdade: a SERES publica portarias que sao tabelas —
# dezenas de cursos de dezenas de faculdades num ato so, com codigo da IES, CNPJ da
# mantenedora e aditamento de vagas. O titulo e "PORTARIA SERES/MEC nº 900" e nao denuncia
# nada; a ementa entrega, porque vem cheia de CNPJ e de "(codigo)".
#
# Sem este corte a SERES sozinha respondia por 106 dos 206 candidatos — mais da metade da
# lista de curadoria seria ato individual travestido de norma.
LOTE_IES = re.compile(
    r"("
    r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}|"        # CNPJ da mantenedora
    r"mantenedora \(cnpj\)|ies \(codigo\)|"
    r"registro e-mec|vagas anuais|aditamento"
    r")", re.I)


def lote_de_ies(reg):
    """Corte 4 — o ato e uma tabela de IES/cursos individuais?"""
    return bool(LOTE_IES.search(sem_acento(reg.get("ementa"))))


def le_bruto():
    if not os.path.exists(BRUTO):
        return {}
    out = {}
    with open(BRUTO, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                r = json.loads(ln)
                out[r["url"]] = r
            except json.JSONDecodeError:
                continue
    return out


def grava_bruto(novos):
    os.makedirs(os.path.dirname(BRUTO), exist_ok=True)
    with open(BRUTO, "a", encoding="utf-8") as f:
        for r in novos:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def varre(pg, termo, tema, ini, fim, max_paginas):
    """Roda uma busca e pagina pelo botao Next, que e o unico jeito: `currentPage` na
    URL nao funciona — devolve sempre a primeira pagina."""
    achados, vistos_pag = [], set()
    pg.goto(url_busca(termo, ini, fim), wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(4500)

    for p in range(max_paginas):
        itens = pg.evaluate(JS_EXTRAI)
        if not itens:
            break
        # a pagina repetiu? entao o Next nao avancou e a varredura acabou
        chave = itens[0].get("url")
        if chave in vistos_pag:
            break
        vistos_pag.add(chave)
        achados.extend(normaliza(x, termo, tema) for x in itens)

        try:
            seta = pg.query_selector("#rightArrow")
            if not seta or not seta.is_enabled():
                break
            seta.click()
            pg.wait_for_timeout(3500)
        except Exception:
            break
    return achados


def relatorio(cands, ini, fim):
    por_tema = {}
    for c in cands:
        por_tema.setdefault(c["tema"], []).append(c)
    linhas = [
        "# Candidatos do DOU para o Ambiente Regulatório",
        "",
        f"Varredura de **{ini:%d/%m/%Y}** a **{fim:%d/%m/%Y}**, Seção 1, órgão principal "
        "*Ministério da Educação*.",
        "",
        "> Esta lista é **matéria-prima para curadoria**, não base publicada. Nada aqui entra "
        "> no dashboard antes de alguém decidir que é relevante e escrever a entrada em "
        "> `config/regulatorio.json`, que passa pelo gate do `08_build_regulatorio.py`.",
        "",
        f"**{len(cands)} candidatos** sobraram depois dos dois cortes (órgão setorial + ato "
        "normativo, sem ruído administrativo).",
        "",
    ]
    for tema in sorted(por_tema):
        itens = sorted(por_tema[tema], key=lambda x: (x["data"] or ""), reverse=True)
        linhas += [f"## {tema} — {len(itens)} candidatos", ""]
        for c in itens:
            d = c["data"] or "sem data"
            linhas.append(f"- **{d}** · [{c['titulo']}]({c['url']})  ")
            linhas.append(f"  {c['orgao']} · Ed. {c['edicao']} · p. {c['pagina']}  ")
            if c["ementa"]:
                linhas.append(f"  _{c['ementa'][:240]}_")
            linhas.append("")
    os.makedirs(os.path.dirname(RELATORIO), exist_ok=True)
    with open(RELATORIO, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--anos", type=float, default=5, help="janela em anos (padrão 5)")
    ap.add_argument("--termo", help="roda só os termos de um tema (ead, medicina, fies, regulacao)")
    ap.add_argument("--max-paginas", type=int, default=8,
                    help="páginas por termo; cada página traz 20 resultados")
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright não instalado. Rode: python -m playwright install chromium")
        return 1

    fim = date.today()
    ini = fim - timedelta(days=int(args.anos * 365.25))
    temas = {args.termo: TERMOS[args.termo]} if args.termo else TERMOS
    if args.termo and args.termo not in TERMOS:
        print(f"tema '{args.termo}' não existe. Opções: {', '.join(TERMOS)}")
        return 1

    ja = le_bruto()
    brutos, novos = [], []
    with sync_playwright() as p:
        # channel="chrome": o Chromium do Playwright é barrado pelo in.gov.br
        b = p.chromium.launch(channel="chrome", headless=True)
        pg = b.new_page(viewport={"width": 1400, "height": 1200})
        for tema, lista in temas.items():
            for termo in lista:
                print(f"  buscando [{tema}] {termo} …", flush=True)
                try:
                    achados = varre(pg, termo, tema, ini, fim, args.max_paginas)
                except Exception as e:
                    print(f"    falhou: {type(e).__name__} {str(e)[:110]}")
                    continue
                print(f"    {len(achados)} resultados brutos")
                brutos.extend(achados)
        b.close()

    # dedup por URL, mantendo o primeiro tema que achou o ato
    unicos = {}
    for r in brutos:
        if r["url"] and r["url"] not in unicos:
            unicos[r["url"]] = r

    cands = [r for r in unicos.values()
             if setorial(r) and normativo(r)
             and not administrativo(r) and not lote_de_ies(r)]
    novos = [r for r in cands if r["url"] not in ja]
    grava_bruto(novos)
    relatorio(cands, ini, fim)

    print()
    print(f"brutos coletados : {len(brutos)}")
    print(f"únicos           : {len(unicos)}")
    print(f"passaram na triagem: {len(cands)}  (órgão setorial · normativo · sem ruído · sem lote de IES)")
    print(f"novos desde a última rodada: {len(novos)}")
    print(f"→ {RELATORIO}")
    print()
    print("Nada foi escrito em config/regulatorio.json — a curadoria é manual, por decisão.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
