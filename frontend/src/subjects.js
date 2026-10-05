// Estudiar, organizado por asignatura. A la izquierda, las asignaturas (primero las que toca
// estudiar ahora); a la derecha, la elegida con tres cosas:
//   1. su temario (con el tema actual marcado y su material anotado, si existe),
//   2. las preguntas de cada tema (las del motor de estudio: leer, hojear, practicar),
//   3. una caja para preguntar a la IA sobre esa asignatura, cuya respuesta sale del RAG
//      (fragmentos de los documentos de esa asignatura + modelo local), con sus fuentes.

import { uned, study, ApiError } from "./api.js";
import { el } from "./dom.js";
import { renderMarkdown } from "./markdown.js";
import { navigate } from "./router.js";
import { sourceLink } from "./source-link.js";
import { subjectByFolder } from "./plan-semestre.js";
import { isNow } from "./syllabus.js";

const GRAY = "#7886a6";
const askHistory = new Map(); // carpeta de asignatura -> [{ question, topic, answer, sources, error }]
const MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];

const pad = (n) => String(n).padStart(2, "0");
const todayIso = () => {
  const d = new Date();
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
};

function shortDate(iso) {
  const [, m, d] = iso.split("-");
  return `${Number(d)} ${MONTHS[Number(m) - 1]}`;
}

function dateRange(item) {
  return item.from && item.to ? `${shortDate(item.from)} – ${shortDate(item.to)}` : "";
}

// ---- datos ----

async function loadData() {
  const today = todayIso();
  const end = new Date();
  end.setDate(end.getDate() + 30);
  const endIso = `${end.getFullYear()}-${pad(end.getMonth() + 1)}-${pad(end.getDate())}`;

  const [subjectsRes, docsRes, setsRes, dueRes, eventsRes] = await Promise.allSettled([
    uned.getSubjects(),
    study.listDocuments(),
    study.listSets(),
    study.dueReview(1),
    uned.listEvents({ start: today, end: endIso }),
  ]);
  const docs = docsRes.status === "fulfilled" ? docsRes.value : [];
  const sets = setsRes.status === "fulfilled" ? setsRes.value : [];
  const docsBySubject = new Map();
  for (const d of docs) {
    const folder = String(d.source_path || "").split("/")[1];
    if (!folder) continue;
    docsBySubject.set(folder, [...(docsBySubject.get(folder) ?? []), d]);
  }
  return {
    today,
    subjects: subjectsRes.status === "fulfilled" ? subjectsRes.value : [],
    docs,
    docsById: new Map(docs.map((d) => [d.id, d])),
    docsBySubject,
    setsByTrack: new Map(sets.map((s) => [s.track, s])),
    engineUp: docsRes.status === "fulfilled",
    due: dueRes.status === "fulfilled" ? dueRes.value.count_due : 0,
    events: eventsRes.status === "fulfilled" ? eventsRes.value : [],
  };
}

/** Cuánto toca estudiarla ahora: tema oficial en curso, material anotado y entregas cercanas. */
function priority(subject, data) {
  const plan = subject.plan;
  if (plan?.pending) return -10;
  let score = 0;
  if (plan?.syllabus.some((t) => isNow(t, data.today) && t.official)) score += 3;
  else if (plan?.syllabus.some((t) => isNow(t, data.today))) score += 1;
  if (data.docsBySubject.get(subject.folder)?.length) score += 2;
  const soon = data.events.some(
    (e) => ["entrega", "examen"].includes(e.type) && subjectByFolder(e.subject)?.key === plan?.key,
  );
  if (soon) score += 1;
  return score;
}

function enrich(subject) {
  const plan = subjectByFolder(subject.folder);
  return { ...subject, plan, color: plan?.color ?? GRAY };
}

// ---- pantalla ----

