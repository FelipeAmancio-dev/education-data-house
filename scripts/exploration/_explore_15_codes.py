"""Codigos exatos de mantenedora dos maiores clusters independentes."""
import sys, duckdb, pandas as pd
sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
IES = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_ED_SUP_IES_2024.CSV"
CUR = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_CADASTRO_CURSOS_2024.CSV"
O = "delim=';', header=true, encoding='latin-1', sample_size=-1, null_padding=true"
con = duckdb.connect()
con.execute(f"CREATE TABLE ies AS SELECT * FROM read_csv('{IES}', {O});")
con.execute(f"CREATE TABLE cur AS SELECT CO_IES, TP_DIMENSAO, QT_MAT FROM read_csv('{CUR}', {O});")
mp = pd.read_csv(r"C:\education\config\ies_grupo_map.csv", sep=";", encoding="utf-8-sig")
mp["GRUPO"] = mp["GRUPO"].fillna("")
con.register("mp", mp[["CO_IES", "GRUPO"]])

print(con.sql("""
WITH m AS (SELECT CO_IES, sum(QT_MAT) mat FROM cur WHERE TP_DIMENSAO IN (1,2,4) GROUP BY 1)
SELECT i.CO_MANTENEDORA, any_value(i.NO_MANTENEDORA) MANTENEDORA,
       any_value(i.TP_CATEGORIA_ADMINISTRATIVA) categ,
       count(*) n_ies, sum(coalesce(m.mat,0)) mat,
       any_value(i.SG_UF_IES) uf
FROM ies i LEFT JOIN m USING (CO_IES) JOIN mp ON mp.CO_IES=i.CO_IES
WHERE mp.GRUPO='' AND i.TP_REDE=2
GROUP BY 1 HAVING sum(coalesce(m.mat,0)) >= 20000
ORDER BY mat DESC;
""").df().to_string(index=False))
