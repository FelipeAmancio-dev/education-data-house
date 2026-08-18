# Hand-off — leia isto primeiro

> Documento de transferência de sessão. Escrito para que outra sessão continue o projeto
> sem redescobrir o que já foi apurado e **sem repetir os erros que já foram corrigidos**.
> Última atualização: 18/08/2026.

---

## 1. O que é o projeto

Dashboard de análise do setor de ensino superior brasileiro, montado sobre os **Microdados do
Censo da Educação Superior (INEP)**, orientado a *equity research*: market share, concentração,
mix, crescimento e posicionamento competitivo dos grupos educacionais.

Roda **localmente**, sem build step. Diretório do projeto: `C:\education`.

**Regra editorial que atravessa tudo:** antes de adicionar qualquer gráfico, a pergunta é
"que dúvida de investidor isso responde?". Se não houver utilidade analítica clara, não entra.

---

## 2. Estado atual

| Etapa | Escopo | Estado |
|---|---|---|
| 1 | Exploração, data dictionary, qualidade, arquitetura, mapeamento de grupos | ✅ |
| 2 | Pipeline de ingestão + cubos + validação, série 2015–2024 | ✅ |
| 3 | MVP do dashboard (6 views) + versão de arquivo único | ✅ |
| 4 | Reorganização em **hub + blocos** no padrão do Healthcare Data House | ✅ |
| 5 | **Price Action, bilíngue PT/EN, CSV em tudo, Glossário** | ✅ |
| 6 | **Bloco Mensalidades** + motores Ânima, Estácio, Cogna e Uniasselvi | ✅ |
| 7 | **Módulo Ambiente Regulatório** (EaD & Polos, Medicina, Fies + feed do MEC) | ✅ |
| 8 | **e-MEC ingerido** + Geografia reconstruída (capilaridade, físico×digital, IGC) | ✅ |
| 9 | **Feed diário do DOU** com triagem de relevância para equity | ✅ |
| 10 | **Publicação no GitHub Pages** + coleta automática por Actions | ✅ |
| 11 | Investor Snapshot, Key Insights, IES individual, Campus Explorer | ⬜ **próximo** |

## 🔗 O projeto está NO AR

| | |
|---|---|
| **Site (atualiza sozinho)** | https://felipeamancio-dev.github.io/education-data-house/ |
| **Repositório** | https://github.com/FelipeAmancio-dev/education-data-house (público) |
| **Artifact** | https://claude.ai/code/artifact/91a062c8-7e5c-49da-b1e2-bb11947af321 |

⚠️ **O site e o artifact NÃO são a mesma coisa.** O Pages se reconstrói a cada coleta; o
artifact é um retrato congelado e só muda quando alguém republica. Para o dia a dia, use o
Pages. Detalhe em `docs/06_publicacao.md`.

⚠️ **Antes de mexer, `git pull`.** Os workflows commitam sozinhos e o remoto costuma estar
à frente. Ver §"Coleta automática" para as armadilhas.

```bash
python run_dashboard.py            # abre o dashboard (versão completa)
python scripts/06_fetch_precos.py  # atualiza os preços das ações do setor
python scripts/07_fetch_mensalidades.py             # coleta as mensalidades
python scripts/07_fetch_mensalidades.py --ies Estácio  # só a Estácio: sem navegador, ~4 min
python scripts/08_build_regulatorio.py              # valida e publica a base regulatória
python scripts/08_build_regulatorio.py --so-verificar   # só valida, não escreve
python scripts/09_fetch_dou.py                      # varre o DOU e lista candidatos p/ curadoria
python scripts/10_ingest_emec.py                    # Dados_GEO.xlsx (e-MEC) → de-para + emec.json
python scripts/11_fetch_dou_diario.py               # feed diário do DOU, triado por relevância
```

Reconstrução completa a partir dos zips:

```bash
python scripts/01_ingest.py        # zips → Parquet limpo (10 anos, 40 MB)
python scripts/02_build_cubes.py   # Parquet → dimensões + cubos (6,4 MB)
python scripts/03_validate.py      # gate de consistência (sai 1 se falhar)
python scripts/04_export_web.py    # cubos → JSON do dashboard (3 MB iniciais)
python scripts/05_build_standalone.py           # arquivo único offline
python scripts/05_build_standalone.py --artifact # fragmento p/ publicar
```

Scripts auxiliares (rodam sob demanda, não fazem parte do build):

```bash
python scripts/build_ies_group_map.py   # regenera o mapeamento de grupos
python scripts/audit_grupos.py          # procura IES que ficaram fora dos grupos
python scripts/valida_reconciliacao.py  # Censo vs. releases das companhias
python scripts/00_fetch_geo.py          # centroides IBGE (já rodou; não precisa repetir)
```

Artifact publicado: https://claude.ai/code/artifact/91a062c8-7e5c-49da-b1e2-bb11947af321
(republicar com o mesmo `file_path` mantém a URL).

---

## 3. ⚠️ As cinco coisas que você precisa saber antes de tocar em qualquer número

### 3.1 `TP_DIMENSAO` — errar aqui duplica 5,2 milhões de alunos

O campo define **quais métricas podem ser somadas em cada linha**. Não é opcional.

| Dim | O que é | Métricas válidas |
|---|---|---|
| 1 | Presencial no Brasil | **todas** |
| 2 | EAD no Brasil | **só** matrículas, ingressantes, concluintes, trancados |
| 3 | EAD nível Brasil | **só** nº de cursos, vagas, inscritos |
| 4 | EAD no exterior | alunos, sem geografia |

```
Alunos          → TP_DIMENSAO IN (1,2,4)
Cursos e vagas  → TP_DIMENSAO IN (1,3)
Geografia       → TP_DIMENSAO IN (1,2)
```

Codificado em `scripts/lib/censo.py` (`DIM_ALUNOS`, `DIM_OFERTA`, `DIM_GEO`). **Use as
constantes, nunca escreva o filtro à mão.**

### 3.2 `QT_MAT` não é "base de alunos" — e a diferença muda o ranking

`QT_MAT` = alunos "Cursando e/ou Formado". **Exclui matrícula trancada.** As companhias
divulgam base que inclui trancados. A taxa de trancamento varia de **0,7% (Vitru) a 87,6%
(UNINTER)**, então as duas definições produzem **rankings diferentes**:

- Por `QT_MAT`: Vitru é a 2ª maior (10,56%), YDUQS a 3ª (8,06%)
- Por base de alunos: **YDUQS é a 2ª (10,57%)**, Vitru cai para 3ª (9,04%)

⚠️ **Corrigido em 12/08/2026:** este documento concluía que a *base* era a definição que
reconcilia com o release. Estava comparando com o número-manchete, que inclui pós, técnico e
preparatório. Refeita a conta só com graduação, **é `QT_MAT` que reconcilia** — ver
`docs/04_reconciliacao_companhias.md`, seção de correção.

### 3.3 Reclassificação de trancados contamina o crescimento de anos específicos

Quando `QT_MAT` e a base de alunos crescem em direções diferentes, o movimento é
**reclassificação de vínculo**, não aluno entrando ou saindo:

| Grupo | Ano | YoY `QT_MAT` | YoY base | Divergência |
|---|---:|---:|---:|---:|
| Ser Educacional | 2022 | +0,4% | **−18,0%** | **+18,4 p.p.** |
| Ânima | 2023 | +1,5% | **−12,7%** | **+14,2 p.p.** |

E o caso inverso: **YDUQS 2021–2022**, com `QT_MAT` parado enquanto a base crescia 12–16%.

O check é permanente (`03_validate.py` §5b). **Não gere insight de crescimento nesses anos sem
mostrar as duas séries.**

### 3.3b ⚠️ A UF de uma IES é o endereço da SEDE — e no EAD isso não é onde o aluno está

Confirmado com número em 14/08/2026, a partir de uma dúvida do usuário sobre o Glossário:

| Grupo | IES | UF | Presencial | EAD | % do grupo |
|---|---|---|---:|---:|---:|
| Cogna | Univ. Pitágoras Unopar Anhanguera (298) | PR | 6.756 | **836.889** | **75,0%** |
| Vitru | C. Univ. Leonardo da Vinci — UNIASSELVI (1472) | SC | 336 | **579.750** | 53,7% |
| Vitru | Universidade Cesumar — UNICESUMAR (1196) | PR | 9.216 | **477.003** | 45,0% |

**Não é erro de mapeamento.** É o Censo lançando a matrícula de EAD na IES sede, não no polo.
A Unopar tem polo no país inteiro e aparece 100% no Paraná.

Consequências práticas, todas já tratadas:

- O **Glossário** avisa na tela quando isso acontece (`#gl-comp-ead` em `views.js`). A regra é
  por dado — IES com ≥40% da base do grupo e ≥80% de EAD —, **não por lista de grupos**: vale
  para qualquer grupo que venha a ter o mesmo desenho. Hoje dispara em Cogna, Vitru e YDUQS, e
  fica calada na Afya, que é presencial.
- O **Overview** usa a UF da sede nos gráficos de curso e área (é o que `passaIES` faz em todo
  o dashboard), enquanto "Matrículas por UF" ao lado usa a geografia de verdade do Censo
  (`c_mun_mod`, dims 1 e 2). **São duas definições de UF na mesma tela**, e as duas notas
  dizem isso.
- Para saber onde os alunos realmente estão, o caminho é o bloco **Geografia**, que distribui
  por município de oferta.

### 3.3c ⚠️ `ies_mun` tem linhas com ZERO aluno — presença ≠ ter linha no cubo

**1.044 das 27.985 linhas de `2024_ies_mun.json` têm `qt_mat = 0`**: município onde a IES
tem oferta registrada e nenhum aluno matriculado.

Contá-las como presença inflava a Cogna de **1.703 para 1.986 municípios** e, pior, fazia a
sobreposição competitiva da Geografia tratar praça vazia como disputa. O bug apareceu porque
o mapa filtrava (`v <= 0`) e a tabela ao lado não — os dois números não batiam na mesma tela.

**Ao contar municípios, filtre `mat > 0` sempre.** Vale para capilaridade, exclusividade e
qualquer contagem de "onde o grupo está".

### 3.4 Não existe identificador de campus. Em nenhum ano.

"Nº de campi" é sempre **proxy = pares distintos (CO_IES, CO_MUNICIPIO) na dimensão 1**.
Grupos com vários campi na mesma cidade são subcontados.

Já investiguei e descartei o `CO_LOCAL_OFERTA` que aparece na tabela IES de 2021: são 2.574
linhas para 2.574 IES, ou seja, só a sede. **Não reabra essa investigação.**

⚠️ **O e-MEC foi obtido em 14/08/2026 e NÃO resolve isto.** O usuário baixou manualmente o
Relatório da Consulta Avançada (`Dados_GEO.xlsx`, 3.267 linhas), mas o que ele traz é o
endereço da **SEDE** — um ponto por IES, não os locais de oferta. Geocodificar colocaria a
Cogna inteira num pin. **Não gaste tempo tentando extrair campus daí.**

