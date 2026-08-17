# Proposta de Arquitetura

> Etapa 1 — proposta para aprovação antes da implementação (Etapas 2 a 4).

## 1. Princípio de projeto

O navegador **nunca** vê os microdados. O pipeline em Python/DuckDB pré-calcula cubos agregados;
o dashboard consome apenas JSON pequeno e faz pivot/rollup em memória.

Três decisões sustentam isso:

**(a) O grão mínimo é IES, não grupo.** Grupo econômico é *atributo* de IES. Se os cubos forem
publicados no nível de IES, o navegador soma para grupo em milissegundos — e **editar
`ies_grupo_map.csv` passa a não exigir reprocessar nada**. O mesmo vale para município → UF →
região, e para rótulo CINE → área CINE. Isso elimina a explosão combinatória de cubos.

**(b) Séries históricas e detalhe do ano são arquivos diferentes.** As visões de evolução
precisam de 10 anos mas pouca granularidade; as visões de detalhe precisam de granularidade mas
de um ano só. Separar os dois evita carregar 10 anos de detalhe para desenhar uma linha do tempo.

**(c) Cruzamentos triplos ficam fora do navegador.** Medidos abaixo, custam 250 MB. Ficam
disponíveis via consulta DuckDB offline, não na interface.

## 2. Dimensionamento medido

Cubos candidatos, medidos sobre a base real (linhas com pelo menos uma métrica > 0):

| Cubo | Linhas/ano | 10 anos | JSON colunar (10 anos) | Destino |
|---|---|---|---|---|
| `ies × modalidade` | 3.196 | 31.960 | ~1,4 MB | 🟢 histórico, sempre carregado |
| `cine × modalidade` | 567 | 5.670 | ~0,2 MB | 🟢 histórico |
| `município × modalidade` | 4.553 | 45.530 | ~2,0 MB | 🟢 histórico |
| `cine × uf × modalidade` | 8.798 | 87.980 | ~3,8 MB | 🟢 histórico |
| `ies × cine × modalidade` | 35.989 | 359.890 | ~15,4 MB | 🟡 por ano (1,5 MB/ano) |
| `ies × município × modalidade` | 27.375 | 273.750 | ~11,7 MB | 🟡 por ano (1,2 MB/ano) |
| `cine × município × modalidade` | 204.829 | 2.048.290 | ~87,9 MB | 🟡 por ano, sob demanda |
| `ies × município × cine × modal.` | 582.592 | 5.825.920 | **~250 MB** | 🔴 só Parquet/DuckDB |

**Payload inicial do dashboard: ~8 MB** (histórico completo + dimensões + ano corrente).
Trocar de ano carrega ~3 MB adicionais. Isso é rápido em disco local.

Nota de eficiência: filtrar linhas com todas as métricas zeradas reduz a base de
**720.349 → 623.464 linhas** (−13%) sem qualquer perda de informação.

## 3. Estrutura de diretórios

```
C:\education\
├── data_raw/
│   └── 2024/                          ← um diretório por ano; zip original preservado
│       ├── microdados_...2024.zip
│       └── microdados_censo_da_educacao_superior_2024/
├── data_processed/
│   ├── fato_cursos_2024.parquet       ← microdados limpos e tipados (~35 MB vs 432 MB CSV)
│   ├── dim_ies_2024.parquet
│   └── cubos/                         ← cubos agregados, particionados por ano
├── scripts/
│   ├── 00_fetch_geo.py                ← centroides IBGE + malha (roda 1x)
│   ├── 01_ingest.py                   ← CSV → Parquet, tipagem, limpeza
│   ├── 02_build_dims.py               ← dimensões + join do mapeamento de grupos
│   ├── 03_build_cubes.py              ← agregações
│   ├── 04_export_web.py               ← Parquet → JSON colunar
│   ├── 05_validate.py                 ← relatório de validação
│   ├── build_ies_group_map.py         ← ✅ já implementado
│   └── lib/                           ← código compartilhado (regras de TP_DIMENSAO etc.)
├── config/
│   ├── ies_grupo_map.csv              ← ✅ EDITÁVEL: IES → mantenedora → grupo
│   ├── ies_grupo_map_nao_encontradas.csv  ← ✅
│   ├── grupos.csv                     ← metadados do grupo (ticker, listada, cor)
│   ├── codigos.json                   ← ✅ tradução de códigos INEP
│   ├── cursos_destaque.json           ← cursos priorizados na visão de curso
│   ├── municipios_ibge.csv            ← centroides (gerado por 00_fetch_geo.py)
│   └── inep_dicionario_2024.json      ← ✅ dicionário completo extraído
├── dashboard/
│   ├── index.html
│   ├── css/, js/, vendor/             ← bibliotecas vendorizadas (offline)
│   └── data/                          ← JSONs gerados; nunca editar à mão
├── outputs/
│   ├── validation_report_2024.md
│   └── exports/                       ← CSV/XLSX exportados pela interface
├── docs/                              ← ✅ esta documentação
├── update_dashboard.py                ← orquestrador único
└── README.md
```

