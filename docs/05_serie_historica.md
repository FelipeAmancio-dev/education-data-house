# Série histórica 2015–2024

> O que a série permite ler, o que ela **não** permite, e as duas armadilhas que
> encontramos ao montá-la. Gerado após a ingestão completa dos 10 anos.

## 1. A série é comparável — melhor do que eu havia previsto

Na Etapa 1 alertei que `TP_DIMENSAO`, `CO_CURSO` e `NO_CURSO` tinham sido "criados em 2022"
(conforme a Nota Informativa do INEP) e que os anos anteriores exigiriam tratamento adicional.
**Verificado empiricamente: esse alerta estava errado.** O INEP republicou toda a série no
layout unificado, e as três variáveis existem em todos os arquivos de 2015 a 2024.

Núcleo do dashboard, disponibilidade por ano:

| Campo | 2015–2024 |
|---|---|
| `NU_ANO_CENSO`, `CO_IES`, `CO_CURSO`, `NO_CURSO` | ✅ todos |
| `TP_DIMENSAO` | ✅ todos |
| `TP_MODALIDADE_ENSINO`, `TP_REDE`, `TP_NIVEL_ACADEMICO`, `TP_GRAU_ACADEMICO` | ✅ todos |
| `NO_CINE_ROTULO`, `CO_CINE_AREA_GERAL` | ✅ todos |
| `CO_MUNICIPIO`, `CO_UF`, `CO_REGIAO` | ✅ todos |
| `QT_MAT`, `QT_ING`, `QT_CONC`, `QT_CURSO`, `QT_VG_TOTAL`, `QT_SIT_TRANCADA` | ✅ todos |

### Ajustes de layout tratados no pipeline

| Ano | O que muda | Tratamento |
|---|---|---|
| 2020 | `CO_CINE_ROTULO` aparece como **`CO_CINE_ROTULO2`** | Renomeado na ingestão (`lib/censo.py::RENOMEAR`) |
| 2015–2022 | **`TP_REDE` não existe na tabela IES** (só a partir de 2023) | Derivado de `TP_CATEGORIA_ADMINISTRATIVA`. Mapeamento validado em 2023/2024, onde as duas colunas coexistem: categorias 1, 2, 3 e **7** → Pública; 4 e 5 → Privada. A categoria 7 ("Especial") mapear para *pública* é contraintuitivo e por isso está explicitado em `lib/censo.py::CATEGORIA_PUBLICA` |
| 2021 | Tabela IES ganha `CO_LOCAL_OFERTA` / `NO_LOCAL_OFERTA` | **Investigado e descartado**: são 2.574 linhas para 2.574 IES, ou seja, o local da *sede*, não a lista de campi. Não resolve a limitação de campus |
| 2023 | Entram `IN_COMUNITARIA`, `IN_CONFESSIONAL` | Fora do núcleo; não afeta a série |
| 2024 | `QT_*_RVETNICO` é substituído por colunas granulares de reserva de vagas | Fora do núcleo; não afeta a série |
| 2022 | Linhas de dimensão 3 e 4 vêm com `CO_UF` preenchido (não deveriam ter geografia) | **Sem impacto**: os cubos geográficos usam apenas dimensões 1 e 2. Registrado como alerta na validação |

## 2. A série nacional