Para capilaridade, o que o projeto já tem é melhor e não precisa de geocodificação:
`<ano>_ies_mun.json` (IES × município de **oferta**) com `dim.mun` carregando lat/lon de
3.741 dos 3.742 municípios. É o que alimenta os mapas da Geografia. Ver §6.4 para o que o
e-MEC agrega de fato.

### 3.5 Grupo econômico é **pro-forma** e é atributo de IES

O perímetro atual dos grupos vale para toda a série 2015–2024. Uma IES adquirida em 2022 conta
no grupo comprador desde 2015. É o que permite ler evolução de share sem degraus artificiais de
M&A — mas **estes números não são o que cada empresa reportava à época**.

Como grupo é atributo de IES, os cubos são publicados **no nível de IES** e o rollup para grupo
acontece no navegador. Consequência prática: **editar o mapeamento não exige reprocessar os
microdados**, só rodar `build_ies_group_map.py` + `04_export_web.py`.

---

## 4. Números de referência (gabarito de validação)

Qualquer agregação tem que reproduzir isto para 2024:

| KPI | Valor |
|---|---|
| Matrículas | **10.227.266** |
| Ingressantes | 5.010.613 |
| Concluintes | 1.333.988 |
| Cursos | 45.776 |
| IES | 2.561 |
| Presencial / EAD | 5.037.875 (49,3%) / 5.189.391 (**50,7%**) |
| Privada | 8.162.199 (79,8%) |
| Fora do recorte geográfico | 2.580 (exterior/N.I.) |

Série: 2015 tinha 8,03 M com 17,3% EAD. **O presencial encolheu 24% em termos absolutos** na
década; todo o crescimento do setor foi EAD.

Cobertura do mapeamento: **60,5% do mercado, 75,7% da rede privada**, em 43 grupos.

---

## 5. Os arquivos que o usuário edita

Todo o resto é gerado. **Nunca edite `config/ies_grupo_map.csv` à mão** — ele é saída.

| Arquivo | Papel |
|---|---|
| `Suporte IES.xlsx` | **Fonte primária.** Uma aba por empresa, schemas heterogêneos |
| `config/suporte_abas.csv` | Aba → nome canônico do grupo |
| `config/grupos_mantenedoras.csv` | Regras por `CO_MANTENEDORA` (grupos adicionais) |
| `config/ies_grupo_overrides.csv` | Exceções por `CO_IES` + pendências comentadas |
| `config/grupos.csv` | Nome, tipo, ticker, **cor**, ordem |
| `config/grupos_consolidacao.csv` | M&A entre grupos (FMU → Ânima, desativada) |
| `config/grupos_marcas.json` | Tokens de marca p/ auditoria + falsos positivos verificados |
| `config/reportado_companhias.csv` | Números de release para reconciliação |
| `config/mensalidades_ies.csv` | Faculdade → motor de coleta + URL + liga/desliga |
| `config/mensalidades_cursos.csv` | Cursos alvo por modalidade + sinônimos por site |
| `config/regulatorio.json` | **Base do Ambiente Regulatório** — temas, esquemas e decisões |
| `Dados_GEO.xlsx` | **Relatório do e-MEC**, baixado à mão. IGC, conceitos e sinalizações vigentes |

**Cadeia de precedência:**
`overrides > Suporte IES.xlsx > grupos_mantenedoras.csv > mantenedora derivada`

### O leitor do Excel é tolerante de propósito

Cada aba pode ter o schema que quiser — o parser detecta a coluna de código e a de nome. Ele
também **distingue código de IES de código de mantenedora** comparando o nome escrito com o
nome da IES e o da mantenedora no Censo. Isso não é enfeite: a aba Cruzeiro do Sul tinha dois
blocos misturados e dois códigos de mantenedora colidiam com IES reais e não relacionadas
(159 = Faculdade Nova Roma Caruaru, 521 = Universidade de Mogi das Cruzes), inflando o grupo em
14,4 mil alunos. Ver `scripts/lib/suporte.py::classifica_codigos`.

---

## 6. Pendências abertas

### 6.1 Confirmações de mapeamento (comentadas em `ies_grupo_overrides.csv`)

| CO_IES | IES | Grupo? | Alunos |
|---|---|---|---:|
| 1131 | Centro Univ. Santo Agostinho (UniFSA Teresina) | Afya? | 4.727 |
| 3839 | Faculdade IPEMED | Afya? | 40 |

Descomentar a linha aplica. A marca bate, a mantenedora não — por isso ficou pendente.

### 6.2 Afya merece uma revisão

O presencial reconcilia bem com o release (−8,6%), mas o Censo atribui **23.194 matrículas EAD**
às 35 IES do grupo, que a Afya não menciona. Ou é EAD residual de IES adquiridas, ou alguma IES
não deveria estar em Afya. Não resolvido.

### 6.3 Cogna — release de 4T24 não obtido

Foi a única das 7 abertas que não consegui reconciliar. As buscas retornam sempre o 4T25 e o
domínio `esg.cogna.com.br` bloqueia acesso automatizado (403). **Se o usuário fornecer o PDF,
extrair e rodar `valida_reconciliacao.py`.**

### 6.4 ✅ e-MEC — RESOLVIDO em 14/08/2026, mas não do jeito esperado

O usuário obteve o **Relatório da Consulta Avançada do e-MEC** e deixou em `Dados_GEO.xlsx`
(3.267 linhas, processado em 11/08/2026). `scripts/10_ingest_emec.py` faz o de-para.

**Cobertura: 2.636 IES casam por `CO_IES` — 99,9% das matrículas de 2024.** As 764 que só
existem no Censo são históricas/extintas; o e-MEC lista apenas IES ativa. A maior sem par tem
2.048 alunos, então a contagem de IES engana e a de matrículas é a que importa.

⚠️ **Ele NÃO destrava campus e polo** — ver o ⚠️ do §3.4. O endereço é o da sede.

**O que ele agrega de verdade é qualidade e situação regulatória:**

| Campo | Uso |
|---|---|
| **IGC**, CI, CI-EaD | índices de 1 a 5; alimentam o gráfico de qualidade da Geografia |
| **Sinalizações Vigentes** | 58 IES com suspensão de ingresso/ProUni, 37 com **FIES suspenso**, 24 em procedimento sancionador |
| Tipo de Credenciamento | quem está credenciado para EaD |
| CNPJ e natureza jurídica | conferir o mapeamento de grupos |

⚠️ **IGC vazio é SEM NOTA, não nota zero.** O e-MEC usa `-` e `SC`; virar 0 puniria IES nova
ainda não avaliada. Toda média é sobre "IES com nota", e o número de avaliadas viaja junto.

⚠️ **Na tela, só as sinalizações RESTRITIVAS entram na tabela.** "Unificação de Mantidas"
(156) e "Credenciamento Prévio" (152) são as duas mais numerosas e não são restrição —
listá-las junto de suspensão de FIES faria o quadro parecer muito pior do que é.

Saídas: `data_processed/emec_ies.csv`, `outputs/emec_depara.md` e `dashboard/data/emec.json`
(payload indexado pela **posição em `dim.ies`**, como os cubos; entra em `CORE` do build).

### 6.5 ✅ O mapa da Geografia não abria fora de um servidor HTTP — CORRIGIDO em 14/08/2026

Fica registrado porque é o arquétipo de um defeito que este projeto produz mais de uma vez.

O usuário relatou que "na maior parte das vezes a Geografia não funciona". Medido: **12 de 12
aberturas OK no servidor local**. O defeito não estava no servidor — `app.js` chamava
`fetch('data/geo/uf.geojson')` **cru**, fora do helper `json()` de `dados.js`, que é justamente
quem consulta `window.__EMBED` antes de ir à rede. O geojson sempre esteve embutido no arquivo
único (245 KB, o build o lista), mas ninguém lia de lá: fora de HTTP o fetch morria,
`window.__ufGeo` ficava indefinido e a view inteira caía com
`Cannot read properties of undefined (reading 'regions')`.

Hoje existe `carregarGeo()` em `dados.js`, no mesmo caminho de código dos demais dados.

⚠️ **A lição, que vale para o próximo:** o defeito só existia no **standalone e no artifact** —
as duas versões que ninguém testa por hábito. É o mesmo motivo pelo qual a colisão de nome de
topo (§9.5) passou despercebida. **Ao mexer em carregamento de dado, teste o arquivo único**,
não só `run_dashboard.py`.

### 6.6 ⚠️ O botão "Baixar Excel" NÃO funciona dentro do artifact publicado

Investigado em 14/08/2026 a partir de outro relato do usuário. **O código está certo**: os 8
blocos geram `.xlsx` válido (conferido abrindo cada arquivo com `openpyxl`), tanto no servidor
local quanto no arquivo único aberto por `file://`.

O que não funciona é o **artifact**: o sandbox do visualizador não concede permissão de download
à página, então `<a download>`, blob e data: URI ficam inertes. O `js/xlsx.js` monta o arquivo
certinho e a entrega é que morre.

⚠️ **Correção de 14/08/2026 — isto TEM conserto, ao contrário do que este documento dizia numa
versão anterior desta mesma seção.** Existe uma capability `downloads` do artifact: declarada na
publicação, o download passa a sair por `window.claude.downloads.save(...)` em vez do link. Não
foi implementado ainda; exige carregar a orientação de capabilities antes de escrever o código,
e o `baixarXLSX()` precisaria de um caminho alternativo quando `window.claude.downloads` existir.

Enquanto não for feito: para baixar os dados use `python run_dashboard.py` ou o
`outputs/dashboard_standalone.html`, onde o botão funciona normalmente.

Destrava campus e polo com lat/long reais. Bloqueado para acesso automatizado. O usuário ficou
de buscar.

---

## 7. Alertas de validação que são esperados (não são bugs)

`03_validate.py` passa com **0 falhas e 6 alertas**. Todos investigados:

1. **2022 — dims 3/4 com `CO_UF` preenchido** (9.590 linhas). Inconsistência do INEP. Sem
   impacto: a geografia usa só dims 1 e 2.
2–4. **Amplitude da taxa de trancamento** de YDUQS (35 p.p.), Ser (27) e Ânima (28).
5–6. **Divergência `QT_MAT` × base** em Ser 2022 e Ânima 2023 (§3.3).

Se aparecer alerta novo, investigar — esses seis são conhecidos.

---

## 8. Peculiaridades de layout por ano (já tratadas)

| Ano | O que muda | Onde está tratado |
|---|---|---|
| 2020 | `CO_CINE_ROTULO` vem como **`CO_CINE_ROTULO2`** | `lib/censo.py::RENOMEAR` |
| 2015–2022 | **`TP_REDE` não existe na tabela IES** | Derivado de `TP_CATEGORIA_ADMINISTRATIVA`. Categorias 1,2,3 e **7** → Pública; 4,5 → Privada. A 7 ("Especial") ser pública é contraintuitivo — validado empiricamente |
| 2023 | Entram `IN_COMUNITARIA`, `IN_CONFESSIONAL` | Fora do núcleo |
| 2024 | `QT_*_RVETNICO` → colunas granulares | Fora do núcleo |

