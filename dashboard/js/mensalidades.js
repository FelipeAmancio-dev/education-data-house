/* Mensalidades praticadas — o preco de tabela das faculdades das companhias abertas.
 *
 * Que duvida de investidor isto responde: quanto cada player consegue cobrar, em que
 * modalidade e em que praca. Junto com a base de alunos, preco e o outro lado da receita;
 * e a distancia entre um presencial de capital e um EAD de R$ 129 e a propria tese de
 * posicionamento de cada grupo.
 *
 * ⚠️ Isto e PRECO DE TABELA, nao ticket liquido. As companhias reportam receita liquida
 * depois de bolsa, desconto de captacao, inadimplencia e FIES/ProUni. A tela nao serve
 * para reconciliar com o release — serve para comparar posicionamento entre players e
 * acompanhar o movimento da tabela ao longo do tempo. O aviso fica na tela, nao so aqui.
 *
 * Fonte: `data/mensalidades.json`, gerado por `scripts/07_fetch_mensalidades.py`.
 * O numero publicado por (IES, curso, modalidade) e a MEDIA SIMPLES do menor preco de
 * cada unidade/polo; min, max e o numero de ofertas viajam junto, e e o que permite
 * mostrar a dispersao em vez de esconder tudo atras de uma media.
 */
import { D, carregarMensalidades, linhas, brl, n } from './dados.js';
import { $, esc, tabela, chart, baseChart, opcoes, registrarCSV, PALETA } from './ui.js';
import { TX, TXcurso, idioma } from './i18n.js';

let modalidade = 'presencial';
let cursoSel = '';

const MODS = ['presencial', 'semipresencial', 'ead'];
const ROT_MOD = { presencial: 'Presencial', semipresencial: 'Semipresencial', ead: 'EAD' };

const meNomeGrupo = g => D.gruposOrd[g]?.nome || g;
const corDoGrupo = (g, i) => D.gruposOrd[g]?.cor || PALETA[i % PALETA.length];

const meData = s => new Date(s + 'T12:00:00').toLocaleDateString(
  idioma() === 'en' ? 'en-US' : 'pt-BR',
  idioma() === 'en' ? { year: 'numeric', month: 'short', day: 'numeric' } : undefined);

/* Mediana, nao media: a distribuicao de mensalidade tem cauda longa (Odontologia e
 * Medicina Veterinaria puxam qualquer media para cima) e o KPI de topo precisa
 * descrever o curso tipico, nao o mais caro. */
