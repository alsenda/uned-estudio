/** Contactos: profesores, tutores, secretaría... con notas y un historial de
 * interacciones por persona — respaldado por `contacts/people/*.md` +
 * `contacts/interactions/*.md` (ver backend/app/contacts/store.py), mismo
 * patrón de fichero-por-registro que agenda/glosario. */

import { uned, ApiError } from "./api.js";
import { el } from "./dom.js";
import { icon } from "./icons.js";
import { showModal, updateModalBody, closeModal } from "./modal.js";

const root = document.getElementById("contacts-root");

const ROLE_SUGGESTIONS = ["profesor", "tutor", "secretaría", "alumno", "otro"];

let filter = { role: "", subject: "", q: "" };
let subjectsCache = null;
let loaded = false;

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

async function render() {
  root.replaceChildren(el("p", { className: "hint" }, "Cargando…"));

  let people, subjects;
  try {
    [people, subjects] = await Promise.all([
      uned.listPeople({ role: filter.role, subject: filter.subject, q: filter.q }),
      listSubjects(),
    ]);
  } catch {
    root.replaceChildren(el("p", { className: "error-banner" }, "No se pudo cargar Contactos. ¿Está el servidor arrancado?"));
    return;
  }

  const toolbar = el(
    "div",
    { className: "calendar-toolbar" },
    el("h2", { className: "pane-heading" }, "Contactos"),
    el(
      "button",
      { className: "btn-primary", onClick: () => openPersonForm() },
      icon("plus", { size: 16 }),
      "Añadir persona",
    ),
  );

  const roles = [...new Set(people.map((p) => p.role).filter(Boolean))];

  const filters = el(
    "div",
    { className: "feed-controls" },
    el("input", {
      type: "text",
      placeholder: "Buscar por nombre…",
      value: filter.q,
      onInput: debounce((ev) => { filter.q = ev.target.value; render(); }),
    }),
    el(
      "select",
      { onInput: (ev) => { filter.role = ev.target.value; render(); } },
      el("option", { value: "" }, "Todos los roles"),
      ...roles.map((r) => el("option", { value: r, selected: filter.role === r }, r)),
    ),
    el(
      "select",
      { onInput: (ev) => { filter.subject = ev.target.value; render(); } },
      el("option", { value: "" }, "Todas las asignaturas"),
      ...subjects.map((s) => el("option", { value: s, selected: filter.subject === s }, s)),
    ),
  );

  const list = people.length
    ? el("div", { className: "task-list" }, ...people.map((p) => renderPersonRow(p)))
    : el("p", { className: "hint" }, "No hay contactos con este filtro.");

  root.replaceChildren(toolbar, filters, list);
}

function renderPersonRow(person) {
  return el(
    "div",
    { className: "task-row panel", onClick: () => openPersonDetail(person), style: "cursor:pointer" },
    el(
      "div",
      { className: "task-row-main" },
      el("div", { className: "task-row-title" }, person.name),
      el(
        "div",
        { className: "task-row-meta" },
        person.role ? el("span", { className: "mono-tag" }, person.role) : null,
        person.subject ? el("span", { className: "mono-tag" }, person.subject) : null,
        person.email ? el("span", { className: "hint" }, person.email) : null,
      ),
    ),
    el(
      "button",
      {
        className: "btn-ghost",
        title: "Borrar",
        onClick: async (ev) => { ev.stopPropagation(); await uned.deletePerson(person.id); render(); },
      },
      icon("trash-2", { size: 14 }),
    ),
  );
}

function debounce(fn, wait = 300) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), wait);
  };
}

// ---- detalle de persona + interacciones ----

async function openPersonDetail(person) {
  renderPersonModal(person, []);
  await refreshPersonModal(person);
}

async function refreshPersonModal(person) {
  let interactions = [];
  try {
    interactions = await uned.listInteractions(person.id);
  } catch {
    // sin interacciones cargadas si falla; se muestra el resto igualmente
  }
  renderPersonModal(person, interactions);
}

function renderPersonModal(person, interactions) {
  const body = el(
    "div",
    {},
    el(
      "div",
      { className: "chip-row" },
      person.role ? el("span", { className: "mono-tag" }, person.role) : null,
      person.subject ? el("span", { className: "mono-tag" }, person.subject) : null,
    ),
    person.email ? el("div", {}, "Email: ", el("a", { href: `mailto:${person.email}` }, person.email)) : null,
    person.phone ? el("div", {}, "Teléfono: ", person.phone) : null,
    person.notes ? el("p", { className: "glossary-term-def" }, person.notes) : null,
    el("h4", {}, "Interacciones"),
    interactions.length
      ? el(
          "div",
          { className: "day-detail-list" },
          ...interactions.map((i) => renderInteraction(i, person)),
        )
      : el("p", { className: "hint" }, "Todavía no hay interacciones registradas."),
    renderInteractionForm(person),
  );

  showModal(person.name, body, [
    el(
      "button",
      { className: "btn-danger", onClick: async () => { await uned.deletePerson(person.id); closeModal(); render(); } },
      icon("trash-2", { size: 14 }),
      "Borrar persona",
    ),
  ]);
}

