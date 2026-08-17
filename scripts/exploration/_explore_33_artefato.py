"""
Quantifica o risco de artefato: crescimento em QT_MAT vs. crescimento em BASE (mat+trancados).

Se a base de alunos (mat+trancados) cresce suavemente mas QT_MAT da um salto, o salto e
reclassificacao de trancado -> cursando, nao ganho real de aluno.
"""
import sys, os, duckdb, pandas as pd
sys.path.insert(0, r"C:\education\scripts")
from lib.censo import DIM_ALUNOS
sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 250)
PROC = r"C:\education\data_processed"
con = duckdb.connect()
con.execute(f"CREATE VIEW f AS SELECT * FROM read_parquet('{PROC}/fato_cursos_*.parquet');".replace("\\", "/"))
con.execute(f"CREATE VIEW di AS SELECT * FROM read_parquet('{PROC}/dim_ies.parquet');".replace("\\", "/"))
d = ",".join(map(str, DIM_ALUNOS))

s = con.sql(f"""
SELECT di.GRUPO, f.NU_ANO_CENSO AS ANO,
       sum(f.QT_MAT) AS MAT,
       sum(f.QT_MAT + coalesce(f.QT_SIT_TRANCADA,0)) AS BASE
FROM f JOIN di ON di.CO_IES=f.CO_IES AND di.ANO=f.NU_ANO_CENSO
WHERE f.TP_DIMENSAO IN ({d}) AND di.GRUPO IN
      ('Cogna','Vitru','YDUQS','Cruzeiro do Sul','Ser Educacional','Ânima','Afya')
GROUP BY 1,2 ORDER BY 1,2
""").df()

print("=" * 118)
print("CRESCIMENTO YoY: QT_MAT vs BASE DE ALUNOS (mat + trancados)")
print("Divergencia grande entre as duas colunas = reclassificacao, nao movimento de mercado")
print("=" * 118)
for grupo, g in s.groupby("GRUPO"):
    g = g.sort_values("ANO").reset_index(drop=True)
    print(f"\n--- {grupo}")
    print(f"{'ANO':>5} {'QT_MAT':>11} {'YoY MAT':>9} {'BASE':>11} {'YoY BASE':>9} {'DIVERG.':>9}")
    for i in range(len(g)):
        if i == 0:
            print(f"{g.ANO[i]:>5} {g.MAT[i]:>11,.0f} {'—':>9} {g.BASE[i]:>11,.0f} {'—':>9} {'—':>9}")
            continue
        ym = 100 * (g.MAT[i] - g.MAT[i-1]) / g.MAT[i-1]
        yb = 100 * (g.BASE[i] - g.BASE[i-1]) / g.BASE[i-1]
        flag = " <<<" if abs(ym - yb) > 12 else ""
        print(f"{g.ANO[i]:>5} {g.MAT[i]:>11,.0f} {ym:>+8.1f}% {g.BASE[i]:>11,.0f} {yb:>+8.1f}% "
              f"{ym-yb:>+8.1f}{flag}")

print("\n" + "=" * 118)
print("MARKET SHARE NACIONAL POR GRUPO (base QT_MAT) — 2015 a 2024")
print("=" * 118)
tot = con.sql(f"""SELECT NU_ANO_CENSO ANO, sum(QT_MAT) T FROM f
                  WHERE TP_DIMENSAO IN ({d}) GROUP BY 1""").df().set_index("ANO")["T"]
piv = s.pivot(index="GRUPO", columns="ANO", values="MAT")
sh = (piv.div(tot, axis=1) * 100).round(2)
sh["Δ 15→24"] = (sh[2024] - sh[2015]).round(2)
print(sh.sort_values(2024, ascending=False).to_string())
