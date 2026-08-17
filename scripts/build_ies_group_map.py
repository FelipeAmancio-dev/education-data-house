"""
Gera config/ies_grupo_map.csv  ->  tabela IES -> mantenedora -> grupo economico.

Cadeia de precedencia (do mais forte para o mais fraco):
  1. config/ies_grupo_overrides.csv    excecoes explicitas por CO_IES
  2. Suporte IES.xlsx                  sua planilha (uma aba por empresa)
  3. config/grupos_mantenedoras.csv    regras explicitas por CO_MANTENEDORA
  4. regra derivada                    mantenedora que ja tem IES mapeada pelo Suporte

Alem de GRUPO (visao standalone), gera GRUPO_CONSOLIDADO aplicando as fusoes marcadas
como ATIVO=sim em config/grupos_consolidacao.csv.

Uso:  python scripts/build_ies_group_map.py
"""
import os
import sys

import duckdb
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.suporte import ler_suporte, ler_csv_comentado, norm, classifica_codigos  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANO = 2024
BASE = os.path.join(ROOT, "data_raw", str(ANO), f"microdados_censo_da_educacao_superior_{ANO}", "dados")
IES_CSV = os.path.join(BASE, f"MICRODADOS_ED_SUP_IES_{ANO}.CSV")
CUR_CSV = os.path.join(BASE, f"MICRODADOS_CADASTRO_CURSOS_{ANO}.CSV")

SUPORTE = os.path.join(ROOT, "Suporte IES.xlsx")
CFG = os.path.join(ROOT, "config")
OUT_MAP = os.path.join(CFG, "ies_grupo_map.csv")
OUT_ORFAOS = os.path.join(CFG, "ies_grupo_map_nao_encontradas.csv")
OUT_POR_GRUPO = os.path.join(ROOT, "outputs", "grupos_composicao_2024.md")

READ = "delim=';', header=true, encoding='latin-1', sample_size=-1, null_padding=true"

# ------------------------------------------------------------ 1. Suporte
abas_cfg = ler_csv_comentado(os.path.join(CFG, "suporte_abas.csv"))
mapa_abas = {norm(r.ABA): str(r.GRUPO).strip() for r in abas_cfg.itertuples()} if len(abas_cfg) else {}

sup_raw, avisos = ler_suporte(SUPORTE, mapa_abas)
for a in avisos:
    print(f"[AVISO] {a}")

print(f"\n1. Suporte IES.xlsx : {sup_raw['ABA'].nunique()} abas, {len(sup_raw)} linhas")

# ------------------------------------------------------------ 2. Censo
con = duckdb.connect()
con.execute(f"CREATE TABLE ies AS SELECT * FROM read_csv('{IES_CSV}', {READ});")
con.execute(f"""CREATE TABLE cur AS SELECT CO_IES, TP_DIMENSAO, TP_MODALIDADE_ENSINO,
                CO_MUNICIPIO, QT_MAT, QT_ING, QT_CONC, QT_CURSO, QT_SIT_TRANCADA
                FROM read_csv('{CUR_CSV}', {READ});""")

base = con.sql("""
WITH m AS (
  SELECT CO_IES, sum(QT_MAT) QT_MAT_TOTAL,
         sum(CASE WHEN TP_MODALIDADE_ENSINO=1 THEN QT_MAT ELSE 0 END) QT_MAT_PRESENCIAL,
         sum(CASE WHEN TP_MODALIDADE_ENSINO=2 THEN QT_MAT ELSE 0 END) QT_MAT_EAD,
         sum(QT_ING) QT_ING, sum(QT_CONC) QT_CONC,
         sum(coalesce(QT_SIT_TRANCADA,0)) QT_TRANCADA,
         sum(QT_MAT + coalesce(QT_SIT_TRANCADA,0)) QT_BASE_ALUNOS
  FROM cur WHERE TP_DIMENSAO IN (1,2,4) GROUP BY 1),
c AS (SELECT CO_IES, sum(QT_CURSO) QT_CURSOS FROM cur WHERE TP_DIMENSAO IN (1,3) GROUP BY 1),
u AS (SELECT CO_IES, count(DISTINCT CO_MUNICIPIO) QT_MUNIC_PRESENCIAL
      FROM cur WHERE TP_DIMENSAO=1 GROUP BY 1),
e AS (SELECT CO_IES, count(DISTINCT CO_MUNICIPIO) QT_MUNIC_EAD
      FROM cur WHERE TP_DIMENSAO=2 AND QT_MAT>0 GROUP BY 1)
SELECT i.CO_IES, i.NO_IES, i.SG_IES, i.CO_MANTENEDORA, i.NO_MANTENEDORA,
       i.TP_REDE, i.TP_CATEGORIA_ADMINISTRATIVA, i.TP_ORGANIZACAO_ACADEMICA,
       i.SG_UF_IES, i.NO_MUNICIPIO_IES,
       coalesce(m.QT_MAT_TOTAL,0) QT_MAT_TOTAL, coalesce(m.QT_MAT_PRESENCIAL,0) QT_MAT_PRESENCIAL,
       coalesce(m.QT_MAT_EAD,0) QT_MAT_EAD, coalesce(m.QT_ING,0) QT_ING, coalesce(m.QT_CONC,0) QT_CONC,
       coalesce(m.QT_TRANCADA,0) QT_TRANCADA, coalesce(m.QT_BASE_ALUNOS,0) QT_BASE_ALUNOS,
       coalesce(c.QT_CURSOS,0) QT_CURSOS, coalesce(u.QT_MUNIC_PRESENCIAL,0) QT_MUNIC_PRESENCIAL,
       coalesce(e.QT_MUNIC_EAD,0) QT_MUNIC_EAD
FROM ies i LEFT JOIN m USING (CO_IES) LEFT JOIN c USING (CO_IES)
LEFT JOIN u USING (CO_IES) LEFT JOIN e USING (CO_IES)
""").df()
base["CO_IES"] = base["CO_IES"].astype("int64")

