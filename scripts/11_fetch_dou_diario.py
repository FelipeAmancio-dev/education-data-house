# -*- coding: utf-8 -*-
"""
Feed diario do DOU: o que o Ministerio da Educacao publicou, com triagem de relevancia
para quem investe em equities.

DE ONDE VEM
-----------
    https://www.in.gov.br/consulta/-/buscar/dou?q=&s=do1&exactDate=personalizado...

A BUSCA do DOU com `q=` vazio e intervalo de um dia, filtrada por orgao principal
"Ministerio da Educacao". Traz a Secao 1 do dia inteiro do MEC — Gabinete do Ministro,
SERES, SESu, CNE, Inep, FNDE e tambem as universidades e institutos federais.

⚠️ **NAO use `leiturajornal`**, que era a fonte da primeira versao e esta descrita como
tal em documento antigo: ela mostra no maximo 10 atos por dia, sem paginacao. Ver o aviso
em cima da constante URL.

⚠️ Playwright com `channel="chrome"` e obrigatorio: `WebFetch` no in.gov.br derruba a
conexao ("socket hang up") e o Chromium do Playwright e barrado.

A TRIAGEM DE RELEVANCIA
-----------------------
Este script NAO decide o que e importante em abstrato — decide o que **move a agulha de
uma companhia aberta de educacao**. Sao coisas diferentes, e a diferenca e o ponto.

O usuario deu dois exemplos de BAIXA que definem a regra:

  - "PORTARIA MEC no 666: altera a tipologia dos Campi Avancados dos Institutos Federais e
    autoriza o funcionamento do Campus Realengo III do Colegio Pedro II" — publicada pelo
    **Gabinete do Ministro**, o orgao mais graduado da lista, e ainda assim irrelevante:
    trata da REDE FEDERAL. Por isso o assunto pesa mais que o orgao na classificacao.
  - "PORTARIA no 1.097 da UFBA: retificacao de homologacao de concurso" — instituicao
    federal e assunto de pessoal.

Ordem dos testes (o primeiro que casar decide):

  1. **Cita marca de grupo aberto** → ALTA. Sinal mais forte que existe: se o ato nomeia a
     Estacio ou a Anhanguera, e da companhia que se esta olhando. Usa os tokens de
     `config/grupos_marcas.json`, os mesmos do audit de grupos.
  2. **Rede federal ou pessoal/administrativo** → BAIXA. Instituto Federal, universidade
     federal, CEFET, Colegio Pedro II, hospital universitario; nomeacao, exoneracao,
     concurso, aposentadoria; regimento, orcamento, empenho.
  3. **Medida com efeito comercial direto** (suspensao de ingresso, de contrato de Fies ou
     de ProUni; descredenciamento; medida cautelar; chamamento publico) → ALTA, mesmo sem
     ser norma geral: muda a receita de quem for atingido.
  4. **Tema quente do setor privado** (EaD, Medicina, Fies, ProUni, supervisao,
     credenciamento) **em ato normativo** → ALTA.
  5. O resto → MEDIA. Tipicamente ato individual sobre uma IES privada nao mapeada:
     interessa ao setor, nao necessariamente a uma tese.

SAIDA
-----
    dashboard/data/dou_diario.json   consumido pelo bloco Ambiente Regulatorio

⚠️ Diferente do `09_fetch_dou.py`, este script ESCREVE direto no payload do dashboard, e
nao em lista de curadoria. Pode fazer isso porque nao afirma nada: mostra o titulo e a
ementa como o DOU publicou, com link para o documento. A curadoria continua sendo exigida
para entrar em `config/regulatorio.json`, que e onde o dashboard AFIRMA o que vale.

USO
---
    python scripts/11_fetch_dou_diario.py                # ultimos 15 dias uteis
    python scripts/11_fetch_dou_diario.py --dias 30
"""
import argparse
import json
import os
import re
import sys
import unicodedata
from datetime import date, timedelta

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARCAS = os.path.join(ROOT, "config", "grupos_marcas.json")
SAIDA = os.path.join(ROOT, "dashboard", "data", "dou_diario.json")

# ⚠️ NAO use `leiturajornal`, que e a pagina que se le no navegador: ela mostra no maximo
# **10 atos por dia** e nao tem paginacao nem carregamento por rolagem. Medido em
# 17/08/2026: a pagina trazia 10, a busca informava **16 resultados** para o mesmo dia e
# orgao. Um terco das publicacoes sumia em silencio, que e o pior tipo de perda.
#
# A busca com `q=` vazio e intervalo de um dia so devolve o dia inteiro, 20 por pagina,
# com a mesma estrutura de resultado.
URL = ("https://www.in.gov.br/consulta/-/buscar/dou?q=&s=do1&exactDate=personalizado"
       "&publishFrom={d}&publishTo={d}"
       "&orgPrin=Minist%C3%A9rio%20da%20Educa%C3%A7%C3%A3o")

# --------------------------------------------------------------- classificacao

