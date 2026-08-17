"""
Regras de negocio e acesso aos microdados do Censo da Educacao Superior.

Fonte unica de verdade para:
  - localizacao dos arquivos de cada ano (nomes de pasta/arquivo variam entre 2015-2024)
  - normalizacao de colunas que o INEP renomeou ao longo do tempo
  - as regras de TP_DIMENSAO, que definem quais metricas sao somaveis em cada linha
"""
import os
import re
import zipfile

# ---------------------------------------------------------------------------
# REGRAS DE TP_DIMENSAO  (ver docs/01_dicionario_dados.md §2)
# ---------------------------------------------------------------------------
# 1 = cursos presenciais no Brasil          -> todas as metricas valem
# 2 = cursos EAD no Brasil                  -> so alunos (mat/ing/conc), com geografia
# 3 = cursos EAD, dimensao so nivel Brasil  -> so cursos/vagas/inscritos, sem geografia
# 4 = cursos EAD no exterior                -> so alunos, sem geografia
DIM_ALUNOS = (1, 2, 4)     # matriculas, ingressantes, concluintes, trancados
DIM_OFERTA = (1, 3)        # numero de cursos, vagas, inscritos
DIM_GEO = (1, 2)           # qualquer recorte geografico

# ---------------------------------------------------------------------------
# Colunas renomeadas pelo INEP entre anos -> nome canonico adotado no projeto
# ---------------------------------------------------------------------------
RENOMEAR = {
    "CO_CINE_ROTULO2": "CO_CINE_ROTULO",   # so em 2020
}

# ---------------------------------------------------------------------------
# Colunas obrigatorias: se faltar alguma, a ingestao do ano falha
# ---------------------------------------------------------------------------
CURSOS_OBRIGATORIAS = [
    "NU_ANO_CENSO", "CO_IES", "CO_CURSO", "NO_CURSO",
    "TP_DIMENSAO", "TP_MODALIDADE_ENSINO", "TP_NIVEL_ACADEMICO", "TP_GRAU_ACADEMICO",
    "TP_REDE", "TP_CATEGORIA_ADMINISTRATIVA", "TP_ORGANIZACAO_ACADEMICA",
    "CO_CINE_ROTULO", "NO_CINE_ROTULO", "CO_CINE_AREA_GERAL", "NO_CINE_AREA_GERAL",
    "CO_MUNICIPIO", "NO_MUNICIPIO", "CO_UF", "SG_UF", "CO_REGIAO", "NO_REGIAO",
    "QT_CURSO", "QT_VG_TOTAL", "QT_INSCRITO_TOTAL",
    "QT_ING", "QT_MAT", "QT_CONC", "QT_SIT_TRANCADA",
]

# Colunas desejaveis: se faltarem no ano, entram como NULL e o fato e registrado no log
CURSOS_OPCIONAIS = [
    "IN_GRATUITO", "IN_CAPITAL",
    "CO_CINE_AREA_ESPECIFICA", "NO_CINE_AREA_ESPECIFICA",
    "CO_CINE_AREA_DETALHADA", "NO_CINE_AREA_DETALHADA",
    "QT_SIT_DESVINCULADO", "QT_SIT_TRANSFERIDO", "QT_SIT_FALECIDO",
    "QT_MAT_DIURNO", "QT_MAT_NOTURNO",
    "QT_MAT_FIES", "QT_MAT_PROUNII", "QT_MAT_PROUNIP",
    "QT_MAT_FINANC_REEMB", "QT_MAT_FINANC_NREEMB",
    "QT_ING_FIES", "QT_ING_PROUNII", "QT_ING_PROUNIP",
    "QT_VG_TOTAL_EAD",
]

IES_OBRIGATORIAS = [
    "NU_ANO_CENSO", "CO_IES", "NO_IES", "CO_MANTENEDORA", "NO_MANTENEDORA",
    "TP_CATEGORIA_ADMINISTRATIVA", "TP_ORGANIZACAO_ACADEMICA",
]
IES_OPCIONAIS = [
    # TP_REDE so existe na tabela IES a partir de 2023; nos anos anteriores e derivada
    # de TP_CATEGORIA_ADMINISTRATIVA (ver CATEGORIA_PUBLICA abaixo).
    "TP_REDE",
    "SG_IES", "SG_UF_IES", "CO_UF_IES", "NO_MUNICIPIO_IES", "CO_MUNICIPIO_IES",
    "NO_REGIAO_IES", "IN_CAPITAL_IES",
    "QT_TEC_TOTAL", "QT_DOC_TOTAL", "QT_DOC_EXE",
    "QT_DOC_EX_DOUT", "QT_DOC_EX_MEST", "QT_DOC_EX_INT_DE",
]

