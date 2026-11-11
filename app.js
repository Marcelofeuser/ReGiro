const state = {
  settings: {
    saleCommissionRate: 0.06,
    tradeFee: 10,
    vipMonthlyPrice: 49.9,
    vipMonthlyFreeTrades: 1,
    vipAdditionalTradeDiscountRate: 0.2,
    vipEarlyAccess: true,
    vipPriorityAlerts: true,
    vipTrialDays: 7,
    vipCoupon: "BEMVINDO10",
  },
  stores: [],
  listings: [],
  negotiations: [],
  chats: [],
  vipSubscriptions: [],
  alerts: [],
  savedListings: [],
};

const formatBRL = (value) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value || 0);
const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (character) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
}[character]));
const nowIso = () => new Date().toISOString();
const uid = (arr) => arr.length + 1;

const isValidCnpj = (value) => {
  const cnpj = String(value || "").replace(/\D/g, "");
  if (cnpj.length !== 14 || /^([0-9])\1{13}$/.test(cnpj)) return false;
  const digit = (base, weights) => {
    const sum = [...base].reduce((total, number, index) => total + Number(number) * weights[index], 0);
    const remainder = sum % 11;
    return remainder < 2 ? 0 : 11 - remainder;
  };
  const first = digit(cnpj.slice(0, 12), [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]);
  const second = digit(cnpj.slice(0, 12) + first, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]);
  return cnpj.endsWith(String(first) + String(second));
};

const getVip = (storeId) => state.vipSubscriptions.find((v) => v.storeId === storeId && new Date(v.endsAt) >= new Date());

const countMonthlyFreeTradeUsed = (storeId, monthKey) => state.negotiations.filter((n) => n.type === "trade" && n.storeId === storeId && n.concludedAt && n.monthKey === monthKey && n.freeTradeApplied).length;

const monthKeyNow = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
};

const el = {
  commissionValue: document.getElementById("commissionValue"),
  tradeFeeValue: document.getElementById("tradeFeeValue"),
  storeForm: document.getElementById("storeForm"),
  storeMessage: document.getElementById("storeMessage"),
  storesList: document.getElementById("storesList"),
  listingForm: document.getElementById("listingForm"),
  listingMessage: document.getElementById("listingMessage"),
  listings: document.getElementById("listings"),
  searchForm: document.getElementById("searchForm"),
  saveListingForm: document.getElementById("saveListingForm"),
  savedListings: document.getElementById("savedListings"),
  negotiationForm: document.getElementById("negotiationForm"),
  negotiationPreview: document.getElementById("negotiationPreview"),
  negotiations: document.getElementById("negotiations"),
  acceptByStarter: document.getElementById("acceptByStarter"),
  acceptByReceiver: document.getElementById("acceptByReceiver"),
  confirmReceipt: document.getElementById("confirmReceipt"),
  chatForm: document.getElementById("chatForm"),
  chatLog: document.getElementById("chatLog"),
  vipRules: document.getElementById("vipRules"),
  vipForm: document.getElementById("vipForm"),
  vipStatus: document.getElementById("vipStatus"),
  alertForm: document.getElementById("alertForm"),
  alertsList: document.getElementById("alertsList"),
  dashboardForm: document.getElementById("dashboardForm"),
  storeDashboard: document.getElementById("storeDashboard"),
  adminConfigForm: document.getElementById("adminConfigForm"),
  verifyStoreForm: document.getElementById("verifyStoreForm"),
  adminMessage: document.getElementById("adminMessage"),
  adminSummary: document.getElementById("adminSummary"),
};

const renderRules = () => {
  el.commissionValue.textContent = `${(state.settings.saleCommissionRate * 100).toFixed(1)}%`;
  el.tradeFeeValue.textContent = formatBRL(state.settings.tradeFee);
  el.vipRules.textContent = `Preço mensal ${formatBRL(state.settings.vipMonthlyPrice)} · 1 troca sem tarifa/mês · ${Math.round(state.settings.vipAdditionalTradeDiscountRate * 100)}% de desconto nas trocas adicionais · teste ${state.settings.vipTrialDays} dias · cupom: ${state.settings.vipCoupon || "-"}.`;
};