# --------------------------------------- 2b. desambigua codigo IES x mantenedora
sup_cls = classifica_codigos(sup_raw, base)
# na deduplicacao, prefere a linha cujo nome melhor casa com o Censo
sup_cls["_score"] = sup_cls[["SCORE_IES", "SCORE_MANT"]].max(axis=1)
sup_cls = sup_cls.sort_values("_score", ascending=False)

sup = sup_cls[sup_cls["TIPO_CODIGO"] == "ies"].drop_duplicates(subset=["CO_IES"], keep="first")
sup_mant = sup_cls[sup_cls["TIPO_CODIGO"] == "mantenedora"].drop_duplicates(subset=["CO_IES"], keep="first")

print(f"   codigos classificados: {len(sup)} como IES · {len(sup_mant)} como MANTENEDORA")
for aba, g in sup_cls.groupby("ABA"):
    ni = g[g["TIPO_CODIGO"] == "ies"]["CO_IES"].nunique()
    nm = g[g["TIPO_CODIGO"] == "mantenedora"]["CO_IES"].nunique()
    extra = f" + {nm} mantenedoras" if nm else ""
    print(f"     {aba:<20} {len(g):>4} linhas -> {ni:>4} IES{extra}   ({g['GRUPO'].iloc[0]})")

if len(sup_mant):
    print("\n   [i] Linhas cujo codigo e de MANTENEDORA, nao de IES (o nome bate com a")
    print("       mantenedora). Aplicadas como regra de mantenedora — nenhuma perda:")
    for r in sup_mant.itertuples():
        print(f"       {r.ABA:<16} {r.CO_IES:>6}  {str(r.NO_IES_SUPORTE)[:42]:<42} "
              f"(IES {r.SCORE_IES:.2f} / mant {r.SCORE_MANT:.2f})")

rev = sup_cls[sup_cls["REVISAR"]]
if len(rev):
    print("\n   [!] AMBIGUOS — o codigo existe nos dois universos e o nome nao bate bem com")
    print("       nenhum. Resolvido pelo maior score, mas vale conferir no Excel:")
    for r in rev.itertuples():
        print(f"       {r.ABA:<16} {r.CO_IES:>6}  {str(r.NO_IES_SUPORTE)[:42]:<42} "
              f"-> {r.TIPO_CODIGO}  (IES {r.SCORE_IES:.2f} / mant {r.SCORE_MANT:.2f})")

# ------------------------------------------------------------ 3. resolucao
mapa = base.merge(sup[["CO_IES", "GRUPO", "NO_IES_SUPORTE", "ABA", "MARCA"]], on="CO_IES", how="left")
mapa["GRUPO"] = mapa["GRUPO"].fillna("")
mapa["ORIGEM_GRUPO"] = ""
mapa.loc[mapa["GRUPO"] != "", "ORIGEM_GRUPO"] = "suporte_xlsx"

