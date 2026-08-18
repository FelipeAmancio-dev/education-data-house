# Publicação e coleta automática — JÁ ESTÁ NO AR

> **Repositório:** https://github.com/FelipeAmancio-dev/education-data-house (público)
> **Site:** https://felipeamancio-dev.github.io/education-data-house/
>
> Ligado e funcionando desde 17/08/2026. Este documento explica como funciona e onde
> mexer — não é mais um passo a passo de instalação.

---

## O problema, em uma frase

O `run_dashboard.py` recoleta preço a cada 5 minutos, mas só enquanto está aberto na sua
máquina. E o **artifact publicado não resolve isso**: ele é um retrato do momento da
publicação e não tem como buscar dado novo — as únicas capacidades que uma página
publicada recebe são `downloads` e `mcp`, nenhuma delas dá acesso de rede, e a CSP bloqueia
host externo. Não é limitação de frequência, é de arquitetura.

Quem resolve é o GitHub: **Actions** coleta, **Pages** serve.

---

## Por que isso funciona sem mudar código

`js/precos.js` reconsulta `data/precos.json` a cada 5 minutos e redesenha quando o carimbo
muda — o laço foi restaurado justamente para acompanhar este workflow. Então basta alguém atualizar aquele arquivo no servidor: a página servida pega
sozinha. É por isso que o `publicar.yml` serve a pasta `dashboard/` **como ela é**, e não o
`dashboard_standalone.html` — o arquivo único embute os dados e precisaria de rebuild a
cada coleta.

---

## Os dois workflows

| Arquivo | O que faz | Quando roda |
|---|---|---|
| `.github/workflows/precos.yml` | roda `06_fetch_precos.py` e commita `precos.json` | **de 5 em 5 min**, 13h–21h UTC (pregão), dias úteis |
| `.github/workflows/dou_diario.yml` | roda `11_fetch_dou_diario.py` e commita o feed | **10h UTC = 7h BRT**, dias úteis |
| `.github/workflows/publicar.yml` | publica a pasta `dashboard/` no Pages | após qualquer um dos dois acima, e a cada push em `dashboard/` |

⚠️ **A corrente entre eles depende de um detalhe que quebra em silêncio.** Push feito com
o `GITHUB_TOKEN` **não dispara outros workflows** — é proteção do GitHub contra laço
infinito. Sem tratamento, os dois coletores atualizariam os dados e a página publicada
nunca seria reconstruída: o site congelado enquanto o repositório avança, que é o pior
caso, porque parece que está funcionando. Por isso o `publicar.yml` escuta `workflow_run`,
que reage à **conclusão** do workflow e não ao push que ele fez — e faz `checkout` com
`ref: main`, porque `workflow_run` roda no commit ANTERIOR por padrão e publicaria os
dados de antes da coleta.

O `06_fetch_precos.py` usa **só biblioteca padrão** do Python — não há `pip install`, e a
rodada leva ~30 s.

⚠️ **O horário é UTC.** O Brasil não tem horário de verão desde 2019, então BRT = UTC−3 o
ano todo, e o pregão (10h–18h) é 13h–21h UTC.

⚠️ **O `precos.yml` tem um passo de conferência, e ele é o ponto do arquivo.** O coletor
devolve código 0 mesmo com falha **parcial** — só sai com 1 quando *nenhuma* série vem. Num
CI isso commitaria um arquivo degradado em silêncio, e o Yahoo costuma limitar IP de nuvem,
que é exatamente o cenário de degradação parcial. O passo quebra a rodada se faltar série
de qualquer papel. Falha só do valor de mercado é tolerada de propósito: sem ele o basket
cai para peso igual, o que a própria tela explica.

---

## O site é público — decisão tomada

O repositório e o Pages são **públicos**, por decisão do usuário em 17/08/2026: "estou
trabalhando apenas com dados públicos". Censo, DOU e e-MEC são de fato públicos.

⚠️ O que também ficou público, e não é dado: os **e-mails dos três integrantes do time** no
cabeçalho. Foi levantado três vezes antes do push e o usuário confirmou que está tranquilo.
Registrado aqui para que ninguém descubra por acidente. Se um dia for preciso remover, o
site para de exibi-los na hora, mas o histórico do git guarda.

---

## Configuração — já feita, registrada para referência

No site do GitHub, três coisas foram ligadas e **sem elas nada funciona**:

1. **Settings → Actions → General → Workflow permissions** = *Read and write permissions*.
   Sem isso os coletores rodam e não conseguem commitar.
2. **Settings → Pages → Source** = *GitHub Actions*.
3. Primeiro `Run workflow` na mão, para confirmar que o Yahoo responde a partir do GitHub.

⚠️ O `.gitignore` mantém `data_raw/` fora do repositório — são **1,1 GB** de zips do Censo
que estourariam o limite do GitHub e ficariam no histórico para sempre. **Não o remova.**
O repositório tem 17,7 MB.

---

## Custo de minutos

Repositório **público** tem minutos ilimitados. **Privado** no plano free tem 2.000
min/mês.

De 5 em 5 minutos no pregão dá ~96 execuções/dia, ~2.000/mês. Isso **estoura os 2.000
minutos gratuitos de um repositório privado** — e é por isso que o cron de 5 minutos só faz
sentido em repositório **público**, onde os minutos são ilimitados.

O feed do DOU é uma execução por dia útil (~21/mês), mas cada uma instala o Chrome e leva
uns 4 minutos. Irrelevante no público; some ~85 min/mês no privado.

⚠️ **5 minutos é o mínimo que o GitHub aceita** — cron mais curto é recusado.

⚠️ **MEDIDO NA PRÁTICA, e a diferença é grande.** O cron de `*/5` NÃO entrega uma execução
a cada 5 minutos. Nas primeiras 2,5 horas de janela após ligar, saíram **3 execuções**, não
as ~30 que o cron pediria — e uma delas às 22:47 UTC, fora da janela 13–21, ou seja,
atrasada em quase uma hora.

O GitHub **pula execuções agendadas** quando a fila está carregada, e agendamento curto é
o primeiro a ser descartado. Isso é da plataforma, não da nossa configuração. Consequência
prática: **trate o feed de preços como "algumas vezes por hora", não como intraday.** A
tela carimba a hora real da coleta, então dá para ver o atraso. Se a cadência importar de
verdade, o caminho não é apertar o cron — é um runner próprio ou outro agendador.

---

## Se você não for publicar no Pages

O `precos.yml` sozinho já entrega algo que hoje não existe: **a série de preços continua
crescendo com o notebook desligado**. Hoje ela só avança nos dias em que você abre o
dashboard, e fica cheia de buraco. Com o workflow ligado num repositório privado, é só dar
`git pull` antes de abrir o dashboard local e a série está completa — sem nada exposto.
