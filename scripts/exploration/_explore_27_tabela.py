"""Tabela final de conferencia por grande player."""
import sys, duckdb, pandas as pd
sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 260)
CUR = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_CADASTRO_CURSOS_2024.CSV"
O = "delim=';', header=true, encoding='latin-1', sample_size=-1, null_padding=true"
con = duckdb.connect()
con.execute(f"CREATE TABLE cur AS SELECT * FROM read_csv('{CUR}', {O});")
mp = pd.read_csv(r"C:\education\config\ies_grupo_map.csv", sep=";", encoding="utf-8-sig")
mp["GRUPO"] = mp["GRUPO"].fillna(""); mp["MARCA"] = mp["MARCA"].fillna("")
con.register("mp", mp[["CO_IES", "GRUPO", "MARCA"]])

print("=== TABELA POR GRUPO (players do Suporte + novos grandes) ===")
print(con.sql("""
SELECT mp.GRUPO,
 count(DISTINCT c.CO_IES) IES,
 sum(c.QT_MAT) FILTER (WHERE c.TP_MODALIDADE_ENSINO=1) PRESENCIAL,
 sum(c.QT_MAT) FILTER (WHERE c.TP_MODALIDADE_ENSINO=2) EAD,
 sum(c.QT_MAT) TOTAL_QT_MAT,
 sum(coalesce(c.QT_SIT_TRANCADA,0)) TRANCADOS,
 round(100.0*sum(coalesce(c.QT_SIT_TRANCADA,0))/nullif(sum(c.QT_MAT),0),1) TRANC_PCT,
 sum(c.QT_MAT+coalesce(c.QT_SIT_TRANCADA,0)) BASE_ALUNOS,
 round(100.0*sum(c.QT_MAT)/10227266,2) SHARE_MAT,
 round(100.0*sum(c.QT_MAT+coalesce(c.QT_SIT_TRANCADA,0))/12035433,2) SHARE_BASE
FROM cur c JOIN mp ON mp.CO_IES=c.CO_IES
WHERE c.TP_DIMENSAO IN (1,2,4) AND mp.GRUPO IN
  ('Cogna','Vitru','YDUQS','Cruzeiro do Sul','Ser Educacional','Ânima','Afya',
   'FMU','UNINTER','UNIP','UNINOVE')
GROUP BY 1 ORDER BY TOTAL_QT_MAT DESC;
""").df().to_string(index=False))

print("\n=== VITRU por MARCA (a aba nova traz essa coluna) ===")
print(con.sql("""
SELECT CASE WHEN mp.MARCA='' THEN '(sem marca)' ELSE mp.MARCA END MARCA,
 count(DISTINCT c.CO_IES) IES,
 sum(c.QT_MAT) FILTER (WHERE c.TP_MODALIDADE_ENSINO=1) PRESENCIAL,
 sum(c.QT_MAT) FILTER (WHERE c.TP_MODALIDADE_ENSINO=2) EAD,
 sum(c.QT_MAT) TOTAL, sum(coalesce(c.QT_SIT_TRANCADA,0)) TRANCADOS,
 sum(c.QT_MAT+coalesce(c.QT_SIT_TRANCADA,0)) BASE
FROM cur c JOIN mp ON mp.CO_IES=c.CO_IES
WHERE c.TP_DIMENSAO IN (1,2,4) AND mp.GRUPO='Vitru' GROUP BY 1 ORDER BY TOTAL DESC;
""").df().to_string(index=False))

print("\n=== ANIMA consolidada com FMU ===")
print(con.sql("""
SELECT 'Ânima standalone' AS cenario, sum(c.QT_MAT) FILTER (WHERE c.TP_MODALIDADE_ENSINO=1) PRES,
 sum(c.QT_MAT) FILTER (WHERE c.TP_MODALIDADE_ENSINO=2) EAD, sum(c.QT_MAT) TOTAL,
 sum(c.QT_MAT+coalesce(c.QT_SIT_TRANCADA,0)) BASE
FROM cur c JOIN mp ON mp.CO_IES=c.CO_IES WHERE c.TP_DIMENSAO IN (1,2,4) AND mp.GRUPO='Ânima'
UNION ALL
SELECT 'Ânima + FMU', sum(c.QT_MAT) FILTER (WHERE c.TP_MODALIDADE_ENSINO=1),
 sum(c.QT_MAT) FILTER (WHERE c.TP_MODALIDADE_ENSINO=2), sum(c.QT_MAT),
 sum(c.QT_MAT+coalesce(c.QT_SIT_TRANCADA,0))
FROM cur c JOIN mp ON mp.CO_IES=c.CO_IES WHERE c.TP_DIMENSAO IN (1,2,4) AND mp.GRUPO IN ('Ânima','FMU');
""").df().to_string(index=False))