function mediana(vs) {
  if (!vs.length) return null;
  const s = [...vs].sort((a, b) => a - b);
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

/* --------------------------------------------------------------------- dados */
function ultimaColeta(MZ) {
  const d = MZ.datas || [];
  return d.length ? d[d.length - 1] : null;
}

/* Linhas da ultima coleta, opcionalmente de uma modalidade. */
function base(MZ, mod) {
  const data = ultimaColeta(MZ);
  return linhas(MZ).filter(r => r.data === data && (!mod || r.modalidade === mod));
}

/* --------------------------------------------- mensalidade media por instituicao */
function porInstituicao(MZ) {
  const rs = base(MZ, modalidade);
  const el = $('#me-inst');
  if (!rs.length) {
    el.innerHTML = `<div class="vazio">${TX('Nenhuma instituição coletada nesta modalidade')}</div>`;
    return;
  }
  const porIes = {};
  rs.forEach(r => (porIes[r.ies] = porIes[r.ies] || { ies: r.ies, grupo: r.grupo, vs: [] })
    .vs.push(r.preco));
  const dados = Object.values(porIes)
    .map(o => ({ ies: o.ies, grupo: o.grupo, mediana: mediana(o.vs),
                 cursos: o.vs.length, min: Math.min(...o.vs), max: Math.max(...o.vs) }))
    .sort((a, b) => b.mediana - a.mediana);

  chart(el, {
    ...baseChart(),
    legend: { show: false },
    grid: { left: 8, right: 60, top: 10, bottom: 6, containLabel: true },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' },
               backgroundColor: '#fff', borderColor: '#D2D4D8', borderWidth: 1,
               textStyle: { color: '#1A1A1A', fontSize: 12.5 },
               formatter: p => {
                 const d = dados[p[0].dataIndex];
                 return `<strong>${esc(d.ies)}</strong><br>${esc(meNomeGrupo(d.grupo))}<br>` +
                   `${TX('Mediana')}: ${brl(d.mediana)}<br>` +
                   `${TX('Faixa')}: ${brl(d.min)} – ${brl(d.max)}<br>` +
                   `${d.cursos} ${TX('cursos acompanhados')}`;
               } },
    xAxis: { type: 'value', splitLine: { lineStyle: { color: '#F2F3F5' } },
             axisLabel: { fontSize: 11.5, color: '#8C8C8C',
                          formatter: v => 'R$ ' + v.toLocaleString(idioma() === 'en' ? 'en-US' : 'pt-BR') } },
    yAxis: { type: 'category', data: dados.map(d => d.ies), inverse: true,
             axisLine: { show: false }, axisTick: { show: false },
             axisLabel: { fontSize: 12, color: '#4A4A4A' } },
    series: [{
      type: 'bar', barMaxWidth: 26,
      data: dados.map((d, i) => ({ value: d.mediana, itemStyle: { color: corDoGrupo(d.grupo, i) } })),
      label: { show: true, position: 'right', fontSize: 11.5, color: '#4A4A4A',
               formatter: p => brl(p.value) },
    }],
  });

  registrarCSV('mensalidades', TX('Mensalidade por instituição'), [
    { k: 'ies', t: TX('Instituição') }, { k: 'grupo', t: TX('Grupo') },
    { k: 'mediana', t: TX('Mediana') }, { k: 'min', t: TX('Mínimo') },
    { k: 'max', t: TX('Máximo') }, { k: 'cursos', t: TX('Cursos acompanhados') },
  ], dados.map(d => ({ ...d, grupo: meNomeGrupo(d.grupo) })));
}

/* ------------------------------------------------- matriz curso x instituicao */
function matriz(MZ) {
  const rs = base(MZ, modalidade);
  const el = $('#me-matriz');
  if (!rs.length) {
    el.innerHTML = `<div class="vazio">${TX('Sem dados nesta modalidade')}</div>`;
    return;
  }
  const ies = [...new Set(rs.map(r => r.ies))].sort();
  // quem só publica "a partir de" nacional leva marca no cabeçalho: comparar um piso
  // nacional com a média de dezenas de unidades é o erro de leitura mais fácil aqui
  const soNacional = {};
  ies.forEach(i => {
    const linhas_i = rs.filter(r => r.ies === i);
    soNacional[i] = linhas_i.length && linhas_i.every(r => r.base === 'nacional');
  });
  const porCurso = {};
  rs.forEach(r => {
    (porCurso[r.curso] = porCurso[r.curso] || { curso: r.curso })[r.ies] = r.preco;
  });

  // "spread" = o quanto o mais caro cobra a mais que o mais barato NAQUELE curso. E a
  // leitura competitiva: mostra onde ha premio de marca e onde o preco ja convergiu.
  const dados = Object.values(porCurso).map(o => {
    const vs = ies.map(i => o[i]).filter(v => v != null);
    return { ...o, _min: Math.min(...vs), _max: Math.max(...vs),
             spread: vs.length > 1 ? 100 * (Math.max(...vs) / Math.min(...vs) - 1) : null };
  });

  const cols = [
    { k: 'curso', t: TX('Curso'), tipo: 'txt', fmt: v => esc(TXcurso(v)) },
    ...ies.map(i => ({ k: i, t: i + (soNacional[i] ? ' *' : ''), tipo: 'num',
                       fmt: v => v == null ? '—' : brl(v) })),
    { k: 'spread', t: TX('Spread'), tipo: 'pct',
      fmt: v => v == null ? '—' : (v >= 0 ? '+' : '') + v.toFixed(0) + '%' },
  ];
  tabela(el, cols, dados, {
    ordem: 'curso',
    csv: { bloco: 'mensalidades', nome: TX('Curso × instituição') + ' — ' + TX(ROT_MOD[modalidade]) },
  });

  const marcadas = ies.filter(i => soNacional[i]);
  $('#me-matriz-nota').textContent = marcadas.length ? TX(
    '* {l} publicam apenas um "a partir de" nacional, sem preço por unidade. O valor é um ' +
    'piso, não a média das praças — o spread contra as demais tende a ficar exagerado.',
    { l: marcadas.sort().join(', ') }) : '';
}

