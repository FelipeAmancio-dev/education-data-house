/* Camada de dados: carrega os JSON colunares e oferece agregacao em memoria.
 *
 * Principio (docs/03_arquitetura.md): os cubos vem no nivel de IES; grupo, UF, regiao e
 * area CINE sao derivados aqui no navegador. E por isso que editar o mapeamento de
 * grupos nao exige reprocessar os microdados.
 */
import { locale, ehIngles } from './i18n.js';

export const D = {
  meta: null, dim: null, precos: null,
  iesMod: null, cineMod: null, munMod: null, iesAno: null,
  detalhe: {},          // {ano: {iesCine, iesMun}}
  _ixIES: null, _ixCur: null, _ixMun: null,
};

/* Le um JSON. Na versao standalone os dados vem embutidos em window.__EMBED e nao
 * ha rede envolvida; servido normalmente, cai no fetch. Mesmo caminho de codigo. */
async function json(url) {
  if (window.__EMBED && window.__EMBED[url] !== undefined) return window.__EMBED[url];
  const r = await fetch(url);
  if (!r.ok) throw new Error(`Falha ao carregar ${url} (${r.status})`);
  return r.json();
}

/* Converte JSON colunar em array de linhas-objeto so quando necessario.
 * Na maior parte dos casos operamos direto nas colunas, que e mais rapido. */
export function linhas(c) {
  const out = new Array(c.n);
  for (let i = 0; i < c.n; i++) {
    const o = {};
    for (const k of c.cols) o[k] = c[k][i];
    out[i] = o;
  }
  return out;
}

export async function carregar() {
  const [meta, dim, iesMod, cineMod, munMod, iesAno] = await Promise.all([
    json('data/meta.json'), json('data/dim.json'),
    json('data/c_ies_mod.json'), json('data/c_cine_mod.json'),
    json('data/c_mun_mod.json'), json('data/c_ies_ano.json'),
  ]);
  Object.assign(D, { meta, dim, iesMod, cineMod, munMod, iesAno });

  // indices auxiliares
  D.gruposOrd = {};
  (dim.grupos.GRUPO || []).forEach((g, i) => {
    D.gruposOrd[g] = { nome: dim.grupos.NOME_EXIBICAO[i] || g, tipo: dim.grupos.TIPO[i] || '',
                       cor: dim.grupos.COR[i] || '', ordem: +dim.grupos.ORDEM[i] || 99,
                       ticker: dim.grupos.TICKER[i] || '' };
  });
  D.ufs = [...new Set(dim.mun.uf)].filter(Boolean).sort();
  D.regioes = [...new Set(dim.mun.regiao)].filter(Boolean).sort();
  D.gruposLista = [...new Set(dim.ies.grupo)].filter(Boolean)
    .sort((a, b) => (D.gruposOrd[a]?.ordem ?? 99) - (D.gruposOrd[b]?.ordem ?? 99) || a.localeCompare(b));
  return D;
}

const CUBO_VAZIO = { n: 0, cols: [], ies: [], cur: [], mun: [], mod: [], qt_mat: [], qt_ing: [], qt_conc: [] };

/* Carrega o detalhe do ano (IES x curso e IES x municipio).
 * Na versao standalone so o ano mais recente vem embutido: nesse caso devolve cubos
 * vazios com `parcial: true`, e as secoes que dependem do detalhe avisam em vez de quebrar. */
export async function carregarAno(ano) {
  if (D.detalhe[ano]) return D.detalhe[ano];
  try {
    const [iesCine, iesMun] = await Promise.all([
      json(`data/ano/${ano}_ies_cine.json`), json(`data/ano/${ano}_ies_mun.json`),
    ]);
    D.detalhe[ano] = { iesCine, iesMun, parcial: false };
  } catch (e) {
    console.warn(`Detalhe de ${ano} indisponível nesta versão`, e);
    D.detalhe[ano] = { iesCine: CUBO_VAZIO, iesMun: CUBO_VAZIO, parcial: true };
  }
  return D.detalhe[ano];
}

/* Precos das acoes do setor (bloco Price Action). Carrega sob demanda: e o unico
 * dado que envelhece em horas, e nem todo uso do dashboard passa por ele. */
