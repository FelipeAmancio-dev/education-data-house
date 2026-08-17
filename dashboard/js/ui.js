/* Componentes de UI reaproveitados pelas views: KPI, tabela ordenavel e temas de grafico. */
import { n, pct, deltaHTML } from './dados.js';
import { TX, ehIngles } from './i18n.js';

export const $ = s => document.querySelector(s);
export const $$ = s => [...document.querySelectorAll(s)];
export const esc = s => String(s ?? '').replace(/[&<>"]/g, c =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

/* --------------------------------------------------------------------- KPI */
export function kpi({ rot, val, sub = '', delta = null, sufixo = '%' }) {
  const d = delta == null ? '' : ` ${deltaHTML(delta, sufixo)}`;
  return `<div class="card kpi">
    <div class="rot">${esc(rot)}</div>
    <div class="val">${val}</div>
    <div class="sub">${sub}${d}</div>
  </div>`;
}

/* --------------------------------------------------------------------- CSV
 * Todo dado que aparece na tela precisa sair em CSV: o investidor confere no Excel.
 * Cada view registra seus conjuntos ao renderizar; o botao do bloco lista o que ha.
 * O registro e refeito a cada render, entao trocar filtro/idioma muda o que baixa. */
const csvPorBloco = new Map();

export function limparCSV(bloco) { csvPorBloco.set(bloco, []); }

/* Registra um conjunto para download. Nome repetido SUBSTITUI o anterior.
 *
 * ⚠️ A substituição é o ponto desta função, não um detalhe. O `render()` do app.js chama
 * `limparCSV()` antes de desenhar a view — mas só quando a navegação passa por ele. Todo
 * bloco com controle próprio (chips de período no Price Action, seleção de grupos em Key
 * Players, curso em Cursos, UF e município em Geografia) se redesenha chamando a própria
 * view direto, sem passar pelo `render()`. Sem substituir por nome, cada clique
 * acrescentava mais uma cópia de cada aba: o Excel do Price Action saía com 20 abas em vez
 * de 4 e 15 MB em vez de 1, e a versão boa era a última — quem abrisse a primeira lia o
 * recorte errado. */
export function registrarCSV(bloco, nome, cols, linhas) {
  if (!csvPorBloco.has(bloco)) csvPorBloco.set(bloco, []);
  const lista = csvPorBloco.get(bloco);
  const i = lista.findIndex(c => c.nome === nome);
  const reg = { nome, cols, linhas };
  if (i >= 0) lista[i] = reg; else lista.push(reg);
}
export function conjuntosCSV(bloco) { return csvPorBloco.get(bloco) || []; }

/* Separador `;` e decimal por vírgula em pt: é o que o Excel brasileiro abre sem
 * assistente de importação. Em inglês, vírgula e ponto decimal. BOM para o acento
 * não chegar quebrado no Excel.                                                    */
export function textoCSV(cols, linhas) {
  const en = ehIngles();
  const sep = en ? ',' : ';';
  const cel = v => {
    if (v == null) return '';
    if (typeof v === 'number') {
      const s = Number.isInteger(v) ? String(v) : v.toFixed(2);
      return en ? s : s.replace('.', ',');
    }
    return String(v);
  };
  const esc2 = v => `"${cel(v).replace(/"/g, '""')}"`;
  const cab = cols.map(c => esc2(c.t)).join(sep);
  const corpo = linhas.map(r => cols.map(c => esc2(r[c.k])).join(sep)).join('\r\n');
  return '﻿' + cab + '\r\n' + corpo;
}

export function baixarCSV(nomeArquivo, cols, linhas) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([textoCSV(cols, linhas)], { type: 'text/csv;charset=utf-8' }));
  a.download = nomeArquivo.replace(/[^\w\-]+/g, '_').replace(/^_|_$/g, '') + '.csv';
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}

/* ------------------------------------------------------------------ tabela
 * cols: [{k, t, tipo:'txt'|'num'|'pct'|'barra'|'html', w, fmt}]
 * Ordenavel por clique no cabecalho; estado guardado no proprio elemento.
 * opt.csv = {bloco, nome} registra o conjunto COMPLETO (sem o limite de linhas da
 * tela) para download — quem baixa quer a tabela inteira, não a primeira página.  */
