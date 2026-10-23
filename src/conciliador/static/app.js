"use strict";

const STATUS = {
  conciliado: "Conciliado",
  suspeito: "Suspeito",
  duplicado: "Duplicado",
  pendente: "Pendente",
  sem_pedido: "Sem pedido",
  ignorado: "Ignorado",
};

const ATTENTION = ["suspeito", "duplicado", "sem_pedido", "pendente"];

const ARROW_SVG =
  '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14m0 0l-5-5m5 5l-5 5" ' +
  'fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>';

const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const dateTime = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

const $ = (id) => document.getElementById(id);

const state = { rows: [], summary: null, filter: null, query: "" };

function el(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (key === "class") node.className = value;
    else node.setAttribute(key, value);
  }
  for (const child of children) {
    if (child === null || child === undefined) continue;
    node.append(child);
  }
  return node;
}

const brl = (value) => money.format(value);
const when = (iso) => dateTime.format(new Date(iso));
const signed = (value) => (value > 0 ? "+" : "") + brl(value);

/* upload */

const files = { pedidos: null, extrato: null };

function setupDropzone(zoneId, inputId, key) {
  const zone = $(zoneId);
  const input = $(inputId);
  const hint = zone.querySelector(".dz-hint");

  const accept = (file) => {
    files[key] = file || null;
    zone.classList.toggle("filled", Boolean(file));
    hint.textContent = file ? file.name : hint.dataset.default;
    $("btn-run").disabled = !(files.pedidos && files.extrato);
  };

  input.addEventListener("change", () => accept(input.files[0]));
  zone.addEventListener("dragover", (event) => {
    event.preventDefault();
    zone.classList.add("drag");
  });
  zone.addEventListener("dragleave", () => zone.classList.remove("drag"));
  zone.addEventListener("drop", (event) => {
    event.preventDefault();
    zone.classList.remove("drag");
    const file = event.dataTransfer.files[0];
    if (!file) return;
    const transfer = new DataTransfer();
    transfer.items.add(file);
    input.files = transfer.files;
    accept(file);
  });
}

function resetUploads() {
  for (const id of ["file-pedidos", "file-extrato"]) $(id).value = "";
  for (const zone of document.querySelectorAll(".dropzone")) {
    zone.classList.remove("filled");
    const hint = zone.querySelector(".dz-hint");
    hint.textContent = hint.dataset.default;
  }
  files.pedidos = null;
  files.extrato = null;
  $("btn-run").disabled = true;
}

/* requests */

function show(view) {
  $("intro").hidden = view !== "intro";
  $("loading").hidden = view !== "loading";
  $("results").hidden = view !== "results";
  window.scrollTo({ top: 0 });
}

function showError(message) {
  const box = $("error");
  box.textContent = message;
  box.hidden = false;
}

async function load(request, sourceLabel) {
  $("error").hidden = true;
  show("loading");
  try {
    const response = await request();
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail || "Algo deu errado ao conciliar. Tente novamente.");
    }
    const data = await response.json();
    state.rows = data.linhas;
    state.summary = data.resumo;
    state.filter = null;
    state.query = "";
    $("search").value = "";
    render(sourceLabel);
    show("results");
  } catch (error) {
    show("intro");
    showError(error.message);
  }
}

function runUpload() {
  const body = new FormData();
  body.append("pedidos", files.pedidos);
  body.append("extrato", files.extrato);
  load(() => fetch("/api/conciliacao", { method: "POST", body }), "Arquivos enviados por você");
}

function runSample() {
  load(() => fetch("/api/exemplo"), "Dados de exemplo do projeto");
}

/* rendering */

function render(sourceLabel) {
  const { rows, summary } = state;
  const count = summary.contagem;
  const orders = new Set(rows.filter((r) => r.pedido).map((r) => r.pedido));

  $("results-sub").textContent = `${sourceLabel} · ${orders.size} pedidos analisados`;

  const reconciledOrders = new Set(
    rows.filter((r) => r.resultado === "conciliado").map((r) => r.pedido),
  );
  $("kpi-ok").textContent = brl(summary.valor_conciliado);
  $("kpi-ok-sub").textContent = `${reconciledOrders.size} pedidos pagos e conferidos`;
  $("kpi-pending").textContent = brl(summary.valor_pendente);
  $("kpi-pending-sub").textContent = `${count.pendente || 0} pedidos aguardando pagamento`;
  $("kpi-review").textContent = brl(summary.valor_revisar);
  const toReview = (count.suspeito || 0) + (count.duplicado || 0);
  $("kpi-review-sub").textContent = `${toReview} Pix suspeitos ou duplicados`;

  renderBar(count);
  renderCards();
  renderChips();
  renderTable();
  renderIgnored();
}

function renderBar(count) {
  const bar = $("bar");
  const legend = $("legend");
  bar.replaceChildren();
  legend.replaceChildren();
  for (const [status, label] of Object.entries(STATUS)) {
    const n = count[status] || 0;
    if (!n) continue;
    const segment = el("span", { class: `s-${status}`, title: `${label}: ${n}` });
    segment.style.flexGrow = n;
    bar.append(segment);
    legend.append(
      el("span", { class: `legend-item s-${status}` }, `${label} `, el("strong", {}, String(n))),
    );
  }
}

