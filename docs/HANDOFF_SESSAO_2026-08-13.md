# Hand-off da sessão de 13/08/2026

> Cole isto na abertura da próxima sessão. É o resumo do que mudou e do que é fácil estragar
> sem perceber — o detalhe todo está em `docs/00_HANDOFF.md`, que foi atualizado até o último
> teste desta sessão.

---

## Abra `docs/00_HANDOFF.md` e nada mais

Ele está em dia, inclusive com as conclusões que **mudaram no meio do caminho** — o preço da
Estácio que não era nacional, o motor da Ânima que estava quebrado sem ninguém saber, e o
Diário Oficial que aceita acesso automatizado.

Estado publicado: **https://claude.ai/code/artifact/91a062c8-7e5c-49da-b1e2-bb11947af321**
(republicar com o mesmo `file_path` mantém a URL).

---

## O que esta sessão entregou

**Mensalidades saiu do papel e virou bloco no dashboard.** Cobertura: **4 dos 6 grupos, 6 das 9
faculdades, 1.764 preços coletados**. Quatro motores funcionando — `anima`, `estacio`, `cogna`
e `uniasselvi`.

**Ambiente Regulatório, do zero.** Módulo navegável por tema (EaD & Polos · Medicina · Fies),
com esquema visual, feed de 11 publicações e **todas com fonte oficial conferida**.

**Duas peças mudaram de bloco**, a seu pedido: ganho de share foi para Key Players, composição
por grupo foi para o Glossário.

---

## Cinco coisas fáceis de estragar sem perceber

**1. Preço nacional e preço por unidade não são a mesma métrica.** Estácio e Ânima descem até a
unidade (até 87 observações numa linha); Cogna e Uniasselvi só publicam "a partir de" nacional
(uma observação). O agregado carrega a coluna `base` e a tela marca isso com asterisco, nota e
exclusão do gráfico de dispersão. **Se acrescentar motor novo que só dê piso nacional, grave
`unidade = "nacional (a partir de)"`** — é isso que `exporta_web()` usa para classificar.

**2. O EaD da Ânima está furado e ninguém deve comparar com o da Estácio.** No Anhembi traz 1
polo por curso quando deveria varrer 7 capitais; no São Judas não traz nada. É o **item 0** da
próxima etapa, antes de qualquer motor novo.

**3. Nada entra no regulatório sem fonte primária.** `config/regulatorio.json` é o arquivo que
se edita à mão e tem a regra escrita no topo. Quando a confirmação vier de imprensa, marque
`confianca: "a_confirmar"` — a tela mostra, e é melhor aparecer marcado do que passar por
conferido. `08_build_regulatorio.py` derruba o build em campo faltando, data inválida, fonte que
não é URL ou **ato duplicado**.

**4. Bloco novo tem de entrar nas listas do build de arquivo único.** `MODULOS` e, se tiver dado
próprio, `CORE` em `05_build_standalone.py`. Os módulos são concatenados num escopo único, então
**nome de topo repetido quebra só o standalone** — a versão servida continua funcionando, e o
defeito passa despercebido. Hoje `checa_colisoes()` derruba o build com a lista dos conflitos;
foi ele que pegou `dataLegivel`, `serie` e `desenhar` duplicados.

**5. Chave de resumo não pode ter nome de coluna.** Em `exporta_web()` isso já custou duas
vezes: a coluna `ies` virava a lista de IES distintas e **cada linha ia para a instituição
errada**. Hoje há um `assert` impedindo a terceira.

---

## O que ficou de fora, e por quê

| Item | Situação |
|---|---|
| **Uninassau** | **Não implementada de propósito.** A listagem mostra "3 primeiras parcelas: R$ 99,00" — promoção de entrada. A regra do menor preço gravaria isso como mensalidade. A URL por unidade e os três valores da página estão mapeados no handoff |
| **Unicesumar** | Catálogo de 515 cursos localizado, **sem preço**. Há um gateway com OAuth aberto — é por ali que o preço deve sair |
| **Cruzeiro do Sul** | O pior caso: loja VTEX, API dá 403, GraphQL diz `disableOffers`, nenhuma página renderizou preço |
| **Coleta automática do regulatório** | Não construída, mas **destravada**: o DOU aceita Playwright com Chrome real. Falta a curadoria, que é o que eu não automatizaria sem você ver o que o classificador decide |

---

## O achado que mais rende na próxima sessão

**O Diário Oficial da União aceita acesso automatizado** — `WebFetch` derruba a conexão, mas
Playwright com `channel="chrome"` abre normalmente, headless. A página do ato entrega tudo em
texto: `Publicado em: 21/05/2025 | Edição: 94 | Seção: 1 | Página: 59`, órgão e ementa. A busca
também funciona.

Foi isso que levou a base regulatória de 5 pendências a zero, e trouxe **três atos que a
imprensa não citava**. Duas armadilhas de busca já pagas: ato do Inep sai como "PORTARIA Nº 413"
(sem a sigla no título), e **zero resultado não prova ausência** — a Portaria MEC nº 129/2026
existe e não aparece em nenhuma variação de busca.

---

## Ordem sugerida para a próxima

1. **Consertar o laço de EaD da Ânima** — é o único ponto em que a tela mostra dois números que
   não deveriam ser lidos lado a lado.
2. **Uninassau**, confirmando antes qual dos três valores da página é a mensalidade.
3. **Coleta automática do regulatório** pela busca do DOU, com curadoria sua no meio.
4. Só então Unicesumar e Cruzeiro do Sul, que são os de pior relação esforço/retorno.

E, quando quiser série de mensalidade: basta rodar `07_fetch_mensalidades.py` em outro dia. O
histórico é append-only, o agregado se refaz sozinho e o gráfico de evolução — hoje oculto de
propósito, porque só existe uma data — nasce sem tocar em código.
