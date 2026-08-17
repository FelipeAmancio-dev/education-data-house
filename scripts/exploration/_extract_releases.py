"""Extrai texto dos PDFs de earnings release baixados via WebFetch, buscando 'base de alunos'."""
import sys, re, pypdf
sys.stdout.reconfigure(encoding="utf-8")

DIR = r"C:\Users\felip\.claude\projects\C--education\ffeae261-e560-4239-ba28-75d44430080f\tool-results"
FILES = {
    "YDUQS (4T24)": f"{DIR}\\webfetch-1786475711211-329csy.pdf",
    "Cogna (4T24)": f"{DIR}\\webfetch-1786475714551-f97dtk.pdf",
    "Ser Educacional (4T24)": f"{DIR}\\webfetch-1786475718483-1f6bdc.pdf",
    "Vitru (4Q24)": f"{DIR}\\webfetch-1786475723720-1uuj9i.pdf",
}

KEYWORDS = ["base de aluno", "alunos matricul", "student base", "presencial", "digital",
            "ead", "hibrid", "híbrid", "premium", "on-campus", "distance"]

for nome, path in FILES.items():
    print("=" * 100)
    print(f"### {nome}  ({path})")
    print("=" * 100)
    try:
        r = pypdf.PdfReader(path)
        print(f"[{len(r.pages)} paginas]")
        full = []
        for i, pg in enumerate(r.pages, 1):
            t = pg.extract_text() or ""
            full.append(t)
        texto = "\n".join(full)
        print(f"total de caracteres extraidos: {len(texto)}")
        if len(texto) < 200:
            print("!! pouco texto extraido - pode ser PDF escaneado/imagem")
    except Exception as e:
        print(f"ERRO ao ler: {e}")
    print()
