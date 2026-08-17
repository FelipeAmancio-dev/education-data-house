"""Compara cabecalhos da tabela IES entre 2015-2024."""
import sys, os
sys.path.insert(0, r"C:\education\scripts")
from lib.censo import cabecalho_do_zip
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:\education"

CHAVES = ["NU_ANO_CENSO", "CO_IES", "NO_IES", "SG_IES", "CO_MANTENEDORA", "NO_MANTENEDORA",
          "TP_REDE", "TP_CATEGORIA_ADMINISTRATIVA", "TP_ORGANIZACAO_ACADEMICA",
          "SG_UF_IES", "CO_UF_IES", "NO_MUNICIPIO_IES", "CO_MUNICIPIO_IES", "NO_REGIAO_IES",
          "IN_CAPITAL_IES", "QT_TEC_TOTAL", "QT_DOC_TOTAL", "QT_DOC_EXE",
          "QT_DOC_EX_DOUT", "QT_DOC_EX_MEST", "QT_DOC_EX_INT_DE"]

headers = {}
for ano in range(2015, 2025):
    cols = cabecalho_do_zip(ROOT, ano, "IES")
    if cols:
        headers[ano] = cols
        print(f"{ano}: {len(cols):3d} colunas")

anos = sorted(headers)
print("\n" + "=" * 92)
print(f"{'CAMPO':32s} " + " ".join(str(a)[2:] for a in anos))
print("=" * 92)
for k in CHAVES:
    print(f"{k:32s} " + " ".join(" x" if k in headers[a] else "  ." for a in anos))

print("\n=== Colunas de 2015 que contem REDE / CATEG / ORGANIZ ===")
for c in headers[2015]:
    if any(t in c.upper() for t in ["REDE", "CATEG", "ORGANIZ", "MANTEN"]):
        print("   ", c)

print("\n=== Diferencas ano a ano ===")
for i in range(1, len(anos)):
    a0, a1 = anos[i-1], anos[i]
    s0, s1 = set(headers[a0]), set(headers[a1])
    novas, saem = sorted(s1 - s0), sorted(s0 - s1)
    if novas or saem:
        print(f"\n{a0} -> {a1}: +{len(novas)} / -{len(saem)}")
        if novas: print(f"   ENTRAM: {', '.join(novas[:12])}{' ...' if len(novas)>12 else ''}")
        if saem:  print(f"   SAEM  : {', '.join(saem[:12])}{' ...' if len(saem)>12 else ''}")