const renderStores = () => {
  el.storesList.innerHTML = state.stores.map((s) => `<div class="list-item">#${s.id} ${escapeHtml(s.nomeFantasia)} (${escapeHtml(s.cnpj)}) · status: ${s.status === "verified" ? "Loja verificada ✅" : s.status}</div>`).join("") || "<p>Nenhuma loja cadastrada.</p>";
};

const renderListings = (items = state.listings) => {
  el.listings.innerHTML = items.map((l) => `<div class="list-item"><strong>#${l.id} ${escapeHtml(l.titulo)}</strong><br>${escapeHtml(l.fabricante)} · ${escapeHtml(l.codigoPeca)} · ${escapeHtml(l.condicao)}<br>${formatBRL(l.preco)} · ${escapeHtml(l.localizacao)} · ${l.distanciaKm}km · status: ${escapeHtml(l.status)}<br>NF: ${escapeHtml(l.notaFiscal)} · Garantia: ${escapeHtml(l.garantia)} · Procedência: ${escapeHtml(l.procedencia)}<br><small>Entrega: ${escapeHtml(l.entrega)} · Negociação: ${l.vendaDireta ? "venda" : ""}${l.aceitaTroca ? " troca" : ""}</small></div>`).join("") || "<p>Sem anúncios.</p>";
};

const renderNegotiations = () => {
  el.negotiations.innerHTML = state.negotiations.map((n) => `<div class="list-item">#${n.id} ${n.type === "trade" ? "Troca" : "Venda"} · anúncio #${n.listingId} · iniciadora #${n.storeId}<br>Tarifa prevista: ${formatBRL(n.tradeFeePreview || 0)} · comissão prevista: ${formatBRL(n.saleCommissionPreview || 0)}<br>Aceites: iniciadora ${n.acceptStarter ? "✅" : "❌"} / outra loja ${n.acceptReceiver ? "✅" : "❌"}<br>Status: ${escapeHtml(n.status)}${n.netSellerEstimate != null ? ` · líquido vendedor ${formatBRL(n.netSellerEstimate)}` : ""}</div>`).join("") || "<p>Sem negociações.</p>";
};

const renderChat = () => {
  el.chatLog.innerHTML = state.chats.map((c) => `<div class="list-item">Anúncio #${c.listingId} · ${escapeHtml(c.sender)}: ${escapeHtml(c.message)}</div>`).join("") || "<p>Sem mensagens.</p>";
};

const renderVip = () => {
  el.vipStatus.innerHTML = state.vipSubscriptions.map((v) => {
    const used = countMonthlyFreeTradeUsed(v.storeId, monthKeyNow());
    const remaining = Math.max(0, state.settings.vipMonthlyFreeTrades - used);
    return `<div class="list-item">Loja #${v.storeId} · ativa até ${new Date(v.endsAt).toLocaleDateString("pt-BR")} · próxima cobrança ${new Date(v.endsAt).toLocaleDateString("pt-BR")} · isenções restantes no mês: ${remaining}</div>`;
  }).join("") || "<p>Sem assinaturas ativas.</p>";
};

const renderAlerts = () => {
  el.alertsList.innerHTML = state.alerts.map((a) => `<div class="list-item">Loja #${a.storeId}: ${escapeHtml(a.alert)}</div>`).join("") || "<p>Sem alertas.</p>";
};

const renderSavedListings = () => {
  el.savedListings.innerHTML = state.savedListings.map((s) => `<div class="list-item">Loja #${s.storeId} salvou anúncio #${s.listingId}</div>`).join("") || "<p>Nenhum anúncio salvo.</p>";
};

const renderAdmin = () => {
  const subscriptions = state.vipSubscriptions.length;
  const cancelled = 0;
  const delinquent = 0;
  const disputes = state.negotiations.filter((n) => n.status === "dispute").length;
  el.adminSummary.innerHTML = `<div class="list-item">Lojas: ${state.stores.length} · anúncios: ${state.listings.length} · negociações: ${state.negotiations.length}<br>Assinaturas ativas: ${subscriptions} · canceladas: ${cancelled} · inadimplentes: ${delinquent}<br>Disputas: ${disputes}. Histórico de alterações mantido nesta sessão de teste.</div>`;
};

