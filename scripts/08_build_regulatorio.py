"""Valida a base regulatoria e gera o JSON que o dashboard consome.

`config/regulatorio.json` e o arquivo que se edita a mao; este script confere a
consistencia e escreve `dashboard/data/regulatorio.json`.

Por que existe um passo de validacao para um arquivo escrito a mao: neste modulo o erro
nao aparece como grafico torto, aparece como uma norma com data errada ou sem fonte — e
essa e a unica parte do dashboard que um investidor pode citar em um relatorio. O gate
falha (sai 1) em erro estrutural e apenas avisa no que e recomendacao.

Uso:
  python scripts/08_build_regulatorio.py
  python scripts/08_build_regulatorio.py --so-verificar   # nao escreve, so valida
"""
import argparse
import json
import os
import sys
import unicodedata
from datetime import date, datetime

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTRADA = os.path.join(ROOT, "config", "regulatorio.json")
SAIDA = os.path.join(ROOT, "dashboard", "data", "regulatorio.json")

STATUS = {"vigente", "transicao", "discussao", "revogada"}
RELEVANCIA = {"alta", "media", "baixa"}
CONFIANCA = {"oficial", "a_confirmar"}
ORGAOS = {"MEC", "SERES", "Inep", "CNE", "FNDE", "Planalto", "Outros"}


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", str(s))
                   if unicodedata.category(c) != "Mn").lower()


def data_valida(s):
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def valida(base):
    """Devolve (erros, avisos). Erro derruba o build; aviso so aparece."""
    erros, avisos = [], []
    ids_tema = {t.get("id") for t in base.get("temas", [])}

    for t in base.get("temas", []):
        onde = f"tema '{t.get('id')}'"
        for campo in ("id", "nome", "status", "relevancia", "resumo", "regra_atual"):
            if not t.get(campo):
                erros.append(f"{onde}: falta '{campo}'")
        if t.get("status") not in STATUS:
            erros.append(f"{onde}: status '{t.get('status')}' fora de {sorted(STATUS)}")
        if t.get("relevancia") not in RELEVANCIA:
            erros.append(f"{onde}: relevancia invalida")
        for m in t.get("timeline", []):
            if not data_valida(m.get("data")):
                erros.append(f"{onde}: marco '{m.get('titulo')}' com data invalida")
            if m.get("status") not in STATUS:
                erros.append(f"{onde}: marco '{m.get('titulo')}' com status invalido")
        # `pontos`: o detalhe do resumo de cada tema. Mesma regra do resto do modulo —
        # afirmacao sem fonte primaria nao entra, entao doc e url sao OBRIGATORIOS aqui.
        # Sem esse gate, "dar mais detalhe" viraria porta de entrada para texto sem lastro.
        for i, pt in enumerate(t.get("pontos", []), 1):
            for campo in ("texto", "doc", "url"):
                if not pt.get(campo):
                    erros.append(f"{onde}: ponto {i} sem '{campo}'")
            u = pt.get("url") or ""
            if u and not u.startswith("http"):
                erros.append(f"{onde}: ponto {i} com url invalida")
            elif u and not any(x in u for x in ("gov.br", "planalto", "in.gov.br", "mec.gov.br")):
                avisos.append(f"{onde}: ponto {i} com fonte nao oficial ({u[:60]})")

    vistos = set()
    for d in base.get("decisoes", []):
        onde = f"decisao '{d.get('documento')}'"
        for campo in ("data", "tema", "documento", "orgao", "resumo", "relevancia",
                      "status", "fonte_url", "confianca"):
            if not d.get(campo):
                erros.append(f"{onde}: falta '{campo}'")
        if not data_valida(d.get("data")):
            erros.append(f"{onde}: data invalida")
        if d.get("tema") not in ids_tema and d.get("tema") != "outros":
            erros.append(f"{onde}: tema '{d.get('tema')}' nao existe")
        if d.get("relevancia") not in RELEVANCIA:
            erros.append(f"{onde}: relevancia invalida")
        if d.get("status") not in STATUS:
            erros.append(f"{onde}: status invalido")
        if d.get("confianca") not in CONFIANCA:
            erros.append(f"{onde}: confianca invalida")
        if d.get("orgao") not in ORGAOS:
            avisos.append(f"{onde}: orgao '{d.get('orgao')}' fora da lista padrao")
        url = d.get("fonte_url") or ""
        if not url.startswith("http"):
            erros.append(f"{onde}: fonte_url precisa ser uma URL")
        elif not any(x in url for x in ("gov.br", "planalto", "in.gov.br", "mec.gov.br")):
            avisos.append(f"{onde}: fonte nao parece oficial ({url[:60]})")
        # duplicata: o mesmo ato costuma aparecer em mais de uma fonte
        chave = (sem_acento(d.get("documento", "")), d.get("data"))
        if chave in vistos:
            erros.append(f"{onde}: duplicada (mesmo documento e data)")
        vistos.add(chave)
        if d.get("confianca") == "a_confirmar":
            avisos.append(f"{onde}: marcada como A CONFIRMAR — conferir no DOU")

    if not data_valida(base.get("atualizado_em")):
        erros.append("falta 'atualizado_em' valido na raiz")
    return erros, avisos


def monta(base):
    """Ordena por data (mais recente primeiro) e pre-computa o texto de busca."""
    decisoes = sorted(base.get("decisoes", []), key=lambda d: d["data"], reverse=True)
    for d in decisoes:
        # busca em titulo, numero, resumo, palavras-chave e no texto de "o que mudou"
        d["_busca"] = sem_acento(" ".join([
            d.get("documento", ""), d.get("resumo", ""), d.get("o_que_mudou", ""),
            d.get("quem_afeta", ""), d.get("orgao", ""), d.get("tema", ""),
            " ".join(d.get("keywords", [])),
        ]))
    for t in base.get("temas", []):
        t["timeline"] = sorted(t.get("timeline", []), key=lambda m: m["data"])

    hoje = date.today().isoformat()
    return {
        "atualizado_em": base["atualizado_em"],
        "gerado_em": hoje,
        "fontes": base.get("fontes", []),
        "temas": base.get("temas", []),
        "decisoes": decisoes,
        "n": len(decisoes),
        "a_confirmar": sum(1 for d in decisoes if d.get("confianca") == "a_confirmar"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--so-verificar", action="store_true", help="valida sem escrever")
    args = ap.parse_args()

    with open(ENTRADA, encoding="utf-8") as f:
        base = json.load(f)

    erros, avisos = valida(base)
    for a in avisos:
        print(f"  [aviso] {a}")
    if erros:
        print(f"\n{len(erros)} erro(s) — nada foi escrito:")
        for e in erros:
            print(f"  - {e}")
        return 1

    obj = monta(base)
    if args.so_verificar:
        print(f"\nOK: {obj['n']} decisões, {len(obj['temas'])} temas, "
              f"{len(avisos)} aviso(s).")
        return 0

    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    with open(SAIDA, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
    kb = os.path.getsize(SAIDA) / 1024
    print(f"\nRegulatório: {obj['n']} decisões, {len(obj['temas'])} temas, "
          f"{obj['a_confirmar']} a confirmar → {SAIDA} ({kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
