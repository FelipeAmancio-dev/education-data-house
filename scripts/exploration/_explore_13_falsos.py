"""Inspeciona candidatos duvidosos da Evidencia B: nome completo da mantenedora e municipio."""
import sys, duckdb
sys.stdout.reconfigure(encoding="utf-8")
IES = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_ED_SUP_IES_2024.CSV"
O = "delim=';', header=true, encoding='latin-1', sample_size=-1, null_padding=true"
con = duckdb.connect()
con.execute(f"CREATE TABLE ies AS SELECT * FROM read_csv('{IES}', {O});")

alvos = [386, 2688, 24381, 5600, 220, 21108, 11841, 22713, 15980, 1131, 4969, 21892,
         19337, 19859, 322, 1491, 316]
print("=== CANDIDATOS DUVIDOSOS: nome completo ===")
print(con.sql(f"""SELECT CO_IES, NO_IES, CO_MANTENEDORA, NO_MANTENEDORA, SG_UF_IES, NO_MUNICIPIO_IES
 FROM ies WHERE CO_IES IN ({','.join(map(str, alvos))}) ORDER BY CO_IES""").df().to_string(index=False))

print("\n=== TODAS AS IES DA MANTENEDORA ASSUPERO (UNIP) ===")
print(con.sql("SELECT CO_IES, NO_IES, SG_UF_IES FROM ies WHERE CO_MANTENEDORA=2415 ORDER BY CO_IES").df().to_string(index=False))

print("\n=== TODAS AS IES DA MANTENEDORA 222 (NOVE DE JULHO) ===")
print(con.sql("SELECT CO_IES, NO_IES, SG_UF_IES FROM ies WHERE CO_MANTENEDORA=222 ORDER BY CO_IES").df().to_string(index=False))

print("\n=== MANTENEDORAS QUE CONTEM 'ANHANGUERA' ===")
print(con.sql("""SELECT CO_MANTENEDORA, any_value(NO_MANTENEDORA) nome, count(*) n_ies,
 string_agg(NO_IES, ' | ') ies FROM ies WHERE upper(NO_MANTENEDORA) LIKE '%ANHANGUERA%'
 GROUP BY 1 ORDER BY 1""").df().to_string(index=False))

print("\n=== IES/MANTENEDORAS COM 'SANTO AGOSTINHO' ou 'TOCANTINENSE' ===")
print(con.sql("""SELECT CO_IES, NO_IES, CO_MANTENEDORA, NO_MANTENEDORA, SG_UF_IES FROM ies
 WHERE upper(NO_IES) LIKE '%AGOSTINHO%' OR upper(NO_MANTENEDORA) LIKE '%AGOSTINHO%'
    OR upper(NO_MANTENEDORA) LIKE '%TOCANTINENSE%' ORDER BY CO_MANTENEDORA""").df().to_string(index=False))

print("\n=== IES COM 'FAMETRO' ===")
print(con.sql("""SELECT CO_IES, NO_IES, CO_MANTENEDORA, NO_MANTENEDORA, SG_UF_IES FROM ies
 WHERE upper(NO_IES) LIKE '%FAMETRO%' ORDER BY CO_IES""").df().to_string(index=False))
