"""Grupos deduplicados + checagens finais de qualidade de dados."""
import sys, duckdb, pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 220)
IES = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_ED_SUP_IES_2024.CSV"
CUR = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_CADASTRO_CURSOS_2024.CSV"
XLS = r"C:\education\Suporte IES.xlsx"

sup = pd.read_excel(XLS, sheet_name="Sheet1", header=1)
sup = sup.rename(columns={"IES Code": "CO_IES", "IES": "NO_IES_SUP", "City": "CIDADE_SUP",
                          "State": "UF_SUP", "Company": "GRUPO"})
sup["CO_IES"] = sup["CO_IES"].astype("int64")
sup["GRUPO"] = sup["GRUPO"].astype(str).str.strip()
# checa se algum CO_IES duplicado tem GRUPO divergente
conf = sup.groupby("CO_IES")["GRUPO"].nunique()
print("CO_IES com GRUPO conflitante:", (conf > 1).sum())
sup_d = sup.drop_duplicates(subset=["CO_IES"])[["CO_IES", "GRUPO", "NO_IES_SUP"]]
print(f"Mapeamento deduplicado: {len(sup)} linhas -> {len(sup_d)} IES unicas")

con = duckdb.connect()
con.execute(f"""CREATE TABLE ies AS SELECT * FROM read_csv('{IES}', delim=';', header=true,
            encoding='latin-1', sample_size=-1, null_padding=true);""")
con.execute(f"""CREATE TABLE cur AS SELECT * FROM read_csv('{CUR}', delim=';', header=true,
            encoding='latin-1', sample_size=-1, null_padding=true);""")
con.register("sup", sup_d)

def show(t, sql):
    print("\n" + "=" * 105); print(t); print("=" * 105)
    print(con.sql(sql).df().to_string(index=False))

show("I2) GRUPOS - CONSOLIDADO CORRETO (dedup)", """
WITH m AS (
  SELECT CO_IES, sum(QT_MAT) mat,
         sum(CASE WHEN TP_MODALIDADE_ENSINO=1 THEN QT_MAT ELSE 0 END) presencial,
         sum(CASE WHEN TP_MODALIDADE_ENSINO=2 THEN QT_MAT ELSE 0 END) ead,
         sum(QT_ING) ing, sum(QT_CONC) conc
  FROM cur WHERE TP_DIMENSAO IN (1,2,4) GROUP BY 1),
c AS (SELECT CO_IES, sum(QT_CURSO) cursos FROM cur WHERE TP_DIMENSAO IN (1,3) GROUP BY 1),
u AS (SELECT DISTINCT CO_IES, CO_MUNICIPIO FROM cur WHERE TP_DIMENSAO=1)
SELECT s.GRUPO, count(DISTINCT s.CO_IES) ies,
       sum(m.mat) matriculas, sum(m.presencial) presencial, sum(m.ead) ead,
       sum(m.ing) ingressantes, sum(m.conc) concluintes, sum(c.cursos) cursos,
       (SELECT count(*) FROM u WHERE u.CO_IES IN (SELECT CO_IES FROM sup s2 WHERE s2.GRUPO=s.GRUPO)) AS unidades_presenciais,
       round(100.0*sum(m.mat)/10227266,2) share_nacional_pct
FROM sup s LEFT JOIN m ON m.CO_IES=s.CO_IES LEFT JOIN c ON c.CO_IES=s.CO_IES
GROUP BY 1 ORDER BY matriculas DESC NULLS LAST;
""")

show("K2) COBERTURA CORRETA DO MAPEAMENTO", """
WITH m AS (SELECT CO_IES, sum(QT_MAT) mat FROM cur WHERE TP_DIMENSAO IN (1,2,4) GROUP BY 1)
SELECT sum(m.mat) mat_total,
       sum(CASE WHEN s.CO_IES IS NOT NULL THEN m.mat ELSE 0 END) mat_mapeada,
       round(100.0*sum(CASE WHEN s.CO_IES IS NOT NULL THEN m.mat ELSE 0 END)/sum(m.mat),2) pct_do_total,
       sum(CASE WHEN i.TP_REDE=2 THEN m.mat ELSE 0 END) mat_privada,
       round(100.0*sum(CASE WHEN s.CO_IES IS NOT NULL THEN m.mat ELSE 0 END)
             /sum(CASE WHEN i.TP_REDE=2 THEN m.mat ELSE 0 END),2) pct_da_privada
FROM m JOIN ies i USING (CO_IES) LEFT JOIN sup s ON s.CO_IES=m.CO_IES;
""")

