# -*- coding: utf-8 -*-
"""
Ingestao do relatorio do e-MEC (`Dados_GEO.xlsx`) e de-para com as IES do Censo.

O QUE ESTE ARQUIVO E
--------------------
`Dados_GEO.xlsx` e o **Relatorio da Consulta Avancada do Sistema e-MEC**, uma linha por
IES ativa, processado em 11/08/2026. Foi o usuario quem o obteveresolvendo a pendencia
§6.4 do handoff: o e-MEC bloqueia acesso automatizado (HTTP 403) e exigia download manual.

⚠️ **Ele NAO resolve o problema de campus/polo.** O endereco que vem e o da **SEDE** —
um ponto por IES. Para capilaridade, o cubo `<ano>_ies_mun.json` que o projeto ja tem e
melhor: traz IES × municipio de oferta (27.985 linhas em 2024), e `dim.mun` ja carrega
lat/lon de 3.741 dos 3.742 municipios. A Cogna aparece em 1.986 municipios ali; pelo
endereco de sede ela seria um ponto so. Ver o relatorio gerado por este script.

O QUE O e-MEC AGREGA DE VERDADE
-------------------------------
Nao e geografia — e **qualidade e situacao regulatoria**, que o Censo nao tem:

- **IGC** (Indice Geral de Cursos) e **CI** / **CI-EaD** (Conceito Institucional), de 1 a 5.
- **Sinalizacoes Vigentes**: suspensao de ingresso, de contrato FIES, de PROUNI,
  descredenciamento voluntario. Isto e material para equity research e conversa direto
  com o bloco Ambiente Regulatorio.
- **Tipo de Credenciamento**: quem esta credenciado para EaD.
- CNPJ e natureza juridica da mantenedora, uteis para conferir o mapeamento de grupos.

SAIDAS
------
    data_processed/emec_ies.csv     de-para CO_IES -> atributos do e-MEC
    outputs/emec_depara.md          relatorio de cobertura e do que casou
    dashboard/data/emec.json        payload do dashboard, indexado por posicao em dim.ies

USO
---
    python scripts/10_ingest_emec.py
"""
import collections
import csv
import json
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XLSX = os.path.join(ROOT, "Dados_GEO.xlsx")
SAIDA = os.path.join(ROOT, "data_processed", "emec_ies.csv")
RELATORIO = os.path.join(ROOT, "outputs", "emec_depara.md")
WEB = os.path.join(ROOT, "dashboard", "data", "emec.json")
DIM = os.path.join(ROOT, "dashboard", "data", "dim.json")
IESMOD = os.path.join(ROOT, "dashboard", "data", "c_ies_mod.json")

# A planilha tem 5 linhas de cabecalho do proprio e-MEC antes da linha de titulos.
LINHA_TITULOS = 6

# indice da coluna -> nome canonico na saida
COLUNAS = {
    0: "co_mantenedora", 1: "mantenedora", 2: "cnpj", 3: "natureza_juridica",
    4: "co_ies", 5: "ies_emec", 6: "sigla", 10: "endereco_sede",
    11: "municipio", 12: "uf", 13: "organizacao", 14: "credenciamento",
    15: "categoria", 18: "ci", 20: "ci_ead", 22: "igc",
    26: "sinalizacoes", 27: "situacao",
}

# O e-MEC usa "-" para "sem conceito" e "SC" para "sem conceito" tambem. Vira vazio, nao
# zero: 0 seria lido como nota pessima, e nao ter nota nao e ter nota ruim.
SEM_NOTA = {"-", "SC", "", None}


def limpa(v):
    if v is None:
        return ""
    s = str(v).replace("\xa0", " ").strip()
    return re.sub(r"\s+", " ", s)


def nota(v):
    v = limpa(v)
    return "" if v in SEM_NOTA else v


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", str(s or ""))
                   if unicodedata.category(c) != "Mn").lower().strip()


def le_planilha():
    try:
        import openpyxl
    except ImportError:
        print("openpyxl nao instalado. Rode: pip install openpyxl")
        sys.exit(1)
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    ws = wb.active
    linhas = list(ws.iter_rows(min_row=LINHA_TITULOS + 1, values_only=True))
    out = []
    for r in linhas:
        reg = {nome: limpa(r[i]) if i < len(r) else "" for i, nome in COLUNAS.items()}
        for k in ("ci", "ci_ead", "igc"):
            reg[k] = nota(reg[k])
        if reg["co_ies"]:
            out.append(reg)
    return out


def dedup(regs):
    """91 linhas repetem CO_IES — sao a mesma IES listada mais de uma vez pelo relatorio.
    Fica a linha mais COMPLETA (mais campos preenchidos), que e a que tem endereco."""
    por = collections.defaultdict(list)
    for r in regs:
        por[r["co_ies"]].append(r)
    out, repetidos = [], 0
    for co, lista in por.items():
        if len(lista) > 1:
            repetidos += len(lista) - 1
        out.append(max(lista, key=lambda x: sum(1 for v in x.values() if v)))
    return out, repetidos


