"""
Tracking de mensalidade dos principais cursos de graduacao das companhias listadas.

Os sites nao publicam preco no HTML: o valor so aparece depois de percorrer um assistente
(buscar curso -> abrir curso -> consultar valores -> escolher unidade/turno, ou
estado/cidade/polo no EAD). Por isso a coleta roda em navegador headless (Playwright).

Regra de preco: sempre o MENOR valor exibido na selecao. Em "de R$ 100 por R$ 79" vale o
79. A mensalidade publicada no dashboard e a media simples do menor preco de cada
unidade/polo — o bruto por unidade fica no historico.

Uso:
  python scripts/07_fetch_mensalidades.py                      # tudo que estiver ATIVO
  python scripts/07_fetch_mensalidades.py --ies "Anhembi Morumbi" --modalidade presencial
  python scripts/07_fetch_mensalidades.py --curso Psicologia --limite-unidades 2
  python scripts/07_fetch_mensalidades.py --so-exportar        # so reagrega o historico
"""
import argparse
import json
import os
import re
import sys
import time
from contextlib import ExitStack
from urllib.parse import parse_qs, quote, unquote, urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import mensalidades as M  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

TIMEOUT = 45000
PAUSA = 0.8          # respiro entre interacoes: nao martelar o site


# ---------------------------------------------------------------- utilitarios
def txt_limpo(s):
    return " ".join((s or "").split())


JS_LISTAS = """() => {
  const out=[];
  for (const l of [...document.querySelectorAll('ul,[role="listbox"]')]) {
    if (!l.offsetParent) continue;
    const its=[...l.querySelectorAll('[role="option"],li')]
      .map(e=>(e.innerText||'').replace(/\\s+/g,' ').trim()).filter(Boolean);
    if (its.length && its.length < 200) out.push(its);
  }
  return out;
}"""

_ultima_lista = []   # opcoes do dropdown aberto por ultimo, para ancorar o clique seguinte


def dropdown_opcoes(pg, palavra):
    """Abre um dropdown customizado (botao + lista flutuante) e devolve as opcoes.

    Os portais da Anima usam Headless UI: o botao nao e <select> e a lista so existe no
    DOM depois do clique. Comparar as listas visiveis antes e depois isola a que abriu.

    ⚠️ `palavra` e uma PALAVRA-CHAVE do rotulo ("unidade", "turno"), nao o texto exato.
    O motor original casava texto exato ("Selecione a unidade") e quebrou inteiro quando o
    portal reescreveu os rotulos para "Selecione aqui a ..." e ainda inseriu um passo novo
    de modalidade antes da unidade. Casar por palavra sobrevive a esse tipo de reescrita.
    """
    antes = pg.evaluate(JS_LISTAS)
    botao = pg.locator(f'button:has-text("{palavra}")').first
    if not botao.count():
        return []
    try:
        botao.scroll_into_view_if_needed(timeout=8000)
        botao.click(timeout=8000)
    except Exception:                                  # noqa: BLE001
        return []
    pg.wait_for_timeout(1200)
    depois = pg.evaluate(JS_LISTAS)
    novas = [d for d in depois if d not in antes]
    # guarda a lista que abriu: e ela que delimita onde o clique seguinte pode cair
    _ultima_lista[:] = novas[0] if novas else []
    return list(_ultima_lista)


# Clicar a opcao pelo DOM, e nao pelo locator do Playwright: com a lista flutuante do
# Headless UI o clique "de verdade" estoura em timeout mesmo com o item visivel (o overlay
# intercepta o ponteiro), e era dai que vinha a maioria dos TimeoutError da coleta.
#
# ⚠️ O clique tem de ficar DENTRO da lista que abriu. Procurar 'ul li' pela pagina inteira
# acha o menu do topo — "Presencial" existe la em Modalidades, e clicar nele leva para
# /modalidades/presencial/, abandonando o assistente sem erro nenhum. Por isso a funcao
# recebe o conjunto de opcoes esperado e so aceita a lista cujos itens batem com ele.
JS_CLICA_OPCAO = """([txt, esperadas]) => {
  const norm = e => (e.innerText||'').replace(/\\s+/g,' ').trim();
  const alvo = txt.replace(/\\s+/g,' ').trim().toLowerCase();
  const chave = esperadas.join('|');
  for (const l of [...document.querySelectorAll('ul,[role="listbox"]')]) {
    if (!l.offsetParent) continue;
    const its = [...l.querySelectorAll('[role="option"],li')].filter(e => norm(e));
    if (its.map(norm).join('|') !== chave) continue;          // nao e a lista que abriu
    const el = its.find(e => norm(e).toLowerCase() === alvo)
            || its.find(e => norm(e).toLowerCase().includes(alvo));
    if (!el) return false;
    (el.querySelector('[role="option"],button,a') || el).click();
    return true;
  }
  return false;
}"""