show("N) MANTENEDORA e uma boa chave de grupo? IES mapeadas x mantenedoras", """
SELECT s.GRUPO, count(DISTINCT i.CO_MANTENEDORA) mantenedoras, count(DISTINCT i.CO_IES) ies
FROM sup s JOIN ies i USING (CO_IES) GROUP BY 1 ORDER BY 2 DESC;
""")

show("N2) MANTENEDORAS COMPARTILHADAS ENTRE GRUPOS (risco de mapear por mantenedora)", """
WITH x AS (SELECT i.CO_MANTENEDORA, count(DISTINCT s.GRUPO) g FROM sup s JOIN ies i USING (CO_IES) GROUP BY 1)
SELECT count(*) FILTER (WHERE g>1) AS mantenedoras_em_mais_de_um_grupo, count(*) AS total FROM x;
""")

show("O) CO_MUNICIPIO: formato IBGE (7 digitos)?", """
SELECT length(CAST(CO_MUNICIPIO AS VARCHAR)) AS tamanho, count(*) linhas,
       count(DISTINCT CO_MUNICIPIO) municipios FROM cur WHERE CO_MUNICIPIO IS NOT NULL
GROUP BY 1 ORDER BY 1;
""")

show("O2) NOMES DE MUNICIPIO INCONSISTENTES (mesmo codigo, nomes diferentes)", """
WITH x AS (SELECT CO_MUNICIPIO, count(DISTINCT NO_MUNICIPIO) n FROM cur WHERE CO_MUNICIPIO IS NOT NULL GROUP BY 1)
SELECT count(*) FILTER (WHERE n>1) AS codigos_com_nomes_divergentes, count(*) AS total_municipios FROM x;
""")

show("P) NO_CURSO vs NO_CINE_ROTULO: cardinalidade", """
SELECT count(DISTINCT NO_CURSO) nomes_curso_livres, count(DISTINCT NO_CINE_ROTULO) rotulos_cine,
       count(DISTINCT CO_CINE_ROTULO) codigos_cine, count(DISTINCT NO_CINE_AREA_GERAL) areas_gerais,
       count(DISTINCT NO_CINE_AREA_DETALHADA) areas_detalhadas FROM cur;
""")

show("P2) MEDICINA: quantos NO_CURSO distintos sob o rotulo CINE 'Medicina'", """
SELECT NO_CINE_ROTULO, count(DISTINCT NO_CURSO) variacoes_nome, count(DISTINCT CO_CURSO) cursos,
       sum(QT_MAT) FILTER (WHERE TP_DIMENSAO IN (1,2,4)) mat
FROM cur WHERE NO_CINE_ROTULO IN ('Medicina','Direito','Enfermagem','Administração')
GROUP BY 1 ORDER BY mat DESC;
""")

show("Q) CHECAGEM: presencial + EAD = total; soma UF = Brasil", """
SELECT
 (SELECT sum(QT_MAT) FROM cur WHERE TP_DIMENSAO IN (1,2,4)) AS total,
 (SELECT sum(QT_MAT) FROM cur WHERE TP_DIMENSAO IN (1,2,4) AND TP_MODALIDADE_ENSINO=1) AS presencial,
 (SELECT sum(QT_MAT) FROM cur WHERE TP_DIMENSAO IN (1,2,4) AND TP_MODALIDADE_ENSINO=2) AS ead,
 (SELECT sum(QT_MAT) FROM cur WHERE TP_DIMENSAO IN (1,2,4) AND CO_UF IS NOT NULL) AS soma_com_uf,
 (SELECT sum(QT_MAT) FROM cur WHERE TP_DIMENSAO IN (1,2,4) AND CO_UF IS NULL) AS sem_uf;
""")

show("R) DISTRIBUICAO POR UF (top 10) e REGIAO", """
SELECT NO_REGIAO, sum(QT_MAT) mat FROM cur WHERE TP_DIMENSAO IN (1,2,4)
GROUP BY 1 ORDER BY mat DESC NULLS LAST;
""")

show("S) TAMANHO DAS COLUNAS QT_* (quantas colunas de metrica existem)", """
SELECT count(*) FILTER (WHERE column_name LIKE 'QT_%') AS colunas_qt,
       count(*) FILTER (WHERE column_name LIKE 'TP_%') AS colunas_tp,
       count(*) FILTER (WHERE column_name LIKE 'IN_%') AS colunas_in,
       count(*) AS total FROM information_schema.columns WHERE table_name='cur';
""")