Correção importante: eu havia alertado na Etapa 1 que `TP_DIMENSAO`/`CO_CURSO` "foram criados em
2022" e exigiriam tratamento nos anos antigos. **Estava errado** — o INEP republicou toda a
série no layout unificado. A série é comparável de ponta a ponta.

Outros pontos de limpeza: `CO_CINE_ROTULO` vem com **aspas duplas literais** no CSV;
`CO_CINE_AREA_GERAL` tem **zero à esquerda** e precisa ser VARCHAR; encoding é **latin-1**,
separador `;`.

---

## 9. Arquitetura do dashboard

```
dashboard/
  index.html          hub (home) + markup dos 7 blocos
  css/app.css         paleta Itaú, tokens em :root, cabeçalho escuro, cards do hub
  js/i18n.js          motor PT/EN: TX(), tradução de rótulos de dado, DOM estático
  js/en.js            dicionário inglês (só dados; o motor é o i18n.js)
  js/dados.js         carga + agregação em memória (rollup IES → grupo/UF/região)
  js/ui.js            KPI, tabela ordenável, `opcoes()`, registro/geração de CSV
  js/views.js         overview, courses, geography, rankings
  js/grupos.js        bloco Key Players (era comparacao.js + groups())
  js/precos.js        bloco Price Action (série de preços, janelas, basket)
  js/mensalidades.js  bloco Mensalidades (preço de tabela por IES, curso e praça)
  js/app.js           hub, roteamento por hash, filtros por bloco, idioma, menu de CSV
  data/               JSON colunar gerado (não editar) + precos.json
  vendor/echarts.min.js
```

### Hub e blocos (Etapa 4)

Mesma linguagem visual do **Healthcare Data House**: cabeçalho escuro com filete laranja, marca
"Education **Data House**" à esquerda e os contatos do time à direita, presentes em todas as telas.
A home é uma grade de cards, um por bloco.

⚠️ **A ordem dos blocos foi definida pelo usuário em 14/08/2026 e é esta.** Ela vale no
`<nav>` e na grade de cards da home, que são duas listas separadas — mexeu numa, mexa na outra.

| Rota | Bloco | O que responde |
|---|---|---|
| `#/` | Home | **só a porta de entrada**: a grade de cards. Sem KPI e sem filtro, por pedido do usuário |
| `#/overview` | Overview | tamanho e trajetória do setor, por UF e por curso — **sem filtro de grupo** |
| `#/grupos` | Key Players | seleção livre (chips) → comparativo, composição da base e mix de modalidade. **As três camadas seguem os chips** |
| `#/cursos` | Cursos | ranking CINE com o **maior grupo de cada curso**, concorrência no curso escolhido com seleção de grupos e pizza de share |
| `#/geografia` | Geografia | **capilaridade**: um mapa por grupo na mesma escala, pegada física × digital, sobreposição competitiva e qualidade (IGC do e-MEC) — mais a liderança por praça |
| `#/mensalidades` | Mensalidades | **quanto cada player consegue cobrar**: mensalidade mediana por IES, matriz curso × IES com o *spread*, e a faixa da unidade mais barata à mais cara |
| `#/regulatorio` | Ambiente Regulatório | **o que está valendo em EaD & Polos, Medicina e Fies**, com "como era → o que mudou → hoje", timeline de marcos e o feed das decisões do MEC com fonte oficial |
| `#/precos` | Price Action | **fechamento diário**: preço dia a dia, retorno por janela (WTD/MTD/YTD/desde-data), comparação entre papéis e basket vs IBOV/SMLL |
| `#/glossario` | Glossário | **as IES somadas em cada player** (composição por grupo) + definição de cada termo e por que o dado diverge do release |

❌ **O bloco Rankings foi REMOVIDO em 14/08/2026, a pedido do usuário.** Saíram com ele o
ranking das 25 maiores IES, "cursos que mais crescem" e os 20 maiores municípios, além das
abas de Excel correspondentes. Não o recrie: se algum desses rankings voltar a ser pedido,
ele deve entrar em outro bloco, não num bloco próprio. (Os "rankings" que o usuário mandou
**manter** são os de dentro do bloco Cursos — grupos e IES no curso selecionado —, que são
outra coisa.)

Continua sendo **um único HTML** — é o que mantém viável a versão standalone/artifact. O hash é a
fonte da verdade quando funciona, mas a navegação não depende dele (dentro de um artifact a barra
de endereço pode não acompanhar): os cliques chamam `irPara()` direto.

### O que mudou na rodada de 14/08/2026 (pedidos do usuário)

Uma lista longa de ajustes. O que é fácil desfazer sem perceber:

- **Cabeçalho:** saiu a marca "Itaú BBA" e o símbolo laranja; sobraram só os contatos do
  time, agora **sem WhatsApp** e com o ícone de e-mail em `mailto:`.
- **Key Players** perdeu 12 KPIs e duas seções inteiras — ver o cabeçalho de `grupos.js`,
  que lista o que saiu e por quê. **As três camadas passaram a seguir os chips**; não há
  mais nenhuma peça fixa nas 7 abertas.
- **Cursos** ganhou seleção de grupos própria (`selCursos`, padrão = abertas), a coluna
  *Maior grupo* na tabela de mercado e a pizza de share dentro do curso.
- **Rede saiu dos filtros de Key Players e de Cursos** (`FILTROS` em `app.js`): a disputa
  nesses dois blocos é entre grupos econômicos, que são privados por definição.
- **Mensalidades** perdeu os 4 KPIs do topo. O carimbo com data da coleta e total de
  preços continua na barra de filtros — era o único dado que só existia nos KPIs.
- **Regulatório** perdeu o filtro de Órgão e ganhou o bloco `pontos` por tema (ver adiante).

⚠️ **Duas peças mudaram de bloco em 13/08/2026, a pedido do usuário — não as devolva:**

- **Ganho e perda de market share** saiu de Rankings e foi para **Key Players**: é leitura
  competitiva. Reaproveita `g`, `gp`, `tot` e `totP`, que já vêm de `fc` (o filtro **sem** grupo)
  — não é economia de código, é o denominador correto.
- **Composição por grupo (IES somadas)** saiu de Rankings e foi para o **Glossário**: é material
  de referência, a lista que explica divergência contra release. Com isso o Glossário deixou de
  ser estático e virou view renderizada (`glossario()` em `views.js`), com `FILTROS.glossario =
  ['ano']` — a composição é de um ano.

**Filtro escondido não é aplicado.** `FILTROS` em `app.js` declara quais filtros globais cada bloco
usa; ao trocar de bloco os demais são zerados, para o usuário não carregar um recorte invisível.
O filtro global de grupo foi removido: Overview não deve ter (decisão do usuário), Geografia e
Rankings têm seletor próprio dentro do bloco.

### Bilíngue PT/EN

A chave do dicionário **é o texto em português**. Não existe esquema de chaves paralelo, e o que
não estiver traduzido cai de volta no português em vez de mostrar chave crua.

- String dinâmica (JS): `TX('texto', {var})`. Rótulo vindo do dado: `TXcurso`, `TXarea`,
  `TXregiao`, `TXorg` — nome de grupo e sigla de UF **não** se traduzem.
- HTML estático: nada a marcar. `capturarEstaticos()` guarda os nós no boot e
  `aplicarEstaticos()` troca na virada. Elemento que a view reescreve leva `data-din`;
  **esquecer isso faz o título voltar ao placeholder ao trocar de idioma**.
- Texto corrido com `<strong>`/`<em>` no meio vira fragmento inútil — esses vão em
  `data-i18n-bloco="nome"` e o inglês entra inteiro, sob a chave `bloco:nome`.
- Número segue o idioma (`10.227.266` × `10,227,266`), inclusive no CSV: separador `;` e vírgula
  decimal em pt, `,` e ponto em en.

**Para auditar o que falta:** abra em EN, navegue por todos os blocos e rode `__faltando()` no
console. Ele lista exatamente as chaves pedidas e não encontradas.

### Download em Excel

Cada bloco tem um botão que gera **um .xlsx com uma aba por conjunto de dados**. As views
registram os conjuntos ao renderizar (`opt.csv` no `tabela()` ou `registrarCSV()` direto), e o
registro é refeito a cada render — trocar filtro ou idioma muda o que sai.

`js/xlsx.js` escreve o arquivo na mão: um .xlsx é um ZIP de XML, e o ZIP é gravado com método
**STORE** (sem compressão), o que evita implementar DEFLATE e continua sendo ZIP válido. Strings
vão inline (`t="inlineStr"`), dispensando a tabela de shared strings. Testado abrindo o resultado
com `openpyxl`. Nada de CDN: a CSP do artifact bloqueia biblioteca externa.

⚠️ **Registre o conjunto completo, não o recortado.** Use `opt.limite` para cortar a exibição e
passe o array inteiro para o `tabela()`. Já esteve errado: o CSV de "todas as IES" saía com 25
linhas porque a tabela recebia `.slice(0, 25)`.

⚠️ **`registrarCSV()` SUBSTITUI por nome, e isso não é detalhe** (corrigido em 14/08/2026).
`render()` do `app.js` chama `limparCSV()` antes de desenhar — mas só quando a navegação passa
por ele. Todo bloco com controle próprio (chips de período no Price Action, seleção de grupos em
Key Players, curso em Cursos, UF e município em Geografia) se redesenha chamando a **própria
view direto**, sem passar pelo `render()`. Antes da correção, cada clique acrescentava mais uma
cópia de cada aba: o Excel do Price Action saía com **20 abas em vez de 4 e 15 MB em vez de 3**,
e a versão boa era a última — quem abrisse a primeira lia o recorte errado. O bug era **geral**,
não só do Price Action, e passou despercebido porque só aparece depois de mexer nos controles.

### Price Action

`scripts/06_fetch_precos.py` coleta do Yahoo Finance (endpoint público, sem chave) e grava
`dashboard/data/precos.json` (~234 KB): fechamento **ajustado** de 5 anos para os 7 papéis,
IBOV, SMAL11 e USDBRL. `config/tickers.csv` mapeia grupo → papel.

⚠️ **O bloco virou de FECHAMENTO DIÁRIO em 14/08/2026, a pedido do usuário — não tente
ressuscitar o tempo real.** Saíram: a coleta de intraday (era uma chamada extra por papel, 9 a
mais por rodada, e só aumentava o risco de o Yahoo limitar o IP), o chip *Intraday*, a coluna
correspondente na tabela de retornos e o `autoAtualizar()`, que reconsultava o arquivo de 5 em
5 minutos. `serie_intraday()` continua no script caso um dia volte a ser preciso.

Entrou a **tabela de fechamento dia a dia** — uma linha por pregão, papel por coluna, 60 na
tela e a série inteira do período no Excel —, porque **não havia como ler o preço em lugar
nenhum do bloco**: tudo era retorno rebaseado em 100.