def dropdown_escolher(pg, opcao):
    """Clica numa opcao do dropdown aberto por `dropdown_opcoes`."""
    if not _ultima_lista:
        return False
    try:
        ok = pg.evaluate(JS_CLICA_OPCAO, [opcao, list(_ultima_lista)])
    except Exception:                                  # noqa: BLE001
        ok = False
    if ok:
        pg.wait_for_timeout(1500)
        return True
    # segunda tentativa pelo locator, para o caso de a opcao so responder a clique real
    alvo = pg.locator('[role="listbox"] li, [role="option"], ul li').filter(has_text=opcao)
    for i in range(min(alvo.count(), 6)):
        el = alvo.nth(i)
        try:
            if el.is_visible():
                el.click(timeout=6000)
                pg.wait_for_timeout(1500)
                return True
        except Exception:                              # noqa: BLE001
            continue
    return False


def preco_da_tela(pg):
    """Menor valor no cartao de preco (ou na pagina, se o cartao nao for identificado)."""
    txt = pg.evaluate("""() => {
      const c=document.querySelector('[class*="preco-curso"],[class*="valores"],[class*="price"]');
      return (c||document.body).innerText;
    }""")
    return M.menor_preco(txt)


# ------------------------------------------------------------- motor: Anima
# Anhembi Morumbi e Sao Judas rodam o mesmo portal, so muda o dominio.
TURNOS_PREF = ["Manhã", "Manha", "Noite", "Noturno", "Tarde", "Integral"]


# ⚠️ SUBSTRING NAO SERVE PARA CASAR NOME DE CURSO, e este bug chegou a ser publicado.
#
# Achado em 18/08/2026 pelo usuario, que estranhou "Medicina por R$ 840 na Sao Judas".
# O codigo anterior era:
#
#     chave = M.sem_acento(termo).split()[0]          # "medicina"
#     exatos = [h for h in alvos if chave in M.sem_acento(h)]
#     escolhido = exatos[0] if exatos else alvos[0]
#
# e `"medicina" in "biomedicina-bacharelado"` e **True**. O motor abria a pagina de
# Biomedicina e gravava aquele preco como Medicina — 13 observacoes em 2 faculdades, com
# min, max e numero de unidades identicos aos de Biomedicina, que foi a impressao digital
# do defeito. A URL coletada provava o erro sozinha: `.../graduacao/biomedicina-bacharelado/`
# numa linha de curso "Medicina".
#
# Duas correcoes, e a segunda importa tanto quanto a primeira:
#
# 1. compara o SLUG inteiro, por palavra, com o termo — "biomedicina" nao contem a palavra
#    "medicina", contem uma palavra que termina assim, que e outra coisa;
# 2. **sem `alvos[0]` de consolo.** O fallback pegava o primeiro resultado da busca fosse
#    ele qual fosse: bastava a faculdade NAO ter o curso para o motor gravar o preco de
#    outro. Recusar e o comportamento certo, e e o mesmo que o motor da Cogna ja faz com
#    card de modalidade ambigua — "sem card exclusivo desta modalidade" e recusa
#    deliberada, nao falha.
#
# O nome que muda de faculdade para faculdade continua sendo resolvido onde sempre foi:
# na coluna SINONIMOS de `config/mensalidades_cursos.csv` — foi assim que "Gestao de
# Pessoas" passou a achar "Gestao de Recursos Humanos", e esse caminho segue funcionando
# porque o sinonimo entra como termo de busca, nao como casamento frouxo.
_SUFIXOS_SLUG = ("bacharelado", "licenciatura", "graduacao", "tecnologica", "tecnologo",
                 "superior", "de", "tecnologia", "em", "curso", "ead", "presencial",
                 "semipresencial", "digital", "flex")


def anima_palavras(txt):
    """Palavras significativas de um nome de curso ou de um slug de URL.

    Os DOIS lados passam por aqui, e é isso que faz a comparação funcionar: o slug traz
    grau e modalidade coladas no nome (`gestao-de-recursos-humanos-graduacao-tecnologica`)
    e o termo traz preposições que o slug às vezes não tem. Normalizados igual, os dois
    viram a mesma lista.
    """
    t = M.sem_acento(txt).replace("-", " ").replace("/", " ")
    return [w for w in t.split() if w and w not in _SUFIXOS_SLUG]


def anima_escolhe_link(alvos, termo):
    """O link cujo slug É o curso procurado — ou None.

    ⚠️ Igualdade da lista inteira de palavras, nunca subconjunto. "medicina" bate só com
    `medicina-bacharelado`: não bate com `biomedicina` (palavra diferente) nem com
    `medicina-veterinaria` (palavra a mais). Aceitar subconjunto reintroduziria, pelo outro
    lado, o mesmo defeito que o substring causou — é a armadilha que o motor da Estácio já
    documenta ("Medicina" casaria com "Medicina Veterinária").
    """
    alvo = anima_palavras(termo)
    if not alvo:
        return None
    for h in alvos:
        if anima_palavras(h.rstrip("/").split("/")[-1]) == alvo:
            return h
    return None


