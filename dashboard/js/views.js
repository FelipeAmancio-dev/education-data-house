/* Views dos blocos Overview, Cursos, Geografia e Glossário.
 * (O bloco Key Players vive em grupos.js e o Price Action em precos.js.)
 *
 * Duas regras editoriais atravessam o arquivo:
 *   - toda tela declara o denominador usado; share sem denominador explícito é fonte
 *     de erro de leitura (docs/03_arquitetura.md §7);
 *   - todo conjunto que aparece na tela é registrado para download em CSV.
 */
import {
  D, carregarAno, carregarEmec, porIES, passaIES, serieIES, totalAno, totalFiltrado,
  unidadesPorIES, kpiAno,
  gr, nomeIES, ufIES, redeIES, nomeCurso, areaCurso, nomeMun, ufMun, regMun,
  n, pct, compacto, deltaHTML,
} from './dados.js';
import { $, esc, kpi, tabela, opcoes, chart, baseChart, fmtEixoMi, registrarCSV,
         PALETA, COR_PRES, COR_EAD, LARANJA } from './ui.js';
import { TX, TXcurso, TXarea, TXregiao, TXorg } from './i18n.js';

const modLabel = f => f.mod === '1' ? TX('presenciais') : f.mod === '2' ? TX('EAD') : TX('totais');
/* Denominador de share: nunca inclui grupo (senao todo grupo teria 100%). */
function denom(f) {
  const p = [];
  if (f.mod) p.push(f.mod === '1' ? TX('presencial') : TX('EAD'));
  if (f.rede) p.push(f.rede === '1' ? TX('rede pública') : TX('rede privada'));
  if (f.uf) p.push(f.uf);
  return p.length ? TX('matrículas {r}', { r: p.join(' · ') }) : TX('matrículas do Brasil');
}
/* Descricao do recorte selecionado. */
function denomSel(f) {
  const p = [];
  if (f.grupo) p.push(D.gruposOrd[f.grupo]?.nome || f.grupo);
  if (f.mod) p.push(f.mod === '1' ? TX('presencial') : TX('EAD'));
  if (f.rede) p.push(f.rede === '1' ? TX('rede pública') : TX('rede privada'));
  if (f.uf) p.push(f.uf);
  return p.length ? p.join(' · ') : TX('Brasil');
}
const nomeGrupo = k => D.gruposOrd[k]?.nome || k;
const corGrupoK = (k, i = 0) => D.gruposOrd[k]?.cor || PALETA[i % PALETA.length];
const ORG = () => D.meta.codigos?.TP_ORGANIZACAO_ACADEMICA || {};
const T_PRES = () => TX('Presencial');
const T_EAD = () => TX('EAD');

/* ========================================================== OVERVIEW =====
 * Sem filtro de grupo por decisao: aqui o interesse e o mercado como um todo,
 * por UF e por curso. A competicao entre players tem bloco proprio.            */
/* async porque, com recorte de UF/rede, os graficos de curso e area dependem do detalhe
 * do ano — que carrega sob demanda. Sem filtro nao ha await de rede: o cubo nacional ja
 * esta em memoria. O roteador ja chamava a view com `await`.                          */
