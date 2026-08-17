"""Exploração inicial: encoding, separador, cabeçalhos e amostra dos CSVs do Censo."""
import io, os, sys

BASE = r"C:\education\data_raw\2024\microdados_censo_da_educacao_superior_2024\dados"
FILES = {
    "CURSOS": os.path.join(BASE, "MICRODADOS_CADASTRO_CURSOS_2024.CSV"),
    "IES": os.path.join(BASE, "MICRODADOS_ED_SUP_IES_2024.CSV"),
}

sys.stdout.reconfigure(encoding="utf-8")

for name, path in FILES.items():
    print("=" * 100)
    print(f"### {name}  ({os.path.getsize(path)/1024/1024:,.1f} MB)")
    print("=" * 100)
    with open(path, "rb") as f:
        head = f.read(4000)
    print("primeiros bytes (repr):")
    print(repr(head[:300]))
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            head.decode(enc)
            print(f"  decodifica em {enc}: OK")
        except Exception as e:
            print(f"  decodifica em {enc}: FALHA ({e})")

    txt = head.decode("latin-1")
    first_line = txt.splitlines()[0]
    for sep in (";", ",", "|", "\t"):
        print(f"  sep '{sep}' -> {first_line.count(sep)} ocorrencias no header")

    cols = first_line.split(";")
    print(f"\n  N COLUNAS: {len(cols)}")
    for i, c in enumerate(cols, 1):
        print(f"    {i:3d}. {c}")
    print()