def anima_url_do_curso(pg, base, modalidade, sinonimos):
    """Busca o curso no portal e devolve a URL da pagina dele."""
    aba = {"presencial": "Presencial", "semipresencial": "Semipresencial", "ead": "EAD"}[modalidade]
    pg.goto(base, timeout=TIMEOUT)
    pg.wait_for_timeout(2500)
    try:
        pg.locator(f'label:has-text("{aba}")').first.click()
        pg.wait_for_timeout(1500)
    except Exception:                                  # noqa: BLE001
        pass

    campo = pg.get_by_placeholder("Pesquise aqui o seu curso de interesse")
    for termo in sinonimos:
        try:
            campo.click()
            campo.fill("")
            campo.type(termo, delay=45)
            pg.wait_for_timeout(2500)
        except Exception:                              # noqa: BLE001
            continue
        links = pg.eval_on_selector_all(
            "a", "els => els.map(e => e.getAttribute('href')).filter(h => h && h.includes('/cursos/graduacao/'))")
        alvos = [h for h in dict.fromkeys(links) if h.rstrip("/").count("/") >= 3]
        if not alvos:
            continue
        escolhido = anima_escolhe_link(alvos, termo)
        if not escolhido:
            continue
        if escolhido.startswith("/"):
            escolhido = base.split("/cursos")[0] + escolhido
        return escolhido
    return None


ANIMA_MOD = {"presencial": "Presencial", "semipresencial": "Semipresencial", "ead": "EAD"}


def anima_abre_form(pg, url, modalidade=None):
    """Abre a pagina do curso, o formulario de valores e escolhe a modalidade.

    ⚠️ Esperar por CONTEUDO, nao por tempo. A pagina do portal chega vazia e so e
    preenchida depois: medido em 12/08/2026, aos 3 s o `body` ainda tinha zero caractere e
    so aos ~5 s aparecia o botao. O motor dormia 2,2 s fixos e concluia "sem botao de
    consultar valores" numa pagina que estava apenas carregando — era essa a causa da
    metade das falhas, e nao um curso sem preco.

    O assistente tambem ganhou um passo: hoje o primeiro dropdown e a MODALIDADE, e so
    depois dela aparecem unidade e turno.
    """
    pg.goto(url, timeout=TIMEOUT)
    try:
        pg.wait_for_function(
            "() => /consultar valores/i.test(document.body.innerText)", timeout=30000)
    except Exception:                                  # noqa: BLE001
        return False
    pg.wait_for_timeout(800)
    botao = pg.locator('text=Consultar valores').first
    if not botao.count():
        return False
    try:
        botao.scroll_into_view_if_needed(timeout=8000)
        botao.click(timeout=8000)
    except Exception:                                  # noqa: BLE001
        return False
    pg.wait_for_timeout(2200)

    if modalidade:
        opcoes_mod = dropdown_opcoes(pg, "modalidade")
        if opcoes_mod:
            alvo = ANIMA_MOD[modalidade]
            escolha = next((o for o in opcoes_mod if M.sem_acento(o) == M.sem_acento(alvo)), None)
            if not escolha:
                return False                           # curso nao tem essa modalidade
            if not dropdown_escolher(pg, escolha):
                return False
            pg.wait_for_timeout(1500)
    return True


