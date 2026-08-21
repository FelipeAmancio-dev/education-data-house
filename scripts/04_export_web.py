"""
Etapa 4 do pipeline: cubos Parquet -> JSON colunar para o dashboard.

Formato colunar (arrays por coluna, nao array de objetos): reduz ~60% do tamanho e
evita o custo de parse de centenas de milhares de objetos no navegador.

    {"n": 1234, "cols": ["ano","ies","mod","mat"], "ano":[...], "ies":[...], ...}

Strings viram indices inteiros apontando para arrays nas dimensoes (dim.json).

Payload:
  meta.json            anos, KPIs nacionais por ano, grupos e cores
  dim.json             IES, cursos CINE, municipios, UFs
  c_ies_mod.json       ano x IES x modalidade      (workhorse: rola para grupo/UF/rede)
  c_cine_mod.json      ano x curso x modalidade
  c_mun_mod.json       ano x municipio x modalidade
  c_ies_ano.json       ano x IES -> unidades, municipios EAD, nº de cursos
  ano/{ano}_ies_cine.json      sob demanda
  ano/{ano}_ies_mun.json       sob demanda
  geo/uf.geojson       malha das UFs

Uso:  python scripts/04_export_web.py
"""
import glob
import json
import os
import shutil
import sys

import duckdb
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data_processed")
CUBOS = os.path.join(PROC, "cubos")
CFG = os.path.join(ROOT, "config")
WEB = os.path.join(ROOT, "dashboard", "data")


def p(*a):
    return os.path.join(*a).replace(os.sep, "/")


def escreve_colunar(df, caminho, inteiros=()):
    """Grava DataFrame em JSON colunar compacto."""
    obj = {"n": int(len(df)), "cols": [c.lower() for c in df.columns]}
    for c in df.columns:
        s = df[c]
        if c in inteiros or pd.api.types.is_integer_dtype(s):
            obj[c.lower()] = [int(x) if x == x and x is not None else 0 for x in s]
        elif pd.api.types.is_float_dtype(s):
            obj[c.lower()] = [None if x != x else (int(x) if float(x).is_integer() else round(float(x), 4))
                              for x in s]
        else:
            obj[c.lower()] = [None if x is None or x != x else str(x) for x in s]
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
    return os.path.getsize(caminho) / 1024


def le_reportado():
    """Numeros de base de alunos divulgados pelas proprias companhias.

    Vao para dentro do meta.json porque a tela de composicao por player precisa mostrar,
    lado a lado, o que o Censo diz e o que a empresa reporta — sem isso o investidor nao
    consegue conferir o dashboard contra o release. NAO sao comparaveis sem ajuste: o
    escopo do numero-manchete varia (pos-graduacao, cursos livres etc.), por isso ESCOPO
    e OBS viajam junto e a interface exibe os dois.
    """
    caminho = p(CFG, "reportado_companhias.csv")
    if not os.path.exists(caminho):
        return []
    df = pd.read_csv(caminho, sep=";", comment="#").fillna("")
    out = []
    for _, r in df.iterrows():
        def num(c):
            v = str(r[c]).strip()
            return int(float(v)) if v not in ("", "nan") else None
        out.append({
            "grupo": str(r["GRUPO"]).strip(), "ano": int(r["ANO"]),
            "fonte": str(r["FONTE"]).strip(), "data_base": str(r["DATA_BASE"]).strip(),
            "presencial": num("ALUNOS_PRESENCIAL"), "ead": num("ALUNOS_EAD"),
            "total": num("ALUNOS_TOTAL"), "escopo": str(r["ESCOPO"]).strip(),
            "obs": str(r["OBS"]).strip(),
        })
    return out