# 3a. mantenedoras vindas da propria planilha
n_supm = 0
if len(sup_mant):
    r = dict(zip(sup_mant["CO_IES"].astype("int64"), sup_mant["GRUPO"].astype(str).str.strip()))
    alvo = (mapa["GRUPO"] == "") & mapa["CO_MANTENEDORA"].isin(r)
    mapa.loc[alvo, "GRUPO"] = mapa.loc[alvo, "CO_MANTENEDORA"].map(r)
    mapa.loc[alvo, "ORIGEM_GRUPO"] = "mantenedora_suporte"
    n_supm = int(alvo.sum())
print(f"\n2. mantenedoras do Suporte : {len(sup_mant)} regras -> {n_supm} IES atribuidas")

# 3b. regras explicitas de config
regras = ler_csv_comentado(os.path.join(CFG, "grupos_mantenedoras.csv"))
n_reg = 0
if len(regras):
    r = dict(zip(regras["CO_MANTENEDORA"].astype("int64"), regras["GRUPO"].astype(str).str.strip()))
    alvo = (mapa["GRUPO"] == "") & mapa["CO_MANTENEDORA"].isin(r)
    mapa.loc[alvo, "GRUPO"] = mapa.loc[alvo, "CO_MANTENEDORA"].map(r)
    mapa.loc[alvo, "ORIGEM_GRUPO"] = "regra_mantenedora"
    n_reg = int(alvo.sum())
print(f"3. grupos_mantenedoras.csv : {len(regras)} regras -> {n_reg} IES atribuidas")

derivado = (mapa[mapa["ORIGEM_GRUPO"] == "suporte_xlsx"].groupby("CO_MANTENEDORA")["GRUPO"]
            .agg(lambda s: s.iloc[0] if s.nunique() == 1 else None).dropna())
alvo = (mapa["GRUPO"] == "") & mapa["CO_MANTENEDORA"].isin(derivado.index)
mapa.loc[alvo, "GRUPO"] = mapa.loc[alvo, "CO_MANTENEDORA"].map(derivado)
mapa.loc[alvo, "ORIGEM_GRUPO"] = "mantenedora_derivada"
print(f"4. mantenedora derivada    : {int(alvo.sum())} IES irmas capturadas")
_n5 = 5

ov = ler_csv_comentado(os.path.join(CFG, "ies_grupo_overrides.csv"))
n_ov = 0
if len(ov):
    ov["CO_IES"] = pd.to_numeric(ov["CO_IES"], errors="coerce").astype("Int64")
    d = dict(zip(ov["CO_IES"], ov["GRUPO"].fillna("").astype(str).str.strip()))
    alvo = mapa["CO_IES"].isin(d)
    mapa.loc[alvo, "GRUPO"] = mapa.loc[alvo, "CO_IES"].map(d)
    mapa.loc[alvo, "ORIGEM_GRUPO"] = "override"
    n_ov = int(alvo.sum())
print(f"5. overrides               : {n_ov} IES")

# ------------------------------------------------------------ 4. consolidacao (M&A)
cons = ler_csv_comentado(os.path.join(CFG, "grupos_consolidacao.csv"))
mapa["GRUPO_CONSOLIDADO"] = mapa["GRUPO"]
ativas = []
if len(cons):
    for r in cons.itertuples():
        ativo = str(getattr(r, "ATIVO", "nao")).strip().lower() in ("sim", "s", "true", "1")
        origem, destino = str(r.GRUPO_ORIGEM).strip(), str(r.GRUPO_DESTINO).strip()
        if ativo:
            mapa.loc[mapa["GRUPO_CONSOLIDADO"] == origem, "GRUPO_CONSOLIDADO"] = destino
            ativas.append(f"{origem} -> {destino}")
        else:
            n = int((mapa["GRUPO"] == origem).sum())
            m = float(mapa.loc[mapa["GRUPO"] == origem, "QT_MAT_TOTAL"].sum())
            print(f"5. consolidacao pendente   : {origem} -> {destino}  "
                  f"(ATIVO=nao | {n} IES, {m:,.0f} alunos separados)")
if ativas:
    print(f"5. consolidacoes aplicadas : {', '.join(ativas)}")

# ------------------------------------------------------------ 5. saida
mapa["MARCA"] = mapa["MARCA"].fillna("")
cols = ["CO_IES", "NO_IES", "SG_IES", "GRUPO", "GRUPO_CONSOLIDADO", "MARCA", "ORIGEM_GRUPO", "ABA",
        "CO_MANTENEDORA", "NO_MANTENEDORA", "TP_REDE", "TP_CATEGORIA_ADMINISTRATIVA",
        "TP_ORGANIZACAO_ACADEMICA", "SG_UF_IES", "NO_MUNICIPIO_IES",
        "QT_MAT_TOTAL", "QT_MAT_PRESENCIAL", "QT_MAT_EAD", "QT_ING", "QT_CONC",
        "QT_TRANCADA", "QT_BASE_ALUNOS",
        "QT_CURSOS", "QT_MUNIC_PRESENCIAL", "QT_MUNIC_EAD", "NO_IES_SUPORTE"]
