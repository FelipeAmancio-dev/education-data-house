# Dashboard do Ensino Superior no Brasil

Ferramenta de análise do setor de ensino superior brasileiro a partir dos **Microdados do Censo
da Educação Superior (INEP)**, orientada a market share, concentração, mix e posicionamento
competitivo dos grupos educacionais.

**Estado atual: Etapas 1 a 3 concluídas.** Série histórica **2015–2024** ingerida, agregada e
validada, e **MVP do dashboard funcionando** (Overview, Grupos, Cursos, Geografia, Rankings).

```bash
python run_dashboard.py           # abre o dashboard no navegador
```

Para reconstruir os dados do zero:

```bash
python scripts/01_ingest.py       # zips -> Parquet limpo (10 anos, ~40 MB)
python scripts/02_build_cubes.py  # Parquet -> dimensões + cubos (~6 MB)
python scripts/03_validate.py     # checklist de consistência; falha o build se quebrar
python scripts/04_export_web.py   # cubos -> JSON do dashboard (3 MB iniciais)
```

---

## Comece por aqui

| Documento | Conteúdo |
|---|---|
| **[`docs/00_HANDOFF.md`](docs/00_HANDOFF.md)** | **Comece aqui se está retomando o projeto** — estado atual, armadilhas, pendências |
| [`docs/01_dicionario_dados.md`](docs/01_dicionario_dados.md) | Data dictionary dos campos usados, regras de agregação e números de referência de 2024 |
| [`docs/02_qualidade_dados.md`](docs/02_qualidade_dados.md) | Testes de qualidade, anomalias, limitações e checklist de validação |
| [`docs/03_arquitetura.md`](docs/03_arquitetura.md) | Proposta de arquitetura, dimensionamento e sequência de entrega |
| [`docs/04_reconciliacao_companhias.md`](docs/04_reconciliacao_companhias.md) | **Por que o Censo não bate com o release da empresa** — e como fazer a ponte |
| [`docs/05_serie_historica.md`](docs/05_serie_historica.md) | **Série 2015–2024**: o que muda, o que é comparável e as armadilhas da série |
| [`outputs/validation_report.md`](outputs/validation_report.md) | Relatório de validação da série (gerado automaticamente) |

**Se você só vai ler uma coisa:** a seção §2 do data dictionary, sobre `TP_DIMENSAO`. É o campo
que determina quais métricas podem ser somadas em cada linha; ignorá-lo duplica 5,2 milhões de
matrículas EAD.

---

## Números de referência — 2024

| KPI | Valor |
|---|---|
| Matrículas | 10.227.266 |
| Ingressantes | 5.010.613 |
| Concluintes | 1.333.988 |
| Cursos | 45.776 |
| Vagas ofertadas | 23.658.494 |
| IES | 2.561 |
| Unidades presenciais (proxy IES × município) | 3.793 |
| EAD | 50,7% · Presencial 49,3% |
| Privada | 79,8% · Pública 20,2% |

Qualquer agregação produzida pelo pipeline deve reproduzir exatamente estes valores.

---

## Estrutura do projeto

```
data_raw/{ano}/      arquivos originais do INEP (zip preservado, não versionado)
data_processed/      Parquet tratado + cubos agregados
scripts/             00_fetch_geo · 01_ingest · 02_build_cubes · 03_validate · 04_export_web
dashboard/           index.html · css/ · js/ (dados · ui · views · comparacao · app)
                     data/ (JSON gerado) · vendor/ (ECharts offline)
config/              mapeamentos editáveis (grupos, códigos, geografia)
outputs/             relatórios de validação, auditoria e reconciliação
docs/                documentação
run_dashboard.py     servidor local + navegador
```

## O dashboard

Seis visões:

| Visão | O que responde |
|---|---|
| **Overview** | Tamanho, crescimento, mix EAD/presencial, composição por área e maiores grupos |
| **Grupos** | Consolidado por grupo econômico, market share ao longo do tempo, mix por modalidade, concentração (Top 5, HHI) |
| **Comparação** | Confronto direto entre players selecionáveis — começa com as 7 companhias abertas |
| **Cursos** | Mercado por rótulo CINE e, dentro de um curso, ranking de grupos e de IES |
| **Geografia** | Mapa coroplético por UF, ranking de estados e municípios, composição por região |
| **Rankings** | Maiores IES, ganho/perda de market share, cursos que mais crescem, maiores municípios |

Filtros integrados (ano, grupo, UF, modalidade, rede) reagem em todas as visões, com
**Reset filters**. Sem build step: HTML + JS puro, ECharts vendorizado, funciona offline.

### Visual

Paleta **Itaú** — laranja `#EC7000` como acento, azul-marinho `#003C7D` como contraponto,
fundo claro e muito respiro. Cards com *eyebrow* de categoria, números grandes nos KPIs e
tabelas com barra de share. Nos gráficos, presencial é azul (estrutura instalada) e EAD é
laranja (o que está crescendo) — duas famílias de matiz que se distinguem até em escala de cinza.
As cores por grupo ficam em `config/grupos.csv`, coluna `COR`.

**Regra editorial:** toda tela declara o denominador usado. Um share sem denominador explícito
é fonte de erro de leitura — o filtro de grupo, por exemplo, nunca entra no denominador de
market share (senão todo grupo teria 100%).

---

## Arquivos que você edita

Apenas estes. Todo o resto é gerado.

### `Suporte IES.xlsx` — fonte primária

Sua planilha, **uma aba por empresa**. Cada aba pode ter o schema que você quiser: o leitor
detecta sozinho a coluna de código e a de nome (`IES Code`, `Cód. IES`, `Código MEC`,
`CÓDIGO DA IES`, `COD. E-MEC`…). Não é preciso padronizar as abas.

O pipeline ainda:

- **deduplica** linhas que listam campi separadamente (o Censo não tem código de campus);
- **distingue código de IES de código de mantenedora** comparando o nome da planilha com o nome
  da IES e o da mantenedora no Censo. Abas que misturam os dois blocos funcionam sem ajuste, e
  códigos de mantenedora viram regra de grupo — o que captura as IES irmãs de brinde.

### `config/suporte_abas.csv` — aba → grupo

Mapeia o nome da aba para o nome canônico do grupo (`ANIMA` → `Ânima`). Para adicionar uma
empresa: crie a aba no Excel e registre uma linha aqui.

### `config/grupos_consolidacao.csv` — fusões e aquisições

Enquanto `ATIVO=nao`, os grupos aparecem separados. Ao mudar para `sim`, o pipeline soma o
grupo de origem dentro do destino na coluna `GRUPO_CONSOLIDADO`, mantendo `GRUPO` com a visão
standalone — as duas leituras convivem. Já contém a linha `FMU → Ânima`, desativada.

### `config/grupos_mantenedoras.csv` — regras por mantenedora

Atribui grupo a uma **mantenedora inteira** (`CO_MANTENEDORA`), capturando todas as suas IES de
uma vez. É assim que os grupos adicionais (UNINTER, UNIP, UNINOVE e os independentes) são
definidos. Adicionar um grupo novo = adicionar suas mantenedoras aqui.

### `config/ies_grupo_overrides.csv` — exceções

Precedência máxima, no nível de `CO_IES`. Use para casos que fogem à regra da mantenedora, ou
para forçar uma IES a **sair** de um grupo (deixe `GRUPO` vazio). Contém também os casos
pendentes de confirmação, comentados com `#`.

### `config/grupos.csv` — metadados

Nome de exibição, `TIPO` (`listada` / `independente` / `confessional_comunitaria` / `sistema_s`),
ticker, bolsa, cor e ordem nos gráficos.

### `config/grupos_marcas.json` — auditoria

