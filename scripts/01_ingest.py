"""
Etapa 1 do pipeline: CSV bruto (dentro do zip) -> Parquet limpo e tipado.

Para cada ano:
  1. extrai os 2 CSVs do zip para uma pasta temporaria
  2. le com DuckDB, aplicando normalizacao de colunas e limpeza
  3. grava data_processed/fato_cursos_{ano}.parquet e dim_ies_{ano}.parquet
  4. apaga os CSVs temporarios (economiza ~2 GB)

Limpezas aplicadas:
  - CO_CINE_ROTULO2 -> CO_CINE_ROTULO (rename do INEP so em 2020)
  - remove aspas duplas literais de CO_CINE_ROTULO
  - preserva zeros a esquerda dos codigos CINE (mantidos como VARCHAR)
  - descarta linhas sem nenhuma metrica (~13% do volume, sem perda de informacao)

Uso:
  python scripts/01_ingest.py                # todos os anos encontrados
  python scripts/01_ingest.py --ano 2025     # so um ano
  python scripts/01_ingest.py --forcar       # reprocessa mesmo se o parquet existir
"""
import argparse
import os
import shutil
import sys
import time

import duckdb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.censo import (  # noqa: E402
    CATEGORIA_PUBLICA, CURSOS_OBRIGATORIAS, CURSOS_OPCIONAIS,
    IES_OBRIGATORIAS, IES_OPCIONAIS,
    caminho_zip, extrai_csv, le_cabecalho, selecao_sql,
)

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data_processed")
TMP = os.path.join(OUT, "_tmp")

READ_OPTS = "delim=';', header=true, encoding='latin-1', sample_size=-1, null_padding=true"


def anos_disponiveis():
    d = os.path.join(ROOT, "data_raw")
    if not os.path.isdir(d):
        return []
    out = []
    for nome in os.listdir(d):
        if nome.isdigit() and caminho_zip(ROOT, int(nome)):
            out.append(int(nome))
    return sorted(out)