mapa["ABA"] = mapa["ABA"].fillna("")
mapa[cols].sort_values(["GRUPO", "QT_MAT_TOTAL"], ascending=[True, False]) \
    .to_csv(OUT_MAP, index=False, encoding="utf-8-sig", sep=";")

orfaos = sup[~sup["CO_IES"].isin(base["CO_IES"])][["CO_IES", "GRUPO", "NO_IES_SUPORTE", "ABA"]].assign(
    MOTIVO_PROVAVEL=f"CO_IES ausente do Censo {ANO} (IES extinta, incorporada ou codigo alterado)")
orfaos.to_csv(OUT_ORFAOS, index=False, encoding="utf-8-sig", sep=";")

# ------------------------------------------------------------ 6. relatorio
tot = float(base["QT_MAT_TOTAL"].sum())
priv = float(base.loc[base["TP_REDE"] == 2, "QT_MAT_TOTAL"].sum())
mapeada = float(mapa.loc[mapa["GRUPO"] != "", "QT_MAT_TOTAL"].sum())
print(f"\nEscrito: {OUT_MAP}  ({len(mapa)} IES)")
print(f"Escrito: {OUT_ORFAOS}  ({len(orfaos)} codigos sem correspondencia no Censo {ANO})")
print(f"\nCobertura: {mapeada:,.0f} de {tot:,.0f} matriculas "
      f"({100*mapeada/tot:.1f}% do total | {100*mapeada/priv:.1f}% da rede privada)")

tot_base = float(base["QT_BASE_ALUNOS"].sum())
res = (mapa[mapa["GRUPO"] != ""].groupby("GRUPO")
       .agg(IES=("CO_IES", "count"), MAT=("QT_MAT_TOTAL", "sum"),
            PRES=("QT_MAT_PRESENCIAL", "sum"), EAD=("QT_MAT_EAD", "sum"),
            TRANC=("QT_TRANCADA", "sum"), BASE=("QT_BASE_ALUNOS", "sum"),
            CURSOS=("QT_CURSOS", "sum"), UNID=("QT_MUNIC_PRESENCIAL", "sum"))
       .sort_values("MAT", ascending=False))
res["SHARE%"] = (100 * res["MAT"] / tot).round(2)
res["EAD%"] = (100 * res["EAD"] / res["MAT"].where(res["MAT"] > 0)).astype(float).round(1)
res["TRANC%"] = (100 * res["TRANC"] / res["MAT"].where(res["MAT"] > 0)).astype(float).round(1)
res["SH_BASE%"] = (100 * res["BASE"] / tot_base).round(2)
print(f"\n{len(res)} grupos:\n")
print(res.to_string())

# detalhe por grupo do Suporte
L = ["# Composição dos grupos — Censo 2024\n",
     f"> Gerado por `scripts/build_ies_group_map.py`. Mercado total: **{tot:,.0f}** matrículas.\n",
     "> Lista as IES efetivamente consideradas em cada grupo vindo do `Suporte IES.xlsx`.\n"]
for g in sup["GRUPO"].unique():
    d = mapa[mapa["GRUPO"] == g].sort_values("QT_MAT_TOTAL", ascending=False)
    if not len(d):
        continue
    L.append(f"\n## {g} — {len(d)} IES · {d['QT_MAT_TOTAL'].sum():,.0f} matrículas "
             f"({100*d['QT_MAT_TOTAL'].sum()/tot:.2f}% do mercado)\n")
    L.append("| CO_IES | IES | UF | Mantenedora | Matrículas | Presencial | EAD | Origem |")
    L.append("|---:|---|---|---|---:|---:|---:|---|")
    for r in d.itertuples():
        L.append(f"| {r.CO_IES} | {str(r.NO_IES)[:46]} | {r.SG_UF_IES} | "
                 f"{str(r.NO_MANTENEDORA)[:32]} | {r.QT_MAT_TOTAL:,.0f} | "
                 f"{r.QT_MAT_PRESENCIAL:,.0f} | {r.QT_MAT_EAD:,.0f} | {r.ORIGEM_GRUPO} |")
os.makedirs(os.path.dirname(OUT_POR_GRUPO), exist_ok=True)
open(OUT_POR_GRUPO, "w", encoding="utf-8").write("\n".join(L))
print(f"\nEscrito: {OUT_POR_GRUPO}")