export function tabela(el, cols, dados, opt = {}) {
  if (opt.csv) registrarCSV(opt.csv.bloco, opt.csv.nome, opt.csv.cols || cols, dados);
  const est = el._ord || (el._ord = { k: opt.ordem || cols[1]?.k, asc: false });

  function render() {
    // asc=false significa MAIOR PRIMEIRO (o padrao util num ranking).
    const d = [...dados].sort((a, b) => {
      const x = a[est.k], y = b[est.k];
      if (typeof x === 'string' || typeof y === 'string')
        return (est.asc ? 1 : -1) * String(x ?? '').localeCompare(String(y ?? ''), 'pt-BR');
      return (est.asc ? -1 : 1) * ((y ?? -Infinity) - (x ?? -Infinity));
    });
    const lim = opt.limite ? d.slice(0, opt.limite) : d;
    const maxBarra = {};
    cols.filter(c => c.tipo === 'barra').forEach(c => {
      maxBarra[c.k] = Math.max(...lim.map(r => +r[c.k] || 0), 0.0001);
    });

    const th = cols.map(c => {
      const cls = [c.tipo === 'num' || c.tipo === 'pct' || c.tipo === 'barra' ? 'num' : '',
                   opt.semOrdenacao ? '' : 'sortable',
                   est.k === c.k ? 'sorted' + (est.asc ? ' asc' : '') : ''].filter(Boolean).join(' ');
      return `<th class="${cls}" data-k="${esc(c.k)}"${c.w ? ` style="width:${c.w}"` : ''}>${esc(c.t)}</th>`;
    }).join('');

    const tr = lim.map((r, i) => '<tr>' + cols.map(c => {
      const v = r[c.k];
      if (c.tipo === 'barra') {
        const w = Math.max(0, Math.min(100, 100 * (+v || 0) / maxBarra[c.k]));
        return `<td class="num"><div style="display:flex;align-items:center;gap:8px;justify-content:flex-end">
          <span>${c.fmt ? c.fmt(v, r, i) : pct(v)}</span>
          <div class="barra" style="width:52px"><i style="width:${w}%"></i></div></div></td>`;
      }
      const txt = c.fmt ? c.fmt(v, r, i)
        : c.tipo === 'num' ? n(v) : c.tipo === 'pct' ? pct(v) : esc(v);
      const cls = c.tipo === 'num' || c.tipo === 'pct' ? 'num' : (c.tipo === 'txt' ? 'nome' : '');
      return `<td class="${cls}">${txt}</td>`;
    }).join('') + '</tr>').join('');

    el.innerHTML = `<div class="tw"><table><thead><tr>${th}</tr></thead><tbody>${tr ||
      `<tr><td colspan="${cols.length}" class="vazio">Sem dados para os filtros selecionados</td></tr>`
      }</tbody></table></div>`;

    if (!opt.semOrdenacao) {
      el.querySelectorAll('th.sortable').forEach(h => h.onclick = () => {
        const k = h.dataset.k;
        if (est.k === k) est.asc = !est.asc; else { est.k = k; est.asc = false; }
        render();
      });
    }
  }
  render();
}

/* -------------------------------------------------------------- seletores
 * Repopula um <select> apenas quando a lista muda de verdade, preservando a escolha
 * do usuario. Popular "uma vez so" nao serve: uma lista derivada do detalhe do ano
 * pode vir vazia num ano sem detalhe e ficar travada vazia para sempre.
 * itens: [{v, t}] · devolve o valor selecionado.                                  */
export function opcoes(el, itens, aoMudar) {
  const sig = itens.map(i => i.v).join('|');
  if (el.dataset.sig !== sig) {
    const atual = el.value;
    el.innerHTML = itens.map(i => `<option value="${esc(i.v)}">${esc(i.t)}</option>`).join('');
    el.dataset.sig = sig;
    if (itens.some(i => String(i.v) === atual)) el.value = atual;
  }
  if (aoMudar && !el.dataset.lig) { el.onchange = aoMudar; el.dataset.lig = '1'; }
  return el.value;
}

/* ------------------------------------------------------------------ charts
 * Paleta Itaú: laranja como acento principal, azul-marinho como contraponto,
 * e tons intermediários para séries categóricas. Duas famílias de matiz mantêm
 * as séries distinguíveis mesmo em escala de cinza.                             */
export const LARANJA = '#EC7000';
export const AZUL = '#003C7D';
export const PALETA = ['#EC7000', '#003C7D', '#F2A25C', '#4A7FB5', '#A34B00', '#8FB4D9', '#6E7B87'];
export const COR_PRES = '#003C7D';   // presencial = azul (estrutura instalada)
export const COR_EAD = '#EC7000';    // EAD = laranja (o que está crescendo)

export function baseChart() {
  return {
    color: PALETA,
    grid: { left: 8, right: 16, top: 28, bottom: 6, containLabel: true },
    textStyle: { fontFamily: '-apple-system, "Segoe UI", Roboto, sans-serif', color: '#4A4A4A' },
    tooltip: {
      trigger: 'axis', backgroundColor: '#fff', borderColor: '#D2D4D8', borderWidth: 1,
      padding: [9, 12], textStyle: { color: '#1A1A1A', fontSize: 12.5 },
      extraCssText: 'box-shadow:0 4px 14px rgba(0,0,0,.10);border-radius:8px',
      axisPointer: { type: 'line', lineStyle: { color: '#D2D4D8' } },
    },
    legend: { top: 0, right: 0, itemWidth: 10, itemHeight: 10, itemGap: 14, icon: 'roundRect',
              textStyle: { fontSize: 11.5, color: '#4A4A4A' } },
    xAxis: { type: 'category', axisLine: { lineStyle: { color: '#E8E8E8' } },
             axisTick: { show: false }, axisLabel: { fontSize: 11.5, color: '#8C8C8C' } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: '#F2F3F5' } },
             axisLine: { show: false }, axisTick: { show: false },
             axisLabel: { fontSize: 11.5, color: '#8C8C8C' } },
  };
}

/* Cor estável por grupo: usa a cor do config quando houver, senão cai na paleta. */
export function corGrupo(chave, ordem, cfg) {
  return (cfg && cfg[chave] && cfg[chave].cor) || PALETA[ordem % PALETA.length];
}

const _charts = new Map();
export function chart(el, opt) {
  if (!el) return null;
  let c = _charts.get(el);
  if (!c || c.isDisposed?.()) { c = echarts.init(el, null, { renderer: 'canvas' }); _charts.set(el, c); }
  c.setOption(opt, true);
  return c;
}
export function resizeCharts() { _charts.forEach(c => { try { c.resize(); } catch (e) { /* ok */ } }); }
window.addEventListener('resize', () => { clearTimeout(window._rt); window._rt = setTimeout(resizeCharts, 120); });

export function fmtEixoMi(v) {
  if (Math.abs(v) >= 1e6) return (v / 1e6).toFixed(1).replace('.', ',') + ' mi';
  if (Math.abs(v) >= 1e3) return Math.round(v / 1e3) + 'k';
  return v;
}
