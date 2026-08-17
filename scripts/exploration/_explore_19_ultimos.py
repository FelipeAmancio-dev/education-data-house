import sys, duckdb
sys.stdout.reconfigure(encoding="utf-8")
IES = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_ED_SUP_IES_2024.CSV"
O = "delim=';', header=true, encoding='latin-1', sample_size=-1, null_padding=true"
con = duckdb.connect()
con.execute(f"CREATE TABLE ies AS SELECT * FROM read_csv('{IES}', {O});")
print(con.sql("""SELECT CO_IES, NO_IES, CO_MANTENEDORA, NO_MANTENEDORA, SG_UF_IES, NO_MUNICIPIO_IES
FROM ies WHERE CO_IES IN (1247, 20499, 3839, 1131) ORDER BY CO_IES""").df().to_string(index=False))