export async function showStudyHome(root, selectedFolder) {
  root.replaceChildren(el("p", { className: "hint" }, "Cargando…"));
  const data = await loadData();
  const subjects = data.subjects.map(enrich);
  if (!subjects.length) {
    root.replaceChildren(el("div", { className: "error-banner" }, "No se pudo cargar la lista de asignaturas. ¿Está el servidor arrancado?"));
    return;
  }

  const current = subjects
    .filter((s) => s.current)
    .map((s, i) => ({ s, i, p: priority(s, data) }))
    .sort((a, b) => b.p - a.p || a.i - b.i)
    .map((x) => x.s);
  const rest = subjects.filter((s) => !s.current);
  const selected = subjects.find((s) => s.folder === selectedFolder) ?? current[0] ?? subjects[0];

  const panel = el("section", { className: "study-panel" });
  const navButton = (s) =>
    el(
      "button",
      {
        className: "study-nav-item" + (s.folder === selected.folder ? " active" : ""),
        type: "button",
        onClick: () => navigate(`estudiar/materia/${s.folder}`),
      },
      el("span", { className: "study-nav-dot", style: `background:${s.color}` }),
      el("span", { className: "study-nav-text" }, el("strong", {}, s.name), el("small", {}, navMeta(s, data))),
    );

  const groups = new Map();
  for (const s of rest) {
    const key = s.semester === "anual" ? `Curso ${s.course} · anual` : `Curso ${s.course} · semestre ${s.semester}`;
    groups.set(key, [...(groups.get(key) ?? []), s]);
  }

  const nav = el(
    "nav",
    { className: "study-nav", "aria-label": "Asignaturas" },
    el("h3", {}, "Estudiar ahora"),
    ...current.map(navButton),
    el("h3", {}, "Resto de asignaturas"),
    ...[...groups.entries()].map(([label, list]) => {
      const details = el("details", { className: "study-nav-group" }, el("summary", {}, `${label} (${list.length})`), ...list.map(navButton));
      if (list.some((s) => s.folder === selected.folder)) details.open = true;
      return details;
    }),
    el("a", { className: "study-nav-link", href: "#/estudiar/documentos" }, "Todos los documentos anotados"),
  );

  const top = el(
    "div",
    { className: "study-topline" },
    data.engineUp
      ? null
      : el("span", { className: "study-warning" }, "Motor de estudio apagado (:8011): sin material anotado ni preguntas, pero puedes preguntar al RAG."),
    data.due
      ? el(
          "button",
          { className: "btn-mark", type: "button", onClick: () => navigate("estudiar/repasar") },
          `Repasar hoy · ${data.due} tarjeta${data.due === 1 ? "" : "s"}`,
        )
      : el("span", { className: "hint" }, "Nada pendiente de repaso hoy."),
  );

  root.replaceChildren(top, el("div", { className: "study-layout" }, nav, panel));
  renderSubject(panel, selected, data);
}

function navMeta(subject, data) {
  const plan = subject.plan;
  if (plan?.pending) return "Pendiente de reconocimiento";
  const now = plan?.syllabus.find((t) => isNow(t, data.today));
  const docs = data.docsBySubject.get(subject.folder)?.length ?? 0;
  const parts = [];
  if (now) parts.push(`Ahora: ${now.title.split(" · ")[0]}`);
  if (docs) parts.push(`${docs} doc. anotado${docs === 1 ? "" : "s"}`);
  if (!parts.length) parts.push(`${subject.document_count} documento${subject.document_count === 1 ? "" : "s"}`);
  return parts.join(" · ");
}

// ---- panel de una asignatura ----

function renderSubject(panel, subject, data) {
  panel.style.setProperty("--subject", subject.color);
  const plan = subject.plan;
  const readme = `asignaturas/${subject.folder}/README.md`;
  const now = plan?.syllabus.find((t) => isNow(t, data.today));

  const header = el(
    "header",
    { className: "study-subject-head" },
    el("h2", {}, subject.name),
    el(
      "div",
      { className: "hint" },
      `${subject.code} · ${subject.ects} ECTS · ${subject.semester === "anual" ? "anual" : `semestre ${subject.semester}`} del curso ${subject.course}`,
      subject.note ? ` · ${subject.note}` : "",
    ),
    el(
      "div",
      { className: "study-subject-actions" },
      now ? el("span", { className: "study-now" }, `Ahora: ${now.title}`) : null,
      el("a", { className: "dash-link-btn", href: `#/documentos/${encodeURIComponent(readme)}` }, `📁 ${subject.document_count} documentos`),
    ),
  );

  const askTopics = plan?.syllabus ?? [];
  const askBox = renderAskBox(subject, askTopics);
  panel.replaceChildren(header, renderSyllabus(subject, data, askBox), askBox.node);
}

