/** Calendario: vista mensual (eventos + todos con fecha) y vista de tareas
 * (todos filtrables por hecho/pendiente y asignatura) — dos caras del mismo
 * almacén (`agenda/events` + `agenda/todos`, ver backend/app/agenda/store.py).
 * Sin librería de calendario: un grid de 7 columnas construido a mano, igual
 * de "sin framework" que el resto del frontend. */

import { uned, ApiError } from "./api.js";
import { el } from "./dom.js";
import { icon } from "./icons.js";
import { setTopbarContext } from "./main.js";
import { showModal, updateModalBody, closeModal, isModalOpen } from "./modal.js";
import { SUBJECTS, subjectByFolder } from "./plan-semestre.js";

const root = document.getElementById("calendar-root");

const TYPE_LABELS = {
  tutoria: "Tutoría",
  entrega: "Entrega",
  examen: "Examen",
  reunion: "Reunión",
  estudio: "Estudio",
  otro: "Otro",
};

// Color por asignatura (franja izquierda de cada chip): misma paleta que el panel de
// Inicio, definida en plan-semestre.js. Se casa por el código que empieza el nombre
// de carpeta (`71031027-fundamentos-...`). Sin coincidencia: gris.
function subjectStyle(subject) {
  const s = subjectByFolder(subject);
  return s ? { name: s.short, color: s.color } : null;
}
const WEEKDAYS = ["L", "M", "X", "J", "V", "S", "D"];
const MONTH_NAMES = [
  "enero", "febrero", "marzo", "abril", "mayo", "junio",
  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
];

let view = "month"; // "month" | "tasks"
let visibleMonth = new Date(); // cualquier día dentro del mes visible
let taskFilter = { done: "", subject: "" };
let subjectsCache = null;
let loaded = false;