el.storeForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target).entries());
  if (!isValidCnpj(data.cnpj)) {
    el.storeMessage.textContent = "CNPJ inválido. Use o formato 00.000.000/0000-00.";
    return;
  }
  const store = {
    id: uid(state.stores),
    ...data,
    status: "pending",
    createdAt: nowIso(),
  };
  state.stores.push(store);
  el.storeMessage.textContent = `Loja #${store.id} cadastrada com sucesso. Aguardando aprovação para selo Loja verificada.`;
  e.target.reset();
  renderStores();
  renderAdmin();
});

el.listingForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target).entries());
  const ownerStore = state.stores.find((store) => store.id === Number(data.storeId));
  if (!ownerStore || ownerStore.status !== "verified") {
    el.listingMessage.textContent = "Informe uma loja cadastrada e verificada para publicar.";
    return;
  }
  const listing = {
    id: uid(state.listings),
    ...data,
    storeId: Number(data.storeId),
    quantidade: Number(data.quantidade),
    preco: Number(data.preco),
    distanciaKm: Number(data.distanciaKm || 0),
    vendaDireta: !!data.vendaDireta,
    aceitaOferta: !!data.aceitaOferta,
    aceitaTroca: !!data.aceitaTroca,
    status: "ativo",
    createdAt: nowIso(),
  };
  state.listings.push(listing);
  el.listingMessage.textContent = `Anúncio #${listing.id} publicado.`;
  e.target.reset();
  renderListings();
  renderAdmin();
});

el.searchForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target).entries());
  const q = (data.q || "").toLowerCase();
  const filtered = [...state.listings].filter((l) => {
    const searchable = `${l.titulo} ${l.fabricante} ${l.codigoPeca} ${l.codigoOem} ${l.aplicacao}`.toLowerCase();
    if (q && !searchable.includes(q)) return false;
    if (data.categoria && l.categoria !== data.categoria) return false;
    if (data.localizacao && !l.localizacao.toLowerCase().includes(data.localizacao.toLowerCase())) return false;
    if (data.condicao && l.condicao !== data.condicao) return false;
    if (data.precoMax && l.preco > Number(data.precoMax)) return false;
    if (data.distanciaMax && l.distanciaKm > Number(data.distanciaMax)) return false;
    if (data.negociacao === "troca" && !l.aceitaTroca) return false;
    if (data.negociacao === "venda" && !l.vendaDireta) return false;
    return true;
  }).sort((a, b) => {
    if (data.ordem === "preco") return a.preco - b.preco;
    if (data.ordem === "data") return new Date(b.createdAt) - new Date(a.createdAt);
    if (data.ordem === "distancia") return a.distanciaKm - b.distanciaKm;
    return 0;
  });
  renderListings(filtered);
});

el.saveListingForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target).entries());
  const listingId = Number(data.listingId);
  const storeId = Number(data.storeId);
  if (!state.listings.find((l) => l.id === listingId) || !state.stores.find((s) => s.id === storeId)) return;
  const alreadySaved = state.savedListings.find((s) => s.storeId === storeId && s.listingId === listingId);
  if (!alreadySaved) state.savedListings.push({ storeId, listingId });
  e.target.reset();
  renderSavedListings();
});