Entrou também o campo **"Até"**, ao lado do "Desde": com os dois é possível fechar qualquer
janela (`2024-01-02` → `2024-12-30` dá os 251 pregões de 2024) e baixar exatamente esse
recorte. O `ate` vazio significa "até o último pregão", que é o comportamento de sempre.

⚠️ **O "Até" vale só para o PERÍODO ESCOLHIDO.** As colunas fixas da tabela de retornos
(WTD, MTD, YTD, 12 meses) continuam ancoradas no último fechamento — "WTD até uma data do ano
passado" não seria WTD de nada.

⚠️ Um alternador base 100 ↔ preço chegou a existir no gráfico de linha e **foi removido a
pedido do usuário**: a leitura de preço vive na tabela, e o gráfico é de retorno relativo.

⚠️ **Cada coluna sai na moeda do seu papel** quando "moeda local" está selecionada — a Afya
negocia em USD. Existe `paPreco()` justamente para isso: usar o `brl()` de `dados.js` carimbaria
R$ na Afya, que é erro de leitura e não de formatação.

⚠️ **A coluna de data guarda o ISO e só exibe DD/MM pelo `fmt`.** Guardar o texto brasileiro
ordenaria por dia do mês. E `ordem: '_iso'` é obrigatório: sem ele o `tabela()` cai em
`cols[1]`, que é o primeiro papel — a tabela saía ordenada pelo preço da COGN3, com as datas
embaralhadas. Foi assim que o bug apareceu.

Nota de dado que a tabela nova tornou visível: **COGN3 e YDUQ3 têm 1.246 pontos contra 1.248 do
IBOV** — faltam 2 pregões (10/08 e 31/07/2026) que o Yahoo devolve nulos. É buraco da fonte, a
célula aparece vazia e a nota explica. Antes isso ficava escondido atrás do rebase.

- **A Vitru migrou para a B3**: hoje é `VTRU3`, não mais `VTRU` na Nasdaq. A série no Yahoo
  começa em 11/06/2024 — em janelas anteriores a isso o papel simplesmente não entra, e o basket
  renormaliza os pesos.
- **SMLL não existe no Yahoo**; o proxy é o **SMAL11**, o ETF que replica o índice.
- **Afya negocia em USD.** O padrão converte tudo para BRL pelo câmbio do dia, senão a comparação
  com IBOV mistura retorno de ativo com retorno de câmbio.
⚠️ **O basket é um índice ENCADEADO, e isso conserta dois artefatos reais** (17/08/2026).

A versão anterior calculava `Σ w·(p/base) / Σ w` sobre os papéis presentes **naquele dia**.
Qualquer mudança de composição mexia no denominador e o índice pulava sem que preço nenhum
tivesse mudado:

- **feriado americano**: a AFYA negocia na Nasdaq; em dia sem pregão lá e com pregão na B3
  ela saía da média e a cesta caía **até 22%**, recuperando tudo no dia seguinte. Eram os
  "vales" que o usuário viu no gráfico. Conferido: **todos** os saltos acima de 12%
  coincidiam com a contagem de papéis mudando de 7 para 6;
- **estreia da VTRU3** na B3 em 11/06/2024: entrava com razão 1,0 numa média que estava em
  0,7 e criava um degrau para cima.

Hoje o valor de hoje é o de ontem vezes o retorno do dia, e **o retorno é calculado só
sobre os papéis com preço nos dois dias**. Nunca se comparam conjuntos diferentes. Depois
da correção o maior salto diário caiu de 21,7% para 8,8%, e o dia 28/11/2024 passou de
−21,7% para −4,4%, que é movimento real das brasileiras.

Junto vai um **carrega-último-preço** para dia sem cotação, depois da primeira aparição do
papel — é o que os provedores de índice fazem, e evita que feriado vire evento de preço.

⚠️ **`Math.max(0, idxAte(...))`, e não `>= 0`, na base de cada papel.** Para a janela
`max`, `inicioJanela` devolve limite `'0000-01-01'` e o `idxAte` responde −1 para todos —
resposta correta a "havia preço antes do início?". Uma versão tratava −1 como "fica de
fora" e mandava a cesta inteira embora: **o gráfico do basket ficava vazio só na janela
Máximo**, enquanto o KPI continuava certo, porque vinha do mesmo cálculo antes de quebrar.
Sintoma sutil, fácil de não notar.

- O **basket é ponderado por valor de mercado**: soma de `ações × preço`, rebaseada em 100 — um
  índice de verdade, com peso flutuando junto com o preço. Peso igual fica como alternativa. As
  ações vêm do endpoint `/v7/finance/quote`, que **exige cookie + crumb** (401 sem isso); a
  função `cotacoes()` faz essa dança. Se falhar, o basket cai para peso igual.
- **O calendário é o do IBOV.** Dia sem pregão do índice sai de todas as séries — senão aparece
  um degrau que é buraco de dado, não movimento de preço.
- É um **snapshot do último fechamento**. O `run_dashboard.py` ainda recoleta em segundo
  plano (`--intervalo`, `--sem-precos`), mas a tela não reconsulta mais o arquivo sozinha:
  com fechamento diário, repintar de 5 em 5 minutos não muda nada. Rode o script quando
  quiser avançar a série.

### O módulo Ambiente Regulatório

`js/regulatorio.js` + a seção `#v-regulatorio`. Fonte: `config/regulatorio.json` — **este é o
arquivo que se edita à mão** —, validado e exportado por `scripts/08_build_regulatorio.py` para
`dashboard/data/regulatorio.json`.

⚠️ **A página inteira depende do TEMA escolhido.** Não existe visão "todos": o usuário não quer
os três panoramas de uma vez. As abas **EaD & Polos · Medicina · Fies** ficam no topo, e trocar
de aba troca o resumo *e* o feed. Por isso o tema saiu do dropdown de filtros — lá parecia um
refinamento entre outros, quando é a navegação principal do módulo. `temaSel` começa em `'ead'`.

Ordem: 1. abas de tema; 2. filtros + busca; 3. **resumo do tema em esquema**; 4. **feed
cronológico**; 5. fontes.

⚠️ **O feed mostra só data, tags e o nome do ato.** O resumo saiu da linha e vive no painel de
detalhe. Foram três rodadas de corte de texto até chegar aqui — se for reintroduzir prosa na
linha do feed, saiba que já foi tentado e recusado.

⚠️ **O resumo por tema é visual, não é texto corrido — mas ganhou um bloco de detalhe.**
A primeira versão trazia quatro parágrafos por tema e o usuário cortou: o que ele precisa é
"5 cursos só presenciais", não três linhas explicando isso.

Em 14/08/2026 ele pediu **mais detalhe de volta**. A solução foi o campo `pontos` — não a
volta da prosa. Cada tema tem 4 itens curtos, cada um **com a etiqueta do ato que o sustenta**,
renderizados em lista (`.rg-pontos`), não em parágrafo. `08_build_regulatorio.py` exige `texto`,
`doc` e `url` em cada ponto e derruba o build sem eles: "dar mais detalhe" não pode virar porta
de entrada para afirmação sem lastro. **Se for pedido ainda mais detalhe, acrescente pontos —
não escreva parágrafos.**

Hoje cada tema tem:

- **quatro destaques** com número grande e tom de cor que carrega o sinal — vermelho fecha
  (`Fechado`, `5 cursos só presenciais`), laranja aperta, verde abre (`50% das vagas`);
- os **`pontos`**: 4 frases de detalhe, cada uma com o ato que a sustenta;
- uma **matriz de regra** quando faz sentido (em EaD: curso → formato permitido);
- o quadro **como era → o que mudou → como funciona hoje**, uma frase em cada;
- a **timeline** de marcos, com os títulos clicáveis;
- duas linhas de rodapé: em discussão e próximo prazo.

**Cada peça do esquema leva o link do ato que a instituiu** (`rgFonte()`) — destaque, matriz,
cada etapa do antes/depois e cada marco da timeline. Regra e fonte não podem ficar em lugares
diferentes da tela. Ao acrescentar destaque novo no `config/regulatorio.json`, preencha `doc` e
`url`; sem eles a peça aparece sem etiqueta e perde o que ela tem de mais útil.

⚠️ **Duas regras que sustentam o módulo:**

1. **Regra vigente ≠ discussão.** Todo item carrega `status` (`vigente`, `transicao`,
   `discussao`, `revogada`) e a tela pinta isso com cor e rótulo. Num módulo regulatório,
   confundir consulta pública com regra em vigor é o erro mais caro que a página pode induzir.
2. **Fonte primária sempre, e honestidade sobre a conferência.** Cada decisão tem `fonte_url`
   para o documento oficial. O que ainda **não foi conferido no DOU** vai com
   `confianca: "a_confirmar"` e aparece marcado na tela, com aviso no painel de detalhe e uma
   contagem no topo do módulo. **Não remova a marca sem abrir o documento** — ela existe porque
   o número de uma portaria compilado de notícia não é o mesmo que o número conferido na fonte.

O `08_build_regulatorio.py` é um gate: derruba o build (sai 1) em campo faltando, status ou
relevância fora do domínio, data inválida, tema inexistente, fonte que não é URL ou **ato
duplicado** (mesmo documento e data — o mesmo ato costuma aparecer em mais de uma fonte). E
avisa, sem derrubar, quando a fonte não parece oficial ou quando o item está `a_confirmar`.

### O feed diário do DOU (aba "Últimas publicações")

`scripts/11_fetch_dou_diario.py` → `dashboard/data/dou_diario.json`. É a **aba de entrada**
do módulo, a pedido do usuário: quem abre o bloco quer ver o que saiu, e só depois escolhe
o panorama de um tema.

⚠️ **NÃO use `leiturajornal`**, que é a página que se lê no navegador: ela mostra no máximo
**10 atos por dia**, sem paginação nem carregamento por rolagem. Medido em 17/08/2026: a
página trazia 10 e a busca informava **16 resultados** para o mesmo dia e órgão — um terço
sumia em silêncio. A fonte certa é a busca com `q=` vazio e intervalo de um dia.

⚠️ **A relevância é de REGRA, não de leitura, e a tela diz isso.** Este feed é o oposto das
abas de tema: ali o dado foi conferido no documento e escrito por alguém; aqui é o que o
Ministério publicou, como publicou. Cada linha mostra **o motivo** da classificação —
sem ele o leitor recebe um rótulo sem poder discordar, e discordar é o mecanismo de
correção de um classificador por regra.

**A ordem dos testes é a regra** (o primeiro que casar decide), calibrada com o usuário em
17/08/2026 nas palavras dele — *baixa*: educação básica, rede federal, pessoal; *média*:
aprovação de polos, temas como Fies e ProUni; *alta*: portarias com mudança regulatória,
instituição de grupos de trabalho, aprovação de novas vagas e de novos cursos de medicina:

1. **Cita marca de grupo aberto** → ALTA. Usa os tokens de `config/grupos_marcas.json`, os
   mesmos do audit de grupos. Se o ato nomeia a Estácio, é da companhia que se está olhando.
2. **Órgão que não faz regulação** → BAIXA. A lógica é por INCLUSÃO: os seis órgãos
   centrais (Gabinete, SERES, SESu, CNE, Inep, FNDE) são lista finita e estável; listar as
   ~70 universidades e ~40 institutos federais para excluir nunca terminaria.
