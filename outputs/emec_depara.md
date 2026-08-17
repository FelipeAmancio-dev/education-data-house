# De-para e-MEC × Censo

Fonte: `Dados_GEO.xlsx` — Relatório da Consulta Avançada do Sistema e-MEC.
Gerado por `scripts/10_ingest_emec.py`.

## Cobertura

| Medida | Valor |
|---|---:|
| IES no e-MEC (únicas) | 3,176 |
| IES no `dim.ies` (toda a série 2015–2024) | 3,400 |
| **Casam por `CO_IES`** | **2,636** |
| Só no Censo (histórico/extintas) | 764 |
| Só no e-MEC (sem matrícula no Censo) | 540 |
| Matrículas 2024 cobertas | **10,212,949 de 10,227,266 (99.9%)** |

> A contagem de IES engana e a de matrículas é a que importa: as que ficam de fora são minúsculas. O e-MEC só traz IES **ativas**, então quase todo o resíduo é IES que existiu na série e não existe mais.

### O casamento está correto? (validação por UF)

Cobertura não é correção. A checagem forte é a **UF**, independente do código: se `CO_IES` tivesse casado com a instituição errada, o estado discordaria.

| Checagem | Resultado |
|---|---:|
| Linhas com UF nos dois lados | 2,631 |
| **UF igual** | **2,631 (100.00%)** |
| UF divergente | 0 |

✅ **Nenhuma divergência de UF.** Onde o nome difere, é renomeação e não erro de casamento: a Afya rebatizou as adquiridas e várias IES subiram de organização acadêmica. O `CO_IES` é o mesmo identificador nas duas bases, então o de-para é direto — nenhuma linha precisou de casamento por nome.

### Maiores IES sem par no e-MEC

| Matrículas 2024 | CO_IES | Instituição | UF |
|---:|---:|---|---|
| 2,048 | 2849 | ESCOLA SUPERIOR DOM HELDER CÂMARA | MG |
| 1,140 | 475 | FACULDADE DE MEDICINA DE PETRÓPOLIS | RJ |
| 1,095 | 20548 | FACULDADE UNINTA TIANGUA | CE |
| 829 | 23242 | Escola Superior São Judas de São Bernardo do Campo | SP |
| 702 | 22329 | FACULDADE UNINTA FORTALEZA | CE |
| 619 | 2460 | FACULDADE ESTÁCIO DE NATAL | RN |
| 604 | 3268 | FACULDADE MADRE THAIS | BA |
| 561 | 1195 | FACULDADE SENAI DE TECNOLOGIA MECATRÔNICA | SP |
| 506 | 24026 | Instituto de Serra Dourada | SP |
| 459 | 24025 | Centro de Ensino Superior de Serra Dourada | SP |
| 431 | 2775 | Faculdade Católica de Várzea Grande | MT |
| 370 | 22196 | Faculdade de Direito Serra Dourada | PA |
| 366 | 339 | FACULDADE UNINEVES | PB |
| 345 | 474 | FACULDADE DE FILOSOFIA CIÊNCIAS E LETRAS DOM BOSCO | RJ |
| 339 | 2511 | FACULDADE DE DIREITO ANHANGUERA UNIDADE GUARAPARI | ES |

## O que o e-MEC agrega ao Censo

Não é geografia — o endereço é o da **sede**, um ponto por IES. É qualidade e situação regulatória:

### IGC médio por grupo (só IES com nota)

| Grupo | IES casadas | IGC médio | com nota |
|---|---:|---:|---:|
| Independentes | 2140 | 3.17 | 1655 |
| Cogna | 135 | 3.08 | 89 |
| YDUQS | 70 | 3.11 | 63 |
| Ânima | 69 | 3.07 | 57 |
| Ser Educacional | 50 | 2.95 | 43 |
| Afya | 35 | 3.11 | 27 |
| Cruzeiro do Sul | 14 | 3.14 | 14 |
| UNIP | 12 | 2.67 | 12 |
| Vitru | 16 | 3.08 | 12 |
| Uniplan | 8 | 2.62 | 8 |
| Multivix | 9 | 4.00 | 8 |
| Universo | 7 | 2.86 | 7 |
| UniFTC | 10 | 3.86 | 7 |
| Ulbra | 5 | 3.40 | 5 |
| UNINOVE | 6 | 3.00 | 4 |
| Catolica (UBEC) | 4 | 3.75 | 4 |
| UNINTA | 4 | 3.75 | 4 |
| Mackenzie | 4 | 4.00 | 3 |
| Unicap | 2 | 3.50 | 2 |
| FMU | 2 | 3.00 | 2 |

