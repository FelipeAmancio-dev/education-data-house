"""Impacto de usar QT_MAT vs QT_MAT+trancados ('base de alunos') no market share."""
import sys, duckdb, pandas as pd
sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 250)
CUR = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_CADASTRO_CURSOS_2024.CSV"
O = "delim=';', header=true, encoding='latin-1', sample_size=-1, null_padding=true"
con = duckdb.connect()
con.execute(f"CREATE TABLE cur AS SELECT * FROM read_csv('{CUR}', {O});")
mp = pd.read_csv(r"C:\education\config\ies_grupo_map.csv", sep=";", encoding="utf-8-sig")
mp["GRUPO"] = mp["GRUPO"].fillna("")
con.register("mp", mp[["CO_IES", "GRUPO"]])

print(con.sql("""
WITH t AS (SELECT sum(QT_MAT) m, sum(QT_MAT+coalesce(QT_SIT_TRANCADA,0)) b
           FROM cur WHERE TP_DIMENSAO IN (1,2,4)),
g AS (SELECT CASE WHEN mp.GRUPO='' THEN '(nao mapeado)' ELSE mp.GRUPO END grupo,
             sum(c.QT_MAT) mat,
             sum(c.QT_MAT+coalesce(c.QT_SIT_TRANCADA,0)) base,
             sum(coalesce(c.QT_SIT_TRANCADA,0)) tranc
      FROM cur c JOIN mp ON mp.CO_IES=c.CO_IES
      WHERE c.TP_DIMENSAO IN (1,2,4) GROUP BY 1)
SELECT grupo, mat, base, tranc,
       round(100.0*tranc/nullif(mat,0),1) AS tranc_pct,
       round(100.0*mat/(SELECT m FROM t),2)  AS share_qt_mat,
       round(100.0*base/(SELECT b FROM t),2) AS share_base,
       round(100.0*base/(SELECT b FROM t) - 100.0*mat/(SELECT m FROM t),2) AS delta_pp
FROM g WHERE mat > 150000 OR grupo='FMU' ORDER BY mat DESC;
""").df().to_string(index=False))

print("\n--- Totais de referencia ---")
print(con.sql("""SELECT sum(QT_MAT) qt_mat_brasil,
 sum(QT_MAT+coalesce(QT_SIT_TRANCADA,0)) base_brasil,
 sum(coalesce(QT_SIT_TRANCADA,0)) trancados_brasil
 FROM cur WHERE TP_DIMENSAO IN (1,2,4);""").df().to_string(index=False))

print("\n--- YDUQS: as IES com maior taxa de trancamento ---")
print(con.sql("""
SELECT c.CO_IES, sum(c.QT_MAT) mat, sum(coalesce(c.QT_SIT_TRANCADA,0)) tranc,
       round(100.0*sum(coalesce(c.QT_SIT_TRANCADA,0))/nullif(sum(c.QT_MAT),0),1) pct
FROM cur c JOIN mp ON mp.CO_IES=c.CO_IES
WHERE mp.GRUPO='YDUQS' AND c.TP_DIMENSAO IN (1,2,4)
GROUP BY 1 HAVING sum(c.QT_MAT)>3000 ORDER BY pct DESC LIMIT 10;
""").df().to_string(index=False))
