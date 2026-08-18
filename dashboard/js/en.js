/* Dicionário de interface PT → EN.
 *
 * A chave é o texto em português exatamente como aparece no código ou no HTML (com o
 * espaçamento já normalizado). O que não estiver aqui cai de volta no português — nunca
 * quebra a tela. Para auditar o que falta: `__faltando()` no console, com a página em EN.
 */
import { registrarEN } from './i18n.js';

registrarEN({
  /* ------------------------------------------------------------- navegação */
  'Dashboards': 'Dashboards',
  '← Dashboards': '← Dashboards',
  'Price Action': 'Price Action',
  'Overview': 'Overview',
  'Key Players': 'Key Players',
  'Cursos': 'Programs',
  'Geografia': 'Geography',
  'Glossário': 'Glossary',
  'Censo da Educação Superior · INEP · {a}–{b}':
    'Higher Education Census · INEP · {a}–{b}',
  'Censo da Educação Superior · INEP': 'Higher Education Census · INEP',
  'Education Data House': 'Education Data House',
  'Carregando dados do Censo…': 'Loading Census data…',
  'Erro ao renderizar esta visão': 'Failed to render this view',

  /* --------------------------------------------------------------- filtros */
  'Ano': 'Year', 'UF': 'State', 'Modalidade': 'Delivery mode', 'Rede': 'Sector',
  'Todas': 'All', 'Presencial': 'On-campus', 'EAD': 'Distance learning',
  /* O Censo so tem presencial e EAD; "semipresencial" aparece no bloco de mensalidades,
   * porque e como as proprias faculdades vendem o formato hibrido. */
  'Semipresencial': 'Blended',
  'Pública': 'Public', 'Privada': 'Private', 'Limpar filtros': 'Clear filters',
  'Grupo': 'Group', 'Curso': 'Program', 'Estado': 'State',
  'Baixar dados (CSV)': 'Download data (CSV)', 'linhas': 'rows',
  'Baixar Excel': 'Download Excel', 'abas': 'sheets', 'Gerando…': 'Generating…',
  'Não foi possível gerar o arquivo': 'Could not generate the file',
  'Ponderado por valor de mercado': 'Market-cap weighted',
  'Agregado de dados do setor de ensino superior': 'Aggregated data on the higher education sector',
  'Índice ponderado por valor de mercado: soma de ações × preço dos papéis selecionados, rebaseada em 100. O peso acompanha o preço ao longo do período, como num índice. Cesta sempre em BRL.':
    'Market-cap weighted index: the sum of shares × price across the selected tickers, rebased to 100. Weights track prices through the period, as in an index. The basket is always in BRL.',
  'Composição no início do período': 'Composition at the start of the period',

  'Baixar todos os arquivos': 'Download every file',

  /* ------------------------------------------------------------ cards home */
  'Mercado': 'Market', 'Setor': 'Sector', 'Competição': 'Competition',
  'Portfólio': 'Portfolio', 'Praças': 'Local markets', 'Base de dados': 'Underlying data',
  'Referência': 'Reference',
  'Como o setor está performando agora? Retorno intraday, WTD, MTD, YTD ou desde a data que você escolher, comparação entre as companhias e um basket de Education contra IBOV e SMLL.':
    'How is the sector trading right now? Intraday, WTD, MTD, YTD or from any start date you pick, a side-by-side comparison of the listed names and an Education basket against IBOV and SMLL.',
  'Qual o tamanho do mercado e para onde ele vai? Matrículas, ingressantes e concluintes na série 2015–2024, a virada do EAD, mix por área, por curso e por UF.':
    'How big is the market and where is it heading? Enrollments, intake and graduates from 2015 to 2024, the shift to distance learning, and the mix by field, program and state.',
  'Escolha quem entra no confronto e compare escala, share, ritmo e mix. Depois, as 7 companhias abertas lado a lado — inclusive a distribuição regional e por curso da base de cada uma.':
    'Pick who goes head to head and compare scale, share, growth and mix. Then the 7 listed companies side by side — including the regional and program breakdown of each student base.',
  'Onde está a demanda e quem domina cada curso? Ranking por rótulo CINE, concentração e quantos alunos cada companhia aberta tem em Pedagogia, Direito, Enfermagem e nos demais cursos.':
    'Where is demand and who dominates each program? Ranking by CINE label, concentration, and how many students each listed company has in Education, Law, Nursing and every other program.',
  'Quem é o player mais forte em cada praça, em número de alunos? Mapa do líder por UF, matriz de força player × estado e o ranking dos maiores municípios com quem manda em cada um.':
    'Who is the strongest player in each local market, by student count? Leader map by state, a player × state strength matrix, and the largest cities with whoever leads each one.',
  'O que exatamente cada número quer dizer? Definição de cada termo, o que entra e o que não entra em cada métrica, e por que o dado do Censo pode divergir do que a companhia divulga.':
    'What exactly does each number mean? Every term defined, what each metric does and does not include, and why Census data can differ from what a company reports.',

  /* --------------------------------------------------------------- comuns */
  'Matrículas': 'Enrollments', 'Matrículas': 'Enrollments', 'matrículas': 'enrollments',
  'Ingressantes': 'New entrants', 'Concluintes': 'Graduates', 'Trancados': 'On leave',
  'Base de alunos': 'Student base', 'Cursos': 'Programs', 'Vagas': 'Seats',
  'IES': 'Institutions', 'Instituição': 'Institution', 'Mantenedora': 'Legal entity',
  'Organização': 'Type', 'Unidades': 'Units', 'Unid.': 'Units',
  'Share': 'Share', 'Δ Share': 'Δ Share', 'Δ Share vs {a}': 'Δ Share vs {a}',
  'Δ absoluto': 'Δ absolute', '% EAD': '% distance', '% Tranc.': '% on leave',
  '% do grupo': '% of group', 'Área': 'Field', 'Região': 'Region', 'Município': 'City',
  'Total': 'Total', 'Companhia': 'Company', 'Alunos': 'Students',
  'Nº cursos': 'No. of programs', 'Data': 'Date', 'Moeda': 'Currency',
  'presenciais': 'on-campus', 'totais': 'total', 'presencial': 'on-campus',
  'rede pública': 'public sector', 'rede privada': 'private sector',
  'matrículas {r}': '{r} enrollments', 'matrículas do Brasil': 'enrollments in Brazil',
  'Brasil': 'Brazil', 'vs {a}': 'vs {a}', '{v} alunos': '{v} students',
  'de {d}': 'of {d}', 'do curso': 'of the program', 'em': 'in',
  'Rede pública': 'Public sector', 'Rede privada': 'Private sector',
  'Independentes / não mapeado': 'Independents / unmapped',
  'Companhias abertas': 'Listed companies', 'Outros grupos': 'Other groups',
  'Listadas em bolsa': 'Listed on an exchange', 'Outros grupos relevantes': 'Other relevant groups',
  'Grupos mapeados': 'Mapped groups', 'Top 5 grupos': 'Top 5 groups',
  'entre grupos mapeados': 'across mapped groups', 'concentração do mercado': 'market concentration',
  '{p} do mercado': '{p} of the market', '{v} alunos · {q} grupos': '{v} students · {q} groups',

  /* -------------------------------------------------------------- overview */
  'Panorama do setor': 'Sector overview', 'Evolução': 'Trend',
  'Onde estão os alunos': 'Where the students are', 'Composição': 'Composition',
  'Modalidade': 'Delivery mode', 'Demanda': 'Demand',
  'Matrículas · recorte': 'Enrollments · selection',
  'Brasil — total': 'Brazil — total', 'todas as modalidades': 'all delivery modes',
  'Participação do recorte': 'Share of selection', 'do mercado nacional': 'of the national market',
  'IES no país': 'Institutions in Brazil', 'instituições ativas': 'active institutions',
  'Municípios com oferta': 'Cities with offerings', 'com curso presencial': 'with on-campus programs',
  'Matrículas por modalidade': 'Enrollments by delivery mode',
  'Matrículas por modalidade — {r}': 'Enrollments by delivery mode — {r}',
  'Participação do EAD': 'Share of distance learning',
  'Participação do EAD — {r}': 'Share of distance learning — {r}',
  'O presencial encolhe em termos absolutos; todo o crescimento do setor é EAD':
    'On-campus is shrinking in absolute terms; all sector growth is distance learning',
  'O EAD ultrapassou o presencial em 2024, pela primeira vez':
    'Distance learning overtook on-campus in 2024, for the first time',
  'Matrículas por UF': 'Enrollments by state',
  '15 maiores estados, com o peso de cada modalidade':
    '15 largest states, with the weight of each delivery mode',
  'Maiores cursos': 'Largest programs', '15 maiores rótulos CINE do país':
    "The country's 15 largest CINE labels",
  'Maiores grupos': 'Largest groups',
  'Quem são os principais players e qual a exposição de cada um ao EAD':
    'Who the main players are and how exposed each one is to distance learning',
  'Mix por área do conhecimento': 'Mix by field of study',
  'Maiores cursos — {r}': 'Largest programs — {r}',
  'Mix por área do conhecimento — {r}': 'Mix by field of study — {r}',
  'Recorte por sede da instituição, não por onde o aluno está — é a mesma regra usada nas tabelas de grupo. No EAD as duas coisas se separam: a matrícula é registrada na sede, então uma instituição de EAD carrega o país inteiro para o estado dela. "Matrículas por UF", ao lado, usa a geografia do Censo e não esta.':
    "Filtered by the institution's home state, not by where the student is — the same rule " +
    'used in the group tables. For distance learning the two come apart: the enrollment is ' +
    "recorded at the head office, so a distance-learning institution drags the whole country " +
    'into its own state. "Enrollments by state", alongside, uses the Census geography, not this one.',
  'O detalhe de {a} não vem nesta versão do arquivo, então estes dois gráficos continuam nacionais — o recorte não foi aplicado.':
    'The {a} detail is not bundled in this build, so these two charts remain national — the ' +
    'filter was not applied.',
  'Onde estão as matrículas — classificação CINE/UNESCO':
    'Where enrollments sit — CINE/UNESCO classification',
  'Série por modalidade': 'Series by delivery mode',
  'KPIs nacionais por ano': 'National KPIs by year',
  'Denominador: {d} em {a} — {t}. Consolidação por grupo econômico em perímetro pro-forma. Fora da tabela, {p} do mercado ({m} matrículas) está em instituições não mapeadas em grupo — bucket residual, não um player.':
    'Denominator: {d} in {a} — {t}. Consolidated by economic group on a pro-forma basis. Outside the table, {p} of the market ({m} enrollments) sits in institutions not mapped to any group — a residual bucket, not a player.',

  /* ----------------------------------------------------------- key players */
  'Escolha quem comparar': 'Choose who to compare',
  'Quem entra no confronto': 'Who goes head to head',
  'Começa com todas as companhias abertas. Clique para incluir ou remover qualquer grupo — os gráficos e a tabela reagem na hora.':
    'Starts with every listed company. Click to add or drop any group — charts and table react immediately.',
  'Retrato do conjunto': 'Snapshot of the selection',
  'Comparativo estrutural': 'Structural comparison',
  'Escala e eficiência': 'Scale and efficiency', 'Comparativo': 'Comparison',
  'Comparativo — {a}': 'Comparison — {a}',
  'Tamanho, ritmo, mix e produtividade por unidade — lado a lado':
    'Size, growth, mix and productivity per unit — side by side',
  'Trajetória': 'Trajectory', 'Market share': 'Market share', 'Volume': 'Volume',
  'Participação de mercado ao longo do tempo': 'Market share over time',
  'Quem ganhou e quem cedeu terreno na década': 'Who gained and who lost ground over the decade',
  'Matrículas em nível': 'Enrollments in absolute terms',
  'O tamanho absoluto por trás do share': 'The absolute size behind the share',
  'Posicionamento': 'Positioning', 'Escala × crescimento': 'Scale × growth',
  'Onde cada player está no mapa competitivo': 'Where each player sits on the competitive map',
  'Eixo horizontal: share atual. Vertical: CAGR da década. Tamanho da bolha: matrículas. O quadrante superior direito é escala com crescimento.':
    'Horizontal axis: current share. Vertical: decade CAGR. Bubble size: enrollments. The top-right quadrant is scale with growth.',
  'Share do mercado': 'Market share', 'crescimento zero': 'zero growth',
  'As companhias abertas': 'The listed companies',
  'Distribuição regional da base': 'Regional breakdown of the student base',
  'Onde cada companhia está exposta — pelo município de oferta, não pela sede':
    'Where each company is exposed — by city of delivery, not by headquarters',
  'Distribuição por curso da base': 'Program breakdown of the student base',
  'Quanto da base de cada companhia está em cada curso. Os 10 maiores rótulos CINE cobrem cerca de metade da base — por isso a visão por área do conhecimento, que é exaustiva como as regiões, fica ao lado.':
    'How much of each company’s base sits in each program. The 10 largest CINE labels cover roughly half the base — hence the field-of-study view next to it, which is exhaustive just like regions.',
  'Rótulo CINE': 'CINE label', 'Área do conhecimento': 'Field of study',
  'Estrutura competitiva do setor': 'Competitive structure of the sector',
  'Grupos econômicos': 'Economic groups', 'Consolidado por grupo': 'Consolidated by group',
  'IES do mesmo grupo econômico somadas — perímetro pro-forma':
    'Institutions of the same economic group added up — pro-forma perimeter',
  'Mix presencial × EAD por grupo': 'On-campus × distance mix by group',
  'Exposição de cada player à modalidade que está crescendo, em volume absoluto':
    'Each player’s exposure to the growing delivery mode, in absolute volume',
  'Grupos comparados': 'Groups compared',
  'clique nos chips para alterar': 'click the chips to change',
  'Matrículas somadas': 'Combined enrollments', 'Share conjunto': 'Combined share',
  'EAD do conjunto': 'Distance share of the set',
  'Alunos/unid.': 'Students/unit', 'Ingr./base': 'Intake/base',
  'Comparativo dos selecionados': 'Comparison of selected groups',
  'Série histórica por grupo': 'Historical series by group',
  'Todos os grupos econômicos': 'All economic groups',
  'Distribuição regional das abertas': 'Regional breakdown, listed companies',
  'Distribuição por curso das abertas': 'Program breakdown, listed companies',
  'Distribuição por área das abertas': 'Field breakdown, listed companies',
  /* as três camadas passaram a seguir a seleção dos chips (14/08/2026) */
  'Distribuição regional dos selecionados': 'Regional breakdown, selected groups',
  'Distribuição por curso dos selecionados': 'Program breakdown, selected groups',
  'Distribuição por área dos selecionados': 'Field breakdown, selected groups',
  'Composição da base': 'Base composition',
  'Composição da base — {q} grupos selecionados': 'Base composition — {q} groups selected',
  'YoY vs {a}': 'YoY vs {a}',
  'Tamanho hoje → share de {d} em {a}': 'Size today → share of {d} in {a}',
  'Ritmo → crescimento anual médio {b}–{a}': 'Pace → average annual growth {b}–{a}',
  'Exposição à modalidade': 'Delivery-mode exposure',
  'Mix presencial × EAD — em alunos': 'On-campus × distance mix — in students',
  'Mix presencial × EAD — em %': 'On-campus × distance mix — in %',
  'Quanto de cada modalidade cada player carrega, em número de matrículas — é o tamanho da operação':
    'How much of each delivery mode every player carries, in enrollments — this is the size of ' +
    'the operation',
  'A mesma leitura normalizada: aqui o grande e o pequeno ficam comparáveis, e o que aparece é a estratégia, não a escala':
    'The same read, normalised: here the large and the small become comparable, and what shows ' +
    'through is strategy rather than scale',
  'Mix de modalidade por grupo': 'Delivery-mode mix by group',
  '% Presencial': '% on campus',
  'Percentual da base de cada grupo por área geral CINE/UNESCO em {a} — {q} categorias que cobrem 100% da base, no mesmo formato da distribuição regional ao lado. Mede concentração de portfólio, não tamanho absoluto.':
    'Share of each group’s base by broad CINE/UNESCO field in {a} — {q} categories covering 100% ' +
    'of the base, in the same format as the regional breakdown beside it. It measures portfolio ' +
    'concentration, not absolute size.',
  'Percentual da base de cada grupo em cada curso, no mesmo formato da distribuição regional. Entram os maiores rótulos CINE do conjunto selecionado em {a} e, sempre, os dois maiores de cada grupo — é o que mantém visível um curso concentrado em um único player, como Medicina na Afya. O restante do portfólio vai para "Outros cursos" ({q} rótulos). Mede concentração de portfólio, não tamanho absoluto — para o volume por curso, veja o bloco de Cursos.':
    'Share of each group’s base in each program, in the same format as the regional breakdown. ' +
    'It includes the largest CINE labels across the selected set in {a} and, always, the two ' +
    'largest of each group — which is what keeps visible a program concentrated in a single ' +
    'player, such as Medicine at Afya. The rest of the portfolio goes to "Other programs" ({q} ' +
    'labels). It measures portfolio concentration, not absolute size — for volume by program, ' +
    'see the Programs block.',
  'Todos': 'All',
  'Categoria': 'Category', '% da base do grupo': '% of the group base',
  'Denominador do share: <strong>{d}</strong> em {a} — {t}. <em>Ingr./base</em> = ingressantes ÷ matrículas: proxy da velocidade de renovação da carteira — quanto maior, mais o grupo depende de captação nova para sustentar a base. <em>Alunos/unid.</em> usa apenas o presencial, já que unidade é proxy de campus físico. <em>% Tranc.</em> é o que explica boa parte da diferença contra a base divulgada pela companhia.':
    'Share denominator: <strong>{d}</strong> in {a} — {t}. <em>Intake/base</em> = new entrants ÷ enrollments: a proxy for how fast the book turns over — the higher it is, the more the group depends on new intake to sustain its base. <em>Students/unit</em> uses on-campus only, since a unit is a proxy for a physical campus. <em>% on leave</em> explains much of the gap against the base a company reports.',
  'Denominador: <strong>{d}</strong> em {a} — {t}. <em>Unidades</em> = pares distintos IES × município no presencial (proxy de campus; o Censo não traz identificador de campus). <em>% Tranc.</em> = trancados ÷ matrículas — varia de 0,7% a 88% entre grupos. <em>Independentes</em> é bucket residual, não player: fica fora do Top 5 e do HHI.':
    'Denominator: <strong>{d}</strong> in {a} — {t}. <em>Units</em> = distinct institution × city pairs on campus (a campus proxy; the Census carries no campus identifier). <em>% on leave</em> = students on leave ÷ enrollments — it ranges from 0.7% to 88% across groups. <em>Independents</em> is a residual bucket, not a player: it stays out of the Top 5 and of the HHI.',
  'Percentual da base de cada companhia por área geral CINE/UNESCO em {a} — {q} categorias que cobrem 100% da base, no mesmo formato da distribuição regional ao lado. Mede concentração de portfólio, não tamanho absoluto.':
    'Share of each company’s base by broad CINE/UNESCO field in {a} — {q} categories covering 100% of the base, in the same format as the regional breakdown beside it. It measures portfolio concentration, not absolute size.',
  'Percentual da base de cada companhia em cada curso, no mesmo formato da distribuição regional. Os 10 rótulos CINE exibidos são os maiores do conjunto das abertas em {a}; o restante do portfólio entra em "Outros cursos" ({q} rótulos). Mede concentração de portfólio, não tamanho absoluto — para o volume por curso, veja o bloco de Cursos.':
    'Share of each company’s base in each program, in the same format as the regional breakdown. The 10 CINE labels shown are the largest across the listed companies in {a}; the rest of the portfolio falls into "Other programmes" ({q} labels). It measures portfolio concentration, not absolute size — for volume by program, see the Programs dashboard.',
  'A distribuição por região e por curso exige o detalhe por IES de {a}, não incluído nesta versão de arquivo único — só o ano mais recente vem embutido. Rode <code>python run_dashboard.py</code> para a série completa.':
    'The regional and program breakdowns require the institution-level detail for {a}, which is not bundled in this single-file build — only the most recent year is embedded. Run <code>python run_dashboard.py</code> for the full series.',

  /* --------------------------------------------------------------- cursos */
  'Mercado por curso': 'Market by program', 'Cursos por matrícula': 'Programs by enrollment',
  'Rótulo CINE padronizado — o nome livre da IES não é comparável entre instituições':
    'Standardised CINE label — the free-form name given by each institution is not comparable',
  'Curso (rótulo CINE)': 'Program (CINE label)',
  'Concorrência dentro de um curso': 'Competition within a program',
  'Matrículas no curso': 'Enrollments in the program', 'Top 3 grupos': 'Top 3 groups',
  'exclui bucket Independentes': 'excludes the Independents bucket',
  'HHI do curso': 'HHI of the program', 'Não mapeado': 'Unmapped',
  '{q} IES ofertam o curso': '{q} institutions offer the program',
  'Alunos por companhia aberta no curso': 'Students per listed company in the program',
  'Alunos por companhia aberta — {c}': 'Students per listed company — {c}',
  'Número de alunos, não share — quem tem a maior base neste curso específico':
    'Student count, not share — who has the largest base in this specific program',
  'Ranking de grupos no curso': 'Group ranking in the program',
  'Quem domina esse mercado específico, incluindo grupos fechados':
    'Who dominates this specific market, private groups included',
  'Ranking de IES no curso': 'Institution ranking in the program',
  'Instituições individuais, sem consolidar por grupo':
    'Individual institutions, not consolidated by group',
  'Share no curso': 'Share of program', 'Todos os cursos': 'All programs',
  /* seleção de grupos + pizza de share dentro do curso (14/08/2026) */
  'Maior grupo': 'Largest group',
  'Matrículas do maior grupo': 'Enrollments of the largest group',
  'Share do maior grupo no curso': "Largest group's share of the program",
  'Concentração': 'Concentration',
  'Market share no curso': 'Market share within the program',
  'Market share em {c}': 'Market share in {c}',
  'Fatia de cada player dentro do curso selecionado':
    "Each player's slice within the selected program",
  'Demais players do curso': 'All other players in the program',
  'Alunos por grupo — {c}': 'Students by group — {c}',
  'Alunos por grupo no curso selecionado': 'Students per group in the selected program',
  'Começa com as companhias abertas. Clique para incluir ou remover qualquer grupo — o gráfico de alunos e a pizza de share reagem na hora.':
    'Starts with the listed companies. Click to add or drop any group — the student chart and ' +
    'the share pie react immediately.',
  '40 maiores de {q} rótulos CINE — o CSV traz todos. Denominador: {t} matrículas {m} em {a}. Usa o rótulo CINE padronizado, não o nome livre dado pela IES (1.497 nomes livres para 381 rótulos). <Maior grupo> é o grupo econômico com mais matrículas naquele curso, com a fatia dele entre parênteses; instituições não mapeadas em grupo ficam fora dessa disputa.':
    'Largest 40 of {q} CINE labels — the CSV has them all. Denominator: {t} {m} enrollments in ' +
    '{a}. Uses the standardised CINE label, not the free-form name given by the institution ' +
    '(1,497 free-form names for 381 labels). <Largest group> is the economic group with the most ' +
    'enrollments in that program, with its slice in brackets; institutions not mapped to a group ' +
    'stay out of that contest.',
  'Alunos dos {q} grupos selecionados em {c} ({m}, {a}). Somados, eles têm {s} alunos no curso — {p} das {t} matrículas. Grupo com barra zerada não oferta o curso no recorte.':
    'Students of the {q} selected groups in {c} ({m}, {a}). Combined, they hold {s} students in ' +
    'the program — {p} of its {t} enrollments. A group with no bar does not offer the program in ' +
    'this selection.',
  'Denominador: as {t} matrículas de {c} ({m}, {a}) — o curso inteiro, não a soma dos selecionados. "Demais players do curso" reúne todo o resto, inclusive as instituições não mapeadas em grupo econômico; é o que impede a pizza de sugerir uma concentração que não existe.':
    'Denominator: the {t} enrollments of {c} ({m}, {a}) — the whole program, not the sum of the ' +
    'selected groups. "All other players in the program" gathers everything else, including ' +
    'institutions not mapped to an economic group; it is what stops the pie from suggesting a ' +
    'concentration that does not exist.',
  'Alunos por companhia no curso selecionado': 'Students per company in the selected program',
  'Grupos no curso selecionado': 'Groups in the selected program',
  'IES no curso selecionado': 'Institutions in the selected program',
  '40 maiores de {q} rótulos CINE — o CSV traz todos. Denominador: {t} matrículas {m} em {a}. Usa o rótulo CINE padronizado, não o nome livre dado pela IES (1.497 nomes livres para 381 rótulos).':
    'Largest 40 of {q} CINE labels — the CSV has them all. Denominator: {t} {m} enrollments in {a}. Uses the standardised CINE label, not the free-form name given by the institution (1,497 free-form names for 381 labels).',
  'Alunos das 7 companhias abertas em {c} ({m}, {a}). Somadas, as abertas têm {s} alunos no curso — {p} das {t} matrículas. Grupo com barra zerada não oferta o curso no recorte.':
    'Students of the 7 listed companies in {c} ({m}, {a}). Combined, they hold {s} students in the program — {p} of its {t} enrollments. A group with no bar does not offer the program in this selection.',
  'O detalhe por IES de {a} não está incluído nesta versão de arquivo único — só o ano mais recente vem embutido. Rode <code>python run_dashboard.py</code> para navegar a série completa.':
    'The institution-level detail for {a} is not bundled in this single-file build — only the most recent year is embedded. Run <code>python run_dashboard.py</code> to browse the full series.',

  /* ------------------------------------------------------------ geografia */
  'Distribuição geográfica': 'Geographic breakdown',
  'Quem lidera cada estado': 'Who leads each state', 'Mapa': 'Map',
  'Player líder por UF': 'Leading player by state',
  'Cada estado pintado com a cor do grupo com mais alunos na praça':
    'Each state painted in the colour of the group with the most students there',
  'Estados': 'States', 'Líder, vice e concentração em cada UF':
    'Leader, runner-up and concentration in each state',
  'Ordenável — clique no cabeçalho para achar as praças mais concentradas':
    'Sortable — click a header to find the most concentrated markets',
  'Força de cada player por praça': 'Strength of each player by market',
  'Matriz': 'Matrix', 'Share do player dentro de cada UF': 'Player share within each state',
  'Share do player dentro de cada UF — {a}': 'Player share within each state — {a}',
  'Lê-se por coluna: dentro daquele estado, qual fatia dos alunos é de cada grupo':
    'Read by column: within that state, what slice of students belongs to each group',
  'Abrir uma praça': 'Open a market', 'Competição local': 'Local competition',
  'Ranking de players no estado': 'Player ranking in the state',
  'Ranking de players em {u}': 'Player ranking in {u}',
  'Alunos e share dentro da UF selecionada': 'Students and share within the selected state',
  'Municípios': 'Cities', 'Maiores municípios do estado': 'Largest cities in the state',
  'Maiores municípios de {u}': 'Largest cities in {u}',
  'Com o player líder em cada um': 'With the leading player in each',
  'Maiores praças do país': 'Largest markets in the country',
  '40 maiores municípios e quem lidera cada um': '40 largest cities and who leads each',
  'Concentração da base e o grupo com mais alunos na cidade':
    'Base concentration and the group with the most students in the city',
  'Composição regional': 'Regional composition',
  'Regiões': 'Regions', 'Presencial × EAD por região': 'On-campus × distance by region',
  'O peso do EAD muda bastante entre regiões':
    'The weight of distance learning varies a lot across regions',
  'Ranking de UFs': 'State ranking',
  'Onde está a base de alunos e o peso do EAD em cada estado':
    'Where the student base is and how much distance learning weighs in each state',
  'Matrículas com geografia': 'Enrollments with geography',
  'de 5.570 no país': 'of 5,570 nationwide', 'Líder nacional': 'National leader',
  'UFs lideradas por abertas': 'States led by listed companies',
  'de {q} unidades da federação': 'of {q} states',
  '{v} alunos · {p}': '{v} students · {p}', 'sem oferta': 'no offering',
  'líder': 'leader', 'Líder': 'Leader', 'Vice': 'Runner-up',
  'Alunos do líder': 'Students of the leader', 'Share do líder': 'Leader share',
  'Share vice': 'Runner-up share', '% não mapeado': '% unmapped',
  'Grupos mapeados': 'Mapped groups', 'Alunos na UF': 'Students in the state',
  'Share na UF': 'Share of the state', '{v} matrículas na UF': '{v} enrollments in the state',
  '{p}% das matrículas do estado': '{p}% of the state enrollments',
  'Liderança por UF': 'Leadership by state', 'Matriz player × UF': 'Player × state matrix',
  'Players em {u}': 'Players in {u}', 'Municípios de {u}': 'Cities in {u}',
  'Municípios do país com líder': 'Cities nationwide with their leader',
  'Composição por região': 'Composition by region',
  'Cada célula é a fatia do grupo dentro do estado (denominador = matrículas {m} com geografia naquela UF). Colunas ordenadas por tamanho do estado; linhas, pelos 12 maiores grupos do país. Rótulo exibido a partir de 5%. Ler por coluna responde "quem manda nesta praça"; por linha, "onde este player está concentrado".':
    'Each cell is the group’s slice within the state (denominator = {m} enrollments with geography in that state). Columns are ordered by state size; rows, by the 12 largest groups in the country. Labels appear from 5% up. Reading by column answers "who runs this market"; by row, "where this player is concentrated".',
  'Geografia usa apenas as dimensões 1 e 2 do Censo e atribui o aluno ao município de oferta. No EAD, esse município é o do polo de apoio presencial — não a residência do aluno; um polo pequeno pode concentrar muitos alunos. Líder exclui o bucket "Independentes", que não é um player. {q} matrículas ficam fora do recorte geográfico com os filtros atuais (exterior/N.I. e o que os filtros excluem). A tabela mostra 40 municípios; o CSV traz todos os {t}.':
    'Geography uses only dimensions 1 and 2 of the Census and assigns each student to the city of delivery. In distance learning, that city is the local support hub — not where the student lives; a small hub can concentrate a lot of students. The leader excludes the "Independents" bucket, which is not a player. {q} enrollments fall outside the geographic scope under the current filters (abroad/not informed, plus whatever the filters exclude). The table shows 40 cities; the CSV has all {t}.',
  'A liderança por praça exige o detalhe por IES × município de {a}, não incluído nesta versão de arquivo único — só o ano mais recente vem embutido. Rode <code>python run_dashboard.py</code> para a série completa.':
    'Leadership by market requires the institution × city detail for {a}, which is not bundled in this single-file build — only the most recent year is embedded. Run <code>python run_dashboard.py</code> for the full series.',

  /* ------------------------------------------------------------- rankings */
  'O que estamos somando em cada player': 'What we are adding up under each player',
  'IES consideradas no grupo': 'Institutions counted in the group',
  'IES consideradas em {g} — {a}': 'Institutions counted in {g} — {a}',
  'A lista completa de instituições atribuídas ao grupo, com o número de alunos de cada uma. É esta lista que explica qualquer diferença contra o release da companhia.':
    'The full list of institutions assigned to the group, with the student count of each. This list is what explains any gap against the company’s earnings release.',
  '25 maiores IES': '25 largest institutions',
  'Instituições individuais, com o grupo a que pertencem':
    'Individual institutions, with the group they belong to',
  'Movimento competitivo': 'Competitive movement',
  'Ganho e perda de market share': 'Market share gains and losses',
  'Quem avançou e quem recuou contra o ano anterior':
    'Who advanced and who fell back versus the prior year',
  'Cursos que mais crescem': 'Fastest-growing programs',
  'Onde a demanda está se movendo': 'Where demand is moving',
  '20 maiores municípios': '20 largest cities',
  'Concentração geográfica da base': 'Geographic concentration of the base',
  'Composição de {g}': 'Composition of {g}', 'Todas as IES': 'All institutions',
  'Movimento de market share': 'Market share movement',
  'Todos os municípios': 'All cities', 'Crescimento por curso': 'Growth by program',
  'Apenas cursos com 20 mil+ matrículas em {a}, para evitar que bases pequenas dominem o ranking.':
    'Only programs with 20k+ enrollments in {a}, so small bases do not dominate the ranking.',
  '<strong>{q} IES</strong> somam <strong>{m}</strong> matrículas ({p} presenciais + {e} EAD) em {a}, {s} do mercado. Com os <strong>{tr}</strong> trancados, a <em>base de alunos</em> é <strong>{b}</strong> — taxa de trancamento de {tx}. O Censo cobre apenas graduação: pós, técnico e cursos livres não entram, e é por isso que o número pode divergir do release da companhia. Perímetro pro-forma: IES adquiridas contam no grupo em toda a série. A mantenedora de cada IES vai no CSV.':
    '<strong>{q} institutions</strong> add up to <strong>{m}</strong> enrollments ({p} on-campus + {e} distance) in {a}, {s} of the market. Adding the <strong>{tr}</strong> students on leave, the <em>student base</em> is <strong>{b}</strong> — a leave rate of {tx}. The Census covers undergraduate programs only: graduate, technical and free courses are out, which is why the figure can differ from the company’s release. Pro-forma perimeter: acquired institutions count in the group across the whole series. Each institution’s legal entity is in the CSV.',

  /* --------------------------------------------------------- price action */
  'Período': 'Period', 'Intraday': 'Intraday', 'Desde': 'From',
  '12 meses': '12 months', 'Máximo': 'Maximum', 'Máximo disponível': 'Longest available',
  'Tudo em BRL': 'Everything in BRL', 'Moeda local': 'Local currency',
  'Atualizar preços': 'Refresh prices', 'Atualizando…': 'Refreshing…',
  'Falha ao atualizar os preços': 'Failed to refresh prices',
  'Preços de {q} · fonte {f}': 'Prices as of {q} · source {f}',
  'Quem entra na comparação': 'Who goes into the comparison',
  'Seleção': 'Selection', 'Papéis comparados': 'Tickers compared',
  'Começa com as 7 companhias abertas do setor. Clique para incluir ou remover — o gráfico, as barras, a tabela e o basket reagem na hora.':
    'Starts with the 7 listed companies in the sector. Click to add or drop — chart, bars, table and basket react immediately.',
  'Retorno no período': 'Return over the period', 'Performance': 'Performance',
  'Retorno acumulado': 'Cumulative return', 'Retorno acumulado — {p}': 'Cumulative return — {p}',
  'Todos os papéis rebaseados em 100 no início do período — a leitura é de retorno relativo, não de preço':
    'Every ticker rebased to 100 at the start of the period — read it as relative return, not price',
  'Comparação': 'Comparison', 'Retorno por papel no período': 'Return by ticker over the period',
  'Retorno por papel — {p}': 'Return by ticker — {p}',
  'Ordenado do melhor para o pior desempenho': 'Sorted from best to worst performer',
  'Basket': 'Basket', 'Basket de Education × IBOV × SMLL': 'Education basket × IBOV × SMLL',
  'Cesta das companhias selecionadas contra os índices, no mesmo período':
    'Basket of the selected companies against the indices, over the same period',
  'Ponderado por base de alunos': 'Weighted by student base', 'Peso igual': 'Equal weight',
  'Tabela': 'Table', 'Retornos': 'Returns', 'Retorno por janela': 'Return by window',
  'Mesma leitura em todas as janelas usuais, mais o período escolhido acima':
    'The same read across every usual window, plus the period selected above',
  'Basket Education': 'Education basket', 'vs IBOV': 'vs IBOV', 'vs SMLL': 'vs SMLL',
  'IBOV {v} no período': 'IBOV {v} over the period',
  'SMLL {v} no período': 'SMLL {v} over the period',
  'Melhor e pior': 'Best and worst', 'pior': 'worst',
  'Na semana (WTD)': 'Week to date (WTD)', 'No mês (MTD)': 'Month to date (MTD)',
  'No ano (YTD)': 'Year to date (YTD)', 'Desde {d}': 'Since {d}',
  'Papel': 'Ticker', 'Tipo': 'Type', 'Último': 'Last', 'índice': 'index', 'ação': 'stock',
  'Retornos por janela': 'Returns by window',
  'Série de preços (fechamento ajustado)': 'Price series (adjusted close)',
  'Fechamento': 'Close', 'Retorno acumulado (base 100)': 'Cumulative return (base 100)',
  'Composição': 'Composition',
  'Os preços ainda não foram coletados. Rode <code>python scripts/06_fetch_precos.py</code> e recarregue esta página.':
    'Prices have not been collected yet. Run <code>python scripts/06_fetch_precos.py</code> and reload this page.',
  'Este snapshot de preços tem {h}h. Rode <code>python scripts/06_fetch_precos.py</code> para atualizar.':
    'This price snapshot is {h}h old. Run <code>python scripts/06_fetch_precos.py</code> to refresh it.',
  'Base 100 no primeiro pregão do período. Papel sem preço no início da janela entra quando passa a ser negociado — a VTRU3 só tem série a partir de 11/06/2024, quando a Vitru migrou a listagem da Nasdaq para a B3. Moeda: {m}.':
    'Base 100 at the first trading session of the period. A ticker with no price at the start of the window joins once it begins trading — VTRU3 only has a series from 11 Jun 2024, when Vitru moved its listing from Nasdaq to B3. Currency: {m}.',
  'tudo convertido para BRL': 'everything converted to BRL',
  'cada papel na moeda local': 'each ticker in its local currency',
  'Fechamento ajustado por proventos e desdobramentos. Intraday compara o último preço do snapshot contra o fechamento anterior. WTD parte do fechamento da última sexta; MTD, do último pregão do mês anterior; YTD, do último pregão do ano anterior. Preços coletados em {q}.':
    'Close adjusted for dividends and splits. Intraday compares the last price in the snapshot against the previous close. WTD starts from last Friday’s close; MTD, from the last session of the prior month; YTD, from the last session of the prior year. Prices collected on {q}.',
  'Cesta com peso igual entre os papéis selecionados.':
    'Basket with equal weight across the selected tickers.',
  'Cesta ponderada pela base de alunos de cada grupo no Censo {a} — o peso reflete o tamanho da operação, não a quantidade de papéis.':
    'Basket weighted by each group’s student base in the {a} Census — weight reflects the size of the operation, not the number of tickers.',
  'Fora da cesta neste período, por não ter preço no início da janela: {l}.':
    'Out of the basket for this period, for lack of a price at the start of the window: {l}.',
  'SMLL entra pelo SMAL11, o ETF que replica o índice.':
    'SMLL comes in through SMAL11, the ETF that tracks the index.',
  'Sem papel com preço no período.': 'No ticker has a price in this period.',

  /* ------------------------------------------------------------- glossário
   * Blocos inteiros: texto corrido com marcação inline vira um nó só, senão o inglês
   * sai picado. A chave é `bloco:<nome>`, declarada em `data-i18n-bloco` no HTML. */
  'bloco:fonte':
    `<p><strong>Source.</strong> Every figure on students, programs, institutions and geography
      comes from the <strong>Higher Education Census microdata</strong> published by
      <strong>INEP</strong>, covering 2015–2024. It is the same base behind the official
      statistics of Brazil's Ministry of Education. Nothing here is our own estimate: what we add
      is aggregation and consolidation by economic group.</p>
     <p><strong>The Census covers undergraduate programs only.</strong> Graduate degrees,
      technical courses, continuing education, free courses and exam-prep <em>are not in it</em>.
      When a company reports its "student base", that number often includes those products — and
      then the two figures are not comparable.</p>
     <p><strong>Expect divergence against the earnings release.</strong> Beyond scope, there are
      three structural causes: (i) Census enrollment excludes students on formal leave, whom
      companies usually keep in their base; (ii) the reference date is the census year, not the
      quarter of the release; (iii) some companies exclude students under their own criteria —
      Vitru, for one, has left out "unengaged" students since 1Q24. <strong>Diverging does not
      mean either side is wrong</strong>: it means the definitions differ.</p>
     <p><strong>Prices.</strong> The Price Action dashboard uses adjusted closing quotes from
      Yahoo Finance, captured on the date stamped in that dashboard. They are a snapshot, not a
      real-time quote.</p>`,
  'bloco:gl-metricas':
    `<div><dt>Enrollment (QT_MAT)</dt><dd>students with an active link to a program on the Census
      date — "attending" or "graduated" in the year. <strong>Excludes students on formal
      leave.</strong> It is the primary metric across this dashboard, because it is INEP's
      official definition, applied identically to all 2,561 institutions in the country.</dd></div>
     <div><dt>On leave</dt><dd>enrollments formally suspended on the Census date. They sit outside
      QT_MAT. The rate varies enormously across groups — from 0.7% to 87.6% of the base — so it
      cannot be treated as noise.</dd></div>
     <div><dt>Student base</dt><dd>enrollments plus students on leave. It appears here because it
      is close to the concept several companies use when reporting a base, but it is not the
      primary metric.</dd></div>
     <div><dt>New entrants</dt><dd>students who joined the program in the reference year, through
      any admission route.</dd></div>
     <div><dt>Graduates</dt><dd>students who completed the program in the reference year.</dd></div>
     <div><dt>Intake/base</dt><dd>new entrants divided by enrollments. A proxy for how fast the
      book turns over: the higher it is, the more the group depends on new intake to sustain its
      base.</dd></div>`,
  'bloco:gl-modalidade':
    `<div><dt>On-campus</dt><dd>program delivered in person. Always blue in the charts — it is the
      installed physical footprint.</dd></div>
     <div><dt>Distance learning</dt><dd>remote delivery. Always orange in the charts — it is what
      grows. In 2024 it overtook on-campus for the first time.</dd></div>
     <div><dt>Public / private sector</dt><dd>classification of the institution's sponsor. The
      dashboard covers both, but the competitive analysis is essentially about the private
      sector.</dd></div>
     <div><dt>Institution (IES)</dt><dd>the higher education institution, which is the Census unit
      of record. An economic group is the sum of several institutions.</dd></div>
     <div><dt>Institution type</dt><dd>university, university center, college, federal institute or
      CEFET — the regulatory category, which determines how freely the institution can open new
      programs.</dd></div>
     <div><dt>Units</dt><dd>a campus proxy: distinct institution × city pairs with on-campus
      offerings. The Census carries no campus identifier, so two campuses in the same city count
      as one.</dd></div>`,
  'bloco:gl-grupos':
    `<div><dt>Economic group</dt><dd>the set of institutions under the same controlling
      shareholder. Mapped institution by institution, with 43 groups covering 60.5% of the market
      and 75.7% of the private sector.</dd></div>
     <div><dt>Pro-forma perimeter</dt><dd>each group keeps today's composition across the whole
      series: an institution acquired in 2022 counts in the buyer from 2015 onward. That is what
      allows share to be read without artificial M&amp;A steps — but it <strong>does not reproduce
      what the company reported at the time</strong>.</dd></div>
     <div><dt>Independents</dt><dd>the residual bucket of whatever is not mapped to a group. It is
      not a player: it stays out of Top N, out of the HHI and out of any local leadership
      contest, but how much it represents is always stated.</dd></div>
     <div><dt>Market share</dt><dd>share of enrollments. Every screen states the denominator in
      use; when a delivery mode, sector or state filter is on, the denominator follows.</dd></div>
     <div><dt>HHI</dt><dd>Herfindahl-Hirschman index: the sum of squared market shares. It measures
      concentration — the higher it is, the less contested the market.</dd></div>
     <div><dt>YoY and CAGR</dt><dd>change against the prior year, and the compound annual growth
      rate over the full series.</dd></div>
     <div><dt>Δ Share</dt><dd>change in market share, in percentage points, against the prior year.
      Growing and gaining share are not the same thing: a company can grow and still lose share in
      a market that grows faster.</dd></div>`,
  'bloco:gl-geografia':
    `<div><dt>CINE label</dt><dd>the standardised program name under the International Standard
      Classification of Education (ISCED/CINE, UNESCO). There are 381 labels for 1,497 free-form
      names given by institutions — only the label is comparable across institutions.</dd></div>
     <div><dt>Field of study</dt><dd>the broad CINE grouping, in 11 fields. Unlike the label, it is
      exhaustive: it adds up to 100% of the base.</dd></div>
     <div><dt>City of delivery</dt><dd>the city where the program is delivered, which is how a
      student enters the geography — not the city of the institution's headquarters.</dd></div>
     <div><dt>Geography of distance learning</dt><dd>in distance programs the city is that of the
      <strong>local support hub</strong>, not where the student lives. A small hub can concentrate
      students from an entire region.</dd></div>
     <div><dt>Market leader</dt><dd>the group with the most students in that state or city,
      excluding the Independents bucket.</dd></div>`,
  'bloco:gl-precos':
    `<div><dt>Intraday, WTD, MTD, YTD</dt><dd>return since the open of the day, since last Monday,
      since the first session of the month and since the first session of the year,
      respectively.</dd></div>
     <div><dt>Adjusted close</dt><dd>closing price corrected for dividends and splits. Without that
      adjustment, the return of a stock that paid a dividend would look smaller than it was.</dd></div>
     <div><dt>Rebase 100</dt><dd>every series starts at 100 at the beginning of the chosen period,
      so the comparison is of relative return rather than of price.</dd></div>
     <div><dt>Education basket</dt><dd>a basket of the selected companies. Under the default
      weighting each stock enters in proportion to its <strong>student base in the Census</strong>
      — which ties the portfolio to the real size of the operation instead of treating every
      company as equal. The alternative is equal weight.</dd></div>
     <div><dt>IBOV and SMLL</dt><dd>the Ibovespa and B3's small-cap index. SMLL comes in through
      <strong>SMAL11</strong>, the ETF that tracks it, because that is the tradable series
      available.</dd></div>
     <div><dt>Everything in BRL</dt><dd>Afya trades in dollars on Nasdaq. Under this option its
      return is converted at the daily exchange rate, which is what makes the comparison against
      IBOV and SMLL honest. Under "local currency", each stock returns in its own currency.</dd></div>`,

  /* ---------------------------------------------------------- mensalidades
   * "Mensalidade" nao tem equivalente exato: em ingles o preco de faculdade e anual
   * (tuition). Como o dado aqui e o valor mensal publicado pela propria instituicao,
   * a traducao diz "monthly tuition" em vez de so "tuition", senao o leitor de fora
   * le o numero como anuidade e erra a ordem de grandeza por 12.                    */
  'Mensalidades': 'Monthly tuition',
  'Preço': 'Price',
  'Quanto cada player consegue cobrar? Mensalidade de tabela dos cursos mais procurados, por modalidade e por instituição, e o quanto o preço varia de uma praça para outra dentro da mesma faculdade.':
    'How much can each player charge? List-price monthly tuition for the most sought-after ' +
    'programs, by delivery mode and by institution, plus how much the price moves from one ' +
    'market to another inside the same school.',
  'mensalidade mediana': 'median monthly tuition',
  'Mensalidade publicada': 'Published monthly tuition',
  'sem coleta nesta modalidade': 'not collected for this delivery mode',
  'curso': 'program', 'cursos': 'programs',
  'instituição': 'institution', 'instituições': 'institutions',
  'Mediana': 'Median', 'Mínimo': 'Minimum', 'Máximo': 'Maximum',
  'Cobertura da coleta': 'Collection coverage',
  'preços por unidade · coleta de {d}': 'unit-level prices · collected {d}',
  'Coleta de {d} · {o} preços por unidade': 'Collected {d} · {o} unit-level prices',

  'Como ler': 'How to read it',
  'Preço de tabela, não ticket líquido': 'List price, not net ticket',
  'bloco:mensalidades-metodo':
    `The figure is what the institution publishes on its own website for someone
      enrolling today. A company books revenue <em>after</em> scholarships, acquisition discounts,
      FIES/ProUni and bad debt — so <strong>this number does not reconcile with the earnings
      release and should not be used for that</strong>. It is here to compare positioning across
      players and to track how the list price moves over time. The published tuition is the
      <strong>simple average of the cheapest price at each campus or hub</strong>; when there is a
      "was R$ 100, now R$ 79" promotion, the lower one counts. The distance-learning sample is
      taken in state capitals, so it tends to sit above the national "from R$" headline, which
      usually comes from hubs in smaller cities.`,

  'Quem cobra mais': 'Who charges more',
  'Mensalidade mediana por instituição': 'Median monthly tuition by institution',
  'Mediana dos cursos acompanhados em cada instituição, na modalidade selecionada — a mediana evita que Odontologia e Medicina Veterinária dominem a leitura':
    'Median across the programs tracked at each institution, for the selected delivery mode — ' +
    'the median keeps Dentistry and Veterinary Medicine from dominating the reading',
  'Mensalidade por instituição': 'Monthly tuition by institution',
  'Nenhuma instituição coletada nesta modalidade': 'No institution collected for this delivery mode',
  'Cursos acompanhados': 'Programs tracked',
  'cursos acompanhados': 'programs tracked',
  'Faixa': 'Range',

  'Curso a curso': 'Program by program',
  'Mensalidade por curso e instituição': 'Monthly tuition by program and institution',
  'bloco:mensalidades-spread':
    `The <em>Spread</em> column shows how much more the priciest charges over the cheapest for
     that program: it is where brand premium shows up, and where price has already converged`,
  'Spread': 'Spread',
  'Curso × instituição': 'Program × institution',
  'Sem dados nesta modalidade': 'No data for this delivery mode',

  'Dispersão dentro da mesma instituição': 'Spread inside the same institution',
  'Praça': 'Market',
  'Da unidade mais barata à mais cara': 'From the cheapest campus to the priciest',
  'Uma mensalidade única por instituição esconde a diferença entre praças. Escolha o curso para ver a faixa efetivamente praticada.':
    'A single tuition figure per institution hides the gap between markets. Pick a program to ' +
    'see the range actually charged.',
  'Dispersão por unidade': 'Spread by campus',
  'Nenhuma instituição publica preço por unidade neste curso.':
    'No institution publishes a per-campus price for this program.',
  'Fora do gráfico: {q} instituição(ões) que só publicam um "a partir de" nacional — {l}.':
    'Not charted: {q} institution(s) that publish only a national "from R$" figure — {l}.',
  '* {l} publicam apenas um "a partir de" nacional, sem preço por unidade. O valor é um piso, não a média das praças — o spread contra as demais tende a ficar exagerado.':
    '* {l} publish only a national "from R$" figure, with no per-campus price. That value is a ' +
    'floor, not an average across markets — the spread against the others tends to look inflated.',
  'Fora da comparação de EAD: {q}. A coleta trouxe apenas {p} polo(s) — abaixo do mínimo de {m} para publicar a linha como média de praças{c}. A instituição oferta EAD; o que falta é cobertura, não o curso.':
    'Excluded from the distance-learning comparison: {q}. The crawl returned only {p} hub(s) — ' +
    'below the minimum of {m} required to publish the row as an average across markets{c}. The ' +
    'institution does offer distance learning; what is missing is coverage, not the program.',
  ', contra os {r} polos de quem está na tela': ', against the {r} hubs behind the rows shown',

  /* ------------------------------------------- geografia: capilaridade (14/08/2026) */
  'Capilaridade — onde cada player realmente está': 'Reach — where each player actually is',
  'Quem entra no mapa': 'Who goes on the map',
  'bloco:geo-capilaridade':
    'Starts with the listed companies. Each bubble is a city where the group has students; ' +
    'the size is the number of students. The mesh comes from the Census city of ' +
    '<em>delivery</em> — not from the head-office address.',
  'Estrutura instalada — {q} municípios': 'Installed footprint — {q} cities',
  'Alcance digital — {q} municípios': 'Digital reach — {q} cities',
  '{q} municípios · {v} alunos': '{q} cities · {v} students',
  '(mostrando os {q} primeiros)': '(showing the first {q})',
  'Um mapa por grupo, na mesma escala — lado a lado é possível comparar a forma do alcance, o que um mapa só com todos sobrepostos não permite':
    'One map per group, on the same scale — side by side you can compare the shape of the ' +
    'reach, which a single map with everything overlaid does not allow',
  'Capilaridade — {g}': 'Reach — {g}',
  'Escolha o grupo para ver a forma do alcance dele no país. A escala das bolhas é comum a todos os grupos, então trocar de grupo mantém a comparação honesta.':
    'Pick the group to see the shape of its reach across the country. The bubble scale is ' +
    'shared across all groups, so switching groups keeps the comparison honest.',
  'Só presencial': 'On-campus only',
  'Só EAD': 'Distance learning only',
  'Overlap na praça': 'Overlap in the local market',
  'Quem está neste município': 'Who is in this city',
  'Quem está em {m}': 'Who is in {m}',
  'Cada grupo selecionado nos chips lá em cima, com o que ele tem nesta cidade — presencial e EAD separados. Barra vazia significa que o grupo não está aqui.':
    'Every group selected in the chips above, with what it holds in this city — on-campus and ' +
    'distance learning split apart. An empty bar means the group is not here.',
  'Alunos na praça': 'Students in the market',
  'Dos selecionados': 'Of the selected',
  'presentes aqui': 'present here',
  'Peso do conjunto': 'Weight of the set',
  'Líder da praça': 'Market leader',
  'da praça': 'of the market',
  'alunos': 'students',
  'ausente': 'absent',
  'Share na praça': 'Share of the market',
  'Overlap em {m}': 'Overlap in {m}',
  'Sem dados para esta praça.': 'No data for this market.',
  'Denominador: as {t} matrículas de {m} em {a}. Barra vazia é grupo que não tem aluno nesta cidade — está na lista de propósito, porque ausência numa praça é informação competitiva. O rótulo do fim da barra traz o total do grupo e a fatia dele na praça.':
    'Denominator: the {t} enrollments of {m} in {a}. An empty bar is a group with no students ' +
    'in this city — it stays on the list on purpose, because absence from a market is ' +
    'competitive information. The label at the end of each bar carries the group total and its ' +
    'share of the market.',
  'Alcance comparado': 'Reach compared',
  'Municípios com aluno, por grupo — o grupo no mapa fica destacado':
    'Cities with students, by group — the group on the map is highlighted',
  'Municípios': 'Cities',
  'Presencial — {q} municípios com campus': 'On campus — {q} cities with a campus',
  'EAD — {q} municípios com polo': 'Distance learning — {q} cities with a hub',
  'A bolha é o número de ALUNOS no município — não o número de campi nem de polos —, dimensionada pela raiz, porque em escala linear São Paulo apagaria todo o interior, que é o que interessa aqui. A posição é o centroide do município ({q} dos {t} têm coordenada), não o endereço de nenhuma unidade: o Censo dá o município de oferta, e não a rua. No presencial o município é onde o curso é dado; no EAD, onde está o polo.':
    'The bubble is the number of STUDENTS in the city — not the number of campuses or hubs — ' +
    'sized by the square root, because on a linear scale São Paulo would wipe out the whole ' +
    'interior, which is what matters here. The position is the city centroid ({q} of {t} have ' +
    'coordinates), not the address of any unit: the Census gives the city of delivery, not the ' +
    'street. On campus, the city is where the programme is taught; in distance learning, where ' +
    'the hub is.',
  'A bolha é sempre ALUNO, nunca unidade: no presencial, matrículas no município onde o curso é dado; no EAD, matrículas no município do polo — e o polo é mesmo onde o aluno está, não a sede (a Unopar, sede no PR, distribui seus alunos por 27 UFs, e o PR fica com 5%). A CONTAGEM de municípios é proxy de campi e de polos, e é um PISO: o Censo não traz identificador de campus nem de polo, então dois campi na mesma cidade contam como um. Estes dois mapas ignoram o filtro de modalidade de propósito — com "EAD" selecionado, o mapa do presencial ficaria vazio e pareceria que o grupo não tem campus. O filtro de rede continua valendo.':
    'The bubble is always a STUDENT, never a unit: on campus, enrollments in the city where the ' +
    'programme is taught; in distance learning, enrollments in the hub city — and the hub really ' +
    'is where the student is, not the head office (Unopar, headquartered in Paraná, spreads its ' +
    'students across all 27 states, and Paraná keeps 5%). The COUNT of cities is a proxy for ' +
    'campuses and hubs, and it is a FLOOR: the Census carries no campus or hub identifier, so ' +
    'two campuses in the same city count as one. These two maps ignore the delivery-mode filter ' +
    'on purpose — with "distance learning" selected, the on-campus map would come up empty and ' +
    'look as though the group had no campuses. The sector filter still applies.',
  'Até': 'To',
  '{p} até {d}': '{p} to {d}',
  /* ------------------------------ regulatório: feed diário do DOU (17/08/2026) */
  'Últimas publicações': 'Latest publications',
  'O que saiu no Diário Oficial, triado por relevância':
    'What came out in the Official Gazette, screened by relevance',
  'bloco:rg-diario-metodo':
    'Everything the Ministry of Education published in Section 1, most recent first. ' +
    'Relevance is assigned by a <strong>deterministic rule</strong>, aimed at equity ' +
    'investors: acts of a federal university or institute, appointments and public ' +
    'examinations are <em>low</em>; rules on distance learning, Medicine, FIES or ProUni ' +
    'and measures suspending intake or contracts are <em>high</em>. Each row shows ' +
    '<strong>why</strong> it was classified that way — and nothing here was checked by ' +
    'hand, unlike the theme tabs.',
  'Abrir no DOU': 'Open in the Gazette',
  'Classificado como {r} porque: {m}': 'Classified as {r} because: {m}',
  'Publicações do DOU': 'Gazette publications',
  'Motivo da classificação': 'Reason for the classification',
  'Ementa': 'Summary',
  'Nenhuma publicação nesta relevância.': 'No publication at this relevance level.',
  'O feed diário ainda não foi coletado nesta cópia. Rode <code>python scripts/11_fetch_dou_diario.py</code>.':
    'The daily feed has not been collected in this build. Run <code>python ' +
    'scripts/11_fetch_dou_diario.py</code>.',
  '{n} publicações em {d} dias · {a} alta · {m} média · {b} baixa':
    '{n} publications over {d} days · {a} high · {m} medium · {b} low',
  'Seção 1 do Diário Oficial, órgão Ministério da Educação, coletado em {d}. A relevância é de regra, não de leitura: ninguém conferiu estes atos um a um — para o que foi conferido e escrito, use as abas de tema. Ato que cite uma companhia aberta entra sempre como alta, e o nome dela aparece ao lado.':
    'Section 1 of the Official Gazette, Ministry of Education, collected on {d}. Relevance ' +
    'comes from a rule, not from reading: nobody checked these acts one by one — for what ' +
    'was checked and written up, use the theme tabs. An act naming a listed company always ' +
    'enters as high, and the company name appears beside it.',
  'Grupo citado': 'Group cited',
  'Instituição citada': 'Institution cited',
  'Cód. e-MEC': 'e-MEC code',
  'Alcance': 'Reach',
  'Capilaridade dos grupos selecionados': 'Reach of the selected groups',
  'Capilaridade — {q} grupos selecionados': 'Reach — {q} groups selected',
  'Sobreponha os grupos para ver quem cobre o país e quem se concentra':
    'Overlay the groups to see who covers the country and who concentrates',
  'Cada bolha é um município onde o grupo tem aluno, dimensionada pela raiz do número de alunos — em escala linear São Paulo apagaria todo o interior, que é o que interessa aqui. A posição é o centroide do município ({q} dos {t} têm coordenada), não o endereço de nenhuma unidade: o Censo dá o município de oferta, e não a rua.':
    'Each bubble is a city where the group has students, sized by the square root of the ' +
    'student count — on a linear scale São Paulo would wipe out the whole interior, which ' +
    'is exactly what matters here. The position is the city centroid ({q} of {t} have ' +
    'coordinates), not any unit address: the Census gives the city of delivery, not the street.',
  'Pegada física × pegada digital': 'Physical footprint × digital footprint',
  'Estrutura instalada': 'Installed footprint',
  'Estrutura instalada — presencial': 'Installed footprint — on campus',
  'Alcance digital': 'Digital reach',
  'Alcance digital — EAD': 'Digital reach — distance learning',
  'Onde há campus de verdade — é o que custa caro e não se move':
    'Where there is an actual campus — the expensive part, and the part that cannot move',
  'Onde o aluno de EAD está, pelo município de oferta':
    'Where the distance-learning student is, by city of delivery',
  'Leitura': 'How to read it',
  'Quantos municípios cada modalidade alcança': 'How many cities each delivery mode reaches',
  'A razão entre as duas colunas é quanto do alcance vem de operação leve':
    'The ratio between the two columns is how much of the reach comes from an asset-light operation',
  'Municípios no total': 'Cities in total',
  'Com presencial': 'With on-campus',
  'Com EAD': 'With distance learning',
  '% sem estrutura física': '% with no physical footprint',
  'Alunos por município': 'Students per city',
  'Capilaridade por grupo': 'Reach by group',
  'Estes dois mapas e esta tabela ignoram o filtro de modalidade de propósito — com "EAD" selecionado, o mapa do presencial ficaria vazio e pareceria que o grupo não tem campus. O filtro de rede continua valendo. <% sem estrutura física> é a fatia dos municípios alcançados em que não há um único aluno presencial: é alcance de operação leve, com custo fixo e margem diferentes de um campus.':
    'These two maps and this table ignore the delivery-mode filter on purpose — with ' +
    '"distance learning" selected, the on-campus map would come up empty and look as though ' +
    'the group had no campuses. The sector filter still applies. <% with no physical ' +
    'footprint> is the share of reached cities without a single on-campus student: ' +
    'asset-light reach, with a different fixed cost and margin from a campus.',
  'Sobreposição competitiva': 'Competitive overlap',
  'Disputa': 'Contest',
  'Onde os selecionados se cruzam': 'Where the selected groups overlap',
  'Onde os {q} selecionados se cruzam': 'Where the {q} selected groups overlap',
  'Cor por quantos dos grupos escolhidos estão presentes no município':
    'Coloured by how many of the chosen groups are present in the city',
  'Só um grupo': 'One group only',
  'Dois grupos': 'Two groups',
  'Três ou mais': 'Three or more',
  'grupos': 'groups',
  'Dos {t} municípios alcançados por pelo menos um dos selecionados, {d} têm mais de um deles presente — {p} do território coberto. Presença aqui é ter ao menos um aluno no município, em qualquer modalidade; não mede quem é mais forte, mede onde há disputa.':
    'Of the {t} cities reached by at least one of the selected groups, {d} have more than one ' +
    'of them present — {p} of the covered territory. Presence here means having at least ' +
    'one student in the city, in any delivery mode; it does not measure who is stronger, it ' +
    'measures where there is a contest.',
  'Exclusividade': 'Exclusivity',
  'Praça exclusiva × disputada': 'Exclusive × contested markets',
  'Quantos municípios cada grupo tem só para si': 'How many cities each group has to itself',
  'Só ele': 'Alone',
  'Divide': 'Shares',
  '% exclusivo': '% exclusive',
  'Exclusividade por município': 'Exclusivity by city',

  /* -------------------------------------------------- geografia: e-MEC (14/08/2026) */
  'Qualidade e situação regulatória': 'Quality and regulatory standing',
  'e-MEC': 'e-MEC',
  'IGC médio por grupo': 'Average IGC by group',
  'IGC por grupo': 'IGC by group',
  'Índice Geral de Cursos, de 1 a 5. Só entram IES com nota publicada':
    'General Programme Index, 1 to 5. Only institutions with a published score are included',
  'IES com nota': 'institutions with a score',
  'IES no grupo': 'Institutions in the group',
  'de': 'of',
  'Restrições vigentes': 'Restrictions in force',
  'IES com sinalização no e-MEC': 'Institutions flagged in e-MEC',
  'Suspensão de ingresso, de FIES ou de ProUni, e procedimentos de supervisão':
    'Suspension of intake, of FIES or of ProUni, and supervisory proceedings',
  'Sinalização': 'Flag',
  'Os dados do e-MEC não estão nesta cópia. Rode <code>python scripts/10_ingest_emec.py</code> para gerar <code>data/emec.json</code> a partir de <code>Dados_GEO.xlsx</code>.':
    'The e-MEC data is not in this build. Run <code>python scripts/10_ingest_emec.py</code> ' +
    'to generate <code>data/emec.json</code> from <code>Dados_GEO.xlsx</code>.',
  'IGC do e-MEC, de 1 a 5, processado em {d}. A média é só entre as IES COM nota — IES sem avaliação publicada não entra como zero, que seria lê-la como péssima. A coluna do tooltip mostra quantas das IES do grupo têm nota. Base casada: {c} IES, cobrindo 99,9% das matrículas de 2024.':
    'e-MEC IGC, 1 to 5, processed on {d}. The average covers only institutions WITH a score ' +
    '— one without a published assessment does not enter as zero, which would read as ' +
    'terrible. The tooltip shows how many of the group institutions carry a score. Matched ' +
    'base: {c} institutions, covering 99.9% of 2024 enrollments.',
  '{t} IES com restrição vigente, das quais {g} pertencem a algum grupo mapeado — as 15 primeiras na tela, todas no Excel. Ficam de fora as sinalizações que não são restrição, como "Unificação de Mantidas" e "Credenciamento Prévio", que são as duas mais numerosas e listá-las aqui faria o quadro parecer pior do que é.':
    '{t} institutions under a restriction in force, {g} of them inside a mapped group — the ' +
    'first 15 on screen, all of them in the Excel file. Flags that are not restrictions are ' +
    'left out, such as "Unification of Maintained Entities" and "Prior Accreditation", which ' +
    'are the two most numerous and would make the picture look worse than it is.',
  /* ------------------------------- price action: fechamento diario (14/08/2026) */
  'Preço de fechamento': 'Closing price',
  'Fechamento por dia': 'Close by day',
  'Preços': 'Prices',
  'Pregão': 'Session',
  'Preço de fechamento, dia a dia': 'Closing price, day by day',
  'Preço de fechamento, dia a dia — {p}': 'Closing price, day by day — {p}',
  'Uma linha por pregão, do mais recente para o mais antigo, com o fechamento ajustado de cada papel selecionado. A série inteira sai no Excel.':
    'One row per trading session, most recent first, with the adjusted close of each selected ' +
    'ticker. The full series comes out in the Excel file.',
  'Os 60 pregões mais recentes do período na tela; o Excel traz os {q} do período inteiro. Fechamento AJUSTADO — incorpora proventos e desdobramentos, então um valor antigo pode não bater com a cotação exibida naquele dia; é a série correta para retorno. Célula vazia é pregão sem negócio para aquele papel, ou papel ainda não listado. Moeda: {m}.':
    'The 60 most recent sessions of the period on screen; the Excel file carries all {q} of ' +
    'the period. ADJUSTED close — it incorporates dividends and splits, so an old value may ' +
    'not match the quote shown on that day; it is the correct series for returns. An empty ' +
    'cell is a session with no trade for that ticker, or a ticker not yet listed. Currency: {m}.',
  'Fechamento AJUSTADO: incorpora proventos e desdobramentos, então é a série que serve para calcular retorno — e por isso o valor de um dia antigo pode não bater com a cotação que o papel exibia naquele pregão. Papéis não se comparam em nível aqui; para comparar, use base 100. Moeda: {m}.':
    'ADJUSTED close: it incorporates dividends and splits, so it is the series to compute ' +
    'returns from — and that is why an old value may not match the quote the ticker showed on ' +
    'that session. Tickers do not compare in level here; to compare, use base 100. ' +
    'Currency: {m}.',
  'Fechamento ajustado por proventos e desdobramentos. WTD parte do fechamento da última sexta; MTD, do último pregão do mês anterior; YTD, do último pregão do ano anterior. Preços coletados em {q}.':
    'Close adjusted for dividends and splits. WTD starts from last Friday\u2019s close; MTD, ' +
    'from the last session of the previous month; YTD, from the last session of the previous ' +
    'year. Prices collected on {q}.',
  'Mais barata': 'Cheapest',
  'Mais cara': 'Priciest',
  'unidades/polos': 'campuses/hubs',
  'Unidades/polos': 'Campuses/hubs',
  'O ponto é a mensalidade publicada (média simples do menor preço de cada unidade). A faixa vai da unidade mais barata à mais cara: {t} unidades/polos observados.':
    'The dot is the published tuition (simple average of the cheapest price at each campus). ' +
    'The band runs from the cheapest campus to the priciest: {t} campuses/hubs observed.',

  'Evolução': 'Trend',
  'Série': 'Series',
  'Mensalidade mediana ao longo do tempo': 'Median monthly tuition over time',
  'Cada ponto é uma coleta. A série começa a existir a partir da segunda rodada — antes disso não há movimento a mostrar.':
    'Each dot is one collection run. The series only exists from the second run onwards — before ' +
    'that there is no movement to show.',
  'Série de mensalidade': 'Tuition series',
  'A coleta de mensalidades ainda não rodou nesta cópia. Rode <code>python scripts/07_fetch_mensalidades.py</code> para preencher este bloco.':
    'The tuition collection has not run in this copy yet. Run ' +
    '<code>python scripts/07_fetch_mensalidades.py</code> to fill this block.',

  /* ------------------------------------------------ ambiente regulatório
   * "Regulatório" vira "Regulatory landscape": em inglês de equity research o termo
   * usual é o ambiente, não a regulação em si. Nome de norma NÃO se traduz — "Decreto
   * nº 12.456/2025" é identificador, e traduzir atrapalharia quem for buscar a fonte. */
  'Alta': 'High', 'Média': 'Medium', 'Baixa': 'Low', 'Relevância': 'Relevance',
  'Definições': 'Definitions',
  'Quem ganhou e quem perdeu terreno': 'Who gained and who lost ground',
  'Ganho e perda de market share — {a} vs {b}': 'Market share gains and losses — {a} vs {b}',
  'bloco:gr-share-hint':
    `Who advanced and who fell back against the previous year. The denominator is the whole
     market for the year, and the ranking deliberately ignores the group filter — share only
     means something against the total. "Independents" is left out because it is a residual
     bucket, not a player.`,
  'bloco:rg-feed-hint':
    `Ordinances, decrees, resolutions and public notices relevant to private higher education,
     newest first. Click <em>Details</em> to open the panel without leaving the page, or go
     straight to the official document.`,

  'Ambiente Regulatório': 'Regulatory Landscape',
  'Regulatório': 'Regulatory',
  'Regulação': 'Regulation',
  'O que está valendo, o que mudou e o que vem pela frente em EaD & Polos, Medicina e Fies — mais o feed das últimas decisões do MEC, com resumo, relevância e link para o documento oficial.':
    'What is in force, what changed and what is coming next in Distance Learning & Hubs, ' +
    'Medicine and Fies — plus a feed of the latest MEC decisions, with a summary, a relevance ' +
    'rating and a link to the official document.',

  'EaD & Polos': 'Distance Learning & Hubs',
  'Medicina': 'Medicine',
  'Fies': 'Fies',
  'Tema': 'Topic', 'Órgão': 'Body', 'Situação': 'Status', 'Conferência': 'Verification',
  'Vigente': 'In force', 'Em transição': 'In transition', 'Em discussão': 'Under discussion',
  'Revogada': 'Revoked',
  'Relevância {r}': '{r} relevance',
  'Regra hoje': 'Rule today', 'O que mudou': 'What changed',
  'Próximo prazo': 'Next deadline',
  'Como era': 'How it was', 'Como funciona hoje': 'How it works today', 'Hoje': 'Today',
  'Buscar': 'Search', 'Limpar': 'Clear',
  'Buscar no ambiente regulatório': 'Search the regulatory landscape',
  'Todo o histórico': 'Full history', 'Últimos 30 dias': 'Last 30 days',
  'Últimos 3 meses': 'Last 3 months', 'Últimos 6 meses': 'Last 6 months',
  'Último ano': 'Last year',
  'O que está acontecendo agora': 'What is happening now',
  'Onde estamos em cada tema': 'Where each topic stands',
  'Onde estamos neste tema': 'Where this topic stands',
  'Últimas decisões do MEC': 'Latest MEC decisions',
  'Feed cronológico': 'Chronological feed',
  '{n} de {t} publicações': '{n} of {t} publications',
  'Publicações': 'Publications',
  'Detalhes': 'Details', 'Fechar': 'Close',
  'Abrir documento': 'Open document', 'Abrir documento oficial': 'Open official document',
  'O que foi publicado': 'What was published', 'Quem é afetado': 'Who is affected',
  'Datas importantes': 'Key dates', 'Publicação': 'Published',
  'Vigência': 'Effective from', 'Inscrições': 'Registration',
  'Inscrições 2026.1': 'Registration 2026.1', 'Aplicação da prova': 'Exam date',
  'a confirmar': 'to confirm',
  'Não conferida no Diário Oficial': 'Not yet checked against the Official Gazette',
  'Compilada a partir de fonte secundária: confira o número e a data no documento oficial antes de citar.':
    'Compiled from a secondary source: check the number and date in the official document ' +
    'before citing it.',
  '{q} das {t} publicações ainda não foram conferidas no Diário Oficial e estão marcadas como "a confirmar". Confira o documento oficial antes de citar qualquer uma delas.':
    '{q} of the {t} publications have not yet been checked against the Official Gazette and are ' +
    'flagged "to confirm". Check the official document before citing any of them.',
  'Base atualizada em {d} · {n} publicações': 'Base updated {d} · {n} publications',
  'Nenhuma publicação para os filtros escolhidos.': 'No publication matches the selected filters.',
  'Sem resumo para este tema.': 'No summary for this topic.',
  'Fontes': 'Sources', 'Fontes oficiais': 'Official sources',
  'Onde isto é apurado': 'Where this comes from',
  'Toda publicação tem link para o documento original. Notícia não entra como fonte primária quando o ato oficial existe.':
    'Every publication links to the original document. News reporting is not used as a primary ' +
    'source when the official act exists.',
  'Decisões regulatórias': 'Regulatory decisions',
  'Documento': 'Document', 'Resumo': 'Summary', 'Fonte oficial': 'Official source',
  'A base regulatória ainda não foi gerada nesta cópia. Rode <code>python scripts/08_build_regulatorio.py</code>.':
    'The regulatory base has not been generated in this copy. Run ' +
    '<code>python scripts/08_build_regulatorio.py</code>.',

  /* nomes próprios e siglas: mesmos nos dois idiomas */
  'Data House': 'Data House', 'PT': 'PT', 'EN': 'EN', 'INEP': 'INEP', 'HHI': 'HHI',
  'WTD': 'WTD', 'MTD': 'MTD', 'YTD': 'YTD', 'IBOV': 'IBOV', 'SMLL': 'SMLL',
  'Education': 'Education', 'Instituições': 'Institutions',
  'Vinicius Figueiredo': 'Vinicius Figueiredo', 'Lucca Marquezini': 'Lucca Marquezini',
  'Felipe Amancio': 'Felipe Amancio',

  'Antes de tudo': 'First things first',
  'De onde vêm os dados e por que eles podem divergir do release da companhia':
    'Where the data comes from and why it can differ from a company’s release',
  'Leia esta parte antes de confrontar qualquer número com o que a empresa divulga.':
    'Read this before checking any number against what a company reports.',
  '{l} concentra(m) {p} da base do grupo, e {q} dessas matrículas são EAD. Isso é registro, não geografia: o Censo lança a matrícula de EAD na IES <strong>sede</strong>, não no polo onde o aluno estuda — a UF da linha é o endereço da mantida, e não onde estão os alunos. Para saber onde eles realmente estão, use o bloco Geografia, que distribui por município de oferta.':
    '{l} hold(s) {p} of the group base, and {q} of those enrollments are distance learning. That ' +
    'is a registration artefact, not geography: the Census books a distance-learning enrollment ' +
    'at the <strong>head-office</strong> institution, not at the hub where the student studies — ' +
    "the state on the row is the entity's registered address, not where the students are. To see " +
    'where they actually are, use the Geography block, which spreads them by city of delivery.',
  'O detalhe que o quadro acima não cabe': 'The detail the panel above cannot hold',
  'Métricas de aluno': 'Student metrics',
  'Modalidade, rede e organização': 'Delivery mode, sector and institution type',
  'Grupos e competição': 'Groups and competition',
  'Curso e geografia': 'Programs and geography',

  /* ----------------------------------------------------- Investor Snapshot */
  'Investor Snapshot': 'Investor Snapshot',
  'Resumo': 'Summary',
  'A página de abertura: o setor na década, de onde vieram os alunos que entraram, quem ganhou e quem perdeu share, e o que cresce em curso e em praça.':
    'The opening page: the sector over the decade, where the incoming students came from, who ' +
    'gained and who lost share, and what is growing by program and by state.',

  'O setor na década': 'The sector over the decade',
  'CAGR {i}–{f}': 'CAGR {i}–{f}',
  'ao ano, em matrículas': 'per year, in enrollments',
  'era {v} em {a}': 'was {v} in {a}',
  'Alunos a mais desde {a}': 'Students added since {a}',
  '{p} em {n} anos': '{p} over {n} years',
  'EAD — variação': 'Distance learning — change',
  'Presencial — variação': 'On-campus — change',
  'alunos desde {a}': 'students since {a}',
  'IES ativas': 'Active institutions',
  'Indicadores do setor': 'Sector indicators',
  'Indicador': 'Indicator',

  'De onde veio o crescimento': 'Where the growth came from',
  'Atribuição': 'Attribution',
  'De onde vieram os alunos — {i} a {f}': 'Where the students came from — {i} to {f}',
  'O total esconde a troca de composição: o EAD privado entregou mais alunos do que o setor inteiro ganhou':
    'The total hides the shift in mix: private distance learning added more students than the ' +
    'whole sector gained',
  'Privada · EAD': 'Private · distance',
  'Privada · presencial': 'Private · on-campus',
  'Pública · EAD': 'Public · distance',
  'Pública · presencial': 'Public · on-campus',
  'Segmento': 'Segment',
  'Variação': 'Change',
  'CAGR (%)': 'CAGR (%)',
  'Crescimento por segmento': 'Growth by segment',
  'Variação absoluta de matrículas por segmento entre {i} e {f}. O setor ganhou <strong>{t}</strong> alunos no período, mas o EAD privado sozinho entregou <strong>{e}</strong> enquanto o presencial privado devolveu <strong>{p}</strong> — quem lê só o total não vê a troca de composição, que é onde está a tese. Denominador: matrículas do Brasil, todas as redes ({d} em {f}).':
    'Absolute change in enrollments by segment between {i} and {f}. The sector gained ' +
    '<strong>{t}</strong> students over the period, but private distance learning alone added ' +
    '<strong>{e}</strong> while private on-campus gave back <strong>{p}</strong> — reading the ' +
    'total alone misses the shift in mix, which is where the thesis is. Denominator: Brazilian ' +
    'enrollments, all sectors ({d} in {f}).',

  'Movimento entre os players': 'Movement among the players',
  'Quem ganhou e quem perdeu share — {p} a {a}': 'Who gained and who lost share — {p} to {a}',
  'Movimento em pontos percentuais contra o ano anterior — não é o ranking de tamanho':
    'Movement in percentage points against the prior year — this is not the size ranking',
  'Grupos econômicos — share e as duas séries de crescimento':
    'Economic groups — share and both growth series',
  'Matrículas e base de alunos lado a lado: quando as duas divergem, o movimento é reclassificação de vínculo, não aluno entrando ou saindo':
    'Enrollments and student base side by side: when the two diverge, the move is a ' +
    'reclassification of enrollment status, not students joining or leaving',
  'YoY matrículas': 'YoY enrollments',
  'YoY base de alunos': 'YoY student base',
  'Movimento de market share': 'Market share movement',
  'QT_MAT e base de alunos divergem mais de {v} p.p. neste ano':
    'QT_MAT and the student base diverge by more than {v} pp in this year',
  'Denominador: matrículas do Brasil em {a} — {t}. Consolidação por grupo econômico em perímetro <strong>pro-forma</strong>: uma IES adquirida em 2022 conta no grupo comprador desde {i}, o que permite ler share sem degrau de M&amp;A — mas não é o que cada empresa reportava à época. <em>Base de alunos</em> = matrículas + trancados, que é a definição que as companhias divulgam; as duas colunas aparecem juntas de propósito. Fora do ranking, {p} do mercado ({m} matrículas) está em instituições não mapeadas em grupo — bucket residual, não um player. Os 15 maiores na tela, todos os {q} grupos no Excel — ordene por qualquer coluna.':
    'Denominator: Brazilian enrollments in {a} — {t}. Consolidated by economic group on a ' +
    '<strong>pro-forma</strong> perimeter: an institution acquired in 2022 counts in the buying ' +
    'group since {i}, which lets share be read without M&amp;A steps — but it is not what each ' +
    'company reported at the time. <em>Student base</em> = enrollments + suspended enrollments, ' +
    'which is the definition companies disclose; the two columns appear together on purpose. ' +
    'Outside the ranking, {p} of the market ({m} enrollments) sits in institutions not mapped to ' +
    'a group — a residual bucket, not a player. The 15 largest on screen, all {q} groups in '
    + 'the Excel file — sort by any column.',
  '<strong>{g}</strong>: matrículas e base de alunos divergem mais de {v} p.p. em {a}. O movimento aí é <strong>reclassificação de vínculo</strong> — trancado que virou ativo, ou o contrário —, não aluno entrando ou saindo. Leia as duas colunas juntas.':
    '<strong>{g}</strong>: enrollments and student base diverge by more than {v} pp in {a}. The ' +
    'move there is a <strong>reclassification of enrollment status</strong> — suspended turning ' +
    'active, or the reverse — not students joining or leaving. Read both columns together.',

  'O que cresce': 'What is growing',
  'Cursos que mais crescem — {i} a {f}': 'Fastest-growing programs — {i} to {f}',
  'Rótulos CINE acima do piso de base, ordenados por CAGR':
    'CINE labels above the size floor, ranked by CAGR',
  'Crescimento por curso': 'Growth by program',
  'Rótulos CINE com pelo menos <strong>{piso}</strong> matrículas em {a} — {q} cursos, {cob} do total do país. O piso é o que impede o topo do ranking de virar curso pequeno que dobrou de tamanho: matematicamente correto e analiticamente inútil. 15 na tela, todos os {q} no Excel. Ordene por qualquer coluna.':
    'CINE labels with at least <strong>{piso}</strong> enrollments in {a} — {q} programs, {cob} ' +
    'of the national total. The floor is what stops the top of the ranking from becoming a tiny ' +
    'program that doubled: mathematically correct and analytically useless. 15 on screen, all ' +
    '{q} in the Excel file. Sort by any column.',

  'Onde o setor cresce — {i} a {f}': 'Where the sector is growing — {i} to {f}',
  'Praça': 'Location',
  'UF de oferta — onde o aluno está, não onde fica a sede da IES':
    'State of delivery — where the student is, not where the institution is registered',
  'Crescimento por UF': 'Growth by state',
  'UF de <strong>oferta</strong> — onde o aluno está —, do cubo por município (dimensões 1 e 2 do Censo). <strong>Não confunda com a UF da sede da IES</strong>, que é o que os demais blocos usam: no EAD a matrícula é lançada na sede, e por isso a Unopar aparece 100% no Paraná com polo no país inteiro. UFs com pelo menos {piso} matrículas em {a}; 15 na tela, todas no Excel. Denominador: {t} matrículas com município identificado.':
    'State of <strong>delivery</strong> — where the student is — from the city-level cube ' +
    '(Census dimensions 1 and 2). <strong>Do not confuse it with the state where the institution ' +
    'is registered</strong>, which is what the other blocks use: in distance learning the ' +
    'enrollment is booked at the head office, which is why Unopar shows up 100% in Paraná while ' +
    'running hubs across the country. States with at least {piso} enrollments in {a}; 15 on ' +
    'screen, all of them in the Excel file. Denominator: {t} enrollments with an identified city.',
});