# ⚠️ O export APAGAVA a pasta inteira, e isso levava junto o que ele não produz.
#
# `dashboard/data/` é escrita por seis scripts: este (cubos do Censo), o de preços, o de
# mensalidades, o do regulatório, o do e-MEC e o do feed do DOU. Um `rmtree(WEB)` aqui
# destruía os cinco outros payloads — em 18/08/2026 bastou rodar o export para
# `precos.json`, `mensalidades.json`, `regulatorio.json`, `emec.json` e `dou_diario.json`
# sumirem. Só não virou site quebrado porque os cinco estão versionados no git.
#
# Agora a limpeza é dos arquivos que ESTE script escreve, e nada mais. Arquivo de outro
# dono fica onde está.
MEUS = ("meta.json", "dim.json")
MEUS_PREFIXO = ("c_",)
MEUS_DIRS = ("ano", "geo")


def limpa_o_que_e_meu():
    for nome in os.listdir(WEB) if os.path.isdir(WEB) else []:
        alvo = p(WEB, nome)
        if os.path.isdir(alvo):
            if nome in MEUS_DIRS:
                shutil.rmtree(alvo)
        elif nome in MEUS or nome.startswith(MEUS_PREFIXO):
            os.remove(alvo)


def main():
    os.makedirs(WEB, exist_ok=True)
    limpa_o_que_e_meu()

    con = duckdb.connect()
    con.execute(f"CREATE VIEW dim_ies AS SELECT * FROM read_parquet('{p(PROC,'dim_ies.parquet')}');")
    con.execute(f"CREATE VIEW dim_curso AS SELECT * FROM read_parquet('{p(PROC,'dim_curso.parquet')}');")
    con.execute(f"CREATE VIEW dim_mun AS SELECT * FROM read_parquet('{p(PROC,'dim_municipio.parquet')}');")
    for nome in ["ies_mod", "cine_mod", "municipio_mod", "cine_uf_mod", "grau_mod",
                 "ies_ano", "ies_cine_mod", "ies_municipio_mod", "kpi_ano"]:
        f = p(CUBOS, f"cubo_{nome}.parquet")
        if os.path.exists(f):
            con.execute(f"CREATE VIEW c_{nome} AS SELECT * FROM read_parquet('{f}');")

    anos = [int(a) for a in con.sql("SELECT DISTINCT ANO FROM c_kpi_ano ORDER BY 1").df()["ANO"]]
    print(f"Anos: {min(anos)}–{max(anos)}\n")
    total_kb = 0

    # ------------------------------------------------------------------ DIMS
    # IES: uma linha por CO_IES (atributos do ano mais recente em que aparece).
    # GRUPO e pro-forma, portanto constante ao longo da serie.
    ies = con.sql("""
        WITH ult AS (
          SELECT *, row_number() OVER (PARTITION BY CO_IES ORDER BY ANO DESC) rn FROM dim_ies)
        SELECT CO_IES, NO_IES, coalesce(SG_IES,'') SG_IES, GRUPO, GRUPO_CONSOLIDADO,
               coalesce(SG_UF_IES,'') SG_UF_IES, coalesce(NO_MUNICIPIO_IES,'') NO_MUNICIPIO_IES,
               TP_REDE, TP_ORGANIZACAO_ACADEMICA, coalesce(NO_MANTENEDORA,'') NO_MANTENEDORA
        FROM ult WHERE rn=1 ORDER BY CO_IES
    """).df()
    cursos = con.sql("""SELECT CO_CINE_ROTULO, NO_CINE_ROTULO, CO_CINE_AREA_GERAL,
                               NO_CINE_AREA_GERAL FROM dim_curso ORDER BY CO_CINE_ROTULO""").df()
    muns = con.sql("""SELECT CO_MUNICIPIO, NO_MUNICIPIO, SG_UF, CO_UF, NO_REGIAO,
                             LATITUDE, LONGITUDE FROM dim_mun ORDER BY CO_MUNICIPIO""").df()

    # indices: codigo -> posicao no array (o cubo referencia a posicao, nao o codigo)
    ies_ix = {int(c): i for i, c in enumerate(ies["CO_IES"])}
    cur_ix = {str(c): i for i, c in enumerate(cursos["CO_CINE_ROTULO"])}
    mun_ix = {int(c): i for i, c in enumerate(muns["CO_MUNICIPIO"])}

    grupos_cfg = pd.read_csv(p(CFG, "grupos.csv"), sep=";").fillna("")
    dim = {
        "ies": {
            "co": [int(x) for x in ies["CO_IES"]],
            "nome": list(ies["NO_IES"]), "sigla": list(ies["SG_IES"]),
            "grupo": list(ies["GRUPO"]), "grupo_cons": list(ies["GRUPO_CONSOLIDADO"]),
            "uf": list(ies["SG_UF_IES"]), "mun": list(ies["NO_MUNICIPIO_IES"]),
            "rede": [int(x) for x in ies["TP_REDE"]],
            "org": [int(x) if x == x else 0 for x in ies["TP_ORGANIZACAO_ACADEMICA"]],
            "mant": list(ies["NO_MANTENEDORA"]),
        },
        "curso": {
            "co": list(cursos["CO_CINE_ROTULO"]), "nome": list(cursos["NO_CINE_ROTULO"]),
            "area_co": list(cursos["CO_CINE_AREA_GERAL"]), "area": list(cursos["NO_CINE_AREA_GERAL"]),
        },
        "mun": {
            "co": [int(x) for x in muns["CO_MUNICIPIO"]], "nome": list(muns["NO_MUNICIPIO"]),
            "uf": list(muns["SG_UF"]), "co_uf": [int(x) for x in muns["CO_UF"]],
            "regiao": list(muns["NO_REGIAO"]),
            "lat": [None if x != x else round(float(x), 5) for x in muns["LATITUDE"]],
            "lon": [None if x != x else round(float(x), 5) for x in muns["LONGITUDE"]],
        },
        "grupos": grupos_cfg.to_dict(orient="list"),
    }
    with open(p(WEB, "dim.json"), "w", encoding="utf-8") as f:
        json.dump(dim, f, ensure_ascii=False, separators=(",", ":"))
    kb = os.path.getsize(p(WEB, "dim.json")) / 1024
    total_kb += kb
    print(f"  dim.json                {len(ies):>7,} IES · {len(cursos):>4} cursos · "
          f"{len(muns):>5,} municípios   {kb:8,.0f} KB")

    # ------------------------------------------------------------------ META
    kpi = con.sql("SELECT * FROM c_kpi_ano ORDER BY ANO").df()
    meta = {
        "anos": anos, "ano_atual": max(anos),
        "gerado_em": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "kpi": {c.lower(): [None if v != v else (int(v) if float(v).is_integer() else float(v))
                            for v in kpi[c]] for c in kpi.columns},
        "codigos": json.load(open(p(CFG, "codigos.json"), encoding="utf-8")),
        "reportado": le_reportado(),
    }
    with open(p(WEB, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, separators=(",", ":"))
    kb = os.path.getsize(p(WEB, "meta.json")) / 1024
    total_kb += kb
    print(f"  meta.json               {len(anos):>7} anos                              {kb:8,.0f} KB")

    # ----------------------------------------------------------------- CUBOS
    def mapear(df, col, ix, novo):
        df[novo] = [ix.get(x, -1) for x in df[col]]
        return df.drop(columns=[col])

    print()
    d = con.sql("""SELECT ANO, CO_IES, MOD, QT_MAT, QT_ING, QT_CONC, QT_TRANCADA,
                          QT_CURSO, QT_VAGA FROM c_ies_mod""").df().fillna(0)
    d = mapear(d, "CO_IES", ies_ix, "IES")
    d = d[["ANO", "IES", "MOD", "QT_MAT", "QT_ING", "QT_CONC", "QT_TRANCADA", "QT_CURSO", "QT_VAGA"]]
    kb = escreve_colunar(d, p(WEB, "c_ies_mod.json")); total_kb += kb
    print(f"  c_ies_mod.json          {len(d):>7,} linhas                            {kb:8,.0f} KB")

    d = con.sql("""SELECT ANO, CO_CINE_ROTULO, MOD, QT_MAT, QT_ING, QT_CONC, QT_TRANCADA,
                          QT_CURSO, QT_VAGA FROM c_cine_mod WHERE CO_CINE_ROTULO IS NOT NULL""").df().fillna(0)
    d = mapear(d, "CO_CINE_ROTULO", cur_ix, "CUR")
    d = d[["ANO", "CUR", "MOD", "QT_MAT", "QT_ING", "QT_CONC", "QT_TRANCADA", "QT_CURSO", "QT_VAGA"]]
    kb = escreve_colunar(d, p(WEB, "c_cine_mod.json")); total_kb += kb
    print(f"  c_cine_mod.json         {len(d):>7,} linhas                            {kb:8,.0f} KB")

    d = con.sql("""SELECT ANO, CO_MUNICIPIO, MOD, QT_MAT, QT_ING, QT_CONC
                   FROM c_municipio_mod""").df().fillna(0)
    d = mapear(d, "CO_MUNICIPIO", mun_ix, "MUN")
    d = d[["ANO", "MUN", "MOD", "QT_MAT", "QT_ING", "QT_CONC"]]
    kb = escreve_colunar(d, p(WEB, "c_mun_mod.json")); total_kb += kb
    print(f"  c_mun_mod.json          {len(d):>7,} linhas                            {kb:8,.0f} KB")

    d = con.sql("SELECT ANO, CO_IES, QT_UNIDADE, QT_MUNIC_EAD, QT_CINE FROM c_ies_ano").df().fillna(0)
    d = mapear(d, "CO_IES", ies_ix, "IES")
    d = d[["ANO", "IES", "QT_UNIDADE", "QT_MUNIC_EAD", "QT_CINE"]]
    kb = escreve_colunar(d, p(WEB, "c_ies_ano.json")); total_kb += kb
    print(f"  c_ies_ano.json          {len(d):>7,} linhas                            {kb:8,.0f} KB")

    # ------------------------------------------------- detalhe por ano (lazy)
    print("\n  detalhe por ano (carregado sob demanda):")
    kb_ano = 0
    for ano in anos:
        d = con.sql(f"""SELECT CO_IES, CO_CINE_ROTULO, MOD, QT_MAT, QT_ING, QT_CONC
                        FROM c_ies_cine_mod WHERE ANO={ano} AND CO_CINE_ROTULO IS NOT NULL""").df().fillna(0)
        d = mapear(mapear(d, "CO_IES", ies_ix, "IES"), "CO_CINE_ROTULO", cur_ix, "CUR")
        d = d[["IES", "CUR", "MOD", "QT_MAT", "QT_ING", "QT_CONC"]]
        kb_ano += escreve_colunar(d, p(WEB, "ano", f"{ano}_ies_cine.json"))

        d = con.sql(f"""SELECT CO_IES, CO_MUNICIPIO, MOD, QT_MAT
                        FROM c_ies_municipio_mod WHERE ANO={ano}""").df().fillna(0)
        d = mapear(mapear(d, "CO_IES", ies_ix, "IES"), "CO_MUNICIPIO", mun_ix, "MUN")
        d = d[["IES", "MUN", "MOD", "QT_MAT"]]
        kb_ano += escreve_colunar(d, p(WEB, "ano", f"{ano}_ies_mun.json"))
    total_kb += kb_ano
    print(f"    {len(anos)*2} arquivos ({min(anos)}–{max(anos)})                          "
          f"{kb_ano:8,.0f} KB  (~{kb_ano/len(anos):,.0f} KB por ano)")

    # -------------------------------------------------------------- geojson
    src = p(CFG, "geo", "uf.geojson")
    if os.path.exists(src):
        os.makedirs(p(WEB, "geo"), exist_ok=True)
        shutil.copy(src, p(WEB, "geo", "uf.geojson"))
        kb = os.path.getsize(p(WEB, "geo", "uf.geojson")) / 1024
        total_kb += kb
        print(f"\n  geo/uf.geojson          {27:>7} UFs                               {kb:8,.0f} KB")

    inicial = sum(os.path.getsize(p(WEB, f)) for f in os.listdir(WEB)
                  if f.endswith(".json")) / 1024
    print(f"\n  {'PAYLOAD INICIAL (sem detalhe por ano)':<48} {inicial:8,.0f} KB")
    print(f"  {'TOTAL EM DISCO':<48} {total_kb:8,.0f} KB")


if __name__ == "__main__":
    main()
