import sys, os, duckdb
sys.path.insert(0, r"C:\education\scripts")
from lib.censo import DIM_ALUNOS
sys.stdout.reconfigure(encoding="utf-8")
PROC = r"C:\education\data_processed"
con = duckdb.connect()
con.execute(f"CREATE VIEW f AS SELECT * FROM read_parquet('{PROC}/fato_cursos_*.parquet');".replace("\\", "/"))
d = ",".join(map(str, DIM_ALUNOS))

print("=== Linhas sem CO_UF por ano (dims de aluno) ===")
print(con.sql(f"""
SELECT NU_ANO_CENSO ANO,
  count(*) FILTER (WHERE CO_UF IS NULL) linhas_sem_uf,
  sum(QT_MAT) FILTER (WHERE CO_UF IS NULL) mat_sem_uf,
  count(*) FILTER (WHERE CO_UF IS NOT NULL) linhas_com_uf,
  sum(QT_MAT) FILTER (WHERE CO_UF IS NOT NULL) mat_com_uf,
  sum(QT_MAT) total
FROM f WHERE TP_DIMENSAO IN ({d}) GROUP BY 1 ORDER BY 1""").df().to_string(index=False))

print("\n=== Distribuicao de TP_DIMENSAO x CO_UF nulo, por ano ===")
print(con.sql(f"""
SELECT NU_ANO_CENSO ANO, TP_DIMENSAO,
  count(*) linhas, count(*) FILTER (WHERE CO_UF IS NULL) sem_uf, sum(QT_MAT) mat
FROM f GROUP BY 1,2 ORDER BY 1,2""").df().to_string(index=False))