def anima_precos(pg, url, modalidade, limite_unidades):
    """Percorre unidade x turno (ou estado/cidade/polo no EAD) e devolve os precos.

    Uma volta = um carregamento da pagina. Depois de escolher uma unidade o botao troca
    de rotulo (vira o nome da unidade) e nao ha id estavel para reabri-lo, entao recarregar
    e o caminho confiavel — mais lento, porem sem estado sujo entre unidades.
    """
    if not anima_abre_form(pg, url, modalidade):
        return [], "assistente não abriu ou curso não tem a modalidade"

    achados = []
    if modalidade == "ead":
        for uf, cidade in M.CIDADES_EAD:
            if not dropdown_opcoes(pg, "estado"):
                continue
            if not dropdown_escolher(pg, uf) and not dropdown_escolher(pg, cidade):
                continue
            cidades = dropdown_opcoes(pg, "cidade")
            alvo_cid = next((c for c in cidades if M.parecido(c, cidade)), None)
            if not alvo_cid or not dropdown_escolher(pg, alvo_cid):
                continue
            polos = dropdown_opcoes(pg, "polo") or [None]
            for polo in polos[:limite_unidades or len(polos)]:
                if polo and not dropdown_escolher(pg, polo):
                    continue
                v = preco_da_tela(pg)
                if v:
                    achados.append({"unidade": f"{cidade} · {polo or 'polo único'}",
                                    "turno": "", "preco": v})
                time.sleep(PAUSA)
        return achados, None

    unidades = dropdown_opcoes(pg, "unidade")
    if not unidades:
        return [], "dropdown de unidade não abriu"
    for i, unidade in enumerate(unidades[:limite_unidades or len(unidades)]):
        if i and not anima_abre_form(pg, url, modalidade):
            break
        if i:
            dropdown_opcoes(pg, "unidade")
        if not dropdown_escolher(pg, unidade):
            continue
        turnos = dropdown_opcoes(pg, "turno")
        # regra do usuario: manha; se nao houver, noite
        escolhido = None
        for pref in TURNOS_PREF:
            escolhido = next((t for t in turnos if M.sem_acento(pref) in M.sem_acento(t)), None)
            if escolhido:
                break
        if escolhido and not dropdown_escolher(pg, escolhido):
            continue
        v = preco_da_tela(pg)
        if v:
            achados.append({"unidade": unidade, "turno": escolhido or "", "preco": v})
        time.sleep(PAUSA)
    return achados, None


# ----------------------------------------------------------- motor: Estacio
# A Estacio nao precisa de navegador: a listagem de cursos e desenhada por uma API publica
# — a mesma que o proprio site chama — e ela responde a HTTP puro. O que a destrava e o
# cabecalho `x-marca-origin: estacio`; sem ele o gateway devolve 502, com ele responde 200.
#
#   /ofertas/unidades?idsMarca=1               as 2.071 unidades (campi + polos)
#   /ofertas/prateleira/v2?...&codigoCampus=N  cursos e precos daquela unidade
#
# Uma chamada por unidade traz TODOS os cursos dela com o preco de cada modalidade. Por
# isso o motor carrega tudo de uma vez num cache e depois responde curso a curso de
# memoria — o inverso do motor da Anima, que navega por curso.
#
# ⚠️ Isto corrige a conclusao da sondagem anterior. O card do site mostra um "a partir de"
# nacional, e dai tinha vindo a ideia de gravar a Estacio como preco nacional. Nao e:
# consultada por unidade, a API mostra o presencial variando muito de praca (Pedagogia de
# R$ 261 a R$ 425; Direito de R$ 345 a R$ 743). Ate EAD e semipresencial variam por polo em
# alguns cursos (Administracao EAD entre R$ 129 e R$ 159). Entao a Estacio entra por
# unidade, com a mesma regra da Anima, e as duas ficam comparaveis.
ESTACIO_API = "https://api.portal.estacio.br/ofertas/api/v1/ofertas"
ESTACIO_H = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/121.0 Safari/537.36"),
    "Accept": "application/json", "Content-Type": "application/json",
    "Accept-Language": "pt-BR", "Referer": "https://estacio.br/",
    "x-marca-origin": "estacio",
}
# indModalidade da API -> modalidade do projeto. "AO VIVO" (V) e "FLEX" (SF) sao formatos
# proprios da Estacio, sem equivalente nas outras faculdades: ficam fora da comparacao.
ESTACIO_IND = {"presencial": "P", "semipresencial": "S", "ead": "T"}
ESTACIO_TIPOS = "11,4"          # 11 = bacharelado/licenciatura, 4 = tecnologo
ESTACIO_POLOS_POR_CAPITAL = 10  # recorte de EAD: as capitais de M.CIDADES_EAD

_estacio_cache = {}             # {(curso_sem_acento, indModalidade): [(unidade, preco)]}
_estacio_nomes = set()          # os nomes de curso como a Estacio escreve


def estacio_json(caminho, tentativas=3):
    import urllib.request
    for i in range(tentativas):
        try:
            req = urllib.request.Request(f"{ESTACIO_API}/{caminho}", headers=ESTACIO_H)
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:                              # noqa: BLE001
            if i == tentativas - 1:
                raise
            time.sleep(1.5 * (i + 1))
    return None


def estacio_unidades():
    """Recorte de unidades: todos os campi + polos nas capitais do recorte de EAD.

    Das 2.071 unidades, 1.911 sao "POLO ..." (pontos de EAD/semipresencial) e 160 sao campi
    com oferta presencial. Varrer todas seria uma requisicao por unidade sem ganho
    analitico; o recorte de polos segue M.CIDADES_EAD, o mesmo criterio ja usado na Anima.
    """
    uni = estacio_json("unidades?idsMarca=1")
    capitais = [M.sem_acento(c) for _, c in M.CIDADES_EAD]
    campi, polos = [], {}
    for u in uni or []:
        nome = u.get("nomeCampus") or ""
        if "POLO" not in nome.upper():
            campi.append(u)
            continue
        cap = next((c for c in capitais if c in M.sem_acento(nome)), None)
        if cap:
            polos.setdefault(cap, []).append(u)
    escolhidas = list(campi)
    for cap in capitais:
        escolhidas += polos.get(cap, [])[:ESTACIO_POLOS_POR_CAPITAL]
    vistos, saida = set(), []                          # a API repete unidade na lista
    for u in escolhidas:
        if u["codigoCampus"] not in vistos:
            vistos.add(u["codigoCampus"])
            saida.append(u)
    return saida


