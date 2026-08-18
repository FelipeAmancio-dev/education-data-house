/* Investor Snapshot — a página objetiva do setor, pensada para virar material de
 * apresentação: tamanho, de onde veio o crescimento, quem ganha share, o que cresce em
 * curso e em praça.
 *
 * ⚠️ REGRA QUE DESENHOU ESTE BLOCO: não repetir gráfico que já existe em outro lugar.
 * O Overview já responde "qual o tamanho do mercado" com KPIs de YoY, a série por
 * modalidade, o mix por área e a tabela dos maiores grupos; o Key Players já compara
 * players escolhidos a dedo. Se o Snapshot repetisse essas peças, seria uma cópia com
 * outro nome — e duas telas com o mesmo número são duas telas que podem discordar.
 *
 * O recorte daqui é outro, e é o que um investidor pede primeiro:
 *   1. os números da DÉCADA, não do ano contra o anterior (o Overview faz o YoY);
 *   2. a ATRIBUIÇÃO do crescimento — qual segmento entregou os alunos que entraram;
 *   3. o MOVIMENTO de share entre grupos, não o ranking de tamanho;
 *   4. o que cresce em CURSO e em PRAÇA, com piso de base declarado.
 *
 * Tudo sai dos cubos do CORE (`c_ies_mod`, `c_cine_mod`, `c_mun_mod`), que trazem os 10
 * anos. Nenhuma seção depende do detalhe por ano — de propósito: é o que faz o bloco
 * funcionar inteiro no arquivo único e no artifact, as duas versões que ninguém testa por
 * hábito (ver docs/00_HANDOFF.md §6.5).
 */
import {
  D, porIES, serieIES, totalAno, kpiAno,
  gr, redeIES, nomeCurso, ufMun,
  n, pct, compacto, deltaHTML,
} from './dados.js';
import { $, esc, kpi, tabela, chart, baseChart, registrarCSV,
         LARANJA, AZUL, COR_PRES, COR_EAD } from './ui.js';
import { TX, TXcurso, locale } from './i18n.js';

/* ⚠️ Número segue o idioma, inclusive dentro do gráfico: 0,88 em pt e 0.88 em en.
 * `toFixed()` cru escreve ponto decimal sempre, e o eixo saía com ponto no meio de uma
 * tela que usa vírgula em todo o resto — a mesma regra que vale para o CSV. */
