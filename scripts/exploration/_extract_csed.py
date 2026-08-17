import sys, pypdf
sys.stdout.reconfigure(encoding="utf-8")
path = r"C:\Users\felip\.claude\projects\C--education\ffeae261-e560-4239-ba28-75d44430080f\tool-results\webfetch-1786483809677-ha4ebh.pdf"
r = pypdf.PdfReader(path)
print(f"[{len(r.pages)} paginas]")
full = "\n".join((pg.extract_text() or "") for pg in r.pages)
print(f"chars: {len(full)}")
print(repr(full[:300]))
print()
TERMOS = ["base de aluno", "alunos matricul", "digital", "presencial", "4t24", "graduacao", "graduação"]
for i, pg in enumerate(r.pages, 1):
    t = pg.extract_text() or ""
    low = t.lower()
    if any(term in low for term in TERMOS):
        print(f"\n--- pagina {i} ---")
        print(t[:3000])