function renderSyllabus(subject, data, askBox) {
  const plan = subject.plan;
  const items = plan?.syllabus ?? [];
  const section = el("section", { className: "study-card-block" }, el("h3", {}, "Temario y preguntas"));

  if (plan?.pending) {
    section.append(el("p", { className: "hint" }, plan.pending));
  } else if (!items.length) {
    section.append(
      el(
        "p",
        { className: "hint" },
        "Todavía no hay temario cargado para esta asignatura. Puedes preguntar al RAG sobre sus documentos (guía docente, apuntes) más abajo.",
      ),
    );
  }

  const list = el("div", { className: "syllabus-list" });
  for (const item of items) {
    const doc = item.doc ? data.docsById.get(item.doc) : null;
    const set = doc ? data.setsByTrack.get(doc.id) : null;
    const now = isNow(item, data.today);
    const row = el(
      "article",
      { className: "syllabus-row" + (now ? " now" : "") },
      el(
        "div",
        { className: "syllabus-head" },
        el("strong", {}, item.title),
        now ? el("span", { className: "study-now" }, "ahora") : null,
        el("span", { className: "dash-source " + (item.official ? "official" : "plan") }, `${item.official ? "oficial" : "orientativo"} · ${dateRange(item)}`),
      ),
    );

    if (doc && set) {
      const questionsBox = el("div", { className: "question-list" });
      let loaded = false;
      const toggle = el(
        "button",
        {
          className: "btn-ghost",
          type: "button",
          onClick: async () => {
            const open = !questionsBox.classList.contains("open");
            questionsBox.classList.toggle("open", open);
            toggle.textContent = open ? "Ocultar preguntas" : `Ver las ${set.question_count} preguntas`;
            if (open && !loaded) {
              loaded = true;
              await fillQuestions(questionsBox, set.id);
            }
          },
        },
        `Ver las ${set.question_count} preguntas`,
      );
      row.append(
        el("div", { className: "hint" }, `Material anotado: ${doc.title}${item.docNote ? ` — ${item.docNote}` : ""}`),
        el(
          "div",
          { className: "syllabus-actions" },
          el("button", { className: "btn-mark", type: "button", onClick: () => navigate(`estudiar/${doc.id}/quiz`) }, `Practicar · ${set.question_count} preguntas`),
          el("button", { className: "btn-ghost", type: "button", onClick: () => navigate(`estudiar/${doc.id}`) }, "Leer"),
          toggle,
          el("button", { className: "btn-ghost", type: "button", onClick: () => askBox.focusTopic(item.id) }, "Preguntar"),
        ),
        questionsBox,
      );
    } else {
      row.append(
        el("div", { className: "hint" }, "Sin material anotado ni preguntas todavía."),
        el(
          "div",
          { className: "syllabus-actions" },
          el("button", { className: "btn-ghost", type: "button", onClick: () => askBox.focusTopic(item.id) }, "Preguntar sobre este tema"),
        ),
      );
    }
    list.append(row);
  }
  if (items.length) section.append(list);
  return section;
}

