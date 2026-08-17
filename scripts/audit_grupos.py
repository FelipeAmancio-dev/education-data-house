"""
Auditoria do mapeamento IES -> grupo economico.

Produz:
  outputs/audit_grupos_2024.md            relatorio legivel
  config/ies_grupo_map_sugestoes.csv      candidatos para revisao (nao aplica nada)

Niveis de evidencia:
  A  mesma CO_MANTENEDORA de uma IES ja mapeada   -> evidencia forte, dentro da propria base
  B  marca do grupo no nome da IES/mantenedora    -> evidencia forte, requer confirmacao
  C  IES privada grande sem grupo                 -> candidata a grupo novo/independente

Uso:  python scripts/audit_grupos.py
"""
import json
import os
import re
import sys
import unicodedata

import duckdb
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANO = 2024
BASE = os.path.join(ROOT, "data_raw", str(ANO), f"microdados_censo_da_educacao_superior_{ANO}", "dados")
IES_CSV = os.path.join(BASE, f"MICRODADOS_ED_SUP_IES_{ANO}.CSV")
CUR_CSV = os.path.join(BASE, f"MICRODADOS_CADASTRO_CURSOS_{ANO}.CSV")
MAP_CSV = os.path.join(ROOT, "config", "ies_grupo_map.csv")
MARCAS = os.path.join(ROOT, "config", "grupos_marcas.json")
OUT_MD = os.path.join(ROOT, "outputs", "audit_grupos_2024.md")
OUT_CSV = os.path.join(ROOT, "config", "ies_grupo_map_sugestoes.csv")

READ = "delim=';', header=true, encoding='latin-1', sample_size=-1, null_padding=true"
LIMIAR_GRANDE = 8000   # matriculas para considerar uma IES privada "relevante"


def norm(s: str) -> str:
    """Maiuscula, sem acento, espacos normalizados."""
    s = "" if s is None else str(s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).upper().strip()


con = duckdb.connect()
con.execute(f"CREATE TABLE ies AS SELECT * FROM read_csv('{IES_CSV}', {READ});")
con.execute(f"""CREATE TABLE cur AS SELECT CO_IES, TP_DIMENSAO, TP_MODALIDADE_ENSINO,
                CO_MUNICIPIO, QT_MAT, QT_CURSO FROM read_csv('{CUR_CSV}', {READ});""")

mapa = pd.read_csv(MAP_CSV, sep=";", encoding="utf-8-sig")
mapa["GRUPO"] = mapa["GRUPO"].fillna("").astype(str).str.strip()
con.register("mp", mapa[["CO_IES", "GRUPO"]])

_marcas_raw = json.load(open(MARCAS, encoding="utf-8"))
marcas = {k: v for k, v in _marcas_raw.items() if not k.startswith("_")}
FALSOS = {int(k) for k in _marcas_raw.get("_falsos_positivos", {}) if k.isdigit()}

df = con.sql("""
WITH m AS (
  SELECT CO_IES, sum(QT_MAT) mat,
         sum(CASE WHEN TP_MODALIDADE_ENSINO=1 THEN QT_MAT ELSE 0 END) presencial,
         sum(CASE WHEN TP_MODALIDADE_ENSINO=2 THEN QT_MAT ELSE 0 END) ead
  FROM cur WHERE TP_DIMENSAO IN (1,2,4) GROUP BY 1),
c AS (SELECT CO_IES, sum(QT_CURSO) cursos FROM cur WHERE TP_DIMENSAO IN (1,3) GROUP BY 1),
u AS (SELECT CO_IES, count(DISTINCT CO_MUNICIPIO) unidades FROM cur WHERE TP_DIMENSAO=1 GROUP BY 1)
SELECT i.CO_IES, i.NO_IES, i.CO_MANTENEDORA, i.NO_MANTENEDORA, i.TP_REDE,
       i.SG_UF_IES, i.NO_MUNICIPIO_IES, mp.GRUPO,
       coalesce(m.mat,0) mat, coalesce(m.presencial,0) presencial, coalesce(m.ead,0) ead,
       coalesce(c.cursos,0) cursos, coalesce(u.unidades,0) unidades
FROM ies i LEFT JOIN m USING (CO_IES) LEFT JOIN c USING (CO_IES)
LEFT JOIN u USING (CO_IES) JOIN mp ON mp.CO_IES = i.CO_IES
""").df()

