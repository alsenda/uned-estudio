/** Inicio: panel del semestre.
 *
 *  - Cabecera: reloj, semana seleccionada, mini calendario, «compañero de estudio»
 *    (resumen local de hoy, sin LLM) y avisos importantes (entregas/exámenes próximos).
 *  - Barra: cuatrimestre, navegación por semanas y accesos (Campus, Ágora, Akademos…).
 *  - Una tarjeta por asignatura: tutoría de la semana, tema de la semana, progreso y
 *    próxima actividad. Todo sale de `agenda/events` + `agenda/todos` (API de agenda) y de
 *    los datos fijos de plan-semestre.js. Lo oficial se distingue de lo orientativo. */

import { uned } from "./api.js";
import { el } from "./dom.js";
import { navigate } from "./router.js";
import { SEMESTER_START, SEMESTER_WEEKS, SUBJECTS, subjectByFolder } from "./plan-semestre.js";

const root = document.getElementById("dash-root");

const MONTHS_SHORT = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const MONTHS_LONG = [
  "enero", "febrero", "marzo", "abril", "mayo", "junio",
  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
];
const WEEKDAYS = ["L", "M", "X", "J", "V", "S", "D"];
const QUICK_LINKS = [
  { label: "Campus UNED", emoji: "🎓", href: "https://www.uned.es/" },
  { label: "Ágora", emoji: "📘", href: "https://agora.uned.es/my/" },
  { label: "Akademos", emoji: "🔗", href: "https://akademosweb.uned.es/Default.aspx" },
  { label: "INTECCA", emoji: "📚", href: "https://www.intecca.uned.es/portal/inicio" },
];

const state = { week: 1, month: new Date(), events: [], todos: [], loaded: false };
let clockEl = null;
let dateEl = null;

// ---- fechas ----

const pad = (n) => String(n).padStart(2, "0");
const iso = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const parseIso = (s) => new Date(`${s}T00:00:00`);
const addDays = (d, n) => {
  const x = new Date(d);
  x.setDate(x.getDate() + n);
  return x;
};
const weekStart = (n) => addDays(parseIso(SEMESTER_START), 7 * (n - 1));
const capitalize = (s) => s.charAt(0).toUpperCase() + s.slice(1);

function weekOf(date) {
  const diff = Math.round((new Date(date.getFullYear(), date.getMonth(), date.getDate()) - parseIso(SEMESTER_START)) / 864e5);
  return Math.min(SEMESTER_WEEKS, Math.max(1, Math.floor(diff / 7) + 1));
}

function formatRange(a, b) {
  const sameMonth = a.getMonth() === b.getMonth();
  return sameMonth
    ? `${a.getDate()}–${b.getDate()} ${MONTHS_SHORT[b.getMonth()]}. ${b.getFullYear()}`
    : `${a.getDate()} ${MONTHS_SHORT[a.getMonth()]}. – ${b.getDate()} ${MONTHS_SHORT[b.getMonth()]}. ${b.getFullYear()}`;
}

function esDate(isoString) {
  const [y, m, d] = isoString.split("-");
  return `${d}/${m}/${y}`;
}

function timeStr(t) {
  if (t === undefined || t === null || t === "") return "";
  if (typeof t === "number") return `${pad(Math.floor(t / 60) % 24)}:${pad(t % 60)}`; // YAML lo leyó como minutos
  return String(t);
}

const isApprox = (title) => /aprox|pendiente|sin publicar/i.test(title || "");

function relativeDays(dateIso, todayIso) {
  const n = Math.round((parseIso(dateIso) - parseIso(todayIso)) / 864e5);
  if (n === 0) return "hoy";
  if (n === 1) return "mañana";
  return `en ${n} días`;
}

// ---- datos ----

async function load() {
  try {
    const [events, todos] = await Promise.all([
      uned.listEvents({ start: "2026-09-01", end: "2027-09-30" }),
      uned.listTodos(),
    ]);
    state.events = events;
    state.todos = todos;
    state.loaded = true;
  } catch {
    state.loaded = false;
  }
  state.week = weekOf(new Date());
  state.month = weekStart(state.week);
  render();
}

