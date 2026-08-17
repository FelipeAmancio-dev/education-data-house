/* Ambiente Regulatório — one-stop shop regulatório do ensino superior privado.
 *
 * A ordem de leitura é a ordem em que o investidor pergunta:
 *   1) o que está acontecendo agora?      → os três cartões de tema, no topo
 *   2) como chegamos aqui?                → a timeline dentro de cada tema
 *   3) o que saiu recentemente?           → o feed de decisões
 *   4) quero achar uma coisa específica   → busca e filtros
 *
 * Duas decisões editoriais que sustentam o resto:
 *
 * ⚠️ REGRA VIGENTE ≠ DISCUSSÃO. Cada item carrega `status` (vigente, transição, discussão,
 * revogada) e a tela pinta isso com cor e rótulo. Num módulo regulatório, confundir uma
 * consulta pública com regra em vigor é o erro mais caro que a página pode induzir.
 *
 * ⚠️ FONTE PRIMÁRIA SEMPRE. Toda decisão tem link para o documento oficial, e as que ainda
 * não foram conferidas no DOU aparecem marcadas como "a confirmar" — em vez de sumirem ou,
 * pior, de se passarem por conferidas.
 *
 * Fonte: `data/regulatorio.json`, gerado por `scripts/08_build_regulatorio.py` a partir de
 * `config/regulatorio.json`, que é o arquivo editado à mão.
 */
import { carregarRegulatorio, carregarDouDiario, D } from './dados.js';
import { $, $$, esc, registrarCSV } from './ui.js';
import { TX, idioma } from './i18n.js';

// 'diario' é a aba de entrada, a pedido do usuário: quem abre o bloco quer ver o que
// saiu, e só depois escolhe o panorama de um tema.
let temaSel = 'diario';
let diaRelev = '';     // filtro de relevância da aba do diário
let relevSel = '';
let periodoSel = '';
let busca = '';
let abertoId = null;

const ROT_STATUS = { vigente: 'Vigente', transicao: 'Em transição',
                     discussao: 'Em discussão', revogada: 'Revogada' };
const ROT_RELEV = { alta: 'Alta', media: 'Média', baixa: 'Baixa' };
const DIAS = { '30d': 30, '3m': 91, '6m': 183, '12m': 365 };