/* ------------------------------------------------------ dispersao por unidade */
function dispersao(MZ) {
  const rs = base(MZ, modalidade);
  const el = $('#me-disp');
  const sel = $('#me-curso');
  const cursos = [...new Set(rs.map(r => r.curso))].sort();
  if (!cursos.length) {
    sel.innerHTML = '';
    el.innerHTML = `<div class="vazio">${TX('Sem dados nesta modalidade')}</div>`;
    $('#me-disp-nota').textContent = '';
    return;
  }
  cursoSel = opcoes(sel, cursos.map(c => ({ v: c, t: TXcurso(c) })), () => {
    cursoSel = sel.value;
    dispersao(MZ);
  });
  if (!cursos.includes(cursoSel)) { cursoSel = cursos[0]; sel.value = cursoSel; }

  // Só entram as instituições que publicam preço POR UNIDADE. Cogna e Uniasselvi divulgam
  // um "a partir de" nacional: elas não têm faixa por praça, e desenhá-las aqui como um
  // ponto sem barra sugeriria preço uniforme no país inteiro — que é conclusão, não dado.
  const todos = rs.filter(r => r.curso === cursoSel);
  const nacionais = todos.filter(r => r.base === 'nacional');
  const dados = todos.filter(r => r.base !== 'nacional')
    .map(r => ({ ies: r.ies, grupo: r.grupo, min: r.min, max: r.max,
                 preco: r.preco, n: r.n_ofertas }))
    .sort((a, b) => b.preco - a.preco);
  if (!dados.length) {
    el.innerHTML = `<div class="vazio">${TX(
      'Nenhuma instituição publica preço por unidade neste curso.')}</div>`;
    $('#me-disp-nota').textContent = '';
    return;
  }

  // Barra flutuante do minimo ao maximo (base transparente + faixa colorida) com o
  // ponto da media publicada em cima. Um preco medio sozinho esconderia que Odontologia
  // presencial vai de R$ 706 a R$ 1.427 na MESMA instituicao, conforme a praca.
  chart(el, {
    ...baseChart(),
    legend: { show: false },
    grid: { left: 8, right: 90, top: 10, bottom: 6, containLabel: true },
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'shadow' },
      backgroundColor: '#fff', borderColor: '#D2D4D8', borderWidth: 1,
      textStyle: { color: '#1A1A1A', fontSize: 12.5 },
      formatter: p => {
        const d = dados[p[0].dataIndex];
        return `<strong>${esc(d.ies)}</strong><br>${esc(meNomeGrupo(d.grupo))}<br>` +
          `${TX('Mensalidade publicada')}: ${brl(d.preco)}<br>` +
          `${TX('Mais barata')}: ${brl(d.min)}<br>${TX('Mais cara')}: ${brl(d.max)}<br>` +
          `${d.n} ${TX('unidades/polos')}`;
      },
    },
    xAxis: { type: 'value', splitLine: { lineStyle: { color: '#F2F3F5' } },
             axisLabel: { fontSize: 11.5, color: '#8C8C8C',
                          formatter: v => 'R$ ' + v.toLocaleString(idioma() === 'en' ? 'en-US' : 'pt-BR') } },
    yAxis: { type: 'category', data: dados.map(d => d.ies), inverse: true,
             axisLine: { show: false }, axisTick: { show: false },
             axisLabel: { fontSize: 12, color: '#4A4A4A' } },
    series: [
      { type: 'bar', stack: 'f', silent: true, itemStyle: { color: 'transparent' },
        data: dados.map(d => d.min) },
      { type: 'bar', stack: 'f', barMaxWidth: 18,
        data: dados.map((d, i) => ({ value: d.max - d.min,
                                     itemStyle: { color: corDoGrupo(d.grupo, i), opacity: .35 } })),
        label: { show: true, position: 'right', fontSize: 11, color: '#8C8C8C',
                 formatter: p => brl(dados[p.dataIndex].min) + ' – ' + brl(dados[p.dataIndex].max) } },
      { type: 'scatter', symbolSize: 11, z: 5,
        data: dados.map((d, i) => ({ value: [d.preco, i],
                                     itemStyle: { color: corDoGrupo(d.grupo, i) } })) },
    ],
  });

  const tot = dados.reduce((s, d) => s + d.n, 0);
  $('#me-disp-nota').textContent = TX(
    'O ponto é a mensalidade publicada (média simples do menor preço de cada unidade). ' +
    'A faixa vai da unidade mais barata à mais cara: {t} unidades/polos observados.',
    { t: n(tot) }) + (nacionais.length ? ' ' + TX(
      'Fora do gráfico: {q} instituição(ões) que só publicam um "a partir de" nacional — {l}.',
      { q: nacionais.length, l: nacionais.map(r => r.ies).sort().join(', ') }) : '');

  registrarCSV('mensalidades', TX('Dispersão por unidade') + ' — ' + TXcurso(cursoSel), [
    { k: 'ies', t: TX('Instituição') }, { k: 'grupo', t: TX('Grupo') },
    { k: 'preco', t: TX('Mensalidade publicada') }, { k: 'min', t: TX('Mínimo') },
    { k: 'max', t: TX('Máximo') }, { k: 'n', t: TX('Unidades/polos') },
  ], dados.map(d => ({ ...d, grupo: meNomeGrupo(d.grupo) })));
}

