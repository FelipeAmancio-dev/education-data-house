"""Busca trechos com numeros de base de alunos nos releases baixados."""
import sys, re, pypdf
sys.stdout.reconfigure(encoding="utf-8")

DIR = r"C:\Users\felip\.claude\projects\C--education\ffeae261-e560-4239-ba28-75d44430080f\tool-results"
FILES = {
    "YDUQS": f"{DIR}\\webfetch-1786475711211-329csy.pdf",
    "COGNA": f"{DIR}\\webfetch-1786475714551-f97dtk.pdf",
    "SER": f"{DIR}\\webfetch-1786475718483-1f6bdc.pdf",
    "VITRU": f"{DIR}\\webfetch-1786475723720-1uuj9i.pdf",
}

TERMOS = ["base de aluno", "alunos matricul", "student base", "mil alunos",
          "thousand students", "número de alunos", "base de estudantes"]

for nome, path in FILES.items():
    print("#" * 100)
    print(f"# {nome}")
    print("#" * 100)
    r = pypdf.PdfReader(path)
    for i, pg in enumerate(r.pages, 1):
        t = pg.extract_text() or ""
        low = t.lower()
        if any(term in low for term in TERMOS):
            print(f"\n--- pagina {i} ---")
            print(t[:3500])
    print()
