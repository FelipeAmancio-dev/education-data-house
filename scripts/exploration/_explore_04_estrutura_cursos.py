"""Valida empiricamente a granularidade da base CURSOS: TP_DIMENSAO, chaves e duplicidades."""
import sys, duckdb

sys.stdout.reconfigure(encoding="utf-8")
CSV = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_CADASTRO_CURSOS_2024.CSV"

con = duckdb.connect()
con.execute("SET preserve_insertion_order=false;")
READ = (f"read_csv('{CSV}', delim=';', header=true, encoding='latin-1', "
        f"sample_size=-1, ignore_errors=false, null_padding=true)")

print("Carregando CSV em tabela temporaria (DuckDB)...")
con.execute(f"CREATE TABLE cursos AS SELECT * FROM {READ};")
n = con.sql("SELECT count(*) FROM cursos").fetchone()[0]
print(f"LINHAS TOTAIS: {n:,}")

def show(title, sql):
    print("\n" + "=" * 100)
    print(title)
    print("=" * 100)
    print(con.sql(sql).df().to_string(index=False))

show("1) DISTRIBUICAO POR TP_DIMENSAO (linhas e somas)", """
SELECT TP_DIMENSAO,
       count(*)                       AS linhas,
       count(DISTINCT CO_CURSO)       AS cursos_distintos,
       count(DISTINCT CO_IES)         AS ies_distintas,
       sum(QT_CURSO)                  AS soma_qt_curso,
       sum(QT_VG_TOTAL)               AS soma_vagas,
       sum(QT_ING)                    AS soma_ingressantes,
       sum(QT_MAT)                    AS soma_matriculas,
       sum(QT_CONC)                   AS soma_concluintes
FROM cursos GROUP BY 1 ORDER BY 1;
""")

show("2) TP_DIMENSAO x TP_MODALIDADE_ENSINO", """
SELECT TP_DIMENSAO, TP_MODALIDADE_ENSINO, count(*) AS linhas,
       count(DISTINCT CO_CURSO) AS cursos, sum(QT_MAT) AS matriculas,
       sum(CASE WHEN NO_MUNICIPIO IS NULL THEN 1 ELSE 0 END) AS linhas_sem_municipio
FROM cursos GROUP BY 1,2 ORDER BY 1,2;
""")

show("3) SOBREPOSICAO: o mesmo CO_CURSO aparece em quais dimensoes?", """
WITH d AS (SELECT CO_CURSO, list_sort(list(DISTINCT TP_DIMENSAO)) AS dims FROM cursos GROUP BY 1)
SELECT dims, count(*) AS qt_cursos FROM d GROUP BY 1 ORDER BY qt_cursos DESC;
""")

show("4) CHAVE CANDIDATA: (CO_CURSO, TP_DIMENSAO, CO_MUNICIPIO) e unicidade de CO_CURSO", """
SELECT
 (SELECT count(*) FROM cursos)                                                     AS linhas,
 (SELECT count(*) FROM (SELECT DISTINCT CO_CURSO) t)                               AS dist_co_curso,
 (SELECT count(*) FROM (SELECT DISTINCT CO_CURSO,TP_DIMENSAO) t)                   AS dist_curso_dim,
 (SELECT count(*) FROM (SELECT DISTINCT CO_CURSO,TP_DIMENSAO,CO_MUNICIPIO) t)      AS dist_curso_dim_mun,
 (SELECT count(*) FROM (SELECT DISTINCT CO_IES,CO_CURSO) t)                        AS dist_ies_curso;
""")

show("5) CO_CURSO em mais de uma IES? (teste de unicidade global)", """
WITH x AS (SELECT CO_CURSO, count(DISTINCT CO_IES) AS n_ies FROM cursos GROUP BY 1)
SELECT n_ies, count(*) AS qt_cursos FROM x GROUP BY 1 ORDER BY 1;
""")

show("6) DIM=1 (presencial): um curso pode ter varios municipios?", """
WITH x AS (SELECT CO_CURSO, count(DISTINCT CO_MUNICIPIO) AS n_mun, count(*) AS n_linhas
           FROM cursos WHERE TP_DIMENSAO=1 GROUP BY 1)
SELECT n_mun, count(*) AS qt_cursos, sum(n_linhas) AS linhas FROM x GROUP BY 1 ORDER BY 1 LIMIT 15;
""")

show("7) DIM=2 (EAD no Brasil): municipios por curso", """
WITH x AS (SELECT CO_CURSO, count(DISTINCT CO_MUNICIPIO) AS n_mun FROM cursos WHERE TP_DIMENSAO=2 GROUP BY 1)
SELECT min(n_mun) AS min_mun, max(n_mun) AS max_mun, avg(n_mun) AS media_mun, count(*) AS cursos FROM x;
""")

show("8) EXEMPLO CONCRETO: um curso EAD grande em todas as dimensoes", """
WITH alvo AS (SELECT CO_CURSO FROM cursos WHERE TP_DIMENSAO=3 ORDER BY QT_MAT DESC LIMIT 1)
SELECT TP_DIMENSAO, count(*) AS linhas, sum(QT_CURSO) AS qt_curso, sum(QT_VG_TOTAL) AS vagas,
       sum(QT_ING) AS ing, sum(QT_MAT) AS mat, sum(QT_CONC) AS conc
FROM cursos WHERE CO_CURSO IN (SELECT CO_CURSO FROM alvo) GROUP BY 1 ORDER BY 1;
""")

show("9) MESMO EXEMPLO: identificacao do curso", """
WITH alvo AS (SELECT CO_CURSO FROM cursos WHERE TP_DIMENSAO=3 ORDER BY QT_MAT DESC LIMIT 1)
SELECT DISTINCT CO_IES, CO_CURSO, NO_CURSO, NO_CINE_ROTULO, TP_MODALIDADE_ENSINO, TP_GRAU_ACADEMICO
FROM cursos WHERE CO_CURSO IN (SELECT CO_CURSO FROM alvo);
""")

show("10) TP_NIVEL_ACADEMICO x TP_MODALIDADE (matriculas) - dim 1 e 3", """
SELECT TP_NIVEL_ACADEMICO, TP_MODALIDADE_ENSINO, count(*) AS linhas, sum(QT_MAT) AS mat
FROM cursos WHERE TP_DIMENSAO IN (1,3) GROUP BY 1,2 ORDER BY 1,2;
""")

con.execute("EXPORT DATABASE '__none__'") if False else None