function subjectEvents(subject) {
  return state.events.filter((e) => subjectByFolder(e.subject)?.key === subject.key);
}

function upcomingDeadlines(todayIso) {
  const items = [];
  const seenTitles = new Set();
  for (const e of state.events) {
    if (!["entrega", "examen"].includes(e.type) || e.date < todayIso) continue;
    if (seenTitles.has(e.title)) continue; // una semana de exámenes = un solo aviso
    seenTitles.add(e.title);
    items.push({ date: e.date, time: timeStr(e.time), title: e.title });
  }
  for (const t of state.todos) {
    if (t.done || !t.due_date || t.due_date < todayIso) continue;
    items.push({ date: t.due_date, time: "", title: t.title });
  }
  return items.sort((a, b) => (a.date + a.time).localeCompare(b.date + b.time)).slice(0, 3);
}

// ---- cabecera ----

function tickClock() {
  const now = new Date();
  if (clockEl) clockEl.textContent = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
  if (dateEl) {
    const long = now.toLocaleDateString("es-ES", { weekday: "long", day: "2-digit", month: "long", year: "numeric" });
    dateEl.textContent = capitalize(long.replace(/ de /g, " de "));
  }
}

function renderMiniCalendar() {
  const y = state.month.getFullYear();
  const m = state.month.getMonth();
  const first = new Date(y, m, 1);
  const gridStart = addDays(first, -((first.getDay() + 6) % 7));
  const withEvents = new Set([...state.events.map((e) => e.date), ...state.todos.filter((t) => t.due_date && !t.done).map((t) => t.due_date)]);
  const ws = iso(weekStart(state.week));
  const we = iso(addDays(weekStart(state.week), 6));
  const todayIso = iso(new Date());

  const cells = [];
  for (let i = 0; i < 42; i++) {
    const d = addDays(gridStart, i);
    const key = iso(d);
    const classes = ["dash-mini-day"];
    if (d.getMonth() !== m) classes.push("other");
    if (withEvents.has(key)) classes.push("has-event");
    if (key >= ws && key <= we) classes.push("in-week");
    if (key === todayIso) classes.push("today");
    cells.push(
      el(
        "button",
        {
          className: classes.join(" "),
          type: "button",
          title: key === todayIso ? "Hoy" : esDate(key),
          onClick: () => {
            const w = weekOf(d);
            if (key >= SEMESTER_START) setWeek(w);
          },
        },
        String(d.getDate()),
      ),
    );
  }

  return el(
    "div",
    { className: "dash-mini" },
    el(
      "div",
      { className: "dash-mini-head" },
      el("button", { className: "dash-mini-nav", type: "button", "aria-label": "Mes anterior", onClick: () => shiftMonth(-1) }, "‹"),
      el("strong", {}, `${MONTHS_LONG[m]} ${y}`),
      el("button", { className: "dash-mini-nav", type: "button", "aria-label": "Mes siguiente", onClick: () => shiftMonth(1) }, "›"),
    ),
    el("div", { className: "dash-mini-grid" }, ...WEEKDAYS.map((w) => el("span", { className: "dash-mini-wd" }, w)), ...cells),
  );
}

function companionLines(todayIso) {
  const lines = [];
  const timed = (day) =>
    state.events
      .filter((e) => e.date === day && timeStr(e.time))
      .sort((a, b) => timeStr(a.time).localeCompare(timeStr(b.time)))
      .map((e) => `${timeStr(e.time)} ${e.title}`);

  const hoy = timed(todayIso);
  lines.push(hoy.length ? `Hoy: ${hoy.join(" · ")}.` : "Hoy no tienes tutorías ni sesiones con hora.");

  for (let i = 1; i <= 14; i++) {
    const day = iso(addDays(parseIso(todayIso), i));
    const list = timed(day);
    if (list.length) {
      const d = parseIso(day);
      lines.push(`${i === 1 ? "Mañana" : capitalize(d.toLocaleDateString("es-ES", { weekday: "long", day: "numeric", month: "long" }))}: ${list.join(" · ")}.`);
      break;
    }
  }

  const topic = SUBJECTS.map((s) => ({ s, t: topicFor(s, state.week) }))
    .filter((x) => x.t?.official)
    .map((x) => `${x.s.short}: ${x.t.title.split(" (")[0]}`)[0];
  if (topic) lines.push(`Esta semana toca ${topic}.`);
  return lines;
}

