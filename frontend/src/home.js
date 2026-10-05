/** Inicio: saludo + tarjetas de estadísticas reales + repaso de hoy + diario
 * (feed.js ya rellena #feed-list) + accedido recientemente (mezcla docs/ del
 * propio UNED y documentos de estudio a fondo) + acceso directo a los
 * documentos en profundidad. */

import { uned, study } from "./api.js";
import { el } from "./dom.js";
import { icon } from "./icons.js";
import { documentCard } from "./study.js";
import { navigate } from "./router.js";
import { refreshRailStreak } from "./main.js";

const homeGreeting = document.getElementById("home-greeting");
const statCards = document.getElementById("stat-cards");
const recentList = document.getElementById("recent-list");
const recentPager = document.getElementById("recent-pager");
const homeStudyList = document.getElementById("home-study-list");
const dueReviewCard = document.getElementById("due-review-card");

const SECONDS_PER_CARD = 30; // grosero, solo para dar una estimación de tiempo

const PAGE_SIZE = 6;
let mergedRecent = [];
let currentPage = 1;

function renderGreeting() {
  const hour = new Date().getHours();
  const saludo = hour < 12 ? "Buenos días" : hour < 20 ? "Buenas tardes" : "Buenas noches";
  const fecha = new Date().toLocaleDateString("es-ES", { weekday: "long", day: "numeric", month: "long" });
  homeGreeting.replaceChildren(
    el("div", { id: "home-greeting-title" }, saludo),
    el("div", { id: "home-greeting-subtitle" }, `${fecha[0].toUpperCase()}${fecha.slice(1)} — esto es lo que ha pasado en tus asignaturas.`),
  );
}

async function loadStatCards() {
  statCards.replaceChildren();
  const [engagementRes, dueRes, docsRes] = await Promise.allSettled([
    study.engagementSummary(),
    study.dueReview(1),
    study.listDocuments(),
  ]);
  const stats = [];
  if (engagementRes.status === "fulfilled") {
    const e = engagementRes.value;
    stats.push({ icon: "flame", value: `${e.streak_days} día${e.streak_days === 1 ? "" : "s"}`, label: "Racha de estudio" });
    stats.push({ icon: "layers", value: String(e.reviewed_today), label: "Tarjetas repasadas hoy" });
  }
  if (dueRes.status === "fulfilled") {
    stats.push({ icon: "clock", value: String(dueRes.value.count_due), label: "Pendientes de repaso" });
  }
  if (docsRes.status === "fulfilled") {
    stats.push({ icon: "book-open", value: String(docsRes.value.length), label: "Documentos en profundidad" });
  }
  if (!stats.length) return; // motor no disponible: sin fila de estadísticas, sin error visible
  statCards.replaceChildren(
    ...stats.map((s) =>
      el(
        "div",
        { className: "stat-card" },
        el("div", { className: "stat-card-value-row" }, icon(s.icon, { size: 16 }), el("div", { className: "stat-card-value" }, s.value)),
        el("div", { className: "stat-card-label" }, s.label),
      ),
    ),
  );
}

async function loadRecent() {
  recentList.replaceChildren(el("p", { className: "hint" }, "Cargando…"));
  const [unedRes, studyRes] = await Promise.allSettled([uned.recent(1, 50), study.recentAccess(1, 50)]);
  const items = [];
  if (unedRes.status === "fulfilled") {
    items.push(...unedRes.value.items.map((i) => ({ kind: "doc", title: i.title, path: i.path, viewed_at: i.viewed_at })));
  }
  if (studyRes.status === "fulfilled") {
    items.push(
      ...studyRes.value.items
        .filter((i) => i.item_type === "document")
        .map((i) => ({ kind: "study", title: i.title, itemId: i.item_id, viewed_at: i.viewed_at })),
    );
  }
  items.sort((a, b) => (a.viewed_at < b.viewed_at ? 1 : -1));
  mergedRecent = items;
  currentPage = 1;
  renderRecentPage();
}

function renderRecentPage() {
  const start = (currentPage - 1) * PAGE_SIZE;
  const pageItems = mergedRecent.slice(start, start + PAGE_SIZE);
  recentList.replaceChildren(
    ...(pageItems.length ? pageItems.map(recentRow) : [el("p", { className: "hint" }, "Nada visitado todavía.")]),
  );
  const totalPages = Math.max(1, Math.ceil(mergedRecent.length / PAGE_SIZE));
  recentPager.replaceChildren(
    el(
      "button",
      { className: "btn-ghost", disabled: currentPage <= 1, onClick: () => { currentPage--; renderRecentPage(); } },
      "‹ anterior",
    ),
    el("span", { className: "mono-tag" }, `${currentPage} / ${totalPages}`),
    el(
      "button",
      { className: "btn-ghost", disabled: currentPage >= totalPages, onClick: () => { currentPage++; renderRecentPage(); } },
      "siguiente ›",
    ),
  );
}

function recentRow(item) {
  const when = new Date(item.viewed_at).toLocaleString("es-ES", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
  const href =
    item.kind === "doc"
      ? `#/documentos/${encodeURIComponent(item.path)}`
      : `#/estudiar/${encodeURIComponent(item.itemId)}`;
  return el(
    "div",
    { className: "recent-row" },
    el("a", { href }, icon(item.kind === "doc" ? "file-text" : "book-open", { size: 14 }), item.title),
    el("span", { className: "hint" }, when),
  );
}

async function loadDueReview() {
  try {
    const data = await study.dueReview(20);
    const count = data.count_due;
    if (!count) {
      dueReviewCard.replaceChildren(
        el(
          "div",
          { className: "due-review-card empty" },
          el("p", { className: "hint" }, "Nada pendiente de repasar hoy — vuelve mañana."),
        ),
      );
      return;
    }
    const minutes = Math.max(1, Math.round((Math.min(count, data.questions.length || count) * SECONDS_PER_CARD) / 60));
    dueReviewCard.replaceChildren(
      el(
        "div",
        { className: "due-review-card" },
        el(
          "div",
          { className: "due-review-text" },
          el("h2", { className: "pane-heading" }, "Repasar hoy"),
          el(
            "p",
            { className: "hint" },
            `${count} tarjeta${count === 1 ? "" : "s"} pendiente${count === 1 ? "" : "s"} · ~${minutes} min`,
          ),
        ),
        el("button", { className: "btn-primary", onClick: () => navigate("estudiar/repasar") }, "Empezar"),
      ),
    );
  } catch {
    dueReviewCard.replaceChildren(); // motor no disponible: la sección simplemente no aparece
  }
}

async function loadHomeStudyList() {
  try {
    const docs = await study.listDocuments();
    homeStudyList.replaceChildren(
      ...(docs.length
        ? docs.slice(0, 4).map((d) => documentCard(d, { compact: true }))
        : [el("p", { className: "hint" }, "Sin documentos en profundidad todavía.")]),
    );
  } catch {
    homeStudyList.replaceChildren(el("p", { className: "hint" }, "Motor de estudio no disponible en :8011."));
  }
}

function loadHome() {
  renderGreeting();
  loadStatCards();
  loadDueReview();
  loadRecent();
  loadHomeStudyList();
  refreshRailStreak();
}

export function initHome() {
  document.addEventListener("activate-section", (ev) => {
    if (ev.detail.section === "inicio") loadHome();
  });
  loadHome();
}
