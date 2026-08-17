"""
Coleta de precos das acoes do setor para o bloco de Price Action.

Fonte: Yahoo Finance (endpoint publico /v8/finance/chart, sem chave). Grava
`dashboard/data/precos.json` no mesmo formato enxuto do resto do payload.

O que entra:
  - fechamento diario ajustado dos ultimos 5 anos, por papel (serve YTD, MTD, WTD e
    qualquer data inicial escolhida pelo investidor);
  - (o intraday de 5 minutos deixou de ser coletado em 14/08/2026: o bloco virou de
    fechamento diario e ninguem le barra de 5 min. `serie_intraday()` segue no arquivo
    caso volte a ser preciso.)
  - IBOV e SMAL11 (proxy negociavel do indice SMLL) como benchmarks;
  - USDBRL, para converter a Afya (Nasdaq, USD) e comparar retorno na mesma moeda.

O arquivo e um SNAPSHOT do ultimo fechamento disponivel. O dashboard mostra a data do
fechamento; rode este script de novo quando quiser avancar a serie.

Uso:
  python scripts/06_fetch_precos.py
  python scripts/06_fetch_precos.py --anos 3 --quieto
"""
import argparse
import datetime as dt
import http.cookiejar
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

# rodando por pythonw.exe (tarefa agendada, sem janela) nao existe stdout: chamar
# reconfigure direto derruba o script antes de coletar qualquer coisa
if getattr(sys.stdout, "reconfigure", None):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = os.path.join(ROOT, "config", "tickers.csv")
SAIDA = os.path.join(ROOT, "dashboard", "data", "precos.json")

API = "https://query1.finance.yahoo.com/v8/finance/chart/"
UA = {"User-Agent": "Mozilla/5.0 (compatible; education-dashboard/1.0)"}


def cotacoes(simbolos):
    """Valor de mercado por papel.

    O endpoint /v7/finance/quote exige cookie + crumb desde 2023 — sem isso responde 401.
    O caminho e sempre o mesmo: pegar o cookie em fc.yahoo.com e trocar por um crumb.
    Se falhar, o basket cai para peso igual e a tela avisa; nao quebra.
    """
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    try:
        op.open(urllib.request.Request("https://fc.yahoo.com", headers=UA), timeout=15)
    except Exception:                                # noqa: BLE001 - o 4xx ja deixa o cookie
        pass
    crumb = op.open(urllib.request.Request(
        "https://query1.finance.yahoo.com/v1/test/getcrumb", headers=UA), timeout=15).read().decode()
    url = ("https://query1.finance.yahoo.com/v7/finance/quote?symbols="
           + urllib.parse.quote(",".join(simbolos)) + "&crumb=" + urllib.parse.quote(crumb))
    d = json.load(op.open(urllib.request.Request(url, headers=UA), timeout=25))
    out = {}
    for q in d.get("quoteResponse", {}).get("result", []):
        mcap, px = q.get("marketCap"), q.get("regularMarketPrice")
        out[q["symbol"]] = {
            "mcap": mcap, "preco": px, "moeda": q.get("currency"),
            # acoes implicitas: a Afya tem classes A e B e o campo sharesOutstanding traz
            # so uma delas, enquanto o marketCap ja considera as duas
            "acoes": (mcap / px) if (mcap and px) else None,
        }
    return out


def le_tickers():
    linhas = []
    with open(CFG, encoding="utf-8") as f:
        cab = None
        for ln in f:
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            campos = ln.split(";")
            if cab is None:
                cab = campos
                continue
            linhas.append(dict(zip(cab, campos)))
    return linhas


def chart(simbolo, rng, intervalo):
    url = f"{API}{urllib.parse.quote(simbolo)}?range={rng}&interval={intervalo}"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.load(r)
    res = (d.get("chart") or {}).get("result") or []
    if not res:
        raise ValueError("resposta sem série")
    return res[0]


def serie_diaria(simbolo, anos):
    """Fechamento diário. Prefere o ajustado (adjclose), que incorpora proventos e
    desdobramentos — sem isso o retorno de um papel que pagou dividendo sai errado."""
    r = chart(simbolo, f"{anos}y", "1d")
    ts = r.get("timestamp") or []
    ind = r.get("indicators", {})
    fech = (ind.get("adjclose") or [{}])[0].get("adjclose") if ind.get("adjclose") else None
    if not fech:
        fech = (ind.get("quote") or [{}])[0].get("close") or []
    datas, valores = [], []
    for t, c in zip(ts, fech):
        if c is None:
            continue                      # feriado/pregão sem negócio: não inventa preço
        datas.append(dt.datetime.fromtimestamp(t).strftime("%Y-%m-%d"))
        valores.append(round(float(c), 4))
    return {"d": datas, "c": valores, "moeda": r["meta"].get("currency", "")}


