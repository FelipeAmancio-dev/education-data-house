/* Bloco "Key Players" — três camadas, na ordem em que o investidor pergunta:
 *
 *   A) escolha livre de quem entra no confronto (chips) e o comparativo estrutural;
 *   B) a composição da base dos selecionados, por região e por curso;
 *   C) a exposição de cada selecionado à modalidade, em alunos e em %.
 *
 * ⚠️ REESCRITO EM 14/08/2026, a pedido do usuário. Antes a camada B era fixa nas 7
 * companhias abertas e ignorava os chips de propósito, e a camada C mostrava o setor
 * inteiro. Hoje **as três camadas seguem a seleção** — não sobrou nenhuma peça que ignore
 * os chips. O padrão continua sendo as abertas porque `montarChips()` já inicia com elas
 * marcadas, então quem não mexe em nada vê o mesmo conjunto de antes.
 *
 * Saíram na mesma rodada, também a pedido: os 4 KPIs do "retrato do conjunto", os 4 das
 * companhias abertas, os 4 de estrutura competitiva (Top 5 e HHI), a tabela "todos os
 * grupos econômicos" e o quadro "quem ganhou e quem perdeu terreno". Com a tabela foram
 * junto duas abas do Excel: "Todos os grupos econômicos" e "Movimento de market share".
 *
 * Não repetir gráfico continua sendo regra: a evolução de share é a camada A e a
 * composição por curso é a camada B — nenhuma das duas reaparece adiante com outro corte.
 */
import {
  D, carregarAno, porIES, serieIES, totalAno, unidadesPorIES,
  gr, ufIES, nomeCurso, areaCurso, ufMun, regMun, n, deltaHTML,
} from './dados.js';
import { $, esc, tabela, chart, baseChart, fmtEixoMi, registrarCSV, PALETA,
         COR_PRES, COR_EAD } from './ui.js';
import { TX, TXcurso, TXarea, TXregiao } from './i18n.js';

let selecao = null;   // Set de grupos selecionados; null = ainda nao inicializado

const cor = (k, i) => D.gruposOrd[k]?.cor || PALETA[i % PALETA.length];
const nome = k => D.gruposOrd[k]?.nome || k;
const abertas = () => D.gruposLista.filter(g => D.gruposOrd[g]?.tipo === 'listada');

/* Alternando as duas famílias de matiz (laranja e azul), 12 categorias continuam
 * distinguíveis; os cinzas do fim caem no resíduo, que é sempre a última categoria. */
const PALETA_CAT = ['#EC7000', '#003C7D', '#F2A25C', '#4A7FB5', '#A34B00', '#8FB4D9',
                    '#FF9A3D', '#33628F', '#7A3E12', '#B8CFE5', '#C9CDD3', '#9AA5B1'];

function denomTxt(f) {
  const p = [];
  if (f.mod) p.push(f.mod === '1' ? TX('presencial') : TX('EAD'));
  if (f.rede) p.push(f.rede === '1' ? TX('rede pública') : TX('rede privada'));
  if (f.uf) p.push(f.uf);
  return p.length ? TX('matrículas {r}', { r: p.join(' · ') }) : TX('matrículas do Brasil');
}

function montarChips() {
  const listadas = abertas();
  const outros = D.gruposLista.filter(g => g !== 'Independentes' && D.gruposOrd[g]?.tipo !== 'listada');
  if (selecao === null) selecao = new Set(listadas);

  const chip = (k, i) => {
    const info = D.gruposOrd[k] || {};
    return `<button class="chip ${selecao.has(k) ? 'on' : ''}" data-g="${esc(k)}">
      <span class="pt" style="background:${cor(k, i)}"></span>${esc(info.nome || k)}
      ${info.ticker ? `<span class="tk">${esc(info.ticker)}</span>` : ''}</button>`;
  };

  $('#cp-chips').innerHTML =
    `<div style="margin-bottom:14px">
       <div class="eyebrow">${TX('Listadas em bolsa')}</div>
       <div class="chips">${listadas.map(chip).join('')}</div>
     </div>
     <div>
       <div class="eyebrow">${TX('Outros grupos relevantes')}</div>
       <div class="chips">${outros.slice(0, 12).map((k, i) => chip(k, i + listadas.length)).join('')}</div>
     </div>`;

  $('#cp-chips').querySelectorAll('.chip').forEach(b => b.onclick = () => {
    const g = b.dataset.g;
    if (selecao.has(g)) { if (selecao.size > 1) selecao.delete(g); }
    else selecao.add(g);
    grupos(window.__filtros);
  });
}

