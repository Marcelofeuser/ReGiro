const byId = (id) => document.getElementById(id);
const demo = [
  { id: 'demo-1', title: 'Kit de embreagem', code: 'LuK · REF-001', vehicle: 'Fiat Palio 1.4', city: 'Curitiba, PR', condition: 'Nova lacrada', price: 540, mode: 'Venda e troca' },
  { id: 'demo-2', title: 'Jogo de pastilhas de freio', code: 'Bosch · REF-002', vehicle: 'Volkswagen Gol 1.6', city: 'São Paulo, SP', condition: 'Nova lacrada', price: 165, mode: 'Venda' },
  { id: 'demo-3', title: 'Alternador 90 A', code: 'Valeo · REF-003', vehicle: 'Chevrolet Onix 1.4', city: 'Joinville, SC', condition: 'Usada revisada', price: 720, mode: 'Venda e troca' },
];
const currency = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });
const read = (key) => JSON.parse(localStorage.getItem(key) || '[]');
const listings = read('regiro.listings');
const favorites = new Set(read('regiro.favorites'));
const normalize = (value) => value.toLowerCase().normalize('NFD').replace(/\p{Diacritic}/gu, '');
function element(tag, content, className = '') {
  const node = document.createElement(tag);
  node.textContent = content;
  node.className = className;
  return node;
}
function render() {
  const terms = normalize(byId('search').value).trim().split(/\s+/);
  const mode = byId('mode').value;
  const sort = byId('sort').value;
  const visible = [...listings, ...demo].filter((item) => {
    const haystack = normalize([item.title, item.code, item.vehicle, item.city].join(' '));
    return terms.every((term) => haystack.includes(term))
      && (!mode || item.mode === mode)
      && (!byId('saved').checked || favorites.has(item.id));
  });
  if (sort) visible.sort((a, b) => sort === 'asc' ? a.price - b.price : b.price - a.price);
  byId('count').textContent = visible.length ? `${visible.length} peça(s) encontrada(s)` : 'Nenhuma peça encontrada.';
  byId('results').replaceChildren(...visible.map((item) => {
    const card = element('article', '');
    const favorite = element('button', favorites.has(item.id) ? 'Remover dos salvos' : 'Salvar peça');
    favorite.setAttribute('aria-pressed', String(favorites.has(item.id)));
    favorite.addEventListener('click', () => {
      if (favorites.has(item.id)) favorites.delete(item.id);
      else favorites.add(item.id);
      localStorage.setItem('regiro.favorites', JSON.stringify([...favorites]));
      render();
    });
    card.append(element('span', item.mode, 'tag'), element('h3', item.title),
      element('p', [item.code, item.vehicle].filter(Boolean).join(' · ')),
      element('p', `${item.condition} · ${item.city}`),
      element('strong', currency.format(item.price), 'price'), favorite);
    return card;
  }));
}
for (const id of ['search', 'mode', 'sort', 'saved']) byId(id).addEventListener('input', render);
const editor = byId('editor');
byId('announce').addEventListener('click', () => editor.showModal());
byId('close').addEventListener('click', () => editor.close());
byId('listing').addEventListener('submit', (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.currentTarget));
  listings.unshift({ ...data, id: crypto.randomUUID(), price: Number(data.price) });
  localStorage.setItem('regiro.listings', JSON.stringify(listings));
  event.currentTarget.reset();
  editor.close();
  byId('search').value = '';
  byId('mode').value = '';
  byId('sort').value = '';
  byId('saved').checked = false;
  render();
  document.getElementById('catalogo').scrollIntoView();
});
render();