export async function carregarPrecos() {
  if (D.precos) return D.precos;
  try {
    D.precos = await json('data/precos.json');
  } catch (e) {
    console.warn('precos.json indisponível', e);
    D.precos = null;
  }
  return D.precos;
}

/* Mensalidades praticadas pelas faculdades das companhias abertas (bloco Mensalidades),
 * geradas por `scripts/07_fetch_mensalidades.py`. Sob demanda pelo mesmo motivo dos
 * precos: e um dado a parte do Censo, e nem toda sessao passa por ele. Ausente, o bloco
 * avisa em vez de quebrar — a coleta pode nao ter rodado nesta copia.                  */
export async function carregarMensalidades() {
  if (D.mensalidades) return D.mensalidades;
  try {
    D.mensalidades = await json('data/mensalidades.json');
  } catch (e) {
    console.warn('mensalidades.json indisponível', e);
    D.mensalidades = null;
  }
  return D.mensalidades;
}

/* Base do modulo Ambiente Regulatorio, gerada por scripts/08_build_regulatorio.py. */
export async function carregarRegulatorio() {
  if (D.regulatorio) return D.regulatorio;
  try {
    D.regulatorio = await json('data/regulatorio.json');
  } catch (e) {
    console.warn('regulatorio.json indisponível', e);
    D.regulatorio = null;
  }
  return D.regulatorio;
}

/* Feed diário do DOU — o que o MEC publicou na Seção 1, com relevância atribuída por
 * regra determinística. Gerado por `scripts/11_fetch_dou_diario.py`.
 *
 * ⚠️ Este dado NÃO passou por curadoria, e a diferença importa: as abas de tema do
 * Ambiente Regulatório mostram o que alguém conferiu no DOU e escreveu; esta mostra o que
 * o Ministério publicou, como publicou. A tela diz isso.                              */
export async function carregarDouDiario() {
  if (D.douDiario !== undefined) return D.douDiario;
  try {
    D.douDiario = await json('data/dou_diario.json');
  } catch (e) {
    console.warn('dou_diario.json indisponível', e);
    D.douDiario = null;
  }
  return D.douDiario;
}

/* Atributos do e-MEC por IES (IGC, CI, CI-EaD, sinalizações vigentes, credenciamento),
 * gerados por `scripts/10_ingest_emec.py` a partir de `Dados_GEO.xlsx`.
 *
 * ⚠️ Indexado pela POSIÇÃO em `dim.ies`, igual aos cubos — `D.emec.igc[ix]` é o IGC da
 * IES de índice `ix`. Quem não casou fica com string vazia, que significa SEM INFORMAÇÃO
 * e não nota zero: 2.636 das IES casaram, cobrindo 99,9% das matrículas de 2024, mas a
 * contagem de IES sem par é grande porque o e-MEC só lista instituição ativa.
 *
 * Sob demanda pelo mesmo motivo dos preços: é dado de fora do Censo, e nem toda sessão
 * passa por ele. Ausente, a seção de qualidade avisa em vez de quebrar.               */
export async function carregarEmec() {
  if (D.emec !== undefined) return D.emec;
  try {
    D.emec = await json('data/emec.json');
  } catch (e) {
    console.warn('emec.json indisponível', e);
    D.emec = null;
  }
  return D.emec;
}

/* Malha das UFs para o mapa da Geografia.
 *
 * ⚠️ Isto existe porque o `app.js` chamava `fetch('data/geo/uf.geojson')` CRU, fora do
 * helper `json()` — e o helper e justamente quem consulta `window.__EMBED` antes de ir a
 * rede. O geojson SEMPRE esteve embutido no arquivo unico (o build o lista, 245 KB), mas
 * ninguem lia de la: fora de um servidor HTTP o fetch morria, `window.__ufGeo` ficava
 * indefinido e a view inteira caia com "Cannot read properties of undefined (reading
 * 'regions')". Servido por HTTP funcionava sempre, entao o defeito so aparecia no
 * standalone e no artifact publicado — as duas versoes que ninguem testa por habito, que
 * e o mesmo motivo pelo qual a colisao de nome de topo passou despercebida.
 *
 * Mesmo caminho de codigo dos demais dados: embutido primeiro, rede depois.            */
