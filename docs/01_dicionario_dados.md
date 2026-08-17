# Data Dictionary — Censo da Educação Superior 2024

> Documento da **Etapa 1**. Cobre apenas os campos que serão efetivamente usados no dashboard.
> O dicionário completo do INEP (316 variáveis) está extraído em `docs/inep_dicionario_2024.csv`
> e `config/inep_dicionario_2024.json`.
>
> **Regra adotada:** nenhum campo foi interpretado pelo nome. Toda leitura abaixo foi validada
> contra o *ANEXO I – Dicionário de Dados* do INEP e conferida empiricamente contra os dados.
> Onde a documentação é ambígua, a interpretação usada está marcada com **[INTERPRETAÇÃO]**.

---

## 1. Fonte e arquivos

| Item | Valor |
|---|---|
| Fonte | INEP — Microdados do Censo da Educação Superior 2024 |
| Publicação | Setembro/2025 (Manual do Usuário) |
| Ano de referência | 2024 (`NU_ANO_CENSO` = 2024 em 100% das linhas) |
| Encoding | **latin-1 / ISO-8859-1** (não é UTF-8) |
| Separador | `;` |
| Decimal | não aplicável — todas as métricas são inteiras |

| Arquivo | Tamanho | Linhas | Colunas | Grão |
|---|---|---|---|---|
| `MICRODADOS_CADASTRO_CURSOS_2024.CSV` | 431,9 MB | 720.349 | 223 | curso × dimensão geográfica × município |
| `MICRODADOS_ED_SUP_IES_2024.CSV` | 1,0 MB | 2.561 | 84 | 1 linha por IES |

Anexos: dicionário de dados (`.xlsx`), 4 questionários (`.pdf`), `Leia_me.pdf`, `Nota informativa.pdf`.

**Não existe** arquivo de aluno, de docente individualizado, nem de local de oferta/campus.

---

## 2. O campo mais importante: `TP_DIMENSAO`

Este é o campo que determina **quais métricas podem ser somadas em cada linha**. Interpretá-lo
errado produz dupla contagem de ~5,2 milhões de matrículas EAD.

| Código | Significado | Linhas | Tem geografia? | Métricas válidas na linha |
|---|---|---|---|---|
| 1 | Cursos **presenciais** ofertados no Brasil | 34.824 | Sim (município) | **todas** |
| 2 | Cursos **EAD** ofertados no Brasil | 673.756 | Sim (município) | **apenas** matrículas, ingressantes, concluintes |
| 3 | Cursos **EAD**, dimensão só a nível Brasil | 11.319 | Não (nulo) | **apenas** nº de cursos, vagas, inscritos |
| 4 | Cursos **EAD** por IES brasileira no exterior | 450 | Não (nulo) | matrículas, ingressantes, concluintes |

Comprovação empírica (soma das colunas por dimensão):

| TP_DIMENSAO | QT_CURSO | QT_VG_TOTAL | QT_ING | QT_MAT | QT_CONC |
|---|---|---|---|---|---|
| 1 | 34.479 | 5.075.146 | 1.663.040 | 5.037.875 | 729.246 |
| 2 | **0** | 6.925 | 3.346.116 | 5.186.852 | 604.269 |
| 3 | 11.297 | 18.583.348 | **0** | **0** | **0** |
| 4 | 0 | 0 | 1.457 | 2.539 | 473 |

Dimensões 2 e 3 são **visões complementares do mesmo curso EAD**, não linhas independentes:
10.798 cursos aparecem em ambas. A dimensão 3 traz o cadastro (curso/vagas), a dimensão 2 traz
os alunos distribuídos geograficamente. Isso é confirmado pela *Nota Informativa* do INEP:

> "para os cursos a distância não é possível quantificar o número de cursos, vagas e inscritos
> por Regiões Geográficas, Unidades da Federação e Municípios."

### Regras de agregação obrigatórias