def estacio_carrega():
    """Uma passada por unidade, montando o cache curso x modalidade x unidade."""
    if _estacio_cache:
        return
    unidades = estacio_unidades()
    print(f"  [estacio] carregando {len(unidades)} unidades da API…")
    erros = 0
    for i, u in enumerate(unidades, 1):
        try:
            d = estacio_json(f"prateleira/v2?pageSize=200&pageNumber=1&idsMarca=1"
                             f"&codigoTipoCurso={ESTACIO_TIPOS}"
                             f"&codigoCampus={u['codigoCampus']}")
        except Exception:                              # noqa: BLE001
            erros += 1
            continue
        rotulo = f"{txt_limpo(u.get('nomeCampus'))} ({u.get('uf')})"
        for c in d or []:
            nome = txt_limpo(c.get("nomeCurso"))
            _estacio_nomes.add(nome)
            for m in c.get("modalidades") or []:
                try:
                    preco = float(m.get("preco"))
                except (TypeError, ValueError):
                    continue
                if preco <= 0:
                    continue
                _estacio_cache.setdefault(
                    (M.sem_acento(nome), m.get("indModalidade")), []).append((rotulo, preco))
        if i % 50 == 0:
            print(f"  [estacio] {i}/{len(unidades)} unidades")
        time.sleep(0.1)                                # nao martelar a API
    print(f"  [estacio] {len(_estacio_nomes)} cursos, "
          f"{sum(len(v) for v in _estacio_cache.values())} ofertas"
          + (f", {erros} unidades falharam" if erros else ""))


def estacio_url_do_curso(pg, base, modalidade, sinonimos):
    """Casa o curso pelo nome EXATO da Estacio; devolve a URL da busca no site.

    O casamento e exato de proposito. Por prefixo, "Medicina" casaria com "Medicina
    Veterinaria" e "Pedagogia" com "Psicopedagogia" — e a Estacio nao oferta Medicina nesta
    marca (na YDUQS a medicina esta sob a IDOMED), entao um casamento frouxo inventaria um
    preco que nao existe. Quando o nome muda de faculdade para faculdade, o lugar de
    resolver e a coluna SINONIMOS de mensalidades_cursos.csv, que existe para isso.
    """
    estacio_carrega()
    for termo in sinonimos:
        alvo = M.sem_acento(termo)
        if any(k[0] == alvo for k in _estacio_cache):
            return f"{base}?term={quote(termo)}"
    return None


def estacio_precos(pg, url, modalidade, limite_unidades):
    termo = unquote((parse_qs(urlparse(url).query).get("term") or [""])[0])
    obs = _estacio_cache.get((M.sem_acento(termo), ESTACIO_IND[modalidade]), [])
    if not obs:
        return [], f"não oferece {modalidade}"
    # a mesma unidade pode repetir o curso; fica o menor preco dela, como manda a regra
    por_unidade = {}
    for unidade, preco in obs:
        if unidade not in por_unidade or preco < por_unidade[unidade]:
            por_unidade[unidade] = preco
    itens = sorted(por_unidade.items())
    if limite_unidades:
        itens = itens[:limite_unidades]
    return [{"unidade": u, "turno": "", "preco": p} for u, p in itens], None