3. **Assunto de rede federal, pessoal ou administração** → BAIXA.
4. **Medida com efeito comercial direto** (suspensão de ingresso/Fies/ProUni,
   descredenciamento, medida cautelar, chamamento) → ALTA.
5. **Tema do setor com peso de norma** → ALTA. "Peso de norma" inclui Portaria do Gabinete
   do Ministro, do CNE e do Inep — não só título que diga "normativa".
6. Resto → MÉDIA.

⚠️ **A ORDEM entre "média" e "norma" custou dois acertos para ser descoberta.** O teste de
polos/Fies/ProUni posto antes do teste de norma engolia a **Lei nº 15.388/2026** — a reforma
do Fies — classificando-a como média por citar Fies, quando é o ato de maior impacto do tema
no período. Regra correta: ato **rotineiro** sobre Fies é média; **norma** sobre Fies é alta.
O que separa os dois é o alcance, não o assunto.

⚠️ **"Dispõe sobre" e "regulamenta" saíram dos gatilhos de alta.** São genéricos demais e
pegavam ato puramente administrativo — "Dispõe sobre a redistribuição de cargos" e "Dispõe
sobre a avocação de competência" entraram como alta numa rodada. Continuam alcançáveis pelo
teste de norma, que exige tema do setor junto.

⚠️ **O código e-MEC vale mais que o token de marca.** Quando a ementa traz `Cód. e-MEC NNN`,
`carrega_emec()` cruza com `data_processed/emec_ies.csv` e devolve o grupo econômico com
certeza de identificador, não de nome parecido — e promove o ato a alta. Cuidado com o falso
amigo: `e-MEC: 202221701` nas súmulas do CNE é número de **processo**, não de instituição.
Só 3 dos 244 atos de uma coleta trazem código de IES, então o nome (`ies_citada`) entra como
segunda opção: pelo menos mostra de quem o ato fala.

**Três calibrações que só apareceram rodando contra dado real** — e cada uma é a razão de
um bloco de código existir:

- **A ementa vem com o preâmbulo de quem assina.** "…UPF (Cód. e-MEC 20). A SECRETÁRIA DE
  REGULAÇÃO E SUPERVISÃO…, no uso das atribuições…". Classificar sobre o texto inteiro fazia
  "SECRETÁRIO **SUBSTITUTO**" casar com o padrão de pessoal e rebaixar o ato pela assinatura
  de quem publicou. `resumo_util()` corta no preâmbulo.
- **Exigir título normativo dava ZERO alta em 15 dias.** "PORTARIA SERES/MEC nº 404" não casa
  com `portaria normativa`. Um corte que nunca dispara não é conservador, está quebrado.
- **SÚMULA DE PARECERES do CNE não é norma**, é a ata de decisões sobre instituições uma a
  uma. Sem a exceção, 9 dos 10 primeiros "alta" eram súmula, o que enterraria o ato real.

**Validação nos dois sentidos**, e é ela que dá confiança na regra: contra as 11 decisões já
curadas em `config/regulatorio.json` — de alto impacto por definição — o classificador acerta
**11 de 11**. E os dois exemplos que o usuário deu como baixa (Portaria MEC 666 dos Institutos
Federais; Portaria 1.097 da UFBA) caem em baixa pelo motivo certo. **Ao mexer nos padrões,
rode esse teste de novo.**

Resultado de 17/08/2026: 244 atos em 20 dias úteis — 1 alta, 115 média, 128 baixa. Uma alta
em 20 dias é realista: a base curada tem 11 atos em cerca de dois anos.

### 💡 O Diário Oficial ACEITA acesso automatizado (com Chrome real)

Isto destrava o item mais difícil do módulo. `WebFetch` no `in.gov.br` derruba a conexão
("socket hang up"), mas **Playwright com `channel="chrome"` abre normalmente, headless** — a
mesma solução que resolveu a Cogna no coletor de mensalidades.

```
ato direto:  https://www.in.gov.br/web/dou/-/<slug-do-ato>-<id>
busca:       https://www.in.gov.br/consulta/-/buscar/dou?q=<termo>&s=do1&exactDate=all
```

A página do ato traz **tudo o que a base precisa**, em texto: `Publicado em: 21/05/2025 |
Edição: 94 | Seção: 1 | Página: 59`, o órgão e a ementa completa. A busca devolve contagem de
resultados e a lista com órgão, edição, data e página.

⚠️ **Duas armadilhas de busca que custaram tempo:**

1. **Ato do Inep sai como "PORTARIA Nº 413", sem a sigla no título.** Procurar por
   `"PORTARIA INEP Nº 413"` devolve zero — e zero resultado aqui **não** significa que o ato não
   existe. Busque pelo formato exato do título do DOU.
2. **Nem tudo está indexado.** A Portaria MEC nº 129/2026 (revogação do chamamento de Medicina)
   não apareceu em nenhuma variação de busca, embora exista e esteja no comunicado oficial do
   MEC. Quando a busca falhar, o comunicado do órgão serve como fonte — mas registre isso na
   própria entrada, como está feito lá.

**O coletor foi construído em 14/08/2026: `scripts/09_fetch_dou.py`.**

```bash
python scripts/09_fetch_dou.py                    # 5 anos, 4 temas
python scripts/09_fetch_dou.py --termo fies       # um tema só
python scripts/09_fetch_dou.py --anos 1 --max-paginas 3
```

⚠️ **Ele NÃO escreve em `config/regulatorio.json`, e isso é decisão de projeto.** A busca por
"educação a distância" nos últimos 5 anos devolve **13.136 resultados**; "curso de medicina",
6.935. A esmagadora maioria é ato de uma IES específica. Despejar isso no feed não daria um
feed, daria um depósito. A saída é uma lista de candidatos para curadoria:

| Arquivo | Papel |
|---|---|
| `data_processed/dou_candidatos.jsonl` | bruto, append-only, deduplicado por URL |
| `outputs/dou_candidatos.md` | relatório para leitura e decisão |

**Quatro cortes, nesta ordem.** Cada padrão saiu de um falso positivo observado ao rodar, não
de suposição — os dois últimos só apareceram depois da primeira varredura de verdade:

1. **Órgão subordinado.** O resultado da busca diz quem publicou. Interessa o que sai do
   Gabinete do Ministro, SERES, SESu, CNE, Inep e FNDE. Resolução do CONSUP do IF de Mato
   Grosso, não. Este corte sozinho elimina a maior parte do ruído.
2. **Tipo do ato.** Lei, decreto, portaria normativa e resolução passam sempre. "Portaria"
   simples só passa se a ementa não parecer ato de uma IES individual.
3. **Ruído administrativo.** Empenho orçamentário, regimento interno, nomeação e medida de
   supervisão sobre **uma** mantenedora. Sem este corte o tema Fies vinha com 63 candidatos;
   com ele, 36.
4. **Ato em lote sobre IES.** O mais importante dos quatro. A SERES publica portarias que são
   **tabelas**: dezenas de cursos de dezenas de faculdades num ato só, com código da IES, CNPJ
   da mantenedora e aditamento de vagas. O título ("PORTARIA SERES/MEC nº 900") não denuncia
   nada; a ementa entrega. Sem este corte a SERES sozinha respondia por **106 de 206**
   candidatos — mais da metade da lista de curadoria seria ato individual travestido de norma.

**Resultado da varredura de 14/08/2026** (5 anos, 13 termos, 5 páginas por termo):

| Etapa | Quantidade |
|---|---:|
| Resultados brutos raspados | 594 |
| Únicos (dedup por URL) | 452 |
| **Candidatos após os 4 cortes** | **176** |

Por tema: medicina 76 · EaD 52 · Fies 34 · regulação 14.
Por órgão: SERES 88 · Gabinete do Ministro 50 · FNDE 17 · Inep 11 · SESu 10.

⚠️ **Os 88 da SERES ainda merecem desconfiança.** O corte 4 só enxerga o que aparece nos 600
caracteres de ementa que a busca devolve; ato em lote cujo CNPJ fique além disso passa. Ao
curar, comece assumindo que portaria da SERES é ato individual até o texto provar o contrário.

⚠️ **A curadoria é o trabalho, e é humana.** Decidir o que é relevante e escrever o resumo é
exatamente o que não se automatiza aqui — foi decisão registrada desde a sessão anterior.

Detalhes técnicos já pagos: a paginação **não** é por URL (`&currentPage=2` devolve a
primeira página de novo) — é o botão `#rightArrow`, que é JS. E `channel="chrome"` continua
obrigatório: o Chromium do Playwright é barrado.

**Estado em 13/08/2026: 11 decisões, 3 temas, ZERO a confirmar** — todas com fonte oficial.

A conferência nas fontes oficiais valeu muito a pena e vale repetir o método: a página de
legislação de EaD do MEC entregou **três atos que a imprensa não citava** — a Portaria nº
378/2025 (formatos de oferta), a nº 506/2025 (corpo docente, tutores e **polos**) e a data
correta da nº 381/2025 (20/05/2025, não 01/01). O comunicado oficial do MEC sobre a revogação do
chamamento de Medicina trouxe uma ressalva que muda a leitura: a Portaria nº 129/2026 **não**
derruba a Portaria nº 650/2023 nem os processos judiciais em curso, que seguem nos parâmetros do
STF — quem lesse só a manchete concluiria que a expansão morreu por completo.

**As 3 que faltam conferir:** Portaria MEC nº 276/2026 e Portaria Inep nº 413/2025 (ambas do
Enamed) e a reforma do Fies. Comece por elas.

Nota de idioma: a **interface** é bilíngue, mas o **conteúdo regulatório permanece em português**
nos dois idiomas — é norma brasileira, e traduzir "Decreto nº 12.456/2025" atrapalharia quem for
atrás da fonte. Mesmo princípio de nome de grupo e sigla de UF.

### O bloco Mensalidades

`js/mensalidades.js` + a seção `#v-mensalidades` do `index.html`. Chips de modalidade
(presencial / semipresencial / EAD) comandam a tela inteira; não há filtro global — é preço de
hoje, não série do Censo, então `FILTROS.mensalidades = []`.

**A regra editorial da tela é o aviso de cima:** isto é **preço de tabela, não ticket líquido**.
A companhia reporta receita depois de bolsa, desconto de captação, FIES/ProUni e inadimplência,
então **este número não reconcilia com o release e não deve ser usado para isso**. Serve para
comparar posicionamento e acompanhar o movimento da tabela. O aviso está na tela, não só aqui.

Quatro peças: mediana por instituição (mediana, não média — Odontologia e Veterinária dominariam
qualquer média), matriz curso × IES com a coluna **Spread** (quanto o mais caro cobra a mais que
o mais barato naquele curso), a faixa min–máx por unidade com o ponto da mensalidade publicada, e
a série no tempo — que **só aparece a partir da segunda coleta**, senão o gráfico desenharia um
ponto solto e sugeriria tendência onde não há.