## 4. Pipeline

```
data_raw/{ano}/*.zip
   │
   ├─ 01_ingest.py     descompacta · lê em latin-1 · aplica TP_DIMENSAO · trim das aspas de
   │                   CO_CINE_ROTULO · preserva zeros à esquerda · descarta linhas zeradas
   │                   · seleciona ~40 das 223 colunas         →  fato_cursos_{ano}.parquet
   │
   ├─ 02_build_dims.py dim_ies (+ GRUPO via config) · dim_curso_cine · dim_municipio (+ lat/lon)
   │                   · dim_grupo                             →  dim_*.parquet
   │
   ├─ 03_build_cubes.py os 7 cubos verdes/amarelos da §2       →  cubos/*.parquet
   │
   ├─ 04_export_web.py JSON colunar + dicionário de strings    →  dashboard/data/*.json
   │
   └─ 05_validate.py   checklist de §10 do relatório de qualidade
                                                               →  outputs/validation_report_{ano}.md
```

Orquestrado por `update_dashboard.py --ano 2025`. Idempotente: reprocessar o mesmo ano
sobrescreve sem efeito colateral.

**Atalho importante:** como grupo é atributo de IES, alterar `ies_grupo_map.csv` exige apenas
`update_dashboard.py --apenas-grupos`, que roda só as etapas 02 e 04 (segundos, sem tocar nos
microdados).

### Formato de saída

JSON **colunar** com dicionário de strings, não array de objetos:

```json
{"cols":["ies","cine","mod","mat","ing","conc"],
 "ies":[298,298,...], "cine":[12,45,...], "mod":[2,1,...],
 "mat":[8421,331,...], "ing":[...], "conc":[...]}
```

Reduz ~60% do tamanho e evita o custo de parse de centenas de milhares de objetos.

### Como o dashboard é servido

`run_dashboard.py` sobe um servidor estático local e abre o navegador — um comando. Isso é
necessário porque `fetch()` de arquivos locais é bloqueado ao abrir HTML por `file://`, e traz
de brinde gzip, cache e carregamento sob demanda. Como efeito colateral desejável, o dashboard
fica **pronto para publicação em qualquer host estático** quando virar material de investidor.

Adicionalmente, `04_export_web.py --standalone` gera um `dashboard_standalone.html` de arquivo
único, com os cubos do ano corrente embutidos — para enviar por e-mail ou apresentar sem
servidor. Sem histórico completo, para não estourar o tamanho.

## 5. Stack

| Camada | Escolha | Motivo |
|---|---|---|
| Processamento | **Python + DuckDB** | DuckDB lê o CSV de 432 MB e agrega em segundos, com SQL legível. Já instalado |
| Armazenamento intermediário | **Parquet** | ~12× menor que CSV, tipado, leitura por coluna |
| Interface | **HTML + JS vanilla (ES modules), sem build** | Sem `npm`, sem transpilação, sem apodrecimento de dependências. Abre daqui a 3 anos |
| Gráficos e mapa | **ECharts** (vendorizado) | Único pacote cobre linhas, barras, treemap, scatter **e mapa coroplético** com GeoJSON. Tooltips de qualidade |
| Tabelas | **Tabulator** (vendorizado) | Ordenação, filtro e scroll virtual — necessário para o Campus Explorer (3.793 linhas) |

Sem CDN: tudo vendorizado em `dashboard/vendor/` para funcionar offline.

## 6. Geografia

Não há latitude/longitude na base. `00_fetch_geo.py` resolve isso uma única vez (API do IBGE já
testada e acessível):

- **Centroides de município** → `config/municipios_ibge.csv` (5.570 registros) para o mapa de
  bolhas de unidades.
- **Malha de UF** (GeoJSON simplificado) → coroplético por estado.
- Malha de município fica **fora** por padrão (~10 MB); coroplético municipal só se houver
  demanda, carregado sob demanda por UF.

Hierarquia Brasil → Região → UF → Município é derivada em memória a partir do código IBGE.
O nível "Campus" é o proxy IES × município descrito no relatório de qualidade.

