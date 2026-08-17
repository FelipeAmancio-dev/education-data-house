/* Orquestracao: home, roteamento por hash, filtros por bloco, idioma e download de CSV.
 *
 * A home e so a porta de entrada — uma grade de cards, um por dashboard. Cada bloco tem
 * rota propria (#/precos, #/overview, ...) para que o link seja compartilhavel e o botao
 * voltar funcione, mas tudo vive num unico HTML, o que mantem viavel a versao offline.
 */
import { carregar, carregarGeo, D } from './dados.js';
import { $, $$, resizeCharts, conjuntosCSV, limparCSV } from './ui.js';
import { baixarXLSX } from './xlsx.js';
import { TX, setIdioma, idiomaSalvo, idioma, capturarEstaticos, aplicarEstaticos } from './i18n.js';
import './en.js';
import { overview, courses, geography, glossario } from './views.js';
import { grupos } from './grupos.js';
import { precos } from './precos.js';
import { mensalidades } from './mensalidades.js';
import { regulatorio } from './regulatorio.js';

const VIEWS = {
  precos, regulatorio, mensalidades, overview, grupos, cursos: courses,
  geografia: geography,
  glossario,   // as definições são estáticas, mas a composição por grupo é renderizada
};

/* Quais filtros globais fazem sentido em cada bloco. Filtro escondido NAO e aplicado:
 * ao sair de uma view que o usava, o valor volta para vazio — senao o usuario carregaria
 * um recorte invisivel de uma tela para outra. */
const FILTROS = {
  precos: [],                                 // tem controles próprios de período
  regulatorio: [],                            // tem tema, período, relevância e órgão próprios
  mensalidades: [],                           // preço de hoje, não série do Censo: sem ano/UF
  overview: ['ano', 'uf', 'mod', 'rede'],
  grupos: ['ano', 'uf', 'mod'],              // sem 'rede': grupo economico e privado
  cursos: ['ano', 'uf', 'mod'],              // sem 'rede': a disputa aqui e entre grupos
  geografia: ['ano', 'mod', 'rede'],          // a UF tem seletor proprio dentro da view
  glossario: ['ano'],                         // a composição por grupo é de um ano
};

const PADRAO = { ano: null, grupo: '', uf: '', rede: '', mod: '' };
let filtros = { ...PADRAO };
let viewAtual = 'home';
window.__filtros = filtros;

/* ------------------------------------------------------------------ filtros */
function montarFiltros() {
  const selAno = $('#f-ano');
  selAno.innerHTML = [...D.meta.anos].reverse().map(a => `<option value="${a}">${a}</option>`).join('');
  selAno.value = D.meta.ano_atual;
  filtros.ano = D.meta.ano_atual;

  $('#f-uf').innerHTML = `<option value="">${TX('Todas')}</option>` +
    D.ufs.map(u => `<option value="${u}">${u}</option>`).join('');

  $$('.filtros:not(.embutido) select').forEach(s => s.onchange = () => { lerFiltros(); render(); });

  $('#f-reset').onclick = () => {
    filtros = { ...PADRAO, ano: D.meta.ano_atual };
    window.__filtros = filtros;
    $('#f-ano').value = filtros.ano;
    ['uf', 'rede', 'mod'].forEach(k => { $('#f-' + k).value = ''; });
    render();
  };
}

function lerFiltros() {
  filtros.ano = +$('#f-ano').value;
  ['uf', 'rede', 'mod'].forEach(k => { filtros[k] = $('#f-' + k).value; });
  window.__filtros = filtros;
}

/* Mostra apenas os filtros pertinentes ao bloco e zera os escondidos. */
function aplicarVisibilidade(view) {
  const ativos = FILTROS[view] || [];
  $('#filtros').hidden = ativos.length === 0;
  $$('.filtros:not(.embutido) .f-item').forEach(el => {
    const k = el.dataset.f;
    const on = ativos.includes(k);
    el.hidden = !on;
    if (!on && k !== 'ano') { $('#f-' + k).value = ''; filtros[k] = ''; }
  });
  window.__filtros = filtros;
}

/* -------------------------------------------------------------- Excel do bloco
 * Um arquivo por dashboard, com uma aba por conjunto de dados. As views registram os
 * conjuntos ao renderizar; aqui só montamos o botão. Um .xlsx único evita o vaivém de
 * baixar seis CSVs e colar tudo à mão. */
