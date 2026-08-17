"""Compara cabecalhos da tabela CURSOS entre 2015-2024, lendo direto do zip (sem extrair)."""
import sys, zipfile, os, io
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:\education\data_raw"

CHAVES = ["NU_ANO_CENSO", "TP_DIMENSAO", "CO_IES", "CO_CURSO", "NO_CURSO",
          "CO_CINE_ROTULO", "NO_CINE_ROTULO", "CO_CINE_AREA_GERAL",
          "TP_MODALIDADE_ENSINO", "TP_NIVEL_ACADEMICO", "TP_GRAU_ACADEMICO",
          "TP_REDE", "TP_CATEGORIA_ADMINISTRATIVA", "TP_ORGANIZACAO_ACADEMICA",
          "CO_MUNICIPIO", "CO_UF", "CO_REGIAO", "IN_CAPITAL", "IN_GRATUITO",
          "QT_MAT", "QT_ING", "QT_CONC", "QT_CURSO", "QT_VG_TOTAL",
          "QT_INSCRITO_TOTAL", "QT_SIT_TRANCADA", "QT_SIT_DESVINCULADO",
          "CO_CURSO_POLO", "CO_POLO", "NO_POLO"]

headers = {}
for ano in range(2015, 2025):
    z = os.path.join(ROOT, str(ano), f"microdados_censo_da_educacao_superior_{ano}.zip")
    if not os.path.exists(z):
        continue
    with zipfile.ZipFile(z) as zf:
        alvo = None
        for i in zf.infolist():
            fn = i.filename.upper()
            if fn.endswith(".CSV") and "CURSO" in fn:
                alvo = i
                break
        if alvo is None:
            print(f"{ano}: CURSOS nao encontrado")
            continue
        with zf.open(alvo) as f:
            primeira = f.readline().decode("latin-1").strip()
    cols = [c.strip().strip('"') for c in primeira.split(";")]
    headers[ano] = cols
    print(f"{ano}: {len(cols):3d} colunas   arquivo={os.path.basename(alvo.filename)}")

print("\n" + "=" * 100)
print("PRESENCA DE CAMPOS-CHAVE POR ANO")
print("=" * 100)
anos = sorted(headers)
print(f"{'CAMPO':30s} " + " ".join(str(a)[2:] for a in anos))
for k in CHAVES:
    linha = " ".join(" x" if k in headers[a] else "  ." for a in anos)
    print(f"{k:30s} {linha}")

print("\n" + "=" * 100)
print("COLUNAS QUE ENTRAM/SAEM AO LONGO DO TEMPO")
print("=" * 100)
for i in range(1, len(anos)):
    a0, a1 = anos[i-1], anos[i]
    s0, s1 = set(headers[a0]), set(headers[a1])
    novas, saem = sorted(s1 - s0), sorted(s0 - s1)
    if novas or saem:
        print(f"\n{a0} -> {a1}:  +{len(novas)} / -{len(saem)}")
        if novas:
            print(f"   ENTRAM: {', '.join(novas[:14])}{' ...' if len(novas)>14 else ''}")
        if saem:
            print(f"   SAEM  : {', '.join(saem[:14])}{' ...' if len(saem)>14 else ''}")

nucleo = ["NU_ANO_CENSO","TP_DIMENSAO","CO_IES","CO_CURSO","CO_CINE_ROTULO","NO_CINE_ROTULO",
          "TP_MODALIDADE_ENSINO","TP_REDE","CO_MUNICIPIO","QT_MAT","QT_ING","QT_CONC",
          "QT_CURSO","QT_VG_TOTAL","QT_SIT_TRANCADA"]
print("\n" + "=" * 100)
print("NUCLEO DO DASHBOARD - disponivel em todos os anos?")
print("=" * 100)
for k in nucleo:
    faltam = [a for a in anos if k not in headers[a]]
    print(f"  {k:26s} {'OK todos os anos' if not faltam else 'FALTA em: ' + str(faltam)}")
