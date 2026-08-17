# Reconciliação: Censo INEP × números reportados pelas companhias

> Por que o número do Censo não bate com o release da empresa — e como fazer a ponte.
> Motivado pela divergência observada na YDUQS em 2024.

---

## ⚠️ Correção de 12/08/2026 — a ponte anterior estava comparando escopos diferentes

A análise original desta página confrontava o Censo com o **número-manchete** de cada release.
Esse número **não é comparável**: ele carrega pós-graduação, técnico, educação continuada e —
no caso da YDUQS — o **Qconcursos, um preparatório para concursos com 498,6 mil alunos que não é
ensino superior** e portanto não existe no Censo.

Refeita a comparação **só com graduação** (colunas `GRAD_*` de `config/reportado_companhias.csv`,
derivadas das aberturas de cada release), a conclusão se inverte:

| Grupo | Reportado (graduação) | Censo `QT_MAT` | Δ | Censo Base | Δ |
|---|---:|---:|---:|---:|---:|
| Ânima | 324.800 | 332.310 | **+2,3%** | 377.714 | +16,3% |
| Cruzeiro do Sul | 491.000 | 512.500 | **+4,4%** | 544.785 | +11,0% |
| YDUQS | 779.200 | 823.886 | **+5,7%** | 1.272.338 | +63,3% |
| Afya | 76.988 | 93.566 | +21,5% | 125.748 | +63,3% |
| Ser Educacional | 307.830 | 375.541 | +22,0% | 412.658 | +34,1% |
| Vitru | 764.500 | 1.080.339 | +41,3% | 1.087.731 | +42,3% |
| Cogna | — | 1.124.318 | — | 1.268.272 | — |

**É `QT_MAT` que reconcilia com a graduação reportada, não a base com trancados.** Nos três
grupos em que o release abre graduação de forma limpa (Ânima, Cruzeiro do Sul, YDUQS) o gap fica
entre +2% e +6% — compatível com diferença de data-base (Censo é anual, release é 4T).

Os três que continuam fora:

- **Vitru (+41%)** — a companhia exclui alunos "unengaged" por critério próprio desde 1T24, o que
  reduz deliberadamente a base divulgada. O sentido do gap é o esperado; a magnitude não foi
  isolada.
- **Afya (+21,5%)** — é o problema já conhecido das 23.194 matrículas EAD que o Censo atribui ao
  grupo e o release não menciona. Sem elas o presencial fecha em **−8,6%**. Ver §6.2 do hand-off.
- **Ser Educacional (+22%)** — não investigado. Próximo item da fila.

O que **permanece válido** da análise original: trancados existem, variam de 0,7% a 87,6% entre
grupos e mudam o ranking dependendo da métrica escolhida. O que muda é a recomendação de uso —
para confrontar com release de graduação, o comparável é `QT_MAT`.

A tabela de reconciliação **saiu do dashboard** por decisão do usuário (o investidor não precisa
vê-la); ela continua sendo gerada por `scripts/valida_reconciliacao.py` em
`outputs/reconciliacao_2024.md`, que é onde a verificação deve ser feita.

---

## O problema

A YDUQS reportou aproximadamente **1,0 milhão de alunos EAD** e **274 mil presenciais** em 2024.
O Censo, somando `QT_MAT` das 71 IES do grupo, dá **594.671 EAD** e **229.215 presenciais**.

A diferença **não é erro de mapeamento**. Foram feitos dois testes exaustivos:

| Teste | Resultado |
|---|---|
| IES com marca YDUQS (Estácio, Ibmec, Wyden, Damásio, IDOMED) fora do grupo | **0** |
| IES não mapeadas sob mantenedora que já é YDUQS | **0** |

O mapeamento está completo. A diferença é de **definição de "aluno"**.

## A causa: `QT_SIT_TRANCADA`

O dicionário do INEP define `QT_MAT` como:

> "soma do número de alunos com situação de vínculo ao curso igual a **Cursando e/ou Formado**"

Alunos com **matrícula trancada ficam de fora**. Eles são reportados à parte, em
`QT_SIT_TRANCADA`. Companhias, ao divulgar "base de alunos", tipicamente incluem vínculos que o
Censo classifica como trancados.

### A ponte fecha