const semAcento = s => String(s ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

const dataBR = s => new Date(s + 'T12:00:00').toLocaleDateString(
  idioma() === 'en' ? 'en-US' : 'pt-BR',
  idioma() === 'en' ? { year: 'numeric', month: 'short', day: 'numeric' }
                    : { year: 'numeric', month: '2-digit', day: '2-digit' });

const nomeTema = (R, id) => R.temas.find(t => t.id === id)?.nome || TX('Outros');

/* ------------------------------------------------------------------ filtros */
function rgFiltradas(R) {
  const hoje = new Date();
  const q = semAcento(busca).trim();
  return R.decisoes.filter(d => {
    if (temaSel !== 'todos' && d.tema !== temaSel) return false;
    if (relevSel && d.relevancia !== relevSel) return false;
    if (periodoSel && DIAS[periodoSel]) {
      const dias = (hoje - new Date(d.data + 'T12:00:00')) / 86400000;
      if (dias > DIAS[periodoSel]) return false;
    }
    // a busca varre título, número, resumo, palavras-chave e o "o que mudou"
    if (q && !d._busca.includes(q)) return false;
    return true;
  });
}

/* ------------------------------------------------- cartões de tema (30 seg) */
function rgSelo(status) {
  return `<span class="rg-selo rg-${status}">${esc(TX(ROT_STATUS[status] || status))}</span>`;
}

/* Link para o ato, do tamanho de uma etiqueta. Aparece dentro de cada peça do esquema:
 * a regra e o documento que a instituiu andam juntos, senão o investidor tem de sair da
 * página para descobrir de onde saiu o número. */
function rgFonte(doc, url) {
  if (!doc) return '';
  return url
    ? `<a class="rg-fonte" href="${esc(url)}" target="_blank" rel="noopener">${esc(doc)} ↗</a>`
    : `<span class="rg-fonte">${esc(doc)}</span>`;
}

/* Cartão de tema — leitura em segundos, sem parágrafo.
 * O usuário cortou o texto duas vezes: o que ele quer é "5 cursos só presenciais", não a
 * frase que explica isso. Aqui só entra fragmento — número, rótulo curto e o link do ato.
 * Cada tema tem faixa de cor própria (`t.cor`), que é o que separa um bloco do outro sem
 * precisar de mais título. */
function cartaoTema(t) {
  const marcos = t.timeline || [];
  const d = t.destaques || [];
  const m = t.marco;

  return `<section class="rg-tema rg-cor-${esc(t.cor || 'azul')}" data-tema="${esc(t.id)}">
    <header class="rg-tema-cab">
      <h3>${esc(t.nome)}</h3>
      <div class="rg-tema-selos">
        ${rgSelo(t.status)}
        <span class="rg-selo rg-rel-${t.relevancia}">${esc(TX(ROT_RELEV[t.relevancia]))}</span>
      </div>
    </header>

    <div class="rg-tema-corpo">
      ${d.length ? `<div class="rg-destaques">
        ${d.map(x => `<div class="rg-dest rg-tom-${x.tom || 'neutro'}">
          <div class="rg-dest-valor">${esc(x.valor)}</div>
          <div class="rg-dest-rot">${esc(x.rot)}</div>
          <div class="rg-dest-det">${esc(x.detalhe)}</div>
          ${rgFonte(x.doc, x.url)}
        </div>`).join('')}
      </div>` : ''}

      ${t.matriz ? `<div class="rg-matriz">
        <div class="rg-matriz-topo">
          <span class="rg-rot">${esc(t.matriz.titulo)}</span>
          ${rgFonte(t.matriz.doc, t.matriz.url)}
        </div>
        ${t.matriz.linhas.map(l => `<div class="rg-mx-linha rg-tom-${l.tom}">
          <div class="rg-mx-grupo">${esc(l.grupo)}</div>
          <div class="rg-mx-formato">${esc(l.formato)}</div>
        </div>`).join('')}
      </div>` : ''}

      ${(t.pontos || []).length ? `<div class="rg-pontos">
        <div class="rg-rot">${esc(TX('O detalhe que o quadro acima não cabe'))}</div>
        ${t.pontos.map(pt => `<div class="rg-ponto">
          <p>${esc(pt.texto)}</p>${rgFonte(pt.doc, pt.url)}
        </div>`).join('')}
      </div>` : ''}

      ${m ? `<div class="rg-fluxo">
        <div class="rg-fx"><span>${esc(TX('Como era'))}</span><b>${esc(m.como_era)}</b>
          ${rgFonte(m.doc_era, m.url_era)}</div>
        <div class="rg-seta">→</div>
        <div class="rg-fx rg-fx-mudou"><span>${esc(TX('O que mudou'))}</span>
          <b>${esc(m.o_que_mudou)}</b>${rgFonte(m.doc_mudou, m.url_mudou)}</div>
        <div class="rg-seta">→</div>
        <div class="rg-fx"><span>${esc(TX('Hoje'))}</span><b>${esc(m.como_hoje)}</b>
          ${rgFonte(m.doc_hoje, m.url_hoje)}</div>
      </div>` : ''}

      ${marcos.length ? `<div class="rg-timeline">
        ${marcos.map(x => `<div class="rg-tl-item rg-tl-${x.status}">
          <div class="rg-tl-data">${esc(dataBR(x.data))}</div>
          ${x.url ? `<a href="${esc(x.url)}" target="_blank" rel="noopener">${esc(x.titulo)} ↗</a>`
                  : `<strong>${esc(x.titulo)}</strong>`}
        </div>`).join('')}
      </div>` : ''}

      <div class="rg-chips">
        <span class="rg-chip"><i>${esc(TX('Em discussão'))}</i>${esc(t.em_discussao)}</span>
        <span class="rg-chip"><i>${esc(TX('Próximo prazo'))}</i>${esc(t.proximo_prazo)}</span>
      </div>
    </div>
  </section>`;
}

/* ------------------------------------------------------- feed de decisões */
function linhaDecisao(R, d, i) {
  const aberto = abertoId === i;
  return `<div class="rg-dec${aberto ? ' on' : ''}" data-i="${i}">
    <div class="rg-dec-topo">
      <div class="rg-dec-data">${esc(dataBR(d.data))}</div>
      <div class="rg-dec-meio">
        <div class="rg-dec-tags">
          <span class="tag">${esc(nomeTema(R, d.tema))}</span>
          <span class="tag">${esc(d.orgao)}</span>
          ${rgSelo(d.status)}
          <span class="rg-selo rg-rel-${d.relevancia}">${esc(TX(ROT_RELEV[d.relevancia]))}</span>
          ${d.confianca === 'a_confirmar'
            ? `<span class="rg-selo rg-conf" title="${esc(TX('Não conferida no Diário Oficial'))}">${
                esc(TX('a confirmar'))}</span>` : ''}
        </div>
        <div class="rg-dec-doc">${esc(d.documento)}</div>
      </div>
      <div class="rg-dec-acao">
        <button class="btn rg-abrir" type="button">${esc(aberto ? TX('Fechar') : TX('Detalhes'))}</button>
        <a class="btn" href="${esc(d.fonte_url)}" target="_blank" rel="noopener">${
          esc(TX('Abrir documento'))} ↗</a>
      </div>
    </div>
    ${aberto ? rgPainel(d) : ''}
  </div>`;
}

/* Painel de detalhe — abre embaixo da linha, sem tirar o investidor da página. */
function rgPainel(d) {
  const datas = (d.datas || []).map(x =>
    `<li><span>${esc(TX(x.rotulo))}</span><strong>${esc(dataBR(x.data))}</strong></li>`).join('');
  return `<div class="rg-painel">
    <div class="rg-painel-grid">
      <div><div class="rg-rot">${esc(TX('O que foi publicado'))}</div><p>${esc(d.resumo)}</p></div>
      ${d.o_que_mudou ? `<div><div class="rg-rot">${esc(TX('O que mudou'))}</div>
        <p>${esc(d.o_que_mudou)}</p></div>` : ''}
      ${d.quem_afeta ? `<div><div class="rg-rot">${esc(TX('Quem é afetado'))}</div>
        <p>${esc(d.quem_afeta)}</p></div>` : ''}
      ${datas ? `<div><div class="rg-rot">${esc(TX('Datas importantes'))}</div>
        <ul class="rg-datas">${datas}</ul></div>` : ''}
    </div>
    <div class="rg-painel-pe">
      ${d.confianca === 'a_confirmar'
        ? `<span class="rg-aviso-conf">${esc(TX(
            'Compilada a partir de fonte secundária: confira o número e a data no documento oficial antes de citar.'))}</span>`
        : ''}
      <a class="btn" href="${esc(d.fonte_url)}" target="_blank" rel="noopener">${
        esc(TX('Abrir documento oficial'))} ↗</a>
    </div>
  </div>`;
}

/* --------------------------------------------------------------- desenhar */
function rgDesenhar(R) {
  /* A aba do diário troca a página inteira, não só o conteúdo de uma seção: os controles
   * de período/relevância/busca abaixo filtram a base CURADA, e deixá-los visíveis sobre
   * o feed do DOU faria o usuário mexer num filtro que não tem efeito nenhum ali. */
  const noDiario = temaSel === 'diario';
  $('#rg-diario').hidden = !noDiario;
  $('#rg-curado').hidden = noDiario;
  $('#rg-controles').hidden = noDiario;
  if (noDiario) { rgDiaDesenhar(D.douDiario); return; }

  const temas = R.temas.filter(t => t.id === temaSel);
  $('#rg-temas').innerHTML = temas.length
    ? temas.map(cartaoTema).join('')
    : `<div class="vazio">${TX('Sem resumo para este tema.')}</div>`;

  const ds = rgFiltradas(R);
  $('#rg-feed').innerHTML = ds.length
    ? ds.map((d, i) => linhaDecisao(R, d, i)).join('')
    : `<div class="vazio">${TX('Nenhuma publicação para os filtros escolhidos.')}</div>`;

  $('#rg-contagem').textContent = TX('{n} de {t} publicações',
    { n: ds.length, t: R.decisoes.length });

  $$('#rg-feed .rg-abrir').forEach(b => b.onclick = ev => {
    const i = +ev.target.closest('.rg-dec').dataset.i;
    abertoId = abertoId === i ? null : i;
    rgDesenhar(R);
  });

  registrarCSV('regulatorio', TX('Decisões regulatórias'), [
    { k: 'data', t: TX('Data') }, { k: 'tema', t: TX('Tema') },
    { k: 'documento', t: TX('Documento') }, { k: 'orgao', t: TX('Órgão') },
    { k: 'status', t: TX('Situação') }, { k: 'relevancia', t: TX('Relevância') },
    { k: 'resumo', t: TX('Resumo') }, { k: 'o_que_mudou', t: TX('O que mudou') },
    { k: 'quem_afeta', t: TX('Quem é afetado') }, { k: 'confianca', t: TX('Conferência') },
    { k: 'fonte_url', t: TX('Fonte oficial') },
  ], ds.map(d => ({ ...d, tema: nomeTema(R, d.tema),
                    status: TX(ROT_STATUS[d.status]), relevancia: TX(ROT_RELEV[d.relevancia]) })));
}

/* ═══════════════════════ aba "Últimas publicações" (DOU diário) ═══════════
 *
 * O que o MEC publicou na Seção 1, sem curadoria, com relevância atribuída por regra.
 *
 * ⚠️ A separação em relação às abas de tema é deliberada e a tela declara: ali o dado foi
 * conferido no documento e escrito por alguém; aqui é o que o Ministério publicou, como
 * publicou. São confiabilidades diferentes, e apresentá-las juntas apagaria isso.
 *
 * ⚠️ Cada linha mostra o MOTIVO da classificação. Sem ele, o leitor recebe um rótulo de
 * relevância sem poder discordar — e num classificador por regra, discordar é o mecanismo
 * de correção: é o motivo aparecendo errado que revela a regra a ajustar.               */
function rgDiaLinha(p) {
  /* Quem o ato cita. Duas origens, e a diferença importa:
   *   - `grupos`  vem do código e-MEC ou do token de marca — é o GRUPO ECONÔMICO, ou seja,
   *               a companhia que o investidor acompanha. Etiqueta laranja, destacada.
   *   - `ies_citada` é o nome da instituição como o DOU escreveu, sem mapeamento. Serve
   *               quando não há grupo: pelo menos mostra de quem o ato fala. */
  const grupos = (p.grupos || []).length
    ? ` <span class="tag lst">${p.grupos.map(esc).join(' · ')}</span>` : '';
  const ies = (!(p.grupos || []).length && p.ies_citada)
    ? ` <span class="tag">${esc(p.ies_citada)}${
        p.cod_ies ? ` · e-MEC ${esc(p.cod_ies)}` : ''}</span>` : '';
  return `<div class="rg-dia rg-dia-${esc(p.relevancia)}">
    <div class="rg-dia-topo">
      <span class="rg-dia-data">${esc(dataBR(p.data))}</span>
      <span class="rg-selo rg-rel-${esc(p.relevancia)}">${esc(TX(ROT_RELEV[p.relevancia]))}</span>
      <span class="rg-dia-orgao">${esc(p.orgao)}</span>
      ${grupos}${ies}
      <a class="rg-dia-link" href="${esc(p.url)}" target="_blank" rel="noopener"
         >${esc(TX('Abrir no DOU'))} ↗</a>
    </div>
    <div class="rg-dia-tit">${esc(p.titulo)}</div>
    ${p.resumo ? `<div class="rg-dia-res">${esc(p.resumo)}</div>` : ''}
    <div class="rg-dia-motivo">${esc(TX('Classificado como {r} porque: {m}',
      { r: TX(ROT_RELEV[p.relevancia]).toLowerCase(), m: p.motivo }))}</div>
  </div>`;
}

function rgDiaDesenhar(DD) {
  const lista = $('#rg-dia-lista');
  if (!DD || !DD.publicacoes?.length) {
    lista.innerHTML = `<div class="aviso">${TX(
      'O feed diário ainda não foi coletado nesta cópia. Rode ' +
      '<code>python scripts/11_fetch_dou_diario.py</code>.')}</div>`;
    $('#rg-dia-nota').textContent = '';
    $('#rg-dia-carimbo').textContent = '';
    return;
  }
  $$('#rg-dia-relev .chip').forEach(b => {
    b.classList.toggle('on', (b.dataset.r || '') === diaRelev);
    b.onclick = () => { diaRelev = b.dataset.r || ''; rgDiaDesenhar(DD); };
  });

  const ps = DD.publicacoes.filter(p => !diaRelev || p.relevancia === diaRelev);
  lista.innerHTML = ps.length
    ? ps.map(rgDiaLinha).join('')
    : `<div class="vazio">${TX('Nenhuma publicação nesta relevância.')}</div>`;

  const c = DD.por_relevancia || {};
  $('#rg-dia-carimbo').textContent = TX(
    '{n} publicações em {d} dias · {a} alta · {m} média · {b} baixa',
    { n: DD.n, d: (DD.dias || []).length, a: c.alta || 0, m: c.media || 0, b: c.baixa || 0 });

  $('#rg-dia-nota').textContent = TX(
    'Seção 1 do Diário Oficial, órgão Ministério da Educação, coletado em {d}. A relevância ' +
    'é de regra, não de leitura: ninguém conferiu estes atos um a um — para o que foi ' +
    'conferido e escrito, use as abas de tema. Ato que cite uma companhia aberta entra ' +
    'sempre como alta, e o nome dela aparece ao lado.',
    { d: dataBR(DD.atualizado_em) });

  registrarCSV('regulatorio', TX('Publicações do DOU'), [
    { k: 'data', t: TX('Data') }, { k: 'orgao', t: TX('Órgão') },
    { k: 'titulo', t: TX('Documento') }, { k: 'relevancia', t: TX('Relevância') },
    { k: 'motivo', t: TX('Motivo da classificação') },
    { k: 'grupos_txt', t: TX('Grupo citado') }, { k: 'ies_citada', t: TX('Instituição citada') },
    { k: 'cod_ies', t: TX('Cód. e-MEC') },
    { k: 'resumo', t: TX('Ementa') }, { k: 'url', t: TX('Fonte oficial') },
  ], ps.map(p => ({ ...p, relevancia: TX(ROT_RELEV[p.relevancia]),
                    grupos_txt: (p.grupos || []).join(' · ') })));
}

/* ---------------------------------------------------------- controles */
/* Abas de tema — a navegação principal do módulo.
 * O usuário não quer os três panoramas de uma vez: escolhe um tema e a página inteira
 * responde, resumo e feed. Por isso o tema saiu do dropdown de filtros, onde parecia um
 * refinamento entre outros, e virou a aba no topo. */
function montarAbas(R) {
  const box = $('#rg-abas');
  // a aba do diário vem primeiro e é o padrão: é o que muda todo dia
  const temas = [{ id: 'diario', nome: TX('Últimas publicações') }, ...R.temas];
  if (R.decisoes.some(d => !R.temas.find(t => t.id === d.tema)))
    temas.push({ id: 'outros', nome: TX('Outros') });
  box.innerHTML = temas.map(t => `<button class="chip${t.id === temaSel ? ' on' : ''}"
    data-t="${esc(t.id)}">${esc(t.nome)}</button>`).join('');
  box.onclick = ev => {
    const b = ev.target.closest('button[data-t]');
    if (!b || b.dataset.t === temaSel) return;
    temaSel = b.dataset.t;
    abertoId = null;
    [...box.querySelectorAll('button')].forEach(x =>
      x.classList.toggle('on', x.dataset.t === temaSel));
    rgDesenhar(R);
  };
}

function montarControles(R) {
  const box = $('#rg-controles');
  if (box.dataset.pronto) return;
  box.dataset.pronto = '1';

  const op = (v, t, sel) => `<option value="${esc(v)}"${v === sel ? ' selected' : ''}>${esc(t)}</option>`;
  $('#rg-relev').innerHTML = op('', TX('Todas'), relevSel)
    + ['alta', 'media', 'baixa'].map(r => op(r, TX(ROT_RELEV[r]), relevSel)).join('');
  $('#rg-periodo').innerHTML = op('', TX('Todo o histórico'), periodoSel)
    + [['30d', TX('Últimos 30 dias')], ['3m', TX('Últimos 3 meses')],
       ['6m', TX('Últimos 6 meses')], ['12m', TX('Último ano')]]
      .map(([v, t]) => op(v, t, periodoSel)).join('');

  $('#rg-relev').onchange = e => { relevSel = e.target.value; abertoId = null; rgDesenhar(R); };
  $('#rg-periodo').onchange = e => { periodoSel = e.target.value; abertoId = null; rgDesenhar(R); };
  $('#rg-busca').oninput = e => { busca = e.target.value; abertoId = null; rgDesenhar(R); };
  $('#rg-limpar').onclick = () => {
    relevSel = ''; periodoSel = ''; busca = ''; abertoId = null;
    $('#rg-relev').value = ''; $('#rg-periodo').value = '';
    $('#rg-busca').value = '';
    rgDesenhar(R);
  };
}

/* -------------------------------------------------------------------- view */
export async function regulatorio() {
  const R = await carregarRegulatorio();
  const aviso = $('#rg-aviso');

  if (!R || !R.decisoes?.length) {
    aviso.innerHTML = `<div class="aviso">${TX(
      'A base regulatória ainda não foi gerada nesta cópia. Rode ' +
      '<code>python scripts/08_build_regulatorio.py</code>.')}</div>`;
    ['#rg-temas', '#rg-feed'].forEach(s => { $(s).innerHTML = ''; });
    return;
  }
  aviso.innerHTML = R.a_confirmar
    ? `<div class="aviso">${TX(
        '{q} das {t} publicações ainda não foram conferidas no Diário Oficial e estão marcadas ' +
        'como "a confirmar". Confira o documento oficial antes de citar qualquer uma delas.',
        { q: R.a_confirmar, t: R.n })}</div>`
    : '';

  $('#rg-carimbo').textContent = TX('Base atualizada em {d} · {n} publicações',
    { d: dataBR(R.atualizado_em), n: R.n });
  $('#rg-fontes').innerHTML = (R.fontes || []).map(f =>
    `<a href="${esc(f.url)}" target="_blank" rel="noopener">${esc(f.nome)} ↗</a>`).join('');

  await carregarDouDiario();
  montarAbas(R);
  montarControles(R);
  rgDesenhar(R);
}
