# -*- coding: utf-8 -*-
"""
Audita `data_processed/mensalidades.jsonl` contra a URL que cada observação guardou.

POR QUE ISTO EXISTE
-------------------
Em 18/08/2026 o usuário estranhou "Medicina por R$ 840 na São Judas". Não era erro de
leitura de preço: o motor da Ânima casava o nome do curso por **substring**, e
`"medicina" in "biomedicina-bacharelado"` é True — ele abria a página de Biomedicina e
gravava aquele preço como Medicina. Treze observações, duas faculdades.

O defeito era invisível na tela (um preço plausível para Biomedicina é plausível para
qualquer coisa), mas **a própria observação carregava a prova**: o campo `url` apontava
`.../graduacao/biomedicina-bacharelado/` numa linha de curso "Medicina". Este script
transforma essa prova em teste.

A regra é a mesma do coletor corrigido (`anima_escolhe_link`): o slug da URL, normalizado,
tem que ser IGUAL à lista de palavras do curso — ou de um dos sinônimos declarados em
`config/mensalidades_cursos.csv`, que é onde "Gestão de Pessoas" vira "Gestão de Recursos
Humanos" legitimamente.

⚠️ Só audita observação com URL de página de curso (o motor da Ânima). Cogna e Uniasselvi
gravam a URL da BUSCA (`?search_texts=Medicina`), que não carrega o slug do curso
escolhido, e a Estácio vem de API sem URL de página. Essas linhas passam sem veredito — o
script diz quantas foram.

USO
---
    python scripts/audita_mensalidades.py              # só relata
    python scripts/audita_mensalidades.py --limpar     # remove as divergentes e reexporta
"""
import argparse
import importlib.util
import json
import os
import shutil
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
BRUTO = os.path.join(ROOT, "data_processed", "mensalidades.jsonl")

import lib.mensalidades as M  # noqa: E402


def carrega_coletor():
    """O módulo do coletor, para reusar EXATAMENTE a regra de casamento dele.

    Importado por caminho porque o nome do arquivo começa com dígito e não é um
    identificador válido de módulo. Reusar em vez de reescrever é o ponto: uma segunda
    cópia da regra divergiria da primeira no dia em que uma das duas mudasse.
    """
    spec = importlib.util.spec_from_file_location(
        "coletor", os.path.join(ROOT, "scripts", "07_fetch_mensalidades.py"))
    mod = importlib.util.module_from_spec(spec)
    argv, sys.argv = sys.argv, ["coletor"]
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.argv = argv
    return mod


def sinonimos_por_curso():
    """curso canônico -> [termos aceitos], de config/mensalidades_cursos.csv."""
    out = {}
    for lista in M.cursos_alvo().values():
        for c in lista:
            nome = c["curso"]
            out.setdefault(nome, [])
            for t in [nome] + list(c.get("sinonimos") or []):
                if t and t not in out[nome]:
                    out[nome].append(t)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limpar", action="store_true",
                    help="remove as observações divergentes e reexporta o payload")
    args = ap.parse_args()

    col = carrega_coletor()
    sinon = sinonimos_por_curso()

    with open(BRUTO, encoding="utf-8") as f:
        linhas = [json.loads(ln) for ln in f if ln.strip()]

    ok = divergentes = sem_veredito = 0
    ruins, achados = [], {}
    for r in linhas:
        u = r.get("url") or ""
        if "/cursos/graduacao/" not in u:
            sem_veredito += 1
            continue
        slug = u.rstrip("/").split("/")[-1]
        termos = sinon.get(r.get("curso"), [r.get("curso")])
        if any(col.anima_escolhe_link([u], t) for t in termos if t):
            ok += 1
            continue
        divergentes += 1
        ruins.append(r)
        ch = (r.get("ies"), r.get("curso"), slug)
        achados[ch] = achados.get(ch, 0) + 1

    print(f"{len(linhas)} observações · {ok} conferem · {divergentes} divergem · "
          f"{sem_veredito} sem URL de página de curso")
    if achados:
        print("\nDivergências (a URL não é a do curso gravado):")
        for (ies, curso, slug), q in sorted(achados.items(), key=lambda x: -x[1]):
            print(f"  {q:4}x  {ies:18} gravou \"{curso}\" · abriu \"{slug}\"")

    if not args.limpar:
        if divergentes:
            print("\nRode com --limpar para remover estas observações e reexportar.")
        return 1 if divergentes else 0

    if not divergentes:
        print("\nNada a limpar.")
        return 0

    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    bkp = f"{BRUTO}.{carimbo}.bak"
    shutil.copy2(BRUTO, bkp)
    bons = [r for r in linhas if r not in ruins]
    with open(BRUTO, "w", encoding="utf-8") as f:
        for r in bons:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\n{len(ruins)} observações removidas · backup em {os.path.basename(bkp)}")

    obj = M.exporta_web()
    print(f"payload reexportado: {obj['n']} linhas em dashboard/data/mensalidades.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