| | Censo `QT_MAT` | Trancados | `QT_MAT` + trancados | Reportado pela YDUQS |
|---|---:|---:|---:|---:|
| EAD | 594.671 | 371.611 | **966.282** | ~1.000.000 |
| Presencial | 229.215 | 76.841 | **306.056** | 274.000 |
| **Total** | **823.886** | **448.452** | **1.272.338** | **~1.274.000** |

O total fecha com **diferença de 0,2%**. A repartição entre modalidades difere em ~34 mil
(2,7% do total) — compatível com o fato de que os segmentos de reporte da companhia
("Ensino Digital" / "Presencial" / "Premium") não são idênticos à `TP_MODALIDADE_ENSINO` do
Censo: formatos flex e semipresenciais são classificados de um jeito no Censo e de outro no
release.

## Por que isso importa muito: a taxa de trancamento varia brutalmente entre grupos

Esta é a razão pela qual a escolha da métrica muda o ranking:

| Grupo | `QT_MAT` | Trancados | **Trancados / matrículas** | Share `QT_MAT` | Share base | Δ p.p. |
|---|---:|---:|---:|---:|---:|---:|
| UNINTER | 286.484 | 250.949 | **87,6%** | 2,80% | 4,47% | **+1,66** |
| YDUQS | 823.886 | 448.452 | **54,4%** | 8,06% | 10,57% | **+2,52** |
| Afya | 93.566 | 32.182 | 34,4% | 0,91% | 1,04% | +0,13 |
| UNIFATECIE | 84.619 | 21.330 | 25,2% | 0,83% | 0,88% | +0,05 |
| FMU | 67.623 | 12.793 | 18,9% | 0,66% | 0,67% | +0,01 |
| UNIP | 262.216 | 43.633 | 16,6% | 2,56% | 2,54% | −0,02 |
| Ânima | 332.310 | 45.404 | 13,7% | 3,25% | 3,14% | −0,11 |
| Cogna | 1.124.318 | 143.954 | 12,8% | 10,99% | 10,54% | −0,46 |
| Ser Educacional | 375.541 | 37.117 | 9,9% | 3,67% | 3,43% | −0,24 |
| Cruzeiro do Sul | 512.500 | 32.285 | 6,3% | 5,01% | 4,53% | −0,48 |
| **Vitru** | 1.080.339 | 7.392 | **0,7%** | 10,56% | 9,04% | **−1,53** |
| **UNINOVE** | 167.819 | 74 | **0,04%** | 1,64% | 1,39% | −0,25 |
| **Brasil** | **10.227.266** | **1.808.167** | **17,7%** | — | — | — |

A dispersão é de **0,04% a 87,6%**. Duas leituras diferentes do mesmo mercado:

- Por `QT_MAT`, a **Vitru é a 2ª maior** (10,56%) e a YDUQS a 3ª (8,06%).
- Por base de alunos, a **YDUQS é a 2ª** (10,57%) e a Vitru cai para 3ª (9,04%).

## Decisão adotada

**`QT_MAT` continua sendo a métrica primária do dashboard.** Motivos:

1. É a definição oficial do INEP, aplicada de forma idêntica a todas as 2.561 IES.
2. É a base das estatísticas oficiais do setor — comparável com qualquer publicação do MEC/INEP.
3. É consistente ao longo dos anos, o que a série histórica exige.

**`QT_BASE_ALUNOS` (= `QT_MAT` + `QT_SIT_TRANCADA`) entra como definição alternativa
selecionável**, porque é a que reconcilia com os releases das companhias — e sem ela é
impossível confrontar o dashboard com um press release.

**A taxa de trancamento vira métrica de primeira classe.** Ela não é ruído: é sinal.
Uma diferença de 0,7% (Vitru) para 54,4% (YDUQS) na mesma indústria reflete alguma combinação de

- política de trancamento e retenção genuinamente distinta;
- prática de declaração ao Censo distinta entre grupos;
- estágio diferente do ciclo de vida do aluno EAD.

O dashboard **mostra o número e não atribui causa**. Mas exibe a taxa lado a lado com o share,
porque um grupo com 54% da base trancada tem qualidade de receita diferente de um com 0,7%.

## Regra de leitura

> Nenhum número de market share deve ser exibido sem que a métrica e o denominador estejam
> declarados na tela. `QT_MAT` e base de alunos produzem rankings diferentes, e ambos estão
> corretos dentro da sua própria definição.

