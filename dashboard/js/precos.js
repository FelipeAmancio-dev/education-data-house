/* Price Action do setor.
 *
 * Fonte: `data/precos.json`, gerado por `scripts/06_fetch_precos.py` (Yahoo Finance,
 * fechamento ajustado). E um SNAPSHOT — a tela carimba a hora da coleta e, quando servida
 * pelo `run_dashboard.py`, oferece um botao que refaz a coleta pelo servidor local.
 *
 * Duas decisoes que mudam a leitura:
 *   - tudo e rebaseado em 100 no inicio do periodo, porque a pergunta e retorno relativo;
 *   - o basket de Education pondera por BASE DE ALUNOS do Censo, nao por peso igual: e o
 *     que liga a carteira ao tamanho real da operacao. Peso igual fica como alternativa.
 */
import { D, carregarPrecos, porIES, gr, pct, n } from './dados.js';
import { $, $$, esc, kpi, tabela, chart, baseChart, registrarCSV, PALETA } from './ui.js';
import { TX, idioma, locale } from './i18n.js';

let selPapeis = null;           // Set de tickers selecionados
let periodo = 'ytd';
let ate = '';                   // data final; vazio = até o último pregão coletado
let peso = 'mcap';
let timerAuto = null;
let timerFrescor = null;

const COR_POS = '#1B7A4B', COR_NEG = '#C4322B';
const CORES_IDX = { IBOV: '#4A4A4A', SMAL11: '#8C8C8C' };

const nomeCia = g => D.gruposOrd[g]?.nome || g;
const corTicker = (p, i) => (p.grupo && D.gruposOrd[p.grupo]?.cor) || PALETA[i % PALETA.length];

/* --------------------------------------------------------------------- datas */
const iso = d => d.toISOString().slice(0, 10);
/* 2026-01-02 vira 02/01/2026 em pt e Jan 2, 2026 em en. */
const dataLegivel = s => new Date(s + 'T12:00:00').toLocaleDateString(
  idioma() === 'en' ? 'en-US' : 'pt-BR',
  idioma() === 'en' ? { year: 'numeric', month: 'short', day: 'numeric' } : undefined);

/* Índice do último pregão ANTERIOR a `limite` (base das janelas WTD/MTD/YTD) ou o
 * último pregão até `limite` inclusive (janelas "desde a data X").              */
/* Preço com o símbolo da moeda certa.
 * ⚠️ Não dá para usar o `brl()` de dados.js aqui: com "moeda local" selecionada a Afya
 * fica em USD, e carimbar R$ nela seria erro de leitura, não de formatação. */