export async function overview(f) {
  const ano = f.ano, prev = ano - 1;
  const k = kpiAno(ano), kp = kpiAno(prev);
  const d = (a, b) => (b && b > 0) ? 100 * (a - b) / b : null;

  const filtroAtivo = f.uf || f.rede || f.mod;
  const sel = totalFiltrado(ano, f), selP = totalFiltrado(prev, f);
  const tot = totalAno(ano, f);

  $('#ov-kpis').innerHTML = filtroAtivo
    ? [kpi({ rot: TX('Matrículas · recorte'), val: compacto(sel),
             sub: `${denomSel(f)} · ${TX('vs {a}', { a: prev })}`, delta: d(sel, selP) }),
       kpi({ rot: TX('Brasil — total'), val: compacto(k.mat_total), sub: TX('todas as modalidades'),
             delta: d(k.mat_total, kp?.mat_total) }),
       kpi({ rot: TX('Participação do recorte'), val: pct(100 * sel / k.mat_total),
             sub: TX('do mercado nacional') }),
       kpi({ rot: TX('IES no país'), val: n(k.ies), sub: TX('instituições ativas'),
             delta: d(k.ies, kp?.ies) })].join('')
    : [kpi({ rot: TX('Matrículas'), val: compacto(k.mat_total), sub: TX('vs {a}', { a: prev }),
             delta: d(k.mat_total, kp?.mat_total) }),
       kpi({ rot: TX('Ingressantes'), val: compacto(k.ingressantes), sub: TX('vs {a}', { a: prev }),
             delta: d(k.ingressantes, kp?.ingressantes) }),
       kpi({ rot: TX('Concluintes'), val: compacto(k.concluintes), sub: TX('vs {a}', { a: prev }),
             delta: d(k.concluintes, kp?.concluintes) }),
       kpi({ rot: TX('Cursos'), val: n(k.cursos), sub: TX('vs {a}', { a: prev }),
             delta: d(k.cursos, kp?.cursos) })].join('');

  $('#ov-kpis2').innerHTML = [
    kpi({ rot: TX('EAD'), val: pct(100 * k.mat_ead / k.mat_total),
          sub: TX('{v} alunos', { v: compacto(k.mat_ead) }),
          delta: kp ? (100 * k.mat_ead / k.mat_total) - (100 * kp.mat_ead / kp.mat_total) : null,
          sufixo: ' p.p.' }),
    kpi({ rot: TX('Presencial'), val: pct(100 * k.mat_presencial / k.mat_total),
          sub: TX('{v} alunos', { v: compacto(k.mat_presencial) }),
          delta: d(k.mat_presencial, kp?.mat_presencial) }),
    kpi({ rot: TX('Rede privada'), val: pct(100 * k.mat_privada / k.mat_total),
          sub: TX('{v} alunos', { v: compacto(k.mat_privada) }),
          delta: kp ? (100 * k.mat_privada / k.mat_total) - (100 * kp.mat_privada / kp.mat_total) : null,
          sufixo: ' p.p.' }),
    kpi({ rot: TX('Municípios com oferta'), val: n(k.munic_presencial),
          sub: TX('com curso presencial') }),
  ].join('');

  // evolucao presencial x EAD — do recorte selecionado, ou nacional se sem filtro
  const anos = D.meta.anos;
  let sPres, sEad, sTot;
  if (f.uf || f.rede) {
    const s = serieIES(() => 'x', f).get('x') || {};
    sPres = anos.map(a => s[a]?.pres ?? 0);
    sEad = anos.map(a => s[a]?.ead ?? 0);
    sTot = anos.map(a => s[a]?.mat ?? 0);
  } else {
    sPres = D.meta.kpi.mat_presencial; sEad = D.meta.kpi.mat_ead; sTot = D.meta.kpi.mat_total;
  }
  const rotuloSerie = filtroAtivo ? denomSel({ ...f, mod: '' }) : TX('Brasil');

  chart($('#ov-evol'), {
    ...baseChart(),
    legend: { ...baseChart().legend, data: [T_PRES(), T_EAD()] },
    xAxis: { ...baseChart().xAxis, data: anos },
    yAxis: { ...baseChart().yAxis, axisLabel: { fontSize: 11.5, color: '#8C8C8C', formatter: fmtEixoMi } },
    series: [
      { name: T_PRES(), type: 'line', smooth: .25, symbol: 'circle', symbolSize: 5,
        data: sPres, itemStyle: { color: COR_PRES }, lineStyle: { width: 2.2 } },
      { name: T_EAD(), type: 'line', smooth: .25, symbol: 'circle', symbolSize: 5,
        data: sEad, itemStyle: { color: COR_EAD }, lineStyle: { width: 2.2 } },
    ],
    tooltip: { ...baseChart().tooltip, valueFormatter: v => n(v) },
  });
  $('#ov-evol-tit').textContent = TX('Matrículas por modalidade — {r}', { r: rotuloSerie });
  registrarCSV('overview', TX('Série por modalidade'),
    [{ k: 'ano', t: TX('Ano') }, { k: 'presencial', t: TX('Presencial') },
     { k: 'ead', t: TX('EAD') }, { k: 'total', t: TX('Total') }, { k: 'pctEad', t: TX('% EAD') }],
    anos.map((a, i) => ({ ano: a, presencial: sPres[i], ead: sEad[i], total: sTot[i],
                          pctEad: sTot[i] ? +(100 * sEad[i] / sTot[i]).toFixed(2) : null })));

  chart($('#ov-ead'), {
    ...baseChart(),
    legend: { show: false },
    xAxis: { ...baseChart().xAxis, data: anos },
    yAxis: { ...baseChart().yAxis, max: 100,
             axisLabel: { fontSize: 11.5, color: '#8C8C8C', formatter: v => v + '%' } },
    series: [{
      type: 'line', smooth: .25, symbol: 'circle', symbolSize: 5, itemStyle: { color: COR_EAD },
      lineStyle: { width: 2.4 }, areaStyle: { color: 'rgba(236,112,0,.12)' },
      data: anos.map((_, i) => sTot[i] ? +(100 * sEad[i] / sTot[i]).toFixed(1) : null),
      markLine: { silent: true, symbol: 'none', label: { formatter: '50%', fontSize: 10, color: '#8C8C8C' },
                  lineStyle: { color: '#D2D4D8', type: 'dashed' }, data: [{ yAxis: 50 }] },
    }],
    tooltip: { ...baseChart().tooltip, valueFormatter: v => v == null ? '—' : v + '%' },
  });
  $('#ov-ead-tit').textContent = TX('Participação do EAD — {r}', { r: rotuloSerie });

  // ------------------------------------------------------------ por UF
  const cm = D.munMod, porUF = new Map();
  for (let i = 0; i < cm.n; i++) {
    if (cm.ano[i] !== ano) continue;
    if (f.mod && cm.mod[i] !== +f.mod) continue;
    const ix = cm.mun[i]; if (ix < 0) continue;
    const uf = ufMun(ix);
    if (f.uf && uf !== f.uf) continue;
    let o = porUF.get(uf);
    if (!o) { o = { pres: 0, ead: 0, mat: 0, regiao: regMun(ix) }; porUF.set(uf, o); }
    o.mat += cm.qt_mat[i];
    if (cm.mod[i] === 1) o.pres += cm.qt_mat[i]; else o.ead += cm.qt_mat[i];
  }
  const ufOrd = [...porUF.entries()].sort((a, b) => b[1].mat - a[1].mat);
  const ufTop = ufOrd.slice(0, 15).reverse();
  chart($('#ov-uf'), {
    ...baseChart(),
    legend: { ...baseChart().legend, data: [T_PRES(), T_EAD()] },
    grid: { left: 8, right: 44, top: 30, bottom: 6, containLabel: true },
    xAxis: { type: 'value', splitLine: { lineStyle: { color: '#F2F3F5' } }, axisLine: { show: false },
             axisTick: { show: false }, axisLabel: { fontSize: 11.5, color: '#8C8C8C', formatter: fmtEixoMi } },
    yAxis: { type: 'category', data: ufTop.map(x => x[0]), axisTick: { show: false },
             axisLine: { show: false }, axisLabel: { fontSize: 11.5, color: '#4A4A4A' } },
    series: [
      { name: T_PRES(), type: 'bar', stack: 'a', barMaxWidth: 15, itemStyle: { color: COR_PRES },
        data: ufTop.map(x => x[1].pres) },
      { name: T_EAD(), type: 'bar', stack: 'a', barMaxWidth: 15, itemStyle: { color: COR_EAD },
        data: ufTop.map(x => x[1].ead),
        label: { show: true, position: 'right', fontSize: 10.5, color: '#8C8C8C',
                 formatter: p => compacto(ufTop[p.dataIndex][1].mat) } },
    ],
    tooltip: { ...baseChart().tooltip, valueFormatter: v => n(v) },
  });
  registrarCSV('overview', TX('Matrículas por UF'),
    [{ k: 'uf', t: 'UF' }, { k: 'regiao', t: TX('Região') }, { k: 'mat', t: TX('Matrículas') },
     { k: 'pres', t: TX('Presencial') }, { k: 'ead', t: TX('EAD') }, { k: 'share', t: TX('Share') }],
    ufOrd.map(([uf, v]) => ({ uf, regiao: TXregiao(v.regiao), mat: v.mat, pres: v.pres, ead: v.ead,
                              share: tot ? +(100 * v.mat / tot).toFixed(2) : null })));

  // --------------------------------------------------------- por curso
  //
  // ⚠️ Estes dois graficos (curso e area) ignoravam o filtro de UF, e por um motivo de
  // dado, nao de esquecimento: `D.cineMod` e um cubo curso × modalidade, SEM geografia —
  // nao ha por onde recortar. O cruzamento so existe no detalhe do ano (`ies × curso`),
  // que se junta a UF pela IES.
  //
  // ⚠️ Isso traz uma definicao DIFERENTE de UF na mesma tela. "Matriculas por UF" usa
  // `c_mun_mod`, a geografia de verdade do Censo (dims 1 e 2). Aqui a UF e a da SEDE da
  // IES, que e a convencao que `passaIES` ja aplica no resto do dashboard. Para o
  // presencial as duas quase coincidem; para o EAD nao coincidem nada — a matricula EAD
  // e registrada na sede, entao a Unopar joga o Brasil inteiro no PR. Por isso as duas
  // notas abaixo, e por isso o titulo passa a dizer o recorte.
  const recorteIES = !!(f.uf || f.rede);
  const det = recorteIES ? await carregarAno(ano) : null;
  const usaDet = !!(det && !det.parcial);

  const cc = D.cineMod, porCur = new Map();
  const soma = (ix, mod, mat) => {
    let o = porCur.get(ix);
    if (!o) { o = { pres: 0, ead: 0, mat: 0 }; porCur.set(ix, o); }
    o.mat += mat;
    if (mod === 1) o.pres += mat; else o.ead += mat;
  };
  if (usaDet) {
    const dc = det.iesCine;
    for (let i = 0; i < dc.n; i++) {
      const ies = dc.ies[i]; if (ies < 0 || !passaIES(ies, f)) continue;
      if (f.mod && dc.mod[i] !== +f.mod) continue;
      const ix = dc.cur[i]; if (ix < 0) continue;
      soma(ix, dc.mod[i], dc.qt_mat[i]);
    }
  } else {
    for (let i = 0; i < cc.n; i++) {
      if (cc.ano[i] !== ano) continue;
      if (f.mod && cc.mod[i] !== +f.mod) continue;
      const ix = cc.cur[i]; if (ix < 0) continue;
      soma(ix, cc.mod[i], cc.qt_mat[i]);
    }
  }
  const curTop = [...porCur.entries()].sort((a, b) => b[1].mat - a[1].mat).slice(0, 15).reverse();
  chart($('#ov-curso'), {
    ...baseChart(),
    legend: { ...baseChart().legend, data: [T_PRES(), T_EAD()] },
    grid: { left: 8, right: 44, top: 30, bottom: 6, containLabel: true },
    xAxis: { type: 'value', splitLine: { lineStyle: { color: '#F2F3F5' } }, axisLine: { show: false },
             axisTick: { show: false }, axisLabel: { fontSize: 11.5, color: '#8C8C8C', formatter: fmtEixoMi } },
    yAxis: { type: 'category', data: curTop.map(x => TXcurso(nomeCurso(x[0]))), axisTick: { show: false },
             axisLine: { show: false },
             axisLabel: { fontSize: 11.5, color: '#4A4A4A', width: 150, overflow: 'truncate' } },
    series: [
      { name: T_PRES(), type: 'bar', stack: 'a', barMaxWidth: 15, itemStyle: { color: COR_PRES },
        data: curTop.map(x => x[1].pres) },
      { name: T_EAD(), type: 'bar', stack: 'a', barMaxWidth: 15, itemStyle: { color: COR_EAD },
        data: curTop.map(x => x[1].ead),
        label: { show: true, position: 'right', fontSize: 10.5, color: '#8C8C8C',
                 formatter: p => compacto(curTop[p.dataIndex][1].mat) } },
    ],
    tooltip: { ...baseChart().tooltip, valueFormatter: v => n(v) },
  });

  // O titulo passa a carregar o recorte, e a nota avisa quando a UF aqui NAO e a mesma
  // UF do grafico ao lado. Duas definicoes de geografia na mesma tela sem dizer qual e
  // qual e exatamente o erro de leitura que este projeto tenta nao induzir.
  const notaRecorte = el => {
    if (!recorteIES) { $(el).textContent = ''; return; }
    $(el).textContent = usaDet
      ? TX('Recorte por sede da instituição, não por onde o aluno está — é a mesma regra ' +
           'usada nas tabelas de grupo. No EAD as duas coisas se separam: a matrícula é ' +
           'registrada na sede, então uma instituição de EAD carrega o país inteiro para o ' +
           'estado dela. "Matrículas por UF", ao lado, usa a geografia do Censo e não esta.')
      : TX('O detalhe de {a} não vem nesta versão do arquivo, então estes dois gráficos ' +
           'continuam nacionais — o recorte não foi aplicado.', { a: ano });
  };
  $('#ov-curso-tit').textContent = recorteIES
    ? TX('Maiores cursos — {r}', { r: denomSel({ ...f, mod: '' }) }) : TX('Maiores cursos');
  notaRecorte('#ov-curso-nota');

  registrarCSV('overview', TX('Maiores cursos'),
    [{ k: 'curso', t: TX('Curso') }, { k: 'mat', t: TX('Matrículas') },
     { k: 'pres', t: TX('Presencial') }, { k: 'ead', t: TX('EAD') }],
    [...porCur.entries()].sort((a, b) => b[1].mat - a[1].mat)
      .map(([ix, v]) => ({ curso: TXcurso(nomeCurso(ix)), mat: v.mat, pres: v.pres, ead: v.ead })));

  // ----------------------------------------------------- maiores grupos
  const g = porIES(ano, gr, f);
  const linhasG = [...g.entries()].filter(([k]) => k && k !== 'Independentes')
    .map(([k, v]) => ({ grupo: nomeGrupo(k), _raw: k, mat: v.mat, share: 100 * v.mat / tot,
                        ead: v.mat ? 100 * v.ead / v.mat : 0 }))
    .sort((a, b) => b.mat - a.mat).slice(0, 10);
  const indep = g.get('Independentes');
  tabela($('#ov-grupos'), [
    { k: 'grupo', t: TX('Grupo'), tipo: 'txt' },
    { k: 'mat', t: TX('Matrículas'), tipo: 'num' },
    { k: 'share', t: TX('Share'), tipo: 'barra' },
    { k: 'ead', t: TX('% EAD'), tipo: 'pct' },
  ], linhasG, { ordem: 'mat', csv: { bloco: 'overview', nome: TX('Maiores grupos') } });
  $('#ov-grupos-nota').textContent = TX(
    'Denominador: {d} em {a} — {t}. Consolidação por grupo econômico em perímetro pro-forma. ' +
    'Fora da tabela, {p} do mercado ({m} matrículas) está em instituições não mapeadas em ' +
    'grupo — bucket residual, não um player.',
    { d: denom(f), a: ano, t: n(tot), p: pct(100 * (indep?.mat || 0) / tot), m: n(indep?.mat || 0) });

  // ------------------------------------------------ mix por area CINE
  // Mesma fonte do grafico de curso — ver o ⚠️ la em cima. Reaproveita `porCur`, que ja
  // esta agregado por curso e ja respeita o recorte: somar area a partir dele garante que
  // os dois graficos nunca discordem sobre o mesmo filtro.
  const area = new Map();
  for (const [ix, v] of porCur) {
    const a = areaCurso(ix); if (!a) continue;
    area.set(a, (area.get(a) || 0) + v.mat);
  }
  const arr = [...area.entries()].sort((a, b) => b[1] - a[1]);
  chart($('#ov-area'), {
    ...baseChart(),
    grid: { left: 8, right: 44, top: 6, bottom: 6, containLabel: true },
    legend: { show: false },
    xAxis: { type: 'value', splitLine: { lineStyle: { color: '#F2F3F5' } }, axisLine: { show: false },
             axisTick: { show: false }, axisLabel: { fontSize: 11.5, color: '#8C8C8C', formatter: fmtEixoMi } },
    yAxis: { type: 'category', data: arr.map(x => TXarea(x[0])).reverse(), axisTick: { show: false },
             axisLine: { show: false },
             axisLabel: { fontSize: 11.5, color: '#4A4A4A', width: 190, overflow: 'truncate' } },
    series: [{ type: 'bar', data: arr.map(x => x[1]).reverse(), barMaxWidth: 15,
               itemStyle: { color: COR_PRES, borderRadius: [0, 2, 2, 0] },
               label: { show: true, position: 'right', fontSize: 11, color: '#8C8C8C',
                        formatter: p => compacto(p.value) } }],
    tooltip: { ...baseChart().tooltip, trigger: 'item', valueFormatter: v => n(v) },
  });
  $('#ov-area-tit').textContent = recorteIES
    ? TX('Mix por área do conhecimento — {r}', { r: denomSel({ ...f, mod: '' }) })
    : TX('Mix por área do conhecimento');
  notaRecorte('#ov-area-nota');

  // ⚠️ o share sai sobre o total DESTE recorte, nao sobre `tot`: com filtro de UF ativo,
  // dividir a area pelo total nacional daria uma coluna que nao soma 100% e nao significa
  // nada. Ja e a mesma pegadinha do §"denominador" que a tela declara em toda parte.
  const totArea = arr.reduce((s, [, v]) => s + v, 0);
  registrarCSV('overview', TX('Mix por área do conhecimento'),
    [{ k: 'area', t: TX('Área') }, { k: 'mat', t: TX('Matrículas') }, { k: 'share', t: TX('Share') }],
    arr.map(([a, v]) => ({ area: TXarea(a), mat: v,
                           share: totArea ? +(100 * v / totArea).toFixed(1) : null })));
  registrarCSV('overview', TX('KPIs nacionais por ano'),
    [{ k: 'ano', t: TX('Ano') }, { k: 'mat_total', t: TX('Matrículas') },
     { k: 'mat_presencial', t: TX('Presencial') }, { k: 'mat_ead', t: TX('EAD') },
     { k: 'mat_publica', t: TX('Rede pública') }, { k: 'mat_privada', t: TX('Rede privada') },
     { k: 'ingressantes', t: TX('Ingressantes') }, { k: 'concluintes', t: TX('Concluintes') },
     { k: 'trancados', t: TX('Trancados') }, { k: 'cursos', t: TX('Cursos') },
     { k: 'vagas', t: TX('Vagas') }, { k: 'ies', t: TX('IES') }],
    anos.map((a, i) => Object.fromEntries(Object.keys(D.meta.kpi).map(c => [c, D.meta.kpi[c][i]]))));
}

/* =========================================================== CURSOS ====== */

/* Seleção de grupos do bloco Cursos. Vive fora da view porque precisa sobreviver ao
 * re-render: `courses()` roda de novo a cada clique de chip, troca de curso ou filtro.
 * `null` = ainda não inicializada; na primeira montagem vira o conjunto das abertas, que
 * é o padrão pedido — quem não mexer em nada vê o que via antes.                      */
let selCursos = null;

function chipsCursos(el, aoTrocar) {
  const listadas = D.gruposLista.filter(k => D.gruposOrd[k]?.tipo === 'listada');
  const outros = D.gruposLista.filter(k => k !== 'Independentes' &&
                                           D.gruposOrd[k]?.tipo !== 'listada');
  if (selCursos === null) selCursos = new Set(listadas);

  const chip = k => {
    const info = D.gruposOrd[k] || {};
    const c = info.cor || PALETA[D.gruposLista.indexOf(k) % PALETA.length];
    return `<button class="chip ${selCursos.has(k) ? 'on' : ''}" data-g="${esc(k)}">
      <span class="pt" style="background:${c}"></span>${esc(info.nome || k)}
      ${info.ticker ? `<span class="tk">${esc(info.ticker)}</span>` : ''}</button>`;
  };
  el.innerHTML =
    `<div style="margin-bottom:14px">
       <div class="eyebrow">${TX('Listadas em bolsa')}</div>
       <div class="chips">${listadas.map(chip).join('')}</div>
     </div>
     <div>
       <div class="eyebrow">${TX('Outros grupos relevantes')}</div>
       <div class="chips">${outros.slice(0, 12).map(chip).join('')}</div>
     </div>`;
  el.querySelectorAll('.chip').forEach(b => b.onclick = () => {
    const g = b.dataset.g;
    // nunca deixa zerar: um gráfico sem nenhum grupo não responde pergunta nenhuma
    if (selCursos.has(g)) { if (selCursos.size > 1) selCursos.delete(g); }
    else selCursos.add(g);
    aoTrocar();
  });
}