function renderCompanion() {
  const todayIso = iso(new Date());
  return el(
    "section",
    { className: "dash-panel dash-companion" },
    el("header", {}, el("strong", {}, "🧑‍🏫 COMPAÑERO DE ESTUDIO"), el("span", { className: "dash-panel-tag" }, "RESUMEN · LOCAL")),
    el("div", { className: "dash-companion-body" }, ...companionLines(todayIso).map((l) => el("p", {}, l))),
    el("button", { className: "dash-panel-btn", type: "button", onClick: () => navigate("buscar") }, "Preguntar a mis apuntes ›"),
  );
}

function renderNotices() {
  const todayIso = iso(new Date());
  const items = upcomingDeadlines(todayIso);
  return el(
    "section",
    { className: "dash-panel dash-notices" },
    el("header", {}, el("strong", {}, "🔔 AVISOS IMPORTANTES")),
    ...(items.length
      ? items.map((it) =>
          el(
            "div",
            { className: "dash-notice" },
            el("strong", {}, `${relativeDays(it.date, todayIso)} · `),
            it.title,
            el("div", { className: "dash-notice-date" }, `${esDate(it.date)}${it.time ? ` · ${it.time}` : ""}${isApprox(it.title) ? " · fecha orientativa" : ""}`),
          ),
        )
      : [el("p", { className: "dash-empty" }, "Sin entregas ni exámenes próximos.")]),
  );
}

function renderHero() {
  const ws = weekStart(state.week);
  clockEl = el("div", { className: "dash-clock" });
  dateEl = el("div", { className: "dash-date" });
  const hero = el(
    "header",
    { className: "dash-hero" },
    el(
      "div",
      { className: "dash-hero-id" },
      el("div", { className: "dash-eyebrow" }, "INGENIERÍA EN INTELIGENCIA ARTIFICIAL · UNED"),
      dateEl,
      clockEl,
    ),
    el(
      "div",
      { className: "dash-hero-week" },
      el("div", { className: "dash-eyebrow" }, "SEMANA SELECCIONADA"),
      el("div", { className: "dash-week-big" }, `Semana ${state.week} de ${SEMESTER_WEEKS}`),
      el("div", { className: "dash-week-range" }, formatRange(ws, addDays(ws, 6))),
    ),
    renderMiniCalendar(),
    renderCompanion(),
    renderNotices(),
  );
  tickClock();
  return hero;
}

// ---- barra de semana ----

function setWeek(n) {
  state.week = Math.min(SEMESTER_WEEKS, Math.max(1, n));
  state.month = weekStart(state.week);
  render();
}

function shiftMonth(delta) {
  state.month = new Date(state.month.getFullYear(), state.month.getMonth() + delta, 1);
  render();
}

function renderToolbar() {
  const weekOptions = [];
  for (let n = 1; n <= SEMESTER_WEEKS; n++) {
    const ws = weekStart(n);
    weekOptions.push(el("option", { value: String(n), selected: n === state.week }, `Semana ${n} · ${formatRange(ws, addDays(ws, 6))}`));
  }
  return el(
    "div",
    { className: "dash-toolbar" },
    el(
      "label",
      { className: "dash-select-wrap" },
      el("span", { className: "dash-select-icon" }, "🗓️"),
      el(
        "select",
        { "aria-label": "Cuatrimestre" },
        el("option", { value: "1", selected: true }, "Primer cuatrimestre"),
        el("option", { value: "2", disabled: true }, "Segundo cuatrimestre (sin planificar)"),
      ),
    ),
    el(
      "div",
      { className: "dash-weeknav" },
      el("button", { type: "button", className: "dash-icon-btn", "aria-label": "Semana anterior", disabled: state.week <= 1, onClick: () => setWeek(state.week - 1) }, "‹"),
      el("select", { "aria-label": "Semana", onInput: (ev) => setWeek(Number(ev.target.value)) }, ...weekOptions),
      el("button", { type: "button", className: "dash-icon-btn", "aria-label": "Semana siguiente", disabled: state.week >= SEMESTER_WEEKS, onClick: () => setWeek(state.week + 1) }, "›"),
      el("button", { type: "button", className: "dash-link-btn", onClick: () => setWeek(weekOf(new Date())) }, "Hoy"),
    ),
    el(
      "nav",
      { className: "dash-links", "aria-label": "Accesos" },
      ...QUICK_LINKS.map((l) => el("a", { href: l.href, target: "_blank", rel: "noopener", className: "dash-link-btn" }, `${l.emoji} ${l.label}`)),
      el("button", { type: "button", className: "dash-link-btn", onClick: openExams }, "📝 Exámenes"),
    ),
  );
}