Tokens de marca usados por `scripts/audit_grupos.py` para **encontrar IES que ficaram de fora**.
Só gera candidatos; nunca aplica. Inclui um registro de falsos positivos já verificados
(homônimos como "Potiguar", "São Judas", "Anhanguera de Goiás") para não reaparecerem.

### `config/codigos.json`

Tradução dos códigos numéricos do INEP (`TP_*`, `IN_*`, CINE, região) para descrições.

### Cadeia de precedência

```
ies_grupo_overrides.csv  >  Suporte IES.xlsx  >  grupos_mantenedoras.csv  >  mantenedora derivada
```

A última regra captura IES "irmãs": se uma mantenedora já tem IES no grupo X, as demais também
são X. Validado — nenhuma mantenedora do Censo 2024 aparece em dois grupos.

Para regerar o mapa depois de editar qualquer um desses arquivos:

```bash
python scripts/build_ies_group_map.py
```

Isso **não reprocessa os microdados** — grupo é atributo de IES e o rollup acontece na interface.

---

## Como atualizar com um novo ano

> Etapa 2 — o pipeline abaixo ainda será implementado. Este é o fluxo definido.

1. Baixe os microdados do ano no INEP
   ([dados abertos](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-da-educacao-superior)).
2. Coloque o `.zip` em `data_raw/2025/`.
3. Rode:

```bash
python update_dashboard.py --ano 2025
```

4. Leia `outputs/validation_report_2025.md`. O script **falha** se alguma checagem de
   fechamento quebrar (presencial + EAD ≠ total, soma das UFs ≠ Brasil, duplicidades etc.).
5. Confira em `config/ies_grupo_map.csv` as IES novas do ano (`GRUPO` vazio) e preencha as que
   pertencerem a grupos cobertos.

Depois de editar só o mapeamento de grupos, use o caminho curto (segundos, não toca nos
microdados):

```bash
python update_dashboard.py --apenas-grupos
```

Para abrir o dashboard:

```bash
python run_dashboard.py
```

---

## Requisitos

Python 3.13 com `duckdb`, `pandas`, `pyarrow`, `openpyxl` — todos já instalados neste ambiente.
O dashboard não tem build step: HTML + JS puro, bibliotecas vendorizadas, funciona offline.

---

## Limitações que você precisa conhecer

Detalhadas em [`docs/02_qualidade_dados.md`](docs/02_qualidade_dados.md).

- **Não existe identificador de campus** no Censo. "Nº de campi" é sempre o proxy
  IES × município — grupos com vários campi na mesma cidade são subcontados.
- **Não existe latitude/longitude de campus ou polo.** Os mapas usam centroides de município
  do IBGE (`config/municipios_ibge.csv`, 5.570 municípios, cobertura de 100% dos municípios
  com oferta). Gerado por `scripts/00_fetch_geo.py` — roda uma vez, depois o projeto é offline.
- **`QT_MAT` inclui "Formado" e exclui "trancado"** — não é a "base de alunos" que as companhias
  divulgam. A taxa de trancamento vai de 0,7% (Vitru) a 87,6% (UNINTER), então as duas
  definições produzem **rankings diferentes**. Ver
  [`docs/04_reconciliacao_companhias.md`](docs/04_reconciliacao_companhias.md).
- **Pós-graduação, cursos livres e ensino técnico estão fora do Censo** — só graduação e
  sequencial.
- **A geografia do EAD é o município do polo**, não a residência do aluno.
- **Não há dado financeiro** (preço, ticket, receita). A ferramenta mede volume e share.
- **O mapeamento de grupos cobre 60,4% do mercado** (75,7% da rede privada), em 43 grupos.
  O restante fica como "Independentes", sempre visível nos rankings.

---

## Fonte

INEP — Microdados do Censo da Educação Superior 2024 (publicados em setembro/2025).
Dados públicos, sob a Lei de Acesso à Informação. O Censo não disponibiliza microdados de aluno
ou docente individualizados (LGPD).
