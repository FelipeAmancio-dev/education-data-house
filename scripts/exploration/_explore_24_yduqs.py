"""Reconciliacao YDUQS: Censo 2024 vs numero reportado pela companhia."""
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
    print("\n" + "=" * 105); print(t); print("=" * 105)
    print(con.sql(sql).df().to_string(index=False))

show("1) YDUQS hoje: total por modalidade", """
SELECT count(DISTINCT c.CO_IES) ies,
 sum(c.QT_MAT) FILTER (WHERE c.TP_MODALIDADE_ENSINO=1) presencial,
 sum(c.QT_MAT) FILTER (WHERE c.TP_MODALIDADE_ENSINO=2) ead,
 sum(c.QT_MAT) total
FROM cur c JOIN mp ON mp.CO_IES=c.CO_IES
WHERE mp.GRUPO='YDUQS' AND c.TP_DIMENSAO IN (1,2,4);
""")

show("2) H1 - IES com marca YDUQS que NAO estao mapeadas", """
WITH m AS (SELECT CO_IES, sum(QT_MAT) mat FROM cur WHERE TP_DIMENSAO IN (1,2,4) GROUP BY 1)
SELECT i.CO_IES, i.NO_IES, i.CO_MANTENEDORA, i.NO_MANTENEDORA, i.SG_UF_IES, coalesce(m.mat,0) mat
FROM ies i LEFT JOIN m USING (CO_IES) JOIN mp ON mp.CO_IES=i.CO_IES
WHERE mp.GRUPO<>'YDUQS' AND (
  upper(i.NO_IES) LIKE '%ESTACIO%' OR upper(i.NO_IES) LIKE '%ESTÁCIO%'
  OR upper(i.NO_IES) LIKE '%IBMEC%' OR upper(i.NO_IES) LIKE '%WYDEN%'
  OR upper(i.NO_IES) LIKE '%DAMASIO%' OR upper(i.NO_IES) LIKE '%DAMÁSIO%'
  OR upper(i.NO_MANTENEDORA) LIKE '%ESTACIO%' OR upper(i.NO_MANTENEDORA) LIKE '%YDUQS%'
  OR upper(i.NO_MANTENEDORA) LIKE '%IBMEC%')
ORDER BY mat DESC;
""")

show("3) H1b - IES nao mapeadas sob mantenedora que ja e YDUQS", """
WITH m AS (SELECT CO_IES, sum(QT_MAT) mat FROM cur WHERE TP_DIMENSAO IN (1,2,4) GROUP BY 1),
gm AS (SELECT DISTINCT i.CO_MANTENEDORA FROM ies i JOIN mp ON mp.CO_IES=i.CO_IES WHERE mp.GRUPO='YDUQS')
SELECT i.CO_IES, i.NO_IES, i.NO_MANTENEDORA, coalesce(m.mat,0) mat
FROM ies i JOIN gm USING (CO_MANTENEDORA) JOIN mp ON mp.CO_IES=i.CO_IES
LEFT JOIN m ON m.CO_IES=i.CO_IES WHERE mp.GRUPO<>'YDUQS' ORDER BY mat DESC;
""")

show("4) H3 - alunos fora de QT_MAT: trancados, desvinculados, transferidos", """
SELECT sum(c.QT_MAT) matriculas_censo, sum(c.QT_SIT_TRANCADA) trancados,
       sum(c.QT_SIT_DESVINCULADO) desvinculados, sum(c.QT_SIT_TRANSFERIDO) transferidos,
       sum(c.QT_MAT + coalesce(c.QT_SIT_TRANCADA,0)) mat_mais_trancados
FROM cur c JOIN mp ON mp.CO_IES=c.CO_IES
WHERE mp.GRUPO='YDUQS' AND c.TP_DIMENSAO IN (1,2,4);
""")

show("5) YDUQS: as 20 maiores IES do grupo", """
WITH m AS (SELECT c.CO_IES, sum(c.QT_MAT) mat,
  sum(c.QT_MAT) FILTER (WHERE c.TP_MODALIDADE_ENSINO=1) pres,
  sum(c.QT_MAT) FILTER (WHERE c.TP_MODALIDADE_ENSINO=2) ead
  FROM cur c WHERE c.TP_DIMENSAO IN (1,2,4) GROUP BY 1)
SELECT i.CO_IES, substr(i.NO_IES,1,48) NO_IES, i.SG_UF_IES, m.mat, m.pres, m.ead
FROM m JOIN ies i USING (CO_IES) JOIN mp ON mp.CO_IES=i.CO_IES
WHERE mp.GRUPO='YDUQS' ORDER BY m.mat DESC LIMIT 20;
""")

show("6) H2 - o que o Censo cobre: nivel academico de TODA a base", """
SELECT TP_NIVEL_ACADEMICO, count(*) linhas, sum(QT_MAT) matriculas
FROM cur WHERE TP_DIMENSAO IN (1,2,4) GROUP BY 1 ORDER BY 1;
""")

show("7) Contexto: EAD do Brasil e share dos 3 maiores", """
WITH g AS (SELECT mp.GRUPO, sum(c.QT_MAT) FILTER (WHERE c.TP_MODALIDADE_ENSINO=2) ead
           FROM cur c JOIN mp ON mp.CO_IES=c.CO_IES
           WHERE c.TP_DIMENSAO IN (1,2,4) AND mp.GRUPO<>'' GROUP BY 1)
SELECT GRUPO, ead, round(100.0*ead/5189391,1) pct_do_ead_br FROM g ORDER BY ead DESC LIMIT 6;
""")
