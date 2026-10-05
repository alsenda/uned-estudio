/** Glosario: términos filtrables por asignatura y por tag — respaldado por
 * `glossary/terms/*.md` (ver backend/app/glossary/store.py), mismo patrón de
 * fichero-por-registro que el resto de "datos reales" de la app. */

import { uned, ApiError } from "./api.js";
import { el } from "./dom.js";
import { icon } from "./icons.js";

const root = document.getElementById("glossary-root");

let filter = { subject: "", tag: "", q: "" };
let subjectsCache = null;
let loaded = false;
let formOpen = false;

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

  let terms, tags, subjects;
  try {
    [terms, tags, subjects] = await Promise.all([
      uned.listTerms({ subject: filter.subject, tag: filter.tag, q: filter.q }),
      uned.listTags(),
      listSubjects(),
    ]);
  } catch {
    root.replaceChildren(el("p", { className: "error-banner" }, "No se pudo cargar el glosario. ¿Está el servidor arrancado?"));
    return;
  }

  const formSlot = el("div", { id: "glossary-form-slot" });

  const toolbar = el(
    "div",
    { className: "calendar-toolbar" },
    el("h2", { className: "pane-heading" }, "Glosario"),
    el(
      "button",
      { className: "btn-primary", onClick: () => toggleForm(formSlot) },
      icon("plus", { size: 16 }),
      "Añadir término",
    ),
  );

  const filters = el(
    "div",
    { className: "feed-controls" },
    el("input", {
      type: "text",
      placeholder: "Buscar…",
      value: filter.q,
      onInput: debounce((ev) => { filter.q = ev.target.value; render(); }),
    }),
    el(
      "select",
      { onInput: (ev) => { filter.subject = ev.target.value; render(); } },
      el("option", { value: "" }, "Todas las asignaturas"),
      ...subjects.map((s) => el("option", { value: s, selected: filter.subject === s }, s)),
    ),
  );

  const tagRow = tags.length
    ? el(
        "div",
        { className: "chip-row" },
        ...tags.map((t) =>
          el(
            "button",
            {
              className: "chip" + (filter.tag === t ? " active" : ""),
              onClick: () => { filter.tag = filter.tag === t ? "" : t; render(); },
            },
            t,
          ),
        ),
      )
    : null;

  const list = terms.length
    ? el("div", { className: "glossary-list" }, ...terms.map((t) => renderTermCard(t)))
    : el("p", { className: "hint" }, "No hay términos con este filtro.");

  root.replaceChildren(...[toolbar, formSlot, filters, tagRow, list].filter(Boolean));
  if (formOpen) openTermForm(formSlot);
}

function renderTermCard(term) {
  return el(
    "div",
    { className: "panel glossary-term" },
    el(
      "div",
      { className: "glossary-term-head" },
      el("h3", {}, term.term),
      el(
        "div",
        { className: "glossary-term-actions" },
        el("button", { className: "btn-ghost", title: "Editar", onClick: () => editTerm(term) }, icon("pencil", { size: 14 })),
        el(
          "button",
          { className: "btn-ghost", title: "Borrar", onClick: async () => { await uned.deleteTerm(term.id); render(); } },
          icon("trash-2", { size: 14 }),
        ),
      ),
    ),
    term.subject || term.tags?.length
      ? el(
          "div",
          { className: "chip-row" },
          term.subject ? el("span", { className: "mono-tag" }, term.subject) : null,
          ...(term.tags ?? []).map((t) => el("span", { className: "mono-tag" }, t)),
        )
      : null,
    el("p", { className: "glossary-term-def" }, term.definition),
  );
}

function toggleForm(formSlot) {
  formOpen = !formOpen;
  if (formOpen) openTermForm(formSlot); else formSlot.replaceChildren();
}

function editTerm(term) {
  formOpen = true;
  const formSlot = document.getElementById("glossary-form-slot");
  if (formSlot) openTermForm(formSlot, term);
}

function debounce(fn, wait = 300) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), wait);
  };
}

function openTermForm(formSlot, existing) {
  const termInput = el("input", { type: "text", placeholder: "Término", value: existing?.term ?? "", required: true });
  const subjectInput = el("input", { type: "text", placeholder: "Asignatura (opcional)", value: existing?.subject ?? "" });
  subjectInput.setAttribute("list", "glossary-subjects");
  const tagsInput = el("input", { type: "text", placeholder: "Tags separados por coma", value: (existing?.tags ?? []).join(", ") });
  const defInput = el("textarea", { rows: 4, placeholder: "Definición", value: existing?.definition ?? "" });
  const alertBox = el("div", { className: "error-banner" });

  const form = el(
    "form",
    {
      className: "panel glossary-form",
      onSubmit: async (ev) => {
        ev.preventDefault();
        const term = termInput.value.trim();
        if (!term) return;
        const tags = tagsInput.value.split(",").map((t) => t.trim()).filter(Boolean);
        try {
          if (existing) {
            await uned.updateTerm(existing.id, { term, subject: subjectInput.value.trim() || null, tags, definition: defInput.value });
          } else {
            await uned.createTerm({ term, subject: subjectInput.value.trim() || null, tags, definition: defInput.value });
          }
          formOpen = false;
          render();
        } catch (error) {
          alertBox.textContent = error instanceof ApiError ? error.message : "No se pudo guardar.";
        }
      },
    },
    el("label", {}, "Término", termInput),
    el("label", {}, "Asignatura", subjectInput),
    el("datalist", { id: "glossary-subjects" }),
    el("label", {}, "Tags", tagsInput),
    el("label", {}, "Definición", defInput),
    alertBox,
    el(
      "div",
      { className: "glossary-form-actions" },
      el("button", { type: "submit", className: "btn-primary" }, existing ? "Guardar cambios" : "Añadir"),
      el("button", { type: "button", className: "btn-ghost", onClick: () => { formOpen = false; render(); } }, "Cancelar"),
    ),
  );

  listSubjects().then((subjects) => {
    form.querySelector("#glossary-subjects").replaceChildren(...subjects.map((s) => el("option", { value: s })));
  });

  formSlot.replaceChildren(form);
}

export function initGlossary() {
  document.addEventListener("activate-section", (ev) => {
    if (ev.detail.section !== "glosario") return;
    if (!loaded) {
      loaded = true;
      render();
    }
  });
}