A coluna `base` atravessa a tela toda: ver o ⚠️ de "Fechar o ciclo das mensalidades". **Preço de
piso nacional e média de unidades não são a mesma métrica**, e o bloco foi construído para não
deixar o leitor confundir os dois.

### Tracking de mensalidades

`scripts/07_fetch_mensalidades.py` acompanha o preço de mensalidade dos cursos mais populares
nas faculdades das companhias abertas. **Os sites não publicam preço no HTML**: o valor só
aparece depois de percorrer um assistente (buscar curso → abrir curso → consultar valores →
unidade + turno, ou estado/cidade/polo no EAD). Por isso a coleta roda em **Playwright**
(instalado nesta máquina; `python -m playwright install chromium` se faltar).

| Peça | Papel |
|---|---|
| `config/mensalidades_ies.csv` | faculdade → motor de coleta + URL + liga/desliga |
| `config/mensalidades_cursos.csv` | cursos alvo por modalidade + **sinônimos** (é o que resolve "Direito com Opice Blum") |
| `scripts/lib/mensalidades.py` | config, parsing de preço, histórico, agregação |
| `data_processed/mensalidades.jsonl` | histórico bruto, uma linha por unidade/polo/dia |
| `dashboard/data/mensalidades.json` | agregado que o bloco **Mensalidades** consome |

⚠️ **Duas armadilhas do payload, já pagas em `exporta_web()`.** Nenhuma chave de resumo pode se
chamar como uma **coluna**: o resumo é escrito depois da expansão colunar, então o nome repetido
**sobrescreve a coluna inteira** e o arquivo sai desalinhado. Aconteceu duas vezes — `ies` (a
coluna de 29 linhas virava a lista de 3 IES distintas, e cada linha ia para a instituição errada:
Anhembi Morumbi aparecia como grupo YDUQS) e a contagem de ofertas chamada de `n`. Hoje a coluna
é `n_ofertas`, os resumos são `ies_lista` e `grupos_lista`, e `n` é o **número de linhas** — que é
a convenção dos demais cubos e o que `linhas()` do dashboard espera. Um `assert` impede a
terceira vez.

**Regra de preço:** sempre o **menor** valor da seleção (em "de R$ 100 por R$ 79" vale o 79);
a mensalidade publicada é a média simples do menor preço de cada unidade/polo, com min, max e
nº de ofertas junto.

São **6 motores para 9 faculdades** — Anhembi e São Judas compartilham o portal da Ânima;
Anhanguera e Unopar, o da Cogna. **`anima` e `estacio` estão implementados**; os demais estão
com `ATIVO=0`. Sondagem de 12/08/2026, que já poupa a próxima sessão de redescobrir:

| Motor | Situação | O que a sondagem mostrou |
|---|---|---|
| `anima` | ✅ coletando | ver §"O motor da Ânima quebrou e foi consertado" |
| `estacio` | ✅ coletando, **sem navegador** | ver §"A Estácio sai por API" |
| `uninassau` | 🟡 **cuidado com a promoção** | ver §"A Uninassau tem uma armadilha de preço" |
| `uniasselvi` | ✅ coletando | busca por URL (`?search=`); ver §"Uniasselvi e Cogna" |
| `unicesumar` | 🟡 explorar | **12/08/2026:** achei o catálogo completo em `inscricoes.unicesumar.edu.br/assets/images/features/dashboard/cursos.json` — 515 cursos com `NM_CURSO`, `URL_CURSO`, `METODOLOGIA` (só EAD e Semipresencial) e duração, **mas sem preço nenhum**. A página do curso também não mostra valor. Há um gateway em `gateway.unicesumar.edu.br` cujo `/auth-server/oauth/token` devolve bearer token **sem credencial**, e endpoints `central-captacao-standalone-api/{pais,estado}` respondem com ele. O preço deve sair de algum endpoint desse gateway — é por aí que a próxima sessão deve procurar. **Correção anterior:** o CPF que parecia barreira é o login da *Área do Candidato* (`#cpfAreaCandidato`, oculto na página), não o portão do preço — a página é listagem de cursos com busca e um lead só de e-mail. O preço deve vir depois de escolher o curso; **nada indica precisar de dado pessoal**. Em 12/08/2026 o usuário ofereceu o CPF dele para esse fim e **ele não foi usado nem guardado**, justamente porque a barreira não existe. Se um site realmente exigir documento, peça ao usuário na hora em vez de deixar dado pessoal em arquivo de projeto. Nota de método: não preencher documento inventado que passe no dígito verificador (é de uma pessoa real e vira lead em nome dela); sequência repetida como 999.999.999-99 não é de ninguém, mas os validadores rejeitam |
| `cruzeiro` | 🔴 o mais difícil | **12/08/2026:** a loja de cursos fica em `cursos.cruzeirodosul.edu.br` e é **VTEX**. A API de catálogo do VTEX (`/api/catalog_system/pub/products/search`) devolve **403** em HTTP puro, o GraphQL público responde com `"disableOffers":true`, e **nenhuma página renderizou preço** — nem a home da loja, nem a busca. Antes de insistir, vale confirmar se o preço está publicado em algum lugar do site |
| `cogna` | ✅ coletando | ver §"A Cogna é nacional e o card mistura modalidade". O **"Access Denied" era o Chromium do Playwright**: com `channel="chrome"` o site abre normalmente, inclusive headless |

💡 **Antes de escrever motor de navegador, procure a API.** A lição da Estácio vale para os
quatro que faltam: abra a listagem com o painel de rede aberto e veja o que alimenta os cards.
Uma API troca um assistente frágil — que quebra quando o site renomeia um rótulo, como acabou de
acontecer com a Ânima — por chamadas estáveis, mais rápidas e com preço por unidade de graça.
O motor da Estácio inteiro cabe em `estacio_json` + `estacio_unidades` + `estacio_carrega`.

### A Estácio sai por API, e o preço dela **não** é nacional

⚠️ **Isto corrige a conclusão anterior deste documento.** A ideia de gravar a Estácio como
`unidade = "nacional (a partir de)"` estava errada e foi abandonada.

A listagem de `estacio.br/cursos/graduacao` é desenhada por uma **API pública**, a mesma que o
site chama, e ela responde a HTTP puro — **sem Playwright, sem Chrome**. O que a destrava é um
cabeçalho: com `x-marca-origin: estacio` responde 200, sem ele o gateway devolve **502**.

```
/ofertas/api/v1/ofertas/unidades?idsMarca=1                as 2.071 unidades (campi + polos)
/ofertas/api/v1/ofertas/prateleira/v2?...&codigoCampus=N   cursos e preços daquela unidade
```

Uma chamada por unidade traz **todos** os cursos dela com o preço de cada modalidade
(`indModalidade`: P presencial, S semipresencial, T EAD; "AO VIVO" e "FLEX" são formatos próprios
da Estácio e ficam fora da comparação). Por isso o motor carrega tudo num cache e depois responde
curso a curso de memória — o inverso do motor da Ânima, que navega por curso.

**Recorte:** os 160 campi (oferta presencial) + até 10 polos por capital de `CIDADES_EAD` — 230
unidades, ~4 min de coleta. O critério de polos é o mesmo já usado na Ânima, para os dois ficarem
comparáveis.

Consultada **por unidade**, a API mostra que o "a partir de" do card é número de vitrine:

| Curso | Coletado por unidade | "A partir de" nacional |
|---|---|---|
| Odontologia presencial | R$ 706,50 (Santo Amaro, SP) a **R$ 1.426,81** (Boa Vista, RR) | R$ 789 — **acima** do mínimo real |
| Administração EAD | R$ 139 a R$ 159 nos polos de capital | R$ 129 — **abaixo** do que a capital cobra |
| Fisioterapia semipresencial | R$ 299 em **todos** os 63 polos de capital | R$ 199 |

Ou seja: o headline nacional **não reconcilia com a oferta por unidade**, nem por cima nem por
baixo. E como o recorte de EAD é amostrado em capital, ele tende a ficar **acima** do piso
nacional, que costuma vir de polo do interior. Isso está escrito na tela do bloco.

**Medicina não aparece na Estácio e isso está certo:** na YDUQS a medicina é ofertada pela marca
**IDOMED**, que não está na prateleira de `idsMarca=1`. Não é falha de busca.

O casamento de curso é por **nome exato**, de propósito: por prefixo, "Medicina" casaria com
"Medicina Veterinária" e "Pedagogia" com "Psicopedagogia". Quando o nome muda de faculdade para
faculdade, o lugar de resolver é a coluna `SINONIMOS` — foi assim que "Gestão de Pessoas" passou
a achar "Gestão de Recursos Humanos".

### A Cogna é nacional e o card mistura modalidade

Anhanguera e Unopar rodam o mesmo portal. A busca é **por URL** (`?search_texts=Pedagogia`),
sem digitar em campo nenhum, e cada card (`div.product`) traz nome, modalidade, preço e turnos
juntos. O link do curso é `/curso/<slug>/` **no singular** — procurar `/cursos/` não acha nada.

⚠️ **O preço da Cogna é nacional.** Nem a listagem nem a página do curso oferecem seleção de
polo ou campus: as duas repetem o mesmo "A partir de". Por isso a observação vai gravada com
`unidade = "nacional (a partir de)"`, e na tela isso aparece como **n=1 e min=max** — que é
justamente o sinal de que aquela média não tem dispersão por praça para mostrar. Diferente da
Estácio, aqui a sondagem por unidade foi tentada e **não existe**.

⚠️ **Um card pode declarar duas modalidades e um preço só.** O card de Pedagogia diz
"Semipresencial Presencial" e mostra um único "A partir de: R$ 157,99". Esse valor é piso das
duas juntas e não pertence a nenhuma em particular — atribuí-lo a uma rotularia errado. O motor
só aceita **card que declare uma única modalidade** (`cogna_modalidades_do_card`); o resto sai
como `"sem card exclusivo desta modalidade"`, que é uma recusa deliberada, não uma falha.
Consequência: a cobertura da Cogna é menor de propósito — 6 de 10 no presencial do Anhanguera.
Se um dia for preciso mais cobertura, o caminho é achar o filtro de modalidade do site (não é
`type[]`, que é grau: bacharelado/tecnólogo/licenciatura) e usá-lo para isolar o preço.

### Uniasselvi: mesma forma da Cogna

Busca por URL (`?search=Enfermagem`) e o card já traz tudo, mas com a **modalidade antes do
nome** do curso: `"Bacharelado | 10 semestres Faculdade Graduação Presencial Enfermagem
A partir de R$ 277,60 mensais"`. A regex `UNIASSELVI_CARD` captura modalidade e nome de uma vez,
em vez de tentar adivinhar onde o nome termina.

**Também é preço nacional.** Tentei descer para a unidade: a página do curso tem estado → polo,
os `<select>` respondem a `change` disparado por JS (clique normal estoura em timeout), a lista
de polos carrega certo — **mas o preço não aparece nem depois de escolher o polo**, e o botão
"CONFIRA NOSSAS OFERTAS" não responde a clique. Fica o "a partir de" da listagem.