/* ------------------------------------------------------------------ helpers
 * Distribuição da base de cada grupo por uma chave do detalhe (região ou curso). */
function distribuicao(cubo, setG, chaveDe, filtroLinha) {
  const porG = new Map(), totChave = new Map();
  for (let i = 0; i < cubo.n; i++) {
    const ix = cubo.ies[i];
    if (ix < 0) continue;
    const k = gr(ix);
    if (!setG.has(k)) continue;
    if (!filtroLinha(i, ix)) continue;
    const ch = chaveDe(i);
    if (ch == null) continue;
    let m = porG.get(k);
    if (!m) { m = {}; porG.set(k, m); }
    m[ch] = (m[ch] || 0) + cubo.qt_mat[i];
    totChave.set(ch, (totChave.get(ch) || 0) + cubo.qt_mat[i]);
  }
  return { porG, totChave };
}

/* Legenda que mostra TODOS os nomes, em vez de esconder o resto atras da setinha.
 *
 * ⚠️ `type: 'scroll'` cabe tudo numa linha so e pagina o excedente — o usuario precisava
 * clicar na seta para descobrir QUEM estava sendo comparado, que e justamente a pergunta
 * do bloco. Com `plain` a legenda quebra em varias linhas e mostra todo mundo de uma vez.
 *
 * O preco de quebrar linha e que a legenda passa a ocupar altura variavel, e a legenda do
 * ECharts nao empurra o grid sozinha: sem reservar o espaco, ela deita por cima das
 * barras. Por isso a largura de cada item e estimada aqui (marcador + texto + folga) para
 * contar quantas linhas vao sair e devolver o `topo` que o grid precisa.               */
function legendaTodos(el, nomes) {
  const larg = Math.max(300, el?.clientWidth || 620);
  const larguraItem = t => 10 + 6 + String(t).length * 6.3 + 16;
  let linhas = 1, usado = 0;
  for (const t of nomes) {
    const w = larguraItem(t);
    if (usado + w > larg && usado > 0) { linhas++; usado = w; } else usado += w;
  }
  return {
    legend: { type: 'plain', top: 0, left: 0, width: '100%', itemWidth: 10, itemHeight: 10,
              itemGap: 16, icon: 'roundRect', data: nomes,
              textStyle: { fontSize: 11.5, color: '#4A4A4A' } },
    topo: 10 + linhas * 20,
  };
}

/* Reparte 100,0% entre as categorias de um grupo com o metodo do MAIOR RESTO.
 *
 * ⚠️ Isto existe porque arredondar cada fatia sozinha NAO fecha a conta. Cada categoria
 * caia num `.toFixed(1)` independente, e a barra somava 99,8% na Ser, 100,1% no Cruzeiro
 * — o usuario viu e reclamou, com razao. O dado nunca esteve errado (no cubo as regioes
 * fecham 100,0% da base de cada grupo); errado era so o arredondamento.
 *
 * Trabalha em DECIMOS de ponto percentual, que e a precisao que a tela mostra: distribui
 * o piso de cada fatia e entrega os decimos que sobraram a quem tem o maior resto. O
 * total sai exatamente 1000 decimos = 100,0%.                                          */
