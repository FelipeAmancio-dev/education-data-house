"""
Etapa 2 do pipeline: Parquet de microdados -> dimensoes + cubos agregados.

Le todos os data_processed/fato_cursos_*.parquet e produz:

  DIMENSOES
    dim_ies.parquet          IES x ano, com GRUPO aplicado (pro-forma) e mantenedora
    dim_curso.parquet        rotulos CINE e hierarquia de area
    dim_municipio.parquet    municipios com oferta, com lat/lon do IBGE

  CUBOS "HISTORICOS" (todos os anos juntos, pequenos, sempre carregados)
    cubo_ies_mod.parquet         ano x IES x modalidade
    cubo_cine_mod.parquet        ano x curso CINE x modalidade
    cubo_municipio_mod.parquet   ano x municipio x modalidade
    cubo_cine_uf_mod.parquet     ano x curso CINE x UF x modalidade
    cubo_kpi_ano.parquet         KPIs nacionais por ano

  CUBOS "DETALHE" (por ano, carregados sob demanda)
    cubo_ies_cine_mod.parquet       ano x IES x CINE x modalidade
    cubo_ies_municipio_mod.parquet  ano x IES x municipio x modalidade

Grupo economico e aplicado PRO-FORMA: o perimetro atual de config/ies_grupo_map.csv
vale para toda a serie historica. E o que permite ler evolucao de market share sem
quebras artificiais por M&A. Ver docs/03_arquitetura.md.

Uso:  python scripts/02_build_cubes.py
"""
import glob
import os
import sys
import time

import duckdb
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.censo import DIM_ALUNOS, DIM_GEO, DIM_OFERTA  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data_processed")
CUBOS = os.path.join(PROC, "cubos")
CFG = os.path.join(ROOT, "config")


def lst(t):
    return ",".join(str(x) for x in t)


