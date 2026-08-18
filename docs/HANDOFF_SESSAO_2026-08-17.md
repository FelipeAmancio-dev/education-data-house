# Hand-off da sessão de 17–18/08/2026

> Cole isto na abertura da próxima sessão. O detalhe todo está em `docs/00_HANDOFF.md`,
> que foi atualizado até o último teste.

---

## Abra `docs/00_HANDOFF.md` e nada mais

Ele está em dia. Comece pela seção **"🔗 O projeto está NO AR"**, que é nova e muda como se
trabalha aqui: o dashboard não vive mais só na sua máquina.

| | |
|---|---|
| **Site (atualiza sozinho)** | https://felipeamancio-dev.github.io/education-data-house/ |
| **Repositório** | https://github.com/FelipeAmancio-dev/education-data-house (público) |
| **Artifact** | https://claude.ai/code/artifact/91a062c8-7e5c-49da-b1e2-bb11947af321 |

⚠️ **`git pull` antes de qualquer coisa.** Os workflows commitam sozinhos várias vezes por
dia e o remoto quase sempre está à frente.

---

## O que esta sessão entregou

**O projeto saiu do notebook.** Repositório público, GitHub Pages no ar e três workflows
coletando sozinhos: preços no pregão, feed do DOU às 7h, e publicação automática a cada
coleta. Testado ponta a ponta — há commits do robô no histórico.

**O e-MEC entrou.** `Dados_GEO.xlsx` virou de-para: **2.636 IES casadas, 99,9% das
matrículas de 2024**, validado por UF com **zero divergência**. Trouxe IGC, conceitos e as
sinalizações de restrição (37 IES com FIES suspenso), que o Censo não tem.

**A Geografia foi reconstruída** em cima disso e do `ies_mun`: capilaridade por grupo,
pegada física × digital, sobreposição competitiva e qualidade. A Cogna alcança **1.703
municípios com apenas 132 de presencial** — 92% do alcance sem estrutura física.

**O Regulatório ganhou o feed diário do DOU**, com triagem de relevância para equity, e
virou a aba de entrada.

---

## Seis coisas fáceis de estragar sem perceber

**1. `precos.json` pode chegar corrompido na área de trabalho.** Achado em 18/08: 1 KB, zero
séries, de uma coleta que falhou por falta de rede. Os commits estavam íntegros. **Confira
≈234 KB antes de commitar** — um arquivo vazio publicado deixa o Price Action em branco.
Restaure com `git checkout origin/main -- dashboard/data/precos.json`.

**2. O cron do GitHub pula execuções.** `*/5` entregou **3 rodadas em 2,5 h**, não ~30, e
uma quase uma hora atrasada. É da plataforma. Trate o preço como "algumas vezes por hora".

**3. Push com `GITHUB_TOKEN` não dispara outro workflow.** É por isso que `publicar.yml`
escuta `workflow_run` e não só `push`. Se alguém "simplificar" isso, o site congela enquanto
o repositório avança — e parece que está funcionando.

**4. `registrarCSV()` substitui por nome, e precisa continuar assim.** Todo bloco com
controle próprio se redesenha chamando a própria view, sem passar pelo `render()` que limpa
o registro. Sem a substituição, cada clique acrescenta uma cópia de cada aba: o Excel do
Price Action saía com **20 abas e 15 MB** em vez de 4 e 3.

**5. Presença = ter aluno, não ter linha.** `ies_mun` tem **1.044 linhas com `qt_mat = 0`**.
Contá-las inflava a Cogna de 1.703 para 1.986 municípios e fazia a sobreposição competitiva
tratar praça vazia como disputa.

**6. Índice não se rebalanceia porque uma bolsa fechou.** O basket é **encadeado**: o retorno
do dia sai só dos papéis com preço nos dois dias. Antes, a AFYA sumindo em feriado americano
derrubava a cesta 22% e ela recuperava tudo no dia seguinte.

---

## O que ficou aberto

| Item | Situação |
|---|---|
| **Etapa 11** | Investor Snapshot, Key Insights, IES individual, Campus Explorer — é o próximo passo de produto |
| **Methodology & Data Notes** | continua sendo o que falta para a ferramenta poder ser entregue a investidor |
| **176 candidatos do DOU** | `outputs/dou_candidatos.md` espera curadoria. Comece pelos 50 do Gabinete do Ministro |
| **"Baixar Excel" no artifact** | inerte lá; resolvível com a capability `downloads`, não implementado. No site e no local funciona |
| **Mensalidades** | **congelado por decisão** — não reabra |

---

## Ordem sugerida para a próxima

1. **Deixe a automação rodar um ciclo completo** e confira o site num dia útil de manhã —
   é o teste real do feed das 7h.
2. **Etapa 11**, começando pelo Investor Snapshot.
3. **Methodology**, sem a qual a ferramenta não deveria ser distribuída.