export async function courses(f) {
  const ano = f.ano;
  const c = D.cineMod;
  const agg = new Map();
  for (let i = 0; i < c.n; i++) {
    if (c.ano[i] !== ano) continue;
    if (f.mod && c.mod[i] !== +f.mod) continue;
    const ix = c.cur[i]; if (ix < 0) continue;
    let o = agg.get(ix);
    if (!o) { o = { mat: 0, ing: 0, pres: 0, ead: 0, cursos: 0 }; agg.set(ix, o); }
    o.mat += c.qt_mat[i]; o.ing += c.qt_ing[i]; o.cursos += c.qt_curso[i];
    if (c.mod[i] === 1) o.pres += c.qt_mat[i]; else o.ead += c.qt_mat[i];
  }
  const totCursos = [...agg.values()].reduce((s, v) => s + v.mat, 0);

  const aggP = new Map();
  for (let i = 0; i < c.n; i++) {
    if (c.ano[i] !== ano - 1) continue;
    if (f.mod && c.mod[i] !== +f.mod) continue;
    const ix = c.cur[i]; if (ix < 0) continue;
    aggP.set(ix, (aggP.get(ix) || 0) + c.qt_mat[i]);
  }

  // O detalhe sobe para cá porque a tabela de mercado agora precisa dele: a coluna do
  // maior grupo só existe cruzando curso × IES × grupo, que é o `iesCine` do ano.
  const det = await carregarAno(ano);

  /* Maior grupo em matrículas dentro de cada curso.
   * ⚠️ "Independentes" fica FORA: é bucket residual de IES não mapeadas, não um player —
   * a mesma regra do Top N e do HHI no resto do dashboard. Sem isso a coluna diria
   * "Independentes" na maioria das linhas e não informaria nada sobre competição. */
  const liderCurso = new Map();
  {
    const porCursoGrupo = new Map();
    const ic0 = det.iesCine;
    for (let i = 0; i < ic0.n; i++) {
      if (f.mod && ic0.mod[i] !== +f.mod) continue;
      const ix = ic0.ies[i]; if (ix < 0 || !passaIES(ix, f)) continue;
      const cur = ic0.cur[i]; if (cur < 0) continue;
      const k = gr(ix); if (!k || k === 'Independentes') continue;
      let m = porCursoGrupo.get(cur);
      if (!m) { m = new Map(); porCursoGrupo.set(cur, m); }
      m.set(k, (m.get(k) || 0) + ic0.qt_mat[i]);
    }
    for (const [cur, m] of porCursoGrupo) {
      let melhor = null;
      for (const [k, v] of m) if (!melhor || v > melhor[1]) melhor = [k, v];
      if (melhor) liderCurso.set(cur, { grupo: melhor[0], mat: melhor[1] });
    }
  }

  const rows = [...agg.entries()].map(([ix, v]) => {
    const ld = liderCurso.get(ix);
    return {
      curso: TXcurso(nomeCurso(ix)), area: TXarea(areaCurso(ix)), _ix: ix,
      mat: v.mat, pres: v.pres, ead: v.ead,
      pctEad: v.mat ? 100 * v.ead / v.mat : 0,
      cursos: v.cursos, share: 100 * v.mat / totCursos,
      cresc: aggP.get(ix) ? 100 * (v.mat - aggP.get(ix)) / aggP.get(ix) : null,
      lider: ld ? nomeGrupo(ld.grupo) : '—',
      liderMat: ld ? ld.mat : null,
      liderShare: ld && v.mat ? 100 * ld.mat / v.mat : null,
    };
  }).sort((a, b) => b.mat - a.mat);

  tabela($('#cu-tab'), [
    { k: 'curso', t: TX('Curso (rótulo CINE)'), tipo: 'txt' },
    { k: 'area', t: TX('Área'), tipo: 'txt', fmt: v => `<span class="tag">${esc(v)}</span>` },
    { k: 'mat', t: TX('Matrículas'), tipo: 'num' },
    { k: 'pres', t: TX('Presencial'), tipo: 'num' },
    { k: 'ead', t: TX('EAD'), tipo: 'num' },
    { k: 'pctEad', t: TX('% EAD'), tipo: 'pct' },
    // o share do líder vem junto do nome: "Cogna" sem o tamanho da fatia nao diz se ele
    // domina o curso ou se apenas ganhou por pouco num mercado pulverizado
    { k: 'lider', t: TX('Maior grupo'), tipo: 'txt', fmt: (v, r) => esc(v) +
        (r.liderShare == null ? '' :
          ` <span class="tag">${r.liderShare.toFixed(1)}%</span>`) },
    { k: 'cursos', t: TX('Nº cursos'), tipo: 'num' },
    { k: 'share', t: TX('Share'), tipo: 'barra' },
    { k: 'cresc', t: 'YoY', tipo: 'num', fmt: v => deltaHTML(v) },
  ], rows, { ordem: 'mat', limite: 40,
    csv: { bloco: 'cursos', nome: TX('Todos os cursos'),
           cols: [{ k: 'curso', t: TX('Curso (rótulo CINE)') }, { k: 'area', t: TX('Área') },
                  { k: 'mat', t: TX('Matrículas') }, { k: 'pres', t: TX('Presencial') },
                  { k: 'ead', t: TX('EAD') }, { k: 'pctEad', t: TX('% EAD') },
                  { k: 'lider', t: TX('Maior grupo') },
                  { k: 'liderMat', t: TX('Matrículas do maior grupo') },
                  { k: 'liderShare', t: TX('Share do maior grupo no curso') },
                  { k: 'cursos', t: TX('Nº cursos') }, { k: 'share', t: TX('Share') },
                  { k: 'cresc', t: 'YoY' }] } });
  $('#cu-nota').textContent = TX(
    '40 maiores de {q} rótulos CINE — o CSV traz todos. Denominador: {t} matrículas {m} em {a}. ' +
    'Usa o rótulo CINE padronizado, não o nome livre dado pela IES (1.497 nomes livres para 381 ' +
    'rótulos). <Maior grupo> é o grupo econômico com mais matrículas naquele curso, com a fatia ' +
    'dele entre parênteses; instituições não mapeadas em grupo ficam fora dessa disputa.',
    { q: rows.length, t: n(totCursos), m: modLabel(f), a: ano });

  // ------------------------------------------- concorrencia no curso escolhido
  const alvo = +opcoes($('#cu-curso'), rows.slice(0, 80).map(r => ({ v: r._ix, t: r.curso })),
                       () => courses(window.__filtros)) || rows[0]?._ix;
  const nomeAlvo = TXcurso(nomeCurso(alvo));
  chipsCursos($('#cu-chips'), () => courses(window.__filtros));
  $('#cu-parcial').innerHTML = det.parcial
    ? `<div class="aviso">${TX('O detalhe por IES de {a} não está incluído nesta versão de ' +
       'arquivo único — só o ano mais recente vem embutido. Rode <code>python ' +
       'run_dashboard.py</code> para navegar a série completa.', { a: ano })}</div>` : '';

  const ic = det.iesCine, porGrupo = new Map(), porIes = new Map();
  let totCurso = 0;
  for (let i = 0; i < ic.n; i++) {
    if (ic.cur[i] !== alvo) continue;
    if (f.mod && ic.mod[i] !== +f.mod) continue;
    const ix = ic.ies[i];
    if (ix < 0) continue;
    if (f.uf && ufIES(ix) !== f.uf) continue;
    if (f.rede && redeIES(ix) !== +f.rede) continue;
    const v = ic.qt_mat[i];
    totCurso += v;
    const k = gr(ix);
    let o = porGrupo.get(k);
    if (!o) { o = { mat: 0, pres: 0, ead: 0 }; porGrupo.set(k, o); }
    o.mat += v; if (ic.mod[i] === 1) o.pres += v; else o.ead += v;
    porIes.set(ix, (porIes.get(ix) || 0) + v);
  }

  const rgTodos = [...porGrupo.entries()].map(([k, v]) => ({
    grupo: k === 'Independentes' ? TX('Independentes / não mapeado') : nomeGrupo(k), _raw: k,
    mat: v.mat, pres: v.pres, ead: v.ead, share: totCurso ? 100 * v.mat / totCurso : 0,
  })).sort((a, b) => b.mat - a.mat);

  // ------------------------ alunos por grupo SELECIONADO neste curso
  // ⚠️ MUDOU: era fixo nas 7 companhias abertas. Hoje segue os chips, que já começam
  // marcados nas abertas — o padrão é o comportamento antigo.
  const ab = D.gruposLista.filter(k => selCursos.has(k))
    .map(k => ({ k, ...(porGrupo.get(k) || { mat: 0, pres: 0, ead: 0 }) }))
    .sort((a, b) => b.mat - a.mat);
  $('#cu-cias-tit').textContent = TX('Alunos por grupo — {c}', { c: nomeAlvo });
  chart($('#cu-cias'), {
    ...baseChart(),
    legend: { ...baseChart().legend, data: [T_PRES(), T_EAD()] },
    grid: { left: 8, right: 30, top: 30, bottom: 6, containLabel: true },
    xAxis: { ...baseChart().xAxis, data: ab.map(r => nomeGrupo(r.k)),
             axisLabel: { fontSize: 11, color: '#8C8C8C', rotate: 22, interval: 0 } },
    yAxis: { ...baseChart().yAxis, axisLabel: { fontSize: 11.5, color: '#8C8C8C', formatter: fmtEixoMi } },
    series: [
      { name: T_PRES(), type: 'bar', stack: 'a', barMaxWidth: 46, itemStyle: { color: COR_PRES },
        data: ab.map(r => r.pres) },
      { name: T_EAD(), type: 'bar', stack: 'a', barMaxWidth: 46, itemStyle: { color: COR_EAD },
        data: ab.map(r => r.ead),
        label: { show: true, position: 'top', fontSize: 11, color: '#4A4A4A', fontWeight: 600,
                 formatter: p => compacto(ab[p.dataIndex].mat) } },
    ],
    tooltip: {
      ...baseChart().tooltip,
      formatter: ps => {
        const r = ab[ps[0].dataIndex];
        return `<strong>${esc(nomeGrupo(r.k))}</strong><br>` +
               ps.map(x => `${x.marker} ${x.seriesName}: ${n(x.value)}`).join('<br>') +
               `<br>${TX('Total')}: <strong>${n(r.mat)}</strong> · ` +
               `${pct(totCurso ? 100 * r.mat / totCurso : 0)} ${TX('do curso')}`;
      },
    },
  });
  const somaAb = ab.reduce((s, r) => s + r.mat, 0);
  $('#cu-cias-nota').textContent = TX(
    'Alunos dos {q} grupos selecionados em {c} ({m}, {a}). Somados, eles têm {s} alunos no ' +
    'curso — {p} das {t} matrículas. Grupo com barra zerada não oferta o curso no recorte.',
    { q: ab.length, c: nomeAlvo, m: modLabel(f), a: ano, s: n(somaAb),
      p: pct(totCurso ? 100 * somaAb / totCurso : 0), t: n(totCurso) });
  registrarCSV('cursos', TX('Alunos por grupo no curso selecionado'),
    [{ k: 'grupo', t: TX('Grupo') }, { k: 'curso', t: TX('Curso') },
     { k: 'pres', t: TX('Presencial') }, { k: 'ead', t: TX('EAD') },
     { k: 'mat', t: TX('Matrículas') }, { k: 'share', t: TX('Share no curso') }],
    ab.map(r => ({ grupo: nomeGrupo(r.k), curso: nomeAlvo, pres: r.pres, ead: r.ead, mat: r.mat,
                   share: totCurso ? +(100 * r.mat / totCurso).toFixed(2) : null })));

  /* ------------------------------------ pizza: market share dentro do curso ---
   * ⚠️ O denominador aqui é o CURSO INTEIRO, não a soma dos selecionados — senão sete
   * companhias que juntas têm 30% do curso apareceriam ocupando 100% da pizza, que é
   * exatamente a leitura errada que uma pizza induz. Por isso entra a fatia "demais
   * players", que é o que sobra para todo mundo que não está nos chips (inclusive as IES
   * sem grupo mapeado). Sem ela, a pizza mentiria sobre concentração.                  */
  const fatias = ab.filter(r => r.mat > 0)
    .map((r, i) => ({ name: nomeGrupo(r.k), value: r.mat,
                      itemStyle: { color: corGrupoK(r.k, i) } }));
  const resto = Math.max(0, totCurso - somaAb);
  if (resto > 0) fatias.push({ name: TX('Demais players do curso'), value: resto,
                               itemStyle: { color: '#D2D4D8' } });

  $('#cu-pizza-tit').textContent = TX('Market share em {c}', { c: nomeAlvo });
  chart($('#cu-pizza'), {
    ...baseChart(),
    // 'plain' e nao 'scroll': a legenda quebra em linhas e mostra todos os nomes de uma
    // vez, sem a setinha de paginacao — mesma correcao feita nos graficos de Key Players
    legend: { type: 'plain', orient: 'horizontal', bottom: 0, left: 0, width: '100%',
              itemWidth: 10, itemHeight: 10, itemGap: 14, icon: 'roundRect',
              textStyle: { fontSize: 11.5, color: '#4A4A4A' } },
    tooltip: {
      ...baseChart().tooltip, trigger: 'item',
      formatter: p => `<strong>${esc(p.name)}</strong><br>${n(p.value)} ${TX('matrículas')}` +
                      `<br>${p.percent.toFixed(1)}% ${TX('do curso')}`,
    },
    series: [{
      // centro subido e raio menor para abrir espaco a legenda de varias linhas embaixo
      type: 'pie', radius: ['36%', '58%'], center: ['50%', '38%'],
      avoidLabelOverlap: true, data: fatias,
      itemStyle: { borderColor: '#fff', borderWidth: 2 },
      label: { show: true, fontSize: 11, color: '#4A4A4A',
               formatter: p => `${p.name}\n${p.percent.toFixed(1)}%` },
      labelLine: { length: 8, length2: 8 },
    }],
  });
  $('#cu-pizza-nota').textContent = TX(
    'Denominador: as {t} matrículas de {c} ({m}, {a}) — o curso inteiro, não a soma dos ' +
    'selecionados. "Demais players do curso" reúne todo o resto, inclusive as instituições ' +
    'não mapeadas em grupo econômico; é o que impede a pizza de sugerir uma concentração ' +
    'que não existe.',
    { t: n(totCurso), c: nomeAlvo, m: modLabel(f), a: ano });

  tabela($('#cu-grupos'), [
    { k: 'grupo', t: TX('Grupo'), tipo: 'txt' },
    { k: 'mat', t: TX('Matrículas'), tipo: 'num' },
    { k: 'share', t: TX('Share no curso'), tipo: 'barra' },
  ], rgTodos, { ordem: 'mat', limite: 12,
    csv: { bloco: 'cursos', nome: TX('Grupos no curso selecionado'),
           cols: [{ k: 'grupo', t: TX('Grupo') }, { k: 'mat', t: TX('Matrículas') },
                  { k: 'pres', t: TX('Presencial') }, { k: 'ead', t: TX('EAD') },
                  { k: 'share', t: TX('Share no curso') }] } });

  const ri = [...porIes.entries()].map(([ix, v]) => ({
    ies: nomeIES(ix), co: D.dim.ies.co[ix], grupo: nomeGrupo(gr(ix)), uf: ufIES(ix),
    mat: v, share: totCurso ? 100 * v / totCurso : 0,
  })).sort((a, b) => b.mat - a.mat);
  tabela($('#cu-ies'), [
    { k: 'ies', t: 'IES', tipo: 'txt' },
    { k: 'grupo', t: TX('Grupo'), tipo: 'txt' },
    { k: 'uf', t: 'UF', tipo: 'txt' },
    { k: 'mat', t: TX('Matrículas'), tipo: 'num' },
    { k: 'share', t: TX('Share'), tipo: 'barra' },
  ], ri, { ordem: 'mat', limite: 12,
    csv: { bloco: 'cursos', nome: TX('IES no curso selecionado'),
           cols: [{ k: 'co', t: 'CO_IES' }, { k: 'ies', t: 'IES' }, { k: 'grupo', t: TX('Grupo') },
                  { k: 'uf', t: 'UF' }, { k: 'mat', t: TX('Matrículas') },
                  { k: 'share', t: TX('Share no curso') }] } });
}

