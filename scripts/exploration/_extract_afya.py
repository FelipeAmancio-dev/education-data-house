import sys, pypdf
sys.stdout.reconfigure(encoding="utf-8")
path = r"C:\Users\felip\.claude\projects\C--education\ffeae261-e560-4239-ba28-75d44430080f\tool-results\webfetch-1786483603532-npdwxp.pdf"
r = pypdf.PdfReader(path)
print(f"[{len(r.pages)} paginas]")
texto = "\n".join((pg.extract_text() or "") for pg in r.pages)
print(f"chars: {len(texto)}")
TERMOS = ["student", "medical school", "undergraduate", "enrolled", "base de aluno", "alunos"]
for i, pg in enumerate(r.pages, 1):
    t = pg.extract_text() or ""
    if any(term in t.lower() for term in TERMOS):
        print(f"\n--- pagina {i} ---")
        print(t[:3000])
