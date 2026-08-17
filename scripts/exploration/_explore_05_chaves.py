"""Aprofunda: chaves, nulos, QT_CURSO=0, geografia EAD, niveis academicos."""
import sys, duckdb

sys.stdout.reconfigure(encoding="utf-8")
CSV = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_CADASTRO_CURSOS_2024.CSV"
con = duckdb.connect()
con.execute("SET preserve_insertion_order=false;")
con.execute(f"""CREATE TABLE cursos AS SELECT * FROM read_csv('{CSV}', delim=';', header=true,
            encoding='latin-1', sample_size=-1, null_padding=true);""")

def show(t, sql):
    print("\n" + "=" * 100); print(t); print("=" * 100)
    print(con.sql(sql).df().to_string(index=False))

show("4) UNICIDADE DE CHAVES", """
SELECT (SELECT count(*) FROM cursos) AS linhas,
       (SELECT count(DISTINCT CO_CURSO) FROM cursos) AS dist_co_curso,
       (SELECT count(*) FROM (SELECT DISTINCT CO_CURSO,TP_DIMENSAO FROM cursos)) AS dist_curso_dim,
       (SELECT count(*) FROM (SELECT DISTINCT CO_CURSO,TP_DIMENSAO,CO_MUNICIPIO FROM cursos)) AS dist_curso_dim_mun,
       (SELECT count(*) FROM (SELECT DISTINCT CO_IES,CO_CURSO FROM cursos)) AS dist_ies_curso,
       (SELECT count(DISTINCT CO_IES) FROM cursos) AS dist_ies;
""")

show("5) CO_CURSO pertence a quantas IES?", """
WITH x AS (SELECT CO_CURSO, count(DISTINCT CO_IES) n FROM cursos GROUP BY 1)
SELECT n AS ies_por_curso, count(*) AS qt_cursos FROM x GROUP BY 1 ORDER BY 1;
""")

show("6) DIM=1: linhas com QT_CURSO=0 (o que sao?)", """
SELECT QT_CURSO, count(*) AS linhas, sum(QT_MAT) AS mat, sum(QT_ING) AS ing, sum(QT_VG_TOTAL) AS vagas
FROM cursos WHERE TP_DIMENSAO=1 GROUP BY 1 ORDER BY 1;
""")

show("6b) DIM=1 QT_CURSO=0: exemplos", """
SELECT NO_IES_X AS _ , * EXCLUDE(NO_IES_X) FROM (
 SELECT NULL AS NO_IES_X, CO_IES, CO_CURSO, NO_CURSO, TP_GRAU_ACADEMICO, TP_NIVEL_ACADEMICO,
        QT_CURSO, QT_VG_TOTAL, QT_MAT, QT_ING, QT_CONC
 FROM cursos WHERE TP_DIMENSAO=1 AND QT_CURSO=0 LIMIT 12);
""")

show("7) GEOGRAFIA EAD (dim=2): quantos municipios distintos", """
SELECT count(DISTINCT CO_MUNICIPIO) AS municipios_ead,
       (SELECT count(DISTINCT CO_MUNICIPIO) FROM cursos WHERE TP_DIMENSAO=1) AS municipios_presencial,
       (SELECT count(DISTINCT CO_MUNICIPIO) FROM cursos) AS municipios_total
FROM cursos WHERE TP_DIMENSAO=2;
""")

show("7b) DIM=2: municipios por curso (distribuicao)", """
WITH x AS (SELECT CO_CURSO, count(DISTINCT CO_MUNICIPIO) n FROM cursos WHERE TP_DIMENSAO=2 GROUP BY 1)
SELECT min(n) mn, max(n) mx, round(avg(n),1) media, median(n) mediana, count(*) cursos FROM x;
""")

show("7c) DIM=2: linhas com QT_MAT=0 ou nulo (ruido?)", """
SELECT CASE WHEN QT_MAT IS NULL THEN 'NULL' WHEN QT_MAT=0 THEN 'zero' ELSE 'positivo' END AS status,
       count(*) AS linhas, sum(QT_MAT) AS mat, sum(QT_ING) AS ing, sum(QT_CONC) AS conc
FROM cursos WHERE TP_DIMENSAO=2 GROUP BY 1 ORDER BY 1;
""")