el.negotiationForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target).entries());
  const listing = state.listings.find((l) => l.id === Number(data.listingId));
  if (!listing || listing.status !== "ativo") {
    el.negotiationPreview.textContent = "Anúncio não encontrado ou indisponível.";
    return;
  }
  const starterStore = state.stores.find((store) => store.id === Number(data.storeId));
  if (!starterStore || starterStore.status !== "verified") {
    el.negotiationPreview.textContent = "A loja iniciadora precisa estar cadastrada e verificada.";
    return;
  }
  if (listing.storeId === starterStore.id) {
    el.negotiationPreview.textContent = "A loja não pode negociar com o próprio anúncio.";
    return;
  }
  if (!["sale", "trade"].includes(data.type)) {
    el.negotiationPreview.textContent = "Tipo de negociação inválido.";
    return;
  }
  if (data.type === "trade") {
    const ownListing = state.listings.find((item) => item.id === Number(data.ownListingId));
    if (!listing.aceitaTroca || !ownListing || ownListing.storeId !== starterStore.id || ownListing.status !== "ativo") {
      el.negotiationPreview.textContent = "A troca exige um anúncio disponível da loja iniciadora e outro anúncio que aceite troca.";
      return;
    }
  } else if (!listing.vendaDireta && !listing.aceitaOferta) {
    el.negotiationPreview.textContent = "Este anúncio não está aceitando ofertas de venda.";
    return;
  }
  const offerValue = Number(data.offerValue || 0);
  const cashDifference = Number(data.cashDifference || 0);
  if (!Number.isFinite(offerValue) || offerValue < 0 || !Number.isFinite(cashDifference)) {
    el.negotiationPreview.textContent = "Informe valores válidos para a proposta.";
    return;
  }

  const negotiation = {
    id: uid(state.negotiations),
    type: data.type,
    storeId: Number(data.storeId),
    listingId: Number(data.listingId),
    ownListingId: data.ownListingId ? Number(data.ownListingId) : null,
    offerValue,
    cashDifference,
    acceptStarter: false,
    acceptReceiver: false,
    receiptConfirmed: false,
    status: "aberta",
    monthKey: monthKeyNow(),
    providerFeePreview: Number((listing.preco * 0.0399).toFixed(2)),
    saleCommissionPreview: data.type === "sale" ? Number((listing.preco * state.settings.saleCommissionRate).toFixed(2)) : 0,
    tradeFeePreview: 0,
    freeTradeApplied: false,
    netSellerEstimate: null,
  };

  if (data.type === "trade") {
    const vip = getVip(negotiation.storeId);
    let fee = state.settings.tradeFee;
    if (vip) {
      const used = countMonthlyFreeTradeUsed(negotiation.storeId, negotiation.monthKey);
      if (used < state.settings.vipMonthlyFreeTrades) {
        fee = 0;
        negotiation.freeTradeApplied = true;
      } else {
        fee = Number((fee * (1 - state.settings.vipAdditionalTradeDiscountRate)).toFixed(2));
      }
    }
    negotiation.tradeFeePreview = fee;
  }

  if (data.type === "sale") {
    negotiation.netSellerEstimate = Number((listing.preco - negotiation.providerFeePreview - negotiation.saleCommissionPreview).toFixed(2));
  }

  state.negotiations.push(negotiation);
  el.negotiationPreview.textContent = data.type === "trade"
    ? `Tarifa da troca para a loja iniciadora (#${negotiation.storeId}): ${formatBRL(negotiation.tradeFeePreview)}. Cobrada uma única vez na conclusão.`
    : `Resumo da venda: preço ${formatBRL(listing.preco)}, taxa provedor ${formatBRL(negotiation.providerFeePreview)}, comissão ReGiro ${formatBRL(negotiation.saleCommissionPreview)}, líquido estimado ${formatBRL(negotiation.netSellerEstimate)}.`;
  renderNegotiations();
  renderAdmin();
});

const currentNegotiation = () => state.negotiations[state.negotiations.length - 1];

el.acceptByStarter.addEventListener("click", () => {
  const n = currentNegotiation();
  if (!n || n.concludedAt || n.status === "cancelada") return;
  n.acceptStarter = true;
  n.status = "aguardando confirmação";
  renderNegotiations();
});

el.acceptByReceiver.addEventListener("click", () => {
  const n = currentNegotiation();
  if (!n || n.concludedAt || n.status === "cancelada") return;
  n.acceptReceiver = true;
  n.status = "aguardando confirmação";
  renderNegotiations();
});

el.confirmReceipt.addEventListener("click", () => {
  const n = currentNegotiation();
  if (!n || n.concludedAt || n.status === "cancelada") return;
  if (!n.acceptStarter || !n.acceptReceiver) {
    n.status = "pendente dos dois aceites";
  } else {
    n.receiptConfirmed = true;
    n.status = n.type === "trade" ? "trocado" : "vendido";
    n.concludedAt = nowIso();
    const listing = state.listings.find((l) => l.id === n.listingId);
    if (listing) listing.status = n.status;
    if (n.type === "trade" && n.ownListingId) {
      const ownListing = state.listings.find((item) => item.id === n.ownListingId);
      if (ownListing) ownListing.status = "trocado";
    }
  }
  renderListings();
  renderNegotiations();
  renderVip();
  renderAdmin();
});