function side(label, name, value, date, emptyText) {
  if (name === null && value === null) {
    return el("div", { class: "side" }, el("span", { class: "side-label" }, label), el("span", { class: "side-empty" }, emptyText));
  }
  return el(
    "div",
    { class: "side" },
    el("span", { class: "side-label" }, label),
    el("span", { class: "side-name" }, name || "Sem nome no extrato"),
    el("span", { class: "side-value" }, brl(value)),
    el("span", { class: "side-date" }, when(date)),
  );
}

function card(row) {
  const hasOrder = Boolean(row.pedido);
  const hasPix = Boolean(row.id_transacao);

  const arrow = el("span", { class: "vs" });
  arrow.innerHTML = ARROW_SVG;

  const foot = el("div", { class: "card-foot" }, el("span", {}, row.motivo));
  if (row.diferenca) foot.append(el("span", { class: "diff" }, signed(row.diferenca)));

  return el(
    "article",
    { class: `card s-${row.resultado}` },
    el(
      "div",
      { class: "card-head" },
      el("span", { class: "pill" }, STATUS[row.resultado]),
      el("span", { class: "card-id" }, hasOrder ? `Pedido ${row.pedido}` : "Sem pedido"),
    ),
    el(
      "div",
      { class: "card-sides" },
      side("Pedido", hasOrder ? row.cliente : null, hasOrder ? row.valor_pedido : null, row.data_pedido, "Nenhum pedido"),
      arrow,
      side("Pix recebido", hasPix ? row.pagador : null, hasPix ? row.valor_pix : null, row.data_pix, "Nenhum Pix"),
    ),
    foot,
  );
}

function renderCards() {
  const box = $("cards");
  box.replaceChildren();
  const attention = ATTENTION.flatMap((status) =>
    state.rows.filter((row) => row.resultado === status),
  );
  if (!attention.length) {
    box.append(el("p", { class: "all-clear" }, "Tudo conferido. Nenhum caso precisa de atenção."));
    return;
  }
  for (const row of attention) box.append(card(row));
}

function renderChips() {
  const box = $("chips");
  box.replaceChildren();
  const count = state.summary.contagem;
  const total = state.rows.filter((r) => r.resultado !== "ignorado").length;

  const make = (status, label, n) => {
    const chip = el(
      "button",
      { class: `chip${status ? ` s-${status}` : ""}`, type: "button", "aria-pressed": String(state.filter === status) },
      label,
      el("span", { class: "n" }, String(n)),
    );
    chip.addEventListener("click", () => {
      state.filter = status;
      renderChips();
      renderTable();
    });
    return chip;
  };

  box.append(make(null, "Todos", total));
  for (const status of Object.keys(STATUS)) {
    if (status === "ignorado" || !count[status]) continue;
    box.append(make(status, STATUS[status], count[status]));
  }
}

function dash() {
  return el("span", { class: "dash" }, "—");
}

function renderTable() {
  const body = $("rows");
  body.replaceChildren();
  const query = state.query.trim().toLowerCase();

  const visible = state.rows.filter((row) => {
    if (row.resultado === "ignorado") return false;
    if (state.filter && row.resultado !== state.filter) return false;
    if (!query) return true;
    return [row.pedido, row.cliente, row.pagador].some((text) => text.toLowerCase().includes(query));
  });

  $("empty").hidden = visible.length > 0;

  for (const row of visible) {
    const payer = row.id_transacao ? row.pagador || "Sem nome no extrato" : null;
    body.append(
      el(
        "tr",
        {},
        el("td", { class: "id" }, row.pedido || "—"),
        el("td", {}, row.cliente || dash()),
        el("td", { class: "num" }, row.valor_pedido === null ? dash() : brl(row.valor_pedido)),
        el("td", {}, payer || dash()),
        el("td", { class: "num" }, row.valor_pix === null ? dash() : brl(row.valor_pix)),
        el("td", { class: `s-${row.resultado}` }, el("span", { class: "pill" }, STATUS[row.resultado])),
      ),
    );
  }
}

function renderIgnored() {
  const ignored = state.rows.filter((row) => row.resultado === "ignorado");
  $("ignored").hidden = ignored.length === 0;
  $("ignored-title").textContent = `${ignored.length} lançamentos ignorados`;
  const list = $("ignored-list");
  list.replaceChildren();
  for (const row of ignored) {
    list.append(el("li", {}, el("span", {}, row.observacao || row.id_transacao), el("span", {}, brl(row.valor_pix))));
  }
}

/* export */

function downloadCsv() {
  const lines = ["pedido;id_transacao;resultado"];
  for (const row of state.rows) lines.push(`${row.pedido};${row.id_transacao};${row.resultado}`);
  const blob = new Blob([lines.join("\n") + "\n"], { type: "text/csv;charset=utf-8" });
  const link = el("a", { href: URL.createObjectURL(blob), download: "conciliacao.csv" });
  link.click();
  URL.revokeObjectURL(link.href);
}

/* init */

setupDropzone("drop-pedidos", "file-pedidos", "pedidos");
setupDropzone("drop-extrato", "file-extrato", "extrato");

$("btn-run").addEventListener("click", runUpload);
$("btn-sample").addEventListener("click", runSample);
$("btn-download").addEventListener("click", downloadCsv);
$("btn-reset").addEventListener("click", () => {
  resetUploads();
  $("error").hidden = true;
  show("intro");
});
$("search").addEventListener("input", (event) => {
  state.query = event.target.value;
  renderTable();
});