Nota de rota: `/graduacao/.../ead` **redireciona para** `/semipresencial`. Na Uniasselvi o que as
outras vendem como EAD chama-se semipresencial. Presencial existe só em Santa Catarina (o
`<select>` de estado tem uma opção só).

### A Uninassau tem uma armadilha de preço

**Não implementada, e por um bom motivo.** O que a listagem mostra é
`"3 primeiras parcelas: R$ 99,00"` — **promoção de entrada, não mensalidade**. A regra do
projeto ("sempre o menor valor") pegaria justamente os R$ 99 e gravaria uma promoção como preço
de tabela. É a mesma armadilha da "Parcela Leve R$ 79" da Estácio, que só não nos pegou porque
lá o dado veio da API.

O caminho está mapeado e é bom: a URL é **por unidade**, no formato
`vest.uninassau.edu.br/cursos/<cidade>/<unidade>/<curso-slug>/<id>?modality=Presencial`, e a
página de uma unidade mostra **três valores** — R$ 99,00 (a promoção), R$ 1.464,05 e R$ 611,23.
Pelo padrão do setor, o R$ 1.464,05 é o "de" e o R$ 611,23 é a mensalidade com desconto.
**Antes de escrever o motor, confirme qual é qual lendo o rótulo ao lado de cada valor** — e não
use `M.menor_preco()` cru nesta faculdade.

### O motor da Ânima quebrou e foi consertado

O documento dava a Ânima como coletando; em 12/08/2026 ela entregava **4 de 10** cursos
presenciais. Três causas, todas corrigidas:

1. **Espera fixa em página que renderiza tarde.** `anima_abre_form` dormia 2,2 s. Medido: aos 3 s
   o `body` tinha **zero caractere** e o botão só aparecia por volta dos 5 s. O motor concluía
   "sem botão de consultar valores" numa página que estava apenas carregando. Hoje espera pelo
   **conteúdo** (`wait_for_function`), não pelo relógio.
2. **O assistente ganhou um passo.** O primeiro dropdown agora é a **modalidade**; unidade e
   turno só aparecem depois dela. E os rótulos foram reescritos ("Selecione aqui a ..."), então
   `dropdown_opcoes` passou a casar por **palavra-chave** ("unidade", "turno"), não por texto
   exato — é o que sobrevive à próxima reescrita.
3. **O clique caía no menu do topo.** Procurar a opção em `ul li` pela página inteira acha o
   "Presencial" do menu *Modalidades*; clicar nele navega para `/modalidades/presencial/` e
   abandona o assistente **sem erro nenhum**. Agora `dropdown_opcoes` guarda a lista que abriu e
   o clique só é aceito dentro da lista cujos itens batem com ela.

O clique de opção é feito por **JS**, não pelo locator: com a lista flutuante do Headless UI o
clique real estoura em timeout mesmo com o item visível, e era daí que vinha a maioria dos
`TimeoutError`.

**Resultado da correção**, na mesma máquina e no mesmo dia — cursos coletados de 10 por
modalidade:

| | Anhembi antes | Anhembi depois | São Judas |
|---|---:|---:|---:|
| Presencial | 4 | **9** | **8** |
| Semipresencial | 0 | **6** | **8** |
| EAD | 0 | **4** | **0** |

⚠️ **O que ainda falha, e é a próxima coisa a olhar na Ânima:**

- Sobrou `"dropdown de unidade não abriu"` em alguns cursos (Odontologia presencial no Anhembi;
  Administração e Sistemas de Informação no São Judas). É **intermitente** — os mesmos cursos
  coletam em outra modalidade —, o que cheira a mais um caso de esperar por conteúdo em vez de
  tempo, agora dentro do assistente.
- **O EAD da Ânima está furado.** No Anhembi traz **1 unidade por curso** quando deveria varrer
  as 7 capitais de `CIDADES_EAD`; no São Judas não traz **nada** (todos caem em "sem preço" ou
  "não tem a modalidade"). O laço estado → cidade → polo está passando batido.

  ✅ **Resolvido na publicação em 14/08/2026, não na coleta.** Com o escopo de mensalidades
  congelado, o laço não será consertado — em vez disso a regra `MIN_POLOS_EAD` deixa essas
  linhas fora da tela, com o nome da IES declarado. Ver §"EAD só entra na tela com cobertura de
  praças". **O número não comparável não está mais publicado**, então a ressalva que existia aqui
  deixou de ser necessária.

⚠️ **Navegador cai em coleta longa.** A primeira rodada completa da Ânima morreu com
`TargetClosedError` depois de ~20 cursos. Hoje o coletor reabre o navegador a cada 12 cursos e
também depois de qualquer erro de sessão fechada.

⚠️ **Grave curso a curso.** A primeira versão só gravava no fim e uma coleta longa morreu no
timeout levando junto tudo o que já tinha levantado. Hoje `M.registra()` é chamado por curso.

Três armadilhas já pagas no motor da Ânima:
1. Os dropdowns **não são `<select>`** (Headless UI): a lista só existe no DOM depois do clique.
   `dropdown_opcoes()` compara as listas visíveis antes e depois para isolar a que abriu.
2. Depois de escolher a unidade **o botão troca de rótulo** e não há id estável para reabri-lo —
   por isso cada unidade recarrega a página. Mais lento, sem estado sujo.
3. Buscar opção por texto solto pega item do menu do topo. Sempre filtrar por `ul li` /
   `[role="option"]` **e** checar visibilidade.

### Números reportados pelas companhias no payload

`04_export_web.py` embute `config/reportado_companhias.csv` em `meta.reportado` (≈3 KB). **A
tabela de reconciliação saiu da interface** (decisão do usuário: o investidor não precisa vê-la);
o dado continua no payload para a Methodology futura, e a verificação se faz por
`scripts/valida_reconciliacao.py` → `outputs/reconciliacao_2024.md`.

⚠️ **A comparação com release é só de graduação.** O CSV ganhou colunas `GRAD_*` com o recorte
de graduação de cada release, derivado das aberturas do próprio documento (a coluna
`GRAD_DERIVACAO` registra a conta). Confrontar com o número-manchete estava errado: ele inclui
pós, técnico e, na YDUQS, o Qconcursos — 498,6 mil alunos de preparatório para concursos, que não
é ensino superior. **Isso inverteu a conclusão da §3.2**: contra graduação reportada, quem
reconcilia é `QT_MAT` (Ânima +2,3%, Cruzeiro +4,4%, YDUQS +5,7%), não a base com trancados.
Detalhe em `docs/04_reconciliacao_companhias.md`.

**Payload inicial: 866 KB comprimidos** (3 MB crus). Detalhe por ano (~860 KB) carrega sob
demanda.

Formato dos cubos: **JSON colunar** (arrays por coluna, não array de objetos) com strings
substituídas por índices para as dimensões. Reduz ~60% e evita parse de centenas de milhares de
objetos.

### Seis armadilhas do front-end já corrigidas — não reintroduza

1. **`totalAno()` vs `totalFiltrado()`.** A primeira é o **denominador de market share** e
   **nunca** filtra por grupo (senão todo grupo teria 100%). A segunda aplica todos os filtros.
   São funções separadas por isso.
2. **Ordenação de tabela**: `asc: false` significa **maior primeiro**. Já esteve invertido.
3. **"Independentes" é bucket residual, não player.** Excluir de Top N, HHI e de qualquer
   disputa de liderança de praça — mas mostrar quanto ele representa, em coluna própria.
4. **`<select>` populado "uma vez só" trava.** O seletor de UF da Geografia deriva do detalhe do
   ano; num ano sem detalhe ele vinha vazio e ficava vazio para sempre. Use `opcoes()` de
   `ui.js`, que repopula quando a lista muda e preserva a escolha.
5. **Nome de topo repetido quebra só o arquivo único.** `05_build_standalone.py` concatena os
   módulos num **escopo único**, então dois `const dataLegivel` (um em `precos.js`, outro em
   `mensalidades.js`) viram `SyntaxError` e a página fica presa no "Carregando…" — enquanto a
   versão servida por módulos ES continua funcionando, o que faz o defeito passar despercebido.
   Pelo mesmo motivo, `import { n as fmtN }` perde o apelido e deixa uma referência morta.
   Hoje `checa_colisoes()` derruba o build com a lista dos nomes em conflito. **Bloco novo:
   entre em `MODULOS` e, se tiver dado próprio, em `CORE`.**
6. **`display: flex` vence o `[hidden]`.** `.filtros` declara `display: flex`, que ganha do
   `display: none` que o atributo `hidden` traz do navegador — a barra continuava aparecendo nos
   blocos sem filtro global (Price Action e Mensalidades): os `.f-item` sumiam um a um e sobrava
   o "Limpar filtros" solto. Resolvido com a regra `.filtros[hidden] { display: none; }`.
7. **`containLabel` do ECharts não reserva espaço para o NOME do eixo**, só para os rótulos.
   Com `grid.bottom: 8`, o nome do eixo X do gráfico escala × crescimento caía fora do canvas e
   simplesmente não aparecia — o texto estava lá na option, invisível na tela. Se puser
   `xAxis.name` ou `yAxis.name`, aumente `grid.bottom`/`grid.left` na mão.
8. **Arredondar cada fatia sozinha não fecha 100%.** As barras 100% empilhadas somavam 99,8% na
   Ser e 100,1% no Cruzeiro, porque cada categoria passava por um `.toFixed(1)` independente. O
   dado estava certo; o arredondamento, não. Hoje `reparte100()` em `grupos.js` usa o método do
   **maior resto**, trabalhando em décimos de p.p. **Use-o em qualquer gráfico novo de 100%.**
9. **`data-din` em elemento que a view NÃO reescreve impede a tradução.** A marca serve para
   dizer "o JS reescreve isto, não capture o texto estático"; posta num `<h3>` fixo, ela faz o
   título nunca aparecer em inglês. Só marque o que a view realmente sobrescreve.
10. **Legenda `type: 'scroll'` esconde nomes atrás de uma setinha.** Num bloco cujo assunto é
   "quem está sendo comparado", isso é o oposto do necessário. Use `legendaTodos()` de
   `grupos.js`, que quebra em linhas e devolve o `topo` que o grid precisa — a legenda do
   ECharts não empurra o grid sozinha e deita por cima das barras se ninguém reservar o espaço.

### Regra editorial da interface

**Toda tela declara o denominador usado.** Um share sem denominador explícito é fonte de erro de
leitura. Quando há filtro de grupo, o ranking competitivo **ignora esse filtro de propósito**
para não perder o contexto, com a linha selecionada destacada.

### Visual

Paleta **Itaú**: laranja `#EC7000` (acento), azul-marinho `#003C7D` (contraponto), fundo claro,
cards com *eyebrow* de categoria. Nos gráficos, **presencial = azul** (estrutura instalada),
**EAD = laranja** (o que cresce) — duas famílias de matiz, distinguíveis em escala de cinza.
Tema único claro por decisão: é identidade corporativa. `body` pinta fundo e cor explicitamente
para não herdar o tema do host.