function isoDate(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function todayIso() {
  return isoDate(new Date());
}

async function listSubjects() {
  if (subjectsCache) return subjectsCache;
  try {
    const tree = await uned.getTree();
    const asignaturas = tree.children?.find((c) => c.path === "asignaturas");
    subjectsCache = (asignaturas?.children ?? [])
      .filter((c) => c.type === "dir" && c.name !== "_plantilla")
      .map((c) => c.name);
  } catch {
    subjectsCache = [];
  }
  return subjectsCache;
}

function monthGridDates(base) {
  const year = base.getFullYear();
  const month = base.getMonth();
  const first = new Date(year, month, 1);
  const startOffset = (first.getDay() + 6) % 7; // lunes = 0
  const gridStart = new Date(year, month, 1 - startOffset);
  const days = [];
  for (let i = 0; i < 42; i++) {
    const d = new Date(gridStart);
    d.setDate(gridStart.getDate() + i);
    days.push(d);
  }
  return days;
}

function render() {
  root.replaceChildren(
    el(
      "div",
      { className: "calendar-toolbar" },
      el(
        "div",
        { className: "calendar-tabs" },
        el(
          "button",
          { className: "calendar-tab" + (view === "month" ? " active" : ""), onClick: () => switchView("month") },
          "Mes",
        ),
        el(
          "button",
          { className: "calendar-tab" + (view === "tasks" ? " active" : ""), onClick: () => switchView("tasks") },
          "Tareas",
        ),
      ),
      el(
        "div",
        { className: "calendar-toolbar-actions" },
        el(
          "button",
          { className: "btn-primary", onClick: () => openItemForm() },
          icon("plus", { size: 16 }),
          "Añadir",
        ),
      ),
    ),
    el("div", { id: "calendar-body" }, el("p", { className: "hint" }, "Cargando…")),
  );
  if (view === "month") renderMonth(); else renderTasks();
}

function switchView(next) {
  view = next;
  render();
}

// ---- vista mensual ----

async function renderMonth() {
  const body = document.getElementById("calendar-body");
  const days = monthGridDates(visibleMonth);
  const start = isoDate(days[0]);
  const end = isoDate(days[days.length - 1]);
  setTopbarContext(el("span", {}, `${MONTH_NAMES[visibleMonth.getMonth()]} ${visibleMonth.getFullYear()}`));

  let events, todos;
  try {
    [events, todos] = await Promise.all([
      uned.listEvents({ start, end }),
      uned.listTodos(),
    ]);
  } catch {
    body.replaceChildren(el("p", { className: "error-banner" }, "No se pudo cargar el calendario. ¿Está el servidor arrancado?"));
    return;
  }

  const byDay = new Map();
  const add = (dateKey, item) => {
    if (!byDay.has(dateKey)) byDay.set(dateKey, []);
    byDay.get(dateKey).push(item);
  };
  events.forEach((e) => add(e.date, { kind: "event", ...e }));
  todos.filter((t) => t.due_date && t.due_date >= start && t.due_date <= end).forEach((t) => add(t.due_date, { kind: "todo", ...t }));

  const nav = el(
    "div",
    { className: "calendar-month-nav" },
    el("button", { className: "btn-ghost", onClick: () => shiftMonth(-1) }, icon("chevron-left", { size: 16 })),
    el("button", { className: "btn-ghost", onClick: () => { visibleMonth = new Date(); renderMonth(); } }, "Hoy"),
    el("button", { className: "btn-ghost", onClick: () => shiftMonth(1) }, icon("chevron-right", { size: 16 })),
  );

  const grid = el(
    "div",
    { className: "calendar-grid" },
    ...WEEKDAYS.map((w) => el("div", { className: "calendar-weekday" }, w)),
    ...days.map((d) => renderDayCell(d, byDay.get(isoDate(d)) ?? [])),
  );

  body.replaceChildren(nav, grid, renderLegend());
}

function renderDayCell(date, items) {
  const iso = isoDate(date);
  const otherMonth = date.getMonth() !== visibleMonth.getMonth();
  const cell = el(
    "div",
    { className: "calendar-day" + (otherMonth ? " other-month" : "") + (iso === todayIso() ? " today" : "") },
    el("div", { className: "calendar-day-num" }, String(date.getDate())),
  );
  const shown = items.slice(0, 3);
  shown.forEach((item) => cell.append(renderChip(item)));
  if (items.length > shown.length) {
    cell.append(el("div", { className: "calendar-day-more" }, `+${items.length - shown.length} más`));
  }
  cell.addEventListener("click", () => openDayDetail(date, items));
  return cell;
}

function renderChip(item) {
  const chip =
    item.kind === "event"
      ? el(
          "div",
          { className: `calendar-chip calendar-chip-${item.type || "otro"}` },
          item.time ? el("span", { className: "calendar-chip-time" }, item.time) : null,
          item.title,
        )
      : el("div", { className: "calendar-chip calendar-chip-todo" + (item.done ? " done" : "") }, item.title);
  chip.title = [item.time, item.title, subjectStyle(item.subject)?.name].filter(Boolean).join(" · ");
  const style = subjectStyle(item.subject);
  if (style) chip.style.setProperty("--chip-subject", style.color);
  return chip;
}

function renderLegend() {
  return el(
    "div",
    { className: "calendar-legend" },
    ...SUBJECTS.map((s) => {
      const item = el("span", { className: "calendar-legend-item" }, el("span", { className: "calendar-legend-dot" }), s.short);
      item.style.setProperty("--chip-subject", s.color);
      return item;
    }),
  );
}

function shiftMonth(delta) {
  visibleMonth = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() + delta, 1);
  renderMonth();
}

function openDayDetail(date, items) {
  renderDayModal(date, items);
}

