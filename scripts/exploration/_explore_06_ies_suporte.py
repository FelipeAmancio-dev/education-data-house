"""Explora MICRODADOS_ED_SUP_IES_2024 e o arquivo Suporte IES.xlsx."""
import sys, duckdb, openpyxl

sys.stdout.reconfigure(encoding="utf-8")
IES = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_ED_SUP_IES_2024.CSV"
CUR = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_CADASTRO_CURSOS_2024.CSV"
XLS = r"C:\education\Suporte IES.xlsx"

con = duckdb.connect()
con.execute(f"""CREATE TABLE ies AS SELECT * FROM read_csv('{IES}', delim=';', header=true,
            encoding='latin-1', sample_size=-1, null_padding=true);""")
con.execute(f"""CREATE TABLE cur AS SELECT CO_IES, TP_DIMENSAO, CO_MUNICIPIO, QT_MAT
            FROM read_csv('{CUR}', delim=';', header=true, encoding='latin-1', sample_size=-1, null_padding=true);""")

def show(t, sql):
    print("\n" + "=" * 100); print(t); print("=" * 100)
    print(con.sql(sql).df().to_string(index=False))

show("A) IES: volumetria e unicidade", """
SELECT count(*) linhas, count(DISTINCT CO_IES) ies, count(DISTINCT CO_MANTENEDORA) mantenedoras,
       count(DISTINCT NO_MANTENEDORA) nomes_mantenedora, min(NU_ANO_CENSO) ano_min, max(NU_ANO_CENSO) ano_max
FROM ies;
""")

show("B) IES: rede x organizacao academica", """
SELECT TP_REDE, TP_ORGANIZACAO_ACADEMICA, count(*) qt FROM ies GROUP BY 1,2 ORDER BY 1,2;
""")

show("C) MANTENEDORA: quantas IES por mantenedora (top 20)", """
SELECT CO_MANTENEDORA, any_value(NO_MANTENEDORA) AS nome, count(*) AS qt_ies
FROM ies GROUP BY 1 ORDER BY qt_ies DESC LIMIT 20;
""")

show("D) COBERTURA: CO_IES em cursos vs cadastro IES", """
SELECT
 (SELECT count(DISTINCT CO_IES) FROM cur) AS ies_em_cursos,
 (SELECT count(DISTINCT CO_IES) FROM ies) AS ies_em_cadastro,
 (SELECT count(*) FROM (SELECT DISTINCT CO_IES FROM cur WHERE CO_IES NOT IN (SELECT CO_IES FROM ies))) AS em_cursos_sem_cadastro,
 (SELECT count(*) FROM ies WHERE CO_IES NOT IN (SELECT DISTINCT CO_IES FROM cur)) AS em_cadastro_sem_cursos;
""")

show("E) NULOS relevantes no cadastro IES", """
SELECT sum(CASE WHEN NO_MANTENEDORA IS NULL THEN 1 ELSE 0 END) null_no_mant,
       sum(CASE WHEN CO_MANTENEDORA IS NULL THEN 1 ELSE 0 END) null_co_mant,
       sum(CASE WHEN SG_IES IS NULL THEN 1 ELSE 0 END) null_sigla,
       sum(CASE WHEN DS_ENDERECO_IES IS NULL THEN 1 ELSE 0 END) null_endereco,
       sum(CASE WHEN NU_CEP_IES IS NULL THEN 1 ELSE 0 END) null_cep
FROM ies;
""")

show("F) EXISTE LATITUDE/LONGITUDE? (colunas do cadastro IES)", """
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name='ies' AND (lower(column_name) LIKE '%lat%' OR lower(column_name) LIKE '%lon%'
      OR lower(column_name) LIKE '%geo%' OR lower(column_name) LIKE '%end%' OR lower(column_name) LIKE '%cep%');
""")

show("G) TOP 15 IES por matriculas (join cursos x ies)", """
SELECT c.CO_IES, i.NO_IES, i.SG_IES, i.NO_MANTENEDORA, i.TP_REDE, sum(c.QT_MAT) AS mat
FROM cur c LEFT JOIN ies i USING (CO_IES)
WHERE c.TP_DIMENSAO IN (1,2,4) GROUP BY 1,2,3,4,5 ORDER BY mat DESC LIMIT 15;
""")

# ---------------- Suporte IES.xlsx ----------------
print("\n" + "#" * 100)
print("### ARQUIVO Suporte IES.xlsx")
print("#" * 100)
wb = openpyxl.load_workbook(XLS, data_only=True)
print("ABAS:", wb.sheetnames)
for ws in wb.worksheets:
    print(f"\n--- ABA '{ws.title}' dims={ws.dimensions} max_row={ws.max_row} max_col={ws.max_column}")
    for i, row in enumerate(ws.iter_rows(values_only=True), 1):
        cells = ["" if c is None else str(c)[:60] for c in row]
        if any(cells):
            print(f"  {i:4d}: " + " | ".join(cells))
        if i > 60:
            print(f"  ... (total {ws.max_row} linhas)")
            break