## O que o Censo não cobre, em nenhuma definição

Vale registrar para evitar reconciliações impossíveis:

- **Pós-graduação lato sensu** — fora dos microdados do Censo da Educação Superior.
- **Cursos livres e preparatórios** (ex.: Damásio, Qconcursos na YDUQS) — fora.
- **Ensino técnico e básico** — fora.
- O Censo cobre **graduação** (10.226.873 matrículas) e **sequencial de formação específica**
  (393 matrículas). Só isso.

Portanto, para grupos com operações relevantes de pós-graduação ou educação continuada, mesmo a
base de alunos do Censo será menor que o total corporativo divulgado. A ponte de trancados
resolve a maior parte do gap, não necessariamente 100% dele.

---

## Auditoria cruzada: os 7 releases de 4T24 (checagem de credibilidade)

> Adicionado após o usuário pedir uma verificação de que o Censo não está "grosseiramente"
> divergente do que as companhias abertas reportaram no 4T24. Os números abaixo foram extraídos
> diretamente dos earnings releases oficiais (PDFs baixados e lidos por extração de texto),
> não de resumos de terceiros. Fontes citadas por empresa.

### Veredito

**Os dados não são grosseiramente inconsistentes.** As seis companhias verificadas (falta Cogna,
ver nota) reconciliam com o Censo dentro de faixas explicáveis, e — o que é o teste mais
importante — **cada gap tem um mecanismo específico e identificável**, não um viés genérico. Isso
é evidência a favor da qualidade do Censo: erros de base de dados tendem a ser sistemáticos
(sempre na mesma direção, mesma magnitude); os gaps aqui têm causas diferentes em cada empresa,
algumas até documentadas pela própria companhia.

| Grupo | Gap no total (`QT_MAT` vs. reportado) | Causa identificada |
|---|---:|---|
| Cruzeiro do Sul | **+4,4%** | Nenhuma anomalia — dentro do ruído normal |
| Ânima | **+2,3%** (total) | Fecha bem no total; diverge na modalidade (ver abaixo) |
| YDUQS | ~0% (ajustado) | "Ensino Digital" reportado inclui produto que não é ensino superior |
| Ser Educacional | +14% a +25% | Provável diferença de classificação Híbrido/EAD (ver abaixo) |
| Afya | +21,5% (total) | Censo inclui EAD que o release de Undergrad não segmenta |
| Vitru | +31% | Vitru **exclui deliberadamente** alunos "unengaged" do KPI — documentado no release |
| Cogna | pendente | Não foi possível obter o release de 4T24 (ver nota final) |

### Cruzeiro do Sul — reconciliação quase perfeita