# ------------------------------------------------------------- motor: Cogna
# Anhanguera e Unopar rodam o mesmo portal, so muda o dominio. A busca e por URL
# (`?search_texts=Pedagogia`), sem digitar em campo nenhum, e cada card da listagem ja traz
# nome, modalidade, preco e turnos juntos. O card e `div.product`; o link do curso e
# `/curso/<slug>/` no SINGULAR — procurar `/cursos/` nao acha nada.
#
# ⚠️ O preco da Cogna e NACIONAL. Diferente da Estacio, aqui nao ha como descer para a
# unidade: nem a listagem nem a pagina do curso oferecem selecao de polo/campus, e a pagina
# do curso repete o mesmo "a partir de". Por isso a observacao vai gravada como
# `unidade = "nacional (a partir de)"` — e na tela isso aparece como n=1 e min=max, que e
# o sinal de que aquela media nao tem dispersao por praca para mostrar.
COGNA_CARDS = """() => {
  const vis = e => e.offsetParent !== null;
  const base = [...document.querySelectorAll('div,article,li,section')].filter(e =>
    vis(e) && /R\\$/.test(e.innerText||'') && (e.innerText||'').length < 500
    && !e.querySelector('div,article,li,section'));
  const out = [], vistos = new Set();
  for (const e of base) {
    let n = e;
    for (let i = 0; i < 9 && n; i++, n = n.parentElement) {
      if (!(n.className||'').toString().includes('product')) continue;
      const t = (n.innerText||'').replace(/\\s+/g,' ').trim();
      const a = n.querySelector('a[href*="/curso/"]');
      if (t.length > 30 && !vistos.has(t)) {
        vistos.add(t);
        out.push({txt: t, href: a ? a.getAttribute('href') : ''});
      }
      break;
    }
  }
  return out;
}"""
def cogna_cards(pg):
    try:
        return pg.evaluate(COGNA_CARDS)
    except Exception:                                  # noqa: BLE001
        return []


def cogna_modalidades_do_card(txt):
    """Modalidades que o card declara — pode ser MAIS DE UMA.

    ⚠️ Um mesmo card pode dizer "Semipresencial Presencial" e mostrar um unico
    "A partir de". Nesse caso o preco e um piso das duas juntas e nao pertence a nenhuma
    delas em particular: atribui-lo a uma so rotularia errado. Por isso quem chama exige
    card inequivoco. "Semipresencial" contem "presencial", entao a deteccao remove a
    palavra maior antes de procurar a menor.
    """
    t = M.sem_acento(txt)
    achadas = set()
    if "semipresencial" in t:
        achadas.add("semipresencial")
        t = t.replace("semipresencial", " ")
    if "ead" in t or "a distancia" in t:
        achadas.add("ead")
    if "presencial" in t:
        achadas.add("presencial")
    return achadas


# O card comeca com o nome do curso e emenda o grau: "Pedagogia Licenciatura - 8 semestres".
# Aceitar so o prefixo do nome casaria "Pedagogia" com "Pedagogia Bilingue"; por isso o que
# vem logo depois do nome tem de ser o grau (ou o fim do texto).
GRAUS = ("licenciatura", "bacharelado", "tecnologo", "superior de tecnologia")


def cogna_card_do_curso(cards, termo, modalidade):
    """Card cujo nome e exatamente o curso procurado e cuja modalidade bate."""
    alvo = M.sem_acento(termo)
    for c in cards:
        t = M.sem_acento(c["txt"])
        if not t.startswith(alvo):
            continue
        resto = t[len(alvo):].lstrip(" -")
        if resto and not resto.startswith(GRAUS):
            continue
        # so card que declara UMA modalidade: ver cogna_modalidades_do_card
        if cogna_modalidades_do_card(c["txt"]) == {modalidade}:
            return c
    return None


def cogna_url_do_curso(pg, base, modalidade, sinonimos):
    for termo in sinonimos:
        url = f"{base}?search_texts={quote(termo)}"
        try:
            pg.goto(url, timeout=TIMEOUT)
        except Exception:                              # noqa: BLE001
            continue
        pg.wait_for_timeout(6000)
        for _ in range(2):                             # a listagem carrega ao rolar
            pg.mouse.wheel(0, 3000)
            pg.wait_for_timeout(1200)
        if cogna_card_do_curso(cogna_cards(pg), termo, modalidade):
            return f"{url}#{quote(termo)}"
    return None


def cogna_precos(pg, url, modalidade, limite_unidades):
    termo = unquote(url.split("#", 1)[1]) if "#" in url else ""
    card = cogna_card_do_curso(cogna_cards(pg), termo, modalidade)
    if not card:
        return [], "sem card exclusivo desta modalidade"
    v = M.menor_preco(card["txt"])
    if not v:
        return [], "sem preço no card"
    return [{"unidade": "nacional (a partir de)", "turno": "", "preco": v}], None


# -------------------------------------------------------- motor: Uniasselvi
# Mesma forma da Cogna: busca por URL (`?search=Enfermagem`) e o card da listagem ja traz
# tudo. O card vem no formato
#   "Bacharelado | 10 semestres  Faculdade  Graduação  Presencial  Enfermagem
#    A partir de R$ 277,60 mensais  Ver mais"
# ou seja, a MODALIDADE vem ANTES do nome do curso — dai a regex abaixo, que captura as
# duas de uma vez em vez de tentar adivinhar onde termina o nome.
#
# ⚠️ Preco nacional, como na Cogna. Tentei descer para a unidade: a pagina do curso tem
# estado -> polo (e os selects respondem a `change` por JS, porque clique normal nao
# funciona neles), mas o preco nao aparece nem depois de escolher o polo, e o botao
# "CONFIRA NOSSAS OFERTAS" nao responde a clique. Fica o "a partir de" da listagem.
#
# Nota de rota: `/graduacao/.../ead` redireciona para `/semipresencial` — na Uniasselvi o
# que as outras chamam de EAD e vendido como semipresencial.
UNIASSELVI_CARD = re.compile(
    r"Gradua[çc][ãa]o\s+(Semipresencial|Presencial|EAD|A dist[âa]ncia)\s+(.+?)\s+"
    r"(?:A partir de\s+)?R\$", re.I)