el.chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target).entries());
  state.chats.push({ listingId: Number(data.listingId), sender: data.sender, message: data.message, createdAt: nowIso() });
  e.target.reset();
  renderChat();
});

el.vipForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target).entries());
  const storeId = Number(data.storeId);
  const store = state.stores.find((s) => s.id === storeId);
  if (!store) {
    el.vipStatus.innerHTML = "<p>Loja não encontrada.</p>";
    return;
  }
  const start = new Date();
  const end = new Date(start);
  end.setDate(end.getDate() + 30);
  const existing = state.vipSubscriptions.find((v) => v.storeId === storeId);
  if (existing) {
    existing.endsAt = end.toISOString();
  } else {
    state.vipSubscriptions.push({ storeId, startsAt: start.toISOString(), endsAt: end.toISOString() });
  }
  renderVip();
  renderAdmin();
});

el.alertForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target).entries());
  state.alerts.push({ storeId: Number(data.storeId), alert: data.alert });
  e.target.reset();
  renderAlerts();
});

el.dashboardForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target).entries());
  const storeId = Number(data.storeId);
  const ownNegotiations = state.negotiations.filter((n) => n.storeId === storeId);
  const ownSales = ownNegotiations.filter((n) => n.type === "sale");
  const ownTrades = ownNegotiations.filter((n) => n.type === "trade");
  const tradeFeesPaid = ownTrades.reduce((acc, n) => acc + (n.status === "trocado" ? n.tradeFeePreview : 0), 0);
  const savedWithVip = ownTrades.reduce((acc, n) => acc + (n.freeTradeApplied ? state.settings.tradeFee : 0), 0);
  const nextRenewal = getVip(storeId)?.endsAt;

  el.storeDashboard.innerHTML = `<div class="list-item">Anúncios ativos: ${state.listings.filter((l) => l.status === "ativo").length} · reservados: ${state.listings.filter((l) => l.status === "reservado").length} · vendidos: ${state.listings.filter((l) => l.status === "vendido").length} · trocados: ${state.listings.filter((l) => l.status === "trocado").length}<br>Ofertas enviadas: ${ownNegotiations.length} · vendas: ${ownSales.length} · trocas: ${ownTrades.length}<br>Tarifas de troca pagas: ${formatBRL(tradeFeesPaid)} · economizadas com VIP: ${formatBRL(savedWithVip)}<br>Próxima renovação VIP: ${nextRenewal ? new Date(nextRenewal).toLocaleDateString("pt-BR") : "sem assinatura"}<br>Alertas cadastrados: ${state.alerts.filter((a) => a.storeId === storeId).length}</div>`;
});

el.adminConfigForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target).entries());
  state.settings.saleCommissionRate = Number(data.commission) / 100;
  state.settings.tradeFee = Number(data.tradeFee);
  state.settings.vipMonthlyPrice = Number(data.vipPrice);
  state.settings.vipAdditionalTradeDiscountRate = Number(data.vipTradeDiscount) / 100;
  state.settings.vipTrialDays = Number(data.vipTrialDays);
  state.settings.vipCoupon = data.vipCoupon;
  el.adminMessage.textContent = "Configurações salvas com sucesso.";
  renderRules();
  renderVip();
  renderNegotiations();
});

el.verifyStoreForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target).entries());
  const store = state.stores.find((s) => s.id === Number(data.storeId));
  if (!store) {
    el.adminMessage.textContent = "Loja não encontrada.";
    return;
  }
  store.status = data.status;
  el.adminMessage.textContent = `Loja #${store.id} atualizada para ${data.status}.`;
  renderStores();
  renderAdmin();
});

renderRules();
renderStores();
renderListings();
renderNegotiations();
renderChat();
renderVip();
renderAlerts();
renderSavedListings();
renderAdmin();