function reparte100(valores) {
  const t = valores.reduce((s, v) => s + v, 0);
  if (!t) return valores.map(() => 0);
  const bruto = valores.map(v => 1000 * v / t);
  const piso = bruto.map(Math.floor);
  let sobra = 1000 - piso.reduce((s, v) => s + v, 0);
  // maior resto primeiro; empate desempata pelo maior valor absoluto, para ser estavel
  const ordem = bruto.map((b, i) => [b - piso[i], valores[i], i])
    .sort((a, b) => b[0] - a[0] || b[1] - a[1]);
  for (let j = 0; j < sobra; j++) piso[ordem[j % ordem.length][2]]++;
  return piso.map(d => d / 10);
}

/* Barras 100% empilhadas: x = grupos, empilhamento = categorias. */
function chart100(el, gruposArr, cats, cores, porG, opt = {}) {
  // absolutos por (grupo, categoria) primeiro; o percentual sai do conjunto, nao da fatia
  const absPorG = new Map(gruposArr.map(k => {
    const m = porG.get(k) || {};
    return [k, cats.map(c => c.chaves.reduce((s, ch) => s + (m[ch] || 0), 0))];
  }));
  const pctPorG = new Map(gruposArr.map(k => [k, reparte100(absPorG.get(k))]));
  const valor = (k, c) => {
    const i = cats.indexOf(c);
    return { abs: absPorG.get(k)[i], pct: pctPorG.get(k)[i] };
  };
  const lg = legendaTodos(el, cats.map(c => c.rot));
  chart(el, {
    ...baseChart(),
    legend: lg.legend,
    grid: { left: 8, right: 16, top: lg.topo, bottom: 6, containLabel: true },
    xAxis: { ...baseChart().xAxis, data: gruposArr.map(nome),
             axisLabel: { fontSize: 10.5, color: '#8C8C8C', rotate: 26, interval: 0 } },
    yAxis: { ...baseChart().yAxis, max: 100,
             axisLabel: { fontSize: 11.5, color: '#8C8C8C', formatter: v => v + '%' } },
    series: cats.map((c, i) => ({
      name: c.rot, type: 'bar', stack: 'a', barMaxWidth: 46,
      itemStyle: { color: cores[i % cores.length] },
      data: gruposArr.map(k => valor(k, c).pct),
    })),
    tooltip: { ...baseChart().tooltip, valueFormatter: v => v + '%' },
  });
  // CSV com percentual E volume: quem abre no Excel costuma querer o número absoluto
  if (opt.csv) registrarCSV('grupos', opt.csv,
    [{ k: 'grupo', t: TX('Grupo') }, { k: 'categoria', t: opt.rotuloCat || TX('Categoria') },
     { k: 'alunos', t: TX('Alunos') }, { k: 'pct', t: TX('% da base do grupo') }],
    gruposArr.flatMap(k => cats.map(c => {
      const v = valor(k, c);
      return { grupo: nome(k), categoria: c.rot, alunos: v.abs, pct: v.pct };
    })));
}

