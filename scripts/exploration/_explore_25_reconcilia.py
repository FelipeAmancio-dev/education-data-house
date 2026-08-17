"""Reconciliacao detalhada YDUQS por modalidade + checagem da FMU."""
import sys, duckdb, pandas as pd
sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
IES = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_ED_SUP_IES_2024.CSV"
CUR = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_CADASTRO_CURSOS_2024.CSV"
O = "delim=';', header=true, encoding='latin-1', sample_size=-1, null_padding=true"
con = duckdb.connect()
con.execute(f"CREATE TABLE ies AS SELECT * FROM read_csv('{IES}', {O});")
con.execute(f"CREATE TABLE cur AS SELECT * FROM read_csv('{CUR}', {O});")
mp = pd.read_csv(r"C:\education\config\ies_grupo_map.csv", sep=";", encoding="utf-8-sig")
mp["GRUPO"] = mp["GRUPO"].fillna("")
con.register("mp", mp[["CO_IES", "GRUPO"]])

def show(t, sql):
    print("\n" + "=" * 108); print(t); print("=" * 108)
    print(con.sql(sql).df().to_string(index=False))

show("A) QT_SIT_* por TP_DIMENSAO - o campo e valido em quais dimensoes?", """
SELECT TP_DIMENSAO, count(*) linhas, sum(QT_MAT) mat, sum(QT_SIT_TRANCADA) trancada,
       sum(QT_SIT_DESVINCULADO) desvinculado, sum(QT_SIT_TRANSFERIDO) transferido
FROM cur GROUP BY 1 ORDER BY 1;
""")

show("B) YDUQS - reconciliacao por modalidade", """
SELECT CASE c.TP_MODALIDADE_ENSINO WHEN 1 THEN 'Presencial' ELSE 'EAD' END modalidade,
       sum(c.QT_MAT) mat_censo,
       sum(c.QT_SIT_TRANCADA) trancados,
       sum(c.QT_MAT + coalesce(c.QT_SIT_TRANCADA,0)) mat_mais_trancados,
       sum(c.QT_SIT_DESVINCULADO) desvinculados
FROM cur c JOIN mp ON mp.CO_IES=c.CO_IES
WHERE mp.GRUPO='YDUQS' AND c.TP_DIMENSAO IN (1,2,4) GROUP BY 1 ORDER BY 1;
""")

show("C) Mesma conta para os 3 maiores grupos (o padrao se repete?)", """
SELECT mp.GRUPO,
 sum(c.QT_MAT) FILTER (WHERE c.TP_MODALIDADE_ENSINO=1) pres,
 sum(c.QT_MAT+coalesce(c.QT_SIT_TRANCADA,0)) FILTER (WHERE c.TP_MODALIDADE_ENSINO=1) pres_c_tranc,
 sum(c.QT_MAT) FILTER (WHERE c.TP_MODALIDADE_ENSINO=2) ead,
 sum(c.QT_MAT+coalesce(c.QT_SIT_TRANCADA,0)) FILTER (WHERE c.TP_MODALIDADE_ENSINO=2) ead_c_tranc,
 round(100.0*sum(c.QT_SIT_TRANCADA)/sum(c.QT_MAT),1) tranc_pct_da_mat
FROM cur c JOIN mp ON mp.CO_IES=c.CO_IES
WHERE mp.GRUPO IN ('YDUQS','Cogna','Vitru','Cruzeiro do Sul','Ânima','Ser Educacional')
  AND c.TP_DIMENSAO IN (1,2,4) GROUP BY 1 ORDER BY ead DESC;
""")

show("D) Brasil: trancados no total", """
SELECT sum(QT_MAT) mat, sum(QT_SIT_TRANCADA) trancados,
       round(100.0*sum(QT_SIT_TRANCADA)/sum(QT_MAT),1) pct
FROM cur WHERE TP_DIMENSAO IN (1,2,4);
""")

show("E) FMU - composicao atual", """
WITH m AS (SELECT c.CO_IES, sum(c.QT_MAT) mat,
  sum(c.QT_MAT) FILTER (WHERE c.TP_MODALIDADE_ENSINO=1) pres,
  sum(c.QT_MAT) FILTER (WHERE c.TP_MODALIDADE_ENSINO=2) ead,
  sum(c.QT_SIT_TRANCADA) tranc
  FROM cur c WHERE c.TP_DIMENSAO IN (1,2,4) GROUP BY 1)
SELECT i.CO_IES, i.NO_IES, i.CO_MANTENEDORA, i.NO_MANTENEDORA, i.SG_UF_IES,
       m.mat, m.pres, m.ead, m.tranc
FROM m JOIN ies i USING (CO_IES) JOIN mp ON mp.CO_IES=i.CO_IES
WHERE mp.GRUPO='FMU' ORDER BY m.mat DESC;
""")

show("F) FMU - existe alguma IES com marca FMU/FIAM/FAAM fora do grupo?", """
WITH m AS (SELECT CO_IES, sum(QT_MAT) mat FROM cur WHERE TP_DIMENSAO IN (1,2,4) GROUP BY 1)
SELECT i.CO_IES, i.NO_IES, i.CO_MANTENEDORA, i.NO_MANTENEDORA, i.SG_UF_IES,
       coalesce(m.mat,0) mat, mp.GRUPO
FROM ies i LEFT JOIN m USING (CO_IES) JOIN mp ON mp.CO_IES=i.CO_IES
WHERE upper(i.NO_IES) LIKE '%METROPOLITANAS UNIDAS%' OR upper(i.NO_IES) LIKE '%FIAM%'
   OR upper(i.NO_IES) LIKE '%FAAM%' OR upper(i.NO_IES) LIKE '%FMU%'
   OR upper(i.NO_MANTENEDORA) LIKE '%METROPOLITANAS UNIDAS%'
ORDER BY mat DESC;
""")

show("G) Anima + FMU consolidados", """
SELECT
 sum(c.QT_MAT) FILTER (WHERE mp.GRUPO='Ânima') anima,
 sum(c.QT_MAT) FILTER (WHERE mp.GRUPO='FMU') fmu,
 sum(c.QT_MAT) FILTER (WHERE mp.GRUPO IN ('Ânima','FMU')) consolidado,
 sum(c.QT_MAT+coalesce(c.QT_SIT_TRANCADA,0)) FILTER (WHERE mp.GRUPO IN ('Ânima','FMU')) consol_c_tranc
FROM cur c JOIN mp ON mp.CO_IES=c.CO_IES WHERE c.TP_DIMENSAO IN (1,2,4);
""")
