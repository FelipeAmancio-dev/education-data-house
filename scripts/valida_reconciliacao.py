"""
Reconcilia o Censo contra os numeros reportados pelas companhias.

Compara duas definicoes do Censo com o que a empresa divulgou:
  QT_MAT                 alunos "Cursando e/ou Formado" (definicao oficial INEP)
  QT_MAT + trancados     "base de alunos", que e o que costuma constar dos releases

Preencha config/reportado_companhias.csv e rode:
  python scripts/valida_reconciliacao.py
"""
import os
import sys

import duckdb
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.suporte import ler_csv_comentado  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANO = 2024
BASE = os.path.join(ROOT, "data_raw", str(ANO), f"microdados_censo_da_educacao_superior_{ANO}", "dados")
CUR_CSV = os.path.join(BASE, f"MICRODADOS_CADASTRO_CURSOS_{ANO}.CSV")
MAP_CSV = os.path.join(ROOT, "config", "ies_grupo_map.csv")
REPORTADO = os.path.join(ROOT, "config", "reportado_companhias.csv")
OUT = os.path.join(ROOT, "outputs", f"reconciliacao_{ANO}.md")

READ = "delim=';', header=true, encoding='latin-1', sample_size=-1, null_padding=true"

con = duckdb.connect()
con.execute(f"""CREATE TABLE cur AS SELECT CO_IES, TP_DIMENSAO, TP_MODALIDADE_ENSINO,
                QT_MAT, QT_SIT_TRANCADA FROM read_csv('{CUR_CSV}', {READ});""")
mp = pd.read_csv(MAP_CSV, sep=";", encoding="utf-8-sig")
mp["GRUPO"] = mp["GRUPO"].fillna("")
con.register("mp", mp[["CO_IES", "GRUPO"]])

censo = con.sql("""
SELECT mp.GRUPO,
  sum(c.QT_MAT) FILTER (WHERE c.TP_MODALIDADE_ENSINO=1)                              AS MAT_PRES,
  sum(c.QT_MAT) FILTER (WHERE c.TP_MODALIDADE_ENSINO=2)                              AS MAT_EAD,
  sum(c.QT_MAT)                                                                      AS MAT_TOT,
  sum(c.QT_MAT+coalesce(c.QT_SIT_TRANCADA,0)) FILTER (WHERE c.TP_MODALIDADE_ENSINO=1) AS BASE_PRES,
  sum(c.QT_MAT+coalesce(c.QT_SIT_TRANCADA,0)) FILTER (WHERE c.TP_MODALIDADE_ENSINO=2) AS BASE_EAD,
  sum(c.QT_MAT+coalesce(c.QT_SIT_TRANCADA,0))                                        AS BASE_TOT,
  sum(coalesce(c.QT_SIT_TRANCADA,0))                                                 AS TRANCADOS
FROM cur c JOIN mp ON mp.CO_IES=c.CO_IES
WHERE mp.GRUPO<>'' AND c.TP_DIMENSAO IN (1,2,4) GROUP BY 1
""").df().fillna(0).set_index("GRUPO")

rep = ler_csv_comentado(REPORTADO)
if not len(rep):
    print("config/reportado_companhias.csv esta vazio — nada a reconciliar.")
    sys.exit(0)
rep = rep[rep["ANO"].astype(str) == str(ANO)]

L = [f"# Reconciliação Censo × reportado pelas companhias — {ANO}\n",
     "> Gerado por `scripts/valida_reconciliacao.py`.",
     "> `QT_MAT` = definição INEP (Cursando + Formado, **exclui trancados**).",
     "> `Base` = `QT_MAT` + trancados, que é o que costuma constar dos releases.\n"]