/* ------------------------------------------------------------- série no tempo
 * So aparece quando ha mais de uma coleta: com uma data unica um grafico de linha
 * desenharia um ponto solto e sugeriria tendencia onde nao ha nenhuma. */
function meSerie(MZ) {
  const card = $('#me-serie-card');
  const datas = MZ.datas || [];
  // o titulo da secao acompanha o card, senao sobra um "Evolução" com nada embaixo
  $('#me-serie-tit').hidden = datas.length < 2;
  if (datas.length < 2) {
    card.hidden = true;
    return;
  }
  card.hidden = false;
  const todas = linhas(MZ).filter(r => r.modalidade === modalidade);
  const ies = [...new Set(todas.map(r => r.ies))].sort();
  const series = ies.map((i, k) => {
    const g = todas.find(r => r.ies === i)?.grupo;
    return {
      name: i, type: 'line', symbol: 'circle', symbolSize: 6, smooth: false,
      itemStyle: { color: corDoGrupo(g, k) }, lineStyle: { width: 2.2 },
      data: datas.map(d => {
        const vs = todas.filter(r => r.ies === i && r.data === d).map(r => r.preco);
        return vs.length ? +mediana(vs).toFixed(2) : null;
      }),
      connectNulls: true,
    };
  });
  chart($('#me-serie'), {
    ...baseChart(),
    xAxis: { ...baseChart().xAxis, data: datas.map(meData) },
    yAxis: { ...baseChart().yAxis,
             axisLabel: { fontSize: 11.5, color: '#8C8C8C',
                          formatter: v => 'R$ ' + v.toLocaleString(idioma() === 'en' ? 'en-US' : 'pt-BR') } },
    series,
  });

  registrarCSV('mensalidades', TX('Série de mensalidade'), [
    { k: 'data', t: TX('Data') }, { k: 'ies', t: TX('Instituição') },
    { k: 'curso', t: TX('Curso') }, { k: 'preco', t: TX('Mensalidade publicada') },
  ], todas.map(r => ({ data: r.data, ies: r.ies, curso: TXcurso(r.curso), preco: r.preco })));
}

