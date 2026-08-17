# Reconciliação Censo × reportado pelas companhias — 2024

> Gerado por `scripts/valida_reconciliacao.py`.
> `QT_MAT` = definição INEP (Cursando + Formado, **exclui trancados**).
> `Base` = `QT_MAT` + trancados, que é o que costuma constar dos releases.


## YDUQS

Comparação restrita a **graduação** — único recorte comparável ao Censo. Escopo do número-manchete do release: *graduacao+pos+cursos_livres* (não usado). Taxa de trancamento no Censo: **54.4%**

Derivação do número de graduação: Presencial 273.600 (segmento Presencial, graduacao) + Premium 19.600 (Medicina e IBMEC, presencial) = 293.200. EAD = Graduacao Digital pura 486.000, excluindo Qconcursos (498,6 mil, preparatorio para concursos, nao e ensino superior) e o restante do Ensino Digital que nao e graduacao.

| Recorte | Reportado | Censo `QT_MAT` | Δ | Censo Base | Δ |
|---|---:|---:|---:|---:|---:|
| Presencial | 293,200 | 229,215 | -21.8% | 306,056 | +4.4% |
| EAD | 486,000 | 594,671 | +22.4% | 966,282 | +98.8% |
| Total | 779,200 | 823,886 | +5.7% | 1,272,338 | +63.3% |

## Vitru

Comparação restrita a **graduação** — único recorte comparável ao Censo. Escopo do número-manchete do release: *graduacao+pos* (não usado). Taxa de trancamento no Censo: **0.7%**

Derivação do número de graduação: Graduacao ex-pos, conforme abertura do proprio release: Presencial 20.400 e EAD 744.100.

| Recorte | Reportado | Censo `QT_MAT` | Δ | Censo Base | Δ |
|---|---:|---:|---:|---:|---:|
| Presencial | 20,400 | 23,461 | +15.0% | 26,137 | +28.1% |
| EAD | 744,100 | 1,056,878 | +42.0% | 1,061,594 | +42.7% |
| Total | 764,500 | 1,080,339 | +41.3% | 1,087,731 | +42.3% |

## Ser Educacional

Comparação restrita a **graduação** — único recorte comparável ao Censo. Escopo do número-manchete do release: *graduacao+pos+tecnico* (não usado). Taxa de trancamento no Censo: **9.9%**

Derivação do número de graduação: Grad. Hibrida 164.879 + Grad. Digital 142.951. O manchete de 330.284 inclui pos e tecnico, que ficam de fora.

| Recorte | Reportado | Censo `QT_MAT` | Δ | Censo Base | Δ |
|---|---:|---:|---:|---:|---:|
| Presencial | 164,879 | 195,960 | +18.9% | 205,999 | +24.9% |
| EAD | 142,951 | 179,581 | +25.6% | 206,659 | +44.6% |
| Total | 307,830 | 375,541 | +22.0% | 412,658 | +34.1% |

## Ânima

Comparação restrita a **graduação** — único recorte comparável ao Censo. Escopo do número-manchete do release: *graduacao* (não usado). Taxa de trancamento no Censo: **13.7%**

Derivação do número de graduação: Ja e graduacao pura: Anima Core Graduacao 191.400 (exceto medicina) + Inspirali Graduacao Medicina 11.500 + Ensino Digital Graduacao 121.900.

| Recorte | Reportado | Censo `QT_MAT` | Δ | Censo Base | Δ |
|---|---:|---:|---:|---:|---:|
| Presencial | 202,900 | 179,121 | -11.7% | 205,845 | +1.5% |
| EAD | 121,900 | 153,189 | +25.7% | 171,869 | +41.0% |
| Total | 324,800 | 332,310 | +2.3% | 377,714 | +16.3% |

## Afya

Comparação restrita a **graduação** — único recorte comparável ao Censo. Escopo do número-manchete do release: *graduacao* (não usado). Taxa de trancamento no Censo: **34.4%**

Derivação do número de graduação: Total Undergrad (end of period) = Medical School 24.255 + Undergrad Health Science 25.570 + Other Ex-Health Undergrad 27.163. A empresa nao divulga split presencial/EAD.

| Recorte | Reportado | Censo `QT_MAT` | Δ | Censo Base | Δ |
|---|---:|---:|---:|---:|---:|
| Total | 76,988 | 93,566 | +21.5% | 125,748 | +63.3% |

## Cruzeiro do Sul

Comparação restrita a **graduação** — único recorte comparável ao Censo. Escopo do número-manchete do release: *graduacao* (não usado). Taxa de trancamento no Censo: **6.3%**

Derivação do número de graduação: Ja e graduacao pura: Presencial 151.000 + Digital 340.000. Medicina e Pos-grad/Colegio sao mostrados a parte pela empresa e nao entram.

| Recorte | Reportado | Censo `QT_MAT` | Δ | Censo Base | Δ |
|---|---:|---:|---:|---:|---:|
| Presencial | 151,000 | 156,570 | +3.7% | 168,000 | +11.3% |
| EAD | 340,000 | 355,930 | +4.7% | 376,785 | +10.8% |
| Total | 491,000 | 512,500 | +4.4% | 544,785 | +11.0% |

## Sem número reportado preenchido

Cogna

Preencha `config/reportado_companhias.csv` para incluí-los na reconciliação.