def ingerir_ano(con, ano, forcar=False):
    alvo_cur = os.path.join(OUT, f"fato_cursos_{ano}.parquet")
    alvo_ies = os.path.join(OUT, f"dim_ies_{ano}.parquet")
    if not forcar and os.path.exists(alvo_cur) and os.path.exists(alvo_ies):
        print(f"  {ano}: ja processado (use --forcar para refazer)")
        return None

    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    rel = {"ano": ano}

    # ---------------------------------------------------------------- CURSOS
    csv_cur = extrai_csv(ROOT, ano, "CURSO", TMP)
    if not csv_cur:
        print(f"  {ano}: [ERRO] CSV de CURSOS nao encontrado no zip")
        return None
    cols = le_cabecalho(csv_cur)
    exprs, falta_obr, falta_opc = selecao_sql(cols, CURSOS_OBRIGATORIAS, CURSOS_OPCIONAIS)
    if falta_obr:
        print(f"  {ano}: [ERRO] colunas obrigatorias ausentes em CURSOS: {falta_obr}")
        os.remove(csv_cur)
        return None

    sel = ",\n         ".join(exprs)
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE cur AS
        SELECT {sel}
        FROM read_csv('{csv_cur.replace(os.sep, "/")}', {READ_OPTS});
    """)
    linhas_brutas = con.sql("SELECT count(*) FROM cur").fetchone()[0]

    # limpeza: tira aspas do codigo CINE, garante VARCHAR nos codigos com zero a esquerda,
    # e descarta linhas 100% zeradas (nao carregam informacao)
    con.execute("""
        CREATE OR REPLACE TEMP TABLE cur2 AS
        SELECT * REPLACE (
            trim(CAST(CO_CINE_ROTULO AS VARCHAR), '"')      AS CO_CINE_ROTULO,
            CAST(CO_CINE_AREA_GERAL AS VARCHAR)             AS CO_CINE_AREA_GERAL
        )
        FROM cur
        WHERE coalesce(QT_MAT,0) > 0 OR coalesce(QT_ING,0) > 0 OR coalesce(QT_CONC,0) > 0
           OR coalesce(QT_CURSO,0) > 0 OR coalesce(QT_VG_TOTAL,0) > 0
           OR coalesce(QT_INSCRITO_TOTAL,0) > 0 OR coalesce(QT_SIT_TRANCADA,0) > 0;
    """)
    linhas_uteis = con.sql("SELECT count(*) FROM cur2").fetchone()[0]
    con.execute(f"COPY cur2 TO '{alvo_cur.replace(os.sep,'/')}' (FORMAT PARQUET, COMPRESSION ZSTD);")

    tot = con.sql("""
        SELECT sum(QT_MAT) FILTER (WHERE TP_DIMENSAO IN (1,2,4)) mat,
               sum(QT_ING) FILTER (WHERE TP_DIMENSAO IN (1,2,4)) ing,
               sum(QT_CONC) FILTER (WHERE TP_DIMENSAO IN (1,2,4)) conc,
               sum(QT_CURSO) FILTER (WHERE TP_DIMENSAO IN (1,3)) cursos,
               count(DISTINCT CO_IES) ies
        FROM cur2""").fetchone()
    rel.update(linhas_brutas=linhas_brutas, linhas_uteis=linhas_uteis,
               matriculas=tot[0], ingressantes=tot[1], concluintes=tot[2],
               cursos=tot[3], ies=tot[4], falta_opc_cursos=falta_opc)
    os.remove(csv_cur)

    # ------------------------------------------------------------------- IES
    csv_ies = extrai_csv(ROOT, ano, "IES", TMP)
    if not csv_ies:
        print(f"  {ano}: [ERRO] CSV de IES nao encontrado no zip")
        return rel
    cols_i = le_cabecalho(csv_ies)
    exprs_i, falta_obr_i, falta_opc_i = selecao_sql(cols_i, IES_OBRIGATORIAS, IES_OPCIONAIS)
    if falta_obr_i:
        print(f"  {ano}: [ERRO] colunas obrigatorias ausentes em IES: {falta_obr_i}")
        os.remove(csv_ies)
        return rel
    sel_i = ",\n         ".join(exprs_i)
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE ies AS
        SELECT {sel_i} FROM read_csv('{csv_ies.replace(os.sep,"/")}', {READ_OPTS});
    """)
    # TP_REDE so existe na tabela IES a partir de 2023 -> deriva da categoria administrativa
    pub = ",".join(str(c) for c in CATEGORIA_PUBLICA)
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE ies2 AS
        SELECT * REPLACE (
            coalesce(TP_REDE,
                     CASE WHEN TP_CATEGORIA_ADMINISTRATIVA IN ({pub}) THEN 1 ELSE 2 END
            ) AS TP_REDE
        ) FROM ies;
    """)
    con.execute(f"COPY ies2 TO '{alvo_ies.replace(os.sep,'/')}' (FORMAT PARQUET, COMPRESSION ZSTD);")
    rel["ies_cadastro"] = con.sql("SELECT count(*) FROM ies2").fetchone()[0]
    rel["tp_rede_derivada"] = "TP_REDE" in falta_opc_i
    rel["falta_opc_ies"] = [c for c in falta_opc_i if c != "TP_REDE"]
    os.remove(csv_ies)

    rel["segundos"] = time.time() - t0
    rel["mb_parquet"] = (os.path.getsize(alvo_cur) + os.path.getsize(alvo_ies)) / 1024 / 1024
    return rel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ano", type=int, help="processa apenas este ano")
    ap.add_argument("--forcar", action="store_true", help="reprocessa mesmo se ja existir")
    args = ap.parse_args()

    anos = [args.ano] if args.ano else anos_disponiveis()
    if not anos:
        print("Nenhum zip encontrado em data_raw/{ano}/")
        return

    print(f"Anos a processar: {anos}\n")
    con = duckdb.connect()
    con.execute("SET preserve_insertion_order=false;")
    con.execute("SET memory_limit='4GB';")

    relatorios = []
    for ano in anos:
        print(f"[{ano}] processando...")
        r = ingerir_ano(con, ano, args.forcar)
        if r and "mb_parquet" in r:
            relatorios.append(r)
            print(f"  {ano}: {r['linhas_brutas']:>9,} -> {r['linhas_uteis']:>9,} linhas uteis "
                  f"| {r['matriculas']:>10,.0f} matriculas | {r['mb_parquet']:5.1f} MB "
                  f"| {r['segundos']:5.1f}s")
            if r.get("tp_rede_derivada"):
                print("       TP_REDE ausente na tabela IES -> derivada de TP_CATEGORIA_ADMINISTRATIVA")
            if r.get("falta_opc_cursos"):
                print(f"       colunas opcionais ausentes (CURSOS): {r['falta_opc_cursos']}")
            if r.get("falta_opc_ies"):
                print(f"       colunas opcionais ausentes (IES)   : {r['falta_opc_ies']}")
        elif r:
            print(f"  {ano}: [FALHA] ingestao interrompida — ver erro acima")

    if os.path.isdir(TMP):
        shutil.rmtree(TMP, ignore_errors=True)

    if relatorios:
        print("\n" + "=" * 104)
        print("SERIE HISTORICA CONSOLIDADA")
        print("=" * 104)
        print(f"{'ANO':>5} {'MATRICULAS':>12} {'INGRESS.':>11} {'CONCL.':>10} "
              f"{'CURSOS':>8} {'IES':>6} {'LINHAS':>10} {'MB':>6}")
        for r in relatorios:
            print(f"{r['ano']:>5} {r['matriculas']:>12,.0f} {r['ingressantes']:>11,.0f} "
                  f"{r['concluintes']:>10,.0f} {r['cursos']:>8,.0f} {r['ies']:>6,} "
                  f"{r['linhas_uteis']:>10,} {r['mb_parquet']:>6.1f}")
        tot_mb = sum(r["mb_parquet"] for r in relatorios)
        print(f"\nTotal em Parquet: {tot_mb:,.1f} MB")


if __name__ == "__main__":
    main()