function montarBotaoExcel(view) {
  const acoes = $(`#v-${view} .acoes`);
  if (!acoes) return;
  const conjuntos = conjuntosCSV(view);
  if (!conjuntos.length) { acoes.innerHTML = ''; return; }

  const linhas = conjuntos.reduce((s, c) => s + c.linhas.length, 0);
  acoes.innerHTML = `<button class="btn btn-excel" type="button">⤓ ${TX('Baixar Excel')}
    <small>${conjuntos.length} ${TX('abas')} · ${
      linhas.toLocaleString(idioma() === 'en' ? 'en-US' : 'pt-BR')} ${TX('linhas')}</small></button>`;

  acoes.querySelector('button').onclick = ev => {
    const b = ev.currentTarget, antes = b.innerHTML;
    b.disabled = true;
    b.textContent = TX('Gerando…');
    // o navegador precisa pintar o "Gerando…" antes de travar no ZIP
    setTimeout(() => {
      try {
        const titulo = $(`#v-${view} .bloco-topo h2`)?.textContent.trim() || view;
        baixarXLSX(`EducationDataHouse_${titulo}_${filtros.ano || D.meta.ano_atual}`, conjuntos);
      } catch (e) {
        console.error(e);
        alert(TX('Não foi possível gerar o arquivo') + ': ' + e.message);
      } finally {
        b.disabled = false;
        b.innerHTML = antes;
      }
    }, 30);
  };
}

/* ----------------------------------------------------------------- roteador
 * O hash e a fonte da verdade quando funciona (link compartilhavel, botao voltar),
 * mas a navegacao nao depende dele: dentro de um artifact publicado a barra de
 * endereco pode nao acompanhar, e os blocos precisam abrir de qualquer forma.   */
function rotaAtual() {
  const h = (location.hash || '').replace(/^#\/?/, '');
  return VIEWS[h] ? h : 'home';
}

function irPara(v, forcar = false) {
  if (v === viewAtual && !forcar) return;
  viewAtual = v;
  if (rotaAtual() !== v) {
    try { location.hash = v === 'home' ? '#/' : '#/' + v; } catch (e) { /* hash bloqueado */ }
  }
  const naHome = v === 'home';
  $('#nav').hidden = naHome;
  $('#filtros').hidden = naHome;
  $$('#nav button').forEach(b => b.classList.toggle('on', b.dataset.v === v));
  $$('.view').forEach(s => s.classList.toggle('on', s.id === 'v-' + v));
  if (!naHome) aplicarVisibilidade(v);
  window.scrollTo({ top: 0 });
  render();
}

let renderizando = false;
async function render() {
  if (renderizando) return;
  renderizando = true;
  try {
    if (viewAtual !== 'home') {
      limparCSV(viewAtual);
      await VIEWS[viewAtual]({ ...filtros });
      montarBotaoExcel(viewAtual);
    }
    requestAnimationFrame(resizeCharts);
  } catch (e) {
    console.error(e);
    const el = $('#v-' + viewAtual);
    if (el) el.insertAdjacentHTML('afterbegin',
      `<div class="aviso">${TX('Erro ao renderizar esta visão')}: ${e.message}</div>`);
  } finally {
    renderizando = false;
  }
}

/* ------------------------------------------------------------------ idioma */
function montarIdioma() {
  $$('#lang button').forEach(b => b.onclick = () => {
    if (b.dataset.l === idioma()) return;
    setIdioma(b.dataset.l);
    aplicarIdioma();
  });
}

function aplicarIdioma() {
  $$('#lang button').forEach(b => b.classList.toggle('on', b.dataset.l === idioma()));
  aplicarEstaticos();
  const selUF = $('#f-uf');
  if (selUF.options.length) selUF.options[0].textContent = TX('Todas');
  render();
}

(async function init() {
  try {
    await carregar();
    // via carregarGeo(), NAO por fetch cru: no arquivo unico e no artifact a malha vem
    // embutida em window.__EMBED e nao ha rede. Ver o comentario em dados.js.
    await carregarGeo();

    // captura o texto estático ANTES de qualquer render: é o que permite virar o
    // idioma do markup sem marcar elemento por elemento no HTML
    capturarEstaticos(document.body);

    montarFiltros();
    montarIdioma();
    $$('#nav button').forEach(b => b.onclick = () => irPara(b.dataset.v));
    // links da home e do "← Dashboards": preventDefault para nao depender do hash
    document.addEventListener('click', ev => {
      const a = ev.target.closest('a[href^="#/"]');
      if (!a) return;
      ev.preventDefault();
      const v = a.getAttribute('href').replace(/^#\/?/, '');
      irPara(VIEWS[v] ? v : 'home');
    });
    window.addEventListener('hashchange', () => {
      const r = rotaAtual();
      if (r !== viewAtual) irPara(r);
    });

    setIdioma(idiomaSalvo());
    $$('#lang button').forEach(b => b.classList.toggle('on', b.dataset.l === idioma()));
    aplicarEstaticos();
    $('#carregando').style.display = 'none';
    irPara(rotaAtual(), true);
  } catch (e) {
    $('#carregando').innerHTML =
      `<div style="max-width:520px;text-align:center">
         <strong style="color:#b3261e">Não foi possível carregar os dados.</strong>
         <p style="margin:10px 0 0">${e.message}</p>
         <p style="margin:10px 0 0;font-size:12px">
           Abra pelo servidor local (<code>python run_dashboard.py</code>) — abrir o HTML
           direto pelo sistema de arquivos é bloqueado pelo navegador.</p>
       </div>`;
  }
})();