/* ========================================================= GEOGRAFIA =====
 * A pergunta que organiza o bloco: quem e mais forte em cada praca, em numero de
 * alunos. Usa o detalhe IES x municipio, que atribui o aluno ao municipio de OFERTA
 * — e nao a UF da sede da instituicao.                                            */
const SG_UF = { 11: 'RO', 12: 'AC', 13: 'AM', 14: 'RR', 15: 'PA', 16: 'AP', 17: 'TO', 21: 'MA',
  22: 'PI', 23: 'CE', 24: 'RN', 25: 'PB', 26: 'PE', 27: 'AL', 28: 'SE', 29: 'BA', 31: 'MG',
  32: 'ES', 33: 'RJ', 35: 'SP', 41: 'PR', 42: 'SC', 43: 'RS', 50: 'MS', 51: 'MT', 52: 'GO', 53: 'DF' };

/* Seleção de grupos da Geografia. Fora da view porque sobrevive ao re-render, igual à
 * do bloco Cursos. `null` = ainda não montada; vira o conjunto das abertas na primeira vez. */
let selGeo = null;

function chipsGeo(el, aoTrocar) {
  const listadas = D.gruposLista.filter(k => D.gruposOrd[k]?.tipo === 'listada');
  const outros = D.gruposLista.filter(k => k !== 'Independentes' &&
                                           D.gruposOrd[k]?.tipo !== 'listada');
  if (selGeo === null) selGeo = new Set(listadas);
  const chip = k => {
    const info = D.gruposOrd[k] || {};
    return `<button class="chip ${selGeo.has(k) ? 'on' : ''}" data-g="${esc(k)}">
      <span class="pt" style="background:${corGrupoK(k, D.gruposLista.indexOf(k))}"></span>
      ${esc(info.nome || k)}
      ${info.ticker ? `<span class="tk">${esc(info.ticker)}</span>` : ''}</button>`;
  };
  el.innerHTML =
    `<div style="margin-bottom:14px">
       <div class="eyebrow">${TX('Listadas em bolsa')}</div>
       <div class="chips">${listadas.map(chip).join('')}</div>
     </div>
     <div>
       <div class="eyebrow">${TX('Outros grupos relevantes')}</div>
       <div class="chips">${outros.slice(0, 12).map(chip).join('')}</div>
     </div>`;
  el.querySelectorAll('.chip').forEach(b => b.onclick = () => {
    const g = b.dataset.g;
    if (selGeo.has(g)) { if (selGeo.size > 1) selGeo.delete(g); }
    else selGeo.add(g);
    aoTrocar();
  });
}

/* Mapa de bolhas sobre a malha do Brasil.
 *
 * ⚠️ O ponto é o CENTROIDE DO MUNICÍPIO, não o endereço de ninguém. `dim.mun` traz
 * lat/lon de 3.741 dos 3.742 municípios (do `00_fetch_geo.py`, centroides do IBGE), e o
 * cubo `ies_mun` diz onde há aluno. É por isso que este mapa mostra capilaridade de
 * verdade: o endereço de sede do e-MEC daria UM ponto por instituição, e a Cogna
 * inteira viraria um pin em Valinhos.
 *
 * `series` = [{nome, cor, pontos:[[lon,lat,valor,rotulo], ...]}]. */
function mapaBolhas(el, series, opt = {}) {
  const todos = series.flatMap(s => s.pontos.map(p => p[2]));
  // `opt.max` permite fixar a escala POR FORA, que é o que torna os pequenos múltiplos
  // comparáveis: sem isso cada painel se auto-normalizaria e bolhas do mesmo tamanho
  // significariam números diferentes em mapas vizinhos.
  const maxV = opt.max || (todos.length ? Math.max(...todos) : 1);
  const rMax = opt.mini ? 14 : 30;
  // raiz quadrada: a área da bolha fica proporcional ao valor. Escala linear faria São
  // Paulo cobrir meio mapa e apagar todo o interior, que é justamente o que interessa aqui.
  const raio = v => Math.max(opt.mini ? 1.5 : 3, Math.min(rMax, rMax * Math.sqrt(v / maxV)));
  chart(el, {
    textStyle: { fontFamily: '-apple-system, "Segoe UI", Roboto, sans-serif' },
    legend: series.length > 1 && !opt.mini
      ? { type: 'plain', top: 0, left: 0, width: '100%', itemWidth: 10, itemHeight: 10,
          itemGap: 14, icon: 'circle', data: series.map(s => s.nome),
          textStyle: { fontSize: 11.5, color: '#4A4A4A' } }
      : { show: false },
    tooltip: {
      trigger: 'item', backgroundColor: '#fff', borderColor: '#D2D4D8', borderWidth: 1,
      padding: [9, 12], textStyle: { color: '#1A1A1A', fontSize: 12.5 },
      extraCssText: 'box-shadow:0 4px 14px rgba(0,0,0,.10);border-radius:8px',
      formatter: p => `<strong>${esc(p.data[3])}</strong><br>` +
                      `${esc(p.seriesName)}<br>${n(p.data[2])} ${TX('alunos')}`,
    },
    geo: {
      map: 'BR', roam: false,
      top: (series.length > 1 && !opt.mini) ? 34 : 6, bottom: 6,
      itemStyle: { areaColor: '#F2F3F5', borderColor: '#fff', borderWidth: .8 },
      emphasis: { itemStyle: { areaColor: '#E8E8E8' }, label: { show: false } },
      select: { disabled: true },
    },
    series: series.map(s => ({
      name: s.nome, type: 'scatter', coordinateSystem: 'geo',
      data: s.pontos, symbolSize: d => raio(d[2]),
      itemStyle: { color: s.cor, opacity: opt.opacidade ?? .62,
                   borderColor: '#fff', borderWidth: .5 },
      emphasis: { itemStyle: { opacity: 1 } },
    })),
  });
}

/* Qualidade e situação regulatória, do e-MEC. É o único pedaço da tela que NÃO vem do
 * Censo — daí o carregamento à parte e o aviso quando o arquivo não existe nesta cópia.
 *
 * ⚠️ IGC vazio é SEM NOTA, não nota zero. Média com zero embutido puniria quem ainda não
 * foi avaliado, que é caso comum em IES nova. Por isso o denominador é sempre "IES com
 * nota", e o número de avaliadas viaja junto na tabela. */
