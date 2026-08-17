/* Bilíngue PT/EN.
 *
 * A chave do dicionário é o próprio texto em português. Duas razões: não existe um
 * esquema de chaves paralelo para manter em sincronia, e qualquer string sem tradução
 * cai de volta no português em vez de mostrar uma chave crua na tela.
 *
 * Texto que vem no HTML estático não precisa de marcação: `capturarEstaticos()` guarda
 * os nós de texto no boot e `aplicarEstaticos()` troca o conteúdo na virada de idioma.
 * Elementos escritos pelas views (títulos que mudam com o filtro) levam `data-din` e
 * ficam de fora — quem os traduz é a própria view, no render seguinte.
 */

let LANG = 'pt';
export const ehIngles = () => LANG === 'en';
export const idioma = () => LANG;
export const locale = () => (LANG === 'en' ? 'en-US' : 'pt-BR');

export function setIdioma(l) {
  LANG = l === 'en' ? 'en' : 'pt';
  try { localStorage.setItem('edh_lang', LANG); } catch (e) { /* sandbox */ }
  document.documentElement.lang = LANG === 'en' ? 'en' : 'pt-BR';
}
export function idiomaSalvo() {
  try { return localStorage.getItem('edh_lang') === 'en' ? 'en' : 'pt'; } catch (e) { return 'pt'; }
}

/* Chaves pedidas e não encontradas, para auditoria durante o desenvolvimento:
 * no console, `__faltando()` lista o que ainda falta traduzir.                    */
const faltando = new Set();
window.__faltando = () => [...faltando].sort();

/* TX('texto', {var: valor}) — o nome é curto porque aparece centenas de vezes, e não
 * colide com as variáveis locais das views (`t`, `L` e `n` já estão em uso). */
export function TX(pt, vars) {
  let s = pt;
  if (LANG === 'en') {
    const tr = EN[pt];
    if (tr === undefined) faltando.add(pt);
    else s = tr;
  }
  if (vars) s = s.replace(/\{(\w+)\}/g, (m, k) => (vars[k] !== undefined ? vars[k] : m));
  return s;
}

/* Rótulos que vêm do dado, não da interface. Nome de grupo e sigla de UF não se
 * traduzem: são nomes próprios.                                                   */
export const TXcurso = v => (LANG === 'en' && EN_CURSO[v]) || v;
export const TXarea = v => (LANG === 'en' && EN_AREA[v]) || v;
export const TXregiao = v => (LANG === 'en' && EN_REGIAO[v]) || v;
export const TXorg = v => (LANG === 'en' && EN_ORG[v]) || v;

/* ---------------------------------------------------------------- HTML estático
 * Texto corrido com <strong>/<em> no meio vira vários nós soltos, e traduzir fragmento
 * por fragmento não produz inglês legível. Por isso um elemento com `data-i18n-bloco`
 * é tratado como uma unidade: o dicionário guarda o HTML inteiro em inglês, sob a
 * chave `bloco:<nome>`.                                                              */
let estaticos = null, blocos = null;

export function capturarEstaticos(raiz = document.body) {
  estaticos = [];
  blocos = [...raiz.querySelectorAll('[data-i18n-bloco]')]
    .map(el => ({ el, chave: 'bloco:' + el.dataset.i18nBloco, pt: el.innerHTML }));
  const w = document.createTreeWalker(raiz, NodeFilter.SHOW_TEXT);
  for (let no; (no = w.nextNode());) {
    const s = no.nodeValue;
    if (!s.trim() || !/[A-Za-zÀ-ÿ]/.test(s)) continue;
    const pai = no.parentElement;
    if (!pai || pai.closest('script,style,[data-din],[data-i18n-bloco]')) continue;
    estaticos.push({ no, pt: s });
  }
}

export function aplicarEstaticos() {
  if (!estaticos) return;
  for (const { el, chave, pt } of blocos || []) {
    if (LANG !== 'en') { el.innerHTML = pt; continue; }
    const tr = EN[chave];
    if (tr === undefined) faltando.add(chave);
    else el.innerHTML = tr;
  }
  for (const { no, pt } of estaticos) {
    if (LANG !== 'en') { no.nodeValue = pt; continue; }
    // preserva a indentação do HTML: só o miolo é traduzido
    const m = pt.match(/^(\s*)([\s\S]*?)(\s*)$/);
    const miolo = m[2].replace(/\s+/g, ' ');
    const tr = EN[miolo];
    if (tr === undefined) { faltando.add(miolo); continue; }
    no.nodeValue = m[1] + tr + m[3];
  }
}

/* ============================================================ DICIONÁRIOS ===== */

const EN_REGIAO = {
  'Norte': 'North', 'Nordeste': 'Northeast', 'Centro-Oeste': 'Central-West',
  'Sudeste': 'Southeast', 'Sul': 'South',
};