# Órgãos CENTRAIS do MEC — a lista curta e conhecida de quem faz regulacao do setor.
#
# ⚠️ A logica e por INCLUSAO, e de proposito. A alternativa — listar as instituicoes
# federais para excluir — nunca termina: sao ~70 universidades, ~40 institutos federais,
# CEFETs, colegios de aplicacao, hospitais, e cada um publica sob um nome diferente
# ("PORTARIA DAP PROGESP UFCSPA", "Nº 3.368/SRDA/GAB/RTR"). Listar os seis orgaos que
# fazem regulacao e finito e estavel; o resto e, por definicao, administracao de uma
# instituicao publica — que nao move tese de companhia aberta.
ORGAO_CENTRAL = re.compile(
    r"("
    r"gabinete do ministro|secretaria executiva|"
    r"secretaria de regulacao e supervisao|secretaria de educacao superior|"
    r"conselho nacional de educacao|"
    r"instituto nacional de estudos e pesquisas educacionais|"
    r"fundo nacional de desenvolvimento da educacao"
    r")", re.I)

# EDUCACAO BASICA: nao e o mercado destas companhias.
#
# ⚠️ Calibrado pelo usuario com um exemplo: a "SUMULA DO PARECER CNE/CEB no 7/2026" trata
# do calendario escolar de 2027 por causa da Copa do Mundo Feminina. Passa pela Camara de
# **Educacao Basica** do CNE — outro nivel de ensino, sem relacao com graduacao privada.
# `CEB` no numero do parecer e o marcador mais confiavel; o resto pega o assunto.
BASICA = re.compile(
    r"("
    r"cne/ceb|camara de educacao basica|"
    r"educacao basica|ensino fundamental|ensino medio|educacao infantil|"
    # ⚠️ 18/08/2026: "primeira infancia" entrou depois de a Portaria nº 725/2026 — GT
    # sobre saude ocupacional do magisterio na primeira infancia — sair como ALTA. E
    # educacao basica escrita com outras palavras.
    r"primeira infancia|magisterio da educacao basica|"
    r"calendario escolar|creche|pre-escola|alfabetizacao"
    r")", re.I)

# Rede federal e assunto de pessoal/administracao: nao movem tese de companhia aberta.
BAIXA = re.compile(
    r"("
    r"instituto federal|institutos federais|colegio pedro ii|cefet|"
    r"universidade federal|universidades federais|hospital universitario|"
    r"campi avancados|campus avancado|"
    r"pro-reitoria|departamento de desenvolvimento de pessoas|"
    r"nomea|exonera|designa|aposentadoria|remocao|substitut|"
    # ⚠️ 18/08/2026: tres atos de pessoal/administracao passaram por aqui e viraram ALTA
    # no teste de grupo de trabalho. Cada termo abaixo saiu de um deles:
    #   Port. 707 — GT sobre "mecanismos de afastamento" de servidor
    #   Port. 706 — GT "Saude do Trabalhador" das instituicoes federais
    #   Port. 646 — "delega competencia aos titulares de unidades do MEC"
    r"afastamento|saude ocupacional|saude do trabalhador|"
    r"instituicoes federais|instituicao federal|"
    r"redistribuicao de cargos|avocacao|delega\w* de competencia|delega competencia|"
    r"concurso publico|homologacao do resultado|resultado final do concurso|"
    r"regimento interno|estrutura (organizacional|regimental)|"
    r"orcamentari|empenho|dotacao|"
    r"stricto sensu|mestrado profissional|doutorado"     # pos avaliada pela Capes
    r")", re.I)

# Temas que mexem com o setor privado.
QUENTE = re.compile(
    r"("
    r"educacao a distancia|ensino a distancia|\bead\b|polo de apoio|"
    # "formatos de oferta" e o nome que a Portaria MEC nº 378/2025 usa para a regra que
    # define presencial × semipresencial × EaD — sem este termo ela escapava da triagem
    r"formato de oferta|formatos de oferta|oferta de cursos superiores|"
    r"regras de transicao|marco regulatorio|processos regulatorios|"
    r"curso de medicina|medicina\b|chamamento publico|"
    r"\bfies\b|financiamento estudantil|\bprouni\b|"
    r"supervis|credenciamento|recredenciamento|descredenciamento|"
    r"suspensao de ingresso|suspensao de contrato|"
    r"avaliacao (institucional|de cursos)|sinaes|enade|enamed"
    r")", re.I)

# Ato de alcance normativo — o tipo que muda regra para todo mundo.
NORMATIVO = re.compile(
    r"^\s*(lei|decreto|medida provisoria|portaria normativa|resolucao|instrucao normativa)\b",
    re.I)

# ⚠️ Medida com EFEITO COMERCIAL DIRETO, mesmo sem ser norma geral.
#
# Isto entrou depois de CALIBRAR contra dado real, e a calibração é o ponto. A primeira
# versão exigia título normativo para dar "alta", e "PORTARIA SERES/MEC nº 404" não casa
# com `portaria normativa`. Resultado: 15 dias de coleta com **zero alta**, incluindo atos
# que suspendem contrato de Fies — exatamente o tipo de coisa que muda a receita de uma
# mantenedora. Um corte que nunca dispara não está sendo conservador, está quebrado.
EFEITO_DIRETO = re.compile(
    r"("
    r"suspensao (de|do|da) (ingresso|contrato|autonomia|prerrogativa)|"
    r"suspensao (pronatec|prouni)|suspensao de novos contratos|"
    r"descredenciamento|medida cautelar|procedimento sancionador|"
    r"desativacao de curso|reducao de vagas|"
    r"chamamento publico"
    r")", re.I)