async function secaoEmec(f, selG) {
  const E = await carregarEmec();
  const av = $('#ge-emec-aviso');
  if (!E) {
    av.innerHTML = `<div class="aviso">${TX(
      'Os dados do e-MEC não estão nesta cópia. Rode ' +
      '<code>python scripts/10_ingest_emec.py</code> para gerar <code>data/emec.json</code> ' +
      'a partir de <code>Dados_GEO.xlsx</code>.')}</div>`;
    ['#ge-igc', '#ge-sinal'].forEach(s => { $(s).innerHTML = ''; });
    ['#ge-igc-nota', '#ge-sinal-nota'].forEach(s => { $(s).textContent = ''; });
    return;
  }
  av.innerHTML = '';

  // agrega por grupo, contando só quem tem nota
  const porG = new Map();
  const nIES = D.dim.ies.co.length;
  for (let ix = 0; ix < nIES; ix++) {
    const k = gr(ix);
    if (!k || k === 'Independentes') continue;
    if (f.rede && redeIES(ix) !== +f.rede) continue;
    let o = porG.get(k);
    if (!o) { o = { soma: 0, comNota: 0, total: 0, sinal: [] }; porG.set(k, o); }
    o.total++;
    const igc = E.igc[ix];
    if (igc && /^[1-5]$/.test(igc)) { o.soma += +igc; o.comNota++; }
    if (E.sinal[ix]) o.sinal.push(ix);
  }

  const linhasIGC = [...porG.entries()]
    .filter(([k, o]) => o.comNota > 0 && (!selG.length || selG.includes(k)))
    .map(([k, o]) => ({ grupo: nomeGrupo(k), _raw: k, igc: o.soma / o.comNota,
                        comNota: o.comNota, total: o.total }))
    .sort((a, b) => b.igc - a.igc);

  chart($('#ge-igc'), {
    ...baseChart(),
    legend: { show: false },
    grid: { left: 8, right: 46, top: 10, bottom: 6, containLabel: true },
    xAxis: { type: 'value', min: 0, max: 5, splitLine: { lineStyle: { color: '#F2F3F5' } },
             axisLine: { show: false }, axisTick: { show: false },
             axisLabel: { fontSize: 11.5, color: '#8C8C8C' } },
    yAxis: { type: 'category', data: linhasIGC.map(r => r.grupo), inverse: true,
             axisLine: { show: false }, axisTick: { show: false },
             axisLabel: { fontSize: 11.5, color: '#4A4A4A' } },
    series: [{
      type: 'bar', barMaxWidth: 22,
      data: linhasIGC.map(r => ({ value: +r.igc.toFixed(2),
                                  itemStyle: { color: corGrupoK(r._raw) } })),
      label: { show: true, position: 'right', fontSize: 11.5, color: '#4A4A4A',
               formatter: p => p.value.toFixed(2) },
    }],
    tooltip: { ...baseChart().tooltip, trigger: 'item',
               formatter: p => `<strong>${esc(linhasIGC[p.dataIndex].grupo)}</strong><br>` +
                 `IGC ${p.value.toFixed(2)}<br>${linhasIGC[p.dataIndex].comNota} ` +
                 `${TX('de')} ${linhasIGC[p.dataIndex].total} ${TX('IES com nota')}` },
  });
  registrarCSV('geografia', TX('IGC por grupo'),
    [{ k: 'grupo', t: TX('Grupo') }, { k: 'igc', t: 'IGC' },
     { k: 'comNota', t: TX('IES com nota') }, { k: 'total', t: TX('IES no grupo') }],
    linhasIGC.map(r => ({ ...r, igc: +r.igc.toFixed(2) })));

  $('#ge-igc-nota').textContent = TX(
    'IGC do e-MEC, de 1 a 5, processado em {d}. A média é só entre as IES COM nota — IES sem ' +
    'avaliação publicada não entra como zero, que seria lê-la como péssima. A coluna do ' +
    'tooltip mostra quantas das IES do grupo têm nota. Base casada: {c} IES, cobrindo 99,9% ' +
    'das matrículas de 2024.',
    { d: E.processado_em ? E.processado_em.split('-').reverse().join('/') : '—',
      c: n(E.casaram) });

  /* Sinalizações: só as RESTRITIVAS entram na tabela. "Unificação de Mantidas" e
   * "Credenciamento Prévio" são as duas mais numerosas e não são restrição — listá-las
   * junto de suspensão de FIES faria o quadro parecer muito pior do que é. */
  const RESTRITIVA = /suspens|descredenciamento|sancionador|cautelar|vedaç|sub judice|saneador/i;
  const rowsSinal = [];
  for (let ix = 0; ix < nIES; ix++) {
    const s = E.sinal[ix];
    if (!s || !RESTRITIVA.test(s)) continue;
    if (f.rede && redeIES(ix) !== +f.rede) continue;
    const k = gr(ix);
    rowsSinal.push({
      ies: nomeIES(ix), co: D.dim.ies.co[ix], uf: ufIES(ix) || '—',
      grupo: k ? nomeGrupo(k) : TX('Independentes / não mapeado'),
      sinal: s, _aberta: D.gruposOrd[k]?.tipo === 'listada',
    });
  }
  // grupo mapeado primeiro: é o que o investidor procura numa lista de 200 linhas
  rowsSinal.sort((a, b) => (b._aberta - a._aberta) || a.grupo.localeCompare(b.grupo));

  tabela($('#ge-sinal'), [
    { k: 'ies', t: 'IES', tipo: 'txt' },
    { k: 'grupo', t: TX('Grupo'), tipo: 'txt' },
    { k: 'uf', t: 'UF', tipo: 'txt' },
    { k: 'sinal', t: TX('Sinalização'), tipo: 'txt',
      fmt: v => `<span class="tag al">${esc(v)}</span>` },
  ], rowsSinal, { limite: 15,
    csv: { bloco: 'geografia', nome: TX('IES com sinalização no e-MEC'),
           cols: [{ k: 'co', t: 'CO_IES' }, { k: 'ies', t: 'IES' },
                  { k: 'grupo', t: TX('Grupo') }, { k: 'uf', t: 'UF' },
                  { k: 'sinal', t: TX('Sinalização') }] } });

  const emGrupo = rowsSinal.filter(r => !r.grupo.startsWith('Independentes')).length;
  $('#ge-sinal-nota').textContent = TX(
    '{t} IES com restrição vigente, das quais {g} pertencem a algum grupo mapeado — as 15 ' +
    'primeiras na tela, todas no Excel. Ficam de fora as sinalizações que não são restrição, ' +
    'como "Unificação de Mantidas" e "Credenciamento Prévio", que são as duas mais numerosas ' +
    'e listá-las aqui faria o quadro parecer pior do que é.',
    { t: n(rowsSinal.length), g: n(emGrupo) });
}

