# -*- coding: utf-8 -*-
"""
Auditoria de ponta a ponta do payload publicado: os números conversam entre si?

POR QUE ISTO EXISTE
-------------------
`03_validate.py` valida os MICRODADOS antes de virarem cubo. Este script valida o outro
lado: o que está em `dashboard/data/`, que é o que o investidor vê. São perguntas
diferentes — um cubo pode estar internamente correto e mesmo assim discordar do painel ao
lado, e foi assim que apareceu o defeito de `ies_mun` com `qt_mat = 0` (o mapa filtrava,
a tabela não, e os dois números não batiam na mesma tela).

A regra que orienta os testes: **todo número que aparece em dois lugares tem que ser o
mesmo número, e toda diferença tem que ter explicação declarada.** As 2.580 matrículas que
separam o total nacional do total geográfico são exterior/N.I. — é diferença explicada, e o
teste exige que ela seja exatamente essa.

USO
---
    python scripts/audita_dashboard.py            # relatório completo
    python scripts/audita_dashboard.py --curto    # só o veredito de cada teste

Sai 1 se algum teste falhar. ALERTA não derruba: é o que precisa de leitura humana.
"""
import argparse
import csv
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "dashboard", "data")
ANO = 2024

# Gabarito do hand-off §4. Se o pipeline mudar algum destes, é para o teste gritar.
GABARITO = {
    "mat_total": 10_227_266, "ingressantes": 5_010_613, "concluintes": 1_333_988,
    "cursos": 45_776, "ies": 2_561, "mat_presencial": 5_037_875, "mat_ead": 5_189_391,
    "mat_privada": 8_162_199,
}
FORA_GEO = 2_580          # exterior / não informado — a única diferença aceita entre cubos

falhas, alertas = [], []


def ok(msg):
    print(f"  ok      {msg}")


def falha(msg):
    falhas.append(msg)
    print(f"  FALHA   {msg}")


def alerta(msg):
    alertas.append(msg)
    print(f"  alerta  {msg}")


def carrega(nome):
    with open(os.path.join(WEB, nome), encoding="utf-8") as f:
        return json.load(f)