/* ============================================================== VIEW ====== */
export async function grupos(f) {
  montarChips();
  const ano = f.ano, prev = ano - 1;
  const sel = D.gruposLista.filter(g => selecao.has(g));   // preserva a ordem do config
  const cores = {};
  sel.forEach((k, i) => { cores[k] = cor(k, i); });

  // a comparacao ignora o filtro de grupo — ele seria contraditorio aqui
  const fc = { ...f, grupo: '' };
  const g = porIES(ano, gr, fc), gp = porIES(prev, gr, fc);
  const u = unidadesPorIES(ano, gr, fc);
  const tot = totalAno(ano, fc), totP = totalAno(prev, fc);
  const serie = serieIES(gr, fc);
  const totalPorAno = D.meta.anos.map(a => totalAno(a, fc));
  const anos = D.meta.anos, anoBase = anos[0], nAnos = anos.length - 1;

  /* ---------------------------------------------------------- A) seleção --- */
  const rows = sel.map(k => {
    const v = g.get(k) || { mat: 0, pres: 0, ead: 0, ing: 0, conc: 0, tranc: 0 };
    const p = gp.get(k);
    const share = tot ? 100 * v.mat / tot : 0;
    const shareP = p && totP ? 100 * p.mat / totP : null;
    const un = u.get(k) || { unidades: 0, municEad: 0, ies: 0 };
    const base0 = serie.get(k)?.[anoBase]?.mat || 0;
    return {
      grupo: nome(k), _raw: k, ticker: D.gruposOrd[k]?.ticker || '',
      mat: v.mat, share, dShare: shareP == null ? null : share - shareP,
      pres: v.pres, ead: v.ead, pctEad: v.mat ? 100 * v.ead / v.mat : 0,
      renov: v.mat ? 100 * v.ing / v.mat : 0,
      tranc: v.mat ? 100 * v.tranc / v.mat : 0,
      ies: un.ies, unidades: un.unidades,
      alunosUnid: un.unidades ? v.pres / un.unidades : null,
      yoy: p && p.mat ? 100 * (v.mat - p.mat) / p.mat : null,
      cagr: base0 > 0 && v.mat > 0 ? (Math.pow(v.mat / base0, 1 / nAnos) - 1) * 100 : null,
    };
  });

  $('#cp-tab-tit').textContent = TX('Comparativo — {a}', { a: ano });
  tabela($('#cp-tab'), [
    { k: 'grupo', t: TX('Grupo'), tipo: 'txt', fmt: (v, r) =>
        `<span style="display:inline-flex;align-items:center;gap:9px">
           <span style="width:9px;height:9px;border-radius:2px;background:${cores[r._raw]};flex:0 0 auto"></span>
           ${esc(v)}${r.ticker ? ` <span class="tag lst">${esc(r.ticker)}</span>` : ''}</span>` },
    { k: 'mat', t: TX('Matrículas'), tipo: 'num' },
    { k: 'share', t: TX('Share'), tipo: 'barra' },
    // ⚠️ o cabecalho diz contra QUE ano, senao "Δ Share" nao tem periodo — o usuario
    // perguntou exatamente isso. E o mesmo ano do YoY ao lado: o anterior.
    { k: 'dShare', t: TX('Δ Share vs {a}', { a: prev }), tipo: 'num',
      fmt: v => v == null ? '—' : deltaHTML(v, ' p.p.') },
    { k: 'yoy', t: TX('YoY vs {a}', { a: prev }), tipo: 'num', fmt: v => deltaHTML(v) },
    { k: 'cagr', t: `CAGR ${anoBase}–${ano}`, tipo: 'num', fmt: v => deltaHTML(v) },
    { k: 'pctEad', t: TX('% EAD'), tipo: 'pct' },
    { k: 'ies', t: 'IES', tipo: 'num' },
    { k: 'unidades', t: TX('Unidades'), tipo: 'num' },
    { k: 'alunosUnid', t: TX('Alunos/unid.'), tipo: 'num', fmt: v => v == null ? '—' : n(v) },
    { k: 'renov', t: TX('Ingr./base'), tipo: 'pct' },
    { k: 'tranc', t: TX('% Tranc.'), tipo: 'pct' },
  ], rows, { ordem: 'mat', csv: { bloco: 'grupos', nome: TX('Comparativo dos selecionados') } });

  $('#cp-tab-nota').innerHTML = TX(
    'Denominador do share: <strong>{d}</strong> em {a} — {t}. <em>Ingr./base</em> = ingressantes ' +
    '÷ matrículas: proxy da velocidade de renovação da carteira — quanto maior, mais o grupo ' +
    'depende de captação nova para sustentar a base. <em>Alunos/unid.</em> usa apenas o presencial, ' +
    'já que unidade é proxy de campus físico. <em>% Tranc.</em> é o que explica boa parte da ' +
    'diferença contra a base divulgada pela companhia.',
    { d: denomTxt(fc), a: ano, t: n(tot) });

  // legenda com todos os nomes: e o bloco em que a pergunta "quem esta sendo comparado?"
  // precisa ser respondida sem clique
  const lgShare = legendaTodos($('#cp-share'), sel.map(nome));
  const lgMat = legendaTodos($('#cp-mat'), sel.map(nome));
  const linhaBase = {
    ...baseChart(),
    xAxis: { ...baseChart().xAxis, data: anos },
  };
  chart($('#cp-share'), {
    ...linhaBase,
    legend: lgShare.legend,
    grid: { left: 8, right: 20, top: lgShare.topo, bottom: 6, containLabel: true },
    yAxis: { ...baseChart().yAxis, axisLabel: { fontSize: 11.5, color: '#8C8C8C', formatter: v => v + '%' } },
    series: sel.map(k => ({
      name: nome(k), type: 'line', smooth: .2, symbol: 'circle', symbolSize: 5,
      lineStyle: { width: 2.4 }, itemStyle: { color: cores[k] },
      data: anos.map((a, j) => {
        const v = serie.get(k)?.[a]?.mat || 0;
        return totalPorAno[j] ? +(100 * v / totalPorAno[j]).toFixed(2) : null;
      }),
    })),
    tooltip: { ...baseChart().tooltip, valueFormatter: v => v == null ? '—' : v + '%' },
  });

  chart($('#cp-mat'), {
    ...linhaBase,
    legend: lgMat.legend,
    grid: { left: 8, right: 20, top: lgMat.topo, bottom: 6, containLabel: true },
    yAxis: { ...baseChart().yAxis, axisLabel: { fontSize: 11.5, color: '#8C8C8C', formatter: fmtEixoMi } },
    series: sel.map(k => ({
      name: nome(k), type: 'line', smooth: .2, symbol: 'circle', symbolSize: 5,
      lineStyle: { width: 2.4 }, itemStyle: { color: cores[k] },
      data: anos.map(a => serie.get(k)?.[a]?.mat ?? null),
    })),
    tooltip: { ...baseChart().tooltip, valueFormatter: v => v == null ? '—' : n(v) },
  });
  registrarCSV('grupos', TX('Série histórica por grupo'),
    [{ k: 'ano', t: TX('Ano') }, { k: 'grupo', t: TX('Grupo') }, { k: 'mat', t: TX('Matrículas') },
     { k: 'pres', t: TX('Presencial') }, { k: 'ead', t: TX('EAD') },
     { k: 'tranc', t: TX('Trancados') }, { k: 'share', t: TX('Share') }],
    sel.flatMap(k => anos.map((a, j) => {
      const s = serie.get(k)?.[a] || {};
      return { ano: a, grupo: nome(k), mat: s.mat || 0, pres: s.pres || 0, ead: s.ead || 0,
               tranc: s.tranc || 0,
               share: totalPorAno[j] ? +(100 * (s.mat || 0) / totalPorAno[j]).toFixed(3) : null };
    })));

  chart($('#cp-disp'), {
    ...baseChart(),
    legend: { show: false },
    // ⚠️ `containLabel` reserva espaco para os RÓTULOS do eixo, nao para o NOME dele —
    // com bottom:8 o nome do eixo X caia fora do canvas e simplesmente nao aparecia.
    // As folgas abaixo sao o nameGap de cada eixo mais a altura do proprio texto.
    grid: { left: 34, right: 90, top: 24, bottom: 44, containLabel: true },
    // Eixos com nome por extenso: "Share" e "CAGR" sozinhos nao dizem share de que nem
    // CAGR de que, e este e o grafico do bloco que mais depende de o leitor saber o que
    // esta lendo — cada eixo carrega a metrica, o denominador e o periodo.
    xAxis: {
      type: 'value',
      name: TX('Tamanho hoje → share de {d} em {a}', { d: denomTxt(fc), a: ano }),
      nameLocation: 'middle', nameGap: 32,
      nameTextStyle: { fontSize: 11.5, color: '#4A4A4A', fontWeight: 600 },
      splitLine: { lineStyle: { color: '#F2F3F5' } }, axisLine: { show: false }, axisTick: { show: false },
      axisLabel: { fontSize: 11.5, color: '#8C8C8C', formatter: v => v + '%' },
    },
    yAxis: {
      type: 'value',
      name: TX('Ritmo → crescimento anual médio {b}–{a}', { b: anoBase, a: ano }),
      nameLocation: 'middle', nameGap: 46,
      nameTextStyle: { fontSize: 11.5, color: '#4A4A4A', fontWeight: 600 },
      splitLine: { lineStyle: { color: '#F2F3F5' } }, axisLine: { show: false }, axisTick: { show: false },
      axisLabel: { fontSize: 11.5, color: '#8C8C8C', formatter: v => v + '%' },
    },
    series: [{
      type: 'scatter',
      symbolSize: d => Math.max(16, Math.min(56, Math.sqrt(d[2]) / 22)),
      data: rows.filter(r => r.cagr != null).map(r =>
        [+r.share.toFixed(2), +r.cagr.toFixed(1), r.mat, r.grupo, cores[r._raw]]),
      itemStyle: { color: p => p.data[4], opacity: .85 },
      label: { show: true, position: 'right', distance: 8, fontSize: 11.5, color: '#4A4A4A',
               fontWeight: 600, formatter: p => p.data[3] },
      markLine: {
        silent: true, symbol: 'none', lineStyle: { color: '#D2D4D8', type: 'dashed' },
        label: { formatter: TX('crescimento zero'), fontSize: 10, color: '#8C8C8C',
                 position: 'insideEndTop' },
        data: [{ yAxis: 0 }],
      },
    }],
    tooltip: {
      ...baseChart().tooltip, trigger: 'item',
      formatter: p => `<strong>${p.data[3]}</strong><br>${TX('Share')}: ${p.data[0]}%<br>` +
                      `CAGR: ${p.data[1]}%<br>${n(p.data[2])} ${TX('matrículas')}`,
    },
  });

  /* -------------------------------------------- B) as companhias abertas --- */
  const det = await carregarAno(ano);
  $('#cp-parcial').innerHTML = det.parcial
    ? `<div class="aviso">${TX('A distribuição por região e por curso exige o detalhe por IES de ' +
       '{a}, não incluído nesta versão de arquivo único — só o ano mais recente vem embutido. ' +
       'Rode <code>python run_dashboard.py</code> para a série completa.', { a: ano })}</div>` : '';

  // ⚠️ MUDOU: esta camada era fixa nas 7 companhias abertas e ignorava os chips de
  // proposito. O usuario pediu que siga a selecao — as abertas continuam sendo o padrao
  // porque `montarChips()` ja inicia com elas marcadas, entao quem nao mexe em nada ve
  // exatamente o que via antes.
  const ab = sel;
  const setAb = new Set(ab);
  $('#ab-secao-tit').textContent = TX('Composição da base — {q} grupos selecionados',
    { q: ab.length });
  const regioes = ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul'];
  const corReg = ['#F2A25C', '#EC7000', '#A34B00', '#003C7D', '#8FB4D9'];
  const dReg = distribuicao(det.iesMun, setAb, i => regMun(det.iesMun.mun[i]),
    (i) => (!f.mod || det.iesMun.mod[i] === +f.mod) &&
           (!f.uf || ufMun(det.iesMun.mun[i]) === f.uf) && (det.iesMun.mun[i] >= 0));
  chart100($('#ab-geo'), ab, regioes.map(r => ({ rot: TXregiao(r), chaves: [r] })), corReg, dReg.porG,
           { csv: TX('Distribuição regional dos selecionados'), rotuloCat: TX('Região') });

  /* curso: por rotulo CINE (os 10 maiores + "outros") ou por area do conhecimento.
   * A area e exaustiva em 11 categorias, o que a torna comparavel do mesmo jeito que a
   * regiao; o rotulo e mais informativo mas deixa metade da base em "outros".        */
  const filtroCine = (i, ix) => (!f.mod || det.iesCine.mod[i] === +f.mod) &&
                                (!f.uf || ufIES(ix) === f.uf) && (det.iesCine.cur[i] >= 0);
  const modoBtns = $('#ab-curso-modo');
  const modo = modoBtns.dataset.m || 'curso';
  modoBtns.querySelectorAll('.chip').forEach(b => {
    b.classList.toggle('on', b.dataset.m === modo);
    b.onclick = () => { modoBtns.dataset.m = b.dataset.m; grupos(window.__filtros); };
  });

  if (modo === 'area') {
    const dArea = distribuicao(det.iesCine, setAb, i => areaCurso(det.iesCine.cur[i]), filtroCine);
    const areas = [...dArea.totChave.entries()].sort((a, b) => b[1] - a[1]).map(x => x[0]);
    chart100($('#ab-curso'), ab, areas.map(a => ({ rot: TXarea(a), chaves: [a] })), PALETA_CAT,
             dArea.porG, { topo: 78, csv: TX('Distribuição por área dos selecionados'),
                           rotuloCat: TX('Área') });
    $('#ab-curso-nota').textContent = TX(
      'Percentual da base de cada grupo por área geral CINE/UNESCO em {a} — {q} categorias ' +
      'que cobrem 100% da base, no mesmo formato da distribuição regional ao lado. Mede ' +
      'concentração de portfólio, não tamanho absoluto.', { a: ano, q: areas.length });
  } else {
    const dCur = distribuicao(det.iesCine, setAb, i => det.iesCine.cur[i], filtroCine);
    /* Não bastam os 10 maiores do conjunto: os dois maiores cursos de CADA companhia
     * entram sempre. Sem isso a Medicina — que é o maior curso da Afya e responde por
     * mais de um quarto da base dela — sumia dentro de "Outros cursos", porque no
     * agregado das sete ela não alcança o top 10. */
    const garantidos = new Set();
    ab.forEach(k => {
      const m = dCur.porG.get(k) || {};
      Object.entries(m).sort((a, b) => b[1] - a[1]).slice(0, 2)
        .forEach(([c]) => garantidos.add(+c));
    });
    const porTamanho = [...dCur.totChave.entries()].sort((a, b) => b[1] - a[1]).map(x => x[0]);
    const topCurAb = [...new Set([...porTamanho.filter(c => garantidos.has(c)),
                                  ...porTamanho])].slice(0, 12);
    const restoAb = porTamanho.filter(c => !topCurAb.includes(c));
    const catsCur = [...topCurAb.map(c => ({ rot: TXcurso(nomeCurso(c)), chaves: [c] })),
                     { rot: TXcurso('Outros cursos'), chaves: restoAb }];
    chart100($('#ab-curso'), ab, catsCur, PALETA_CAT, dCur.porG,
             { topo: 78, csv: TX('Distribuição por curso dos selecionados'), rotuloCat: TX('Curso') });
    $('#ab-curso-nota').textContent = TX(
      'Percentual da base de cada grupo em cada curso, no mesmo formato da distribuição ' +
      'regional. Entram os maiores rótulos CINE do conjunto selecionado em {a} e, sempre, os ' +
      'dois maiores de cada grupo — é o que mantém visível um curso concentrado em um ' +
      'único player, como Medicina na Afya. O restante do portfólio vai para "Outros cursos" ' +
      '({q} rótulos). Mede concentração de portfólio, não tamanho absoluto — para o volume por ' +
      'curso, veja o bloco de Cursos.', { a: ano, q: n(restoAb.length) });
  }

  /* --------------------------------------- C) exposicao a modalidade ------
   * O que sobrou da antiga camada C. Sairam, a pedido do usuario: os 4 KPIs de estrutura
   * competitiva (Top 5, HHI), a tabela "todos os grupos economicos" e o quadro de ganho e
   * perda de share. Com isso o bloco inteiro passou a responder aos chips — nao ha mais
   * nenhuma peca aqui que ignore a selecao.
   *
   * ⚠️ Dois graficos, de proposito. Em alunos, a Cogna e a Vitru achatam todo mundo e a
   * unica leitura possivel e "quem e grande". Em %, o grande e o pequeno ficam do mesmo
   * tamanho e o que aparece e a ESTRATEGIA de modalidade. Sao perguntas diferentes, e
   * empilhar as duas num grafico so obrigaria a escolher uma delas.                     */
  const mixRows = sel.map(k => {
    const v = g.get(k) || { pres: 0, ead: 0, mat: 0 };
    return { grupo: nome(k), _raw: k, pres: v.pres, ead: v.ead, mat: v.mat };
  }).sort((a, b) => b.mat - a.mat);

  const eixoX = {
    ...baseChart().xAxis, data: mixRows.map(r => r.grupo),
    axisLabel: { fontSize: 10.5, color: '#8C8C8C', rotate: 32, interval: 0 },
  };
  const serieMix = (chave, fmt) => [
    { name: TX('Presencial'), type: 'bar', stack: 'a', itemStyle: { color: COR_PRES },
      barMaxWidth: 32, data: mixRows.map(chave.pres) },
    { name: TX('EAD'), type: 'bar', stack: 'a', itemStyle: { color: COR_EAD },
      barMaxWidth: 32, data: mixRows.map(chave.ead) },
  ];

  chart($('#gr-mix'), {
    ...baseChart(),
    legend: { ...baseChart().legend, data: [TX('Presencial'), TX('EAD')] },
    xAxis: eixoX,
    yAxis: { ...baseChart().yAxis, axisLabel: { fontSize: 11.5, color: '#8C8C8C', formatter: fmtEixoMi } },
    series: serieMix({ pres: r => r.pres, ead: r => r.ead }),
    tooltip: { ...baseChart().tooltip, valueFormatter: v => n(v) },
  });

  // mesmo reparte100 das outras barras 100%: presencial + EAD fecham exatamente 100,0%
  const mixPct = mixRows.map(r => reparte100([r.pres, r.ead]));
  chart($('#gr-mix-pct'), {
    ...baseChart(),
    legend: { ...baseChart().legend, data: [TX('Presencial'), TX('EAD')] },
    xAxis: eixoX,
    yAxis: { ...baseChart().yAxis, max: 100,
             axisLabel: { fontSize: 11.5, color: '#8C8C8C', formatter: v => v + '%' } },
    series: [
      { name: TX('Presencial'), type: 'bar', stack: 'a', itemStyle: { color: COR_PRES },
        barMaxWidth: 32, data: mixPct.map(x => x[0]) },
      { name: TX('EAD'), type: 'bar', stack: 'a', itemStyle: { color: COR_EAD },
        barMaxWidth: 32, data: mixPct.map(x => x[1]) },
    ],
    tooltip: { ...baseChart().tooltip, valueFormatter: v => v + '%' },
  });

  registrarCSV('grupos', TX('Mix de modalidade por grupo'),
    [{ k: 'grupo', t: TX('Grupo') }, { k: 'pres', t: TX('Presencial') },
     { k: 'ead', t: TX('EAD') }, { k: 'mat', t: TX('Total') },
     { k: 'pctPres', t: TX('% Presencial') }, { k: 'pctEad', t: TX('% EAD') }],
    mixRows.map((r, i) => ({ grupo: r.grupo, pres: r.pres, ead: r.ead, mat: r.mat,
                             pctPres: mixPct[i][0], pctEad: mixPct[i][1] })));
}