linhas, sem_dado = [], []
for r in rep.itertuples():
    g = str(r.GRUPO).strip()
    if g not in censo.index:
        continue
    c = censo.loc[g]

    def num(v):
        try:
            v = float(v)
            return v if v == v and v > 0 else None
        except (TypeError, ValueError):
            return None

    # Comparar com o numero-manchete e errado: ele carrega pos, tecnico e ate curso
    # preparatorio, que nao existem no Censo da Educacao Superior. Quando ha recorte
    # de graduacao no release (colunas GRAD_*), e ele que vale.
    grad = (num(getattr(r, "GRAD_PRESENCIAL", None)), num(getattr(r, "GRAD_EAD", None)),
            num(getattr(r, "GRAD_TOTAL", None)))
    so_graduacao = any(v is not None for v in grad)
    if so_graduacao:
        alvos = {"Presencial": (grad[0], c.MAT_PRES, c.BASE_PRES),
                 "EAD": (grad[1], c.MAT_EAD, c.BASE_EAD),
                 "Total": (grad[2], c.MAT_TOT, c.BASE_TOT)}
    else:
        alvos = {"Presencial": (num(r.ALUNOS_PRESENCIAL), c.MAT_PRES, c.BASE_PRES),
                 "EAD": (num(r.ALUNOS_EAD), c.MAT_EAD, c.BASE_EAD),
                 "Total": (num(r.ALUNOS_TOTAL), c.MAT_TOT, c.BASE_TOT)}
    if alvos["Total"][0] is None and alvos["Presencial"][0] and alvos["EAD"][0]:
        alvos["Total"] = (alvos["Presencial"][0] + alvos["EAD"][0], c.MAT_TOT, c.BASE_TOT)

    if all(v[0] is None for v in alvos.values()):
        sem_dado.append(g)
        continue

    escopo = str(getattr(r, "ESCOPO", "") or "").strip() or "não informado"
    tranc_pct = 100 * c.TRANCADOS / c.MAT_TOT if c.MAT_TOT else 0
    L.append(f"\n## {g}\n")
    if so_graduacao:
        L.append("Comparação restrita a **graduação** — único recorte comparável ao Censo. "
                 f"Escopo do número-manchete do release: *{escopo}* (não usado). "
                 f"Taxa de trancamento no Censo: **{tranc_pct:.1f}%**\n")
        deriv = str(getattr(r, "GRAD_DERIVACAO", "") or "").strip()
        if deriv:
            L.append(f"Derivação do número de graduação: {deriv}.\n")
    else:
        L.append(f"⚠️ Sem recorte de graduação no release — comparando com o número-manchete, "
                 f"escopo **{escopo}**, que não é diretamente comparável. "
                 f"Taxa de trancamento no Censo: **{tranc_pct:.1f}%**\n")
    L.append("| Recorte | Reportado | Censo `QT_MAT` | Δ | Censo Base | Δ |")
    L.append("|---|---:|---:|---:|---:|---:|")
    for nome, (rep_v, mat, bse) in alvos.items():
        if rep_v is None:
            continue
        d1 = 100 * (mat - rep_v) / rep_v
        d2 = 100 * (bse - rep_v) / rep_v
        L.append(f"| {nome} | {rep_v:,.0f} | {mat:,.0f} | {d1:+.1f}% | {bse:,.0f} | {d2:+.1f}% |")
        linhas.append({"GRUPO": g, "RECORTE": nome, "REPORTADO": rep_v,
                       "CENSO_QT_MAT": mat, "GAP_QT_MAT_%": round(d1, 1),
                       "CENSO_BASE": bse, "GAP_BASE_%": round(d2, 1)})

if sem_dado:
    L.append("\n## Sem número reportado preenchido\n")
    L.append(", ".join(sorted(sem_dado)) + "\n")
    L.append("Preencha `config/reportado_companhias.csv` para incluí-los na reconciliação.\n")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write("\n".join(L))
print(f"Escrito: {OUT}")

if linhas:
    d = pd.DataFrame(linhas)
    print()
    print(d.to_string(index=False))
    print("\nLeitura: |GAP| < 5% indica que a definicao reconcilia bem.")
if sem_dado:
    print(f"\nSem numero reportado: {', '.join(sorted(sem_dado))}")
