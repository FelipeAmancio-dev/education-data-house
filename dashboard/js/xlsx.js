/* Gerador de .xlsx sem dependência externa.
 *
 * O artifact publicado roda sob CSP estrita: nenhuma biblioteca de CDN carrega. E baixar
 * um .csv por tabela espalha o trabalho do investidor. Então geramos aqui um workbook de
 * verdade — uma aba por conjunto de dados — escrevendo o ZIP na mão.
 *
 * Um .xlsx é um ZIP com XML dentro. O ZIP é gravado com método STORE (sem compressão):
 * é o que evita ter de implementar DEFLATE, continua sendo ZIP válido, e o custo é um
 * arquivo maior — irrelevante para as dezenas de milhares de linhas que saem daqui.
 * As strings vão inline (`t="inlineStr"`), o que dispensa a tabela de shared strings.
 */

/* ------------------------------------------------------------------- CRC-32 */
const TABELA_CRC = (() => {
  const t = new Uint32Array(256);
  for (let i = 0; i < 256; i++) {
    let c = i;
    for (let k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
    t[i] = c >>> 0;
  }
  return t;
})();

function crc32(bytes) {
  let c = 0xFFFFFFFF;
  for (let i = 0; i < bytes.length; i++) c = TABELA_CRC[(c ^ bytes[i]) & 0xFF] ^ (c >>> 8);
  return (c ^ 0xFFFFFFFF) >>> 0;
}

/* ----------------------------------------------------------------------- ZIP */
function zip(arquivos) {
  const enc = new TextEncoder();
  const partes = [], central = [];
  let offset = 0;

  const u16 = v => [v & 0xFF, (v >> 8) & 0xFF];
  const u32 = v => [v & 0xFF, (v >>> 8) & 0xFF, (v >>> 16) & 0xFF, (v >>> 24) & 0xFF];

  for (const { nome, dados } of arquivos) {
    const bytes = typeof dados === 'string' ? enc.encode(dados) : dados;
    const nomeB = enc.encode(nome);
    const crc = crc32(bytes);
    // data/hora fixas: o conteúdo do arquivo não muda com o relógio, e assim dois
    // downloads do mesmo dado geram bytes idênticos
    const hora = 0, data = ((2020 - 1980) << 9) | (1 << 5) | 1;
    const local = [...u32(0x04034B50), ...u16(20), ...u16(0x0800), ...u16(0), ...u16(hora),
                   ...u16(data), ...u32(crc), ...u32(bytes.length), ...u32(bytes.length),
                   ...u16(nomeB.length), ...u16(0)];
    partes.push(new Uint8Array(local), nomeB, bytes);
    central.push([...u32(0x02014B50), ...u16(20), ...u16(20), ...u16(0x0800), ...u16(0),
                  ...u16(hora), ...u16(data), ...u32(crc), ...u32(bytes.length),
                  ...u32(bytes.length), ...u16(nomeB.length), ...u16(0), ...u16(0), ...u16(0),
                  ...u16(0), ...u32(0), ...u32(offset)], nomeB);
    offset += local.length + nomeB.length + bytes.length;
  }

  const cd = [];
  for (let i = 0; i < central.length; i += 2) {
    cd.push(new Uint8Array(central[i]), central[i + 1]);
  }
  const tamCD = cd.reduce((s, p) => s + p.length, 0);
  const eocd = new Uint8Array([...u32(0x06054B50), ...u16(0), ...u16(0),
    ...u16(arquivos.length), ...u16(arquivos.length), ...u32(tamCD), ...u32(offset), ...u16(0)]);
  return new Blob([...partes, ...cd, eocd], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
}

/* ----------------------------------------------------------------------- XML */
const escX = s => String(s ?? '')
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')
  // caracteres de controle quebram o XML e o Excel recusa o arquivo inteiro
  .replace(/[\x00-\x08\x0B\x0C\x0E-\x1F]/g, '');

function coluna(i) {
  let s = '';
  for (i += 1; i > 0; i = Math.floor((i - 1) / 26)) s = String.fromCharCode(65 + (i - 1) % 26) + s;
  return s;
}

/* Nome de aba: o Excel recusa > 31 caracteres, os caracteres []:*?/\ e nomes repetidos. */
function nomeAba(nome, usados) {
  let n = String(nome).replace(/[\[\]:*?/\\]/g, ' ').trim().slice(0, 31) || 'Dados';
  if (usados.has(n)) {
    const base = n.slice(0, 27);
    let i = 2;
    while (usados.has(`${base} (${i})`)) i++;
    n = `${base} (${i})`;
  }
  usados.add(n);
  return n;
}

function planilha(cols, linhas) {
  const cel = (v, ref) => {
    if (v == null || v === '') return '';
    if (typeof v === 'number' && isFinite(v)) {
      return `<c r="${ref}"><v>${Math.round(v * 1e6) / 1e6}</v></c>`;
    }
    return `<c r="${ref}" t="inlineStr"><is><t xml:space="preserve">${escX(v)}</t></is></c>`;
  };
  const cab = '<row r="1">' + cols.map((c, i) =>
    `<c r="${coluna(i)}1" t="inlineStr" s="1"><is><t>${escX(c.t)}</t></is></c>`).join('') + '</row>';
  const corpo = linhas.map((r, li) => '<row r="' + (li + 2) + '">' +
    cols.map((c, i) => cel(r[c.k], coluna(i) + (li + 2))).join('') + '</row>').join('');
  // largura generosa na primeira coluna: costuma ser nome de IES, curso ou município
  const larguras = '<cols>' + cols.map((c, i) =>
    `<col min="${i + 1}" max="${i + 1}" width="${i === 0 ? 42 : Math.min(30, Math.max(12, c.t.length + 4))}" customWidth="1"/>`).join('') + '</cols>';
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<sheetPr><outlinePr/></sheetPr>${larguras}
<sheetData>${cab}${corpo}</sheetData></worksheet>`;
}

/* --------------------------------------------------------------------- API
 * conjuntos: [{nome, cols:[{k,t}], linhas:[{...}]}] — um por aba.               */
export function montarXLSX(conjuntos) {
  const usados = new Set();
  const abas = conjuntos.map((c, i) => ({
    nome: nomeAba(c.nome, usados), cols: c.cols, linhas: c.linhas, id: i + 1,
  }));

  const arquivos = [
    { nome: '[Content_Types].xml', dados:
      `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
${abas.map(a => `<Override PartName="/xl/worksheets/sheet${a.id}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>`).join('\n')}
</Types>` },
    { nome: '_rels/.rels', dados:
      `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>` },
    { nome: 'xl/workbook.xml', dados:
      `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets>${abas.map(a =>
  `<sheet name="${escX(a.nome)}" sheetId="${a.id}" r:id="rId${a.id}"/>`).join('')}</sheets>
</workbook>` },
    { nome: 'xl/_rels/workbook.xml.rels', dados:
      `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
${abas.map(a => `<Relationship Id="rId${a.id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet${a.id}.xml"/>`).join('\n')}
<Relationship Id="rId${abas.length + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>` },
    // dois estilos: o 0 é o padrão e o 1 é o cabeçalho em negrito
    { nome: 'xl/styles.xml', dados:
      `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font>
<font><b/><sz val="11"/><name val="Calibri"/></font></fonts>
<fills count="2"><fill><patternFill patternType="none"/></fill>
<fill><patternFill patternType="gray125"/></fill></fills>
<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/></cellXfs>
<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>` },
    ...abas.map(a => ({ nome: `xl/worksheets/sheet${a.id}.xml`, dados: planilha(a.cols, a.linhas) })),
  ];
  return zip(arquivos);
}

export function baixarXLSX(nomeArquivo, conjuntos) {
  const blob = montarXLSX(conjuntos);
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = nomeArquivo.replace(/[^\w\-]+/g, '_').replace(/^_|_$/g, '') + '.xlsx';
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 4000);
  return blob;
}