/* Nomes oficiais dos campos amplos da ISCED/UNESCO, que é a base da CINE. */
const EN_AREA = {
  'Programas básicos': 'Generic programmes and qualifications',
  'Educação': 'Education',
  'Artes e humanidades': 'Arts and humanities',
  'Ciências sociais, comunicação e informação': 'Social sciences, journalism and information',
  'Negócios, administração e direito': 'Business, administration and law',
  'Ciências naturais, matemática e estatística': 'Natural sciences, mathematics and statistics',
  'Computação e Tecnologias da Informação e Comunicação (TIC)':
    'Information and Communication Technologies (ICTs)',
  'Engenharia, produção e construção': 'Engineering, manufacturing and construction',
  'Agricultura, silvicultura, pesca e veterinária': 'Agriculture, forestry, fisheries and veterinary',
  'Saúde e bem-estar': 'Health and welfare',
  'Serviços': 'Services',
};

const EN_ORG = {
  'UNIVERSIDADE': 'UNIVERSITY',
  'Universidade': 'University',
  'CENTRO UNIVERSITARIO': 'UNIVERSITY CENTER',
  'Centro Universitario': 'University Center',
  'FACULDADE': 'COLLEGE',
  'Faculdade': 'College',
  'Instituto Federal de Educacao, Ciencia e Tecnologia': 'Federal Institute of Education, Science and Technology',
  'Centro Federal de Educacao Tecnologica': 'Federal Center for Technological Education',
};

/* Rótulos CINE. Cobre os ~130 maiores cursos de 2024, que é tudo o que as tabelas e
 * gráficos chegam a exibir; o que faltar aparece em português mesmo.               */