# ALTA por definicao do usuario (17/08/2026), nas palavras dele:
#   "portarias com mudancas regulatorias, instituicao de grupos de trabalho, aprovacoes de
#    novas vagas e novos cursos de medicina".
#
# Os tres primeiros sao sinal de que a REGRA vai mudar — grupo de trabalho e o passo que
# antecede norma nova, e por isso vale mais do que o volume dele sugere. Vagas e curso de
# medicina sao oferta entrando no mercado, que e o lado da receita.
# ⚠️ DIVIDIDO EM DOIS em 18/08/2026, e a divisao e a regra.
#
# A primeira coleta depois de a automacao entrar no ar devolveu **5 altas, e as 5 eram
# falso positivo**: GT sobre saude ocupacional de professor da primeira infancia, GT
# sobre afastamento de servidor, GT de saude do trabalhador da rede federal e uma
# portaria que delega competencia interna do MEC. Todas casavam por "grupo de trabalho"
# ou "altera a portaria" — gatilhos que nao dizem NADA sobre o assunto do ato.
#
# E o mesmo defeito que ja tinha tirado "dispoe sobre" e "regulamenta" daqui, e a
# correcao e a mesma: gatilho generico so vira alta **com tema do setor junto**. O que
# separa "GT do novo marco do EaD" de "GT de saude do trabalhador" nao e a forma do ato,
# e o assunto.
#
# ALTA_SEMPRE: o gatilho JA descreve oferta entrando no mercado — nao precisa de tema.
ALTA_SEMPRE = re.compile(
    r"("
    r"aumento de vagas|ampliacao de vagas|novas vagas|aditamento de vagas|"
    r"autoriza o funcionamento do curso de medicina|"
    r"autorizacao (de|do) curso de medicina|curso de medicina.{0,40}autoriza"
    r")", re.I)

# ALTA_COM_TEMA: forma de ato que ANTECEDE mudanca de regra — vale muito quando o
# assunto e do setor, e nao vale nada quando nao e. Exige QUENTE junto.
ALTA_COM_TEMA = re.compile(
    r"("
    r"institui (o )?grupo de trabalho|grupo de trabalho|comissao especial|"
    r"altera a portaria|altera o decreto|altera a resolucao|"
    r"revoga a portaria|revoga o decreto"
    # ⚠️ "dispoe sobre" e "regulamenta" SAIRAM daqui: sao genericos demais e pegavam ato
    # puramente administrativo — "Dispoe sobre a redistribuicao de cargos" e "Dispoe sobre
    # a avocacao de competencia" entraram como alta na primeira rodada. Os dois continuam
    # alcancaveis pelo teste de norma la embaixo, que exige tema do setor junto.
    r")", re.I)

# ⚠️ Ato que NOMEIA uma IES pelo codigo nao e norma, ainda que saia do Gabinete do
# Ministro e fale de "oferta de cursos superiores".
#
# 18/08/2026: a Retificacao da Portaria MEC nº 901 — "Fica credenciada a Faculdade
# Republica de Sao Paulo - Faresp (Cod. 28570)" — saiu como ALTA pelo teste de norma,
# porque o orgao da peso e a ementa casa "oferta de cursos superiores". E credenciamento
# de UMA faculdade independente: media, que e onde o projeto ja poe ato individual.
#
# Aceita as duas grafias vistas no DOU — "(Cod. e-MEC 20)" e "(Cod. 28570)". Isto NAO
# desliga a promocao por codigo: `normaliza()` roda depois e devolve o ato para alta
# quando o codigo aponta um grupo aberto, que e o caso que interessa.
IES_NOMEADA = re.compile(r"\(\s*cod\.?\s*(e-mec\s*)?:?\s*\d{1,6}\s*\)", re.I)

# MEDIA por definicao do usuario: "aprovacao de polos, temas como Fies e ProUni".
# Sao atos do mercado privado que interessam ao setor, mas nao mudam a regra do jogo.
MEDIA_EXPLICITA = re.compile(
    r"("
    r"polo de apoio|polos de apoio|aprovacao de polo|credenciamento de polo|"
    r"\bpolo\b|\bpolos\b|"
    r"\bfies\b|financiamento estudantil|\bprouni\b"
    r")", re.I)


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", str(s or ""))
                   if unicodedata.category(c) != "Mn").lower()