### Sinalizações vigentes

Restrição regulatória em vigor. Material para o setor e ligado ao bloco Ambiente Regulatório.

| Sinalização | IES |
|---|---:|
| Unificação de Mantidas | 156 |
| Credenciamento Prévio | 152 |
| Suspensão de Ingresso, Suspensão PRONATEC, Suspensão PROUNI | 58 |
| Em Descredenciamento voluntário | 49 |
| Suspensão contrato FIES, Suspensão PRONATEC, Suspensão PROUNI | 37 |
| Adesão ao PROIES | 29 |
| Em supervisão - Procedimento Sancionador | 24 |
| Credenciamento EaD Provisório | 14 |
| Em supervisão - Procedimento Sancionador sem Medida Cautelar | 10 |
| Sub Judice | 9 |
| Suspensão de autonomia para EAD | 4 |
| Em Supervisão - Procedimento Sancionador com Medida Cautelar, Suspensão contrato FIES, Suspensão PRONATEC, Suspensão PROUNI | 4 |
| Em Supervisão - Procedimento Sancionador com Medida Cautelar | 3 |
| Suspensão de Ingresso | 3 |
| Em Descredenciamento voluntário EAD | 2 |
| Em Supervisão - Procedimento Saneador sem Medida Cautelar | 2 |
| Descredenciada por medida de supervisão | 2 |
| Em supervisão - Procedimento Sancionador, Suspensão de Ingresso, Suspensão PRONATEC, Suspensão PROUNI | 2 |
| Em Descredenciamento voluntário, Suspensão de Ingresso, Suspensão PRONATEC, Suspensão PROUNI | 2 |
| Em Descredenciamento voluntário, Unificação de Mantidas | 2 |
| Suspensão de autonomia para EAD, Unificação de Mantidas | 1 |
| Em supervisão - Procedimento Sancionador, Suspensão de Ingresso, Unificação de Mantidas | 1 |
| Suspensão de Ingresso, Suspensão PRONATEC, Suspensão PROUNI, Unificação de Mantidas | 1 |
| Em Descredenciamento voluntário, Suspensão contrato FIES, Suspensão PRONATEC, Suspensão PROUNI | 1 |
| Descredenciada | 1 |
| Vedação de criação de cursos de especialização Lato Sensu | 1 |
| Em supervisão - Procedimento Sancionador sem Medida Cautelar, Suspensão de Ingresso | 1 |
| Em Supervisão - Determinação de Providências, Suspensão contrato FIES, Suspensão PRONATEC, Suspensão PROUNI | 1 |
| Em supervisão - Procedimento Sancionador, Suspensão contrato FIES, Suspensão de Ingresso, Suspensão de ingresso nos cursos de especialização Lato Sensu , Suspensão PRONATEC, Suspensão PROUNI, Vedação de Participação em Transferência de Mantença | 1 |
| Em Supervisão - Procedimento Sancionador com Medida Cautelar, Suspensão contrato FIES, Suspensão de autonomia para EAD, Suspensão de Ingresso, Suspensão de ingresso nos cursos de especialização Lato Sensu , Suspensão PRONATEC, Suspensão PROUNI | 1 |
| Em supervisão - Procedimento Sancionador, Suspensão contrato FIES, Suspensão PRONATEC, Suspensão PROUNI | 1 |
| Suspensão de ingresso nos cursos de especialização Lato Sensu , Vedação de criação de cursos de especialização Lato Sensu | 1 |
| Acervo Acadêmico | 1 |
| Em supervisão - Procedimento Sancionador, Suspensão de Ingresso, Suspensão de ingresso nos cursos de especialização Lato Sensu | 1 |
| Em supervisão - Procedimento Sancionador, Unificação de Mantidas | 1 |
| Em Descredenciamento voluntário, Suspensão das Prerrogativas de Autonomia, Suspensão de autonomia para EAD, Suspensão de ingresso nos cursos de especialização Lato Sensu | 1 |
