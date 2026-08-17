"""Le o dicionario de dados oficial do INEP (xlsx) e imprime as abas/conteudo."""
import sys, openpyxl

sys.stdout.reconfigure(encoding="utf-8")
PATH = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\Anexos\ANEXO I - Dicionário de Dados\dicionário_dados_educação_superior.xlsx"

wb = openpyxl.load_workbook(PATH, data_only=True)
print("ABAS:", wb.sheetnames)
for ws in wb.worksheets:
    print("=" * 110)
    print(f"### ABA: {ws.title}  dims={ws.dimensions}  max_row={ws.max_row} max_col={ws.max_column}")
    print("=" * 110)
    for row in ws.iter_rows(min_row=1, max_row=min(ws.max_row, 40), values_only=True):
        cells = ["" if c is None else str(c).replace("\n", " | ")[:120] for c in row]
        if any(cells):
            print(" || ".join(cells))
    print(f"... (aba tem {ws.max_row} linhas)\n")