## 7. Regras de negócio codificadas no pipeline

Centralizadas em `scripts/lib/regras.py`, uma fonte única de verdade:

| Regra | Implementação |
|---|---|
| Alunos | `TP_DIMENSAO IN (1,2,4)` |
| Cursos, vagas, inscritos | `TP_DIMENSAO IN (1,3)` |
| Recortes geográficos | `TP_DIMENSAO IN (1,2)` |
| Unidade/campus (proxy) | `COUNT(DISTINCT CO_IES, CO_MUNICIPIO)` com `TP_DIMENSAO=1` |
| Municípios EAD (proxy de polos) | `COUNT(DISTINCT CO_MUNICIPIO)` com `TP_DIMENSAO=2` |
| Curso | `NO_CINE_ROTULO` (nunca `NO_CURSO`) |
| Grupo | join com `ies_grupo_map.csv`; sem grupo → **"Independentes"**, sempre visível |
| Sem geografia | bucket **"Exterior / N.I."**, nunca descartado |
| Market share | denominador **explícito** em cada visão (nacional, da modalidade, do curso, da UF) |

Toda tela exibe o denominador usado. Um share sem denominador declarado é fonte de erro de
leitura em material de investidor.

## 8. Indicadores

Calculados no **navegador**, a partir dos cubos, para reagirem a filtros:

- **Share**: nacional · por modalidade · por curso · por UF · por município
- **Concentração**: Top 3 / Top 5 / Top 10 · HHI — sempre com o universo declarado
- **Crescimento** (quando houver histórico): YoY · CAGR · Δ share em p.p.
- **Mix**: EAD/presencial · por curso · geográfico · por grau acadêmico
- **Escala**: alunos/unidade · alunos/IES · cursos/unidade · alunos/docente
- **Funil**: vagas → inscritos → ingressantes (taxa de preenchimento e de conversão)
- **Dependência de funding**: % FIES · % ProUni · % financiamento privado

Referências já calculadas para 2024: Top 3 IES = 18,7% · Top 5 = 25,7% · Top 10 = 34,0% ·
Top 20 = 41,2% do mercado.

## 9. Insights automáticos

`Key Insights` é gerado por **regras determinísticas**, não por texto livre. Cada insight é um
objeto com o número, o denominador e o período — a frase é só a renderização:

```
{ tipo: "share_gain", entidade: "Grupo X", valor: +0.8, unidade: "p.p.",
  base: "market share nacional", de: 2023, para: 2024,
  evidencia: { mat_2023: ..., mat_2024: ..., mercado_2023: ..., mercado_2024: ... } }
```

Regras: ganho/perda de share acima de um limiar · crescimento acima do mercado · aceleração de
EAD · variação de HHI · entrada em novos municípios · mudança de mix de curso. Cada card mostra
os números que o sustentam e um link para a visão detalhada. **Sem histórico, a seção exibe
apenas insights estruturais de 2024** (concentração, mix, exposição), não de crescimento.

## 10. Sequência de entrega

| Etapa | Escopo | Estado |
|---|---|---|
| **1** | Exploração, data dictionary, qualidade, arquitetura, mapeamento de grupos | ✅ concluída |
| **2** | `01_ingest` → `05_validate`, cubos, relatório de validação | a aprovar |
| **3** | MVP: Overview · Groups · Courses · Geography · Rankings · filtros · Methodology | a aprovar |
| **4** | Histórico · Comparação de players · Investor Snapshot · Key Insights · IES detail · Campus Explorer | a aprovar |

A página *Methodology & Data Notes* entra já na Etapa 3, não no fim: ela é o que torna a
ferramenta distribuível.

## 11. Decisões que dependem de você

1. **Players não cobertos.** UNINTER (286 mil), UNIP (260 mil) e UNINOVE (163 mil) somam 6,9% do
   mercado e hoje não têm grupo. Entram no `Suporte IES.xlsx` ou permanecem em "Independentes"?
2. **Histórico.** Quais anos baixar (sugestão: 2015–2024) e quando. O layout mudou em 2022
   (`CO_CURSO`, `TP_DIMENSAO` foram criados) — anos anteriores exigem tratamento adicional.
3. **Grupo no histórico.** *Pro-forma* (perímetro atual aplicado a todos os anos, melhor para ler
   share) ou *as-reported* (perímetro vigente em cada ano)? Recomendação: **pro-forma**.
4. **4 IES sugeridas** por mantenedora (§7.4 do relatório de qualidade): confirmar inclusão.