```
Alunos (matrículas, ingressantes, concluintes)  ->  WHERE TP_DIMENSAO IN (1, 2, 4)
Cursos, vagas e inscritos                       ->  WHERE TP_DIMENSAO IN (1, 3)
Recortes geográficos                            ->  WHERE TP_DIMENSAO IN (1, 2)
```

**[INTERPRETAÇÃO]** Na dimensão 2 o município é descrito pelo INEP como *"local de oferta do
curso"*. Para EAD, entendemos como **município do polo de apoio presencial ao qual o aluno está
vinculado**, e não o município de residência do aluno. Consequência prática: a geografia EAD
mede *presença/captação por polo*, não domicílio do estudante. Isso será declarado na página
*Methodology* do dashboard.

---

## 3. Campos de identificação

### 3.1 IES, mantenedora e grupo

| Campo | Tabela | Tipo | Descrição validada | Observação |
|---|---|---|---|---|
| `CO_IES` | ambas | int | Código único da IES | **Chave de join entre as duas tabelas.** 2.561 IES, cobertura 100% nos dois sentidos (0 órfãos) |
| `NO_IES` | IES | texto | Nome da IES | |
| `SG_IES` | IES | texto | Sigla | **459 nulos (17,9%)** — não usar como rótulo primário |
| `CO_MANTENEDORA` | IES | int | Código da mantenedora (entidade jurídica) | 1.755 mantenedoras |
| `NO_MANTENEDORA` | IES | texto | Nome da mantenedora | 1.741 nomes distintos para 1.755 códigos → há nomes repetidos entre CNPJs diferentes; **usar sempre o código** |
| `GRUPO` | `config/ies_grupo_map.csv` | texto | Grupo econômico | Campo **nosso**, não do INEP. Ver §6 |

Hierarquia real na base: `CO_MANTENEDORA` (1) → (N) `CO_IES` → (N) `CO_CURSO`.
O **grupo econômico não existe no Censo** e precisa ser adicionado por mapeamento externo.

### 3.2 Curso

| Campo | Tipo | Descrição validada | Observação |
|---|---|---|---|
| `CO_CURSO` | int | Código único do curso | 46.150 cursos. **Único globalmente** — nenhum código pertence a mais de uma IES |
| `NO_CURSO` | texto | Nome livre dado pela IES | 1.497 nomes distintos. **Não usar para agrupar** |
| `CO_CINE_ROTULO` | texto | Código CINE/UNESCO do curso | 353 rótulos. **Vem com aspas duplas literais no CSV** (`"0011A01"`) — precisa `trim('"')` |
| `NO_CINE_ROTULO` | texto | Nome padronizado do curso | **Este é o campo correto para "curso"** (Medicina, Direito, Pedagogia…) |
| `CO_CINE_AREA_GERAL` | **texto** | Área geral CINE (11 valores) | **Texto com zero à esquerda** (`"00"`,`"01"`) — ler como VARCHAR |
| `NO_CINE_AREA_GERAL` | texto | Nome da área geral | |
| `NO_CINE_AREA_ESPECIFICA` / `NO_CINE_AREA_DETALHADA` | texto | Níveis intermediários (89 áreas detalhadas) | |

Exemplo do ganho de padronização: sob o rótulo CINE *Administração* existem 7 nomes livres
distintos e 2.179 cursos; *Medicina* tem 1 nome livre e 467 cursos.

### 3.3 Geografia

| Campo | Tabela | Descrição | Observação |
|---|---|---|---|
| `CO_MUNICIPIO` / `NO_MUNICIPIO` | Cursos | Município do **local de oferta** | Código IBGE de 7 dígitos em 100% dos casos; 0 divergências de nome por código. 3.551 municípios |
| `CO_UF` / `SG_UF` / `NO_UF` | Cursos | UF do local de oferta | |
| `CO_REGIAO` / `NO_REGIAO` | Cursos | Região | |
| `IN_CAPITAL` | Cursos | Local de oferta é capital | Nulo quando EAD sem dimensão |
| `*_IES` (ex. `SG_UF_IES`) | IES | Geografia da **sede/reitoria**, não dos campi | Não confundir com a geografia de oferta |
| `DS_ENDERECO_IES`, `NU_CEP_IES` | IES | Endereço **da sede apenas** | 26 CEPs nulos |