function paPreco(v, moedaSel, papel) {
  if (v == null) return '—';
  const usd = moedaSel !== 'brl' && papel?.moeda === 'USD';
  const loc = idioma() === 'en' ? 'en-US' : 'pt-BR';
  return (usd ? 'US$ ' : 'R$ ') +
    v.toLocaleString(loc, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function idxAte(datas, limite, inclusive) {
  let r = -1;
  for (let i = 0; i < datas.length; i++) {
    if (inclusive ? datas[i] <= limite : datas[i] < limite) r = i; else break;
  }
  return r;
}

/* Índice do último pregão até a data FINAL da janela.
 *
 * `ate` vazio significa "até o fim da série", que é o comportamento de sempre — por isso
 * o padrão devolve o último índice e nada muda para quem não mexer no campo.
 *
 * ⚠️ Isto vale só para o PERÍODO ESCOLHIDO. As colunas fixas da tabela (WTD, MTD, YTD,
 * 12 meses) continuam ancoradas no último fechamento: "WTD até uma data do ano passado"
 * não seria WTD de nada. A nota da tabela diz isso. */
function idxFim(datas, fim) {
  if (!fim) return datas.length - 1;
  let r = -1;
  for (let i = 0; i < datas.length; i++) {
    if (datas[i] <= fim) r = i; else break;
  }
  return r;
}

function inicioJanela(P, tipo) {
  const ult = ultimaData(P);
  const d = new Date(ult + 'T12:00:00');
  if (tipo === 'wtd') {
    const dow = d.getDay() || 7;                     // domingo = 7
    const seg = new Date(d); seg.setDate(d.getDate() - (dow - 1));
    return { limite: iso(seg), inclusive: false };
  }
  if (tipo === 'mtd') return { limite: `${ult.slice(0, 7)}-01`, inclusive: false };
  if (tipo === 'ytd') return { limite: `${ult.slice(0, 4)}-01-01`, inclusive: false };
  if (tipo === '12m') {
    const a = new Date(d); a.setFullYear(d.getFullYear() - 1);
    return { limite: iso(a), inclusive: true };
  }
  if (tipo === 'max') return { limite: '0000-01-01', inclusive: true };
  return { limite: tipo, inclusive: true };          // data escolhida no calendário
}

function ultimaData(P) {
  let u = '';
  for (const k of Object.keys(P.series)) {
    const d = P.series[k].d;
    if (d.length && d[d.length - 1] > u) u = d[d.length - 1];
  }
  return u;
}

/* Calendário de pregão = o do IBOV. Dia em que o índice não negociou (feriado que só
 * vale para um dos ativos, ou falha da fonte) sai de todas as séries: senão aparece um
 * degrau que é buraco de dado, não movimento de preço. */
function diasValidos(P) {
  if (P._dias) return P._dias;
  P._dias = new Set(P.series.IBOV ? P.series.IBOV.d : []);
  return P._dias;
}

/* ------------------------------------------------------------------- séries
 * Devolve {datas, valores} já convertidos para a moeda escolhida. A Afya negocia em
 * USD: comparar com IBOV sem converter mistura retorno de ativo com retorno de câmbio. */
function serie(P, tk, moeda) {
  const s0 = P.series[tk];
  if (!s0) return null;
  const dias = diasValidos(P);
  const s = dias.size && tk !== 'USDBRL'
    ? s0.d.reduce((a, d, i) => (dias.has(d) && (a.d.push(d), a.c.push(s0.c[i])), a),
                  { d: [], c: [], moeda: s0.moeda })
    : s0;
  if (moeda !== 'brl' || s.moeda !== 'USD' || !P.series.USDBRL) return { d: s.d, c: s.c };
  const fx = new Map(P.series.USDBRL.d.map((d, i) => [d, P.series.USDBRL.c[i]]));
  let ult = null;
  const c = s.c.map((v, i) => {
    const t = fx.get(s.d[i]);
    if (t) ult = t;                                   // feriado no câmbio: carrega o último
    return ult ? v * ult : null;
  });
  return { d: s.d, c };
}

/* Retorno % de um papel na janela. Devolve null quando não há preço-base — é o caso
 * da VTRU3 antes de junho/2024, quando o papel ainda não era negociado na B3.      */
function retorno(P, tk, janela, moeda, fimJanela) {
  const s = serie(P, tk, moeda);
  if (!s || !s.c.length) return null;
  const { limite, inclusive } = inicioJanela(P, janela);
  const i = idxAte(s.d, limite, inclusive);
  const j = idxFim(s.d, fimJanela);
  if (j < 0 || j <= Math.max(0, i)) return null;   // janela vazia ou invertida
  const base = i >= 0 ? s.c[i] : s.c[0];
  const fim = s.c[j];
  if (!base || !fim) return null;
  return 100 * (fim / base - 1);
}

/* Série rebaseada em 100 dentro da janela. */
function rebase(P, tk, janela, moeda, fimJanela) {
  const s = serie(P, tk, moeda);
  if (!s) return null;
  const { limite, inclusive } = inicioJanela(P, janela);
  const i0 = Math.max(0, idxAte(s.d, limite, inclusive));
  const i1 = idxFim(s.d, fimJanela);
  if (i1 < i0) return null;
  const base = s.c[i0];
  if (!base) return null;
  return { x: s.d.slice(i0, i1 + 1),
           y: s.c.slice(i0, i1 + 1).map(v => v == null ? null : +(100 * v / base).toFixed(2)) };
}

/* ============================================================== VIEW ====== */
export async function precos() {
  const P = await carregarPrecos();
  const alvo = $('#pa-aviso');
  if (!P || !P.series || !Object.keys(P.series).length) {
    alvo.innerHTML = `<div class="aviso">${TX(
      'Os preços ainda não foram coletados. Rode <code>python scripts/06_fetch_precos.py</code> ' +
      'e recarregue esta página.')}</div>`;
    return;
  }

  const acoes = P.papeis.filter(p => p.tipo === 'acao');
  const indices = P.papeis.filter(p => p.tipo === 'indice').map(p => p.ticker);
  if (selPapeis === null) selPapeis = new Set(acoes.map(p => p.ticker));

  const moeda = $('#pa-moeda').value || 'brl';
  const ult = ultimaData(P);

  // ---------------------------------------------------------------- controles
  $$('#pa-periodo .chip').forEach(b => {
    b.classList.toggle('on', b.dataset.p === periodo);
    // trocar de janela pronta zera as duas datas: manter um "até" de outro recorte
    // deixaria o rótulo dizendo YTD sobre um período que não é o ano corrente
    b.onclick = () => {
      periodo = b.dataset.p;
      ate = ''; $('#pa-desde').value = ''; $('#pa-ate').value = '';
      precos();
    };
  });
  $('#pa-desde').onchange = () => {
    const v = $('#pa-desde').value;
    if (v) { periodo = v; precos(); }
  };
  $('#pa-ate').onchange = () => { ate = $('#pa-ate').value || ''; precos(); };
  $('#pa-desde').max = ate || ult;
  $('#pa-ate').max = ult;
  // o "até" nunca pode ser anterior ao início escolhido
  $('#pa-ate').min = /^\d{4}-/.test(periodo) ? periodo : '';
  $('#pa-ate').value = ate;
  $('#pa-moeda').onchange = () => precos();
  $$('#pa-peso .chip').forEach(b => {
    b.classList.toggle('on', b.dataset.w === peso);
    b.onclick = () => { peso = b.dataset.w; precos(); };
  });

  const rotuloPeriodo = {
    wtd: TX('Na semana (WTD)'), mtd: TX('No mês (MTD)'),
    ytd: TX('No ano (YTD)'), '12m': TX('12 meses'), max: TX('Máximo disponível'),
  }[periodo] || TX('Desde {d}', { d: dataLegivel(periodo) });
  const rotuloJanela = ate
    ? TX('{p} até {d}', { p: rotuloPeriodo, d: dataLegivel(ate) })
    : rotuloPeriodo;

  /* O carimbo mostra a hora NO FUSO DE QUEM ESTÁ OLHANDO, derivada do instante UTC —
   * antes exibia a string crua do arquivo, que vinha em UTC do robô e fazia o usuário em
   * Brasília ler "17:02" às 14h. */
  const quando = instanteColeta(P);
  $('#pa-carimbo').textContent = TX('Preços de {q} · fonte {f}', {
    q: quando ? quando.toLocaleString(locale(), { dateStyle: 'short', timeStyle: 'short' })
              : P.atualizado_em,
    f: P.fonte });
  pintaFrescor($('#pa-frescor'));
  ligaFrescor();
  const horas = quando ? (Date.now() - quando.getTime()) / 36e5 : 0;
  alvo.innerHTML = horas > 24
    ? `<div class="aviso">${TX('Este snapshot de preços tem {h}h. Rode <code>python ' +
        'scripts/06_fetch_precos.py</code> para atualizar.', { h: Math.round(horas) })}</div>` : '';
  // chips de seleção
  $('#pa-chips').innerHTML = `<div class="chips">${acoes.map((p, i) => `
    <button class="chip ${selPapeis.has(p.ticker) ? 'on' : ''}" data-t="${esc(p.ticker)}">
      <span class="pt" style="background:${corTicker(p, i)}"></span>${esc(p.grupo ? nomeCia(p.grupo) : p.ticker)}
      <span class="tk">${esc(p.ticker)}</span></button>`).join('')}</div>`;
  $('#pa-chips').querySelectorAll('.chip').forEach(b => b.onclick = () => {
    const t = b.dataset.t;
    if (selPapeis.has(t)) { if (selPapeis.size > 1) selPapeis.delete(t); } else selPapeis.add(t);
    precos();
  });

  const sel = acoes.filter(p => selPapeis.has(p.ticker));
  const cores = {};
  acoes.forEach((p, i) => { cores[p.ticker] = corTicker(p, i); });

  // ------------------------------------------------------------------ KPIs
  const rets = sel.map(p => ({ ...p, r: retorno(P, p.ticker, periodo, moeda, ate) }))
                  .filter(x => x.r != null).sort((a, b) => b.r - a.r);
  const bsk = basket(P, sel, periodo, peso, ate);
  const rIbov = retorno(P, 'IBOV', periodo, moeda, ate);
  const rSmll = retorno(P, 'SMAL11', periodo, moeda, ate);
  const delta = (a, b) => (a == null || b == null) ? null : a - b;

  $('#pa-kpis').innerHTML = [
    kpi({ rot: TX('Basket Education'), val: sinal(bsk.retorno), sub: rotuloJanela }),
    kpi({ rot: TX('vs IBOV'), val: sinal(delta(bsk.retorno, rIbov), ' p.p.'),
          sub: TX('IBOV {v} no período', { v: sinal(rIbov) }) }),
    kpi({ rot: TX('vs SMLL'), val: sinal(delta(bsk.retorno, rSmll), ' p.p.'),
          sub: TX('SMLL {v} no período', { v: sinal(rSmll) }) }),
    kpi({ rot: TX('Melhor e pior'), val: rets.length ? esc(rets[0].ticker) : '—',
          sub: rets.length ? `${sinal(rets[0].r)} · ${TX('pior')}: ${esc(rets[rets.length - 1].ticker)} ` +
               `${sinal(rets[rets.length - 1].r)}` : '' }),
  ].join('');

  // -------------------------------------------------------- linha rebaseada
  const series = sel.map(p => ({ p, s: rebase(P, p.ticker, periodo, moeda, ate) }))
    .filter(x => x.s);
  const xs = [...new Set(series.flatMap(x => x.s.x))].sort();

  $('#pa-linha-tit').textContent = TX('Retorno acumulado — {p}', { p: rotuloJanela });
  chart($('#pa-linha'), {
    ...baseChart(),
    legend: { ...baseChart().legend, type: 'scroll', data: series.map(x => x.p.ticker) },
    grid: { left: 8, right: 20, top: 34, bottom: 6, containLabel: true },
    xAxis: { ...baseChart().xAxis, data: xs,
             axisLabel: { fontSize: 11, color: '#8C8C8C', hideOverlap: true } },
    yAxis: { ...baseChart().yAxis, scale: true,
             axisLabel: { fontSize: 11.5, color: '#8C8C8C' },
             splitLine: { lineStyle: { color: '#F2F3F5' } } },
    series: series.map(({ p, s }) => {
      const m = new Map(s.x.map((d, i) => [d, s.y[i]]));
      return {
        name: p.ticker, type: 'line', smooth: false, symbol: 'none', connectNulls: true,
        lineStyle: { width: 2 }, itemStyle: { color: cores[p.ticker] },
        data: xs.map(d => m.has(d) ? m.get(d) : null),
        markLine: p.ticker === series[0].p.ticker
          ? { silent: true, symbol: 'none', lineStyle: { color: '#D2D4D8', type: 'dashed' },
              label: { show: false }, data: [{ yAxis: 100 }] } : undefined,
      };
    }),
    tooltip: { ...baseChart().tooltip,
      valueFormatter: v => v == null ? '—' : `${v} (${sinal(v - 100)})` },
  });
  $('#pa-linha-nota').textContent = TX(
    'Base 100 no primeiro pregão do período. Papel sem preço no início da janela entra ' +
    'quando passa a ser negociado — a VTRU3 só tem série a partir de 11/06/2024, quando a ' +
    'Vitru migrou a listagem da Nasdaq para a B3. Moeda: {m}.',
    { m: moeda === 'brl' ? TX('tudo convertido para BRL') : TX('cada papel na moeda local') });

  // ------------------------------------------------------------ barras
  chart($('#pa-barras'), {
    ...baseChart(),
    legend: { show: false },
    grid: { left: 8, right: 52, top: 10, bottom: 6, containLabel: true },
    xAxis: { type: 'value', splitLine: { lineStyle: { color: '#F2F3F5' } }, axisLine: { show: false },
             axisTick: { show: false }, axisLabel: { fontSize: 11.5, color: '#8C8C8C', formatter: v => v + '%' } },
    yAxis: { type: 'category', data: rets.map(x => x.ticker).reverse(), axisTick: { show: false },
             axisLine: { show: false }, axisLabel: { fontSize: 11.5, color: '#4A4A4A' } },
    series: [{
      type: 'bar', barMaxWidth: 22,
      data: rets.map(x => ({ value: +x.r.toFixed(1),
                             itemStyle: { color: x.r >= 0 ? COR_POS : COR_NEG } })).reverse(),
      label: { show: true, position: 'right', fontSize: 11, color: '#4A4A4A', fontWeight: 600,
               formatter: p => sinal(p.value) },
    }],
    tooltip: { ...baseChart().tooltip, trigger: 'item', valueFormatter: v => sinal(v) },
  });
  $('#pa-barras-tit').textContent = TX('Retorno por papel — {p}', { p: rotuloJanela });

  // ------------------------------------------------------------ basket
  const linhasIdx = [{ nome: TX('Basket Education'), cor: '#EC7000', larg: 2.6, s: bsk.serie }];
  for (const ix of indices) {
    const s = rebase(P, ix, periodo, moeda, ate);
    if (s) linhasIdx.push({ nome: ix === 'SMAL11' ? 'SMLL (SMAL11)' : ix,
                            cor: CORES_IDX[ix] || '#8C8C8C', larg: 1.8, s });
  }
  const xsB = [...new Set(linhasIdx.flatMap(l => l.s ? l.s.x : []))].sort();
  chart($('#pa-basket'), {
    ...baseChart(),
    legend: { ...baseChart().legend, data: linhasIdx.map(l => l.nome) },
    grid: { left: 8, right: 20, top: 34, bottom: 6, containLabel: true },
    xAxis: { ...baseChart().xAxis, data: xsB,
             axisLabel: { fontSize: 11, color: '#8C8C8C', hideOverlap: true } },
    yAxis: { ...baseChart().yAxis, scale: true, axisLabel: { fontSize: 11.5, color: '#8C8C8C' } },
    series: linhasIdx.map(l => {
      const m = new Map((l.s?.x || []).map((d, i) => [d, l.s.y[i]]));
      return { name: l.nome, type: 'line', symbol: 'none', connectNulls: true,
               lineStyle: { width: l.larg }, itemStyle: { color: l.cor },
               data: xsB.map(d => m.has(d) ? m.get(d) : null) };
    }),
    tooltip: { ...baseChart().tooltip, valueFormatter: v => v == null ? '—' : `${v} (${sinal(v - 100)})` },
  });
  $('#pa-basket-nota').innerHTML = bsk.nota;

  // ------------------------------------------------------------- tabela
  const janelas = ['wtd', 'mtd', 'ytd', '12m'];
  const linhas = [...acoes, ...P.papeis.filter(p => p.tipo === 'indice')].map(p => {
    const s = serie(P, p.ticker, moeda);
    const o = {
      ticker: p.ticker, nome: p.grupo ? nomeCia(p.grupo) : (p.ticker === 'SMAL11' ? 'SMLL (SMAL11)' : p.ticker),
      tipo: p.tipo === 'indice' ? TX('índice') : TX('ação'),
      moeda: moeda === 'brl' ? 'BRL' : p.moeda,
      ultimo: s && s.c.length ? s.c[s.c.length - 1] : null,
      sel: selPapeis.has(p.ticker) ? '●' : '',
    };
    janelas.forEach(j => { o[j] = retorno(P, p.ticker, j, moeda); });
    o.periodo = retorno(P, p.ticker, periodo, moeda, ate);
    return o;
  });
  const colRet = (k, t) => ({ k, t, tipo: 'num', fmt: v => v == null ? '—'
    : `<span class="delta ${v > 0 ? 'pos' : v < 0 ? 'neg' : ''}">${sinal(v)}</span>` });
  tabela($('#pa-tab'), [
    { k: 'ticker', t: TX('Papel'), tipo: 'txt' },
    { k: 'nome', t: TX('Companhia'), tipo: 'txt' },
    { k: 'tipo', t: TX('Tipo'), tipo: 'txt', fmt: v => `<span class="tag">${esc(v)}</span>` },
    { k: 'ultimo', t: TX('Último'), tipo: 'num', fmt: (v, r) => v == null ? '—'
        : `${r.moeda} ${v.toLocaleString(idioma() === 'en' ? 'en-US' : 'pt-BR',
            { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` },
    colRet('wtd', 'WTD'), colRet('mtd', 'MTD'),
    colRet('ytd', 'YTD'), colRet('12m', TX('12 meses')),
    colRet('periodo', rotuloJanela),
  ], linhas, { ordem: 'periodo', csv: { bloco: 'precos', nome: TX('Retornos por janela') } });
  $('#pa-tab-nota').textContent = TX(
    'Fechamento ajustado por proventos e desdobramentos. WTD parte do fechamento da última ' +
    'sexta; MTD, do último pregão do mês anterior; YTD, do último pregão do ano anterior. ' +
    'Preços coletados em {q}.', { q: P.atualizado_em });

  /* ---------------------------------------- fechamento dia a dia ------------
   * A peça que faltava: o bloco inteiro era retorno rebaseado, e não havia onde LER o
   * preço de um pregão específico. Aqui é uma linha por dia, papel por coluna.
   *
   * ⚠️ Cada coluna sai na moeda do seu papel quando "moeda local" está selecionada — a
   * Afya negocia em USD. Uma tabela que carimbasse R$ em tudo estaria errada, não
   * apenas mal formatada.
   *
   * Na tela vão os 60 pregões mais recentes; o Excel leva a série inteira do período,
   * que é a razão de o conjunto registrado no CSV ser `todasLinhas` e não o recorte. */
  const dias = [...new Set(sel.flatMap(p => {
    const s = serie(P, p.ticker, moeda);
    if (!s) return [];
    const { limite, inclusive } = inicioJanela(P, periodo);
    const i0 = Math.max(0, idxAte(s.d, limite, inclusive));
    const i1 = idxFim(s.d, ate);
    return i1 >= i0 ? s.d.slice(i0, i1 + 1) : [];
  }))].sort().reverse();

  const mapaPapel = {};
  sel.forEach(p => {
    const s = serie(P, p.ticker, moeda);
    mapaPapel[p.ticker] = s ? new Map(s.d.map((d, i) => [d, s.c[i]])) : new Map();
  });
  const todasLinhas = dias.map(d => {
    const o = { _iso: d };
    sel.forEach(p => { o[p.ticker] = mapaPapel[p.ticker].get(d) ?? null; });
    return o;
  });

  $('#pa-fech-tit').textContent = TX('Preço de fechamento, dia a dia — {p}',
    { p: rotuloJanela });
  /* ⚠️ A coluna de data guarda o ISO e SÓ exibe o formato brasileiro pelo `fmt`.
   * Guardar "17/08/2026" no dado ordenaria por dia do mês. E `ordem` é obrigatório
   * aqui: sem ele o `tabela()` cai em `cols[1]`, que é o primeiro papel — a tabela
   * saía ordenada por preço da COGN3, com as datas embaralhadas. */
  tabela($('#pa-fech'), [
    { k: '_iso', t: TX('Pregão'), tipo: 'txt', fmt: v => dataLegivel(v) },
    ...sel.map(p => ({
      k: p.ticker, t: p.ticker, tipo: 'num',
      fmt: v => v == null ? '—' : paPreco(v, moeda, p),
    })),
  ], todasLinhas, {
    ordem: '_iso', limite: 60,
    csv: { bloco: 'precos', nome: TX('Fechamento por dia'),
           cols: [{ k: '_iso', t: TX('Data') },
                  ...sel.map(p => ({ k: p.ticker, t: p.ticker }))] },
  });
  $('#pa-fech-nota').textContent = TX(
    'Os 60 pregões mais recentes do período na tela; o Excel traz os {q} do período inteiro. ' +
    'Fechamento AJUSTADO — incorpora proventos e desdobramentos, então um valor antigo pode ' +
    'não bater com a cotação exibida naquele dia; é a série correta para retorno. Célula ' +
    'vazia é pregão sem negócio para aquele papel, ou papel ainda não listado. Moeda: {m}.',
    { q: n(dias.length),
      m: moeda === 'brl' ? TX('tudo convertido para BRL')
                         : TX('cada papel na moeda local') });

  // CSV da série completa do gráfico
  registrarCSV('precos', TX('Série de preços (fechamento ajustado)'),
    [{ k: 'data', t: TX('Data') }, { k: 'ticker', t: TX('Papel') },
     { k: 'fechamento', t: TX('Fechamento') }, { k: 'moeda', t: TX('Moeda') }],
    P.papeis.filter(p => p.tipo !== 'cambio').flatMap(p => {
      const s = serie(P, p.ticker, moeda);
      return s ? s.d.map((d, i) => ({ data: d, ticker: p.ticker, fechamento: s.c[i],
                                      moeda: moeda === 'brl' ? 'BRL' : p.moeda })) : [];
    }));
  registrarCSV('precos', TX('Retorno acumulado (base 100)'),
    [{ k: 'x', t: TX('Data') }, ...series.map(x => ({ k: x.p.ticker, t: x.p.ticker })),
     { k: 'BASKET', t: TX('Basket Education') }],
    xs.map(d => {
      const o = { x: d };
      series.forEach(({ p, s }) => { const i = s.x.indexOf(d); o[p.ticker] = i >= 0 ? s.y[i] : null; });
      const ib = bsk.serie ? bsk.serie.x.indexOf(d) : -1;
      o.BASKET = ib >= 0 ? bsk.serie.y[ib] : null;
      return o;
    }));

  autoAtualizar();
}

/* Reconsulta o arquivo de preços e redesenha quando o carimbo muda.
 *
 * ⚠️ Isto foi REMOVIDO e depois RESTAURADO, e a ida e volta tem razão. Saiu quando o bloco
 * virou de fechamento diário: repintar de 5 em 5 minutos não fazia sentido para um dado
 * que muda uma vez por dia. Voltou quando o `precos.yml` passou a coletar de 5 em 5
 * minutos no pregão pelo GitHub Actions — sem este laço, o arquivo ficaria fresco no
 * servidor e a tela aberta continuaria mostrando o preço de quando foi carregada, o que
 * anularia a coleta.
 *
 * O intervalo acompanha o do coletor. Só redesenha se o carimbo mudou: sem essa guarda,
 * a tela repintaria sozinha a cada 5 minutos e perderia a ordenação e o scroll do usuário.
 * No arquivo único e no artifact o fetch falha e fica o snapshot embutido — que é o
 * comportamento certo, porque ali não há servidor para consultar. */
function autoAtualizar() {
  if (timerAuto) return;
  timerAuto = setInterval(async () => {
    if (!document.querySelector('#v-precos')?.classList.contains('on')) return;
    try {
      const r = await fetch('data/precos.json?t=' + Date.now(), { cache: 'no-store' });
      if (!r.ok) return;
      const novo = await r.json();
      if (!novo?.atualizado_em || novo.atualizado_em === D.precos?.atualizado_em) return;
      D.precos = novo;
      await precos();
    } catch (e) { /* offline ou sem servidor: mantém o snapshot */ }
  }, 5 * 60 * 1000);
}

/* ─────────────────────────────────────────────────── frescor da coleta ─────
 * "Coletado há 4 min", com bolinha. Existe porque o bloco passou a ser alimentado por
 * robô: sem um sinal de idade na tela, uma coleta que parou de rodar é indistinguível de
 * um mercado parado — os dois deixam o número igual ao de antes.
 *
 * ⚠️ O instante vem de `atualizado_utc`, e isso não é preciosismo. `atualizado_em` é uma
 * string SEM FUSO ("2026-08-18 17:02"), e `new Date()` a interpreta como hora LOCAL: o
 * arquivo que o GitHub Actions grava em UTC era lido como se fosse BRT e a idade dava
 * ~3 horas NEGATIVA. Era por isso que o aviso de "snapshot com mais de 24h" nunca
 * aparecia. Arquivo antigo, sem o campo novo, cai no fallback de ler como UTC — que é o
 * que todo arquivo publicado sempre foi.
 */
function instanteColeta(P) {
  if (!P) return null;
  if (P.atualizado_utc) {
    const d = new Date(P.atualizado_utc);
    if (!isNaN(d)) return d;
  }
  if (!P.atualizado_em) return null;
  const d = new Date(P.atualizado_em.replace(' ', 'T') + 'Z');
  return isNaN(d) ? null : d;
}

/* Faixas deliberadamente largas. O cron do GitHub PULA execuções — medido: 3 rodadas em
 * 2,5 h, não ~30 — e fora do pregão o dado É velho e está certo assim. Bolinha vermelha
 * num domingo seria alarme falso, que treina o leitor a ignorar o indicador. */
function frescor(P) {
  const d = instanteColeta(P);
  if (!d) return { cor: 'nd', txt: '—', titulo: TX('Sem carimbo de coleta neste arquivo') };
  const min = Math.max(0, Math.round((Date.now() - d.getTime()) / 60000));
  const txt = min < 1 ? TX('agora')
    : min < 60 ? TX('há {n} min', { n: min })
    : min < 60 * 36 ? TX('há {n} h', { n: Math.round(min / 60) })
    : TX('há {n} dias', { n: Math.round(min / 1440) });
  const cor = min <= 90 ? 'ok' : min <= 60 * 24 ? 'meio' : 'velho';
  return {
    cor, txt, min,
    titulo: TX('Última coleta: {q} (seu fuso). Durante o pregão o robô coleta algumas ' +
               'vezes por hora; fora dele o dado fica parado, e isso é o esperado.',
              { q: d.toLocaleString(locale()) }),
  };
}

/* Reescreve SÓ a bolinha, de 30 em 30 segundos. Não pode chamar a view: um re-render a
 * cada meio minuto perderia a ordenação da tabela e o scroll de quem está lendo. */
function ligaFrescor() {
  if (timerFrescor) return;
  timerFrescor = setInterval(() => {
    const el = $('#pa-frescor');
    if (!el || !document.querySelector('#v-precos')?.classList.contains('on')) return;
    pintaFrescor(el);
  }, 30000);
}

function pintaFrescor(el) {
  const f = frescor(D.precos);
  el.className = `frescor ${f.cor}`;
  el.title = f.titulo;
  el.innerHTML = `<i></i>${esc(f.txt)}`;
}

/* Formata retorno com sinal explícito — sem o "+" o investidor precisa procurar a cor. */
function sinal(v, suf = '%') {
  if (v == null || isNaN(v)) return '—';
  return (v > 0 ? '+' : '') + v.toFixed(1).replace('.', idioma() === 'en' ? '.' : ',') + suf;
}

/* ------------------------------------------------------------------ basket
 * Índice de Education com as companhias selecionadas, rebaseado em 100.
 *
 * No peso padrão a cesta é um índice de capitalização de verdade: soma-se
 * `ações × preço` de cada papel e rebaseia-se o total. Isso faz o peso flutuar com o
 * preço ao longo do período, como num índice, em vez de congelar a foto de hoje.
 * A cesta é SEMPRE em BRL — somar valor de mercado em moedas diferentes não faz
 * sentido, e é o que torna a comparação com IBOV e SMLL legítima.
 *
 * Quem não tem preço no início da janela fica de fora e a cesta é renormalizada, senão
 * ela daria um salto artificial no dia em que o papel estreia.                        */
function basket(P, sel, janela, modo, fimJanela) {
  const acoesDe = p => (modo === 'igual' ? null : p.acoes_eq) || null;

  /* Sempre em BRL, mesmo que a tela esteja em "moeda local": somar valor de mercado de
   * papel em USD com papel em BRL não significaria nada, e é a conversão que torna a
   * comparação com IBOV e SMLL legítima.
   *
   * ⚠️ `idxAte` devolvendo -1 significa "não havia preço no início da janela" — e aqui
   * isso EXCLUI o papel, diferente do `rebase()`, que cai no primeiro preço disponível.
   * Se a VTRU3 entrasse na cesta no dia da estreia na B3, a cesta daria um salto que é
   * entrada de papel, não retorno. */
  const { limite, inclusive } = inicioJanela(P, janela);
  const comp = [], fora = [];
  sel.forEach(p => {
    const s = serie(P, p.ticker, 'brl');
    if (!s || !s.c.length) { fora.push(p); return; }
    /* ⚠️ `Math.max(0, ...)`, e não `>= 0`, é o que faz a janela "Máximo" funcionar.
     *
     * Para `max`, `inicioJanela` devolve o limite '0000-01-01' — anterior a tudo —, então
     * `idxAte` responde -1 para TODOS os papéis, que é a resposta correta à pergunta
     * "havia preço antes do início?". Uma versão anterior tratava -1 como "fica de fora"
     * e mandava a cesta inteira para `fora`: o gráfico do basket ficava vazio só nessa
     * janela, enquanto o KPI continuava certo, porque vinha do mesmo cálculo antes de
     * quebrar. Aqui -1 significa "começa no primeiro preço que tiver", que é o mesmo
     * tratamento do `rebase()`.
     *
     * Papel que estreia no meio da janela não precisa mais ser excluído: o encadeamento
     * abaixo cuida da entrada dele sem criar degrau. */
    const i0 = Math.max(0, idxAte(s.d, limite, inclusive));
    const base = s.c[i0];
    if (!base) { fora.push(p); return; }
    // corta a série no fim da janela antes de entrar na cesta
    const i1 = idxFim(s.d, fimJanela);
    if (i1 <= i0) { fora.push(p); return; }
    comp.push({ p, s: { d: s.d.slice(0, i1 + 1), c: s.c.slice(0, i1 + 1) }, i0, base });
  });

  if (!comp.length) return { retorno: null, serie: null, nota: TX('Sem papel com preço no período.') };

  // peso: valor de mercado no início da janela (ou 1, no modo peso igual)
  const w = {};
  comp.forEach(({ p, base }) => { const q = acoesDe(p); w[p.ticker] = q ? q * base : 1; });

  const xs = [...new Set(comp.flatMap(x => x.s.d.slice(x.i0)))].sort();

  /* ⚠️ CARREGA O ÚLTIMO PREÇO em dia sem cotação — não deixa o papel sair da cesta.
   *
   * Este é o conserto dos "vales" que apareciam no gráfico: quedas de até 22% num único
   * pregão, com recuperação integral no dia seguinte. Nenhum preço tinha se mexido.
   *
   * A causa é a AFYA, que negocia na Nasdaq. Em feriado americano com pregão na B3 ela
   * fica sem preço; a versão anterior a excluía do dia e renormalizava a média sobre os
   * outros seis. Como a razão dela contra a base era diferente da média dos demais, o
   * índice saltava — e voltava no dia seguinte, quando ela reaparecia. Conferido: TODOS
   * os saltos acima de 12% coincidem com a contagem de papéis mudando de 7 para 6.
   *
   * Índice de verdade não se rebalanceia porque a bolsa de um componente fechou. A regra
   * correta é a que os provedores usam: repete o último preço conhecido.
   *
   * ⚠️ A repetição só vale DEPOIS da primeira cotação do papel na janela. Antes disso ele
   * genuinamente não existe na cesta — a VTRU3 só passou a ser negociada na B3 em
   * 11/06/2024 —, e aí a exclusão com renormalização é o tratamento certo. Confundir as
   * duas coisas criaria o degrau artificial que a exclusão existe para evitar. */
  const mapas = comp.map(({ p, s, base }) => {
    const bruto = new Map(s.d.map((d, i) => [d, s.c[i] == null ? null : s.c[i] / base]));
    const m = new Map();
    let ult = null;
    for (const d of xs) {
      const v = bruto.get(d);
      if (v != null) ult = v;
      // `ult` nulo = ainda não estreou na janela; fica de fora e a cesta renormaliza
      m.set(d, ult);
    }
    return { tk: p.ticker, m };
  });

  /* ÍNDICE ENCADEADO: o valor de hoje é o de ontem vezes o retorno do dia, e o retorno do
   * dia é calculado SÓ sobre os papéis que tinham preço nos DOIS dias.
   *
   * ⚠️ Isto substitui a média rebaseada, que tinha um defeito estrutural: o valor saía de
   * `Σ w·(p/base) / Σ w` sobre os papéis presentes NAQUELE dia, então qualquer mudança na
   * composição mexia no denominador e o índice pulava sem que preço nenhum tivesse
   * mudado. Dois casos reais no gráfico:
   *
   *   - feriado americano: a AFYA sumia por um dia e a cesta caía 22%, recuperando tudo
   *     no dia seguinte — os "vales" que o usuário viu;
   *   - estreia da VTRU3 na B3 em 11/06/2024: o papel entrava com razão 1,0 no meio de
   *     uma média que estava em 0,7, e a cesta dava um degrau para cima.
   *
   * O encadeamento resolve os dois porque nunca compara conjuntos diferentes: no dia em
   * que um papel entra, ele simplesmente não participa do retorno daquele dia, e passa a
   * participar do seguinte. É o que qualquer provedor de índice faz.
   *
   * `w[tk]` é `ações × preço-base` e `m` guarda `preço/base`, então `w·m` é `ações ×
   * preço` — o valor de mercado do dia. A razão entre a soma de hoje e a de ontem é o
   * retorno ponderado por valor de mercado. */
  let idx = 100, ultimo = null, ant = null;
  const y = xs.map(d => {
    const hoje = {};
    for (const { tk, m } of mapas) {
      const v = m.get(d);
      if (v != null) hoje[tk] = v;
    }
    if (!Object.keys(hoje).length) { ant = ant || null; return null; }
    if (ant) {
      let num = 0, den = 0;
      for (const tk of Object.keys(hoje)) {
        if (ant[tk] == null) continue;      // entrou hoje: fora do retorno de hoje
        num += w[tk] * hoje[tk];
        den += w[tk] * ant[tk];
      }
      if (den) idx *= num / den;
    }
    ant = hoje;
    ultimo = +idx.toFixed(2);
    return ultimo;
  });
  return { retorno: ultimo == null ? null : ultimo - 100, serie: { x: xs, y },
           nota: notaBasket(comp.map(x => x.p), fora, modo, w) };
}

function ultimoFX(P) {
  const s = P.series.USDBRL;
  return s && s.c.length ? s.c[s.c.length - 1] : 1;
}

function notaBasket(dentro, fora, modo, w) {
  const tot = Object.values(w).reduce((s, v) => s + v, 0) || 1;
  const ord = [...dentro].sort((a, b) => (w[b.ticker] || 0) - (w[a.ticker] || 0));
  const comp = ord.map(p => `${esc(p.ticker)} ${pct(100 * w[p.ticker] / tot)}`).join(' · ');
  const base = modo === 'igual'
    ? TX('Cesta com peso igual entre os papéis selecionados.')
    : TX('Índice ponderado por valor de mercado: soma de ações × preço dos papéis ' +
         'selecionados, rebaseada em 100. O peso acompanha o preço ao longo do período, ' +
         'como num índice. Cesta sempre em BRL.');
  const excl = fora.length
    ? ' ' + TX('Fora da cesta neste período, por não ter preço no início da janela: {l}.',
               { l: fora.map(p => esc(p.ticker)).join(', ') })
    : '';
  return `${base} <strong>${TX('Composição no início do período')}:</strong> ${comp}.${excl} ` +
         TX('SMLL entra pelo SMAL11, o ETF que replica o índice.');
}