function renderDayModal(date, items) {
  const iso = isoDate(date);
  const label = date.toLocaleDateString("es-ES", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
  const titleText = label.charAt(0).toUpperCase() + label.slice(1);

  const list = items.length
    ? el(
        "div",
        { className: "day-detail-list" },
        ...items.map((item) => renderDayDetailItem(item, () => refreshDayModal(date))),
      )
    : el("p", { className: "hint" }, "Nada para este día.");

  if (isModalOpen()) {
    updateModalBody(list);
  } else {
    showModal(titleText, list, [
      el(
        "button",
        { className: "btn-primary", onClick: () => { closeModal(); openItemForm(iso); } },
        icon("plus", { size: 15 }),
        "Añadir a este día",
      ),
    ]);
  }
}

async function refreshDayModal(date) {
  const iso = isoDate(date);
  const [events, todos] = await Promise.all([uned.listEvents({ start: iso, end: iso }), uned.listTodos()]);
  const items = [
    ...events.map((e) => ({ kind: "event", ...e })),
    ...todos.filter((t) => t.due_date === iso).map((t) => ({ kind: "todo", ...t })),
  ];
  renderDayModal(date, items);
  renderMonth();
}

function renderDayDetailItem(item, onChanged) {
  if (item.kind === "event") {
    return el(
      "div",
      { className: "day-detail-item" },
      el(
        "div",
        { className: "day-detail-item-head" },
        el("span", { className: `tag tag-${typeTagClass(item.type)}` }, TYPE_LABELS[item.type] || item.type),
        item.time ? el("span", { className: "hint" }, item.time) : null,
        el("strong", {}, item.title),
      ),
      item.subject ? el("div", { className: "hint" }, subjectStyle(item.subject)?.name ?? item.subject) : null,
      item.location ? el("div", { className: "hint" }, `📍 ${item.location}`) : null,
      item.description ? el("p", {}, item.description) : null,
      renderLinks(item.links),
      el(
        "button",
        { className: "btn-danger", onClick: async () => { await uned.deleteEvent(item.id); onChanged(); } },
        icon("trash-2", { size: 14 }),
        "Borrar",
      ),
    );
  }
  return el(
    "div",
    { className: "day-detail-item" },
    el(
      "label",
      { className: "day-detail-item-head" },
      el("input", {
        type: "checkbox",
        checked: !!item.done,
        onInput: async (ev) => { await uned.updateTodo(item.id, { done: ev.target.checked }); onChanged(); },
      }),
      el("strong", { className: item.done ? "done-text" : "" }, item.title),
    ),
    item.subject ? el("div", { className: "hint" }, item.subject) : null,
    item.description ? el("p", {}, item.description) : null,
    renderLinks(item.links),
    el(
      "button",
      { className: "btn-danger", onClick: async () => { await uned.deleteTodo(item.id); onChanged(); } },
      icon("trash-2", { size: 14 }),
      "Borrar",
    ),
  );
}

// Etiqueta legible según a dónde apunta el enlace; el resto sigue como «Enlace N».
function linkLabel(link, i, total) {
  if (/google\.[^/]+\/maps/.test(link)) return "Cómo llegar (Google Maps)";
  if (/intecca\.uned\.es/.test(link)) return "Sala en línea (AVIP)";
  if (/agora\.uned\.es/.test(link)) return "Agora";
  return `Enlace ${total > 1 ? i + 1 : ""}`.trim();
}

function renderLinks(links) {
  if (!links?.length) return null;
  return el(
    "div",
    { className: "item-links" },
    ...links.map((link, i) => el("a", { href: link, target: "_blank", rel: "noopener" }, `${linkLabel(link, i, links.length)} ↗`)),
  );
}

function typeTagClass(type) {
  if (type === "examen" || type === "entrega") return "outline";
  if (type === "reunion" || type === "tutoria") return "accent-2";
  if (type === "estudio") return "accent";
  return "neutral";
}

// ---- vista de tareas ----

async function renderTasks() {
  const body = document.getElementById("calendar-body");
  setTopbarContext();

  let todos;
  try {
    todos = await uned.listTodos({ done: taskFilter.done, subject: taskFilter.subject });
  } catch {
    body.replaceChildren(el("p", { className: "error-banner" }, "No se pudo cargar la lista de tareas."));
    return;
  }

  const subjects = await listSubjects();

  const filters = el(
    "div",
    { className: "feed-controls" },
    el(
      "select",
      { onInput: (ev) => { taskFilter.done = ev.target.value; renderTasks(); } },
      el("option", { value: "", selected: taskFilter.done === "" }, "Todas"),
      el("option", { value: "false", selected: taskFilter.done === "false" }, "Pendientes"),
      el("option", { value: "true", selected: taskFilter.done === "true" }, "Hechas"),
    ),
    el(
      "select",
      { onInput: (ev) => { taskFilter.subject = ev.target.value; renderTasks(); } },
      el("option", { value: "" }, "Todas las asignaturas"),
      ...subjects.map((s) => el("option", { value: s, selected: taskFilter.subject === s }, s)),
    ),
  );

  todos.sort((a, b) => (a.due_date || "9999").localeCompare(b.due_date || "9999"));

  const list = todos.length
    ? el("div", { className: "task-list" }, ...todos.map((t) => renderTaskRow(t)))
    : el("p", { className: "hint" }, "No hay tareas con este filtro.");

  body.replaceChildren(filters, list);
}

function renderTaskRow(todo) {
  return el(
    "div",
    { className: "task-row panel" + (todo.done ? " done" : "") },
    el("input", {
      type: "checkbox",
      className: "task-checkbox",
      checked: !!todo.done,
      onInput: async (ev) => { await uned.updateTodo(todo.id, { done: ev.target.checked }); renderTasks(); },
    }),
    el(
      "div",
      { className: "task-row-main" },
      el("div", { className: "task-row-title" }, todo.title),
      todo.description ? el("div", { className: "hint" }, todo.description) : null,
      el(
        "div",
        { className: "task-row-meta" },
        todo.due_date ? el("span", { className: "mono-tag" }, todo.due_date) : null,
        todo.subject ? el("span", { className: "mono-tag" }, todo.subject) : null,
        renderLinks(todo.links),
      ),
    ),
    el(
      "button",
      { className: "btn-ghost", title: "Borrar", onClick: async () => { await uned.deleteTodo(todo.id); renderTasks(); } },
      icon("trash-2", { size: 14 }),
    ),
  );
}

// ---- alta de evento/todo ----

function openItemForm(presetDate) {
  let kind = "event";

  const titleInput = el("input", { type: "text", placeholder: "Título", required: true });
  const dateInput = el("input", { type: "date", value: presetDate || todayIso() });
  const timeInput = el("input", { type: "time" });
  const typeSelect = el(
    "select",
    {},
    ...Object.entries(TYPE_LABELS).map(([value, label]) => el("option", { value }, label)),
  );
  const subjectInput = el("input", { type: "text", placeholder: "Asignatura (opcional)" });
  subjectInput.setAttribute("list", "calendar-subjects");
  const linksInput = el("textarea", { rows: 2, placeholder: "https://…\nhttps://… (uno por línea)" });
  const descInput = el("textarea", { rows: 3, placeholder: "Descripción" });
  const dueOptional = el("span", { className: "hint" }, "(opcional — sin fecha solo aparece en Tareas)");

  const fieldsBox = el("div", { className: "calendar-form-fields" });

  function renderFields() {
    fieldsBox.replaceChildren(
      el("label", {}, "Título", titleInput),
      kind === "event"
        ? el(
            "div",
            { className: "calendar-form-row" },
            el("label", {}, "Fecha", dateInput),
            el("label", {}, "Hora (opcional)", timeInput),
            el("label", {}, "Tipo", typeSelect),
          )
        : el("label", {}, "Fecha límite ", dueOptional, dateInput),
      el("label", {}, "Asignatura", subjectInput),
      el("label", {}, "Enlaces (opcional, uno por línea)", linksInput),
      el("label", {}, "Descripción", descInput),
    );
  }
  renderFields();

  const kindToggle = el(
    "div",
    { className: "calendar-type-toggle" },
    el("button", { type: "button", className: "calendar-tab active", onClick: (ev) => setKind("event", ev) }, "Evento"),
    el("button", { type: "button", className: "calendar-tab", onClick: (ev) => setKind("todo", ev) }, "Tarea"),
  );

  function setKind(next, ev) {
    kind = next;
    kindToggle.querySelectorAll(".calendar-tab").forEach((b) => b.classList.remove("active"));
    ev.target.closest("button").classList.add("active");
    renderFields();
  }

  const form = el(
    "form",
    {
      onSubmit: async (ev) => {
        ev.preventDefault();
        const title = titleInput.value.trim();
        if (!title) return;
        const links = linksInput.value.split("\n").map((l) => l.trim()).filter(Boolean);
        try {
          if (kind === "event") {
            await uned.createEvent({
              title,
              date: dateInput.value || todayIso(),
              time: timeInput.value || null,
              type: typeSelect.value,
              subject: subjectInput.value.trim() || null,
              links,
              description: descInput.value,
            });
          } else {
            await uned.createTodo({
              title,
              due_date: dateInput.value || null,
              subject: subjectInput.value.trim() || null,
              links,
              description: descInput.value,
            });
          }
          closeModal();
          if (view === "month") renderMonth(); else renderTasks();
        } catch (error) {
          alertBox.textContent = error instanceof ApiError ? error.message : "No se pudo guardar.";
        }
      },
    },
    kindToggle,
    fieldsBox,
    el("datalist", { id: "calendar-subjects" }),
    el("div", { className: "error-banner" }),
    el("button", { type: "submit", className: "btn-primary" }, "Guardar"),
  );

  const alertBox = form.querySelector(".error-banner");
  listSubjects().then((subjects) => {
    const datalist = form.querySelector("#calendar-subjects");
    datalist.replaceChildren(...subjects.map((s) => el("option", { value: s })));
  });

  showModal("Añadir al calendario", form, []);
}

export function initCalendar() {
  document.addEventListener("activate-section", (ev) => {
    if (ev.detail.section !== "calendario") return;
    if (!loaded) {
      loaded = true;
      render();
    } else if (view === "month") {
      renderMonth();
    } else {
      renderTasks();
    }
  });
}