/* -------------------------------------------------------------------- chips */
function meChips(MZ) {
  const box = $('#me-mod');
  if (box.dataset.pronto) return;
  box.dataset.pronto = '1';
  box.onclick = ev => {
    const b = ev.target.closest('button[data-m]');
    if (!b || b.dataset.m === modalidade) return;
    modalidade = b.dataset.m;
    [...box.querySelectorAll('button')].forEach(x => x.classList.toggle('on', x.dataset.m === modalidade));
    desenhar(MZ);
  };
}

/* ------------------------------------------------------- exclusao por cobertura */
/* No EAD o preco varia por polo, entao a linha so e comparavel se vier de varias pracas
 * — a Estacio entra com 64 polos de capital. `exporta_web()` deixa de fora quem nao chega
 * a MIN_POLOS_EAD e devolve os nomes em `ead_fora`; aqui a tela DIZ quem ficou de fora.
 * Excluir calado seria pior que o problema original: a IES sumiria da coluna e o leitor
 * concluiria que ela nao oferta EAD. */
function notaEAD(MZ) {
  const el = $('#me-ead-nota');
  const fora = MZ.ead_fora || [];
  if (modalidade !== 'ead' || !fora.length) { el.innerHTML = ''; return; }

  const quem = fora.map(f => `${f.ies} (${f.grupo})`).join(', ');
  const polos = Math.max(...fora.map(f => f.polos));
  // a referencia sai do proprio dado publicado, nao cravada no texto: o numero de polos
  // muda a cada coleta, e um "64" fixo aqui envelhece calado
  const pub = base(MZ, 'ead').map(r => r.n_ofertas);
  const ref = pub.length ? Math.max(...pub) : null;
  el.innerHTML = `<div class="aviso">${TX(
    'Fora da comparação de EAD: {q}. A coleta trouxe apenas {p} polo(s) — abaixo do mínimo ' +
    'de {m} para publicar a linha como média de praças{c}. A instituição oferta EAD; o que ' +
    'falta é cobertura, não o curso.',
    { q: quem, p: polos, m: MZ.ead_min_polos,
      c: ref ? TX(', contra os {r} polos de quem está na tela', { r: ref }) : '' })}</div>`;
}

function desenhar(MZ) {
  notaEAD(MZ);
  porInstituicao(MZ);
  matriz(MZ);
  dispersao(MZ);
  meSerie(MZ);
}

/* --------------------------------------------------------------------- view */
export async function mensalidades() {
  const MZ = await carregarMensalidades();
  const aviso = $('#me-aviso');

  if (!MZ || !MZ.n) {
    aviso.innerHTML = `<div class="aviso">${TX(
      'A coleta de mensalidades ainda não rodou nesta cópia. Rode ' +
      '<code>python scripts/07_fetch_mensalidades.py</code> para preencher este bloco.')}</div>`;
    ['#me-inst', '#me-matriz', '#me-disp'].forEach(s => { $(s).innerHTML = ''; });
    $('#me-serie-card').hidden = true;
    $('#me-serie-tit').hidden = true;
    return;
  }
  aviso.innerHTML = '';

  $('#me-carimbo').textContent = TX('Coleta de {d} · {o} preços por unidade', {
    d: meData(ultimaColeta(MZ)), o: n(MZ.observacoes_brutas) });

  meChips(MZ);
  desenhar(MZ);
}