show("8) TOTAIS CORRETOS PROPOSTOS (dims 1,2,4 p/ alunos | dims 1,3 p/ cursos e vagas)", """
SELECT
 (SELECT sum(QT_MAT)  FROM cursos WHERE TP_DIMENSAO IN (1,2,4)) AS matriculas_total,
 (SELECT sum(QT_ING)  FROM cursos WHERE TP_DIMENSAO IN (1,2,4)) AS ingressantes_total,
 (SELECT sum(QT_CONC) FROM cursos WHERE TP_DIMENSAO IN (1,2,4)) AS concluintes_total,
 (SELECT sum(QT_CURSO)FROM cursos WHERE TP_DIMENSAO IN (1,3))   AS cursos_total,
 (SELECT sum(QT_VG_TOTAL) FROM cursos WHERE TP_DIMENSAO IN (1,3)) AS vagas_total;
""")

show("8b) MATRICULAS POR MODALIDADE E REDE", """
SELECT TP_MODALIDADE_ENSINO, TP_REDE, sum(QT_MAT) AS mat, sum(QT_ING) AS ing, sum(QT_CONC) AS conc
FROM cursos WHERE TP_DIMENSAO IN (1,2,4) GROUP BY 1,2 ORDER BY 1,2;
""")

show("10) NIVEL ACADEMICO x MODALIDADE (alunos: dims 1,2,4)", """
SELECT TP_NIVEL_ACADEMICO, TP_MODALIDADE_ENSINO, count(*) linhas, sum(QT_MAT) mat
FROM cursos WHERE TP_DIMENSAO IN (1,2,4) GROUP BY 1,2 ORDER BY 1,2;
""")

show("11) GRAU ACADEMICO (dims 1,2,4)", """
SELECT TP_GRAU_ACADEMICO, count(*) linhas, sum(QT_MAT) mat FROM cursos
WHERE TP_DIMENSAO IN (1,2,4) GROUP BY 1 ORDER BY 1;
""")

show("12) PROXY DE CAMPUS: pares distintos (CO_IES, CO_MUNICIPIO) no presencial", """
SELECT count(*) AS unidades_presenciais FROM (
  SELECT DISTINCT CO_IES, CO_MUNICIPIO FROM cursos WHERE TP_DIMENSAO=1);
""")

show("13) NULOS EM COLUNAS-CHAVE", """
SELECT
 sum(CASE WHEN CO_IES IS NULL THEN 1 ELSE 0 END) AS null_co_ies,
 sum(CASE WHEN CO_CURSO IS NULL THEN 1 ELSE 0 END) AS null_co_curso,
 sum(CASE WHEN CO_MUNICIPIO IS NULL THEN 1 ELSE 0 END) AS null_municipio,
 sum(CASE WHEN NO_CINE_ROTULO IS NULL THEN 1 ELSE 0 END) AS null_cine_rotulo,
 sum(CASE WHEN TP_GRAU_ACADEMICO IS NULL THEN 1 ELSE 0 END) AS null_grau,
 sum(CASE WHEN QT_MAT IS NULL THEN 1 ELSE 0 END) AS null_qt_mat
FROM cursos;
""")

show("14) TOP 15 CINE ROTULO por matriculas (dims 1,2,4)", """
SELECT NO_CINE_ROTULO, sum(QT_MAT) AS mat,
       sum(CASE WHEN TP_MODALIDADE_ENSINO=1 THEN QT_MAT ELSE 0 END) AS presencial,
       sum(CASE WHEN TP_MODALIDADE_ENSINO=2 THEN QT_MAT ELSE 0 END) AS ead
FROM cursos WHERE TP_DIMENSAO IN (1,2,4) GROUP BY 1 ORDER BY mat DESC LIMIT 15;
""")
