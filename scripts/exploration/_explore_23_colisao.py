"""Verifica colisao de codigos de mantenedora usados como IES na aba CRUZEIRO DO SUL."""
import sys, os, duckdb, pandas as pd, openpyxl
sys.path.insert(0, r"C:\education\scripts")
from lib.suporte import ler_suporte, ler_csv_comentado, norm
sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 250)

IES = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados\MICRODADOS_ED_SUP_IES_2024.CSV"
O = "delim=';', header=true, encoding='latin-1', sample_size=-1, null_padding=true"
con = duckdb.connect()
con.execute(f"CREATE TABLE ies AS SELECT * FROM read_csv('{IES}', {O});")

print("=== A) Codigos do BLOCO DE MANTENEDORAS da aba CRUZEIRO DO SUL que existem como CO_IES ===")
bloco_mant = [290, 342, 159, 418, 365, 943, 359, 120, 521, 245, 1007]
print(con.sql(f"""SELECT CO_IES, NO_IES, CO_MANTENEDORA, NO_MANTENEDORA, SG_UF_IES, TP_REDE
 FROM ies WHERE CO_IES IN ({','.join(map(str,bloco_mant))}) ORDER BY CO_IES""").df().to_string(index=False))

print("\n=== B) Esses codigos como MANTENEDORA (o que o usuario quis dizer) ===")
print(con.sql(f"""SELECT CO_MANTENEDORA, any_value(NO_MANTENEDORA) nome, count(*) n_ies
 FROM ies WHERE CO_MANTENEDORA IN ({','.join(map(str,bloco_mant))}) GROUP BY 1 ORDER BY 1""").df().to_string(index=False))

print("\n=== C) Aba VITRU completa ===")
wb = openpyxl.load_workbook(r"C:\education\Suporte IES.xlsx", data_only=True)
for i, row in enumerate(wb["VITRU"].iter_rows(values_only=True), 1):
    cells = ["" if c is None else str(c)[:50] for c in row]
    print(f"  {i:3d}: " + " | ".join(cells))

print("\n=== D) Aba ANIMA: ultimas linhas ===")
ws = wb["ANIMA"]
for i, row in enumerate(ws.iter_rows(values_only=True), 1):
    if i >= 66:
        cells = ["" if c is None else str(c)[:50] for c in row]
        print(f"  {i:3d}: " + " | ".join(cells))

print("\n=== E) Aba YDUQS: ultimas linhas ===")
ws = wb["YDUQS"]
for i, row in enumerate(ws.iter_rows(values_only=True), 1):
    if i >= 68:
        cells = ["" if c is None else str(c)[:50] for c in row]
        print(f"  {i:3d}: " + " | ".join(cells))
