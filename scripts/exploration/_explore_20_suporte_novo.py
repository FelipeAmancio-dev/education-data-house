"""Inspeciona a nova estrutura do Suporte IES.xlsx (uma aba por empresa)."""
import sys, openpyxl
sys.stdout.reconfigure(encoding="utf-8")
XLS = r"C:\education\Suporte IES.xlsx"

wb = openpyxl.load_workbook(XLS, data_only=True)
print(f"ABAS ({len(wb.sheetnames)}): {wb.sheetnames}\n")
for ws in wb.worksheets:
    print("=" * 100)
    print(f"ABA '{ws.title}'  dims={ws.dimensions}  max_row={ws.max_row}  max_col={ws.max_column}")
    print("=" * 100)
    for i, row in enumerate(ws.iter_rows(values_only=True), 1):
        cells = ["" if c is None else str(c)[:45] for c in row]
        if any(cells):
            print(f"  {i:4d}: " + " | ".join(cells))
        if i >= 12:
            print(f"  ... (aba tem {ws.max_row} linhas)")
            break
    print()
