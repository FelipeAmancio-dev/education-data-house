import sys, duckdb
sys.stdout.reconfigure(encoding="utf-8")
CUR = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_CADASTRO_CURSOS_2024.CSV"
IES = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_ED_SUP_IES_2024.CSV"
O = "delim=';', header=true, encoding='latin-1', sample_size=-1, null_padding=true"
con = duckdb.connect()
con.execute(f"CREATE TABLE c AS SELECT * FROM read_csv('{CUR}', {O});")
con.execute(f"CREATE TABLE i AS SELECT * FROM read_csv('{IES}', {O});")
for col in ["TP_CATEGORIA_ADMINISTRATIVA", "TP_ORGANIZACAO_ACADEMICA", "TP_GRAU_ACADEMICO",
            "TP_NIVEL_ACADEMICO", "TP_MODALIDADE_ENSINO", "TP_REDE", "IN_GRATUITO",
            "IN_CAPITAL", "IN_COMUNITARIA", "IN_CONFESSIONAL"]:
    v = con.sql(f"SELECT DISTINCT {col} AS v FROM c ORDER BY 1").df()["v"].tolist()
    print(f"{col:32s} cursos: {v}")
for col in ["TP_CATEGORIA_ADMINISTRATIVA", "TP_ORGANIZACAO_ACADEMICA", "TP_REDE"]:
    v = con.sql(f"SELECT DISTINCT {col} AS v FROM i ORDER BY 1").df()["v"].tolist()
    print(f"{col:32s} ies   : {v}")
print()
print(con.sql("SELECT DISTINCT CO_REGIAO, NO_REGIAO FROM c WHERE CO_REGIAO IS NOT NULL ORDER BY 1").df().to_string(index=False))
print()
print(con.sql("SELECT CO_CINE_AREA_GERAL, any_value(NO_CINE_AREA_GERAL) nome FROM c GROUP BY 1 ORDER BY 1").df().to_string(index=False))
print()
print("CO_CINE_ROTULO exemplos (formato texto?):")
print(con.sql("SELECT DISTINCT CO_CINE_ROTULO FROM c ORDER BY 1 LIMIT 8").df().to_string(index=False))
