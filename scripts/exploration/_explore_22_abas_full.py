"""Dump completo das abas com anomalias de parsing."""
import sys, openpyxl
sys.stdout.reconfigure(encoding="utf-8")
wb = openpyxl.load_workbook(r"C:\education\Suporte IES.xlsx", data_only=True)
for nome in ["CRUZEIRO DO SUL", "AFYA", "VITRU"]:
    ws = wb[nome]
    print("=" * 110)
    print(f"ABA '{nome}'  max_row={ws.max_row} max_col={ws.max_column}")
    print("=" * 110)
    for i, row in enumerate(ws.iter_rows(values_only=True), 1):
        cells = ["" if c is None else str(c)[:48] for c in row]
        print(f"  {i:4d}: " + " | ".join(cells))
    print()
