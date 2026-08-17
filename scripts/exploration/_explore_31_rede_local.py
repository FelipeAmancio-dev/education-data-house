"""1) Deriva TP_REDE a partir de TP_CATEGORIA_ADMINISTRATIVA. 2) Investiga CO_LOCAL_OFERTA de 2021."""
import sys, os, duckdb
sys.path.insert(0, r"C:\education\scripts")
from lib.censo import extrai_csv
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:\education"
TMP = os.path.join(ROOT, "data_processed", "_tmp_probe")
O = "delim=';', header=true, encoding='latin-1', sample_size=-1, null_padding=true"
con = duckdb.connect()

# ---------- 1. mapa TP_CATEGORIA -> TP_REDE, validado em 2023 e 2024
print("=" * 92)
print("1) TP_CATEGORIA_ADMINISTRATIVA -> TP_REDE (validado onde as duas colunas coexistem)")
print("=" * 92)
for ano in (2023, 2024):
    p = extrai_csv(ROOT, ano, "IES", TMP)
    con.execute(f"CREATE OR REPLACE TEMP TABLE i AS SELECT * FROM read_csv('{p.replace(os.sep,'/')}', {O});")
    print(f"\n--- {ano} ---")
    print(con.sql("""SELECT TP_CATEGORIA_ADMINISTRATIVA cat, TP_REDE rede, count(*) n_ies
                     FROM i GROUP BY 1,2 ORDER BY 1,2""").df().to_string(index=False))
    os.remove(p)

# ---------- 2. CO_LOCAL_OFERTA em 2021
print("\n" + "=" * 92)
print("2) CO_LOCAL_OFERTA / NO_LOCAL_OFERTA — tabela IES de 2021")
print("=" * 92)
p = extrai_csv(ROOT, 2021, "IES", TMP)
con.execute(f"CREATE OR REPLACE TEMP TABLE i21 AS SELECT * FROM read_csv('{p.replace(os.sep,'/')}', {O});")
print(con.sql("""SELECT count(*) linhas, count(DISTINCT CO_IES) ies,
                        count(DISTINCT CO_LOCAL_OFERTA) locais_oferta,
                        count(DISTINCT CO_PROJETO) projetos,
                        sum(CASE WHEN CO_LOCAL_OFERTA IS NULL THEN 1 ELSE 0 END) nulos_local
                 FROM i21""").df().to_string(index=False))
print("\nAmostra:")
print(con.sql("""SELECT CO_IES, substr(NO_IES,1,38) NO_IES, CO_LOCAL_OFERTA,
                        substr(NO_LOCAL_OFERTA,1,42) NO_LOCAL_OFERTA, CO_PROJETO
                 FROM i21 ORDER BY CO_IES LIMIT 12""").df().to_string(index=False))
print("\nIES com mais locais de oferta distintos:")
print(con.sql("""SELECT CO_IES, any_value(substr(NO_IES,1,40)) NO_IES,
                        count(DISTINCT CO_LOCAL_OFERTA) n_locais, count(*) n_linhas
                 FROM i21 GROUP BY 1 ORDER BY n_locais DESC LIMIT 10""").df().to_string(index=False))
os.remove(p)
import shutil; shutil.rmtree(TMP, ignore_errors=True)
