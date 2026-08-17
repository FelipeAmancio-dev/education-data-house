"""Marcas independentes que se espalham por varias mantenedoras."""
import sys, duckdb, pandas as pd
sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
IES = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_ED_SUP_IES_2024.CSV"
CUR = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_CADASTRO_CURSOS_2024.CSV"
O = "delim=';', header=true, encoding='latin-1', sample_size=-1, null_padding=true"
con = duckdb.connect()
con.execute(f"CREATE TABLE ies AS SELECT * FROM read_csv('{IES}', {O});")
con.execute(f"CREATE TABLE cur AS SELECT CO_IES, TP_DIMENSAO, QT_MAT FROM read_csv('{CUR}', {O});")

for marca in ["MULTIVIX", "TIRADENTES", "UNIFTC", "FTC", "UNINTA", "UNIVERSO", "SALGADO"]:
    d = con.sql(f"""
    WITH m AS (SELECT CO_IES, sum(QT_MAT) mat FROM cur WHERE TP_DIMENSAO IN (1,2,4) GROUP BY 1)
    SELECT i.CO_MANTENEDORA, substr(any_value(i.NO_MANTENEDORA),1,48) MANT, count(*) n_ies,
           sum(coalesce(m.mat,0)) mat, substr(string_agg(i.NO_IES,' | '),1,90) ies
    FROM ies i LEFT JOIN m USING (CO_IES)
    WHERE upper(i.NO_IES) LIKE '%{marca}%' OR upper(i.NO_MANTENEDORA) LIKE '%{marca}%'
    GROUP BY 1 ORDER BY mat DESC""").df()
    if len(d):
        print(f"\n=== {marca} — total {d['mat'].sum():,.0f} matriculas em {len(d)} mantenedoras ===")
        print(d.to_string(index=False))