# Categorias administrativas que correspondem a TP_REDE=1 (Publica).
# Validado empiricamente em 2023 e 2024, onde as duas colunas coexistem:
#   cat 1 (Federal), 2 (Estadual), 3 (Municipal) e 7 (Especial) -> Publica
#   cat 4 (Privada c/ fins lucrativos) e 5 (Privada s/ fins)     -> Privada
# A categoria 7 mapear para PUBLICA e contraintuitivo e por isso esta explicitada aqui.
CATEGORIA_PUBLICA = (1, 2, 3, 7)


def caminho_zip(root, ano):
    """Localiza o zip do ano em data_raw/{ano}/, tolerando variacao de nome."""
    d = os.path.join(root, "data_raw", str(ano))
    if not os.path.isdir(d):
        return None
    cands = [f for f in os.listdir(d) if f.lower().endswith(".zip") and str(ano) in f]
    if not cands:
        return None
    return os.path.join(d, cands[0])


def _acha_csv(zf, palavra):
    """Acha o CSV cujo nome contem `palavra` (CURSO ou IES), ignorando encoding do nome."""
    melhor, tam = None, -1
    for i in zf.infolist():
        if i.is_dir():
            continue
        nome = os.path.basename(i.filename).upper()
        if not nome.endswith(".CSV"):
            continue
        if palavra == "CURSO" and "CURSO" in nome:
            if i.file_size > tam:
                melhor, tam = i, i.file_size
        elif palavra == "IES" and "IES" in nome and "CURSO" not in nome:
            if i.file_size > tam:
                melhor, tam = i, i.file_size
    return melhor


def extrai_csv(root, ano, qual, destino):
    """
    Extrai o CSV (`qual` in {'CURSO','IES'}) do zip do ano para `destino`.

    Escreve com nome limpo, evitando o problema de encoding dos nomes de arquivo
    dentro dos zips antigos do INEP (cp437 vs cp850).
    Devolve o caminho do arquivo extraido, ou None.
    """
    z = caminho_zip(root, ano)
    if not z:
        return None
    os.makedirs(destino, exist_ok=True)
    saida = os.path.join(destino, f"{qual}_{ano}.CSV")
    with zipfile.ZipFile(z) as zf:
        info = _acha_csv(zf, qual)
        if info is None:
            return None
        with zf.open(info) as src, open(saida, "wb") as dst:
            while True:
                bloco = src.read(1 << 20)
                if not bloco:
                    break
                dst.write(bloco)
    return saida


def le_cabecalho(path, encoding="latin-1"):
    """
    Le so a primeira linha do CSV e devolve os nomes de coluna COMO ESTAO NO ARQUIVO.

    Nao aplica RENOMEAR aqui de proposito: quem monta o SELECT precisa do nome real
    para conseguir referenciar a coluna no arquivo.
    """
    with open(path, "rb") as f:
        linha = f.readline().decode(encoding).strip()
    return [c.strip().strip('"') for c in linha.split(";")]


def cabecalho_do_zip(root, ano, qual):
    """Le o cabecalho direto do zip, sem extrair o arquivo inteiro (nomes crus)."""
    z = caminho_zip(root, ano)
    if not z:
        return []
    with zipfile.ZipFile(z) as zf:
        info = _acha_csv(zf, qual)
        if info is None:
            return []
        with zf.open(info) as f:
            linha = f.readline().decode("latin-1").strip()
    return [c.strip().strip('"') for c in linha.split(";")]


def selecao_sql(cols_no_arquivo, obrigatorias, opcionais):
    """
    Monta a lista de expressoes SELECT do DuckDB.

    Aplica o rename canonico e materializa como NULL as colunas opcionais ausentes,
    de modo que o Parquet de todo ano tenha exatamente o mesmo schema.
    Devolve (expressoes, faltando_obrigatorias, faltando_opcionais).
    """
    # nome no arquivo -> nome canonico
    canon = {c: RENOMEAR.get(c, c) for c in cols_no_arquivo}
    disponivel = {v: k for k, v in canon.items()}   # canonico -> nome real no arquivo

    faltando_obr = [c for c in obrigatorias if c not in disponivel]
    faltando_opc = [c for c in opcionais if c not in disponivel]

    exprs = []
    for c in obrigatorias + opcionais:
        if c in disponivel:
            real = disponivel[c]
            exprs.append(f'"{real}" AS {c}' if real != c else f'"{c}"')
        else:
            exprs.append(f"CAST(NULL AS BIGINT) AS {c}")
    return exprs, faltando_obr, faltando_opc