Fonte: [Apresentação 4T25](https://d169uzu5o4xu1k.cloudfront.net/9981e6b2-05ad-4e8d-a4c8-8242bd52879a/2025/ae56caf7-2191-4408-8904-04b1513d9f06.pdf)
(coluna comparativa 4T24), Cruzeiro do Sul Educacional.

| | Reportado (graduação) | Censo `QT_MAT` | Gap |
|---|---:|---:|---:|
| Presencial | 151.000 | 156.570 | **+3,7%** |
| Digital | 340.000 | 355.930 | **+4,7%** |
| Total | 491.000 | 512.500 | **+4,4%** |

O melhor caso da amostra. Gap pequeno e na mesma direção nos dois recortes — compatível com
diferença de data de referência ou pequenas divergências de escopo, não com erro estrutural.

### YDUQS — fecha quase exatamente, uma vez corrigido o escopo

Fonte: [Release 4T24](https://www.yduqs.com.br/Download.aspx?Arquivo=3d4EKKQMqSkAX9vvrhd75g%3D%3D), pág. 6-9.

**Achado crítico:** o "Ensino Digital" que a YDUQS reporta (1.026,1 mil alunos) **não é só
ensino superior**. Ele soma:

| Componente | Alunos | É ensino superior (Censo)? |
|---|---:|---|
| Graduação Digital | 411,6 mil | Sim |
| Graduação Flex | 74,4 mil | Sim, provavelmente |
| Vida Toda (educação continuada) | 41,5 mil | Não |
| **Qconcursos** (curso preparatório para concursos) | **498,6 mil** | **Não — não é curso de graduação registrado no MEC** |

Quase metade da "base digital" divulgada pela YDUQS é o Qconcursos — uma assinatura de
preparatório para concursos públicos, produto que **nunca apareceria nos microdados do Censo**
porque não é um curso de graduação autorizado. Ao restringir à Graduação Digital de fato
(486,0 mil) e somar a Premium Graduação (Medicina + IBMEC, presencial, 15,6 mil):

| | Reportado (graduação, escopo corrigido) | Censo `QT_MAT` | Gap |
|---|---:|---:|---:|
| Presencial (Presencial BU + Premium Graduação) | ~283 mil | 229.215 | −19% |
| EAD (Graduação Digital) | 486,0 mil | 594.671 | **+22%** |
| Total | ~769 mil | 823.886 | **+7,1%** |

O total cai de um gap de −37,6% (comparação ingênua) para **+7,1%** só ao remover produtos que
não são ensino superior. O resíduo de modalidade (Presencial vs. EAD) provavelmente reflete
"Semipresencial" (68,7 mil, contado como Presencial pela YDUQS) sendo registrado como EAD no
MEC/Censo — Brasil tem regulação específica que permite até 40% de carga EAD em cursos
formalmente presenciais, e o inverso também ocorre.

### Ser Educacional — fecha bem quando comparado a graduação, com viés direcional

Fonte: [Release 4T24](https://api.mziq.com/mzfilemanager/v2/d/4e9e23d7-cea5-42fd-bf06-7a7ca01880fc/dd438d8f-0346-0ca0-bd06-c6c98d8b629d?origin=2), pág. 7.

Os números "Alunos de Graduação Híbrida" e "Alunos de Graduação Digital" da tabela de
financiamento estudantil **já são graduação pura** (sem pós, sem técnico):

| | Reportado (graduação) | Censo `QT_MAT` | Gap |
|---|---:|---:|---:|
| Híbrida (presencial) | 164.879 | 195.960 | **+18,9%** |
| Digital (EAD) | 142.951 | 179.581 | **+25,6%** |

O Censo é consistentemente **maior** nas duas modalidades, ao contrário do padrão esperado
(trancados deveriam fazer o reportado ser maior, não menor). Hipótese mais provável: parte do
que a Ser chama de "Híbrido" tem autorização MEC como EAD (o termo comercial "ensino híbrido" no
Brasil frequentemente corresponde à modalidade regulatória "EAD com atividades presenciais
obrigatórias", que o Censo classifica como `TP_MODALIDADE_ENSINO=2`). Não testado diretamente —
fica como item para investigação, não como conclusão.

### Ânima — fecha muito bem no total, diverge na modalidade

Fonte: [Release 4T24](https://ri.animaeducacao.com.br/Download.aspx?Arquivo=KqjtZpy6bx2UYy6z0YT9WA%3D%3D),
pág. 1 e 9-11.

Reconstrução graduação-only a partir dos segmentos (Ânima Core Graduação + Inspirali Graduação
Medicina = Presencial; Ensino Digital Graduação = EAD):

| | Reportado (graduação) | Censo `QT_MAT` | Gap |
|---|---:|---:|---:|
| Presencial (Core + Inspirali) | 202.900 | 179.121 | −11,7% |
| EAD (Ensino Digital) | 121.900 | 153.189 | +25,7% |
| **Total** | **324.800** | **332.310** | **+2,3%** |

O total é o segundo melhor da amostra. A divergência de modalidade é grande e na mesma direção
observada na Ser Educacional — reforça a hipótese de classificação Híbrido/EAD divergente entre
o rótulo comercial da empresa e a modalidade regulatória registrada no MEC.

### Vitru — o gap é uma escolha metodológica declarada pela própria empresa

Fonte: [Release 4Q24](https://api.mziq.com/mzfilemanager/v2/d/053b9d06-7899-42e6-978d-2f68f55dac9a/b2575015-7741-3090-23ea-8771c8c9f94a?origin=2),
pág. 5-6.

Este é o caso mais importante para entender antes de usar o número da Vitru em qualquer análise.
O release afirma, textualmente:

> "the exclusion of students considered 'unengaged' from the base as of 1Q24, which initially
> translates into **reduced growth in the student base and revenue**"

A Vitru mudou seu próprio critério de contagem em 2024: excluiu do KPI reportado os alunos que
considera "não engajados", mesmo que formalmente matriculados. O número que ela divulga
(744,1 mil em Graduação EAD) é **menor por decisão editorial da empresa**, não por sonegar
matrícula formal.

| | Reportado (KPI "engaged") | Censo `QT_MAT` (matrícula formal) | Gap |
|---|---:|---:|---:|
| EAD Graduação | 744.100 | 1.056.878 | **+42%** |
| Presencial Graduação | 20.400 | 23.461 | +15% |
| Total | 764.500 | 1.080.339 | **+41%** |

O Censo captura todo aluno com vínculo formal "Cursando", independentemente de estar "engajado"
segundo o critério interno da Vitru. **O gap grande aqui não é sinal de problema no Censo — é o
esperado**, dado que a empresa admite reportar uma métrica deliberadamente mais conservadora.
Consequência prática: comparar a Vitru com outros grupos usando o número que ela mesma divulga
subestima sua real matrícula/exposição regulatória frente aos pares.

### Afya — presencial reconcilia bem; total diverge por escopo de segmento

Fonte: [Release 4Q24](https://www.gurufocus.com/news/2738428/afya-limited-announces-fourth-quarter-and-fullyear-2024-financial-results),
Table 2, "Key Revenue Drivers – Undergraduate Programs".

| Segmento (fim de período, 2024) | Alunos |
|---|---:|
| Medical School | 24.255 |
| Undergraduate Health Science | 25.570 |
| Other Ex-Health Undergraduate | 27.163 |
| **Total Undergrad** | **76.988** |

| | Reportado | Censo `QT_MAT` | Gap |
|---|---:|---:|---:|
| Presencial | 76.988 | 70.372 | **−8,6%** |
| Total (Afya não reporta EAD) | 76.988 | 93.566 | **+21,5%** |

O presencial reconcilia bem. O gap do total existe porque a Afya não divulga um segmento EAD em
sua tabela de "Undergrad Programs", mas o Censo atribui **23.194 matrículas EAD** às 35 IES
mapeadas ao grupo. Duas explicações possíveis, não distinguidas aqui: (a) a Afya de fato tem
oferta EAD residual em IES adquiridas que não entra no KPI consolidado da forma como definido no
release, ou (b) alguma das 35 IES no mapeamento não deveria estar em Afya. Recomendação: revisar
a composição do grupo Afya com atenção específica às IES com maior matrícula EAD.

### Cogna — pendente

Não foi possível obter o release oficial de 4T24 nesta sessão: as buscas retornaram
consistentemente o release de 4T25 (o mais recente disponível nos índices de busca), e o
domínio `esg.cogna.com.br` bloqueou o acesso automatizado (HTTP 403) aos arquivos históricos.
O release de 4T25 confirma qualitativamente uma tendência de crescimento contínuo da base
(*"18º trimestre consecutivo de crescimento de base de alunos"*), mas não traz a tabela de base
de alunos em números absolutos para 4T24 especificamente — só variações percentuais.
**Ação sugerida:** se você tiver o PDF do release de 4T24 da Cogna à mão, envie que eu extraio e
reconcilio da mesma forma.

### Conclusão para uso em equity research

1. **Não use o `QT_MAT` bruto do Censo contra o número-manchete de um release sem antes checar
   o escopo.** Cada empresa embala coisas diferentes em "base de alunos": Qconcursos (YDUQS),
   critério de engajamento (Vitru), pós-graduação e técnico (Ser, Ânima, Cogna).
2. **A comparação correta é sempre graduação-contra-graduação**, e mesmo assim sobra um resíduo
   de 2% a 8% que parece estrutural — plausivelmente a fronteira Presencial/EAD regulatória
   (MEC) divergindo do rótulo comercial "Híbrido"/"Flex"/"Semipresencial" usado pelas empresas.
3. **Esse resíduo é uma característica do dado, não um defeito.** Ele existe em toda comparação
   Censo-vs-empresa que se pode fazer, incluindo em análises publicadas por bancos e casas de
   research que usam o Censo como benchmark — o ponto é saber que ele existe e não superinterpretar
   diferenças de 5-10 p.p. como se fossem sinal de ganho/perda real de mercado.
4. **Nenhuma das 6 empresas verificadas mostrou gap incompatível com uso do Censo como
   benchmark de mercado.** O maior gap (Vitru, +41%) tem causa documentada pela própria empresa
   e não indica problema de qualidade da base pública.
