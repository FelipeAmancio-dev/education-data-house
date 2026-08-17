# Relatório de Qualidade de Dados — Censo 2024

> Etapa 1. Todos os testes abaixo foram executados sobre a base completa (720.349 linhas),
> não sobre amostra. Scripts de exploração em `scripts/_explore_*.py`.

## Resumo

| Dimensão | Veredito |
|---|---|
| Integridade referencial | ✅ Perfeita |
| Duplicidade nos microdados | ✅ Nenhuma |
| Completude dos campos-chave | ✅ Alta |
| Consistência de nomenclatura | ✅ Alta |
| Consistência aritmética | ✅ Fecha |
| Arquivo de suporte de grupos | ⚠️ 2 problemas corrigíveis |
| Granularidade de campus | ⚠️ Limitação estrutural |

**Conclusão: a base é de qualidade alta e está pronta para produção.** Os riscos reais não são
de sujeira de dados, e sim de **interpretação** (`TP_DIMENSAO`) e de **cobertura do mapeamento
de grupos**.

---

## 1. Integridade referencial ✅

| Teste | Resultado |
|---|---|
| `CO_IES` em Cursos sem correspondência em IES | **0** |
| `CO_IES` em IES sem nenhum curso | **0** |
| `CO_IES` nulo | 0 |
| `CO_CURSO` nulo | 0 |
| `CO_CURSO` pertencente a >1 IES | **0** (46.150 cursos, todos com exatamente 1 IES) |

O join `Cursos → IES` por `CO_IES` é 1:N puro, sem perda nos dois sentidos.

## 2. Duplicidade ✅

| Teste | Resultado |
|---|---|
| Linhas totais | 720.349 |
| Combinações distintas (`CO_CURSO`,`TP_DIMENSAO`,`CO_MUNICIPIO`) | **720.349** |

A chave primária é exatamente essa tripla — **zero duplicatas**. Na dimensão 1, cada `CO_CURSO`
aparece 1 única vez (34.824 linhas = 34.824 cursos), ou seja, **um curso presencial existe em
apenas um município**.

> ⚠️ **O risco de dupla contagem não vem de duplicatas, e vem de `TP_DIMENSAO`.** Somar
> ingenuamente `QT_CURSO` sobre tudo, ou somar `QT_MAT` incluindo a dimensão 3, produz números
> errados. Ver `docs/01_dicionario_dados.md` §2.

## 3. Completude

### Tabela de Cursos

| Campo | Nulos | % | Diagnóstico |
|---|---|---|---|
| `CO_IES`, `CO_CURSO`, `NO_CINE_ROTULO`, `QT_MAT` | 0 | 0% | ✅ |
| `CO_MUNICIPIO` | 11.778 | 1,6% | ✅ **Esperado**: dim. 3 (11.319) + dim. 4 (450) + 9 linhas EAD |
| `TP_GRAU_ACADEMICO` | 2.046 | 0,3% | ✅ **Esperado**: cursos ABI e sequenciais |

### Tabela de IES

| Campo | Nulos | % | Diagnóstico |
|---|---|---|---|
| `NO_MANTENEDORA`, `CO_MANTENEDORA`, `DS_ENDERECO_IES` | 0 | 0% | ✅ |
| `NU_CEP_IES` | 26 | 1,0% | ⚠️ Irrelevante (não usaremos CEP) |
| `SG_IES` | **459** | **17,9%** | ⚠️ **Não usar sigla como rótulo primário** — usar `NO_IES` com fallback |

Nenhum nulo bloqueia análise. Não há valores negativos nas colunas de métrica.

## 4. Consistência de nomenclatura ✅

| Teste | Resultado |
|---|---|
| `CO_MUNICIPIO` com >1 grafia de `NO_MUNICIPIO` | **0** de 3.551 |
| `CO_MUNICIPIO` fora do padrão IBGE 7 dígitos | **0** de 708.571 linhas |
| `CO_REGIAO`/`NO_REGIAO` divergentes | 0 |

Geografia totalmente padronizada. Já vem com código IBGE, então o join com malhas
cartográficas e com bases externas (PIB, população) é direto.

**Nomes de curso**, ao contrário, **não** são padronizados: 1.497 valores livres em `NO_CURSO`
contra 353 rótulos CINE. Toda análise por curso usa `NO_CINE_ROTULO`.

## 5. Consistência aritmética ✅

| Checagem | Esperado | Obtido |
|---|---|---|
| Presencial + EAD = Total | 10.227.266 | 5.037.875 + 5.189.391 = **10.227.266** ✅ |
| Soma das 5 regiões + sem-região | 10.227.266 | 10.224.686 + 2.580 = **10.227.266** ✅ |
| Soma das UFs + sem-UF | 10.227.266 | 10.224.686 + 2.580 = **10.227.266** ✅ |
| Pública + Privada | 10.227.266 | 2.065.067 + 8.162.199 = **10.227.266** ✅ |