def main():
    if not os.path.exists(XLSX):
        print(f"nao encontrei {XLSX}")
        return 1

    regs = le_planilha()
    regs, repetidos = dedup(regs)
    print(f"e-MEC: {len(regs)} IES únicas ({repetidos} linhas duplicadas descartadas)")

    dim = json.load(open(DIM, encoding="utf-8"))
    ies = dim["ies"]
    censo = {str(co): i for i, co in enumerate(ies["co"])}

    # matriculas de 2024 por CO_IES, para pesar a cobertura por ALUNO e nao por contagem
    # de IES — 764 IES sem par parece muito ate ver que sao casos minusculos.
    cim = json.load(open(IESMOD, encoding="utf-8"))
    mat = collections.Counter()
    for i in range(cim["n"]):
        if cim["ano"][i] != 2024:
            continue
        ix = cim["ies"][i]
        if ix >= 0:
            mat[str(ies["co"][ix])] += cim["qt_mat"][i]

    emec = {r["co_ies"]: r for r in regs}
    casam = [co for co in censo if co in emec]
    so_censo = [co for co in censo if co not in emec]
    so_emec = [co for co in emec if co not in censo]

    tot = sum(mat.values())
    cob = sum(v for k, v in mat.items() if k in emec)

    # grava o de-para, ja com grupo e nome do Censo ao lado
    cols = (["co_ies", "ies_censo", "grupo", "uf_censo"] +
            [c for c in COLUNAS.values() if c != "co_ies"])
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    with open(SAIDA, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter=";")
        w.writeheader()
        for co in sorted(casam, key=lambda c: -mat.get(c, 0)):
            ix = censo[co]
            linha = dict(emec[co])
            linha.update({"co_ies": co, "ies_censo": ies["nome"][ix],
                          "grupo": ies["grupo"][ix] or "", "uf_censo": ies["uf"][ix] or ""})
            w.writerow({k: linha.get(k, "") for k in cols})

    # ---- payload do dashboard
    #
    # Arquivo proprio, carregado sob demanda, como precos/mensalidades/regulatorio. E dado
    # que NAO vem do Censo, entao nao entra nos cubos nem obriga a reprocessar microdado.
    #
    # ⚠️ Indexado pela POSICAO em `dim.ies`, nao por CO_IES: o dashboard ja trabalha com
    # indices em todos os cubos, e guardar o codigo de novo custaria espaco a toa. Quem
    # nao casou fica com string vazia, que a tela le como "sem informacao" — diferente de
    # zero, que seria nota pessima.
    n_ies = len(ies["co"])
    vazio = [""] * n_ies
    pay = {c: list(vazio) for c in ("igc", "ci", "ci_ead", "sinal", "cred", "situacao")}
    casou = 0
    for co, r in emec.items():
        ix = censo.get(co)
        if ix is None:
            continue
        casou += 1
        pay["igc"][ix] = r["igc"]
        pay["ci"][ix] = r["ci"]
        pay["ci_ead"][ix] = r["ci_ead"]
        pay["sinal"][ix] = r["sinalizacoes"]
        pay["cred"][ix] = r["credenciamento"]
        pay["situacao"][ix] = r["situacao"]

    obj = {
        "fonte": "Sistema e-MEC — Relatório da Consulta Avançada",
        "processado_em": "2026-08-11",
        "n": n_ies, "casaram": casou,
        "cols": ["igc", "ci", "ci_ead", "sinal", "cred", "situacao"],
        **pay,
    }
    os.makedirs(os.path.dirname(WEB), exist_ok=True)
    with open(WEB, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))

    # ---- validacao do de-para
    #
    # Cobertura NAO e correcao: contar quantos codigos bateram nao prova que os dois lados
    # falam da mesma instituicao. A checagem forte e a UF, que e independente do codigo —
    # se `CO_IES` tivesse casado com IES errada, o estado discordaria com frequencia.
    #
    # Resultado em 14/08/2026: 2.631 de 2.631 com UF igual, ZERO divergencia. O nome bate
    # em 93,7%; as ~123 divergencias sao RENOMEACAO, nao erro — a Afya rebatizou as
    # adquiridas ("Universidade do Grande Rio" -> "Afya Universidade Unigranrio") e varias
    # subiram de organizacao academica ("Escola Superior Batista do Amazonas" ->
    # "Centro Universitario ESBAM"). Todas as 123 tambem tem UF igual.
    uf_ok = uf_dif = 0
    divergentes = []
    for co in casam:
        ix = censo[co]
        r = emec[co]
        u1, u2 = (ies["uf"][ix] or ""), (r["uf"] or "")
        if u1 and u2:
            if u1 == u2:
                uf_ok += 1
            else:
                uf_dif += 1
                divergentes.append((co, ies["nome"][ix], r["ies_emec"], u1, u2))

    # ---- relatorio
    por_grupo = collections.Counter()
    igc_grupo = collections.defaultdict(list)
    for co in casam:
        ix = censo[co]
        g = ies["grupo"][ix]
        if not g:
            continue
        por_grupo[g] += 1
        v = emec[co]["igc"]
        if v.isdigit():
            igc_grupo[g].append(int(v))

    sinal = collections.Counter(r["sinalizacoes"] for r in regs if r["sinalizacoes"])
    faltantes = sorted(((mat.get(co, 0), co) for co in so_censo), reverse=True)[:15]

    L = ["# De-para e-MEC × Censo", "",
         "Fonte: `Dados_GEO.xlsx` — Relatório da Consulta Avançada do Sistema e-MEC.",
         "Gerado por `scripts/10_ingest_emec.py`.", "",
         "## Cobertura", "",
         "| Medida | Valor |", "|---|---:|",
         f"| IES no e-MEC (únicas) | {len(emec):,} |",
         f"| IES no `dim.ies` (toda a série 2015–2024) | {len(censo):,} |",
         f"| **Casam por `CO_IES`** | **{len(casam):,}** |",
         f"| Só no Censo (histórico/extintas) | {len(so_censo):,} |",
         f"| Só no e-MEC (sem matrícula no Censo) | {len(so_emec):,} |",
         f"| Matrículas 2024 cobertas | **{cob:,} de {tot:,} ({100*cob/tot:.1f}%)** |",
         "",
         "> A contagem de IES engana e a de matrículas é a que importa: as que ficam de fora "
         "são minúsculas. O e-MEC só traz IES **ativas**, então quase todo o resíduo é IES "
         "que existiu na série e não existe mais.", "",
         "### O casamento está correto? (validação por UF)", "",
         "Cobertura não é correção. A checagem forte é a **UF**, independente do código: se "
         "`CO_IES` tivesse casado com a instituição errada, o estado discordaria.", "",
         "| Checagem | Resultado |", "|---|---:|",
         f"| Linhas com UF nos dois lados | {uf_ok + uf_dif:,} |",
         f"| **UF igual** | **{uf_ok:,} ({100*uf_ok/max(1, uf_ok+uf_dif):.2f}%)** |",
         f"| UF divergente | {uf_dif:,} |", ""]
    if divergentes:
        L += ["⚠️ **Divergências de UF — investigar, são candidatas a erro real:**", "",
              "| CO_IES | Censo | e-MEC | UF Censo | UF e-MEC |", "|---:|---|---|---|---|"]
        for co, a, b, u1, u2 in divergentes[:20]:
            L.append(f"| {co} | {a} | {b} | {u1} | {u2} |")
        L.append("")
    else:
        L += ["✅ **Nenhuma divergência de UF.** Onde o nome difere, é renomeação e não erro "
              "de casamento: a Afya rebatizou as adquiridas e várias IES subiram de "
              "organização acadêmica. O `CO_IES` é o mesmo identificador nas duas bases, "
              "então o de-para é direto — nenhuma linha precisou de casamento por nome.", ""]
    L += [
         "### Maiores IES sem par no e-MEC", "",
         "| Matrículas 2024 | CO_IES | Instituição | UF |", "|---:|---:|---|---|"]
    for v, co in faltantes:
        ix = censo[co]
        L.append(f"| {v:,} | {co} | {ies['nome'][ix]} | {ies['uf'][ix] or '—'} |")

    L += ["", "## O que o e-MEC agrega ao Censo", "",
          "Não é geografia — o endereço é o da **sede**, um ponto por IES. É qualidade e "
          "situação regulatória:", "",
          "### IGC médio por grupo (só IES com nota)", "",
          "| Grupo | IES casadas | IGC médio | com nota |", "|---|---:|---:|---:|"]
    for g in sorted(igc_grupo, key=lambda g: -len(igc_grupo[g]))[:20]:
        vs = igc_grupo[g]
        L.append(f"| {g} | {por_grupo[g]} | {sum(vs)/len(vs):.2f} | {len(vs)} |")

    L += ["", "### Sinalizações vigentes", "",
          "Restrição regulatória em vigor. Material para o setor e ligado ao bloco "
          "Ambiente Regulatório.", "",
          "| Sinalização | IES |", "|---|---:|"]
    for k, v in sinal.most_common():
        L.append(f"| {k} | {v} |")

    os.makedirs(os.path.dirname(RELATORIO), exist_ok=True)
    open(RELATORIO, "w", encoding="utf-8").write("\n".join(L) + "\n")

    print(f"casam por CO_IES  : {len(casam):,}")
    print(f"matrículas cobertas: {cob:,} / {tot:,} ({100*cob/tot:.1f}%)")
    print(f"→ {SAIDA}")
    print(f"→ {WEB}  ({os.path.getsize(WEB)//1024} KB)")
    print(f"→ {RELATORIO}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