async function fillQuestions(box, setId) {
  box.replaceChildren(el("p", { className: "hint" }, "Cargando preguntas…"));
  try {
    const questions = await study.listSetQuestions(setId);
    box.replaceChildren(
      ...questions.map((q) => {
        const body = [];
        if (q.options) {
          body.push(
            el(
              "ol",
              { className: "question-options", type: "A" },
              ...q.options.map((o, i) => el("li", { className: i === q.correct_index ? "correct" : "" }, o)),
            ),
          );
        }
        body.push(el("p", { className: "question-notes" }, q.answer_notes));
        const link = sourceLink(q);
        if (link) body.push(link);
        return el(
          "details",
          { className: "question-item" },
          el(
            "summary",
            {},
            el("span", { className: "mono-tag" }, q.type === "mc" ? "test" : "tarjeta"),
            el("span", { className: "mono-tag" }, q.topic),
            q.prompt,
          ),
          ...body,
        );
      }),
    );
  } catch (error) {
    box.replaceChildren(el("div", { className: "error-banner" }, error instanceof ApiError ? error.message : "No se pudieron cargar las preguntas."));
  }
}

// ---- preguntar a la IA (RAG) ----

function renderAskBox(subject, topics) {
  const log = el("div", { className: "ask-log" });
  const status = el("span", { className: "hint" });
  const input = el("textarea", {
    rows: 3,
    placeholder: `Escribe tu pregunta sobre ${subject.name}…`,
    required: true,
  });
  const topicSelect = el(
    "select",
    { "aria-label": "Tema" },
    el("option", { value: "" }, "Toda la asignatura"),
    ...topics.map((t) => el("option", { value: t.id }, t.title)),
  );
  const submit = el("button", { className: "btn-mark", type: "submit" }, "Preguntar");

  const renderLog = () => {
    const entries = askHistory.get(subject.folder) ?? [];
    log.replaceChildren(
      ...[...entries].reverse().map((e) =>
        el(
          "article",
          { className: "ask-entry" },
          el("div", { className: "ask-question" }, el("strong", {}, "Tú: "), e.question, e.topic ? el("span", { className: "mono-tag" }, e.topic) : null),
          e.error
            ? el("div", { className: "error-banner" }, e.error)
            : el(
                "div",
                { className: "ask-answer" },
                el("div", { className: "markdown-body", html: renderMarkdown(e.answer, "") }),
                e.sources?.length
                  ? el(
                      "div",
                      { className: "sources" },
                      el("strong", {}, "Fuentes (RAG): "),
                      ...e.sources.map((s) =>
                        el(
                          "a",
                          { href: `#/documentos/${encodeURIComponent(s.source)}`, title: s.snippet || s.source },
                          s.source.split("/").pop(),
                        ),
                      ),
                    )
                  : null,
              ),
        ),
      ),
    );
  };

  const form = el(
    "form",
    {
      className: "ask-form",
      onSubmit: async (ev) => {
        ev.preventDefault();
        const question = input.value.trim();
        if (!question) return;
        const topic = topics.find((t) => t.id === topicSelect.value)?.title ?? "";
        submit.disabled = true;
        status.textContent = "Consultando tus apuntes con el modelo local… puede tardar unos segundos.";
        const entry = { question, topic };
        try {
          const data = await uned.ragQuery(question, { subject: subject.folder, topic, k: 6 });
          entry.answer = data.answer;
          entry.sources = data.sources;
        } catch (error) {
          entry.error = error instanceof ApiError ? `No se pudo responder: ${error.message}` : "No se pudo consultar el RAG. ¿Están arrancados el servidor y Ollama?";
        }
        askHistory.set(subject.folder, [...(askHistory.get(subject.folder) ?? []), entry]);
        input.value = "";
        status.textContent = "";
        submit.disabled = false;
        renderLog();
      },
    },
    el("div", { className: "ask-row" }, el("label", {}, "Tema", topicSelect)),
    input,
    el("div", { className: "ask-row" }, submit, status),
  );

  const node = el(
    "section",
    { className: "study-card-block ask-block" },
    el("h3", {}, `Pregunta a la IA sobre ${subject.name}`),
    el(
      "p",
      { className: "hint" },
      "La respuesta sale del RAG: se buscan los fragmentos de los documentos de esta asignatura y el modelo local responde solo con ellos, citando las fuentes.",
    ),
    form,
    log,
  );
  renderLog();

  return {
    node,
    focusTopic(topicId) {
      topicSelect.value = topicId;
      node.scrollIntoView({ behavior: "smooth", block: "center" });
      input.focus();
    },
  };
}
