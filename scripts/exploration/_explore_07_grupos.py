"""Valida o mapeamento Suporte IES.xlsx contra o Censo 2024."""
import sys, duckdb, pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 200)
IES = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_ED_SUP_IES_2024.CSV"
CUR = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_CADASTRO_CURSOS_2024.CSV"
XLS = r"C:\education\Suporte IES.xlsx"

sup = pd.read_excel(XLS, sheet_name="Sheet1", header=1)
sup.columns = [str(c).strip() for c in sup.columns]
print("COLUNAS:", list(sup.columns))
print("LINHAS:", len(sup))
print("\nNULOS POR COLUNA:\n", sup.isna().sum().to_string())
print("\nTIPOS:\n", sup.dtypes.to_string())

sup = sup.rename(columns={"IES Code": "CO_IES", "IES": "NO_IES_SUP", "City": "CIDADE_SUP",
                          "State": "UF_SUP", "Company": "GRUPO"})
sup["CO_IES"] = pd.to_numeric(sup["CO_IES"], errors="coerce")
print("\nCO_IES nao numericos:", sup["CO_IES"].isna().sum())
sup = sup.dropna(subset=["CO_IES"])
sup["CO_IES"] = sup["CO_IES"].astype("int64")

print("\n--- GRUPOS DISTINTOS ---")
print(sup["GRUPO"].value_counts(dropna=False).to_string())

dup = sup[sup.duplicated("CO_IES", keep=False)].sort_values("CO_IES")
print(f"\n--- CO_IES DUPLICADOS: {len(dup)} linhas ---")
if len(dup):
    print(dup.to_string(index=False))

con = duckdb.connect()
con.execute(f"""CREATE TABLE ies AS SELECT * FROM read_csv('{IES}', delim=';', header=true,
            encoding='latin-1', sample_size=-1, null_padding=true);""")
con.execute(f"""CREATE TABLE cur AS SELECT CO_IES, TP_DIMENSAO, TP_MODALIDADE_ENSINO, CO_MUNICIPIO,
            QT_MAT, QT_CURSO FROM read_csv('{CUR}', delim=';', header=true, encoding='latin-1',
            sample_size=-1, null_padding=true);""")
con.register("sup", sup)

def show(t, sql):
    print("\n" + "=" * 100); print(t); print("=" * 100)
    print(con.sql(sql).df().to_string(index=False))

show("H) CODIGOS DO SUPORTE QUE NAO EXISTEM NO CENSO 2024", """
SELECT s.CO_IES, s.NO_IES_SUP, s.UF_SUP, s.GRUPO FROM sup s
LEFT JOIN ies i ON i.CO_IES = s.CO_IES WHERE i.CO_IES IS NULL ORDER BY s.GRUPO, s.CO_IES;
""")

show("I) CONSOLIDADO POR GRUPO (matriculas 2024)", """
WITH m AS (SELECT CO_IES, sum(QT_MAT) mat,
                  sum(CASE WHEN TP_MODALIDADE_ENSINO=1 THEN QT_MAT ELSE 0 END) presencial,
                  sum(CASE WHEN TP_MODALIDADE_ENSINO=2 THEN QT_MAT ELSE 0 END) ead
           FROM cur WHERE TP_DIMENSAO IN (1,2,4) GROUP BY 1)
SELECT s.GRUPO, count(DISTINCT s.CO_IES) ies_mapeadas,
       sum(m.mat) matriculas, sum(m.presencial) presencial, sum(m.ead) ead,
       round(100.0*sum(m.mat)/10227266,2) AS share_pct
FROM sup s LEFT JOIN m ON m.CO_IES = s.CO_IES
GROUP BY 1 ORDER BY matriculas DESC NULLS LAST;
""")

show("J) MAIORES IES PRIVADAS SEM GRUPO MAPEADO (top 25)", """
WITH m AS (SELECT CO_IES, sum(QT_MAT) mat FROM cur WHERE TP_DIMENSAO IN (1,2,4) GROUP BY 1)
SELECT i.CO_IES, i.NO_IES, i.SG_IES, i.NO_MANTENEDORA, i.SG_UF_IES, m.mat
FROM m JOIN ies i USING (CO_IES)
WHERE i.TP_REDE = 2 AND i.CO_IES NOT IN (SELECT CO_IES FROM sup)
ORDER BY m.mat DESC LIMIT 25;
""")

show("K) COBERTURA GLOBAL DO MAPEAMENTO", """
WITH m AS (SELECT CO_IES, sum(QT_MAT) mat FROM cur WHERE TP_DIMENSAO IN (1,2,4) GROUP BY 1)
SELECT
 sum(m.mat) AS mat_total,
 sum(CASE WHEN s.CO_IES IS NOT NULL THEN m.mat ELSE 0 END) AS mat_mapeada,
 round(100.0*sum(CASE WHEN s.CO_IES IS NOT NULL THEN m.mat ELSE 0 END)/sum(m.mat),2) AS pct_mapeada,
 sum(CASE WHEN i.TP_REDE=2 THEN m.mat ELSE 0 END) AS mat_privada,
 round(100.0*sum(CASE WHEN s.CO_IES IS NOT NULL THEN m.mat ELSE 0 END)
       /sum(CASE WHEN i.TP_REDE=2 THEN m.mat ELSE 0 END),2) AS pct_da_privada
FROM m JOIN ies i USING (CO_IES) LEFT JOIN sup s ON s.CO_IES=m.CO_IES;
""")

show("L) IES MAPEADAS QUE SAO PUBLICAS (checagem de erro)", """
SELECT s.CO_IES, s.GRUPO, i.NO_IES, i.TP_REDE FROM sup s JOIN ies i USING (CO_IES)
WHERE i.TP_REDE = 1;
""")

show("M) CONSISTENCIA UF: suporte vs censo", """
SELECT count(*) AS divergencias FROM sup s JOIN ies i USING (CO_IES)
WHERE upper(trim(s.UF_SUP)) <> upper(trim(i.SG_UF_IES));
""")