**Não há latitude/longitude em nenhuma das tabelas.** Ver §5.

### 3.4 Classificação institucional

`TP_REDE` (Pública/Privada), `TP_CATEGORIA_ADMINISTRATIVA` (6 valores presentes),
`TP_ORGANIZACAO_ACADEMICA` (Universidade/Centro Universitário/Faculdade/IF/CEFET),
`TP_MODALIDADE_ENSINO` (Presencial/EAD), `TP_NIVEL_ACADEMICO` (Graduação/Sequencial),
`TP_GRAU_ACADEMICO` (Bacharelado/Licenciatura/Tecnológico), `IN_GRATUITO`.

Traduções completas em `config/codigos.json`.

---

## 4. Campos de métrica

Das 193 colunas `QT_*` da tabela de cursos, o dashboard usa **6 como núcleo** e um subconjunto
como apoio analítico. As demais (recortes por cor/raça, faixa etária, sexo, reserva de vagas,
deficiência, mobilidade) não respondem a perguntas de investimento e ficam fora.

### Núcleo

| Campo | Definição **oficial** do INEP | Uso |
|---|---|---|
| `QT_MAT` | "soma do número de alunos com situação de vínculo ao curso igual a **Cursando e/ou Formado**" | Base de tamanho de mercado e market share |
| `QT_ING` | "soma do número de alunos com data de ingresso de **01 de janeiro e 01 de julho** do ano de referência" | Proxy de captação/intake do ano |
| `QT_CONC` | Quantidade de concluintes | Saída da base / renovação |
| `QT_CURSO` | Número de cursos | Contagem de oferta (**só dims 1 e 3**) |
| `QT_VG_TOTAL` | Quantidade total de vagas oferecidas | Capacidade instalada |
| `QT_INSCRITO_TOTAL` | Inscritos nos processos seletivos | Demanda; base para vagas/inscrito |

> ⚠️ `QT_MAT` **inclui alunos com vínculo "Formado"**. Não é estritamente "aluno pagante ativo".
> Para leitura de base ativa, considerar líquido de `QT_CONC`. Registrar isso na *Methodology*.
>
> ⚠️ `QT_ING` conta ingressos em **duas datas de corte** (jan e jul), não é fluxo contínuo.

### Apoio (com utilidade analítica clara)

| Campo | Pergunta de investidor que responde |
|---|---|
| `QT_MAT_FIES`, `QT_MAT_PROUNII`, `QT_MAT_PROUNIP` | Qual a dependência de financiamento público do grupo? |
| `QT_MAT_FINANC_REEMB_OUTROS` | Qual o peso do financiamento próprio (PRAVALER/carteira própria)? |
| `QT_MAT_NOTURNO` / `QT_MAT_DIURNO` | Perfil do aluno (trabalhador) e utilização do ativo |
| `QT_SIT_TRANCADA`, `QT_SIT_DESVINCULADO` | Proxy de evasão/churn |
| `QT_VG_TOTAL` vs `QT_ING` | Taxa de preenchimento de vagas (ociosidade) |

### Tabela de IES — campos usados

`QT_DOC_TOTAL`, `QT_DOC_EXE` (docentes em exercício), `QT_DOC_EX_DOUT/MEST` (titulação),
`QT_DOC_EX_INT_DE` (regime integral) e `QT_TEC_TOTAL` (técnico-administrativos).
Uso: **alunos por docente** — proxy direto de eficiência operacional e margem. As demais
colunas de docente (cor/raça, faixa etária, nacionalidade) e de biblioteca ficam fora.

---

## 5. O que **não** existe na base

Limitações estruturais que definem o teto do que o dashboard pode entregar:

| Ausência | Impacto | Mitigação adotada |
|---|---|---|
| **Identificador de campus / local de oferta** | Impossível contar campi de verdade | **Proxy: pares distintos (`CO_IES`,`CO_MUNICIPIO`) na dim. 1** → 3.793 unidades presenciais no país. Um grupo com 3 campi na mesma cidade conta como 1 |
| **Latitude/longitude** | Sem mapa de pontos | Centroides de município via API IBGE (`config/municipios_ibge.csv`, gerado uma vez) + choropleth por UF/município |
| **Endereço dos campi** | Só existe endereço da sede | Campus Explorer terá município/UF, sem endereço |
| **Número de polos EAD** | Não é possível contar polos | Proxy: municípios distintos com matrícula EAD por IES |
| **Preço / ticket / receita** | Nenhum dado financeiro | Fora de escopo — dashboard mede **volume e share**, não receita |
| **Grupo econômico** | Não existe no Censo | Mapeamento manual (`config/ies_grupo_map.csv`) |
| **Dados de aluno/docente individualizados** | — | Não publicados por LGPD (só via SEDAP) |

---

## 6. Arquivo de suporte — `Suporte IES.xlsx`

| Item | Valor |
|---|---|
| Aba | `Sheet1`, **cabeçalho na linha 2** (linha 1 vazia) |
| Colunas | `IES Code`, `IES`, `City`, `State`, `Company` |
| Linhas | 423 |
| CO_IES únicos | **416** |
| Grupos | Cogna, Ânima, YDUQS, Ser Educacional, Afya, Vitru, Cruzeiro do Sul |

Validações realizadas:

- ✅ Sem valores nulos; `IES Code` 100% numérico
- ✅ 0 conflitos: nenhum `CO_IES` aparece com dois grupos diferentes
- ✅ 0 divergências de UF contra o Censo
- ✅ 0 IES mapeadas que sejam públicas (nenhum erro de classificação)
- ✅ Nenhuma mantenedora aparece em mais de um grupo
- ⚠️ **7 linhas duplicadas** (5 `CO_IES`): o arquivo lista alguns *campi* separadamente
  (UNAMA 383 aparece 6×, UNG 481 2×, UNIGRANRIO 472 2×). O Censo não tem código de campus,
  então esses campi compartilham o mesmo `CO_IES`. **Somar sem deduplicar infla o mercado em
  235.518 matrículas** (10,46 M em vez de 10,23 M).
- ⚠️ **21 `CO_IES` não existem no Censo 2024** (IES extintas, incorporadas ou com código
  alterado) — listados em `config/ies_grupo_map_nao_encontradas.csv`

O mapeamento consolidado e editável foi gerado em **`config/ies_grupo_map.csv`** (`;`, UTF-8-BOM),
contendo **todas as 2.561 IES** — basta preencher a coluna `GRUPO` para incorporar novos players.
A coluna `GRUPO_SUGERIDO` traz inferência automática por mantenedora (apoio, nunca sobrescreve).

---

## 7. Números de referência validados — 2024

Estes valores são o **gabarito de validação**: qualquer agregação do dashboard deve reproduzi-los.

| KPI | Valor |
|---|---|
| Matrículas | **10.227.266** |
| Ingressantes | **5.010.613** |
| Concluintes | **1.333.988** |
| Cursos | **45.776** |
| Vagas ofertadas | **23.658.494** |
| IES | **2.561** |
| Unidades presenciais (proxy IES×município) | **3.793** |
| Municípios com oferta | **3.551** |

| Recorte | Matrículas | % |
|---|---|---|
| Presencial | 5.037.875 | 49,3% |
| **EAD** | **5.189.391** | **50,7%** |
| Pública | 2.065.067 | 20,2% |
| **Privada** | **8.162.199** | **79,8%** |

Checagens de fechamento: presencial + EAD = total ✅ · soma das UFs + sem-UF (2.580, exterior)
= total ✅ · soma das regiões = total ✅

**Marco setorial de 2024: o EAD ultrapassou o presencial pela primeira vez.**