Cores por grupo ficam em `config/grupos.csv`, coluna `COR`.

---

## 9b. Coleta automática (GitHub Actions) — LIGADA

Três workflows em `.github/workflows/`. Detalhe completo em `docs/06_publicacao.md`.

| Workflow | Faz | Quando |
|---|---|---|
| `precos.yml` | `06_fetch_precos.py` → commita `precos.json` | `*/5 13-21 * * 1-5` (pregão) |
| `dou_diario.yml` | `11_fetch_dou_diario.py` → commita o feed | `0 10 * * 1-5` = 7h BRT |
| `publicar.yml` | publica `dashboard/` no Pages | ao fim dos dois acima |

⚠️ **`workflow_run` não é redundante com `push`, e sem ele a automação falha em silêncio.**
Push feito com o `GITHUB_TOKEN` **não dispara outros workflows** — proteção do GitHub contra
laço infinito. Sem esse gancho, os coletores atualizariam os dados e a página nunca seria
reconstruída: **site congelado enquanto o repositório avança**, que é o pior caso porque
parece funcionar. O `publicar.yml` também faz `checkout` com `ref: main`, porque
`workflow_run` roda no commit ANTERIOR por padrão e publicaria os dados de antes da coleta.

⚠️ **O cron do GitHub PULA execuções, e muito.** Medido nas primeiras 2,5 h após ligar:
saíram **3 execuções de preço, não ~30**, e uma delas às 22:47 UTC — fora da janela 13–21,
quase uma hora atrasada. Agendamento curto é o primeiro a ser descartado quando a fila
aperta. **Trate o feed de preços como "algumas vezes por hora", não como intraday.** Não
adianta apertar o cron; se a cadência importar, o caminho é runner próprio.

⚠️ **`git pull` ANTES de qualquer coisa.** Os workflows commitam sozinhos várias vezes por
dia. Em 17/08 o rebase deu conflito em `precos.json` — a resolução certa é **ficar com a
versão do remoto** (`git checkout --ours` durante rebase), porque é a coleta mais recente e
a próxima rodada sobrescreve de qualquer jeito.

⚠️ **Cuidado com `precos.json` corrompido na área de trabalho.** Achado em 18/08: o arquivo
local estava com **1 KB** — uma coleta que falhou por falta de rede
(`URLError: getaddrinfo failed`), com zero papéis e zero séries, gravada por alguma rodada
em ambiente sem internet. Os commits estavam íntegros. **Confira o tamanho (≈234 KB) antes
de commitar**; um `precos.json` vazio publicado deixa o Price Action em branco. Para
restaurar: `git checkout origin/main -- dashboard/data/precos.json`.

---

## 10. O que vem a seguir

### Mensalidades: escopo CONGELADO em 14/08/2026 — não reabrir

⚠️ **Decisão do usuário, tomada com a cobertura na mesa: a coleta de mensalidades para aqui.**
Os três motores que faltam — `uninassau`, `unicesumar` e `cruzeiro` — **não serão escritos**. A
relação esforço/retorno é a pior do projeto (VTEX com 403, gateway OAuth a explorar, promoção de
entrada a desambiguar) e a cobertura atual já sustenta o bloco. **Não proponha esses motores de
novo**; o que está mapeado sobre eles abaixo fica como registro, não como pendência.

O que **continua** valendo e é barato: rodar `07_fetch_mensalidades.py` em outra data destrava a
série temporal, sem tocar em código.

**Cobertura de 12/08/2026: 6 das 9 faculdades, 4 dos 6 grupos** — Anhembi Morumbi e São Judas
(Ânima), Estácio (YDUQS), Anhanguera e Unopar (Cogna) e Uniasselvi (Vitru). Ser Educacional,
Cruzeiro do Sul e Unicesumar ficam **fora por decisão**, não por pendência.

### EAD só entra na tela com cobertura de praças (`MIN_POLOS_EAD`)

Com o escopo congelado, o laço de polos da Ânima **não vai ser consertado** — então a
consequência analítica dele precisou ser resolvida na publicação, não na coleta.

`MIN_POLOS_EAD = 3` em `scripts/lib/mensalidades.py`: linha de EAD com `base = "unidades"` e
menos de 3 polos **não é publicada**. No EAD o preço varia por polo, então a linha só significa
alguma coisa se vier de várias praças — a Estácio entra com 64. As 4 linhas de EAD da Anhembi
vinham de **1 polo** e, publicadas ao lado da Estácio, sugeriam que a Anhembi cobra ~45% mais
caro no EAD, quando a comparação era um ponto contra uma média nacional de praças.

Três propriedades da regra, todas deliberadas:

1. **É por cobertura, não por IES.** Nenhum nome aparece no código. Se a coleta da Ânima um dia
   melhorar, as linhas voltam sozinhas — não há exceção para alguém lembrar de desfazer.
2. **O piso nacional não entra nesta regra.** "A partir de" nunca prometeu ser média de praças;
   a tela já o marca com asterisco por outro motivo (coluna `base`).
3. **A exclusão é declarada, não silenciosa.** O payload carrega `ead_fora` (quem, qual grupo,
   quantos cursos, quantos polos) e `notaEAD()` põe o nome na tela. Omitir calado seria pior que
   o problema original: a IES sumiria da coluna e o leitor concluiria que ela **não oferta EAD**.

Efeito: 79 → **75 linhas**, e a aba EAD passou a ter **uma instituição só** (a Uniasselvi chama
de semipresencial o que as outras vendem como EAD). É pouco, mas é comparável — que é a ordem de
prioridade do projeto.

⚠️ **Dois tipos de preço convivem, e a tela agora diz qual é qual.** Estácio (via API) e Ânima
(via assistente) descem até a **unidade**; Cogna e Uniasselvi só publicam **"a partir de"
nacional** — a sondagem por unidade foi tentada nas duas e não existe. Como isso é diferença de
natureza, e não de metadado, o agregado ganhou a coluna **`base`** (`unidades` × `nacional`) e a
interface usa essa coluna em três lugares:

- na matriz curso × instituição, quem é nacional leva **asterisco no cabeçalho** e uma nota
  explicando que ali o valor é um **piso**, não a média das praças — e que por isso o *spread*
  contra as demais sai exagerado;
- o gráfico de dispersão **exclui** as nacionais e diz quais ficaram de fora. Desenhá-las como
  um ponto sem faixa sugeriria preço uniforme no país inteiro, o que é conclusão, não dado;
- o `n` de cada linha continua visível, então dá para ver na hora se a média veio de 64 polos
  ou de uma observação só.

**Regra ao adicionar motor novo:** se o site só publicar piso nacional, grave
`unidade = "nacional (a partir de)"` — é isso que `exporta_web()` usa para classificar a linha.

~~0. Consertar o EAD da Ânima~~ — **cancelado em 14/08/2026** (escopo congelado). A consequência
   analítica foi resolvida por `MIN_POLOS_EAD`, acima.

~~1. Os três motores que faltam~~ — **cancelados em 14/08/2026.** `uninassau`, `unicesumar` e
   `cruzeiro` não serão implementados. O que está mapeado sobre eles fica como registro.

~~2. Ampliar a cobertura da Cogna~~ — **fora de escopo pela mesma decisão.** A limitação atual
   (regra do card exclusivo) é uma recusa deliberada e continua correta.

**O que sobrou, e é barato:**

1. **A segunda coleta destrava a série.** Hoje há **uma** data, então o gráfico de evolução
   está oculto de propósito. Basta rodar `07_fetch_mensalidades.py` em outro dia — o histórico
   é append-only e o agregado se refaz sozinho. **Nada de código.**
2. **Coleta agendada.** Com os motores estáveis, uma rodada semanal alimenta a série. A Estácio
   sai por API e é barata (~4 min); a Ânima é lenta (recarrega a página por unidade) e é a que
   quebra quando o portal muda — vale rodar as duas separadas.

### Escopo originalmente pedido e ainda não construído

**A Methodology perdeu urgência mas não saiu**: as notas metodológicas da home cobrem o essencial
(matrícula × base, pro-forma, polo EAD, proxy de campus, denominador), mas não substituem uma
página completa.

- **Investor Snapshot** — página objetiva: tamanho, crescimento, EAD, maiores players, quem
  ganha share, cursos e regiões crescendo, exposição dos grupos. Pensada para virar material de
  apresentação.
- **Key Insights** — insights automáticos por **regras determinísticas**, cada um carregando o
  número, o denominador e o período que o sustentam. Sem interpretação sem respaldo. Deve
  respeitar §3.3: nada de insight de crescimento em ano contaminado por reclassificação.
- **Análise por IES individual** — seleção de uma instituição com seu perfil completo.
- **Campus Explorer** — tabela pesquisável IES × município (é o que o Censo permite; ver §3.4).
- **Methodology & Data Notes** — a página que torna a ferramenta distribuível. Precisa
  consolidar: conceito de matrícula/ingressante/concluinte, tratamento de EAD, agrupamento
  econômico, pro-forma, ponte de trancados, anos contaminados e a limitação de campus.
  **Sem essa página a ferramenta não deveria ser entregue a investidor.**

Já disponível mas não exposto no dashboard: dados de docentes (`QT_DOC_*`), financiamento
estudantil (`QT_MAT_FIES`, `PROUNI`), turno e evasão (`QT_SIT_*`) estão nos Parquet e podem
virar métricas de eficiência operacional e dependência de funding.

---

## 11. Documentação completa

| Documento | Conteúdo |
|---|---|
| `docs/01_dicionario_dados.md` | Data dictionary, regras de agregação, números de referência |
| `docs/02_qualidade_dados.md` | Testes, anomalias, limitações, checklist de validação |
| `docs/03_arquitetura.md` | Arquitetura, dimensionamento dos cubos, sequência de entrega |
| `docs/04_reconciliacao_companhias.md` | **Censo × releases das 7 abertas**, com fontes |
| `docs/05_serie_historica.md` | Série 2015–2024, comparabilidade e armadilhas |
| `docs/06_publicacao.md` | **GitHub Actions + Pages**: como a automação funciona e onde mexer |
| `docs/HANDOFF_SESSAO_2026-08-17.md` | Resumo da sessão que pôs o projeto no ar |
| `outputs/validation_report.md` | Relatório de validação (gerado) |
| `outputs/audit_grupos_2024.md` | Auditoria do mapeamento (gerado) |
| `outputs/grupos_composicao_2024.md` | IES por IES dentro de cada grupo (gerado) |
| `outputs/reconciliacao_2024.md` | Reconciliação com releases (gerado) |

---

## 12. Preferências de trabalho observadas

- O usuário é analista de *equity research* e cobra **consistência com o que as companhias
  reportam**. Foi ele quem apontou a divergência da YDUQS que revelou o problema dos trancados.
- Quer **validação antes de confiar**: pediu explicitamente checagem contra os releases de 4T24
  antes de aceitar a série histórica.
- Mantém o `Suporte IES.xlsx` no formato que for mais prático para ele atualizar — **o pipeline
  se adapta ao Excel, não o contrário**.
- Trabalha em português.