// ---- tarjetas ----

function topicFor(subject, week) {
  const mondayIso = iso(weekStart(week));
  return subject.topics.find((t) => mondayIso >= t.from && mondayIso <= t.to) ?? null;
}

function nextActivity(subject, fromIso) {
  return subjectEvents(subject)
    .filter((e) => ["entrega", "examen", "otro"].includes(e.type) && e.date >= fromIso)
    .sort((a, b) => (a.date + timeStr(a.time)).localeCompare(b.date + timeStr(b.time)))[0];
}

const ACTIVITY_LABEL = { entrega: "Próxima entrega", examen: "Próximo examen", otro: "Próximo aviso" };

function renderSubjectCard(subject) {
  const ws = weekStart(state.week);
  const wsIso = iso(ws);
  const weIso = iso(addDays(ws, 6));
  const card = el("article", { className: "dash-card" + (subject.pending ? " pending" : "") });
  card.style.setProperty("--subject", subject.color);

  const tut = subjectEvents(subject).find((e) => e.type === "tutoria" && e.title.startsWith("Tutoría") && e.date >= wsIso && e.date <= weIso);
  let dateBlock;
  let when;
  if (tut) {
    const d = parseIso(tut.date);
    dateBlock = el(
      "div",
      { className: "dash-date-block" },
      el("div", { className: "dash-date-month" }, MONTHS_SHORT[d.getMonth()].slice(0, 3)),
      el("div", { className: "dash-date-day" }, String(d.getDate())),
      el("div", { className: "dash-date-time" }, timeStr(tut.time)),
    );
    const aula = String(tut.location || "").split("—")[1]?.trim() || "";
    when = [aula, "UNED Cádiz", "presencial + AVIP"].filter(Boolean).join(" · ");
  } else {
    dateBlock = el("div", { className: "dash-date-block empty" }, el("div", { className: "dash-date-month" }, "—"), el("div", { className: "dash-date-day" }, "·"));
    when = subject.pending ? "Sin tutorías" : "Sin tutoría esta semana";
  }

  const head = el(
    "div",
    { className: "dash-card-head" },
    dateBlock,
    el(
      "div",
      { className: "dash-card-title" },
      el("h3", {}, subject.name),
      el("div", { className: "dash-card-meta" }, `${subject.code} · ${subject.ects} ECTS`),
      el("div", { className: "dash-card-meta" }, when),
    ),
  );

  const pct = Math.round((state.week / SEMESTER_WEEKS) * 100);
  const progress = el(
    "div",
    {},
    el("div", { className: "dash-progress" }, el("span", { style: `width:${pct}%` })),
    el("div", { className: "dash-week-label" }, el("span", {}, "ESTA SEMANA"), el("span", {}, `${state.week}/${SEMESTER_WEEKS}`)),
  );

  let topicBox;
  if (subject.pending) {
    topicBox = el("div", { className: "dash-topic muted" }, subject.pending);
  } else {
    const t = topicFor(subject, state.week);
    topicBox = el(
      "div",
      { className: "dash-topic" },
      el("div", {}, t ? t.title : subject.defaultTopic),
      t ? el("span", { className: "dash-source " + (t.official ? "official" : "plan") }, t.official ? "oficial" : "orientativo") : null,
    );
  }

  const parts = [head, progress, topicBox];

  if (!subject.pending) {
    const next = nextActivity(subject, wsIso);
    const notice = [];
    if (subject.note) notice.push(el("p", {}, el("strong", {}, "PEC: "), subject.note.replace(/^PEC:\s*/, "")));
    if (next) {
      notice.push(
        el(
          "p",
          {},
          el("strong", {}, `${ACTIVITY_LABEL[next.type]}: `),
          `${next.title.replace(/^[^:]+:\s*/, "")} · ${esDate(next.date)}${timeStr(next.time) ? ` ${timeStr(next.time)}` : ""}`,
          isApprox(next.title) ? el("em", {}, " (fecha orientativa)") : null,
        ),
      );
    }
    if (notice.length) parts.push(el("div", { className: "dash-amber" }, ...notice));
  }

  card.append(...parts);
  return card;
}

