"""Extrai o dicionario INEP para JSON/CSV e imprime texto integral de campos criticos."""
import sys, json, csv, openpyxl

sys.stdout.reconfigure(encoding="utf-8")
PATH = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\Anexos\ANEXO I - Dicionário de Dados\dicionário_dados_educação_superior.xlsx"
OUT_JSON = r"C:\education\config\inep_dicionario_2024.json"
OUT_CSV = r"C:\education\docs\inep_dicionario_2024.csv"

wb = openpyxl.load_workbook(PATH, data_only=True)
result = {}
rows_flat = []

for ws in wb.worksheets:
    entries = []
    section = None
    for row in ws.iter_rows(min_row=1, values_only=True):
        n, var, desc, tipo, tam, categoria, obs = (list(row) + [None] * 7)[:7]
        # linha de secao: coluna A preenchida, B vazia
        if var is None and isinstance(n, str) and n.strip() and not n.strip().isdigit():
            if n.strip().upper() == n.strip() and len(n.strip()) > 5:
                section = n.strip()
            continue
        if not isinstance(var, str) or not var.strip() or var.strip() == "Nome da Variável":
            continue
        e = {
            "n": n, "secao": section, "variavel": var.strip(),
            "descricao": (desc or "").strip(),
            "tipo": (tipo or ""), "tamanho": (tam or ""),
            "categorias": (categoria or "").strip(),
            "observacao": (obs or "").strip(),
        }
        entries.append(e)
        rows_flat.append({"tabela": ws.title, **e})
    result[ws.title] = entries
    print(f"{ws.title}: {len(entries)} variaveis extraidas")

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)
with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["tabela", "n", "secao", "variavel", "descricao", "tipo", "tamanho", "categorias", "observacao"])
    w.writeheader(); w.writerows(rows_flat)

CRITICOS = ["TP_DIMENSAO", "TP_MODALIDADE_ENSINO", "TP_NIVEL_ACADEMICO", "TP_GRAU_ACADEMICO",
            "TP_ORGANIZACAO_ACADEMICA", "TP_CATEGORIA_ADMINISTRATIVA", "TP_REDE",
            "QT_CURSO", "QT_MAT", "QT_ING", "QT_CONC", "QT_VG_TOTAL", "CO_CURSO", "CO_CINE_ROTULO",
            "QT_SIT_TRANCADA", "QT_SIT_DESVINCULADO", "QT_SIT_TRANSFERIDO", "QT_SIT_FALECIDO",
            "CO_MANTENEDORA", "IN_CAPITAL", "NO_MUNICIPIO"]
print("\n" + "#" * 110)
print("TEXTO INTEGRAL DOS CAMPOS CRITICOS")
print("#" * 110)
for tabela, entries in result.items():
    for e in entries:
        if e["variavel"] in CRITICOS:
            print(f"\n--- [{tabela}] {e['variavel']}  (secao: {e['secao']})")
            print(f"  DESC : {e['descricao']}")
            if e["categorias"]:
                print(f"  CATEG: {e['categorias']}")
            if e["observacao"]:
                print(f"  OBS  : {e['observacao']}")