export async function carregarGeo() {
  if (window.__ufGeo) return window.__ufGeo;
  try {
    window.__ufGeo = await json('data/geo/uf.geojson');
  } catch (e) {
    console.warn('malha de UF indisponível — o mapa não será desenhado', e);
    window.__ufGeo = null;
  }
  return window.__ufGeo;
}

/* ------------------------------------------------------------------ helpers */
export const gr = i => D.dim.ies.grupo[i];                 // grupo da IES (indice)
export const nomeIES = i => D.dim.ies.nome[i];
export const ufIES = i => D.dim.ies.uf[i];
export const redeIES = i => D.dim.ies.rede[i];
export const nomeCurso = i => D.dim.curso.nome[i];
export const areaCurso = i => D.dim.curso.area[i];
export const nomeMun = i => D.dim.mun.nome[i];
export const ufMun = i => D.dim.mun.uf[i];
export const regMun = i => D.dim.mun.regiao[i];

export function kpiAno(ano) {
  const i = D.meta.anos.indexOf(ano);
  if (i < 0) return null;
  const k = D.meta.kpi, o = {};
  for (const c of Object.keys(k)) o[c] = k[c][i];
  return o;
}

/* Testa se uma linha do cubo IES passa nos filtros ativos.
 * `f` = {grupo, uf, rede, mod} — mod tratado fora, por ser coluna do cubo. */
export function passaIES(ix, f) {
  if (f.grupo && D.dim.ies.grupo[ix] !== f.grupo) return false;
  if (f.uf && D.dim.ies.uf[ix] !== f.uf) return false;
  if (f.rede && D.dim.ies.rede[ix] !== +f.rede) return false;
  return true;
}

/* Agrega o cubo ies_mod por uma chave derivada da IES.
 * chave(ix) -> string|null ; devolve Map chave -> {mat,ing,conc,tranc,cursos,vagas,pres,ead} */
export function porIES(ano, chave, filtro = {}) {
  const c = D.iesMod, m = new Map();
  const modF = filtro.mod ? +filtro.mod : 0;
  for (let i = 0; i < c.n; i++) {
    if (c.ano[i] !== ano) continue;
    const ix = c.ies[i];
    if (ix < 0 || !passaIES(ix, filtro)) continue;
    if (modF && c.mod[i] !== modF) continue;
    const k = chave(ix);
    if (k == null) continue;
    let o = m.get(k);
    if (!o) { o = { mat: 0, ing: 0, conc: 0, tranc: 0, cursos: 0, vagas: 0, pres: 0, ead: 0 }; m.set(k, o); }
    o.mat += c.qt_mat[i]; o.ing += c.qt_ing[i]; o.conc += c.qt_conc[i];
    o.tranc += c.qt_trancada[i]; o.cursos += c.qt_curso[i]; o.vagas += c.qt_vaga[i];
    if (c.mod[i] === 1) o.pres += c.qt_mat[i]; else o.ead += c.qt_mat[i];
  }
  return m;
}

/* Serie temporal agregada por chave derivada da IES. Map chave -> {ano: {..}} */
export function serieIES(chave, filtro = {}) {
  const c = D.iesMod, m = new Map();
  const modF = filtro.mod ? +filtro.mod : 0;
  for (let i = 0; i < c.n; i++) {
    const ix = c.ies[i];
    if (ix < 0 || !passaIES(ix, filtro)) continue;
    if (modF && c.mod[i] !== modF) continue;
    const k = chave(ix);
    if (k == null) continue;
    let s = m.get(k);
    if (!s) { s = {}; m.set(k, s); }
    const a = c.ano[i];
    let o = s[a];
    if (!o) { o = { mat: 0, ing: 0, conc: 0, tranc: 0, pres: 0, ead: 0 }; s[a] = o; }
    o.mat += c.qt_mat[i]; o.ing += c.qt_ing[i]; o.conc += c.qt_conc[i]; o.tranc += c.qt_trancada[i];
    if (c.mod[i] === 1) o.pres += c.qt_mat[i]; else o.ead += c.qt_mat[i];
  }
  return m;
}

/* DENOMINADOR de market share.
 * Aplica modalidade, UF e rede — mas NUNCA grupo: se filtrasse por grupo, todo grupo
 * teria 100% de share. Para o total *do que esta filtrado*, use totalFiltrado(). */