const snPP = v => (v == null || isNaN(v)) ? '—'
  : v.toLocaleString(locale(), { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const snNome = k => D.gruposOrd[k]?.nome || k;

/* ⚠️ Mesmo limiar do gate de validação (`scripts/03_validate.py` §5b): 12 p.p. de
 * divergência entre o YoY de `QT_MAT` e o YoY da base de alunos (QT_MAT + trancados)
 * denunciam RECLASSIFICAÇÃO DE VÍNCULO, não aluno entrando ou saindo. Ser Educacional em
 * 2022 e Ânima em 2023 são os casos conhecidos. O número tem que ser o mesmo do pipeline:
 * a ferramenta não pode marcar na tela um ano que o validador deixa passar. */
const SN_DIVERG = 12;

/* Piso de base para as tabelas de crescimento. Sem piso, o topo do ranking vira curso de
 * 300 alunos que dobrou — matematicamente correto e analiticamente inútil. O piso é
 * declarado na nota junto com quanto do mercado ele cobre, para o leitor saber o que
 * ficou de fora. */
const SN_PISO_CURSO = 50000;
const SN_PISO_UF = 40000;

const snCagr = (fim, ini, anos) =>
  (ini > 0 && fim > 0 && anos > 0) ? (Math.pow(fim / ini, 1 / anos) - 1) * 100 : null;

export function snapshot(f) {
  const ano = f.ano;
  const prev = ano - 1;
  const anos = D.meta.anos;
  const base = anos[0];
  const nAnos = ano - base;
  const k = kpiAno(ano), kp = kpiAno(prev), kb = kpiAno(base);
  const d = (a, b) => (b && b > 0) ? 100 * (a - b) / b : null;

  /* ============================================================ 1) a década ===
   * ⚠️ Estes KPIs são de DÉCADA (contra {base}), não de YoY. O Overview já mostra o ano
   * contra o anterior; repetir aqui seria a mesma tela duas vezes. A pergunta deste
   * bloco é "o que aconteceu com o setor no período", que é a que abre apresentação. */
  const dEad = k.mat_ead - (kb?.mat_ead ?? 0);
  const dPres = k.mat_presencial - (kb?.mat_presencial ?? 0);
  const dTot = k.mat_total - (kb?.mat_total ?? 0);

  $('#sn-kpis').innerHTML = [
    kpi({ rot: TX('Matrículas'), val: compacto(k.mat_total),
          sub: TX('vs {a}', { a: prev }), delta: d(k.mat_total, kp?.mat_total) }),
    kpi({ rot: TX('CAGR {i}–{f}', { i: base, f: ano }),
          val: pct(snCagr(k.mat_total, kb?.mat_total, nAnos)),
          sub: TX('ao ano, em matrículas') }),
    kpi({ rot: TX('EAD'), val: pct(100 * k.mat_ead / k.mat_total),
          sub: TX('era {v} em {a}', { v: pct(100 * (kb?.mat_ead ?? 0) / (kb?.mat_total || 1)), a: base }),
          delta: kb ? (100 * k.mat_ead / k.mat_total) - (100 * kb.mat_ead / kb.mat_total) : null,
          sufixo: ' p.p.' }),
    kpi({ rot: TX('Rede privada'), val: pct(100 * k.mat_privada / k.mat_total),
          sub: TX('era {v} em {a}', { v: pct(100 * (kb?.mat_privada ?? 0) / (kb?.mat_total || 1)), a: base }),
          delta: kb ? (100 * k.mat_privada / k.mat_total) - (100 * kb.mat_privada / kb.mat_total) : null,
          sufixo: ' p.p.' }),
  ].join('');

  $('#sn-kpis2').innerHTML = [
    kpi({ rot: TX('Alunos a mais desde {a}', { a: base }), val: compacto(dTot),
          sub: TX('{p} em {n} anos', { p: pct(100 * dTot / (kb?.mat_total || 1)), n: nAnos }) }),
    kpi({ rot: TX('EAD — variação'), val: (dEad >= 0 ? '+' : '') + compacto(dEad),
          sub: TX('alunos desde {a}', { a: base }) }),
    kpi({ rot: TX('Presencial — variação'), val: (dPres >= 0 ? '+' : '') + compacto(dPres),
          sub: TX('alunos desde {a}', { a: base }) }),
    kpi({ rot: TX('IES ativas'), val: n(k.ies), sub: TX('vs {a}', { a: prev }),
          delta: d(k.ies, kp?.ies) }),
  ].join('');

  registrarCSV('snapshot', TX('Indicadores do setor'),
    [{ k: 'ind', t: TX('Indicador') }, { k: 'ini', t: String(base) }, { k: 'fim', t: String(ano) }],
    [{ ind: TX('Matrículas'), ini: kb?.mat_total ?? null, fim: k.mat_total },
     { ind: TX('Presencial'), ini: kb?.mat_presencial ?? null, fim: k.mat_presencial },
     { ind: TX('EAD'), ini: kb?.mat_ead ?? null, fim: k.mat_ead },
     { ind: TX('Rede privada'), ini: kb?.mat_privada ?? null, fim: k.mat_privada },
     { ind: TX('Rede pública'), ini: kb?.mat_publica ?? null, fim: k.mat_publica },
     { ind: TX('Ingressantes'), ini: kb?.ingressantes ?? null, fim: k.ingressantes },
     { ind: TX('Concluintes'), ini: kb?.concluintes ?? null, fim: k.concluintes },
     { ind: 'IES', ini: kb?.ies ?? null, fim: k.ies }]);

  /* ================================================ 2) de onde veio o aluno ===
   * A leitura que o agregado esconde: o setor cresceu ~2,2 milhões na década, mas o EAD
   * privado entregou ~3,7 milhões e o presencial privado DEVOLVEU ~1,6 milhão. Quem olha
   * só o total conclui "o setor cresce 2,7% ao ano" e perde a troca de composição, que é
   * onde está a tese.
   *
   * Sai do mesmo cubo `c_ies_mod` dos demais blocos (soma 10.227.266 em 2024, o número de
   * referência), com a rede vindo da dimensão de IES. */
  const segChave = ix => (redeIES(ix) === 1 ? 'pub' : 'priv');
  const sSeg = serieIES(segChave, {});
  const seg = (rede, campo, a) => sSeg.get(rede)?.[a]?.[campo] ?? 0;
  const SEGS = [
    { id: 'priv-ead', rot: TX('Privada · EAD'), rede: 'priv', campo: 'ead', cor: COR_EAD },
    { id: 'priv-pres', rot: TX('Privada · presencial'), rede: 'priv', campo: 'pres', cor: COR_PRES },
    { id: 'pub-ead', rot: TX('Pública · EAD'), rede: 'pub', campo: 'ead', cor: '#F2A25C' },
    { id: 'pub-pres', rot: TX('Pública · presencial'), rede: 'pub', campo: 'pres', cor: '#8FB4D9' },
  ];
  const segRows = SEGS.map(s => {
    const ini = seg(s.rede, s.campo, base), fim = seg(s.rede, s.campo, ano);
    return { seg: s.rot, cor: s.cor, ini, fim, delta: fim - ini,
             cagr: snCagr(fim, ini, nAnos), peso: fim };
  }).sort((a, b) => b.delta - a.delta);

  chart($('#sn-cresc'), {
    ...baseChart(),
    legend: { show: false },
    grid: { left: 8, right: 60, top: 10, bottom: 6, containLabel: true },
    xAxis: { type: 'value', splitLine: { lineStyle: { color: '#F2F3F5' } },
             axisLine: { show: false }, axisTick: { show: false },
             axisLabel: { fontSize: 11.5, color: '#8C8C8C',
                          formatter: v => (v >= 0 ? '+' : '') + compacto(v) } },
    yAxis: { type: 'category', data: segRows.map(r => r.seg).reverse(),
             axisTick: { show: false }, axisLine: { show: false },
             axisLabel: { fontSize: 11.5, color: '#4A4A4A' } },
    series: [{
      type: 'bar', barMaxWidth: 26,
      data: segRows.map(r => ({ value: r.delta, itemStyle: { color: r.cor } })).reverse(),
      label: { show: true, position: 'right', fontSize: 11, color: '#4A4A4A',
               formatter: p => (p.value >= 0 ? '+' : '') + compacto(p.value) },
    }],
    tooltip: { ...baseChart().tooltip, trigger: 'item',
               valueFormatter: v => (v >= 0 ? '+' : '') + n(v) },
  });

  $('#sn-cresc-tit').textContent =
    TX('De onde vieram os alunos — {i} a {f}', { i: base, f: ano });
  $('#sn-cresc-nota').innerHTML = TX(
    'Variação absoluta de matrículas por segmento entre {i} e {f}. O setor ganhou ' +
    '<strong>{t}</strong> alunos no período, mas o EAD privado sozinho entregou ' +
    '<strong>{e}</strong> enquanto o presencial privado devolveu <strong>{p}</strong> — ' +
    'quem lê só o total não vê a troca de composição, que é onde está a tese. ' +
    'Denominador: matrículas do Brasil, todas as redes ({d} em {f}).',
    { i: base, f: ano, t: compacto(dTot),
      e: compacto(segRows.find(r => r.seg === TX('Privada · EAD'))?.delta ?? 0),
      p: compacto(Math.abs(segRows.find(r => r.seg === TX('Privada · presencial'))?.delta ?? 0)),
      d: n(k.mat_total) });

  registrarCSV('snapshot', TX('Crescimento por segmento'),
    [{ k: 'seg', t: TX('Segmento') }, { k: 'ini', t: String(base) }, { k: 'fim', t: String(ano) },
     { k: 'delta', t: TX('Variação') }, { k: 'cagr', t: TX('CAGR (%)') }],
    segRows.map(r => ({ seg: r.seg, ini: r.ini, fim: r.fim, delta: r.delta,
                        cagr: r.cagr == null ? null : +r.cagr.toFixed(2) })));

  /* ================================================== 3) movimento de share ===
   * ⚠️ NÃO é o ranking de tamanho — esse já está no Overview ("Maiores grupos"). Aqui a
   * pergunta é quem GANHOU e quem PERDEU praça no último ano.
   *
   * ⚠️ "Independentes" é bucket residual de IES não mapeada, não um player: fica fora do
   * ranking e aparece só na nota, com o peso dele. Incluí-lo faria o maior "ganhador" ou
   * "perdedor" da tela ser um agregado de milhares de instituições sem relação entre si.
   *
   * ⚠️ E a tabela mostra as DUAS séries de crescimento — `QT_MAT` e base de alunos
   * (QT_MAT + trancados) —, não uma. Quando as duas andam em direções diferentes o
   * movimento é reclassificação de vínculo, e o hand-off é explícito: não gerar insight de
   * crescimento nesses anos sem mostrar as duas. Divergência acima de SN_DIVERG marca a
   * linha e entra na nota. */
  const fc = { ...f, grupo: '' };            // share nunca filtra por grupo
  const g = porIES(ano, gr, fc), gp = porIES(prev, gr, fc);
  const tot = totalAno(ano, fc), totP = totalAno(prev, fc);
  const indep = g.get('Independentes');

  const movRows = [...g.keys()].filter(x => x && x !== 'Independentes').map(kg => {
    const v = g.get(kg), p = gp.get(kg);
    const share = tot ? 100 * v.mat / tot : 0;
    const shareP = (p && totP) ? 100 * p.mat / totP : null;
    const yoy = (p && p.mat) ? 100 * (v.mat - p.mat) / p.mat : null;
    const baseAt = v.mat + v.tranc, baseAnt = p ? p.mat + p.tranc : 0;
    const yoyBase = baseAnt > 0 ? 100 * (baseAt - baseAnt) / baseAnt : null;
    const diverg = (yoy != null && yoyBase != null) ? Math.abs(yoy - yoyBase) : null;
    return {
      grupo: snNome(kg), _raw: kg, ticker: D.gruposOrd[kg]?.ticker || '',
      mat: v.mat, share, dShare: shareP == null ? null : share - shareP,
      yoy, yoyBase, pctEad: v.mat ? 100 * v.ead / v.mat : 0,
      _alerta: diverg != null && diverg > SN_DIVERG,
    };
  }).filter(r => r.mat > 0);

  const contaminados = movRows.filter(r => r._alerta);
  const movOrd = [...movRows].sort((a, b) => (b.dShare ?? -99) - (a.dShare ?? -99));
  const topMov = [...movOrd.slice(0, 6), ...movOrd.slice(-6)]
    .filter((r, i, arr) => arr.findIndex(x => x._raw === r._raw) === i)
    .sort((a, b) => (a.dShare ?? 0) - (b.dShare ?? 0));

  chart($('#sn-share'), {
    ...baseChart(),
    legend: { show: false },
    grid: { left: 8, right: 56, top: 10, bottom: 6, containLabel: true },
    xAxis: { type: 'value', splitLine: { lineStyle: { color: '#F2F3F5' } },
             axisLine: { show: false }, axisTick: { show: false },
             axisLabel: { fontSize: 11.5, color: '#8C8C8C',
                          formatter: v => (v > 0 ? '+' : '') + snPP(v) } },
    yAxis: { type: 'category', data: topMov.map(r => r.grupo),
             axisTick: { show: false }, axisLine: { show: false },
             axisLabel: { fontSize: 11.5, color: '#4A4A4A' } },
    series: [{
      type: 'bar', barMaxWidth: 20,
      // laranja ganha praça, azul devolve — as duas famílias de matiz da paleta, que
      // continuam distinguíveis em escala de cinza
      data: topMov.map(r => ({ value: r.dShare == null ? 0 : +r.dShare.toFixed(3),
                               itemStyle: { color: (r.dShare ?? 0) >= 0 ? LARANJA : AZUL } })),
      label: { show: true, position: 'right', fontSize: 11, color: '#4A4A4A',
               formatter: p => (p.value > 0 ? '+' : '') + snPP(p.value) },
    }],
    tooltip: { ...baseChart().tooltip, trigger: 'item',
               valueFormatter: v => (v > 0 ? '+' : '') + snPP(v) + ' p.p.' },
  });
  $('#sn-share-tit').textContent =
    TX('Quem ganhou e quem perdeu share — {p} a {a}', { p: prev, a: ano });

  tabela($('#sn-share-tab'), [
    { k: 'grupo', t: TX('Grupo'), tipo: 'txt', fmt: (v, r) =>
        `${esc(v)}${r.ticker ? ` <span class="tag lst">${esc(r.ticker)}</span>` : ''}` +
        `${r._alerta ? ' <span class="tag" title="' +
          esc(TX('QT_MAT e base de alunos divergem mais de {v} p.p. neste ano', { v: SN_DIVERG })) +
          '">⚠</span>' : ''}` },
    { k: 'mat', t: TX('Matrículas'), tipo: 'num' },
    { k: 'share', t: TX('Share'), tipo: 'barra' },
    { k: 'dShare', t: TX('Δ Share vs {a}', { a: prev }), tipo: 'num',
      fmt: v => v == null ? '—' : deltaHTML(v, ' p.p.') },
    { k: 'yoy', t: TX('YoY matrículas'), tipo: 'num', fmt: v => deltaHTML(v) },
    { k: 'yoyBase', t: TX('YoY base de alunos'), tipo: 'num', fmt: v => deltaHTML(v) },
    { k: 'pctEad', t: TX('% EAD'), tipo: 'pct' },
  /* ⚠️ Ordena por TAMANHO e corta em 15, e as duas decisões são deliberadas.
   *
   * Por Δ share, os 15 primeiros seriam só ganhadores — o leitor veria metade do movimento
   * e concluiria que ninguém perdeu praça. Quem se moveu mais já está no gráfico ao lado,
   * nas duas pontas; aqui a pergunta é como os grandes se mexeram.
   *
   * E o corte é só de EXIBIÇÃO: `opt.limite` recorta a tela, o `tabela()` recebe o array
   * inteiro e é ele que vai para o Excel. Passar `.slice()` aqui já derrubou o CSV de
   * "todas as IES" para 25 linhas uma vez. */
  ], movRows, { ordem: 'mat', limite: 15,
                csv: { bloco: 'snapshot', nome: TX('Movimento de market share') } });

  $('#sn-share-nota').innerHTML = TX(
    'Denominador: matrículas do Brasil em {a} — {t}. Consolidação por grupo econômico em ' +
    'perímetro <strong>pro-forma</strong>: uma IES adquirida em 2022 conta no grupo comprador ' +
    'desde {i}, o que permite ler share sem degrau de M&amp;A — mas não é o que cada empresa ' +
    'reportava à época. <em>Base de alunos</em> = matrículas + trancados, que é a definição ' +
    'que as companhias divulgam; as duas colunas aparecem juntas de propósito. Fora do ' +
    'ranking, {p} do mercado ({m} matrículas) está em instituições não mapeadas em grupo — ' +
    'bucket residual, não um player. Os 15 maiores na tela, todos os {q} grupos no Excel — ' +
    'ordene por qualquer coluna.',
    { a: ano, t: n(tot), i: base, q: n(movRows.length),
      p: pct(100 * (indep?.mat || 0) / (tot || 1)), m: n(indep?.mat || 0) })
    + (contaminados.length ? '<br><br>⚠️ ' + TX(
        '<strong>{g}</strong>: matrículas e base de alunos divergem mais de {v} p.p. em {a}. ' +
        'O movimento aí é <strong>reclassificação de vínculo</strong> — trancado que virou ' +
        'ativo, ou o contrário —, não aluno entrando ou saindo. Leia as duas colunas juntas.',
        { g: contaminados.map(r => r.grupo).join(', '), v: SN_DIVERG, a: ano }) : '');

  /* ======================================================= 4) o que cresce ====
   * Curso e praça, com piso de base declarado nas duas tabelas.
   *
   * Os dois cubos são NACIONAIS e trazem os 10 anos no CORE — nenhuma chamada de detalhe
   * por ano, que é o que faz este bloco funcionar inteiro no arquivo único. */
  const anoIni = anos.includes(ano - 5) ? ano - 5 : base;
  const janela = ano - anoIni;

  // -------------------------------------------------------------- cursos
  const cin = D.cineMod;
  const curAgg = new Map();          // cur -> {ini, fim, prev, ead}
  for (let i = 0; i < cin.n; i++) {
    const a = cin.ano[i];
    if (a !== ano && a !== prev && a !== anoIni) continue;
    const c = cin.cur[i];
    let o = curAgg.get(c);
    if (!o) { o = { ini: 0, fim: 0, ant: 0, ead: 0 }; curAgg.set(c, o); }
    if (a === anoIni) o.ini += cin.qt_mat[i];
    if (a === prev) o.ant += cin.qt_mat[i];
    if (a === ano) { o.fim += cin.qt_mat[i]; if (cin.mod[i] !== 1) o.ead += cin.qt_mat[i]; }
  }
  const totCurso = [...curAgg.values()].reduce((s, o) => s + o.fim, 0);
  const cursoRows = [...curAgg.entries()]
    .filter(([, o]) => o.fim >= SN_PISO_CURSO)
    .map(([c, o]) => ({
      curso: TXcurso(nomeCurso(c)), mat: o.fim,
      yoy: o.ant > 0 ? 100 * (o.fim - o.ant) / o.ant : null,
      cagr: snCagr(o.fim, o.ini, janela),
      pctEad: o.fim ? 100 * o.ead / o.fim : 0,
      share: totCurso ? 100 * o.fim / totCurso : 0,
    }));
  const cobCurso = cursoRows.reduce((s, r) => s + r.mat, 0);

  tabela($('#sn-cursos'), [
    { k: 'curso', t: TX('Curso'), tipo: 'txt' },
    { k: 'mat', t: TX('Matrículas'), tipo: 'num' },
    { k: 'cagr', t: TX('CAGR {i}–{f}', { i: anoIni, f: ano }), tipo: 'num',
      fmt: v => deltaHTML(v) },
    { k: 'yoy', t: TX('YoY vs {a}', { a: prev }), tipo: 'num', fmt: v => deltaHTML(v) },
    { k: 'pctEad', t: TX('% EAD'), tipo: 'pct' },
  ], cursoRows, { ordem: 'cagr', limite: 15,
                  csv: { bloco: 'snapshot', nome: TX('Crescimento por curso') } });

  $('#sn-cursos-tit').textContent = TX('Cursos que mais crescem — {i} a {f}', { i: anoIni, f: ano });
  $('#sn-cursos-nota').innerHTML = TX(
    'Rótulos CINE com pelo menos <strong>{piso}</strong> matrículas em {a} — {q} cursos, ' +
    '{cob} do total do país. O piso é o que impede o topo do ranking de virar curso pequeno ' +
    'que dobrou de tamanho: matematicamente correto e analiticamente inútil. 15 na tela, ' +
    'todos os {q} no Excel. Ordene por qualquer coluna.',
    { piso: n(SN_PISO_CURSO), a: ano, q: n(cursoRows.length),
      cob: pct(100 * cobCurso / (totCurso || 1)) });

  // ------------------------------------------------------------------ UF
  const mn = D.munMod;
  const ufAgg = new Map();
  for (let i = 0; i < mn.n; i++) {
    const a = mn.ano[i];
    if (a !== ano && a !== prev && a !== anoIni) continue;
    const u = ufMun(mn.mun[i]);
    if (!u) continue;
    let o = ufAgg.get(u);
    if (!o) { o = { ini: 0, fim: 0, ant: 0, ead: 0 }; ufAgg.set(u, o); }
    if (a === anoIni) o.ini += mn.qt_mat[i];
    if (a === prev) o.ant += mn.qt_mat[i];
    if (a === ano) { o.fim += mn.qt_mat[i]; if (mn.mod[i] !== 1) o.ead += mn.qt_mat[i]; }
  }
  const totUF = [...ufAgg.values()].reduce((s, o) => s + o.fim, 0);
  const ufRows = [...ufAgg.entries()]
    .filter(([, o]) => o.fim >= SN_PISO_UF)
    .map(([u, o]) => ({
      uf: u, mat: o.fim,
      yoy: o.ant > 0 ? 100 * (o.fim - o.ant) / o.ant : null,
      cagr: snCagr(o.fim, o.ini, janela),
      pctEad: o.fim ? 100 * o.ead / o.fim : 0,
      share: totUF ? 100 * o.fim / totUF : 0,
    }));

  tabela($('#sn-uf'), [
    { k: 'uf', t: 'UF', tipo: 'txt' },
    { k: 'mat', t: TX('Matrículas'), tipo: 'num' },
    { k: 'share', t: TX('Share'), tipo: 'barra' },
    { k: 'cagr', t: TX('CAGR {i}–{f}', { i: anoIni, f: ano }), tipo: 'num',
      fmt: v => deltaHTML(v) },
    { k: 'yoy', t: TX('YoY vs {a}', { a: prev }), tipo: 'num', fmt: v => deltaHTML(v) },
    { k: 'pctEad', t: TX('% EAD'), tipo: 'pct' },
  ], ufRows, { ordem: 'cagr', limite: 15,
               csv: { bloco: 'snapshot', nome: TX('Crescimento por UF') } });

  $('#sn-uf-tit').textContent = TX('Onde o setor cresce — {i} a {f}', { i: anoIni, f: ano });
  /* ⚠️ A nota abaixo não é enfeite. Esta é a ÚNICA definição de UF do dashboard que diz
   * onde o aluno está: vem do cubo por município de OFERTA (dimensões 1 e 2). Nos demais
   * blocos a UF é o endereço da SEDE da IES, e no EAD isso põe 836 mil alunos da Unopar
   * no Paraná. Duas definições diferentes com o mesmo rótulo "UF" é exatamente o tipo de
   * coisa que faz um investidor tirar a conclusão errada sem perceber. */
  $('#sn-uf-nota').innerHTML = TX(
    'UF de <strong>oferta</strong> — onde o aluno está —, do cubo por município ' +
    '(dimensões 1 e 2 do Censo). <strong>Não confunda com a UF da sede da IES</strong>, que ' +
    'é o que os demais blocos usam: no EAD a matrícula é lançada na sede, e por isso a ' +
    'Unopar aparece 100% no Paraná com polo no país inteiro. UFs com pelo menos {piso} ' +
    'matrículas em {a}; 15 na tela, todas no Excel. Denominador: {t} matrículas com ' +
    'município identificado.',
    { piso: n(SN_PISO_UF), a: ano, t: n(totUF) });
}
