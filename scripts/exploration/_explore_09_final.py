"""Checagens residuais: inscritos/vagas por dimensao, cursos ABI, deteccao de IES faltantes por mantenedora."""
import sys, duckdb, pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 220)
IES = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_ED_SUP_IES_2024.CSV"
CUR = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_CADASTRO_CURSOS_2024.CSV"
XLS = r"C:\education\Suporte IES.xlsx"

sup = pd.read_excel(XLS, sheet_name="Sheet1", header=1).rename(
    columns={"IES Code": "CO_IES", "Company": "GRUPO"})[["CO_IES", "GRUPO"]].drop_duplicates("CO_IES")

con = duckdb.connect()
con.execute(f"""CREATE TABLE ies AS SELECT * FROM read_csv('{IES}', delim=';', header=true, encoding='latin-1', sample_size=-1, null_padding=true);""")
con.execute(f"""CREATE TABLE cur AS SELECT * FROM read_csv('{CUR}', delim=';', header=true, encoding='latin-1', sample_size=-1, null_padding=true);""")
con.register("sup", sup)

def show(t, sql):
    print("\n" + "=" * 105); print(t); print("=" * 105)
    print(con.sql(sql).df().to_string(index=False))

show("T) VAGAS e INSCRITOS por dimensao (anomalia residual em dim=2?)", """
SELECT TP_DIMENSAO, sum(QT_VG_TOTAL) vagas, sum(QT_INSCRITO_TOTAL) inscritos,
       count(*) FILTER (WHERE QT_VG_TOTAL>0) linhas_com_vaga
FROM cur GROUP BY 1 ORDER BY 1;
""")

show("U) CURSOS ABI (QT_CURSO=0 na dim=1): impacto", """
SELECT count(*) linhas, sum(QT_MAT) mat, sum(QT_ING) ing, sum(QT_CONC) conc,
       round(100.0*sum(QT_MAT)/10227266,3) pct_do_total
FROM cur WHERE TP_DIMENSAO=1 AND QT_CURSO=0;
""")

show("V) IES NAO MAPEADAS QUE COMPARTILHAM MANTENEDORA COM GRUPO CONHECIDO (candidatas a incluir)", """
WITH gm AS (SELECT DISTINCT i.CO_MANTENEDORA, s.GRUPO FROM sup s JOIN ies i USING (CO_IES)),
m AS (SELECT CO_IES, sum(QT_MAT) mat FROM cur WHERE TP_DIMENSAO IN (1,2,4) GROUP BY 1)
SELECT gm.GRUPO, i.CO_IES, i.NO_IES, i.NO_MANTENEDORA, i.SG_UF_IES, m.mat
FROM ies i JOIN gm ON gm.CO_MANTENEDORA = i.CO_MANTENEDORA LEFT JOIN m ON m.CO_IES=i.CO_IES
WHERE i.CO_IES NOT IN (SELECT CO_IES FROM sup)
ORDER BY m.mat DESC NULLS LAST;
""")

show("W) TOP 20 IES DO PAIS (para o snapshot)", """
WITH m AS (SELECT CO_IES, sum(QT_MAT) mat,
           sum(CASE WHEN TP_MODALIDADE_ENSINO=2 THEN QT_MAT ELSE 0 END) ead
           FROM cur WHERE TP_DIMENSAO IN (1,2,4) GROUP BY 1)
SELECT i.CO_IES, i.NO_IES, coalesce(s.GRUPO,'(sem grupo)') grupo, i.TP_REDE, m.mat,
       round(100.0*m.ead/nullif(m.mat,0),1) pct_ead, round(100.0*m.mat/10227266,2) share_pct
FROM m JOIN ies i USING (CO_IES) LEFT JOIN sup s USING (CO_IES)
ORDER BY m.mat DESC LIMIT 20;
""")

show("X) CONCENTRACAO DO MERCADO (todas as IES)", """
WITH m AS (SELECT CO_IES, sum(QT_MAT) mat FROM cur WHERE TP_DIMENSAO IN (1,2,4) GROUP BY 1),
r AS (SELECT CO_IES, mat, row_number() OVER (ORDER BY mat DESC) rk FROM m)
SELECT round(100.0*sum(mat) FILTER (WHERE rk<=3)/10227266,1) top3_ies,
       round(100.0*sum(mat) FILTER (WHERE rk<=5)/10227266,1) top5_ies,
       round(100.0*sum(mat) FILTER (WHERE rk<=10)/10227266,1) top10_ies,
       round(100.0*sum(mat) FILTER (WHERE rk<=20)/10227266,1) top20_ies FROM r;
""")

show("Y) AREAS CINE GERAIS (mix do mercado)", """
SELECT NO_CINE_AREA_GERAL, sum(QT_MAT) mat,
       round(100.0*sum(QT_MAT)/10227266,1) pct,
       round(100.0*sum(CASE WHEN TP_MODALIDADE_ENSINO=2 THEN QT_MAT ELSE 0 END)/nullif(sum(QT_MAT),0),1) pct_ead
FROM cur WHERE TP_DIMENSAO IN (1,2,4) GROUP BY 1 ORDER BY mat DESC;
""")

show("Z) ORGANIZACAO ACADEMICA x matriculas", """
SELECT TP_ORGANIZACAO_ACADEMICA, TP_REDE, sum(QT_MAT) mat, count(DISTINCT CO_IES) ies
FROM cur WHERE TP_DIMENSAO IN (1,2,4) GROUP BY 1,2 ORDER BY 1,2;
""")