export async function geography(f) {
  const ano = f.ano;
  const det = await carregarAno(ano);
  $('#ge-parcial').innerHTML = det.parcial
    ? `<div class="aviso">${TX('A liderança por praça exige o detalhe por IES × município de ' +
       '{a}, não incluído nesta versão de arquivo único — só o ano mais recente vem embutido. ' +
       'Rode <code>python run_dashboard.py</code> para a série completa.', { a: ano })}</div>` : '';

  // ---------------------------------------------- agregacao por praca x grupo
  const im = det.iesMun;
  const uf = new Map();     // sigla -> {mat,pres,ead,regiao, g:Map(grupo->mat)}
  const mun = new Map();    // ixMun -> {mat,pres,ead, g:Map(grupo->mat)}
  let tot = 0;
  for (let i = 0; i < im.n; i++) {
    const ix = im.ies[i], mx = im.mun[i];
    if (ix < 0 || mx < 0) continue;
    if (f.mod && im.mod[i] !== +f.mod) continue;
    if (f.rede && redeIES(ix) !== +f.rede) continue;
    const v = im.qt_mat[i], k = gr(ix), sg = ufMun(mx);
    tot += v;
    let a = uf.get(sg);
    if (!a) { a = { mat: 0, pres: 0, ead: 0, regiao: regMun(mx), g: new Map() }; uf.set(sg, a); }
    a.mat += v; if (im.mod[i] === 1) a.pres += v; else a.ead += v;
    a.g.set(k, (a.g.get(k) || 0) + v);
    let m = mun.get(mx);
    if (!m) { m = { mat: 0, pres: 0, ead: 0, g: new Map() }; mun.set(mx, m); }
    m.mat += v; if (im.mod[i] === 1) m.pres += v; else m.ead += v;
    m.g.set(k, (m.g.get(k) || 0) + v);
  }

  /* Grupo → município → {pres, ead, mat}. É a estrutura que os mapas de bolha pedem, e
   * não dá para derivar de `mun` acima: lá o `g` guarda só o total por grupo, sem separar
   * modalidade, que é justamente o corte da seção "pegada física × digital".
   *
   * ⚠️ Este laço IGNORA `f.mod` de propósito. A comparação presencial × EAD deixaria de
   * existir se o filtro global de modalidade a zerasse — com "EAD" selecionado, o mapa do
   * presencial ficaria vazio e pareceria que o grupo não tem campus. O filtro de rede
   * continua valendo. A tela diz isso na nota. */
  const porGrupoMun = new Map();
  for (let i = 0; i < im.n; i++) {
    const ix = im.ies[i], mx = im.mun[i];
    if (ix < 0 || mx < 0) continue;
    if (f.rede && redeIES(ix) !== +f.rede) continue;
    const k = gr(ix);
    if (!k) continue;
    let g = porGrupoMun.get(k);
    if (!g) { g = new Map(); porGrupoMun.set(k, g); }
    let o = g.get(mx);
    if (!o) { o = { pres: 0, ead: 0, mat: 0 }; g.set(mx, o); }
    const v2 = im.qt_mat[i];
    o.mat += v2;
    if (im.mod[i] === 1) o.pres += v2; else o.ead += v2;
  }

  /* "Independentes" e bucket residual, nao player: fica de fora da disputa de
   * lideranca, mas o quanto ele representa aparece em coluna propria. */
  const ranking = mapaG => [...mapaG.entries()]
    .filter(([k]) => k && k !== 'Independentes').sort((a, b) => b[1] - a[1]);
  function lider(o) {
    const r = ranking(o.g);
    return {
      lider: r[0]?.[0] || null, matLider: r[0]?.[1] || 0,
      vice: r[1]?.[0] || null, matVice: r[1]?.[1] || 0,
      indep: o.g.get('Independentes') || 0, players: r.length,
    };
  }

  const nacional = new Map();
  uf.forEach(a => a.g.forEach((v, k) => nacional.set(k, (nacional.get(k) || 0) + v)));
  const liderNac = ranking(nacional)[0];

  $('#ge-kpis').innerHTML = [
    kpi({ rot: TX('Matrículas com geografia'), val: compacto(tot), sub: `${modLabel(f)} · ${ano}` }),
    kpi({ rot: TX('Municípios com oferta'), val: n(mun.size), sub: TX('de 5.570 no país') }),
    kpi({ rot: TX('Líder nacional'), val: liderNac ? nomeGrupo(liderNac[0]) : '—',
          sub: liderNac ? TX('{v} alunos · {p}', { v: compacto(liderNac[1]),
                                                   p: pct(100 * liderNac[1] / tot) }) : '' }),
    kpi({ rot: TX('UFs lideradas por abertas'), val: n([...uf.values()]
            .filter(a => D.gruposOrd[lider(a).lider]?.tipo === 'listada').length),
          sub: TX('de {q} unidades da federação', { q: uf.size }) }),
  ].join('');

  // a malha precisa estar registrada ANTES do primeiro mapa da tela — os de bolha vêm
  // primeiro agora, então o registro subiu junto
  if (window.__ufGeo && !window.__mapaReg) {
    echarts.registerMap('BR', window.__ufGeo);
    window.__mapaReg = true;
  }

  /* ══════════════════════════════════════════ CAPILARIDADE ═══════════════ */
  chipsGeo($('#ge-chips'), () => geography(window.__filtros));
  const selG = D.gruposLista.filter(k => selGeo.has(k));
  const latlon = mx => [D.dim.mun.lon[mx], D.dim.mun.lat[mx]];
  const temGeo = mx => D.dim.mun.lat[mx] != null && D.dim.mun.lon[mx] != null;

  /* Pontos de um grupo, opcionalmente só de uma modalidade. `campo` é 'mat', 'pres' ou
   * 'ead' — a mesma função serve ao mapa de capilaridade e aos dois de pegada. */
  const pontosDe = (k, campo) => {
    const g = porGrupoMun.get(k);
    if (!g) return [];
    const out = [];
    for (const [mx, o] of g) {
      const v = o[campo];
      if (v <= 0 || !temGeo(mx)) continue;
      const [lon, lat] = latlon(mx);
      out.push([lon, lat, v, `${nomeMun(mx)} — ${ufMun(mx)}`]);
    }
    return out;
  };

  /* UM mapa grande com seletor de grupo.
   *
   * ⚠️ Já foram tentadas as duas alternativas, nesta ordem: (1) todos os grupos
   * sobrepostos num mapa só — ~9.000 bolhas translúcidas empilhadas, ilegível; (2) oito
   * pequenos múltiplos de 210px — apertado demais para ler. Hoje é um mapa em tamanho de
   * leitura e o usuário escolhe o grupo.
   *
   * A comparação entre grupos continua honesta porque `maxCap` é calculado sobre TODOS os
   * selecionados, não sobre o grupo exibido: trocar de grupo não reescala as bolhas, e uma
   * bolha do mesmo tamanho significa o mesmo número de alunos em qualquer grupo. */
  const modoCap = opcoes($('#ge-cap-mod'),
    [{ v: 'mat', t: TX('Todas') }, { v: 'pres', t: TX('Só presencial') },
     { v: 'ead', t: TX('Só EAD') }],
    () => geography(window.__filtros)) || 'mat';
  const grupoCap = opcoes($('#ge-cap-grupo'),
    selG.map(k => ({ v: k, t: nomeGrupo(k) })),
    () => geography(window.__filtros)) || selG[0];

  const maxCap = Math.max(1, ...selG.flatMap(k => pontosDe(k, modoCap).map(p => p[2])));
  const ptsCap = grupoCap ? pontosDe(grupoCap, modoCap) : [];
  mapaBolhas($('#ge-cap'), [{ nome: nomeGrupo(grupoCap), cor: corGrupoK(grupoCap,
                              D.gruposLista.indexOf(grupoCap)), pontos: ptsCap }],
             { max: maxCap });
  $('#ge-cap-tit').textContent = TX('Capilaridade — {g}', { g: nomeGrupo(grupoCap) });
  $('#ge-cap-resumo').textContent = TX('{q} municípios · {v} alunos', {
    q: n(ptsCap.length), v: compacto(ptsCap.reduce((s, p) => s + p[2], 0)) });

  /* Ranking ao lado do mapa. Serve a dois propósitos: dá contexto ao mapa (1.703
   * municípios é muito ou pouco?) e ocupa a faixa que sobrava — o Brasil é quase quadrado
   * e o cartão é largo, então um mapa sozinho deixava um vazio grande dos dois lados. */
  const rankCap = selG.map(k => {
    const pts = pontosDe(k, modoCap);
    return { grupo: nomeGrupo(k), _raw: k, munic: pts.length,
             mat: pts.reduce((s, p) => s + p[2], 0), _on: k === grupoCap };
  }).sort((a, b) => b.munic - a.munic);
  tabela($('#ge-cap-rank'), [
    { k: 'grupo', t: TX('Grupo'), tipo: 'txt', fmt: (v, r) =>
        `<span style="display:inline-flex;align-items:center;gap:7px;${r._on ? 'font-weight:700' : ''}">
           <span style="width:8px;height:8px;border-radius:50%;background:${corGrupoK(r._raw)}"></span>
           ${esc(v)}${r._on ? ' ◂' : ''}</span>` },
    // `barra` sem `fmt` rotula com pct() e sairia "1.703,0%"; aqui o valor é CONTAGEM.
    // A barra em si já escala pelo maior da coluna, que é o que se quer comparar.
    { k: 'munic', t: TX('Municípios'), tipo: 'barra', fmt: v => n(v) },
    { k: 'mat', t: TX('Alunos'), tipo: 'num', fmt: v => compacto(v) },
  ], rankCap, { ordem: 'munic' });

  /* ⚠️ Presença = ter ALUNO no município, não ter linha no cubo.
   *
   * `ies_mun` tem 1.044 linhas com `qt_mat = 0` — município onde a IES tem oferta
   * registrada e nenhum aluno matriculado. Contá-las inflava a Cogna de 1.703 para 1.986
   * municípios e, pior, fazia a sobreposição competitiva tratar praça vazia como disputa.
   * O mapa já filtrava (`v <= 0`) e a tabela não, e foi a divergência entre os dois que
   * denunciou o problema. Agora os dois usam o mesmo critério. */
  const munDe = k => {
    const s = new Set();
    for (const [mx, o] of (porGrupoMun.get(k) || new Map())) if (o.mat > 0) s.add(mx);
    return s;
  };
  const capLinhas = selG.map(k => {
    const g = porGrupoMun.get(k) || new Map();
    let nPres = 0, nEad = 0, nMun = 0, mat = 0;
    for (const o of g.values()) {
      if (o.mat <= 0) continue;
      nMun++;
      if (o.pres > 0) nPres++;
      if (o.ead > 0) nEad++;
      mat += o.mat;
    }
    return {
      grupo: nomeGrupo(k), _raw: k, munic: nMun, pres: nPres, ead: nEad, mat,
      // quanto do alcance NÃO tem estrutura física por trás
      leve: nMun ? 100 * (nMun - nPres) / nMun : 0,
      porMun: nMun ? mat / nMun : 0,
    };
  }).sort((a, b) => b.munic - a.munic);

  $('#ge-cap-nota').textContent = TX(
    'A bolha é o número de ALUNOS no município — não o número de campi nem de polos —, ' +
    'dimensionada pela raiz, porque em escala linear São Paulo apagaria todo o interior, que ' +
    'é o que interessa aqui. A posição é o centroide do município ({q} dos {t} têm ' +
    'coordenada), não o endereço de nenhuma unidade: o Censo dá o município de oferta, e não ' +
    'a rua. No presencial o município é onde o curso é dado; no EAD, onde está o polo.',
    { q: n(D.dim.mun.lat.filter(v => v != null).length), t: n(D.dim.mun.lat.length) });

  /* ═══════════════════════════════ PEGADA FÍSICA × DIGITAL ═══════════════ */
  /* ⚠️ Aqui os selecionados entram SOMADOS, numa cor só por mapa — não uma série por
   * grupo. A pergunta desta seção não é "qual grupo", é "quanto do alcance tem estrutura
   * física por trás"; sete cores sobrepostas responderiam pior e repetiriam o painel de
   * cima. As cores são as do projeto: presencial = azul (estrutura instalada),
   * EAD = laranja (o que cresce). Quem quiser abrir por grupo tem a tabela abaixo. */
  const uniao = campo => {
    const acc = new Map();
    selG.forEach(k => {
      for (const [mx, o] of (porGrupoMun.get(k) || new Map())) {
        if (o[campo] > 0) acc.set(mx, (acc.get(mx) || 0) + o[campo]);
      }
    });
    return [...acc.entries()].filter(([mx]) => temGeo(mx)).map(([mx, v]) => {
      const [lon, lat] = latlon(mx);
      return [lon, lat, v, `${nomeMun(mx)} — ${ufMun(mx)}`];
    });
  };
  const ptsFis = uniao('pres'), ptsDig = uniao('ead');
  // escala comum aos dois mapas: e o contraste entre eles e o proprio ponto da secao
  const maxFD = Math.max(1, ...ptsFis.map(p => p[2]), ...ptsDig.map(p => p[2]));
  // ⚠️ O título diz "municípios COM presencial", não "unidades": o Censo não tem
  // identificador de campus nem de polo, então dois campi na mesma cidade contam como um.
  // É piso do número de unidades, não o número — ver a nota da seção.
  $('#ge-fis-tit').textContent = TX('Presencial — {q} municípios com campus',
    { q: n(ptsFis.length) });
  $('#ge-dig-tit').textContent = TX('EAD — {q} municípios com polo', { q: n(ptsDig.length) });
  mapaBolhas($('#ge-fis'), [{ nome: TX('Presencial'), cor: COR_PRES, pontos: ptsFis }],
             { max: maxFD });
  mapaBolhas($('#ge-dig'), [{ nome: TX('EAD'), cor: COR_EAD, pontos: ptsDig }],
             { max: maxFD });

  tabela($('#ge-fisdig'), [
    { k: 'grupo', t: TX('Grupo'), tipo: 'txt', fmt: (v, r) =>
        `<span style="display:inline-flex;align-items:center;gap:8px"><span style="width:9px;
         height:9px;border-radius:2px;background:${corGrupoK(r._raw)}"></span>${esc(v)}</span>` },
    { k: 'munic', t: TX('Municípios no total'), tipo: 'num' },
    { k: 'pres', t: TX('Com presencial'), tipo: 'num' },
    { k: 'ead', t: TX('Com EAD'), tipo: 'num' },
    { k: 'leve', t: TX('% sem estrutura física'), tipo: 'pct' },
    { k: 'porMun', t: TX('Alunos por município'), tipo: 'num', fmt: v => n(Math.round(v)) },
  ], capLinhas, { ordem: 'munic',
    csv: { bloco: 'geografia', nome: TX('Capilaridade por grupo') } });

  $('#ge-fisdig-nota').textContent = TX(
    'A bolha é sempre ALUNO, nunca unidade: no presencial, matrículas no município onde o ' +
    'curso é dado; no EAD, matrículas no município do polo — e o polo é mesmo onde o aluno ' +
    'está, não a sede (a Unopar, sede no PR, distribui seus alunos por 27 UFs, e o PR fica ' +
    'com 5%). A CONTAGEM de municípios é proxy de campi e de polos, e é um PISO: o Censo não ' +
    'traz identificador de campus nem de polo, então dois campi na mesma cidade contam como ' +
    'um. Estes dois mapas ignoram o filtro de modalidade de propósito — com "EAD" ' +
    'selecionado, o mapa do presencial ficaria vazio e pareceria que o grupo não tem campus. ' +
    'O filtro de rede continua valendo.');

  /* ═════════════════════════════ SOBREPOSIÇÃO COMPETITIVA ═══════════════ */
  // quantos dos grupos escolhidos estão em cada município
  const presencaPorMun = new Map();
  selG.forEach(k => munDe(k).forEach(mx => {
    if (!presencaPorMun.has(mx)) presencaPorMun.set(mx, new Set());
    presencaPorMun.get(mx).add(k);
  }));
  const FAIXAS = [
    { rot: TX('Só um grupo'), cor: '#8FB4D9', teste: q => q === 1 },
    { rot: TX('Dois grupos'), cor: '#EC7000', teste: q => q === 2 },
    { rot: TX('Três ou mais'), cor: '#A34B00', teste: q => q >= 3 },
  ];
  const sobSeries = FAIXAS.map(fx => ({
    nome: fx.rot, cor: fx.cor,
    pontos: [...presencaPorMun.entries()]
      .filter(([mx, s]) => fx.teste(s.size) && temGeo(mx))
      .map(([mx, s]) => {
        const [lon, lat] = latlon(mx);
        const alunos = selG.reduce((acc, k) => acc + (porGrupoMun.get(k)?.get(mx)?.mat || 0), 0);
        return [lon, lat, alunos, `${nomeMun(mx)} — ${ufMun(mx)} · ${s.size} ${TX('grupos')}`];
      }),
  }));
  $('#ge-sob-tit').textContent = TX('Onde os {q} selecionados se cruzam', { q: selG.length });
  mapaBolhas($('#ge-sob'), sobSeries, { opacidade: .55 });

  const disputados = [...presencaPorMun.values()].filter(s => s.size > 1).length;
  $('#ge-sob-nota').textContent = TX(
    'Dos {t} municípios alcançados por pelo menos um dos selecionados, {d} têm mais de um ' +
    'deles presente — {p} do território coberto. Presença aqui é ter ao menos um aluno no ' +
    'município, em qualquer modalidade; não mede quem é mais forte, mede onde há disputa.',
    { t: n(presencaPorMun.size), d: n(disputados),
      p: pct(presencaPorMun.size ? 100 * disputados / presencaPorMun.size : 0) });

  const exclLinhas = selG.map(k => {
    const meus = munDe(k);
    let so = 0;
    meus.forEach(mx => { if (presencaPorMun.get(mx)?.size === 1) so++; });
    return { grupo: nomeGrupo(k), _raw: k, munic: meus.size, exclusivo: so,
             dividido: meus.size - so,
             pctExcl: meus.size ? 100 * so / meus.size : 0 };
  }).sort((a, b) => b.exclusivo - a.exclusivo);
  tabela($('#ge-excl'), [
    { k: 'grupo', t: TX('Grupo'), tipo: 'txt' },
    { k: 'exclusivo', t: TX('Só ele'), tipo: 'num' },
    { k: 'dividido', t: TX('Divide'), tipo: 'num' },
    { k: 'pctExcl', t: TX('% exclusivo'), tipo: 'pct' },
  ], exclLinhas, { ordem: 'exclusivo',
    csv: { bloco: 'geografia', nome: TX('Exclusividade por município') } });

  /* ══════════════════════════ QUALIDADE E SITUAÇÃO (e-MEC) ══════════════ */
  await secaoEmec(f, selG);

  const lideres = new Map();
  const dadosMapa = Object.entries(SG_UF).map(([co, sg]) => {
    const a = uf.get(sg);
    if (!a) return { name: co, value: 0, sg, txt: TX('sem oferta') };
    const L = lider(a);
    if (L.lider) lideres.set(L.lider, (lideres.get(L.lider) || 0) + 1);
    const top3 = ranking(a.g).slice(0, 3)
      .map(([k, v]) => `${esc(nomeGrupo(k))}: ${n(v)} (${pct(100 * v / a.mat)})`).join('<br>');
    return {
      name: co, value: L.matLider, sg, grupo: L.lider,
      itemStyle: { areaColor: L.lider ? corGrupoK(L.lider) : '#EEEFF1' },
      txt: `<span style="color:#8C8C8C">${TX('{v} matrículas na UF', { v: n(a.mat) })}</span><br>${top3}`,
    };
  });
  chart($('#ge-mapa'), {
    textStyle: { fontFamily: '-apple-system, "Segoe UI", Roboto, sans-serif' },
    tooltip: {
      trigger: 'item', backgroundColor: '#fff', borderColor: '#D2D4D8', borderWidth: 1,
      padding: [9, 12], textStyle: { color: '#1A1A1A', fontSize: 12.5 },
      extraCssText: 'box-shadow:0 4px 14px rgba(0,0,0,.10);border-radius:8px',
      formatter: p => `<strong>${p.data?.sg || ''}</strong>` +
        (p.data?.grupo ? ` · ${TX('líder')} ${esc(nomeGrupo(p.data.grupo))}` : '') +
        `<br>${p.data?.txt || ''}`,
    },
    series: [{
      type: 'map', map: 'BR', roam: false, data: dadosMapa,
      itemStyle: { borderColor: '#fff', borderWidth: .8 },
      emphasis: { itemStyle: { areaColor: LARANJA }, label: { show: false } },
      select: { disabled: true },
    }],
  });
  $('#ge-mapa-leg').innerHTML = '<div class="legenda">' +
    [...lideres.entries()].sort((a, b) => b[1] - a[1]).map(([k, q]) =>
      `<span><i style="background:${corGrupoK(k)}"></i>${esc(nomeGrupo(k))} <b>${q}</b></span>`).join('') +
    '</div>';

  // -------------------------------------------------- tabela lider por UF
  const rowsUFL = [...uf.entries()].map(([sg, a]) => {
    const L = lider(a);
    return {
      uf: sg, regiao: TXregiao(a.regiao), mat: a.mat, pres: a.pres, ead: a.ead,
      pctEad: a.mat ? 100 * a.ead / a.mat : 0, share: tot ? 100 * a.mat / tot : 0,
      lider: L.lider ? nomeGrupo(L.lider) : '—', _lider: L.lider,
      matLider: L.matLider, shareLider: a.mat ? 100 * L.matLider / a.mat : 0,
      vice: L.vice ? nomeGrupo(L.vice) : '—', shareVice: a.mat ? 100 * L.matVice / a.mat : 0,
      indep: a.mat ? 100 * L.indep / a.mat : 0,
    };
  }).sort((a, b) => b.mat - a.mat);
  const celGrupo = (v, r) => r._lider
    ? `<span style="display:inline-flex;align-items:center;gap:7px"><span style="width:8px;height:8px;
       border-radius:2px;background:${corGrupoK(r._lider)}"></span>${esc(v)}</span>` : '—';
  tabela($('#ge-lider-uf'), [
    { k: 'uf', t: 'UF', tipo: 'txt' },
    { k: 'mat', t: TX('Matrículas'), tipo: 'num' },
    { k: 'lider', t: TX('Líder'), tipo: 'txt', fmt: celGrupo },
    { k: 'matLider', t: TX('Alunos do líder'), tipo: 'num' },
    { k: 'shareLider', t: TX('Share do líder'), tipo: 'barra' },
    { k: 'vice', t: TX('Vice'), tipo: 'txt' },
    { k: 'shareVice', t: TX('Share vice'), tipo: 'pct' },
    { k: 'indep', t: TX('% não mapeado'), tipo: 'pct' },
  ], rowsUFL, { ordem: 'mat',
    csv: { bloco: 'geografia', nome: TX('Liderança por UF'),
           cols: [{ k: 'uf', t: 'UF' }, { k: 'regiao', t: TX('Região') },
                  { k: 'mat', t: TX('Matrículas') }, { k: 'pres', t: TX('Presencial') },
                  { k: 'ead', t: TX('EAD') }, { k: 'lider', t: TX('Líder') },
                  { k: 'matLider', t: TX('Alunos do líder') },
                  { k: 'shareLider', t: TX('Share do líder') }, { k: 'vice', t: TX('Vice') },
                  { k: 'shareVice', t: TX('Share vice') }, { k: 'indep', t: TX('% não mapeado') }] } });

  // -------------------------------------------------------- abrir uma praca
  const ufSel = opcoes($('#ge-uf-sel'), rowsUFL.map(r => ({ v: r.uf, t: `${r.uf} — ${r.regiao}` })),
                       () => geography(window.__filtros)) || rowsUFL[0]?.uf;
  const aSel = uf.get(ufSel);
  $('#ge-uf-tit').textContent = TX('Ranking de players em {u}', { u: ufSel });
  $('#ge-uf-mun-tit').textContent = TX('Maiores municípios de {u}', { u: ufSel });
  const rowsPl = aSel ? [...aSel.g.entries()].map(([k, v]) => ({
    grupo: k === 'Independentes' ? TX('Independentes / não mapeado') : nomeGrupo(k), _raw: k,
    mat: v, share: 100 * v / aSel.mat,
  })).sort((a, b) => b.mat - a.mat) : [];
  tabela($('#ge-uf-players'), [
    { k: 'grupo', t: TX('Grupo'), tipo: 'txt', fmt: (v, r) => r._raw === 'Independentes' ? esc(v)
        : `<span style="display:inline-flex;align-items:center;gap:7px"><span style="width:8px;height:8px;
           border-radius:2px;background:${corGrupoK(r._raw)}"></span>${esc(v)}</span>` },
    { k: 'mat', t: TX('Alunos na UF'), tipo: 'num' },
    { k: 'share', t: TX('Share na UF'), tipo: 'barra' },
  ], rowsPl, { ordem: 'mat', limite: 15,
    csv: { bloco: 'geografia', nome: TX('Players em {u}', { u: ufSel }),
           cols: [{ k: 'grupo', t: TX('Grupo') }, { k: 'mat', t: TX('Alunos na UF') },
                  { k: 'share', t: TX('Share na UF') }] } });

  /* ───────────────────── overlap dentro de um município ─────────────────────
   * O nível mais fino que o Censo permite. Responde "nesta cidade, quem está e com
   * quanto" — que é a pergunta que a matriz por UF não alcança, porque um estado grande
   * esconde que os players podem estar em cidades diferentes dentro dele.
   *
   * ⚠️ O seletor de município é repopulado a cada troca de UF. `opcoes()` do ui.js existe
   * exatamente para isso: repopula quando a lista muda e preserva a escolha se ela ainda
   * existir — um `<select>` populado "uma vez só" travaria vazio, que é a armadilha nº 4
   * já paga neste projeto. */
  const munDaUF = [...mun.entries()]
    .filter(([ix]) => ufMun(ix) === ufSel)
    .sort((a, b) => b[1].mat - a[1].mat);
  const munSelIx = opcoes($('#ge-mun-sel'),
    munDaUF.map(([ix, m]) => ({ v: String(ix), t: `${nomeMun(ix)} — ${compacto(m.mat)}` })),
    () => geography(window.__filtros));
  const mIx = munSelIx != null && munSelIx !== '' ? +munSelIx : (munDaUF[0]?.[0] ?? null);
  const mDados = mIx != null ? mun.get(mIx) : null;

  if (!mDados) {
    $('#ge-praca-tit').textContent = TX('Quem está neste município');
    $('#ge-praca-kpis').innerHTML = '';
    $('#ge-praca-tab').innerHTML = `<div class="vazio">${TX('Sem dados para esta praça.')}</div>`;
    $('#ge-praca-nota').textContent = '';
    chart($('#ge-praca'), { series: [] });
  } else {
    const nomeP = `${nomeMun(mIx)} — ${ufSel}`;
    $('#ge-praca-tit').textContent = TX('Quem está em {m}', { m: nomeP });

    // presencial e EAD separados por grupo, só dos selecionados nos chips
    const praca = selG.map(k => {
      const o = porGrupoMun.get(k)?.get(mIx) || { pres: 0, ead: 0, mat: 0 };
      return { grupo: nomeGrupo(k), _raw: k, pres: o.pres, ead: o.ead, mat: o.mat,
               share: mDados.mat ? 100 * o.mat / mDados.mat : 0 };
    }).sort((a, b) => b.mat - a.mat);

    chart($('#ge-praca'), {
      ...baseChart(),
      legend: { ...baseChart().legend, data: [T_PRES(), T_EAD()] },
      grid: { left: 8, right: 60, top: 30, bottom: 6, containLabel: true },
      xAxis: { type: 'value', splitLine: { lineStyle: { color: '#F2F3F5' } },
               axisLine: { show: false }, axisTick: { show: false },
               axisLabel: { fontSize: 11.5, color: '#8C8C8C', formatter: fmtEixoMi } },
      yAxis: { type: 'category', data: praca.map(r => r.grupo), inverse: true,
               axisLine: { show: false }, axisTick: { show: false },
               axisLabel: { fontSize: 12, color: '#4A4A4A' } },
      series: [
        { name: T_PRES(), type: 'bar', stack: 'a', barMaxWidth: 24,
          itemStyle: { color: COR_PRES }, data: praca.map(r => r.pres) },
        { name: T_EAD(), type: 'bar', stack: 'a', barMaxWidth: 24,
          itemStyle: { color: COR_EAD }, data: praca.map(r => r.ead),
          label: { show: true, position: 'right', fontSize: 11, color: '#4A4A4A',
                   formatter: p => praca[p.dataIndex].mat
                     ? `${compacto(praca[p.dataIndex].mat)} · ${pct(praca[p.dataIndex].share)}`
                     : TX('ausente') } },
      ],
      tooltip: { ...baseChart().tooltip, valueFormatter: v => n(v) },
    });

    const presentes = praca.filter(r => r.mat > 0);
    const somaSel = presentes.reduce((s, r) => s + r.mat, 0);
    const Lp = lider(mDados);
    $('#ge-praca-kpis').innerHTML = `<div class="praca-kpis">
      <div class="praca-kpi"><div class="rot">${TX('Alunos na praça')}</div>
        <div class="val">${compacto(mDados.mat)}</div>
        <div class="sub">${pct(mDados.mat ? 100 * mDados.pres / mDados.mat : 0)} ${TX('presencial')}</div></div>
      <div class="praca-kpi"><div class="rot">${TX('Dos selecionados')}</div>
        <div class="val">${n(presentes.length)}<span style="font-size:13px;color:var(--ink-3)">/${selG.length}</span></div>
        <div class="sub">${TX('presentes aqui')}</div></div>
      <div class="praca-kpi"><div class="rot">${TX('Peso do conjunto')}</div>
        <div class="val">${pct(mDados.mat ? 100 * somaSel / mDados.mat : 0)}</div>
        <div class="sub">${compacto(somaSel)} ${TX('alunos')}</div></div>
      <div class="praca-kpi"><div class="rot">${TX('Líder da praça')}</div>
        <div class="val" style="font-size:15px">${Lp.lider ? esc(nomeGrupo(Lp.lider)) : '—'}</div>
        <div class="sub">${pct(mDados.mat ? 100 * Lp.matLider / mDados.mat : 0)} ${TX('da praça')}</div></div>
    </div>`;

    tabela($('#ge-praca-tab'), [
      { k: 'grupo', t: TX('Grupo'), tipo: 'txt', fmt: (v, r) =>
          `<span style="display:inline-flex;align-items:center;gap:7px;${r.mat ? '' : 'opacity:.45'}">
             <span style="width:8px;height:8px;border-radius:2px;background:${corGrupoK(r._raw)}"></span>
             ${esc(v)}</span>` },
      { k: 'mat', t: TX('Alunos'), tipo: 'num', fmt: v => v ? n(v) : '—' },
      { k: 'share', t: TX('Share na praça'), tipo: 'barra' },
    ], praca, { ordem: 'mat',
      csv: { bloco: 'geografia', nome: TX('Overlap em {m}', { m: nomeP }),
             cols: [{ k: 'grupo', t: TX('Grupo') }, { k: 'pres', t: TX('Presencial') },
                    { k: 'ead', t: TX('EAD') }, { k: 'mat', t: TX('Alunos') },
                    { k: 'share', t: TX('Share na praça') }] } });

    $('#ge-praca-nota').textContent = TX(
      'Denominador: as {t} matrículas de {m} em {a}. Barra vazia é grupo que não tem aluno ' +
      'nesta cidade — está na lista de propósito, porque ausência numa praça é informação ' +
      'competitiva. O rótulo do fim da barra traz o total do grupo e a fatia dele na praça.',
      { t: n(mDados.mat), m: nomeP, a: ano });
  }

  const munUF = [...mun.entries()].filter(([ix]) => ufMun(ix) === ufSel)
    .map(([ix, m]) => {
      const L = lider(m);
      return { mun: nomeMun(ix), mat: m.mat, pres: m.pres, ead: m.ead,
               lider: L.lider ? nomeGrupo(L.lider) : '—', _lider: L.lider,
               shareLider: m.mat ? 100 * L.matLider / m.mat : 0 };
    }).sort((a, b) => b.mat - a.mat);
  tabela($('#ge-uf-mun'), [
    { k: 'mun', t: TX('Município'), tipo: 'txt' },
    { k: 'mat', t: TX('Matrículas'), tipo: 'num' },
    { k: 'lider', t: TX('Líder'), tipo: 'txt', fmt: celGrupo },
    { k: 'shareLider', t: TX('Share do líder'), tipo: 'barra' },
  ], munUF, { ordem: 'mat', limite: 20,
    csv: { bloco: 'geografia', nome: TX('Municípios de {u}', { u: ufSel }),
           cols: [{ k: 'mun', t: TX('Município') }, { k: 'mat', t: TX('Matrículas') },
                  { k: 'pres', t: TX('Presencial') }, { k: 'ead', t: TX('EAD') },
                  { k: 'lider', t: TX('Líder') }, { k: 'shareLider', t: TX('Share do líder') }] } });

  // ------------------------------------------ maiores municipios do pais
  const rowsMun = [...mun.entries()].map(([ix, m]) => {
    const L = lider(m);
    return {
      mun: nomeMun(ix), uf: ufMun(ix), mat: m.mat, pres: m.pres, ead: m.ead,
      lider: L.lider ? nomeGrupo(L.lider) : '—', _lider: L.lider,
      matLider: L.matLider, shareLider: m.mat ? 100 * L.matLider / m.mat : 0,
      players: L.players,
    };
  }).sort((a, b) => b.mat - a.mat);
  tabela($('#ge-mun-lider'), [
    { k: 'mun', t: TX('Município'), tipo: 'txt' },
    { k: 'uf', t: 'UF', tipo: 'txt' },
    { k: 'mat', t: TX('Matrículas'), tipo: 'num' },
    { k: 'pres', t: TX('Presencial'), tipo: 'num' },
    { k: 'ead', t: TX('EAD'), tipo: 'num' },
    { k: 'lider', t: TX('Líder'), tipo: 'txt', fmt: celGrupo },
    { k: 'matLider', t: TX('Alunos do líder'), tipo: 'num' },
    { k: 'shareLider', t: TX('Share do líder'), tipo: 'barra' },
    { k: 'players', t: TX('Grupos mapeados'), tipo: 'num' },
  ], rowsMun, { ordem: 'mat', limite: 40,
    csv: { bloco: 'geografia', nome: TX('Municípios do país com líder'),
           cols: [{ k: 'mun', t: TX('Município') }, { k: 'uf', t: 'UF' },
                  { k: 'mat', t: TX('Matrículas') }, { k: 'pres', t: TX('Presencial') },
                  { k: 'ead', t: TX('EAD') }, { k: 'lider', t: TX('Líder') },
                  { k: 'matLider', t: TX('Alunos do líder') },
                  { k: 'shareLider', t: TX('Share do líder') }] } });
  $('#ge-nota').textContent = TX(
    'Geografia usa apenas as dimensões 1 e 2 do Censo e atribui o aluno ao município de oferta. ' +
    'No EAD, esse município é o do polo de apoio presencial — não a residência do aluno; um polo ' +
    'pequeno pode concentrar muitos alunos. Líder exclui o bucket "Independentes", que não é um ' +
    'player. {q} matrículas ficam fora do recorte geográfico com os filtros atuais (exterior/N.I. ' +
    'e o que os filtros excluem). A tabela mostra 40 municípios; o CSV traz todos os {t}.',
    { q: n(kpiAno(ano).mat_total - tot), t: n(rowsMun.length) });

  // ------------------------------------------------- composicao regional
  const porReg = new Map();
  uf.forEach(a => {
    let o = porReg.get(a.regiao);
    if (!o) { o = { pres: 0, ead: 0, mat: 0 }; porReg.set(a.regiao, o); }
    o.pres += a.pres; o.ead += a.ead; o.mat += a.mat;
  });
  const rr = [...porReg.entries()].sort((a, b) => b[1].mat - a[1].mat);
  chart($('#ge-reg'), {
    ...baseChart(),
    legend: { ...baseChart().legend, data: [T_PRES(), T_EAD()] },
    xAxis: { ...baseChart().xAxis, data: rr.map(x => TXregiao(x[0])) },
    yAxis: { ...baseChart().yAxis, axisLabel: { fontSize: 11.5, color: '#8C8C8C', formatter: fmtEixoMi } },
    series: [
      { name: T_PRES(), type: 'bar', stack: 'a', itemStyle: { color: COR_PRES }, barMaxWidth: 44,
        data: rr.map(x => x[1].pres) },
      { name: T_EAD(), type: 'bar', stack: 'a', itemStyle: { color: COR_EAD }, barMaxWidth: 44,
        data: rr.map(x => x[1].ead) },
    ],
    tooltip: { ...baseChart().tooltip, valueFormatter: v => n(v) },
  });
  registrarCSV('geografia', TX('Composição por região'),
    [{ k: 'regiao', t: TX('Região') }, { k: 'mat', t: TX('Matrículas') },
     { k: 'pres', t: TX('Presencial') }, { k: 'ead', t: TX('EAD') }],
    rr.map(([r, v]) => ({ regiao: TXregiao(r), mat: v.mat, pres: v.pres, ead: v.ead })));

  tabela($('#ge-uf'), [
    { k: 'uf', t: 'UF', tipo: 'txt' }, { k: 'regiao', t: TX('Região'), tipo: 'txt' },
    { k: 'mat', t: TX('Matrículas'), tipo: 'num' }, { k: 'pres', t: TX('Presencial'), tipo: 'num' },
    { k: 'ead', t: TX('EAD'), tipo: 'num' }, { k: 'pctEad', t: TX('% EAD'), tipo: 'pct' },
    { k: 'share', t: TX('Share'), tipo: 'barra' },
  ], rowsUFL, { ordem: 'mat' });
}