UNIASSELVI_CARDS_JS = """() => {
  const vis = e => e.offsetParent !== null;
  const cs = [...document.querySelectorAll('div,article,li,section')].filter(e =>
    vis(e) && /R\\$/.test(e.innerText||'') && (e.innerText||'').length < 420
    && !e.querySelector('div,article,li,section'));
  return [...new Set(cs.map(e => (e.parentElement?.innerText||'').replace(/\\s+/g,' ').trim()))];
}"""


def uniasselvi_le_card(txt):
    """(modalidade, nome) do card, ou (None, None)."""
    m = UNIASSELVI_CARD.search(txt)
    if not m:
        return None, None
    bruta = M.sem_acento(m.group(1))
    mod = {"semipresencial": "semipresencial", "presencial": "presencial",
           "ead": "ead", "a distancia": "ead"}.get(bruta)
    return mod, m.group(2).strip()


def uniasselvi_url_do_curso(pg, base, modalidade, sinonimos):
    for termo in sinonimos:
        url = f"{base}?search={quote(termo)}"
        try:
            pg.goto(url, timeout=TIMEOUT)
        except Exception:                              # noqa: BLE001
            continue
        pg.wait_for_timeout(6000)
        for card in pg.evaluate(UNIASSELVI_CARDS_JS):
            mod, nome = uniasselvi_le_card(card)
            if mod == modalidade and M.parecido(nome, termo):
                return f"{url}#{quote(termo)}"
    return None


def uniasselvi_precos(pg, url, modalidade, limite_unidades):
    termo = unquote(url.split("#", 1)[1]) if "#" in url else ""
    for card in pg.evaluate(UNIASSELVI_CARDS_JS):
        mod, nome = uniasselvi_le_card(card)
        if mod == modalidade and M.parecido(nome, termo):
            v = M.menor_preco(card)
            if v:
                return [{"unidade": "nacional (a partir de)", "turno": "", "preco": v}], None
    return [], f"sem card de {modalidade}"


# O terceiro campo diz se o motor precisa de Playwright. A Estacio sai por API, entao uma
# coleta so dela roda sem abrir navegador nenhum.
MOTORES = {
    "anima": (anima_url_do_curso, anima_precos, True),
    "estacio": (estacio_url_do_curso, estacio_precos, False),
    "cogna": (cogna_url_do_curso, cogna_precos, True),
    "uniasselvi": (uniasselvi_url_do_curso, uniasselvi_precos, True),
}


# ------------------------------------------------------------------- coleta
def abre_navegador(p, visivel=False):
    """Prefere o Chrome instalado na maquina ao Chromium que o Playwright baixa.

    Nao e detalhe: a protecao anti-bot da Cogna (Anhanguera e Unopar) recusa o Chromium
    do Playwright com "Access Denied" em 300 bytes, e aceita o Chrome instalado — mesmo
    headless, mesma maquina, mesmo IP. O que ela olha e a assinatura do navegador.
    Se o Chrome nao estiver instalado, cai no Chromium e os demais sites seguem
    funcionando; so a Cogna fica de fora.
    """
    args_nav = ["--disable-blink-features=AutomationControlled"]
    try:
        return p.chromium.launch(headless=not visivel, channel="chrome", args=args_nav)
    except Exception:                                  # noqa: BLE001
        print("[aviso] Chrome não encontrado; usando o Chromium do Playwright "
              "(Anhanguera e Unopar vão bloquear)")
        return p.chromium.launch(headless=not visivel, args=args_nav)