def main():
    t0 = time.time()
    os.makedirs(CUBOS, exist_ok=True)

    fatos = sorted(glob.glob(os.path.join(PROC, "fato_cursos_*.parquet")))
    dims_ies = sorted(glob.glob(os.path.join(PROC, "dim_ies_*.parquet")))
    if not fatos:
        print("Nenhum fato_cursos_*.parquet encontrado. Rode scripts/01_ingest.py antes.")
        return
    print(f"Fatos encontrados: {len(fatos)} anos")

    con = duckdb.connect()
    con.execute("SET preserve_insertion_order=false;")
    con.execute("SET memory_limit='4GB';")

    g = os.path.join(PROC, "fato_cursos_*.parquet").replace(os.sep, "/")
    gi = os.path.join(PROC, "dim_ies_*.parquet").replace(os.sep, "/")
    con.execute(f"CREATE VIEW f AS SELECT * FROM read_parquet('{g}');")
    con.execute(f"CREATE VIEW ies_raw AS SELECT * FROM read_parquet('{gi}');")

    # ------------------------------------------------------------- mapeamento
    mapa = pd.read_csv(os.path.join(CFG, "ies_grupo_map.csv"), sep=";", encoding="utf-8-sig")
    for c in ("GRUPO", "GRUPO_CONSOLIDADO", "MARCA"):
        if c in mapa.columns:
            mapa[c] = mapa[c].fillna("")
    cols_mapa = ["CO_IES", "GRUPO", "GRUPO_CONSOLIDADO"] + (["MARCA"] if "MARCA" in mapa.columns else [])
    con.register("mapa", mapa[cols_mapa])

    munic_path = os.path.join(CFG, "municipios_ibge.csv")
    tem_geo = os.path.exists(munic_path)
    if tem_geo:
        con.execute(f"""CREATE VIEW mun_ibge AS SELECT * FROM
                        read_csv('{munic_path.replace(os.sep,'/')}', delim=';', header=true);""")

    anos = con.sql("SELECT DISTINCT NU_ANO_CENSO FROM f ORDER BY 1").df()["NU_ANO_CENSO"].tolist()
    print(f"Anos na base: {min(anos)}–{max(anos)}\n")

    # ================================================================ DIMENSOES
    print("DIMENSOES")
    con.execute(f"""
        COPY (
          SELECT i.NU_ANO_CENSO AS ANO, i.CO_IES, i.NO_IES, i.SG_IES,
                 i.CO_MANTENEDORA, i.NO_MANTENEDORA,
                 i.TP_REDE, i.TP_CATEGORIA_ADMINISTRATIVA, i.TP_ORGANIZACAO_ACADEMICA,
                 i.SG_UF_IES, i.NO_MUNICIPIO_IES, i.CO_MUNICIPIO_IES, i.NO_REGIAO_IES,
                 i.QT_DOC_TOTAL, i.QT_DOC_EXE, i.QT_DOC_EX_DOUT, i.QT_DOC_EX_MEST, i.QT_TEC_TOTAL,
                 coalesce(nullif(m.GRUPO,''), 'Independentes')             AS GRUPO,
                 coalesce(nullif(m.GRUPO_CONSOLIDADO,''), 'Independentes') AS GRUPO_CONSOLIDADO
          FROM ies_raw i LEFT JOIN mapa m ON m.CO_IES = i.CO_IES
        ) TO '{os.path.join(PROC,'dim_ies.parquet').replace(os.sep,'/')}'
          (FORMAT PARQUET, COMPRESSION ZSTD);
    """)
    n = con.sql(f"SELECT count(*) FROM read_parquet('{os.path.join(PROC,'dim_ies.parquet').replace(os.sep,'/')}')").fetchone()[0]
    print(f"  dim_ies.parquet          {n:>9,} linhas (IES x ano)")

    con.execute(f"""
        COPY (
          SELECT CO_CINE_ROTULO, any_value(NO_CINE_ROTULO) AS NO_CINE_ROTULO,
                 any_value(CO_CINE_AREA_GERAL) AS CO_CINE_AREA_GERAL,
                 any_value(NO_CINE_AREA_GERAL) AS NO_CINE_AREA_GERAL,
                 any_value(NO_CINE_AREA_ESPECIFICA) AS NO_CINE_AREA_ESPECIFICA,
                 any_value(NO_CINE_AREA_DETALHADA) AS NO_CINE_AREA_DETALHADA,
                 min(NU_ANO_CENSO) AS ANO_MIN, max(NU_ANO_CENSO) AS ANO_MAX
          FROM f WHERE CO_CINE_ROTULO IS NOT NULL GROUP BY 1
        ) TO '{os.path.join(PROC,'dim_curso.parquet').replace(os.sep,'/')}'
          (FORMAT PARQUET, COMPRESSION ZSTD);
    """)
    n = con.sql(f"SELECT count(*) FROM read_parquet('{os.path.join(PROC,'dim_curso.parquet').replace(os.sep,'/')}')").fetchone()[0]
    print(f"  dim_curso.parquet        {n:>9,} rotulos CINE")

    join_geo = ("LEFT JOIN mun_ibge g ON g.CO_MUNICIPIO = x.CO_MUNICIPIO" if tem_geo else "")
    sel_geo = ("g.LATITUDE, g.LONGITUDE, g.NO_MESORREGIAO" if tem_geo
               else "CAST(NULL AS DOUBLE) AS LATITUDE, CAST(NULL AS DOUBLE) AS LONGITUDE, "
                    "CAST(NULL AS VARCHAR) AS NO_MESORREGIAO")
    con.execute(f"""
        COPY (
          SELECT x.CO_MUNICIPIO, x.NO_MUNICIPIO, x.SG_UF, x.CO_UF, x.NO_REGIAO, {sel_geo}
          FROM (SELECT CO_MUNICIPIO, any_value(NO_MUNICIPIO) NO_MUNICIPIO,
                       any_value(SG_UF) SG_UF, any_value(CO_UF) CO_UF,
                       any_value(NO_REGIAO) NO_REGIAO
                FROM f WHERE CO_MUNICIPIO IS NOT NULL GROUP BY 1) x
          {join_geo}
        ) TO '{os.path.join(PROC,'dim_municipio.parquet').replace(os.sep,'/')}'
          (FORMAT PARQUET, COMPRESSION ZSTD);
    """)
    n, sem = con.sql(f"""SELECT count(*), count(*) FILTER (WHERE LATITUDE IS NULL)
                         FROM read_parquet('{os.path.join(PROC,'dim_municipio.parquet').replace(os.sep,'/')}')""").fetchone()
    print(f"  dim_municipio.parquet    {n:>9,} municipios ({sem} sem coordenada)")

    # ================================================================== CUBOS
    # Metricas de aluno (dims 1,2,4) e de oferta (dims 1,3) sao calculadas com
    # filtros diferentes na MESMA agregacao, via FILTER — nunca somadas juntas.
    METRICAS = f"""
        sum(QT_MAT)          FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_ALUNOS)})) AS QT_MAT,
        sum(QT_ING)          FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_ALUNOS)})) AS QT_ING,
        sum(QT_CONC)         FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_ALUNOS)})) AS QT_CONC,
        sum(QT_SIT_TRANCADA) FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_ALUNOS)})) AS QT_TRANCADA,
        sum(QT_CURSO)        FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_OFERTA)})) AS QT_CURSO,
        sum(QT_VG_TOTAL)     FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_OFERTA)})) AS QT_VAGA,
        sum(QT_INSCRITO_TOTAL) FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_OFERTA)})) AS QT_INSCRITO
    """
    ALUNOS_ONLY = f"""
        sum(QT_MAT)          AS QT_MAT,
        sum(QT_ING)          AS QT_ING,
        sum(QT_CONC)         AS QT_CONC,
        sum(QT_SIT_TRANCADA) AS QT_TRANCADA
    """

    print("\nCUBOS HISTORICOS (todos os anos)")
    cubos = [
        ("cubo_ies_mod",
         f"""SELECT NU_ANO_CENSO AS ANO, CO_IES, TP_MODALIDADE_ENSINO AS MOD, {METRICAS}
             FROM f GROUP BY 1,2,3"""),
        ("cubo_cine_mod",
         f"""SELECT NU_ANO_CENSO AS ANO, CO_CINE_ROTULO, TP_MODALIDADE_ENSINO AS MOD, {METRICAS}
             FROM f GROUP BY 1,2,3"""),
        ("cubo_municipio_mod",
         f"""SELECT NU_ANO_CENSO AS ANO, CO_MUNICIPIO, TP_MODALIDADE_ENSINO AS MOD, {ALUNOS_ONLY}
             FROM f WHERE TP_DIMENSAO IN ({lst(DIM_GEO)}) AND CO_MUNICIPIO IS NOT NULL
             GROUP BY 1,2,3"""),
        ("cubo_cine_uf_mod",
         f"""SELECT NU_ANO_CENSO AS ANO, CO_CINE_ROTULO, CO_UF, TP_MODALIDADE_ENSINO AS MOD, {ALUNOS_ONLY}
             FROM f WHERE TP_DIMENSAO IN ({lst(DIM_GEO)}) AND CO_UF IS NOT NULL
             GROUP BY 1,2,3,4"""),
        ("cubo_grau_mod",
         f"""SELECT NU_ANO_CENSO AS ANO, TP_GRAU_ACADEMICO AS GRAU,
                    TP_MODALIDADE_ENSINO AS MOD, TP_REDE, {METRICAS}
             FROM f GROUP BY 1,2,3,4"""),
        # unidades = proxy de campus (pares distintos IES x municipio no presencial)
        # e municipios com oferta EAD (proxy de pegada de polos). Ver docs/02 §8.
        ("cubo_ies_ano",
         f"""SELECT NU_ANO_CENSO AS ANO, CO_IES,
                    count(DISTINCT CASE WHEN TP_DIMENSAO=1 THEN CO_MUNICIPIO END) AS QT_UNIDADE,
                    count(DISTINCT CASE WHEN TP_DIMENSAO=2 AND QT_MAT>0 THEN CO_MUNICIPIO END) AS QT_MUNIC_EAD,
                    count(DISTINCT CO_CINE_ROTULO) AS QT_CINE
             FROM f GROUP BY 1,2"""),
    ]
    for nome, sql in cubos:
        p = os.path.join(CUBOS, f"{nome}.parquet").replace(os.sep, "/")
        con.execute(f"COPY ({sql}) TO '{p}' (FORMAT PARQUET, COMPRESSION ZSTD);")
        n = con.sql(f"SELECT count(*) FROM read_parquet('{p}')").fetchone()[0]
        mb = os.path.getsize(p) / 1024 / 1024
        print(f"  {nome:26s} {n:>9,} linhas  {mb:6.2f} MB")

    print("\nCUBOS DE DETALHE (por ano, sob demanda)")
    detalhe = [
        ("cubo_ies_cine_mod",
         f"""SELECT NU_ANO_CENSO AS ANO, CO_IES, CO_CINE_ROTULO, TP_MODALIDADE_ENSINO AS MOD, {METRICAS}
             FROM f GROUP BY 1,2,3,4"""),
        ("cubo_ies_municipio_mod",
         f"""SELECT NU_ANO_CENSO AS ANO, CO_IES, CO_MUNICIPIO, TP_MODALIDADE_ENSINO AS MOD, {ALUNOS_ONLY}
             FROM f WHERE TP_DIMENSAO IN ({lst(DIM_GEO)}) AND CO_MUNICIPIO IS NOT NULL
             GROUP BY 1,2,3,4"""),
    ]
    for nome, sql in detalhe:
        p = os.path.join(CUBOS, f"{nome}.parquet").replace(os.sep, "/")
        con.execute(f"COPY ({sql}) TO '{p}' (FORMAT PARQUET, COMPRESSION ZSTD, "
                    f"PARTITION_BY (ANO), OVERWRITE_OR_IGNORE);") if False else \
            con.execute(f"COPY ({sql}) TO '{p}' (FORMAT PARQUET, COMPRESSION ZSTD);")
        n = con.sql(f"SELECT count(*) FROM read_parquet('{p}')").fetchone()[0]
        mb = os.path.getsize(p) / 1024 / 1024
        print(f"  {nome:26s} {n:>9,} linhas  {mb:6.2f} MB")

    # --------------------------------------------------------------- KPI/ano
    p = os.path.join(CUBOS, "cubo_kpi_ano.parquet").replace(os.sep, "/")
    con.execute(f"""
        COPY (
          SELECT NU_ANO_CENSO AS ANO,
            sum(QT_MAT)  FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_ALUNOS)}))                              AS MAT_TOTAL,
            sum(QT_MAT)  FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_ALUNOS)}) AND TP_MODALIDADE_ENSINO=1)   AS MAT_PRESENCIAL,
            sum(QT_MAT)  FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_ALUNOS)}) AND TP_MODALIDADE_ENSINO=2)   AS MAT_EAD,
            sum(QT_MAT)  FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_ALUNOS)}) AND TP_REDE=1)                AS MAT_PUBLICA,
            sum(QT_MAT)  FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_ALUNOS)}) AND TP_REDE=2)                AS MAT_PRIVADA,
            sum(QT_ING)  FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_ALUNOS)}))                              AS INGRESSANTES,
            sum(QT_CONC) FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_ALUNOS)}))                              AS CONCLUINTES,
            sum(QT_SIT_TRANCADA) FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_ALUNOS)}))                      AS TRANCADOS,
            -- Financiamento estudantil. Estava nos microdados desde sempre e nunca tinha
            -- sido exposto; entrou em 18/08/2026 para o gráfico do FIES no bloco
            -- Regulatório. FIES e ProUni sao politica publica, e a serie deles e a medida
            -- do efeito que uma decisao regulatoria tem sobre a receita do setor privado.
            sum(QT_MAT_FIES) FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_ALUNOS)}))                          AS MAT_FIES,
            sum(QT_MAT_FIES) FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_ALUNOS)}) AND TP_REDE=2)            AS MAT_FIES_PRIVADA,
            sum(QT_ING_FIES) FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_ALUNOS)}))                          AS ING_FIES,
            sum(QT_MAT_PROUNII) FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_ALUNOS)}))                       AS MAT_PROUNI_INTEGRAL,
            sum(QT_MAT_PROUNIP) FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_ALUNOS)}))                       AS MAT_PROUNI_PARCIAL,
            sum(QT_CURSO) FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_OFERTA)}))                             AS CURSOS,
            sum(QT_VG_TOTAL) FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_OFERTA)}))                          AS VAGAS,
            count(DISTINCT CO_IES)                                                                      AS IES,
            count(DISTINCT CASE WHEN TP_DIMENSAO=1 THEN CO_MUNICIPIO END)                               AS MUNIC_PRESENCIAL,
            count(DISTINCT CASE WHEN TP_DIMENSAO=2 THEN CO_MUNICIPIO END)                               AS MUNIC_EAD
          FROM f GROUP BY 1 ORDER BY 1
        ) TO '{p}' (FORMAT PARQUET, COMPRESSION ZSTD);
    """)
    print(f"\n  cubo_kpi_ano.parquet     {len(anos):>9,} anos")

    tot_mb = sum(os.path.getsize(x) for x in glob.glob(os.path.join(CUBOS, "*.parquet"))) / 1024 / 1024
    print(f"\nTotal dos cubos: {tot_mb:,.1f} MB   |   tempo: {time.time()-t0:.1f}s")

    print("\n" + "=" * 100)
    print("SERIE HISTORICA NACIONAL")
    print("=" * 100)
    d = con.sql(f"""SELECT ANO, MAT_TOTAL, MAT_PRESENCIAL, MAT_EAD,
                    round(100.0*MAT_EAD/MAT_TOTAL,1) AS PCT_EAD,
                    MAT_PRIVADA, round(100.0*MAT_PRIVADA/MAT_TOTAL,1) AS PCT_PRIV,
                    INGRESSANTES, CONCLUINTES, CURSOS, IES
                    FROM read_parquet('{p}') ORDER BY ANO""").df()
    print(d.to_string(index=False))


if __name__ == "__main__":
    main()