def serie_intraday(simbolo):
    """Última sessão em barras de 5 min, com o fechamento anterior como base do dia."""
    r = chart(simbolo, "1d", "5m")
    ts = r.get("timestamp") or []
    q = (r.get("indicators", {}).get("quote") or [{}])[0]
    fech = q.get("close") or []
    horas, valores = [], []
    for t, c in zip(ts, fech):
        if c is None:
            continue
        horas.append(dt.datetime.fromtimestamp(t).strftime("%H:%M"))
        valores.append(round(float(c), 4))
    meta = r["meta"]
    return {
        "t": horas, "c": valores,
        "prev": meta.get("chartPreviousClose"),
        "ultimo": meta.get("regularMarketPrice"),
        "data": dt.datetime.fromtimestamp(ts[-1]).strftime("%Y-%m-%d") if ts else None,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anos", type=int, default=5, help="anos de histórico diário")
    ap.add_argument("--quieto", action="store_true")
    args = ap.parse_args()
    log = (lambda *a: None) if args.quieto else print

    saida = {
        "atualizado_em": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "fonte": "Yahoo Finance",
        "papeis": [], "series": {}, "falhas": [],
    }

    log(f"{'TICKER':<9} {'SÍMBOLO':<11} {'MOEDA':<6} {'PONTOS':>7}  PERÍODO")
    log("-" * 62)
    for t in le_tickers():
        tk, sym = t["TICKER"], t["YAHOO"]
        try:
            s = serie_diaria(sym, args.anos)
        except Exception as e:                       # noqa: BLE001 - queremos seguir
            saida["falhas"].append({"ticker": tk, "erro": f"{type(e).__name__}: {e}"})
            log(f"{tk:<9} {sym:<11} FALHOU: {type(e).__name__}")
            continue
        saida["series"][tk] = s
        saida["papeis"].append({
            "ticker": tk, "grupo": t.get("GRUPO", ""), "yahoo": sym,
            "moeda": s["moeda"] or t.get("MOEDA", ""), "bolsa": t.get("BOLSA", ""),
            "tipo": t.get("TIPO", "acao"),
        })
        # ⚠️ O intraday NAO e mais coletado (14/08/2026, decisao do usuario): o bloco
        # Price Action passou a ser de FECHAMENTO DIARIO, e a tela nao tem mais onde
        # mostrar barra de 5 minutos. Coletar dado que ninguem le custaria uma chamada
        # extra por papel — 9 a mais por rodada — e so aumentaria a chance de o Yahoo
        # limitar o IP. `serie_intraday()` fica no arquivo caso o intraday volte.
        log(f"{tk:<9} {sym:<11} {s['moeda']:<6} {len(s['c']):>7}  "
            f"{s['d'][0] if s['d'] else '-'} → {s['d'][-1] if s['d'] else '-'}")

    # valor de mercado: e o peso do basket, entao vale a chamada extra
    acoes = [t for t in le_tickers() if t.get("TIPO") == "acao"]
    try:
        q = cotacoes([t["YAHOO"] for t in acoes])
        for t in acoes:
            info = q.get(t["YAHOO"])
            if not info:
                continue
            for p in saida["papeis"]:
                if p["ticker"] == t["TICKER"]:
                    p["mcap"], p["acoes_eq"] = info["mcap"], info["acoes"]
        log("\nValor de mercado:")
        for p in saida["papeis"]:
            if p.get("mcap"):
                log(f"  {p['ticker']:<8} {p['moeda']} {p['mcap']:>16,.0f}")
    except Exception as e:                            # noqa: BLE001
        saida["falhas"].append({"ticker": "quote", "erro": f"market cap: {type(e).__name__}: {e}"})
        log(f"\n[AVISO] valor de mercado indisponível ({type(e).__name__}) — "
            f"o basket cai para peso igual")

    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    with open(SAIDA, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, separators=(",", ":"))
    kb = os.path.getsize(SAIDA) / 1024
    log("-" * 62)
    log(f"Escrito: {SAIDA}  ({kb:,.0f} KB)")
    if saida["falhas"]:
        log(f"[AVISO] {len(saida['falhas'])} falha(s): "
            + ", ".join(x["ticker"] for x in saida["falhas"]))
    return 0 if saida["series"] else 1


if __name__ == "__main__":
    sys.exit(main())