| Ano | Matrículas | Presencial | EAD | % EAD | Privada | % Priv. | Ingressantes | Cursos | IES |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2015 | 8.033.574 | 6.639.794 | 1.393.780 | 17,3% | 6.080.989 | 75,7% | 2.922.400 | 33.607 | 2.364 |
| 2016 | 8.052.254 | 6.557.827 | 1.494.427 | 18,6% | 6.061.756 | 75,3% | 2.986.636 | 34.440 | 2.407 |
| 2017 | 8.290.911 | 6.531.661 | 1.759.250 | 21,2% | 6.242.825 | 75,3% | 3.226.906 | 35.443 | 2.448 |
| 2018 | 8.451.748 | 6.395.189 | 2.056.559 | 24,3% | 6.373.913 | 75,4% | 3.446.328 | 38.007 | 2.537 |
| 2019 | 8.604.526 | 6.154.261 | 2.450.265 | 28,5% | 6.524.108 | 75,8% | 3.633.644 | 40.463 | 2.608 |
| 2020 | 8.680.945 | 5.575.142 | 3.105.803 | 35,8% | 6.724.339 | 77,5% | 3.765.669 | 41.978 | 2.457 |
| 2021 | 8.987.120 | 5.270.750 | 3.716.370 | 41,4% | 6.908.214 | 76,9% | 3.945.091 | 43.102 | 2.574 |
| 2022 | 9.444.116 | 5.113.182 | 4.330.934 | 45,9% | 7.367.363 | 78,0% | 4.756.957 | 44.960 | 2.595 |
| 2023 | 9.977.217 | 5.063.936 | 4.913.281 | 49,2% | 7.907.851 | 79,3% | 4.994.192 | 45.964 | 2.580 |
| 2024 | **10.227.266** | **5.037.875** | **5.189.391** | **50,7%** | 8.162.199 | 79,8% | 5.010.613 | 45.776 | 2.561 |

Três fatos estruturais que a série mostra:

1. **O presencial encolhe em termos absolutos**: 6,64 M → 5,04 M, **−24%** em 10 anos. O
   crescimento do setor (+27% no total) é inteiramente EAD.
2. **O EAD triplica de participação**: 17,3% → 50,7%, ultrapassando o presencial em 2024.
3. **O número de IES cai desde 2019** (2.608 → 2.561) enquanto o de cursos cresce — consolidação
   institucional com expansão de oferta.

## 3. Market share por grupo (perímetro pro-forma, base `QT_MAT`)

| Grupo | 2015 | 2018 | 2021 | 2023 | 2024 | Δ 2015→2024 |
|---|---:|---:|---:|---:|---:|---:|
| **Vitru** | 2,07% | 3,79% | 9,14% | 11,91% | 10,56% | **+8,49 p.p.** |
| **Cruzeiro do Sul** | 2,15% | 3,24% | 4,03% | 4,64% | 5,01% | **+2,86 p.p.** |
| **YDUQS** | 6,38% | 6,54% | 8,59% | 8,59% | 8,06% | +1,68 p.p. |
| **Ser Educacional** | 2,51% | 2,64% | 2,84% | 2,79% | 3,67% | +1,16 p.p. |
| **Cogna** | 10,82% | 9,52% | 9,59% | 10,37% | 10,99% | +0,17 p.p. |
| **Ânima** | 3,71% | 3,75% | 3,66% | 3,76% | 3,25% | −0,46 p.p. |
| **Afya** | 1,14% | 1,01% | 0,90% | 0,83% | 0,91% | −0,23 p.p. |

Leitura: a Vitru é o movimento dominante da década — 5× de ganho de participação, quase todo
via EAD. A Cogna passou por um vale (9,21% em 2019) e recuperou. Afya perde share em volume
porque seu negócio é medicina — alto valor, baixo volume; share de matrícula é a métrica errada
para avaliá-la isoladamente.

> **Pro-forma:** o perímetro atual dos grupos é aplicado a toda a série. Uma IES adquirida em
> 2022 já conta no grupo comprador desde 2015. É o que permite ler evolução de share sem
> degraus artificiais de M&A — mas significa que estes números **não** são o que cada empresa
> reportava à época.

## 4. ⚠️ Armadilha 1: reclassificação de trancados contamina o crescimento

Esta é a descoberta mais importante da série, e ela **muda como certos anos devem ser lidos**.

A taxa de trancamento (trancados ÷ matrículas) não é estável ao longo do tempo para vários
grupos:

| Grupo | 2015 | 2017 | 2019 | 2021 | 2022 | 2023 | 2024 | Amplitude |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **YDUQS** | 39% | 44% | 37% | 46% | 62% | 66% | 54% | **35 p.p.** |
| **Ânima** | 16% | 24% | 30% | 42% | 34% | 15% | 14% | **28 p.p.** |
| **Ser Educacional** | 12% | 26% | 22% | 36% | 11% | 8% | 10% | **27 p.p.** |
| Afya | 14% | 18% | 21% | 25% | 21% | 28% | 34% | 20 p.p. |
| Cogna | 23% | 12% | 11% | 9% | 10% | 13% | 13% | 14 p.p. |
| **Cruzeiro do Sul** | 10% | 8% | 8% | 6% | 9% | 6% | 6% | **4 p.p.** |
| **Vitru** | 4% | 1% | 3% | 0% | 0% | 1% | 1% | **4 p.p.** |

