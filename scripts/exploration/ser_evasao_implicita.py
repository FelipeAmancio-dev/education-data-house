# -*- coding: utf-8 -*-
"""EVASÃO IMPLÍCITA: o teste que separa "aluno novo" de "vínculo que não foi baixado".

A base de alunos de um ano é a do ano anterior, mais quem entrou, menos quem formou, menos
quem saiu:

    evasão(t) = base(t−1) + ingressantes(t) − concluintes(t) − base(t)

Tudo do próprio Censo, sem número de release. Se o grupo declarar como "cursando" vínculo
que na prática já tinha se perdido, a evasão implícita despenca — a base cresce sem que
tenha entrado gente suficiente para explicar o crescimento.

`base` aqui é QT_MAT + trancados, que é o universo de vínculos ativos declarado.
"""
import json
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")
D = lambda f: json.load(open(f"dashboard/data/{f}.json", encoding="utf-8"))
dim, cubo = D("dim"), D("c_ies_mod")
grp = dim["ies"]["grupo"]

s = defaultdict(lambda: defaultdict(lambda: {"mat": 0, "ing": 0, "conc": 0, "tranc": 0}))
for j in range(cubo["n"]):
    ix = cubo["ies"][j]
    if ix < 0:
        continue
    g = grp[ix]
    if not g or g == "Independentes":
        continue
    o = s[g][cubo["ano"][j]]
    o["mat"] += cubo["qt_mat"][j]
    o["ing"] += cubo["qt_ing"][j]
    o["conc"] += cubo["qt_conc"][j]
    o["tranc"] += cubo["qt_trancada"][j]

ABERTAS = ["Ser Educacional", "Ânima", "Cruzeiro do Sul", "YDUQS", "Vitru", "Cogna", "Afya"]
anos = sorted({a for g in s.values() for a in g})

print("Evasão implícita, em % da base do ano anterior\n")
print(f"{'GRUPO':17} " + " ".join(f"{a:>7}" for a in anos[1:]))
for g in ABERTAS:
    if g not in s:
        continue
    linha = []
    for i in range(1, len(anos)):
        a, b = anos[i - 1], anos[i]
        base_a = s[g][a]["mat"] + s[g][a]["tranc"]
        base_b = s[g][b]["mat"] + s[g][b]["tranc"]
        if base_a <= 0:
            linha.append("     —")
            continue
        ev = base_a + s[g][b]["ing"] - s[g][b]["conc"] - base_b
        linha.append(f"{100*ev/base_a:>6.1f}%")
    print(f"{g[:17]:17} " + " ".join(linha))

print("\n⚠️ Leitura: evasão implícita muito baixa significa base que cresceu sem entrada")
print("   suficiente para sustentá-la — vínculo que ficou declarado como cursando.")

print("\n=== A conta da Ser, ano a ano ===")
g = "Ser Educacional"
print(f"{'ANO':>5} {'base ant.':>10} {'+ ingress.':>11} {'− conclui.':>11} "
      f"{'= esperado':>11} {'base real':>10} {'evasão':>9} {'%':>7}")
for i in range(1, len(anos)):
    a, b = anos[i - 1], anos[i]
    base_a = s[g][a]["mat"] + s[g][a]["tranc"]
    base_b = s[g][b]["mat"] + s[g][b]["tranc"]
    esp = base_a + s[g][b]["ing"] - s[g][b]["conc"]
    ev = esp - base_b
    print(f"{b:>5} {base_a:>10,} {s[g][b]['ing']:>11,} {s[g][b]['conc']:>11,} "
          f"{esp:>11,} {base_b:>10,} {ev:>9,} {100*ev/base_a:>6.1f}%")
