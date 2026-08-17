"""
Base compartilhada do tracking de mensalidades.

Separado do coletor porque a parte que muda toda semana e o adaptador de cada site;
leitura de config, parsing de preco e armazenamento do historico nao mudam.

O historico e um JSONL append-only (`data_processed/mensalidades.jsonl`): uma linha por
coleta de (data, IES, modalidade, curso, unidade). Isso mantem o dado bruto por unidade
— util para conferir uma media estranha — e permite reprocessar o agregado sem recoletar.
"""
import json
import os
import re
import unicodedata
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CFG = os.path.join(ROOT, "config")
HIST = os.path.join(ROOT, "data_processed", "mensalidades.jsonl")
WEB = os.path.join(ROOT, "dashboard", "data", "mensalidades.json")


# --------------------------------------------------------------------- config
def _linhas_csv(caminho):
    with open(caminho, encoding="utf-8") as f:
        cab = None
        for ln in f:
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            campos = ln.split(";")
            if cab is None:
                cab = campos
                continue
            yield dict(zip(cab, campos))


def cursos_alvo():
    """{modalidade: [{curso, sinonimos:[...]}]}"""
    out = {}
    for r in _linhas_csv(os.path.join(CFG, "mensalidades_cursos.csv")):
        out.setdefault(r["MODALIDADE"], []).append({
            "curso": r["CURSO"],
            "sinonimos": [s.strip() for s in r["SINONIMOS"].split("|") if s.strip()],
        })
    return out


def ies_alvo(engine=None, incluir_inativos=False):
    out = []
    for r in _linhas_csv(os.path.join(CFG, "mensalidades_ies.csv")):
        if not incluir_inativos and r.get("ATIVO", "1") != "1":
            continue
        if engine and r["ENGINE"] != engine:
            continue
        out.append(r)
    return out


# Cidades do recorte de EAD, conforme pedido: uma capital por regiao relevante.
CIDADES_EAD = [("SP", "São Paulo"), ("RJ", "Rio de Janeiro"), ("MG", "Belo Horizonte"),
               ("RS", "Porto Alegre"), ("BA", "Salvador"), ("CE", "Fortaleza"),
               ("AM", "Manaus")]

# Minimo de polos para que uma linha de EAD seja publicada como media de pracas.
# No EAD o preco varia por polo, entao o numero da tela so significa alguma coisa se vier
# de varias pracas: a Estacio entra com 64 polos de capital. Uma linha de um polo so nao e
# media de nada — e um ponto —, e publicada ao lado da Estacio ela convida a uma comparacao
# que o dado nao sustenta (o laco de polos da Anima traz 1 capital quando deveria varrer as
# 7 de CIDADES_EAD). A regra e por cobertura, nao por IES: no dia em que o laco for
# consertado as linhas voltam sozinhas, sem ninguem lembrar de desfazer excecao nenhuma.
MIN_POLOS_EAD = 3


# ---------------------------------------------------------------------- texto
def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", str(s))
                   if unicodedata.category(c) != "Mn").lower().strip()


def parecido(a, b):
    """Compara nome de curso ignorando acento, caixa e ruido de sufixo."""
    a, b = sem_acento(a), sem_acento(b)
    return a == b or a.startswith(b) or b.startswith(a)


# Preco brasileiro: R$ 1.234,56 — o ponto e milhar e a virgula e decimal.
_RE_PRECO = re.compile(r"R\$\s*([\d.]{1,9},\d{2}|\d{1,6})")


def precos_no_texto(txt):
    """Todos os valores monetarios de um trecho, em float."""
    out = []
    for m in _RE_PRECO.finditer(txt or ""):
        bruto = m.group(1).replace(".", "").replace(",", ".")
        try:
            v = float(bruto)
        except ValueError:
            continue
        # abaixo de 30 costuma ser parcela de material ou taxa; acima de 50 mil, ruido
        if 30 <= v <= 50000:
            out.append(v)
    return out


def menor_preco(txt):
    """O MENOR valor do trecho.

    Regra do usuario: em "de R$ 100 por R$ 79", vale o 79. Pegar o menor resolve o caso
    geral, inclusive quando o site inverte a ordem ou usa "a partir de".
    """
    p = precos_no_texto(txt)
    return min(p) if p else None


# ------------------------------------------------------------------ historico
def registra(linhas):
    """Acrescenta observacoes ao historico. Cada linha e um dict com:
    data, grupo, ies, modalidade, curso, unidade, turno, preco, url."""
    if not linhas:
        return 0
    os.makedirs(os.path.dirname(HIST), exist_ok=True)
    with open(HIST, "a", encoding="utf-8") as f:
        for l in linhas:
            f.write(json.dumps(l, ensure_ascii=False) + "\n")
    return len(linhas)