def coleta(args):
    cursos = M.cursos_alvo()
    ies = [i for i in M.ies_alvo() if not args.ies or args.ies.lower() in i["IES"].lower()]
    ies = [i for i in ies if i["ENGINE"] in MOTORES]
    if not ies:
        print("Nenhuma IES ativa com motor implementado. Motores prontos: "
              + ", ".join(MOTORES))
        return 1

    mods = [args.modalidade] if args.modalidade else ["presencial", "semipresencial", "ead"]
    hoje = M.hoje()
    linhas, falhas = [], []
    # navegador so quando algum motor selecionado precisa: uma coleta so da Estacio
    # (que sai por API) roda sem Playwright e sem Chrome instalado
    precisa_nav = any(MOTORES[i["ENGINE"]][2] for i in ies)

    with ExitStack() as pilha:
        nav = ctx = pg = p = None
        if precisa_nav:
            from playwright.sync_api import sync_playwright
            p = pilha.enter_context(sync_playwright())
            nav = abre_navegador(p, args.visivel)
            ctx = nav.new_context(viewport={"width": 1440, "height": 1000},
                                  locale="pt-BR", user_agent=(
                                      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                      "(KHTML, like Gecko) Chrome/121.0 Safari/537.36"))
            pg = ctx.new_page()

        def reabre():
            """Recria navegador e aba.

            Coleta longa derruba o navegador: a primeira rodada completa da Ânima morreu
            com TargetClosedError depois de ~20 cursos. Reabrir de tempos em tempos (e
            depois de qualquer falha) e o que faz a coleta chegar ao fim.
            """
            nonlocal nav, ctx, pg
            if not precisa_nav:
                return
            try:
                nav.close()
            except Exception:                          # noqa: BLE001
                pass
            nav = abre_navegador(p, args.visivel)
            ctx = nav.new_context(viewport={"width": 1440, "height": 1000}, locale="pt-BR")
            pg = ctx.new_page()

        feitos = 0
        for inst in ies:
            achar, precos, usa_nav = MOTORES[inst["ENGINE"]]
            for mod in mods:
                alvos = [c for c in cursos.get(mod, [])
                         if not args.curso or args.curso.lower() in c["curso"].lower()]
                print(f"\n=== {inst['IES']} · {mod} · {len(alvos)} cursos ===")
                for c in alvos:
                    # respiro preventivo: navegador aberto por muitas páginas vai
                    # acumulando memória até cair no meio da coleta
                    feitos += 1
                    if usa_nav and feitos % 12 == 0:
                        reabre()
                    try:
                        url = achar(pg, inst["URL"], mod, c["sinonimos"])
                        if not url:
                            falhas.append({"ies": inst["IES"], "modalidade": mod,
                                           "curso": c["curso"], "motivo": "curso não encontrado"})
                            print(f"  {c['curso']:<26} — não encontrado")
                            continue
                        obs, erro = precos(pg, url, mod, args.limite_unidades)
                        if erro or not obs:
                            falhas.append({"ies": inst["IES"], "modalidade": mod,
                                           "curso": c["curso"], "motivo": erro or "sem preço"})
                            print(f"  {c['curso']:<26} — {erro or 'sem preço'}")
                            continue
                        novas = [{"data": hoje, "grupo": inst["GRUPO"], "ies": inst["IES"],
                                  "modalidade": mod, "curso": c["curso"],
                                  "unidade": o["unidade"], "turno": o["turno"],
                                  "preco": o["preco"], "url": url} for o in obs]
                        # grava curso a curso: uma coleta completa leva minutos e uma queda
                        # no meio nao pode custar o que ja foi levantado
                        M.registra(novas)
                        linhas += novas
                        media = sum(o["preco"] for o in obs) / len(obs)
                        print(f"  {c['curso']:<26} R$ {media:>9,.2f}  "
                              f"({len(obs)} unid., min R$ {min(o['preco'] for o in obs):,.2f})")
                    except Exception as e:              # noqa: BLE001
                        falhas.append({"ies": inst["IES"], "modalidade": mod,
                                       "curso": c["curso"], "motivo": f"{type(e).__name__}"})
                        print(f"  {c['curso']:<26} — erro {type(e).__name__}")
                        # navegador morto derruba todos os cursos seguintes se não reabrir
                        if "TargetClosed" in type(e).__name__ or "Closed" in str(e)[:60]:
                            reabre()
        if nav:
            nav.close()

    print(f"\n{len(linhas)} observações gravadas em {M.HIST}")
    if falhas:
        print(f"{len(falhas)} falhas: " + ", ".join(
            f"{f['curso']}/{f['modalidade']}" for f in falhas[:8])
            + (" …" if len(falhas) > 8 else ""))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ies", help="filtra por nome da instituição")
    ap.add_argument("--modalidade", choices=["presencial", "semipresencial", "ead"])
    ap.add_argument("--curso", help="filtra por nome do curso")
    ap.add_argument("--limite-unidades", type=int, default=0,
                    help="teto de unidades/polos por curso (0 = todas)")
    ap.add_argument("--visivel", action="store_true", help="abre o navegador para depurar")
    ap.add_argument("--so-exportar", action="store_true",
                    help="não coleta; só reagrega o histórico para o dashboard")
    args = ap.parse_args()

    if not args.so_exportar:
        rc = coleta(args)
        if rc:
            return rc
    obj = M.exporta_web()
    print(f"Dashboard: {obj['n']} linhas agregadas, {len(obj['datas'])} data(s), "
          f"{len(obj['ies_lista'])} IES → {M.WEB}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
