/** Diario: entradas de aprendizaje + noticias, en feed/entries/. */

import { uned } from "./api.js";
import { el, escapeHtml } from "./dom.js";

const feedList = document.getElementById("feed-list");
const feedStatus = document.getElementById("feed-status");
const filterType = document.getElementById("filter-type");
const refreshNewsBtn = document.getElementById("refresh-news-btn");

export async function loadFeed() {
  feedStatus.textContent = "Cargando…";
  try {
    const entries = await uned.getFeed(filterType.value || undefined);
    feedStatus.textContent = `${entries.length} entrada${entries.length === 1 ? "" : "s"}`;
    feedList.replaceChildren(
      ...(entries.length
        ? entries.map(entryCard)
        : [el("p", { className: "hint" }, "No hay entradas todavía.")]),
    );
  } catch {
    feedStatus.textContent = "Error al cargar el feed. ¿Está el servidor arrancado?";
  }
}

function entryCard(e) {
  return el(
    "article",
    { className: "entry" },
    el("h3", {}, e.title),
    el(
      "div",
      { className: "meta" },
      el("span", { className: `badge badge-${e.type}` }, e.type),
      el("span", {}, e.date),
      e.subject ? el("span", {}, e.subject) : null,
    ),
    el("div", { className: "entry-content", html: escapeHtml(e.content).replace(/\n/g, "<br>") }),
  );
}

export function initFeed() {
  filterType.addEventListener("change", loadFeed);
  refreshNewsBtn.addEventListener("click", async () => {
    feedStatus.textContent = "Refrescando noticias…";
    try {
      const result = await uned.refreshNews();
      feedStatus.textContent = `Añadidas ${result.added} noticias de ${result.sources_checked} fuentes`;
    } catch {
      feedStatus.textContent = "Error al refrescar noticias.";
    } finally {
      loadFeed();
    }
  });
  loadFeed();
}