def le_historico():
    if not os.path.exists(HIST):
        return []
    out = []
    with open(HIST, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except json.JSONDecodeError:
                    continue
    return out


def exporta_web():
    """Agrega o historico bruto no JSON que o dashboard consome.

    A mensalidade publicada e a MEDIA SIMPLES do menor preco de cada unidade/polo, como
    pedido. min/max e o numero de ofertas viajam junto: uma media de 3 unidades com
    dispersao de 40% merece leitura diferente de uma media de 30 unidades homogeneas.
    """
    hist = le_historico()
    # dedupe: recoletar o mesmo dia sobrescreve a observacao anterior daquela unidade,
    # senao rodar o script duas vezes puxaria a media para a unidade repetida
    unico = {}
    for r in hist:
        if r.get("preco") is None:
            continue
        unico[(r["data"], r["ies"], r["modalidade"], r["curso"], r.get("unidade", ""))] = r

    agg = {}
    for r in unico.values():
        k = (r["data"], r["grupo"], r["ies"], r["modalidade"], r["curso"])
        agg.setdefault(k, []).append(float(r["preco"]))

    # De onde veio o preco daquela linha. Nao e detalhe de metadado: "media de 64 polos" e
    # "a partir de nacional" sao numeros de natureza diferente, e sem essa marca a tela
    # convida a comparar a dispersao de um com a do outro. Cogna e Uniasselvi so publicam
    # o piso nacional; Estacio e Anima descem ate a unidade.
    def base_do_preco(rs):
        return "nacional" if all("nacional" in (r.get("unidade") or "") for r in rs) else "unidades"

    linhas, fora_ead = [], []
    for (dt, grupo, ies, mod, curso), vs in sorted(agg.items()):
        obs = [r for r in unico.values()
               if (r["data"], r["grupo"], r["ies"], r["modalidade"], r["curso"])
               == (dt, grupo, ies, mod, curso)]
        l = {
            "data": dt, "grupo": grupo, "ies": ies, "modalidade": mod, "curso": curso,
            "preco": round(sum(vs) / len(vs), 2), "n_ofertas": len(vs),
            "min": round(min(vs), 2), "max": round(max(vs), 2),
            "base": base_do_preco(obs),
        }
        # Ver MIN_POLOS_EAD: EAD por unidade com um punhado de polos nao e media de pracas.
        # O piso nacional ("a partir de") nao entra nesta regra — ele nunca prometeu ser
        # media de pracas, e a tela ja o marca com asterisco por outro motivo.
        if mod == "ead" and l["base"] == "unidades" and l["n_ofertas"] < MIN_POLOS_EAD:
            fora_ead.append(l)
        else:
            linhas.append(l)

    # ⚠️ Nenhuma chave de resumo pode se chamar como uma COLUNA: o resumo e escrito depois
    # da expansao colunar, entao o nome repetido sobrescreve a coluna inteira e o payload
    # sai desalinhado. Ja aconteceu duas vezes aqui — "ies" (a coluna virava a lista de IES
    # distintas, jogando cada linha para a instituicao errada) e a contagem de ofertas
    # chamada de "n". A contagem de ofertas virou "n_ofertas" e "n" ficou com o numero de
    # linhas, que e a convencao dos demais cubos do projeto e o que `linhas()` do
    # dashboard espera. O assert abaixo impede a terceira vez.
    cols = ["data", "grupo", "ies", "modalidade", "curso", "preco", "n_ofertas", "min", "max",
            "base"]
    obj = {
        "atualizado_em": max([l["data"] for l in linhas], default=None),
        "fonte": "sites das próprias instituições",
        "n": len(linhas), "cols": cols,
        **{c: [l[c] for l in linhas] for c in cols},
        "datas": sorted({l["data"] for l in linhas}),
        "ies_lista": sorted({l["ies"] for l in linhas}),
        "grupos_lista": sorted({l["grupo"] for l in linhas}),
        "observacoes_brutas": len(hist),
        # Quem ficou de fora do EAD por cobertura de polos, para a tela poder dizer o nome
        # em vez de simplesmente omitir a linha. Omissao silenciosa e pior que exclusao
        # declarada: o leitor conclui que a IES nao oferta EAD.
        "ead_min_polos": MIN_POLOS_EAD,
        "ead_fora": [
            {"ies": i, "grupo": g, "cursos": sum(1 for l in fora_ead
                                                 if (l["ies"], l["grupo"]) == (i, g)),
             "polos": max(l["n_ofertas"] for l in fora_ead
                          if (l["ies"], l["grupo"]) == (i, g))}
            for i, g in sorted({(l["ies"], l["grupo"]) for l in fora_ead})
        ],
    }
    assert all(len(obj[c]) == len(linhas) for c in cols), \
        "chave de resumo colidiu com nome de coluna e sobrescreveu a coluna"
    os.makedirs(os.path.dirname(WEB), exist_ok=True)
    with open(WEB, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
    return obj


def hoje():
    return date.today().isoformat()
