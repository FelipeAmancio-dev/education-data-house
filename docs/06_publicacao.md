# Publicar o dashboard e automatizar a coleta de preços

Como deixar o dashboard acessível por um link e os preços se atualizando sozinhos, com o
notebook desligado.

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

`js/precos.js` já reconsulta `data/precos.json` em intervalo e redesenha quando o carimbo
muda. Então basta alguém atualizar aquele arquivo no servidor: a página servida pega
sozinha. É por isso que o `publicar.yml` serve a pasta `dashboard/` **como ela é**, e não o
`dashboard_standalone.html` — o arquivo único embute os dados e precisaria de rebuild a
cada coleta.

---

## Os dois workflows

| Arquivo | O que faz | Quando roda |
|---|---|---|
| `.github/workflows/precos.yml` | roda `06_fetch_precos.py` e commita `precos.json` | de 15 em 15 min, 13h–21h UTC, dias úteis |
| `.github/workflows/publicar.yml` | publica a pasta `dashboard/` no Pages | a cada push que mexa em `dashboard/` |

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

## ⚠️ Antes de ligar o Pages: o site fica público

No GitHub, site do Pages é **público** — inclusive a partir de repositório privado, exceto
em plano Enterprise. Ligar o `publicar.yml` deixa o dashboard e os e-mails do time no
cabeçalho acessíveis a quem tiver a URL.

Os **dados** são públicos (Censo, DOU, e-MEC), mas o **produto** é trabalho interno. Se
isso não puder ser exposto, não ligue o workflow: a pasta `dashboard/` é estática e roda em
qualquer servidor de arquivos, então o mesmo resultado sai num host do banco. O
`precos.yml` continua útil de todo jeito — ver a última seção.

---

## Passo a passo

O projeto ainda não é um repositório git.

```bash
cd C:\education
git init -b main
git add .
git commit -m "Dashboard do setor de ensino superior"
```

⚠️ **Confira o `.gitignore` antes do `git add`.** `data_raw/` tem **1,1 GB** de zips do
Censo; sem a exclusão, o push estoura o limite do GitHub e o que passar fica no histórico
para sempre. Com o `.gitignore` do projeto, entram **17,7 MB** e nenhum arquivo passa de
1 MB. Para conferir antes de commitar:

```bash
git count-objects -vH
```

Depois, crie o repositório no GitHub e conecte:

```bash
git remote add origin https://github.com/<usuario>/<repo>.git
git push -u origin main
```

Por fim, no site do GitHub:

1. **Settings → Actions → General → Workflow permissions**: marque *Read and write
   permissions*. Sem isso o `precos.yml` não consegue commitar de volta.
2. **Settings → Pages → Source**: escolha *GitHub Actions*. (Só se você decidiu publicar.)
3. **Actions → Preços do setor → Run workflow**: rode uma vez na mão para confirmar que o
   Yahoo responde a partir do GitHub antes de confiar no cron.

---

## Custo de minutos

Repositório **público** tem minutos ilimitados. **Privado** no plano free tem 2.000
min/mês.

De 15 em 15 minutos no pregão dá ~670 rodadas/mês. A ~1–2 min cada, são **700 a 1.300
minutos** — cabe, mas sem folga grande. Se apertar, troque o cron para `*/30`, que corta
pela metade.

Vale saber que o cron do GitHub **não é pontual**: em horário de pico ele atrasa, às vezes
bastante. Para preço de fechamento isso é irrelevante; para intraday, o carimbo na tela
mostra a hora real da coleta.

---

## Se você não for publicar no Pages

O `precos.yml` sozinho já entrega algo que hoje não existe: **a série de preços continua
crescendo com o notebook desligado**. Hoje ela só avança nos dias em que você abre o
dashboard, e fica cheia de buraco. Com o workflow ligado num repositório privado, é só dar
`git pull` antes de abrir o dashboard local e a série está completa — sem nada exposto.