/* ============================================== GLOSSÁRIO ================ */
/* ------------------------------------------------ composicao por player
 * Mora no GLOSSÁRIO, não nos Rankings: é material de referência — a lista exata de IES
 * somadas em cada grupo é o que explica qualquer divergência contra o release, e o lugar
 * natural para isso é junto das definições, não junto dos rankings competitivos.
 * Depende do ano, então `FILTROS.glossario` inclui 'ano'.                              */
export async function glossario(f) {
  const ano = f.ano, tot = totalAno(ano, f);
  const selG = $('#gl-grupo');
  if (!selG.dataset.pronto) {
    const listadas = D.gruposLista.filter(k => D.gruposOrd[k]?.tipo === 'listada');
    const outros = D.gruposLista.filter(k => k !== 'Independentes' && !listadas.includes(k));
    selG.innerHTML =
      `<optgroup label="${TX('Companhias abertas')}">` +
      listadas.map(k => `<option value="${esc(k)}">${esc(nomeGrupo(k))}</option>`).join('') +
      `</optgroup><optgroup label="${TX('Outros grupos')}">` +
      outros.map(k => `<option value="${esc(k)}">${esc(nomeGrupo(k))}</option>`).join('') +
      `</optgroup>`;
    selG.dataset.pronto = '1';
    selG.onchange = () => glossario(window.__filtros);
  }
  const grupoSel = selG.value || D.gruposLista.find(k => D.gruposOrd[k]?.tipo === 'listada');

  const fComp = { ...f, grupo: grupoSel };
  const iesComp = porIES(ano, ix => ix, fComp);
  const iesCompP = porIES(ano - 1, ix => ix, fComp);
  const unComp = unidadesPorIES(ano, ix => ix, fComp);
  const org = ORG();
  const compRows = [...iesComp.entries()].map(([ix, v]) => {
    const p = iesCompP.get(ix);
    return {
      co: D.dim.ies.co[ix], ies: nomeIES(ix), uf: ufIES(ix),
      org: TXorg(org[String(D.dim.ies.org[ix])] || '—'),
      mant: D.dim.ies.mant[ix] || '',
      unidades: unComp.get(ix)?.unidades || 0,
      mat: v.mat, pres: v.pres, ead: v.ead, tranc: v.tranc, base: v.mat + v.tranc,
      yoy: p && p.mat ? 100 * (v.mat - p.mat) / p.mat : null,
    };
  }).sort((a, b) => b.mat - a.mat);
  const somaC = compRows.reduce((s, r) => ({
    mat: s.mat + r.mat, pres: s.pres + r.pres, ead: s.ead + r.ead,
    tranc: s.tranc + r.tranc, base: s.base + r.base, unidades: s.unidades + r.unidades,
  }), { mat: 0, pres: 0, ead: 0, tranc: 0, base: 0, unidades: 0 });
  compRows.forEach(r => { r.pctGrupo = somaC.mat ? 100 * r.mat / somaC.mat : 0; });

  $('#gl-comp-tit').textContent = TX('IES consideradas em {g} — {a}',
    { g: nomeGrupo(grupoSel), a: ano });

  /* ⚠️ Concentração em poucas IES quase sempre é ARTEFATO DE REGISTRO, não geografia.
   *
   * O Censo lança a matrícula de EAD na IES **sede**, não no polo onde o aluno estuda.
   * Quando um grupo consolida todo o EAD numa mantida só, essa IES aparece com 50–75% da
   * base do grupo e uma UF colada nela — e o leitor conclui concentração geográfica que
   * não existe: a Unopar tem polo no país inteiro, e a UF do quadro é só o endereço da
   * sede em Londrina. Foi exatamente a dúvida levantada sobre Cogna (75% numa IES do PR)
   * e Vitru (98,7% em duas).
   *
   * A regra é por dado, não por nome de grupo: dispara quando as IES que somam a maior
   * parte da base são predominantemente EAD. Assim vale para qualquer grupo que venha a
   * ter o mesmo desenho, e não vira lista de exceções para alguém manter à mão.        */
  const LIM_CONCENTRACAO = 40;   // % da base do grupo numa única IES
  const LIM_EAD = 80;            // % de EAD dentro dessa IES
  const concentradas = compRows.filter(r =>
    r.pctGrupo >= LIM_CONCENTRACAO && r.mat && (100 * r.ead / r.mat) >= LIM_EAD);
  $('#gl-comp-ead').innerHTML = concentradas.length ? `<div class="aviso">${TX(
    '{l} concentra(m) {p} da base do grupo, e {q} dessas matrículas são EAD. Isso é registro, ' +
    'não geografia: o Censo lança a matrícula de EAD na IES <strong>sede</strong>, não no polo ' +
    'onde o aluno estuda — a UF da linha é o endereço da mantida, e não onde estão os alunos. ' +
    'Para saber onde eles realmente estão, use o bloco Geografia, que distribui por município ' +
    'de oferta.',
    { l: concentradas.map(r => `<strong>${esc(r.ies)}</strong>`).join(', '),
      p: pct(concentradas.reduce((s, r) => s + r.pctGrupo, 0)),
      q: pct(100 * concentradas.reduce((s, r) => s + r.ead, 0) /
             Math.max(1, concentradas.reduce((s, r) => s + r.mat, 0))) })}</div>` : '';
  tabela($('#gl-comp'), [
    { k: 'co', t: 'CO_IES', tipo: 'num', fmt: v => `<code>${v}</code>` },
    { k: 'ies', t: TX('Instituição'), tipo: 'txt' },
    { k: 'uf', t: 'UF', tipo: 'txt' },
    { k: 'org', t: TX('Organização'), tipo: 'txt', fmt: v => `<span class="tag">${esc(v)}</span>` },
    { k: 'unidades', t: TX('Unid.'), tipo: 'num' },
    { k: 'mat', t: TX('Matrículas'), tipo: 'num' },
    { k: 'pres', t: TX('Presencial'), tipo: 'num' },
    { k: 'ead', t: TX('EAD'), tipo: 'num' },
    { k: 'tranc', t: TX('Trancados'), tipo: 'num' },
    { k: 'base', t: TX('Base de alunos'), tipo: 'num' },
    { k: 'pctGrupo', t: TX('% do grupo'), tipo: 'barra' },
    { k: 'yoy', t: 'YoY', tipo: 'num', fmt: v => deltaHTML(v) },
  ], compRows, { ordem: 'mat',
    csv: { bloco: 'glossario', nome: TX('Composição de {g}', { g: nomeGrupo(grupoSel) }),
           cols: [{ k: 'co', t: 'CO_IES' }, { k: 'ies', t: TX('Instituição') }, { k: 'uf', t: 'UF' },
                  { k: 'org', t: TX('Organização') }, { k: 'mant', t: TX('Mantenedora') },
                  { k: 'unidades', t: TX('Unidades') }, { k: 'mat', t: TX('Matrículas') },
                  { k: 'pres', t: TX('Presencial') }, { k: 'ead', t: TX('EAD') },
                  { k: 'tranc', t: TX('Trancados') }, { k: 'base', t: TX('Base de alunos') },
                  { k: 'pctGrupo', t: TX('% do grupo') }] } });

  $('#gl-comp-nota').innerHTML = TX(
    '<strong>{q} IES</strong> somam <strong>{m}</strong> matrículas ({p} presenciais + {e} EAD) ' +
    'em {a}, {s} do mercado. Com os <strong>{tr}</strong> trancados, a <em>base de alunos</em> é ' +
    '<strong>{b}</strong> — taxa de trancamento de {tx}. O Censo cobre apenas graduação: ' +
    'pós, técnico e cursos livres não entram, e é por isso que o número pode divergir do release ' +
    'da companhia. Perímetro pro-forma: IES adquiridas contam no grupo em toda a série. ' +
    'A mantenedora de cada IES vai no CSV.',
    { q: n(compRows.length), m: n(somaC.mat), p: n(somaC.pres), e: n(somaC.ead), a: ano,
      s: pct(tot ? 100 * somaC.mat / tot : 0), tr: n(somaC.tranc), b: n(somaC.base),
      tx: pct(somaC.mat ? 100 * somaC.tranc / somaC.mat : 0) });
}