O teste decisivo é comparar o crescimento de `QT_MAT` com o da base de alunos
(`QT_MAT` + trancados). Se divergem muito, o movimento é **reclassificação de vínculo**, não
aluno entrando ou saindo:

| Grupo | Ano | YoY `QT_MAT` | YoY base | Divergência |
|---|---:|---:|---:|---:|
| **Ser Educacional** | 2022 | +0,4% | **−18,0%** | **+18,4 p.p.** |
| **Ânima** | 2023 | +1,5% | **−12,7%** | **+14,2 p.p.** |

Em ambos os casos a base de alunos **despencou** enquanto as matrículas ficaram estáveis — ou
seja, um contingente grande de alunos trancados saiu da base sem que as matrículas caíssem.
Ler esses anos como "grupo se manteve estável" é errado; a base real encolheu com força.

O caso inverso é a **YDUQS em 2021–2022**: `QT_MAT` praticamente parado (+3,9% e +0,3%) enquanto
a base crescia 15,7% e 11,9%. O grupo estava acumulando trancados — o crescimento real da base
estava sendo mascarado pelo `QT_MAT` estável.

**Vitru e Cruzeiro do Sul são as duas séries limpas** (amplitude de 4 p.p.): para elas,
`QT_MAT` e base de alunos contam a mesma história, e o crescimento é real.

### Regra adotada

Nas visões de evolução histórica, o dashboard vai:

1. exibir **as duas séries** (`QT_MAT` e base de alunos) para qualquer grupo selecionado;
2. **marcar visualmente** os anos em que as duas divergem mais de 12 p.p.;
3. nunca gerar um insight automático de crescimento/queda em um ano marcado sem exibir as duas
   séries lado a lado.

O check é permanente: `scripts/03_validate.py` §5b recalcula isso a cada build e emite alerta.

## 5. ⚠️ Armadilha 2: a Vitru mudou o próprio critério em 2024

Já documentado em [`04_reconciliacao_companhias.md`](04_reconciliacao_companhias.md), mas o
efeito aparece na série: a Vitru cai **−9,1%** em matrículas em 2024 (1,19 M → 1,08 M) e perde
1,35 p.p. de share, depois de nove anos de crescimento ininterrupto.

Isso coincide com a limpeza de base de alunos "não engajados" que a empresa descreve no release
de 4Q24. A queda de 2024 da Vitru provavelmente **não é perda de mercado** — é depuração de
base. Diferente das armadilhas do item 4, aqui `QT_MAT` e base caem juntas (−9,1% e −9,0%), o
que sugere que a depuração chegou até a declaração ao Censo.

## 6. O que a série **não** permite

- **Comparar campi ao longo do tempo** — não há identificador de campus em nenhum ano
  (confirmado inclusive para 2021, que tem `CO_LOCAL_OFERTA` mas só da sede).
- **Reconstruir o perímetro histórico real dos grupos** — a decisão foi pro-forma. Para
  *as-reported* seria preciso um mapeamento com `ANO_INICIO`/`ANO_FIM` por IES, que não temos.
- **Comparar com releases de empresa sem ajuste** — ver `04_reconciliacao_companhias.md`.
- **Analisar pós-graduação, cursos livres ou ensino técnico** — fora do Censo em todos os anos.

## 7. Volumetria do pipeline

| Etapa | Volume |
|---|---|
| ZIPs originais (10 anos) | 871 MB |
| CSV descompactado equivalente | ~2,0 GB |
| **Parquet de microdados** | **39,9 MB** (50× menor) |
| **Cubos agregados** | **6,4 MB** |
| Tempo total de ingestão | ~1,5 min |
| Tempo de construção dos cubos | 2,6 s |

Os 6,4 MB de cubos são o que o dashboard efetivamente consome — abaixo do orçamento de ~8 MB
projetado na arquitetura.