function renderInteraction(interaction, person) {
  return el(
    "div",
    { className: "day-detail-item" },
    el(
      "div",
      { className: "day-detail-item-head" },
      el("strong", {}, interaction.title),
      el("span", { className: "hint" }, interaction.date),
      interaction.channel ? el("span", { className: "mono-tag" }, interaction.channel) : null,
    ),
    interaction.detail ? el("p", {}, interaction.detail) : null,
    el(
      "button",
      {
        className: "btn-ghost",
        onClick: async () => { await uned.deleteInteraction(interaction.id); await refreshPersonModal(person); },
      },
      icon("trash-2", { size: 14 }),
      "Borrar",
    ),
  );
}

function renderInteractionForm(person) {
  const titleInput = el("input", { type: "text", placeholder: "Título (ej. Consulta por email)" });
  const channelInput = el("input", { type: "text", placeholder: "Canal (email, llamada, presencial…)" });
  const detailInput = el("textarea", { rows: 2, placeholder: "Detalle" });

  return el(
    "form",
    {
      className: "calendar-form-fields",
      onSubmit: async (ev) => {
        ev.preventDefault();
        const title = titleInput.value.trim();
        if (!title) return;
        await uned.createInteraction(person.id, {
          title,
          channel: channelInput.value.trim() || null,
          detail: detailInput.value,
        });
        await refreshPersonModal(person);
      },
    },
    el("label", {}, "Nueva interacción", titleInput),
    channelInput,
    detailInput,
    el("button", { type: "submit", className: "btn-primary" }, "Añadir interacción"),
  );
}

// ---- alta de persona ----

function openPersonForm() {
  const nameInput = el("input", { type: "text", placeholder: "Nombre", required: true });
  const roleInput = el("input", { type: "text", placeholder: "Rol (profesor, tutor, secretaría…)" });
  roleInput.setAttribute("list", "contacts-roles");
  const subjectInput = el("input", { type: "text", placeholder: "Asignatura (opcional)" });
  subjectInput.setAttribute("list", "contacts-subjects");
  const emailInput = el("input", { type: "email", placeholder: "Email" });
  const phoneInput = el("input", { type: "text", placeholder: "Teléfono" });
  const notesInput = el("textarea", { rows: 3, placeholder: "Notas (despacho, horario de tutoría…)" });
  const alertBox = el("div", { className: "error-banner" });

  const form = el(
    "form",
    {
      className: "panel glossary-form",
      onSubmit: async (ev) => {
        ev.preventDefault();
        const name = nameInput.value.trim();
        if (!name) return;
        try {
          await uned.createPerson({
            name,
            role: roleInput.value.trim() || null,
            subject: subjectInput.value.trim() || null,
            email: emailInput.value.trim() || null,
            phone: phoneInput.value.trim() || null,
            notes: notesInput.value,
          });
          closeModal();
          render();
        } catch (error) {
          alertBox.textContent = error instanceof ApiError ? error.message : "No se pudo guardar.";
        }
      },
    },
    el("label", {}, "Nombre", nameInput),
    el("label", {}, "Rol", roleInput),
    el("datalist", { id: "contacts-roles" }, ...ROLE_SUGGESTIONS.map((r) => el("option", { value: r }))),
    el("label", {}, "Asignatura", subjectInput),
    el("datalist", { id: "contacts-subjects" }),
    el("label", {}, "Email", emailInput),
    el("label", {}, "Teléfono", phoneInput),
    el("label", {}, "Notas", notesInput),
    alertBox,
    el("button", { type: "submit", className: "btn-primary" }, "Añadir"),
  );

  listSubjects().then((subjects) => {
    form.querySelector("#contacts-subjects").replaceChildren(...subjects.map((s) => el("option", { value: s })));
  });

  showModal("Añadir persona", form, []);
}

export function initContacts() {
  document.addEventListener("activate-section", (ev) => {
    if (ev.detail.section !== "contactos") return;
    if (!loaded) {
      loaded = true;
      render();
    }
  });
}
