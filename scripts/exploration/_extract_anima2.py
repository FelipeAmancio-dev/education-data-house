import sys, pypdf
sys.stdout.reconfigure(encoding="utf-8")
path = r"C:\Users\felip\.claude\projects\C--education\ffeae261-e560-4239-ba28-75d44430080f\tool-results\webfetch-1786483671105-xtgs9r.pdf"
r = pypdf.PdfReader(path)
print(f"[{len(r.pages)} paginas]")
full = "\n".join((pg.extract_text() or "") for pg in r.pages)
print(f"chars extraidos: {len(full)}")
print(repr(full[:500]))