TOTAL = float(df["mat"].sum())
priv = df[df["TP_REDE"] == 2]
naomap = priv[priv["GRUPO"] == ""].copy()
df["_no"] = df["NO_IES"].map(norm)
df["_mant"] = df["NO_MANTENEDORA"].map(norm)
naomap["_no"] = naomap["NO_IES"].map(norm)
naomap["_mant"] = naomap["NO_MANTENEDORA"].map(norm)

sugest = []

# --------------------------------------------------- A: mesma mantenedora
mant_grupo = (df[df["GRUPO"] != ""].groupby("CO_MANTENEDORA")["GRUPO"]
              .agg(lambda s: s.iloc[0] if s.nunique() == 1 else None).dropna())
for _, r in naomap.iterrows():
    g = mant_grupo.get(r["CO_MANTENEDORA"])
    if g:
        sugest.append({**r[["CO_IES", "NO_IES", "NO_MANTENEDORA", "SG_UF_IES", "mat"]].to_dict(),
                       "GRUPO_SUGERIDO": g, "EVIDENCIA": "A",
                       "MOTIVO": f"mantenedora {r['CO_MANTENEDORA']} ja pertence a {g}"})

ja = {s["CO_IES"] for s in sugest} | FALSOS   # falsos positivos ja verificados nao voltam

# --------------------------------------------------- B: marca no nome
for grupo, tokens in marcas.items():
    for tok in tokens:
        pat = re.compile(rf"\b{re.escape(norm(tok))}\b")
        for _, r in naomap.iterrows():
            if r["CO_IES"] in ja:
                continue
            onde = "nome da IES" if pat.search(r["_no"]) else ("mantenedora" if pat.search(r["_mant"]) else None)
            if onde:
                sugest.append({**r[["CO_IES", "NO_IES", "NO_MANTENEDORA", "SG_UF_IES", "mat"]].to_dict(),
                               "GRUPO_SUGERIDO": grupo, "EVIDENCIA": "B",
                               "MOTIVO": f"marca '{tok}' encontrada no {onde}"})
                ja.add(r["CO_IES"])

sug = pd.DataFrame(sugest)
if len(sug):
    sug = sug.sort_values(["EVIDENCIA", "mat"], ascending=[True, False])
    sug.to_csv(OUT_CSV, sep=";", index=False, encoding="utf-8-sig")

# --------------------------------------------------- C: clusters sem grupo
restante = naomap[~naomap["CO_IES"].isin(ja)]
clusters = (restante.groupby("CO_MANTENEDORA")
            .agg(MANTENEDORA=("NO_MANTENEDORA", "first"), N_IES=("CO_IES", "count"),
                 MAT=("mat", "sum"), EAD=("ead", "sum"), UF=("SG_UF_IES", "first"),
                 IES=("NO_IES", lambda s: " · ".join(sorted(s)[:4])))
            .reset_index().sort_values("MAT", ascending=False))
clusters["SHARE"] = (100 * clusters["MAT"] / TOTAL).round(2)
clusters["PCT_EAD"] = (100 * clusters["EAD"] / clusters["MAT"].where(clusters["MAT"] > 0)).astype(float).round(0)

# --------------------------------------------------- relatorio
L = []
w = L.append
w("# Auditoria do Mapeamento de Grupos Econômicos — Censo 2024\n")
w(f"> Gerado por `scripts/audit_grupos.py`. Mercado total: **{TOTAL:,.0f}** matrículas.\n")
w("> Nada aqui é aplicado automaticamente. Este relatório produz candidatos para sua decisão.\n")

w("\n## 1. Cobertura atual\n")
mapeada = float(df.loc[df["GRUPO"] != "", "mat"].sum())
matpriv = float(priv["mat"].sum())
w(f"| Métrica | Valor |\n|---|---|")
w(f"| Matrículas mapeadas a grupo | {mapeada:,.0f} |")
w(f"| % do mercado total | {100*mapeada/TOTAL:.1f}% |")
w(f"| % da rede privada | {100*mapeada/matpriv:.1f}% |")
w(f"| IES privadas sem grupo | {len(naomap):,} de {len(priv):,} |")
w(f"| Matrículas privadas sem grupo | {float(naomap['mat'].sum()):,.0f} |")

w("\n## 2. Grupos atuais\n")
g = (df[df["GRUPO"] != ""].groupby("GRUPO")
     .agg(IES=("CO_IES", "count"), MAT=("mat", "sum"), PRES=("presencial", "sum"),
          EAD=("ead", "sum"), CURSOS=("cursos", "sum"), UNID=("unidades", "sum"))
     .sort_values("MAT", ascending=False))
