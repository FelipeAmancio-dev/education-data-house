# Hand-off da sessão de 14/08/2026

> Cole isto na abertura da próxima sessão. O detalhe todo está em `docs/00_HANDOFF.md`,
> que foi atualizado até o último teste desta sessão.

---

## Abra `docs/00_HANDOFF.md` e nada mais

Ele está em dia, inclusive com o que **mudou de conclusão** aqui: o "bug da Geografia" e o
"bug do Excel" não eram bugs do código servido, e a soma que não fechava 100% não era erro
de dado.

---

## O que esta sessão entregou

Uma lista longa de ajustes pedidos pelo usuário, todos aplicados e verificados. Os que
importam para quem for continuar:

**Dois defeitos reais, com a mesma raiz.** A Geografia não abria e o Excel não baixava —
os dois **só no artifact publicado**, nunca no servidor local (medido: 12 de 12 aberturas
OK). A Geografia estava quebrada porque `app.js` chamava `fetch('data/geo/uf.geojson')`
cru, fora do helper que consulta os dados embutidos; **corrigido** com `carregarGeo()`. O
Excel **não tem conserto**: o sandbox do artifact bloqueia download iniciado pela própria
página. Para baixar, use o servidor local ou o arquivo único.

**As barras 100% agora fecham 100%.** Cada fatia passava por um `.toFixed(1)` separado e a
soma dava 99,8% ou 100,1%. O dado sempre esteve certo. Hoje `reparte100()` usa maior resto.

**Key Players e Cursos passaram a seguir a seleção.** Não sobrou nenhuma peça fixa nas 7
companhias abertas — elas continuam sendo o padrão, mas agora são só o estado inicial dos
chips. Saíram 12 KPIs, três seções e o bloco Rankings inteiro.

**O DOU virou coletor.** `scripts/09_fetch_dou.py` varre 5 anos e entrega **176 candidatos**
para curadoria — a partir de ~20.000 resultados brutos.

**O e-MEC entrou, e a Geografia foi reconstruída em cima dele e do que já havia.** O
de-para casa **2.636 IES, 99,9% das matrículas**. Mas o endereço do e-MEC é o da **sede** —
não resolve campus/polo, ao contrário do que o handoff esperava. A capilaridade veio do
`ies_mun`, que o projeto já tinha, com os centroides do IBGE.

---

## Cinco coisas fáceis de estragar sem perceber

**1. Teste o arquivo único, não só o servidor.** Os dois defeitos desta sessão viviam
exatamente onde ninguém testa por hábito. É o mesmo motivo pelo qual a colisão de nome de
topo passou despercebida na sessão passada. `python scripts/05_build_standalone.py` e abra
`outputs/dashboard_standalone.html` por `file://`.

**2. A UF de uma IES é o endereço da sede.** No EAD isso não é onde o aluno está: a Unopar
concentra 75% da Cogna no Paraná porque o Censo lança a matrícula de EAD na sede, não no
polo. O Glossário avisa isso na tela, **por regra de dado** (≥40% da base do grupo e ≥80%
de EAD), não por lista de nomes — vale para qualquer grupo com o mesmo desenho.

**3. `containLabel` do ECharts não reserva espaço para o nome do eixo.** Só para os
rótulos. Se puser `xAxis.name`, aumente `grid.bottom` na mão — senão o texto fica na option
e invisível na tela, que é bem pior que não estar lá.

**4. `data-din` só em elemento que a view reescreve.** Posto num `<h3>` fixo, ele impede a
tradução: `capturarEstaticos()` pula o nó e o título nunca vira inglês.

**5. `ies_mun` tem 1.044 linhas com ZERO aluno.** Município com oferta registrada e nenhum
matriculado. Contá-las inflava a Cogna de 1.703 para 1.986 municípios e fazia a sobreposição
competitiva tratar praça vazia como disputa. **Ao contar municípios, filtre `mat > 0`.** O
bug só apareceu porque o mapa filtrava e a tabela ao lado não — dois números discordando na
mesma tela.

**6. Mais detalhe no regulatório = mais `pontos`, nunca mais prosa.** O usuário pediu mais
detalhe de volta depois de ter cortado a prosa em três rodadas. A solução foi o campo
`pontos`: itens curtos, cada um com a etiqueta do ato. O gate exige `texto`, `doc` e `url`
em cada um — dar mais detalhe não pode virar porta para afirmação sem lastro.

---

## O que ficou aberto

| Item | Situação |
|---|---|
| **Curadoria dos 176 candidatos do DOU** | O coletor está pronto e rodado; `outputs/dou_candidatos.md` é a lista. **Nada foi escrito em `config/regulatorio.json`** — decidir o que é relevante é trabalho humano, e é o que falta |
| **Os 88 candidatos da SERES** | Merecem desconfiança: o corte de "ato em lote" só enxerga os 600 caracteres de ementa que a busca devolve. Assuma que portaria da SERES é ato individual até o texto provar o contrário |
| **Abas de Excel que sumiram** | Com as seções removidas de Key Players foram junto "Todos os grupos econômicos" e "Movimento de market share"; com o bloco Rankings, "Todas as IES", "Todos os municípios" e "Crescimento por curso". Se fizerem falta, o caminho é registrá-las em outro bloco |
| **Mensalidades** | **Congelado por decisão do usuário** — não reabra. Ver a seção própria no `00_HANDOFF.md` |

---

## Ordem sugerida para a próxima

1. **Curar o `outputs/dou_candidatos.md`** com o usuário ao lado, começando pelos 50 do
   Gabinete do Ministro, que é onde está a norma de alcance setorial.
2. **Etapa 8**, que segue sendo o próximo passo de produto: Investor Snapshot, Key Insights,
   IES individual e Campus Explorer.
3. **Methodology & Data Notes** — continua sendo o que falta para a ferramenta poder ser
   entregue a investidor.