export function totalAno(ano, filtro = {}) {
  return _soma(ano, filtro, false);
}

/* Total do recorte selecionado, aplicando TODOS os filtros, inclusive grupo. */
export function totalFiltrado(ano, filtro = {}) {
  return _soma(ano, filtro, true);
}

function _soma(ano, filtro, comGrupo) {
  const c = D.iesMod;
  const modF = filtro.mod ? +filtro.mod : 0;
  let t = 0;
  for (let i = 0; i < c.n; i++) {
    if (c.ano[i] !== ano) continue;
    if (modF && c.mod[i] !== modF) continue;
    const ix = c.ies[i];
    if (ix < 0) continue;
    if (comGrupo && filtro.grupo && D.dim.ies.grupo[ix] !== filtro.grupo) continue;
    if (filtro.uf && D.dim.ies.uf[ix] !== filtro.uf) continue;
    if (filtro.rede && D.dim.ies.rede[ix] !== +filtro.rede) continue;
    t += c.qt_mat[i];
  }
  return t;
}

/* Unidades (proxy de campus) e municipios EAD por chave derivada da IES. */
export function unidadesPorIES(ano, chave, filtro = {}) {
  const c = D.iesAno, m = new Map();
  for (let i = 0; i < c.n; i++) {
    if (c.ano[i] !== ano) continue;
    const ix = c.ies[i];
    if (ix < 0 || !passaIES(ix, filtro)) continue;
    const k = chave(ix);
    if (k == null) continue;
    let o = m.get(k);
    if (!o) { o = { unidades: 0, municEad: 0, ies: 0 }; m.set(k, o); }
    o.unidades += c.qt_unidade[i]; o.municEad += c.qt_munic_ead[i]; o.ies += 1;
  }
  return m;
}

/* ---------------------------------------------------------------- formatacao
 * Segue o idioma: 10.227.266 em pt-BR, 10,227,266 em en-US. Os formatadores sao
 * recriados quando o idioma vira — Intl.NumberFormat e caro para instanciar a cada
 * chamada, e barato de cachear.                                                    */
let _loc = null, nf0, nf1, nf2;
function fmts() {
  const l = locale();
  if (l !== _loc) {
    _loc = l;
    nf0 = new Intl.NumberFormat(l);
    nf1 = new Intl.NumberFormat(l, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
    nf2 = new Intl.NumberFormat(l, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
  return { nf0, nf1, nf2 };
}

export const n = v => (v == null || isNaN(v)) ? '—' : fmts().nf0.format(Math.round(v));
/* Mensalidade e sempre em real, nos dois idiomas: e preco de tabela de faculdade
 * brasileira, e converter para dolar so acrescentaria risco de cambio a uma leitura
 * que e de posicionamento de preco. */
export const brl = v => (v == null || isNaN(v)) ? '—' : 'R$ ' + fmts().nf2.format(v);
export const pct = (v, d = 1) => (v == null || isNaN(v)) ? '—'
  : (d === 2 ? fmts().nf2 : fmts().nf1).format(v) + '%';
export const pp = v => (v == null || isNaN(v)) ? '—' : (v >= 0 ? '+' : '') + fmts().nf1.format(v) + ' p.p.';
export function compacto(v) {
  if (v == null || isNaN(v)) return '—';
  const f = fmts(), a = Math.abs(v);
  if (ehIngles()) {
    if (a >= 1e6) return f.nf2.format(v / 1e6) + 'M';
    if (a >= 1e3) return f.nf0.format(Math.round(v / 1e3)) + 'k';
    return f.nf0.format(v);
  }
  if (a >= 1e6) return f.nf2.format(v / 1e6) + ' mi';
  if (a >= 1e3) return f.nf0.format(Math.round(v / 1e3)) + ' mil';
  return f.nf0.format(v);
}
export function deltaHTML(v, sufixo = '%') {
  if (v == null || isNaN(v) || !isFinite(v)) return '<span class="delta">—</span>';
  const cls = v > 0 ? 'pos' : (v < 0 ? 'neg' : '');
  const s = (v >= 0 ? '+' : '') + nf1.format(v) + sufixo;
  return `<span class="delta ${cls}">${s}</span>`;
}
