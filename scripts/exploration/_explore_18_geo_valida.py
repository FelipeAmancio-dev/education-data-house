"""Valida cobertura dos centroides contra os municipios com oferta no Censo."""
import sys, duckdb, pandas as pd
sys.stdout.reconfigure(encoding="utf-8")
CUR = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_CADASTRO_CURSOS_2024.CSV"
O = "delim=';', header=true, encoding='latin-1', sample_size=-1, null_padding=true"
geo = pd.read_csv(r"C:\education\config\municipios_ibge.csv", sep=";", encoding="utf-8-sig")
con = duckdb.connect()
con.execute(f"CREATE TABLE cur AS SELECT * FROM read_csv('{CUR}', {O});")
con.register("geo", geo)

print(con.sql("""
SELECT
 (SELECT count(DISTINCT CO_MUNICIPIO) FROM cur WHERE CO_MUNICIPIO IS NOT NULL) AS munic_no_censo,
 (SELECT count(DISTINCT c.CO_MUNICIPIO) FROM cur c JOIN geo g ON g.CO_MUNICIPIO=c.CO_MUNICIPIO
   WHERE g.LATITUDE IS NOT NULL) AS com_coordenada,
 (SELECT count(DISTINCT c.CO_MUNICIPIO) FROM cur c LEFT JOIN geo g ON g.CO_MUNICIPIO=c.CO_MUNICIPIO
   WHERE g.CO_MUNICIPIO IS NULL) AS sem_correspondencia;
""").df().to_string(index=False))

print("\n--- Cobertura por tipo de oferta ---")
print(con.sql("""
SELECT CASE c.TP_DIMENSAO WHEN 1 THEN '1 presencial' WHEN 2 THEN '2 EAD' ELSE 'outras' END dim,
       count(DISTINCT c.CO_MUNICIPIO) municipios,
       count(DISTINCT CASE WHEN g.LATITUDE IS NOT NULL THEN c.CO_MUNICIPIO END) com_coord,
       sum(c.QT_MAT) matriculas
FROM cur c LEFT JOIN geo g ON g.CO_MUNICIPIO=c.CO_MUNICIPIO
WHERE c.CO_MUNICIPIO IS NOT NULL AND c.TP_DIMENSAO IN (1,2) GROUP BY 1 ORDER BY 1;
""").df().to_string(index=False))

print("\n--- Amostra: maiores unidades presenciais ja com lat/lon ---")
print(con.sql("""
SELECT g.NO_MUNICIPIO, g.SG_UF, round(g.LATITUDE,4) lat, round(g.LONGITUDE,4) lon,
       count(DISTINCT c.CO_IES) ies, sum(c.QT_MAT) matriculas
FROM cur c JOIN geo g ON g.CO_MUNICIPIO=c.CO_MUNICIPIO
WHERE c.TP_DIMENSAO=1 GROUP BY 1,2,3,4 ORDER BY matriculas DESC LIMIT 12;
""").df().to_string(index=False))

print("\n--- Endereco da SEDE das IES: quao geocodificavel? ---")
IES = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_ED_SUP_IES_2024.CSV"
con.execute(f"CREATE TABLE ies AS SELECT * FROM read_csv('{IES}', {O});")
print(con.sql("""
SELECT count(*) ies,
 count(*) FILTER (WHERE DS_ENDERECO_IES IS NOT NULL AND length(trim(DS_ENDERECO_IES))>3) com_logradouro,
 count(*) FILTER (WHERE DS_NUMERO_ENDERECO_IES IS NOT NULL) com_numero,
 count(*) FILTER (WHERE NU_CEP_IES IS NOT NULL) com_cep,
 count(*) FILTER (WHERE DS_ENDERECO_IES IS NOT NULL AND NU_CEP_IES IS NOT NULL) endereco_completo
FROM ies;
""").df().to_string(index=False))
print(con.sql("SELECT NO_IES, DS_ENDERECO_IES, DS_NUMERO_ENDERECO_IES, NO_BAIRRO_IES, NU_CEP_IES, NO_MUNICIPIO_IES FROM ies LIMIT 5").df().to_string(index=False))
