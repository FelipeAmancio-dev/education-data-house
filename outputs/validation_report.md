# Relatório de Validação — série 2015–2024

> Gerado por `scripts/03_validate.py`. Reproduzir: `python scripts/03_validate.py`


**✅ PASSOU** — 0 falha(s) crítica(s), 6 alerta(s).


## 1. Fechamentos por ano (checagens críticas)

| Ano | Total | Pres+EAD | Pub+Priv | UF+s/UF | Área CINE |
|---|---:|:--:|:--:|:--:|:--:|
| 2015 | 8,033,574 | ✅ | ✅ | ✅ | ✅ |
| 2016 | 8,052,254 | ✅ | ✅ | ✅ | ✅ |
| 2017 | 8,290,911 | ✅ | ✅ | ✅ | ✅ |
| 2018 | 8,451,748 | ✅ | ✅ | ✅ | ✅ |
| 2019 | 8,604,526 | ✅ | ✅ | ✅ | ✅ |
| 2020 | 8,680,945 | ✅ | ✅ | ✅ | ✅ |
| 2021 | 8,987,120 | ✅ | ✅ | ✅ | ✅ |
| 2022 | 9,444,116 | ✅ | ✅ | ✅ | ✅ |
| 2023 | 9,977,217 | ✅ | ✅ | ✅ | ✅ |
| 2024 | 10,227,266 | ✅ | ✅ | ✅ | ✅ |

## 2. Cubos reconciliam com os microdados

| Cubo | Δ matrículas vs. fato |
|---|---:|
| `cubo_ies_mod` | ✅ 0 |
| `cubo_cine_mod` | ✅ 0 |
| `cubo_municipio_mod` | ✅ 0 |
| `cubo_ies_cine_mod` | ✅ 0 |

## 3. Sanidade dos dados

- Métricas negativas: **0** ✅
- `(ano, CO_IES)` duplicados em `dim_ies`: **0** ✅
- Chave do fato duplicada: **0** ✅
- Dimensões 3/4 com geografia indevida: ⚠️ 2022 (9,590 linhas) — sem impacto nos cubos, que usam apenas dims 1 e 2 para recorte geográfico

## 4. Variação ano a ano (alerta se fora de ±15%)

| Ano | Matrículas | YoY | Presencial YoY | EAD YoY |
|---|---:|---:|---:|---:|
| 2015 | 8,033,574 | — | — | — |
| 2016 | 8,052,254 | +0.2% | -1.2% | +7.2% |
| 2017 | 8,290,911 | +3.0% | -0.4% | +17.7% |
| 2018 | 8,451,748 | +1.9% | -2.1% | +16.9% |
| 2019 | 8,604,526 | +1.8% | -3.8% | +19.1% |
| 2020 | 8,680,945 | +0.9% | -9.4% | +26.8% |
| 2021 | 8,987,120 | +3.5% | -5.5% | +19.7% |
| 2022 | 9,444,116 | +5.1% | -3.0% | +16.5% |
| 2023 | 9,977,217 | +5.6% | -1.0% | +13.4% |
| 2024 | 10,227,266 | +2.5% | -0.5% | +5.6% |

## 5. Taxa de trancamento por grupo ao longo do tempo

Risco material para a série: se um grupo **mudar sua prática de classificação** de trancados entre anos, o crescimento em `QT_MAT` vira artefato contábil e não movimento de mercado. A tabela abaixo existe para detectar isso.

| Grupo | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | Δ max |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Cogna | 23% | 13% | 12% | 13% | 11% | 15% | 9% | 10% | 13% | 13% | **14 p.p.** |
| Vitru | 4% | 2% | 1% | 1% | 3% | 3% | 0% | 0% | 1% | 1% | **4 p.p.** |
| YDUQS | 39% | 43% | 44% | 41% | 37% | 31% | 46% | 62% | 66% | 54% | **35 p.p.** |
| Cruzeiro do Sul | 10% | 8% | 8% | 8% | 8% | 8% | 6% | 9% | 6% | 6% | **4 p.p.** |
| Ser Educacional | 12% | 23% | 26% | 23% | 22% | 24% | 36% | 11% | 8% | 10% | **27 p.p.** |
| Ânima | 16% | 18% | 24% | 24% | 30% | 40% | 42% | 34% | 15% | 14% | **28 p.p.** |
| Afya | 14% | 15% | 18% | 20% | 21% | 27% | 25% | 21% | 28% | 34% | **20 p.p.** |

## 5b. Crescimento em `QT_MAT` vs. em base de alunos

Teste direto de artefato. Se a base (`QT_MAT` + trancados) cai enquanto `QT_MAT` fica estável — ou vice-versa — o movimento é **reclassificação de vínculo**, não ganho ou perda real de aluno. Sinalizado quando as duas taxas divergem mais de 12 p.p. no mesmo ano.

| Grupo | Ano | YoY `QT_MAT` | YoY base | Divergência |
|---|---:|---:|---:|---:|
| Ser Educacional | 2022 | +0.4% | -18.0% | **+18.4 p.p.** |
| Ânima | 2023 | +1.5% | -12.7% | **+14.2 p.p.** |

> **Como ler:** nesses anos, o crescimento reportado pelo Censo para o grupo não deve ser interpretado como ganho/perda de mercado sem antes olhar a base de alunos. Use a definição de base de alunos para a série desses grupos.


## 6. Cobertura do mapeamento de grupos por ano

| Ano | % do mercado mapeado | % da rede privada | IES sem grupo |
|---|---:|---:|---:|
| 2015 | 44.7% | 59.0% | 2,035 |
| 2016 | 45.4% | 60.3% | 2,072 |
| 2017 | 46.6% | 61.8% | 2,090 |
| 2018 | 47.9% | 63.5% | 2,154 |
| 2019 | 49.7% | 65.5% | 2,202 |
| 2020 | 54.7% | 70.6% | 2,021 |
| 2021 | 56.0% | 72.9% | 2,114 |
| 2022 | 58.4% | 74.9% | 2,104 |
| 2023 | 60.3% | 76.0% | 2,073 |
| 2024 | 60.5% | 75.7% | 2,048 |

> A cobertura cai nos anos antigos porque o mapeamento é **pro-forma**: usa o perímetro atual dos grupos. IES adquiridas depois de 2015 já entram no grupo comprador em toda a série — que é o comportamento desejado para ler market share, mas significa que a cobertura de anos antigos reflete o perímetro de hoje.


## ⚠️ Alertas

- dimensões 3/4 com CO_UF preenchido (não deveriam ter geografia): 2022 (9,590 linhas)
- YDUQS: taxa de trancamento varia 35 p.p. na série — possível mudança de critério de declaração
- Ser Educacional: taxa de trancamento varia 27 p.p. na série — possível mudança de critério de declaração
- Ânima: taxa de trancamento varia 28 p.p. na série — possível mudança de critério de declaração
- Ser Educacional 2022: QT_MAT +0.4% vs base -18.0% (+18.4 p.p.) — provável reclassificação, não movimento real
- Ânima 2023: QT_MAT +1.5% vs base -12.7% (+14.2 p.p.) — provável reclassificação, não movimento real