const EN_CURSO = {
  'Pedagogia': 'Education (Pedagogy)',
  'Administração': 'Business Administration',
  'Direito': 'Law',
  'Enfermagem': 'Nursing',
  'Sistemas de informação': 'Information Systems',
  'Psicologia': 'Psychology',
  'Contabilidade': 'Accounting',
  'Educação física': 'Physical Education',
  'Educação física formação de professor': 'Physical Education (teacher training)',
  'Medicina': 'Medicine',
  'Fisioterapia': 'Physical Therapy',
  'Farmácia': 'Pharmacy',
  'Gestão de pessoas': 'Human Resources Management',
  'Biomedicina': 'Biomedicine',
  'Nutrição': 'Nutrition',
  'Engenharia civil': 'Civil Engineering',
  'Odontologia': 'Dentistry',
  'Medicina veterinária': 'Veterinary Medicine',
  'Agronomia': 'Agronomy',
  'Logística': 'Logistics',
  'Ciência da computação': 'Computer Science',
  'Engenharia de produção': 'Industrial Engineering',
  'Serviço social': 'Social Work',
  'Arquitetura e urbanismo': 'Architecture and Urban Planning',
  'Marketing': 'Marketing',
  'Engenharia mecânica': 'Mechanical Engineering',
  'Engenharia elétrica': 'Electrical Engineering',
  'Gestão de negócios': 'Business Management',
  'História formação de professor': 'History (teacher training)',
  'Matemática formação de professor': 'Mathematics (teacher training)',
  'Gestão comercial': 'Sales Management',
  'Letras português formação de professor': 'Portuguese Language (teacher training)',
  'Gestão financeira': 'Financial Management',
  'Gestão pública': 'Public Management',
  'Estética e cosmética': 'Aesthetics and Cosmetics',
  'Publicidade e propaganda': 'Advertising',
  'Biologia formação de professor': 'Biology (teacher training)',
  'Engenharia de software': 'Software Engineering',
  'Economia': 'Economics',
  'Engenharia de computação (DCN Engenharia)': 'Computer Engineering',
  'Gestão da tecnologia da informação': 'IT Management',
  'Teologia': 'Theology',
  'Geografia formação de professor': 'Geography (teacher training)',
  'Jornalismo': 'Journalism',
  'Design gráfico': 'Graphic Design',
  'Letras português inglês formação de professor': 'Portuguese and English (teacher training)',
  'Segurança pública': 'Public Safety',
  'ABI Saúde e bem-estar': 'Broad-entry: Health and welfare',
  'Investigação e perícia': 'Forensic Investigation',
  'Terapia ocupacional': 'Occupational Therapy',
  'Biologia': 'Biology',
  'Gestão da qualidade': 'Quality Management',
  'Gastronomia': 'Culinary Arts',
  'Gestão ambiental': 'Environmental Management',
  'Radiologia': 'Radiology',
  'Gestão da produção': 'Production Management',
  'Relações internacionais': 'International Relations',
  'Química formação de professor': 'Chemistry (teacher training)',
  'Letras inglês formação de professor': 'English Language (teacher training)',
  'Artes visuais formação de professor': 'Visual Arts (teacher training)',
  'Programas interdisciplinares abrangendo ciências naturais, matemática e estatística':
    'Interdisciplinary programmes: natural sciences, mathematics and statistics',
  'Ciência de dados': 'Data Science',
  'Engenharia química': 'Chemical Engineering',
  'Design de interiores': 'Interior Design',
  'Física formação de professor': 'Physics (teacher training)',
  'Gestão hospitalar': 'Hospital Management',
  'Programas abrangendo ciências sociais, comunicação e informação em processo de definição da classificação':
    'Social sciences, journalism and information: classification pending',
  'Psicopedagogia': 'Educational Psychology',
  'Moda': 'Fashion',
  'Serviços jurídicos e cartoriais': 'Legal and Notary Services',
  'Fonoaudiologia': 'Speech Therapy',
  'Comércio exterior': 'Foreign Trade',
  'Segurança privada': 'Private Security',
  'Engenharia de controle e automação': 'Control and Automation Engineering',
  'Segurança no trabalho': 'Occupational Safety',
  'Design': 'Design',
  'Filosofia formação de professor': 'Philosophy (teacher training)',
  'Redes de computadores': 'Computer Networks',
  'Gestão do agronegócio': 'Agribusiness Management',
  'Zootecnia': 'Animal Science',
  'Educação especial formação de professor': 'Special Education (teacher training)',
  'Música formação de professor': 'Music (teacher training)',
  'Turismo': 'Tourism',
  'Engenharia ambiental': 'Environmental Engineering',
  'Administração pública': 'Public Administration',
  'Práticas integrativas': 'Integrative Health Practices',
  'Podologia': 'Podiatry',
  'Ciências sociais formação de professor': 'Social Sciences (teacher training)',
  'Sistemas para internet': 'Web Systems',
  'Engenharia ambiental e sanitária': 'Environmental and Sanitary Engineering',
  'Química': 'Chemistry',
  'Programas interdisciplinares abrangendo computação e Tecnologias da Informação e Comunicação (TIC)':
    'Interdisciplinary programmes: computing and ICTs',
  'Biblioteconomia': 'Library Science',
  'Secretariado': 'Executive Secretarial Studies',
  'Negócios imobiliários': 'Real Estate',
  'Computação formação de professor': 'Computing (teacher training)',
  'Letras língua brasileira de sinais formação de professor': 'Brazilian Sign Language (teacher training)',
  'Automação industrial': 'Industrial Automation',
  'Programas interdisciplinares abrangendo educação': 'Interdisciplinary programmes: education',
  'Defesa cibernética': 'Cyber Defense',
  'Relações públicas': 'Public Relations',
  'Segurança da informação': 'Information Security',
  'Engenharia de alimentos': 'Food Engineering',
  'Ciências sociais': 'Social Sciences',
  'Geografia': 'Geography',
  'Ensino profissionalizante em área específica formação de professor':
    'Vocational teaching in a specific field (teacher training)',
  'Letras português espanhol formação de professor': 'Portuguese and Spanish (teacher training)',
  'Engenharia florestal': 'Forestry Engineering',
  'Química industrial e tecnológica': 'Industrial and Technological Chemistry',
  'Cinema e audiovisual': 'Film and Audiovisual',
  'Filosofia': 'Philosophy',
  'Optometria': 'Optometry',
  'Jogos digitais': 'Digital Games',
  'História': 'History',
  'ABI Artes e humanidades': 'Broad-entry: Arts and humanities',
  'Engenharia mecatrônica': 'Mechatronics Engineering',
  'Empreendedorismo': 'Entrepreneurship',
  'Gestão da saúde': 'Healthcare Management',
  'Banco de dados': 'Databases',
  'Artes visuais': 'Visual Arts',
  'Ciências naturais formação de professor': 'Natural Sciences (teacher training)',
  'Programas interdisciplinares abrangendo ciências sociais, comunicação e informação':
    'Interdisciplinary programmes: social sciences, journalism and information',
  'Letras português': 'Portuguese Language',
  'Letras espanhol formação de professor': 'Spanish Language (teacher training)',
  'Animação': 'Animation',
  'Gerontologia': 'Gerontology',
  'Alimentos': 'Food Technology',
  'Física': 'Physics',
  'Teatro formação de professor': 'Theatre (teacher training)',
  'ABI Ciências naturais, matemática e estatística': 'Broad-entry: Natural sciences, mathematics and statistics',
  'Outros cursos': 'Other programmes',
};

/* Interface. Preenchido a partir da auditoria de `__faltando()` — se algo escapar,
 * a tela mostra o português, nunca uma chave crua.                                */
const EN = {
  ...Object.fromEntries(Object.entries(EN_REGIAO)),
  ...Object.fromEntries(Object.entries(EN_AREA)),
};

export function registrarEN(mapa) { Object.assign(EN, mapa); }