w("| Grupo | IES | Matrículas | Presencial | EAD | % EAD | Cursos | Unidades | Share |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|")
for k, r in g.iterrows():
    w(f"| {k} | {r.IES:.0f} | {r.MAT:,.0f} | {r.PRES:,.0f} | {r.EAD:,.0f} | "
      f"{100*r.EAD/r.MAT if r.MAT else 0:.0f}% | {r.CURSOS:,.0f} | {r.UNID:,.0f} | {100*r.MAT/TOTAL:.2f}% |")

if len(sug):
    for ev, titulo, nota in [
        ("A", "3. Evidência A — mesma mantenedora de IES já mapeada",
         "Evidência interna à base: estas IES têm a **mesma mantenedora** de uma IES já atribuída ao grupo. "
         "É o indício mais forte disponível no Censo."),
        ("B", "4. Evidência B — marca do grupo no nome",
         "Marca do grupo encontrada no nome da IES ou da mantenedora. Forte, mas **confirme**: "
         "marcas homônimas entre grupos diferentes existem."),
    ]:
        s = sug[sug["EVIDENCIA"] == ev]
        w(f"\n## {titulo}\n")
        if not len(s):
            w("_Nenhum caso._\n")
            continue
        w(nota + "\n")
        w(f"**{len(s)} IES · {float(s['mat'].sum()):,.0f} matrículas**\n")
        w("| CO_IES | IES | UF | Matrículas | Grupo sugerido | Motivo |\n|---:|---|---|---:|---|---|")
        for _, r in s.iterrows():
            w(f"| {r.CO_IES} | {str(r.NO_IES)[:48]} | {r.SG_UF_IES} | {r.mat:,.0f} | "
              f"**{r.GRUPO_SUGERIDO}** | {r.MOTIVO} |")

w("\n## 5. Evidência C — maiores players privados ainda sem grupo\n")
w(f"Agrupados por mantenedora. Estes são os candidatos a **grupo próprio** ou a permanecer como "
  f"Independentes.\n")
big = clusters[clusters["MAT"] >= LIMIAR_GRANDE]
w(f"**{len(big)} clusters · {float(big['MAT'].sum()):,.0f} matrículas "
  f"({100*float(big['MAT'].sum())/TOTAL:.1f}% do mercado)**\n")
w("| Mantenedora | UF | IES | Matrículas | % EAD | Share | Principais IES |\n|---|---|---:|---:|---:|---:|---|")
for _, r in big.iterrows():
    w(f"| {str(r.MANTENEDORA)[:40]} | {r.UF} | {r.N_IES} | {r.MAT:,.0f} | "
      f"{r.PCT_EAD if pd.notna(r.PCT_EAD) else 0:.0f}% | {r.SHARE:.2f}% | {str(r.IES)[:70]} |")

w("\n## 6. Ranking do mercado com os grupos atuais\n")
rk = df.copy()
rk["G"] = rk.apply(lambda r: r["GRUPO"] if r["GRUPO"] else
                   ("Pública — " + str(r["NO_IES"])[:30] if r["TP_REDE"] == 1 else "Independentes"), axis=1)
top = (rk.groupby("G")["mat"].sum().sort_values(ascending=False).head(15))
w("| # | Grupo / bloco | Matrículas | Share |\n|---:|---|---:|---:|")
for i, (k, v) in enumerate(top.items(), 1):
    w(f"| {i} | {k} | {v:,.0f} | {100*v/TOTAL:.2f}% |")

os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
open(OUT_MD, "w", encoding="utf-8").write("\n".join(L))

print(f"Relatorio : {OUT_MD}")
print(f"Sugestoes : {OUT_CSV}  ({len(sug)} candidatos)")
print(f"\nCobertura atual: {100*mapeada/TOTAL:.1f}% do mercado / {100*mapeada/matpriv:.1f}% da privada")
if len(sug):
    print("\nCandidatos por evidencia:")
    print(sug.groupby("EVIDENCIA").agg(IES=("CO_IES", "count"), MATRICULAS=("mat", "sum")).to_string())
    print("\nPor grupo sugerido:")
    print(sug.groupby(["EVIDENCIA", "GRUPO_SUGERIDO"])
          .agg(IES=("CO_IES", "count"), MAT=("mat", "sum")).to_string())
