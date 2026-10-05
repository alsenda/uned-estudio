/** Entry point: the router (src/router.js) owns navigation — clicking a rail
 * item or any in-page link just changes location.hash, and this file reacts
 * by toggling the active pane/rail-item and re-emitting an `activate-section`
 * CustomEvent (detail: { section, rest }) that each section's own module
 * listens for, so section modules never need to import each other. */

import { onRoute, navigate, startRouter } from "./router.js";
import { initFeed } from "./feed.js";
import { initRag } from "./rag.js";
import { initLibrary } from "./library.js";
import { initStudy } from "./study.js";
import { initHome } from "./home.js";
import { initDashboard } from "./dashboard.js";
import { initCalendar } from "./calendar.js";
import { initGlossary } from "./glossary.js";
import { initContacts } from "./contacts.js";
import { el } from "./dom.js";
import { icon } from "./icons.js";
import { study } from "./api.js";

const SECTION_TITLES = {
  inicio: "Inicio",
  documentos: "Documentos",
  buscar: "Buscar en apuntes",
  estudiar: "Estudiar a fondo",
  calendario: "Calendario",
  glosario: "Glosario",
  contactos: "Contactos",
};

const railItems = document.querySelectorAll(".rail-item");
const panes = document.querySelectorAll(".pane");
const sectionTitle = document.getElementById("section-title");
const topbarContext = document.getElementById("topbar-context");
const railStreak = document.getElementById("rail-streak");

export function setTopbarContext(...nodes) {
  topbarContext.replaceChildren(...nodes);
}

railItems.forEach((btn) => {
  btn.querySelector(".rail-item-icon")?.append(icon(btn.dataset.icon, { size: 19 }));
  btn.addEventListener("click", () => navigate(btn.dataset.section));
});

// La racha vive en el rail (visible en toda la app, no solo en Inicio) — un
// contador tranquilo, nunca un aviso de "vas a perderla" (ver
// estudio-profundo/backend/app/routers/engagement.py).
export async function refreshRailStreak() {
  try {
    const summary = await study.engagementSummary();
    railStreak.replaceChildren(
      icon("flame", { size: 20 }),
      el(
        "div",
        {},
        el("div", { className: "rail-streak-days" }, `${summary.streak_days} día${summary.streak_days === 1 ? "" : "s"}`),
        el("div", { className: "rail-streak-label" }, "de racha de estudio"),
      ),
    );
  } catch {
    railStreak.replaceChildren();
  }
}

onRoute(({ section, rest }) => {
  const known = SECTION_TITLES[section] ? section : "inicio";
  railItems.forEach((btn) => btn.classList.toggle("active", btn.dataset.section === known));
  panes.forEach((pane) => pane.classList.toggle("active", pane.id === `view-${known}`));
  sectionTitle.textContent = SECTION_TITLES[known];
  setTopbarContext();
  document.dispatchEvent(new CustomEvent("activate-section", { detail: { section: known, rest } }));
});

initFeed();
initRag();
initLibrary();
initStudy();
initHome();
initDashboard();
initCalendar();
initGlossary();
initContacts();
refreshRailStreak();
startRouter();
