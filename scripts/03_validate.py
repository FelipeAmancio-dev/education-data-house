"""
Etapa 3 do pipeline: validacao da serie historica.

Executa o checklist de docs/02_qualidade_dados.md §10 para TODOS os anos e grava
outputs/validation_report.md. Sai com codigo 1 se qualquer checagem critica falhar,
para poder ser usado como gate de build.

Checagens criticas (falham o build):
  - presencial + EAD = total, por ano
  - publica + privada = total, por ano
  - soma dos municipios + sem-municipio = total, por ano
  - soma das areas CINE = total, por ano
  - cubos reconciliam com os microdados
  - nenhuma metrica negativa
  - nenhum CO_IES duplicado dentro de um ano na dim_ies

Checagens de alerta (nao falham, mas sao reportadas):
  - variacao YoY fora de faixa esperada
  - taxa de trancamento instavel por grupo (risco de artefato na serie)
  - cobertura do mapeamento de grupos por ano

Uso:  python scripts/03_validate.py
"""
import glob
import os
import sys

import duckdb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.censo import DIM_ALUNOS, DIM_GEO, DIM_OFERTA  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data_processed")
CUBOS = os.path.join(PROC, "cubos")
OUT = os.path.join(ROOT, "outputs", "validation_report.md")

TOL = 0.5  # tolerancia absoluta (alunos) para igualdades que devem fechar exatamente


def lst(t):
    return ",".join(str(x) for x in t)