// ---- exámenes ----

let examsDetails = null;

function openExams() {
  if (!examsDetails) return;
  examsDetails.open = true;
  examsDetails.scrollIntoView({ behavior: "smooth", block: "center" });
}

function renderExams() {
  const groups = new Map();
  for (const e of state.events) {
    if (e.type !== "examen" || e.date > "2027-03-01") continue;
    const g = groups.get(e.title) ?? { title: e.title, from: e.date, to: e.date };
    g.from = e.date < g.from ? e.date : g.from;
    g.to = e.date > g.to ? e.date : g.to;
    groups.set(e.title, g);
  }
  const extra = state.events.find((e) => e.type === "examen" && /extraordinaria/i.test(e.title));
  const rows = [...groups.values()]
    .sort((a, b) => a.from.localeCompare(b.from))
    .map((g) => el("li", {}, el("strong", {}, g.title.replace("Primeras pruebas presenciales — ", "").replace(/^\w/, (c) => c.toUpperCase()) + ": "), formatRange(parseIso(g.from), parseIso(g.to))));
  if (extra) rows.push(el("li", {}, el("strong", {}, "Extraordinaria: "), `${esDate(extra.date)} (septiembre)`));

  examsDetails = el(
    "details",
    { className: "dash-exams", id: "dash-exams" },
    el("summary", {}, el("span", {}, "🎓 Exámenes · pruebas presenciales"), el("span", { className: "dash-exams-sum" }, "1.ª y 2.ª semana"), el("span", { className: "dash-plus" }, "+")),
    el(
      "div",
      { className: "dash-exams-body" },
      el("ul", {}, ...rows),
      el(
        "p",
        { className: "dash-empty" },
        "El día y la hora de cada asignatura aún no están publicados: se consultan en ",
        el("a", { href: "https://akademosweb.uned.es/Default.aspx", target: "_blank", rel: "noopener" }, "Akademos"),
        " › «Fechas y enunciados de exámenes».",
      ),
    ),
  );
  return examsDetails;
}

// ---- render ----

function render() {
  if (!state.loaded) {
    root.replaceChildren(
      renderHero(),
      el("div", { className: "dash-body" }, el("p", { className: "error-banner" }, "No se pudo cargar la agenda. ¿Está el servidor arrancado?")),
    );
    return;
  }
  root.replaceChildren(
    renderHero(),
    el(
      "div",
      { className: "dash-body" },
      el("div", { className: "dash-board" }, renderToolbar(), el("div", { className: "dash-cards" }, ...SUBJECTS.map(renderSubjectCard))),
      renderExams(),
      el(
        "p",
        { className: "dash-foot" },
        "Panel local e interactivo · Curso 2026/27 · 1.º curso · 1.º cuatrimestre. Las fechas oficiales (Ágora, Akademos, guía docente) se distinguen de las orientativas, que se marcan como «orientativo», «aprox.» o «pendiente»; no se convierten en fechas oficiales.",
      ),
    ),
  );
}

export function initDashboard() {
  document.addEventListener("activate-section", (ev) => {
    if (ev.detail.section === "inicio") load();
  });
  setInterval(tickClock, 1000);
  load();
}