def carrega_emec():
    """{codigo e-MEC: grupo} — vem do de-para gerado por `10_ingest_emec.py`.

    ⚠️ É o vínculo mais forte possível entre um ato e uma companhia: o código de IES é
    identificador, não nome parecido. Quando o ato traz `Cód. e-MEC 20`, sabemos com
    certeza de quem ele fala. Se o de-para não existir nesta cópia, devolve vazio e a
    classificação segue pelos tokens de marca."""
    cam = os.path.join(ROOT, "data_processed", "emec_ies.csv")
    if not os.path.exists(cam):
        return {}
    import csv
    out = {}
    with open(cam, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if r.get("co_ies") and r.get("grupo"):
                out[r["co_ies"]] = r["grupo"]
    return out


def carrega_marcas():
    """{token: grupo}, dos mesmos tokens que o audit de grupos usa."""
    d = json.load(open(MARCAS, encoding="utf-8"))
    out = {}
    for grupo, tokens in d.items():
        if grupo.startswith("_") or not isinstance(tokens, list):
            continue
        for t in tokens:
            out[sem_acento(t)] = grupo
    return out


def resumo_util(ementa):
    """Só a EMENTA de verdade, sem o preâmbulo de quem assina.

    ⚠️ Este corte é o que faz a classificação funcionar, e custou um falso negativo para
    ser descoberto. O texto que o DOU devolve é:

        "Renova a qualificação ... UPF (Cód. e-MEC 20). A SECRETÁRIA DE REGULAÇÃO E
         SUPERVISÃO DA EDUCAÇÃO SUPERIOR, no uso das atribuições que lhe confere o
         Decreto nº 12.769 ..."

    Só a primeira frase é o assunto; o resto é fórmula. Classificar sobre o texto inteiro
    fazia "O SECRETÁRIO ... SUBSTITUTO" casar com o padrão de pessoal e rebaixar o ato
    para BAIXA — três portarias da SERES foram parar lá por causa da assinatura de quem
    publicou, não do que o ato faz.

    Quando não há ementa (o texto já começa no preâmbulo), devolve vazio: aí a
    classificação se apoia só no título, e é melhor cair em MÉDIA do que fingir certeza.
    """
    e = (ementa or "").strip()
    corte = re.search(
        r"\b(O|A)\s+(MINISTR|SECRETÁRI|SECRETARI|PRESIDENTE|REITOR|DIRETOR|PRÓ-REITOR|"
        r"CONSELH|COORDENADOR|SUBSECRETÁRI)",
        e)
    if corte:
        e = e[:corte.start()]
    return e.strip()


def _chave_nome(s):
    """Nome normalizado para casar mantenedora do DOU com a nossa base.

    Tira acento, caixa e as formas societárias (LTDA, S/A, ME, EIRELI…), que aparecem
    numa fonte e não na outra — "Fasipe Centro Educacional Ltda" no DOU contra "FASIPE
    CENTRO EDUCACIONAL" no e-MEC.
    """
    s = "".join(c for c in unicodedata.normalize("NFD", str(s or ""))
                if unicodedata.category(c) != "Mn").upper()
    s = re.sub(r"\b(LTDA|S/?A|ME|EIRELI|EPP|SOCIEDADE SIMPLES|SS)\b", " ", s)
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def indice_nomes():
    """{nome normalizado: (nome da IES, grupo)} a partir do de-para do e-MEC.

    Indexa por mantenedora E por nome de IES, porque o DOU cita ora um, ora outro: as
    súmulas do CNE trazem a MANTENEDORA ("Interessado: Fasipe Centro Educacional Ltda"),
    enquanto as portarias da SERES trazem a IES ("a IES Universidade de Passo Fundo").
    """
    cam = os.path.join(ROOT, "data_processed", "emec_ies.csv")
    if not os.path.exists(cam):
        return {}
    import csv
    idx = {}
    with open(cam, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            for campo in ("mantenedora", "ies_censo", "ies_emec"):
                k = _chave_nome(r.get(campo))
                if len(k) > 8:
                    idx.setdefault(k, (r.get("ies_censo") or "", r.get("grupo") or ""))
    return idx


def casa_nome(nome, idx):
    """(nome da IES na nossa base, grupo) ou (None, None).

    ⚠️ Exato primeiro; prefixo de 22 caracteres só como segunda tentativa. O prefixo é
    o que resolve "Organização Mogiana de Educação e Cultura Sociedade Simples Ltda" ->
    "ORGANIZACAO MOGIANA DE EDUCACAO E CULTURA", mas é também por onde entraria falso
    positivo, então precisa dos dois lados começando igual e de tamanho mínimo.
    """
    k = _chave_nome(nome)
    if len(k) < 10:
        return None, None
    if k in idx:
        return idx[k]
    for kk, v in idx.items():
        if len(kk) >= 22 and (kk.startswith(k[:22]) or k.startswith(kk[:22])):
            return v
    return None, None


IDX_NOMES = {}


def instituicao_citada(ementa, emec_por_codigo):
    """(nome da IES citada, código e-MEC, grupo) — o que o ato está tratando.

    ⚠️ Só 3 dos 244 atos de uma coleta de 20 dias trazem código e-MEC na ementa; o nome
    aparece um pouco mais. Por isso os dois caminhos: o CÓDIGO, quando existe, é exato e
    cruza com `data_processed/emec_ies.csv` para dar o grupo econômico; o NOME serve de
    consolo quando não há código — pelo menos o leitor vê de quem o ato fala.

    Cuidado com o falso amigo: "e-MEC: 202221701" nas súmulas do CNE é número de PROCESSO,
    não de instituição. Só `Cód. e-MEC NNN` é código de IES.
    """
    e = ementa or ""
    cod = None
    mc = re.search(r"[Cc][óo]d\.?\s*e-MEC[:\s]*(\d{1,6})", e)
    if mc:
        cod = mc.group(1)

    # duas formas de o DOU nomear quem o ato trata, e as duas aparecem:
    #   portaria da SERES  → "a IES Universidade de Passo Fundo - UPF (Cód. e-MEC 20)"
    #   súmula do CNE      → "Interessado: Fasipe Centro Educacional Ltda. - Sinop/MT"
    nome = None
    mn = re.search(r"IES\s+([A-ZÁÂÃÉÊÍÓÔÕÚÇ][^(.;]{6,70})", e)
    if mn:
        nome = mn.group(1).strip(" -")
    else:
        mi = re.search(r"Interessad[oa]s?:\s*(.{6,120}?)"
                       r"(?:\.\s|;|\s*Assunto:|\s*Relator:|$)", e, re.S)
        if mi:
            nome = re.sub(r"\s+", " ", mi.group(1)).strip(" .-")

    # o código é identificador e ganha do nome; o nome é a segunda tentativa
    grupo = emec_por_codigo.get(cod) if cod else None
    if not grupo and nome:
        achado, g = casa_nome(nome, IDX_NOMES)
        if achado:
            nome, grupo = achado, (g or None)
    return nome, cod, grupo


def classifica(titulo, orgao, ementa, marcas):
    """Devolve (relevancia, motivo, [grupos citados]).

    A ordem dos testes E a regra: o primeiro que casar decide.

    Calibrado com o usuario em 17/08/2026, nas palavras dele:
      BAIXA  — educacao basica, rede federal, pessoal
      MEDIA  — aprovacao de polos, temas como Fies e ProUni
      ALTA   — portarias com mudanca regulatoria, instituicao de grupo de trabalho,
               aprovacao de novas vagas e de novos cursos de medicina
    """
    resumo = resumo_util(ementa)
    txt = sem_acento(f"{titulo} {resumo}")
    t = sem_acento(titulo)

    # 1) cita companhia aberta — o sinal mais forte que existe
    citados = sorted({g for tok, g in marcas.items()
                      if re.search(rf"{re.escape(tok)}", txt)})
    if citados:
        return "alta", f"cita {', '.join(citados)}", citados

    # 2) educacao basica: outro nivel de ensino, fora do mercado destas companhias
    b = BASICA.search(txt)
    if b:
        return "baixa", f"educação básica ({b.group(0).strip()})", []

    # 3) orgao que nao faz regulacao: administracao de instituicao publica.
    # Vem cedo porque muitos desses atos nao tem ementa — so o orgao identifica.
    if not ORGAO_CENTRAL.search(sem_acento(orgao)):
        return "baixa", f"ato interno de {orgao}", []

    # 4) rede federal, pessoal ou administracao interna
    m = BAIXA.search(txt)
    if m:
        return "baixa", f"rede federal ou ato interno ({m.group(0).strip()})", []

    # 5) o que o usuario chamou de ALTA, explicitamente e sem depender do assunto
    a = ALTA_SEMPRE.search(txt)
    if a:
        return "alta", f"mudança regulatória ou nova oferta: {a.group(0).strip()}", []

    # 5b) gatilho generico (GT, altera/revoga portaria): so e alta COM tema do setor.
    # Sem tema, cai adiante e termina em media — nao volta a ser alta por acidente.
    a = ALTA_COM_TEMA.search(txt)
    if a:
        qa = QUENTE.search(txt)
        if qa:
            return "alta", (f"mudança regulatória ou nova oferta: {a.group(0).strip()} "
                            f"({qa.group(0).strip()})"), []

    # 6) medida com efeito comercial direto sobre quem opera no setor privado
    e = EFEITO_DIRETO.search(txt)
    if e:
        return "alta", f"medida com efeito direto: {e.group(0).strip()}", []

    # 7) SUMULA DE PARECERES nao e norma, e a ATA do que o CNE decidiu sobre instituicoes
    # uma a uma. Sem esta excecao, 9 dos 10 primeiros "alta" de uma coleta eram sumula, o
    # que enterraria o ato que de fato importa.
    if re.match(r"^\s*sumula", t):
        return "media", "súmula do CNE — lote de decisões sobre instituições", []

    # 8) ato sobre uma IES nomeada pelo codigo: individual, nao norma
    if IES_NOMEADA.search(txt):
        return "media", "ato sobre instituição específica (código na ementa)", []

    # 9) tema do setor com alcance de norma.
    #
    # ⚠️ "Alcance de norma" NAO e so o titulo. Calibrado contra as 11 decisoes ja curadas
    # em `config/regulatorio.json`: exigindo apenas `NORMATIVO`, acertava 5 de 11. As que
    # escapavam eram "PORTARIA MEC no X" — e a 378, a 381 e a 506 sao justamente as que
    # remodelaram o EaD em 2025. Portaria do Gabinete do Ministro sobre tema do setor e
    # norma por natureza, ainda que o titulo nao diga "normativa".
    q = QUENTE.search(txt)
    org = sem_acento(orgao)
    peso_de_norma = (NORMATIVO.match(t)
                     or "gabinete do ministro" in org
                     or "conselho nacional de educacao" in org
                     # o Inep define os exames que travam expansao (Enade, Enamed)
                     or "instituto nacional de estudos" in org)
    if q and peso_de_norma:
        return "alta", f"norma sobre {q.group(0).strip()}", []

    # o que o usuario chamou de MEDIA: polos, Fies, ProUni.
    #
    # ⚠️ Vem DEPOIS do teste de norma, e a ordem custou 2 acertos para ser descoberta.
    # Posto antes, este teste engolia a **Lei nº 15.388/2026**, que e a reforma do Fies —
    # classificada como "media" por citar Fies, quando e o ato de maior impacto do tema no
    # periodo. A regra correta: ato ROTINEIRO sobre Fies/ProUni/polo e media; NORMA sobre
    # Fies e alta. O que separa os dois e o alcance, nao o assunto.
    md = MEDIA_EXPLICITA.search(txt)
    if md:
        return "media", f"tema do setor: {md.group(0).strip()}", []

    if q:
        return "media", f"trata de {q.group(0).strip()}", []

    return "media", "ato do setor sem tema de tese identificado", []


# ------------------------------------------------------------------ coleta

JS_EXTRAI = r"""
() => {
  const out = [];
  document.querySelectorAll('h5 a, a.title-marker').forEach(a => {
    const titulo = (a.innerText || '').trim();
    if (!titulo) return;
    let bloco = a.closest('div');
    for (let i = 0; i < 5 && bloco && !/Seção 1|Edição/.test(bloco.innerText || ''); i++) {
      bloco = bloco.parentElement;
    }
    const linhas = ((bloco ? bloco.innerText : '') || '')
      .split('\n').map(s => s.trim()).filter(Boolean);
    const iTit = linhas.findIndex(l => l === titulo);
    // a trilha é "Seção 1 > Ministério da Educação > <órgão> [> <subórgão>]"
    const trilha = linhas.slice(0, iTit).filter(l => !/^Edição/.test(l));
    const ed = linhas.find(l => /Edição/.test(l)) || '';
    // a ementa do site repete o título na frente; tira para não duplicar na tela
    let ementa = linhas.slice(iTit + 1).join(' ');
    if (ementa.startsWith(titulo)) ementa = ementa.slice(titulo.length).trim();
    out.push({ titulo, url: a.getAttribute('href') || '', trilha, ed,
               ementa: ementa.slice(0, 400) });
  });
  return out;
}
"""

RE_ED = re.compile(r"Edição Nº\s*([\w-]+)\s*de\s*(\d{2})/(\d{2})/(\d{4})\s*-\s*Pág\.\s*(\d+)")


def triagem(titulo, orgao, ementa, marcas, emec):
    """classifica() + a promocao por codigo e-MEC, que e o passo seguinte dela.

    Separado de `normaliza()` para que `--reclassificar` possa reprocessar o payload que
    ja esta em disco sem raspar o DOU de novo — e para que os dois caminhos nunca possam
    divergir na regra.
    """
    rel, motivo, grupos = classifica(titulo, orgao, ementa, marcas)
    nome_ies, cod_ies, grupo_cod = instituicao_citada(ementa, emec)
    # o codigo e-MEC e identificador: se ele aponta um grupo, o ato fala daquele grupo,
    # e isso vale mais do que a coincidencia de token de marca
    # ⚠️ "Independentes" e bucket residual de IES nao mapeada, nao e player: identificar a
    # instituicao e util para o leitor, mas nao torna o ato relevante para uma tese.
    if grupo_cod and grupo_cod != "Independentes" and grupo_cod not in grupos:
        grupos = sorted(set(grupos) | {grupo_cod})
        if rel != "alta":
            rel, motivo = "alta", f"cita {grupo_cod}"
    return rel, motivo, grupos, nome_ies, cod_ies


def normaliza(item, marcas, emec):
    m = RE_ED.search(item.get("ed", "") or "")
    edicao = pagina = data_iso = None
    if m:
        edicao, dd, mm, yyyy, pagina = m.groups()
        data_iso = f"{yyyy}-{mm}-{dd}"
    trilha = [t for t in item.get("trilha", []) if t not in ("Seção 1", "Ministério da Educação")]
    orgao = trilha[0] if trilha else "Ministério da Educação"
    sub = trilha[-1] if len(trilha) > 1 else ""
    url = item.get("url") or ""
    if url.startswith("/"):
        url = "https://www.in.gov.br" + url
    rel, motivo, grupos, nome_ies, cod_ies = triagem(
        item["titulo"], orgao, item.get("ementa", ""), marcas, emec)
    return {
        "data": data_iso, "titulo": item["titulo"], "url": url,
        "orgao": orgao, "suborgao": sub, "edicao": edicao, "pagina": pagina,
        "ementa": (item.get("ementa") or "").strip(),
        "resumo": resumo_util(item.get("ementa", "")),
        "relevancia": rel, "motivo": motivo, "grupos": grupos,
        "ies_citada": nome_ies or "", "cod_ies": cod_ies or "",
    }


# ------------------------------------------------------------------ autoteste

# ⚠️ O hand-off manda "rodar o teste de novo ao mexer nos padroes" desde 17/08/2026, mas
# o teste so existia como conta feita a mao numa sessao. Aqui ele vira codigo: sao os
# mesmos casos, e agora falham sozinhos.
#
# Os orgaos de `config/regulatorio.json` sao apelidos ("MEC", "Inep"); o DOU publica o
# nome por extenso, que e o que a triagem le. Este de-para e so do teste.
ORGAO_TESTE = {
    "MEC": "Gabinete do Ministro",
    "Inep": "Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira",
    "FNDE": "Fundo Nacional de Desenvolvimento da Educação",
}

# Casos observados no DOU, com o rotulo que o usuario definiu em 17/08/2026.
CASOS = [
    # os dois exemplos de BAIXA que ele deu, e que definiram a regra
    ("baixa", "PORTARIA MEC nº 666, DE 30 DE JULHO DE 2025", "Gabinete do Ministro",
     "Altera a tipologia dos Campi Avançados dos Institutos Federais e autoriza o "
     "funcionamento do Campus Realengo III do Colégio Pedro II."),
    ("baixa", "PORTARIA Nº 1.097, DE 5 DE AGOSTO DE 2026", "Universidade Federal da Bahia",
     "Retificação de homologação de resultado final de concurso público."),

    # ⚠️ os 5 falsos positivos da primeira coleta com a automacao no ar (18/08/2026).
    # Todos casavam gatilho generico de ALTA sem tema do setor junto.
    ("baixa", "PORTARIA Nº 725, DE 13 DE AGOSTO DE 2026", "Secretaria Executiva",
     "Institui o Grupo de Trabalho Nacional sobre Condições de Trabalho e Saúde "
     "Ocupacional do Magistério na Primeira Infância."),
    ("baixa", "PORTARIA Nº 707, DE 6 DE AGOSTO DE 2026", "Secretaria Executiva",
     "Institui Grupo de Trabalho - GT Formação Complementar de Pós-Graduação, com o "
     "objetivo de elaborar subsídios para o aprimoramento de mecanismos de afastamento "
     "para capacitação dos servidores."),
    ("baixa", "PORTARIA Nº 706, DE 6 DE AGOSTO DE 2026", "Secretaria Executiva",
     "Institui Grupo de Trabalho - GT Saúde do Trabalhador, com o objetivo de elaborar "
     "subsídios para o aprimoramento da saúde dos trabalhadores das Instituições "
     "Federais de Ensino."),
    ("baixa", "PORTARIA MEC Nº 646, DE 30 DE JULHO DE 2026", "Gabinete do Ministro",
     "Altera a Portaria MEC nº 1.819, de 11 de setembro de 2023, que delega competência "
     "aos titulares de unidades do Ministério da Educação e aos Dirigentes Máximos das "
     "entidades vinculadas."),
    ("media", "RETIFICAÇÃO", "Gabinete do Ministro",
     "A Portaria MEC nº 901, de 23 de dezembro de 2025, passa a vigorar com a seguinte "
     "redação: Art. 2º Fica credenciada a Faculdade República de São Paulo - Faresp "
     "(Cód. 28570), para oferta de cursos superiores no formato semipresencial."),

    # ⚠️ o outro lado do mesmo corte: com TEMA DO SETOR junto, o gatilho generico continua
    # sendo alta. Sem estes dois casos, a correcao de 18/08 poderia ser "consertada" para
    # o outro extremo — matando o sinal que o usuario pediu — sem nada acusar.
    ("alta", "PORTARIA Nº 900, DE 1º DE AGOSTO DE 2026", "Gabinete do Ministro",
     "Institui Grupo de Trabalho para revisão do marco regulatório da educação a "
     "distância e dos polos de apoio presencial."),
    ("alta", "PORTARIA MEC Nº 910, DE 1º DE AGOSTO DE 2026", "Gabinete do Ministro",
     "Altera a Portaria MEC nº 378, de 19 de maio de 2025, que dispõe sobre os formatos "
     "de oferta de cursos superiores."),
]


def autoteste():
    """Roda a triagem contra os casos conhecidos. Sai 1 se algum divergir."""
    global IDX_NOMES
    IDX_NOMES = {}
    marcas = carrega_marcas()
    falhas = []

    print("— casos observados no DOU —")
    for esperado, titulo, orgao, ementa in CASOS:
        rel, motivo, _ = classifica(titulo, orgao, ementa, marcas)
        ok = rel == esperado
        if not ok:
            falhas.append((titulo, esperado, rel, motivo))
        print("  {} {:5} → {:5}  {:44} {}".format(
            "ok   " if ok else "FALHA", esperado, rel, titulo[:44], motivo[:44]))

    # as decisoes ja curadas: sao de alto impacto por definicao — entraram no
    # `config/regulatorio.json` porque alguem leu o documento e decidiu que valem.
    reg = os.path.join(ROOT, "config", "regulatorio.json")
    print("— decisões curadas em config/regulatorio.json (esperado: alta) —")
    with open(reg, encoding="utf-8") as f:
        decisoes = json.load(f).get("decisoes", [])
    for d in decisoes:
        org = d.get("orgao", "")
        if org not in ORGAO_TESTE:
            # ⚠️ Lei e Decreto saem sob a Presidência da República, fora do recorte deste
            # feed (que busca `orgPrin=Ministério da Educação`). Ficam de fora do teste
            # por alcance da COLETA, nao por duvida sobre a classificacao.
            print("  --    (fora do feed: órgão {}) {}".format(org, d["documento"][:40]))
            continue
        rel, motivo, _ = classifica(d["documento"], ORGAO_TESTE[org], d.get("resumo", ""), marcas)
        ok = rel == "alta"
        if not ok:
            falhas.append((d["documento"], "alta", rel, motivo))
        print("  {} alta  → {:5}  {:44} {}".format(
            "ok   " if ok else "FALHA", rel, d["documento"][:44], motivo[:44]))

    if falhas:
        print("\n{} FALHA(S):".format(len(falhas)))
        for t, esp, got, mot in falhas:
            print("  {} — esperado {}, veio {} ({})".format(t[:60], esp, got, mot))
        return 1
    print("\nTodos os casos passaram.")
    return 0


def reclassifica():
    """Recalcula a relevância do payload que já está em disco, sem raspar o DOU.

    Existe porque a regra de triagem muda mais rápido do que o dado: quando um falso
    positivo é corrigido, o feed publicado continua errado até a próxima coleta. Como
    título, órgão e ementa estão gravados, a reclassificação é offline e imediata.
    """
    global IDX_NOMES
    IDX_NOMES = indice_nomes()
    marcas, emec = carrega_marcas(), carrega_emec()
    with open(SAIDA, encoding="utf-8") as f:
        payload = json.load(f)

    mudou, porRel = [], {}
    for p in payload.get("publicacoes", []):
        antes = p.get("relevancia")
        rel, motivo, grupos, nome_ies, cod_ies = triagem(
            p.get("titulo", ""), p.get("orgao", ""), p.get("ementa", ""), marcas, emec)
        if rel != antes:
            mudou.append((antes, rel, p.get("titulo", ""), motivo))
        p.update({"relevancia": rel, "motivo": motivo, "grupos": grupos,
                  "ies_citada": nome_ies or "", "cod_ies": cod_ies or ""})
        porRel[rel] = porRel.get(rel, 0) + 1

    payload["por_relevancia"] = porRel
    with open(SAIDA, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))

    print("{} atos · {} reclassificados".format(len(payload.get("publicacoes", [])), len(mudou)))
    for antes, dep, tit, mot in mudou:
        print("  {:5} → {:5}  {:52} {}".format(antes, dep, tit[:52], mot[:50]))
    print("por relevância: {}".format(porRel))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dias", type=int, default=15, help="dias úteis para trás (padrão 15)")
    ap.add_argument("--autoteste", action="store_true",
                    help="roda a triagem contra os casos conhecidos e sai (sem rede)")
    ap.add_argument("--reclassificar", action="store_true",
                    help="recalcula a relevância do payload em disco, sem raspar o DOU")
    args = ap.parse_args()

    if args.autoteste:
        return autoteste()
    if args.reclassificar:
        return reclassifica()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright não instalado. Rode: python -m playwright install chromium")
        return 1

    marcas = carrega_marcas()
    emec = carrega_emec()
    global IDX_NOMES
    IDX_NOMES = indice_nomes()
    print(f"{len(marcas)} tokens de marca · {len(emec)} códigos e-MEC · "
          f"{len(IDX_NOMES)} nomes indexados")

    # só dias úteis: o DOU da Seção 1 não sai em fim de semana (edição extra é exceção)
    dias, d = [], date.today()
    while len(dias) < args.dias:
        if d.weekday() < 5:
            dias.append(d)
        d -= timedelta(days=1)

    todos, vistos = [], set()
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True)
        pg = b.new_page(viewport={"width": 1400, "height": 1200})
        for dia in dias:
            u = URL.format(d=dia.strftime("%d-%m-%Y"))
            itens = []
            try:
                pg.goto(u, wait_until="domcontentloaded", timeout=90000)
                pg.wait_for_timeout(4000)
                # a busca traz 20 por pagina; `currentPage` na URL NAO funciona (devolve
                # sempre a primeira), entao a paginacao e pelo botao, que e JS
                vistas = set()
                for _ in range(6):
                    lote = pg.evaluate(JS_EXTRAI)
                    if not lote or lote[0].get("url") in vistas:
                        break
                    vistas.add(lote[0].get("url"))
                    itens.extend(lote)
                    seta = pg.query_selector("#rightArrow")
                    if not seta or not seta.is_enabled():
                        break
                    seta.click()
                    pg.wait_for_timeout(3000)
            except Exception as e:                       # noqa: BLE001
                print(f"  {dia:%d/%m} falhou: {type(e).__name__}")
                continue
            novos = 0
            for it in itens:
                r = normaliza(it, marcas, emec)
                if not r["url"] or r["url"] in vistos:
                    continue
                vistos.add(r["url"])
                todos.append(r)
                novos += 1
            print(f"  {dia:%d/%m/%Y}: {novos} atos")
        b.close()

    todos.sort(key=lambda r: (r["data"] or "", r["titulo"]), reverse=True)
    porRel = {}
    for r in todos:
        porRel[r["relevancia"]] = porRel.get(r["relevancia"], 0) + 1

    obj = {
        "atualizado_em": date.today().isoformat(),
        "fonte": "Diário Oficial da União — Seção 1, Ministério da Educação",
        "url_fonte": "https://www.in.gov.br/leiturajornal?org=Ministério da Educação",
        "n": len(todos),
        "dias": sorted({r["data"] for r in todos if r["data"]}, reverse=True),
        "por_relevancia": porRel,
        "publicacoes": todos,
    }
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    with open(SAIDA, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))

    print()
    print(f"total: {len(todos)} atos em {len(obj['dias'])} dias")
    for k in ("alta", "media", "baixa"):
        print(f"  {k:<6}: {porRel.get(k, 0)}")
    print(f"→ {SAIDA}  ({os.path.getsize(SAIDA)/1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