As 2.580 matrículas sem geografia são a dimensão 4 (IES brasileiras no exterior, 2.539) mais 41
de linhas EAD sem município. **0,025% do total** — serão exibidas como bucket "Exterior/N.I."
em vez de silenciosamente descartadas.

## 6. Anomalias identificadas

| # | Anomalia | Magnitude | Tratamento |
|---|---|---|---|
| 1 | **Cursos ABI** (Área Básica de Ingresso) na dim. 1 com `QT_CURSO=0` mas com alunos | 345 linhas · 37.882 matrículas (**0,37%**) | Manter nas matrículas; não contam como curso (correto — ABI é porta de entrada, não curso). `TP_GRAU_ACADEMICO` nulo |
| 2 | **Vagas/inscritos residuais na dim. 2**, que deveria ter zero | 5 linhas · 6.925 vagas · 3.590 inscritos | Ignorar: regra "vagas só nas dims 1 e 3" já exclui. Contradiz levemente a nota do INEP |
| 3 | Linhas dim. 2 com todas as métricas zeradas | 150.463 linhas (22% do arquivo) | **Descartar no processamento** — reduz o volume em 1/5 sem perda. (Atenção: 68.911 ingressantes estão em linhas com `QT_MAT=0`; filtrar por `QT_MAT=0 AND QT_ING=0 AND QT_CONC=0`) |
| 4 | `TP_CATEGORIA_ADMINISTRATIVA` sem valores 6, 8, 9 em 2024 | — | Dicionário histórico prevê; manter no decode para compatibilidade com anos antigos |
| 5 | `CO_CINE_ROTULO` com **aspas duplas literais** no CSV (`"0011A01"`) | 100% das linhas | `trim('"')` obrigatório no processamento |
| 6 | `CO_CINE_AREA_GERAL` com **zero à esquerda** (`"00"`,`"01"`) | — | Ler como VARCHAR; nunca converter para inteiro |

## 7. Arquivo de suporte de grupos — ⚠️ 2 problemas

### 7.1 Duplicidade por campus (corrigido)

7 linhas repetem `CO_IES` porque o arquivo lista campi separadamente, mas o Censo não tem código
de campus:

| CO_IES | IES | Linhas | Grupo |
|---|---|---|---|
| 383 | UNAMA | **6** | Ser Educacional |
| 481 | UNG | 2 | Ser Educacional |
| 472 | UNIGRANRIO | 2 | Afya |

**Impacto se não deduplicado: +235.518 matrículas fantasma** (mercado apareceria como 10,46 M).
Ser Educacional saltaria de 375.541 para 588.628 (+57%) e Afya de 79.727 para 102.158 (+28%).

✅ Tratado em `scripts/build_ies_group_map.py` (`drop_duplicates` por `CO_IES`, após verificar
que não há conflito de grupo). **Recomendação:** manter o Excel como está (a granularidade de
campus é informação útil) — a deduplicação é automática no pipeline.

### 7.2 Códigos ausentes do Censo 2024

21 dos 416 `CO_IES` não existem no Censo 2024 — IES extintas, incorporadas ou com código
alterado. Distribuição: Vitru 7, Afya 5, Cogna 3, Ser 2, YDUQS 2, Ânima 2.
Lista completa em `config/ies_grupo_map_nao_encontradas.csv`.

Impacto em 2024: **nulo** (não têm dados). Impacto no histórico: **relevante** — quando os anos
anteriores forem carregados, esses códigos passam a ter matrículas. Por isso o mapeamento é
mantido *year-agnostic*: guardamos todos os códigos, e cada ano usa os que existirem.

### 7.3 Cobertura do mapeamento

| Métrica | Valor |
|---|---|
| Matrículas mapeadas a grupo | 4.321.233 |
| % do mercado total | **42,3%** |
| % da rede privada | **52,9%** |

| Grupo | IES | Matrículas | Presencial | EAD | % EAD | Share nacional |
|---|---|---|---|---|---|---|
| Cogna | 142 | 1.124.066 | 184.003 | 940.063 | 83,6% | 10,99% |
| Vitru | 16 | 1.080.339 | 23.461 | 1.056.878 | 97,8% | 10,56% |
| YDUQS | 68 | 817.088 | 223.013 | 594.075 | 72,7% | 7,99% |
| Cruzeiro do Sul | 14 | 512.500 | 156.570 | 355.930 | 69,4% | 5,01% |
| Ser Educacional | 50 | 375.541 | 195.960 | 179.581 | 47,8% | 3,67% |
| Ânima | 72 | 331.972 | 178.783 | 153.189 | 46,1% | 3,25% |
| Afya | 33 | 79.727 | 68.652 | 11.075 | 13,9% | 0,78% |

⚠️ **Players relevantes fora da cobertura.** Os 47% restantes da rede privada incluem:

| CO_IES | IES | Matrículas |
|---|---|---|
| 1491 | Centro Universitário Internacional (**UNINTER**) | 286.484 |
| 322 | Universidade Paulista (**UNIP**) | 260.362 |
| 316 | Universidade Nove de Julho (**UNINOVE**) | 162.714 |
| 4751 | Centro Universitário **UNIFATECIE** | 84.619 |
| 374 | **FMU** | 63.561 |
| 3840 | **UNIFACVEST** | 55.176 |
| 1446 | **UNIPLAN** | 47.240 |
| 3649 | **UniCV** | 45.360 |

UNINTER, UNIP e UNINOVE sozinhas somam **709.560 matrículas (6,9% do mercado)** — mais que a
YDUQS. Sem elas, qualquer ranking de "maiores players" fica distorcido.

**Recomendação:** decidir se entram como grupos próprios no `Suporte IES.xlsx`. Enquanto não
entrarem, o dashboard as tratará como **"Independentes"** e sempre exibirá a linha
*"Não mapeado / Independentes"* nos rankings — nunca omitindo-as silenciosamente, para que
nenhum share seja lido como maior do que é.

### 7.4 IES não mapeadas com mantenedora de grupo conhecido

4 candidatas detectadas automaticamente (revisar):

| CO_IES | IES | Mantenedora | Grupo sugerido | Matrículas |
|---|---|---|---|---|
| 15450 | Centro Universitário Única | FACULDADE UNICA LTDA | Afya | 13.134 |
| 17433 | Fac. Santo Agostinho de V. da Conquista | INST. EDUC. SANTO AGOSTINHO S.A. | Afya | 705 |
| 23236 | Escola Superior São Judas de Guarulhos | AMC – SERVIÇOS EDUCACIONAIS | Ânima | 337 |
| 3437 | Faculdade UNISUL de Balneário Camboriú | IEDUC S/A | Ânima | 1 |

## 8. Limitação estrutural: campus

Não existe identificador de campus/local de oferta. Consequências:

- "Nº de campi" será sempre um **proxy** = pares distintos (`CO_IES`, `CO_MUNICIPIO`).
- Grupos com múltiplos campi na mesma cidade (comum em SP, RJ, BH) são **subcontados**.
- "Alunos por campus" fica **superestimado** para esses grupos.
- O Campus Explorer é, na verdade, um **"Unit Explorer" IES × município**.

O `Suporte IES.xlsx` prova o ponto: contém 6 campi da UNAMA que o Censo enxerga como 1.
Isso é limitação da fonte pública, não do tratamento — e será declarado na página *Methodology*.

## 9. Comparabilidade histórica

O dicionário do INEP traz uma matriz de coleta por ano (2009–2024). Verificação:

- ✅ Todas as variáveis do núcleo (`QT_MAT`, `QT_ING`, `QT_CONC`, `QT_CURSO`, `QT_VG_TOTAL`,
  `TP_DIMENSAO`, `CO_IES`, `CO_CURSO`, CINE, geografia) são coletadas **em todos os anos
  de 2009 a 2024** → série de ~10 anos é viável sem remendos.
- ⚠️ `IN_COMUNITARIA` e `IN_CONFESSIONAL` só existem a partir de **2023**.
- ⚠️ `TP_CATEGORIA_ADMINISTRATIVA`: categorias 6/8/9 só em 2009; categoria 7 criada em 2012.
- ⚠️ `TP_ORGANIZACAO_ACADEMICA`: opção 5 (CEFET) não existe em 2009.
- ⚠️ `CO_CURSO`, `NO_CURSO`, `IN_GRATUITO` e `TP_DIMENSAO` foram **inseridos em 2022**
  (Nota Informativa). Para anos anteriores a granularidade e as chaves mudam — **validar ao
  carregar cada ano**, não assumir layout idêntico.
- ⚠️ Mudanças societárias (fusões/aquisições) fazem o grupo de uma IES mudar ao longo do tempo.
  O mapeamento atual é **estático**. Para série histórica correta é preciso decidir entre
  *pro-forma* (grupo atual aplicado retroativamente — melhor para ler market share) ou
  *as-reported* (grupo vigente em cada ano). **Recomendação: pro-forma**, com campo
  `ANO_INICIO`/`ANO_FIM` opcional no mapeamento para casos que exijam as-reported.

## 10. Checklist de validação automatizada (Etapa 2)

O `scripts/validate.py` deverá falhar o build se qualquer item abaixo quebrar:

- [ ] Total de matrículas == 10.227.266 (para 2024)
- [ ] Presencial + EAD == Total
- [ ] Soma das UFs + bucket "Exterior/N.I." == Total
- [ ] Soma das regiões == Total
- [ ] Soma por área CINE == Total
- [ ] Soma dos grupos + "Independentes" == Total da rede privada
- [ ] Nenhuma linha agregada com `QT_MAT` negativo
- [ ] Nenhum `CO_IES` com dois grupos no mapeamento
- [ ] Nenhum `CO_IES` duplicado nas tabelas agregadas de IES
- [ ] Toda IES do Censo presente em `ies_grupo_map.csv` (grupo pode ser vazio)
- [ ] Cursos == soma de dims 1 e 3
- [ ] Cobertura do mapeamento reportada (não é falha, é métrica de acompanhamento)