def soma_ano(c, ano, col="qt_mat"):
    return sum(c[col][j] for j in range(c["n"]) if c["ano"][j] == ano)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--curto", action="store_true", help="omite as tabelas de detalhe")
    args = ap.parse_args()

    meta = carrega("meta.json")
    dim = carrega("dim.json")
    iesmod = carrega("c_ies_mod.json")
    cine = carrega("c_cine_mod.json")
    munmod = carrega("c_mun_mod.json")
    det_cine = carrega(os.path.join("ano", f"{ANO}_ies_cine.json"))
    det_mun = carrega(os.path.join("ano", f"{ANO}_ies_mun.json"))
    i = meta["anos"].index(ANO)
    k = meta["kpi"]
    grp, co, nome_ies = dim["ies"]["grupo"], dim["ies"]["co"], dim["ies"]["nome"]

    # ------------------------------------------------------------------ 1
    print("\n1. Gabarito de 2024 (hand-off §4)")
    for campo, esperado in GABARITO.items():
        v = k[campo][i]
        (ok if v == esperado else falha)(f"{campo}: {v:,} (esperado {esperado:,})")

    # ------------------------------------------------------------------ 2
    print("\n2. Os cubos somam o mesmo total")
    tot = k["mat_total"][i]
    for nome, c, esperado in [
        ("c_ies_mod", soma_ano(iesmod, ANO), tot),
        ("c_cine_mod", soma_ano(cine, ANO), tot),
        ("2024_ies_cine", sum(det_cine["qt_mat"]), tot),
        ("c_mun_mod", soma_ano(munmod, ANO), tot - FORA_GEO),
        ("2024_ies_mun", sum(det_mun["qt_mat"]), tot - FORA_GEO),
    ]:
        (ok if c == esperado else falha)(f"{nome}: {c:,} (esperado {esperado:,})")

    # ------------------------------------------------------------------ 3
    print("\n3. As aberturas fecham o total")
    for rot, soma in [("presencial + EAD", k["mat_presencial"][i] + k["mat_ead"][i]),
                      ("pública + privada", k["mat_publica"][i] + k["mat_privada"][i])]:
        (ok if soma == tot else falha)(f"{rot} = {soma:,} (total {tot:,})")

    # ------------------------------------------------------------------ 4
    print("\n4. Key Players e Geografia contam o mesmo grupo igual")
    kp, geo, ies_g = {}, {}, {}
    for j in range(iesmod["n"]):
        if iesmod["ano"][j] != ANO:
            continue
        ix = iesmod["ies"][j]
        if ix < 0:
            continue
        g = grp[ix] or "(sem grupo)"
        kp[g] = kp.get(g, 0) + iesmod["qt_mat"][j]
    for j in range(det_mun["n"]):
        ix = det_mun["ies"][j]
        if ix < 0:
            continue
        g = grp[ix] or "(sem grupo)"
        geo[g] = geo.get(g, 0) + det_mun["qt_mat"][j]
        if det_mun["qt_mat"][j] > 0:
            ies_g.setdefault(g, set()).add(ix)
    dif = sum(kp.values()) - sum(geo.values())
    (ok if dif == FORA_GEO else falha)(
        f"diferença total entre os dois cubos: {dif:,} (esperado {FORA_GEO:,} — exterior/N.I.)")
    negativos = [g for g in kp if geo.get(g, 0) > kp[g]]
    (ok if not negativos else falha)(
        f"nenhum grupo com mais aluno na Geografia do que no total: {negativos[:5]}")
    share = sum(100 * v / tot for v in kp.values())
    (ok if abs(share - 100) < 1e-6 else falha)(f"soma dos shares = {share:.6f}%")

    # o bloco Cursos lê o detalhe por curso; ele tem que somar o mesmo por grupo que o
    # cubo de modalidade, senão dois blocos afirmam bases diferentes para o mesmo player
    cur = {}
    for j in range(det_cine["n"]):
        ix = det_cine["ies"][j]
        if ix < 0:
            continue
        g = grp[ix] or "(sem grupo)"
        cur[g] = cur.get(g, 0) + det_cine["qt_mat"][j]
    divergem = {g: (kp[g], cur.get(g, 0)) for g in kp if cur.get(g, 0) != kp[g]}
    (ok if not divergem else falha)(
        f"Cursos e Key Players somam igual por grupo ({len(kp)} grupos conferidos)"
        + (f" — divergem: {list(divergem.items())[:3]}" if divergem else ""))

    # ------------------------------------------------------------------ 5
    print("\n5. Mapeamento de grupos")
    por_co = {}
    for j, c in enumerate(co):
        por_co.setdefault(c, set()).add(grp[j])
    dupes = [c for c, g in por_co.items() if len(g) > 1]
    (ok if not dupes else falha)(f"nenhuma IES em dois grupos ({len(por_co)} códigos)")
    vazios = [g for g, s in ies_g.items() if not s]
    (ok if not vazios else falha)(f"nenhum grupo sem IES com aluno: {vazios[:5]}")
    if not args.curto:
        print(f"\n     {'GRUPO':30} {'ALUNOS':>11} {'IES':>5} {'SHARE':>7}")
        for g, v in sorted(kp.items(), key=lambda x: -x[1])[:14]:
            print(f"     {g[:30]:30} {v:>11,} {len(ies_g.get(g, ())):>5} {100*v/tot:>6.2f}%")

    # ------------------------------------------------------------------ 6
    print("\n6. Geografia: coordenadas e presença")
    lat, lon = dim["mun"]["lat"], dim["mun"]["lon"]
    sem = sum(1 for j in range(len(lat)) if lat[j] is None or lon[j] is None)
    (ok if sem <= 1 else alerta)(f"municípios sem coordenada: {sem} de {len(lat)}")
    zeros = sum(1 for v in det_mun["qt_mat"] if v == 0)
    ok(f"linhas de ies_mun com zero aluno: {zeros:,} — contá-las como presença infla a "
       f"capilaridade (hand-off §3.3c); a tela filtra")

    # ------------------------------------------------------------------ 7
    print("\n7. e-MEC")
    E = carrega("emec.json")
    igc = [v for v in E["igc"] if v]
    fora = sorted({v for v in igc if v not in list("12345")})
    (ok if not fora else falha)(f"IGC fora do domínio 1–5: {fora}")
    matcasada = 0
    porix = {}
    for j in range(iesmod["n"]):
        if iesmod["ano"][j] != ANO:
            continue
        ix = iesmod["ies"][j]
        if ix >= 0:
            porix[ix] = porix.get(ix, 0) + iesmod["qt_mat"][j]
    for ix, v in porix.items():
        if ix < len(E["igc"]) and (E["igc"][ix] or E["ci"][ix] or E["situacao"][ix]):
            matcasada += v
    cob = 100 * matcasada / tot
    (ok if cob >= 99 else alerta)(f"cobertura do e-MEC: {cob:.1f}% das matrículas de {ANO}")

    # ------------------------------------------------------------------ 8
    print("\n8. Reconciliação contra o reportado pelas companhias (4T24)")
    rep = {}
    with open(os.path.join(ROOT, "config", "reportado_companhias.csv"), encoding="utf-8") as f:
        for r in csv.DictReader((ln for ln in f if not ln.startswith("#")), delimiter=";"):
            if r.get("GRAD_TOTAL"):
                rep[r["GRUPO"]] = float(r["GRAD_TOTAL"])
    # o CSV usa o nome de exibição; o cubo usa a chave do grupo
    exib = {}
    for j, g in enumerate(dim["grupos"]["GRUPO"]):
        exib[dim["grupos"]["NOME_EXIBICAO"][j] or g] = g
    if not args.curto:
        print(f"\n     {'GRUPO':18} {'REPORTADO':>11} {'CENSO':>11} {'GAP':>8}")
    for nome, r in sorted(rep.items()):
        g = exib.get(nome, nome)
        v = kp.get(g)
        if v is None:
            falha(f"grupo reportado sem correspondência no cubo: {nome}")
            continue
        gap = 100 * (v - r) / r
        if not args.curto:
            print(f"     {nome[:18]:18} {r:>11,.0f} {v:>11,} {gap:>7.1f}%")
        if abs(gap) > 15:
            alerta(f"{nome}: Censo {gap:+.1f}% vs. graduação reportada — precisa de explicação escrita")
        elif abs(gap) > 5:
            alerta(f"{nome}: Censo {gap:+.1f}% vs. reportado")
        else:
            ok(f"{nome}: {gap:+.1f}%")

    # ------------------------------------------------------------------ 9
    print("\n9. Saltos na série que pedem explicação")
    serie = {}
    for j in range(iesmod["n"]):
        ix = iesmod["ies"][j]
        if ix < 0:
            continue
        g = grp[ix]
        if not g or g == "Independentes":
            continue
        serie.setdefault(g, {}).setdefault(iesmod["ano"][j], 0)
        serie[g][iesmod["ano"][j]] += iesmod["qt_mat"][j]
    saltos = []
    for g, s in serie.items():
        a, b = s.get(ANO - 1, 0), s.get(ANO, 0)
        if a >= 20000 and b and abs(100 * (b - a) / a) > 25:
            saltos.append((g, a, b, 100 * (b - a) / a))
    for g, a, b, p in sorted(saltos, key=lambda x: -abs(x[3])):
        alerta(f"{g}: {p:+.1f}% em {ANO} ({a:,} → {b:,}) — conferir contra o release antes de usar")
    if not saltos:
        ok(f"nenhum grupo com base ≥ 20 mil variou mais de 25% em {ANO}")

    # ------------------------------------------------------------------ 10
    print("\n10. Bases auxiliares")
    P = carrega("precos.json")
    (ok if len(P["series"]) >= 9 and not P["falhas"] else alerta)(
        f"preços: {len(P['series'])} séries, atualizado em {P['atualizado_em']}, "
        f"falhas: {P['falhas'] or 'nenhuma'}")
    tam = os.path.getsize(os.path.join(WEB, "precos.json")) / 1024
    (ok if tam > 150 else falha)(f"precos.json com {tam:.0f} KB (arquivo vazio deixa o bloco em branco)")
    Dd = carrega("dou_diario.json")
    dom = {p["relevancia"] for p in Dd["publicacoes"]} <= {"alta", "media", "baixa"}
    (ok if dom else falha)(f"DOU: {Dd['n']} atos, relevância {Dd['por_relevancia']}")
    sem_motivo = [p for p in Dd["publicacoes"] if not p.get("motivo")]
    (ok if not sem_motivo else falha)(
        f"todo ato do DOU declara o motivo da classificação ({len(sem_motivo)} sem)")
    M = carrega("mensalidades.json")
    bases = sorted(set(M["base"]))
    (ok if bases == ["nacional", "unidades"] else falha)(f"mensalidades: base ∈ {bases}")
    ead_pouco = [j for j in range(M["n"])
                 if M["modalidade"][j] == "ead" and M["base"][j] == "unidades"
                 and M["n_ofertas"][j] < M.get("ead_min_polos", 3)]
    (ok if not ead_pouco else falha)(
        f"nenhuma linha de EAD por unidades abaixo de {M.get('ead_min_polos')} polos")
    R = carrega("regulatorio.json")
    aconf = [d for d in R.get("decisoes", []) if d.get("confianca") == "a_confirmar"]
    (ok if not aconf else alerta)(
        f"regulatório: {len(R.get('decisoes', []))} decisões, {len(aconf)} a confirmar")

    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print(f"{len(falhas)} falha(s) · {len(alertas)} alerta(s)")
    for f_ in falhas:
        print(f"  FALHA   {f_}")
    for a_ in alertas:
        print(f"  alerta  {a_}")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
