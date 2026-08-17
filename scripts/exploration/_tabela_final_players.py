import sys, duckdb, pandas as pd
sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 200)
CUR = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_CADASTRO_CURSOS_2024.CSV"
O = "delim=';', header=true, encoding='latin-1', sample_size=-1, null_padding=true"
con = duckdb.connect()
con.execute(f"CREATE TABLE cur AS SELECT * FROM read_csv('{CUR}', {O});")
mp = pd.read_csv(r"C:\education\config\ies_grupo_map.csv", sep=";", encoding="utf-8-sig")
mp["GRUPO"] = mp["GRUPO"].fillna("")
con.register("mp", mp[["CO_IES", "GRUPO"]])
print(con.sql("""
SELECT mp.GRUPO,
 sum(c.QT_MAT) FILTER (WHERE c.TP_MODALIDADE_ENSINO=1) PRESENCIAL,
 sum(c.QT_MAT) FILTER (WHERE c.TP_MODALIDADE_ENSINO=2) EAD,
 sum(c.QT_MAT) TOTAL_QT_MAT,
 round(100.0*sum(c.QT_MAT)/10227266,2) SHARE_MAT
FROM cur c JOIN mp ON mp.CO_IES=c.CO_IES
WHERE c.TP_DIMENSAO IN (1,2,4) AND mp.GRUPO IN
  ('Cogna','Vitru','YDUQS','Cruzeiro do Sul','Ser Educacional','Ânima','Afya')
GROUP BY 1 ORDER BY TOTAL_QT_MAT DESC;
""").df().to_string(index=False))
