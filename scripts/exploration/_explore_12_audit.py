"""Levantamento para auditoria de grupos: IES privadas nao mapeadas e clusters de mantenedora."""
import sys, duckdb, pandas as pd
sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400)

IES = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_ED_SUP_IES_2024.CSV"
CUR = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_CADASTRO_CURSOS_2024.CSV"
MAP = r"C:\education\config\ies_grupo_map.csv"
O = "delim=';', header=true, encoding='latin-1', sample_size=-1, null_padding=true"

con = duckdb.connect()
con.execute(f"CREATE TABLE ies AS SELECT * FROM read_csv('{IES}', {O});")
con.execute(f"""CREATE TABLE cur AS SELECT CO_IES, TP_DIMENSAO, TP_MODALIDADE_ENSINO, QT_MAT
                FROM read_csv('{CUR}', {O});""")
mp = pd.read_csv(MAP, sep=";", encoding="utf-8-sig")
mp["GRUPO"] = mp["GRUPO"].fillna("")
con.register("mp", mp[["CO_IES", "GRUPO"]])

print("=" * 120)
print("1) TODAS AS IES PRIVADAS NAO MAPEADAS COM >= 8.000 MATRICULAS")
print("=" * 120)
print(con.sql("""
WITH m AS (SELECT CO_IES, sum(QT_MAT) mat,
                  sum(CASE WHEN TP_MODALIDADE_ENSINO=2 THEN QT_MAT ELSE 0 END) ead
           FROM cur WHERE TP_DIMENSAO IN (1,2,4) GROUP BY 1)
SELECT i.CO_IES, substr(i.NO_IES,1,52) NO_IES, substr(i.NO_MANTENEDORA,1,42) MANTENEDORA,
       i.CO_MANTENEDORA, i.SG_UF_IES uf, m.mat, round(100.0*m.ead/nullif(m.mat,0)) pct_ead
FROM m JOIN ies i USING (CO_IES) JOIN mp ON mp.CO_IES=i.CO_IES
WHERE i.TP_REDE=2 AND mp.GRUPO='' AND m.mat>=8000
ORDER BY m.mat DESC;
""").df().to_string(index=False))

print("\n" + "=" * 120)
print("2) CLUSTERS: mantenedoras com >=2 IES nao mapeadas (candidatos a novos grupos)")
print("=" * 120)
print(con.sql("""
WITH m AS (SELECT CO_IES, sum(QT_MAT) mat FROM cur WHERE TP_DIMENSAO IN (1,2,4) GROUP BY 1)
SELECT i.CO_MANTENEDORA, substr(any_value(i.NO_MANTENEDORA),1,55) MANTENEDORA,
       count(*) n_ies, sum(m.mat) mat_total, string_agg(substr(i.NO_IES,1,28), ' | ') ies
FROM ies i JOIN m USING (CO_IES) JOIN mp ON mp.CO_IES=i.CO_IES
WHERE i.TP_REDE=2 AND mp.GRUPO=''
GROUP BY 1 HAVING count(*)>=2 AND sum(m.mat)>=5000
ORDER BY mat_total DESC LIMIT 45;
""").df().to_string(index=False))

print("\n" + "=" * 120)
print("3) MANTENEDORAS DOS GRUPOS JA MAPEADOS (para checar consistencia)")
print("=" * 120)
print(con.sql("""
WITH m AS (SELECT CO_IES, sum(QT_MAT) mat FROM cur WHERE TP_DIMENSAO IN (1,2,4) GROUP BY 1)
SELECT mp.GRUPO, i.CO_MANTENEDORA, substr(any_value(i.NO_MANTENEDORA),1,50) MANTENEDORA,
       count(*) n_ies, sum(m.mat) mat
FROM ies i JOIN m USING (CO_IES) JOIN mp ON mp.CO_IES=i.CO_IES
WHERE mp.GRUPO<>'' GROUP BY 1,2 ORDER BY mp.GRUPO, mat DESC;
""").df().to_string(index=False))