def main():
    con = duckdb.connect()
    g = os.path.join(PROC, "fato_cursos_*.parquet").replace(os.sep, "/")
    if not glob.glob(os.path.join(PROC, "fato_cursos_*.parquet")):
        print("Nada a validar. Rode scripts/01_ingest.py antes.")
        sys.exit(1)
    con.execute(f"CREATE VIEW f AS SELECT * FROM read_parquet('{g}');")
    con.execute(f"CREATE VIEW kpi AS SELECT * FROM read_parquet('{os.path.join(CUBOS,'cubo_kpi_ano.parquet').replace(os.sep,'/')}');")
    con.execute(f"CREATE VIEW dim_ies AS SELECT * FROM read_parquet('{os.path.join(PROC,'dim_ies.parquet').replace(os.sep,'/')}');")

    falhas, alertas = [], []
    L = ["# Relatório de Validação — série 2015–2024\n",
         "> Gerado por `scripts/03_validate.py`. Reproduzir: `python scripts/03_validate.py`\n"]

    # ---------------------------------------------------------- 1. fechamentos
    L.append("\n## 1. Fechamentos por ano (checagens críticas)\n")
    d = con.sql(f"""
        SELECT NU_ANO_CENSO AS ANO,
          sum(QT_MAT) FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_ALUNOS)}))                            AS total,
          sum(QT_MAT) FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_ALUNOS)}) AND TP_MODALIDADE_ENSINO=1) AS pres,
          sum(QT_MAT) FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_ALUNOS)}) AND TP_MODALIDADE_ENSINO=2) AS ead,
          sum(QT_MAT) FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_ALUNOS)}) AND TP_REDE=1)              AS pub,
          sum(QT_MAT) FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_ALUNOS)}) AND TP_REDE=2)              AS priv,
          sum(QT_MAT) FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_ALUNOS)}) AND CO_UF IS NOT NULL)      AS com_uf,
          sum(QT_MAT) FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_ALUNOS)}) AND CO_UF IS NULL)          AS sem_uf,
          sum(QT_MAT) FILTER (WHERE TP_DIMENSAO IN ({lst(DIM_ALUNOS)}) AND CO_CINE_AREA_GERAL IS NOT NULL) AS com_cine
        FROM f GROUP BY 1 ORDER BY 1
    """).df()
    L.append("| Ano | Total | Pres+EAD | Pub+Priv | UF+s/UF | Área CINE |")
    L.append("|---|---:|:--:|:--:|:--:|:--:|")
    # sum() de conjunto vazio devolve NULL, nao 0 (ex.: 2015/2016 nao tem linhas de
    # dimensao 4), entao os componentes precisam ser coalescidos antes de somar.
    z = lambda v: 0.0 if v != v else float(v)  # noqa: E731  (v!=v detecta NaN)
    for r in d.itertuples():
        c1 = abs((z(r.pres) + z(r.ead)) - z(r.total)) < TOL
        c2 = abs((z(r.pub) + z(r.priv)) - z(r.total)) < TOL
        c3 = abs((z(r.com_uf) + z(r.sem_uf)) - z(r.total)) < TOL
        c4 = abs(z(r.com_cine) - z(r.total)) < TOL
        for ok, nome in ((c1, "presencial+EAD"), (c2, "pública+privada"),
                         (c3, "UF+sem-UF"), (c4, "área CINE")):
            if not ok:
                falhas.append(f"{r.ANO}: {nome} não fecha com o total")
        m = lambda b: "✅" if b else "❌"  # noqa: E731
        L.append(f"| {r.ANO} | {r.total:,.0f} | {m(c1)} | {m(c2)} | {m(c3)} | {m(c4)} |")

    # ------------------------------------------------- 2. cubos vs microdados
    L.append("\n## 2. Cubos reconciliam com os microdados\n")
    L.append("| Cubo | Δ matrículas vs. fato |")
    L.append("|---|---:|")
    base = {int(r.ANO): float(r.total) for r in d.itertuples()}
    for nome, filtro in [("cubo_ies_mod", None),
                         ("cubo_cine_mod", None),
                         ("cubo_municipio_mod", "geo"),
                         ("cubo_ies_cine_mod", None)]:
        p = os.path.join(CUBOS, f"{nome}.parquet").replace(os.sep, "/")
        if not os.path.exists(p):
            continue
        cub = con.sql(f"SELECT ANO, sum(QT_MAT) v FROM read_parquet('{p}') GROUP BY 1").df()
        pior, pior_ano = 0.0, None
        for r in cub.itertuples():
            ref = base.get(int(r.ANO), 0)
            if filtro == "geo":
                ref = float(con.sql(f"""SELECT sum(QT_MAT) FROM f WHERE NU_ANO_CENSO={int(r.ANO)}
                    AND TP_DIMENSAO IN ({lst(DIM_GEO)}) AND CO_MUNICIPIO IS NOT NULL""").fetchone()[0])
            dif = abs(float(r.v) - ref)
            if dif > pior:
                pior, pior_ano = dif, int(r.ANO)
        ok = pior < TOL
        if not ok:
            falhas.append(f"{nome}: diverge do fato em {pior:,.0f} alunos (pior ano {pior_ano})")
        L.append(f"| `{nome}` | {'✅ 0' if ok else f'❌ {pior:,.0f} ({pior_ano})'} |")

    # ------------------------------------------------------- 3. sanidade geral
    L.append("\n## 3. Sanidade dos dados\n")
    neg = con.sql("""SELECT count(*) FROM f WHERE QT_MAT<0 OR QT_ING<0 OR QT_CONC<0
                     OR QT_CURSO<0 OR QT_VG_TOTAL<0 OR QT_SIT_TRANCADA<0""").fetchone()[0]
    if neg:
        falhas.append(f"{neg} linhas com métrica negativa")
    dup = con.sql("SELECT count(*) FROM (SELECT ANO, CO_IES FROM dim_ies GROUP BY 1,2 HAVING count(*)>1)").fetchone()[0]
    if dup:
        falhas.append(f"{dup} pares (ano, CO_IES) duplicados em dim_ies")
    dup_f = con.sql("""SELECT count(*) FROM (SELECT NU_ANO_CENSO, CO_CURSO, TP_DIMENSAO, CO_MUNICIPIO
                       FROM f GROUP BY 1,2,3,4 HAVING count(*)>1)""").fetchone()[0]
    if dup_f:
        falhas.append(f"{dup_f} chaves duplicadas no fato (ano, curso, dimensão, município)")
    L.append(f"- Métricas negativas: **{neg}** {'✅' if neg == 0 else '❌'}")
    L.append(f"- `(ano, CO_IES)` duplicados em `dim_ies`: **{dup}** {'✅' if dup == 0 else '❌'}")
    L.append(f"- Chave do fato duplicada: **{dup_f}** {'✅' if dup_f == 0 else '❌'}")

    # Dimensoes 3 e 4 nao deveriam ter geografia (ver docs/01 §2). Em alguns anos o INEP
    # preenche CO_UF nelas. Nao contamina os cubos (a geografia usa so dims 1 e 2), mas
    # e uma inconsistencia da fonte que precisa ficar registrada.
    geo34 = con.sql("""SELECT NU_ANO_CENSO AS ano, count(*) n FROM f
                       WHERE TP_DIMENSAO IN (3,4) AND CO_UF IS NOT NULL
                       GROUP BY 1 ORDER BY 1""").df()
    if len(geo34):
        anos_txt = ", ".join(f"{int(r.ano)} ({r.n:,} linhas)" for r in geo34.itertuples())
        alertas.append(f"dimensões 3/4 com CO_UF preenchido (não deveriam ter geografia): {anos_txt}")
        L.append(f"- Dimensões 3/4 com geografia indevida: ⚠️ {anos_txt} — "
                 f"sem impacto nos cubos, que usam apenas dims 1 e 2 para recorte geográfico")
    else:
        L.append("- Dimensões 3/4 sem geografia indevida: **0** ✅")

    # -------------------------------------------------- 4. variacao YoY (alerta)
    L.append("\n## 4. Variação ano a ano (alerta se fora de ±15%)\n")
    L.append("| Ano | Matrículas | YoY | Presencial YoY | EAD YoY |")
    L.append("|---|---:|---:|---:|---:|")
    k = con.sql("SELECT * FROM kpi ORDER BY ANO").df()
    for i, r in enumerate(k.itertuples()):
        if i == 0:
            L.append(f"| {r.ANO} | {r.MAT_TOTAL:,.0f} | — | — | — |")
            continue
        p = k.iloc[i - 1]
        yoy = 100 * (r.MAT_TOTAL - p.MAT_TOTAL) / p.MAT_TOTAL
        yp = 100 * (r.MAT_PRESENCIAL - p.MAT_PRESENCIAL) / p.MAT_PRESENCIAL
        ye = 100 * (r.MAT_EAD - p.MAT_EAD) / p.MAT_EAD
        if abs(yoy) > 15:
            alertas.append(f"{r.ANO}: variação total de {yoy:+.1f}% — verificar")
        L.append(f"| {r.ANO} | {r.MAT_TOTAL:,.0f} | {yoy:+.1f}% | {yp:+.1f}% | {ye:+.1f}% |")

    # ------------------------- 5. estabilidade da taxa de trancamento por grupo
    L.append("\n## 5. Taxa de trancamento por grupo ao longo do tempo\n")
    L.append("Risco material para a série: se um grupo **mudar sua prática de classificação** de "
             "trancados entre anos, o crescimento em `QT_MAT` vira artefato contábil e não "
             "movimento de mercado. A tabela abaixo existe para detectar isso.\n")
    tr = con.sql(f"""
        SELECT di.GRUPO, f.NU_ANO_CENSO AS ANO,
               round(100.0*sum(f.QT_SIT_TRANCADA)/nullif(sum(f.QT_MAT),0),1) AS pct
        FROM f JOIN dim_ies di ON di.CO_IES=f.CO_IES AND di.ANO=f.NU_ANO_CENSO
        WHERE f.TP_DIMENSAO IN ({lst(DIM_ALUNOS)}) AND di.GRUPO <> 'Independentes'
        GROUP BY 1,2
    """).df()
    piv = tr.pivot(index="GRUPO", columns="ANO", values="pct")
    principais = ["Cogna", "Vitru", "YDUQS", "Cruzeiro do Sul", "Ser Educacional", "Ânima", "Afya"]
    piv = piv.reindex([x for x in principais if x in piv.index])
    anos_c = sorted(piv.columns)
    L.append("| Grupo | " + " | ".join(str(a) for a in anos_c) + " | Δ max |")
    L.append("|---" * (len(anos_c) + 2) + "|")
    for grupo, row in piv.iterrows():
        vals = [row[a] for a in anos_c]
        validos = [v for v in vals if v == v]
        amp = (max(validos) - min(validos)) if validos else 0
        if amp > 25:
            alertas.append(f"{grupo}: taxa de trancamento varia {amp:.0f} p.p. na série — "
                           f"possível mudança de critério de declaração")
        L.append(f"| {grupo} | " + " | ".join("—" if v != v else f"{v:.0f}%" for v in vals)
                 + f" | **{amp:.0f} p.p.** |")

    # ------------------------ 5b. divergencia QT_MAT vs BASE (deteccao de artefato)
    L.append("\n## 5b. Crescimento em `QT_MAT` vs. em base de alunos\n")
    L.append("Teste direto de artefato. Se a base (`QT_MAT` + trancados) cai enquanto `QT_MAT` "
             "fica estável — ou vice-versa — o movimento é **reclassificação de vínculo**, não "
             "ganho ou perda real de aluno. Sinalizado quando as duas taxas divergem mais de "
             "12 p.p. no mesmo ano.\n")
    sb = con.sql(f"""
        SELECT di.GRUPO, f.NU_ANO_CENSO AS ANO, sum(f.QT_MAT) AS MAT,
               sum(f.QT_MAT + coalesce(f.QT_SIT_TRANCADA,0)) AS BASE
        FROM f JOIN dim_ies di ON di.CO_IES=f.CO_IES AND di.ANO=f.NU_ANO_CENSO
        WHERE f.TP_DIMENSAO IN ({lst(DIM_ALUNOS)}) AND di.GRUPO <> 'Independentes'
        GROUP BY 1,2 ORDER BY 1,2
    """).df()
    achados = []
    for grupo in [g for g in principais if g in set(sb["GRUPO"])]:
        gg = sb[sb["GRUPO"] == grupo].sort_values("ANO").reset_index(drop=True)
        for i in range(1, len(gg)):
            ym = 100 * (gg.MAT[i] - gg.MAT[i - 1]) / gg.MAT[i - 1]
            yb = 100 * (gg.BASE[i] - gg.BASE[i - 1]) / gg.BASE[i - 1]
            if abs(ym - yb) > 12:
                achados.append((grupo, int(gg.ANO[i]), ym, yb, ym - yb))
    if achados:
        L.append("| Grupo | Ano | YoY `QT_MAT` | YoY base | Divergência |")
        L.append("|---|---:|---:|---:|---:|")
        for grupo, ano, ym, yb, dv in achados:
            L.append(f"| {grupo} | {ano} | {ym:+.1f}% | {yb:+.1f}% | **{dv:+.1f} p.p.** |")
            alertas.append(f"{grupo} {ano}: QT_MAT {ym:+.1f}% vs base {yb:+.1f}% "
                           f"({dv:+.1f} p.p.) — provável reclassificação, não movimento real")
        L.append("\n> **Como ler:** nesses anos, o crescimento reportado pelo Censo para o grupo "
                 "não deve ser interpretado como ganho/perda de mercado sem antes olhar a base "
                 "de alunos. Use a definição de base de alunos para a série desses grupos.\n")
    else:
        L.append("Nenhuma divergência acima de 12 p.p. detectada. ✅\n")

    # ------------------------------------------ 6. cobertura do mapeamento/ano
    L.append("\n## 6. Cobertura do mapeamento de grupos por ano\n")
    cov = con.sql(f"""
        SELECT f.NU_ANO_CENSO AS ANO,
          round(100.0*sum(f.QT_MAT) FILTER (WHERE di.GRUPO<>'Independentes')/sum(f.QT_MAT),1) AS pct_total,
          round(100.0*sum(f.QT_MAT) FILTER (WHERE di.GRUPO<>'Independentes')
                /nullif(sum(f.QT_MAT) FILTER (WHERE di.TP_REDE=2),0),1)                       AS pct_privada,
          count(DISTINCT CASE WHEN di.GRUPO='Independentes' THEN f.CO_IES END)                AS ies_sem_grupo
        FROM f JOIN dim_ies di ON di.CO_IES=f.CO_IES AND di.ANO=f.NU_ANO_CENSO
        WHERE f.TP_DIMENSAO IN ({lst(DIM_ALUNOS)}) GROUP BY 1 ORDER BY 1
    """).df()
    L.append("| Ano | % do mercado mapeado | % da rede privada | IES sem grupo |")
    L.append("|---|---:|---:|---:|")
    for r in cov.itertuples():
        L.append(f"| {r.ANO} | {r.pct_total:.1f}% | {r.pct_privada:.1f}% | {r.ies_sem_grupo:,} |")
    L.append("\n> A cobertura cai nos anos antigos porque o mapeamento é **pro-forma**: usa o "
             "perímetro atual dos grupos. IES adquiridas depois de 2015 já entram no grupo "
             "comprador em toda a série — que é o comportamento desejado para ler market share, "
             "mas significa que a cobertura de anos antigos reflete o perímetro de hoje.\n")

    # ------------------------------------------------------------------ saida
    L.insert(2, f"\n**{'❌ FALHOU' if falhas else '✅ PASSOU'}** — "
                f"{len(falhas)} falha(s) crítica(s), {len(alertas)} alerta(s).\n")
    if falhas:
        L.append("\n## ❌ Falhas críticas\n")
        L += [f"- {x}" for x in falhas]
    if alertas:
        L.append("\n## ⚠️ Alertas\n")
        L += [f"- {x}" for x in alertas]

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write("\n".join(L))
    print(f"Escrito: {OUT}")
    print(f"\n{'FALHOU' if falhas else 'PASSOU'}: {len(falhas)} falhas, {len(alertas)} alertas")
    for x in falhas:
        print(f"  [FALHA]  {x}")
    for x in alertas:
        print(f"  [ALERTA] {x}")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
