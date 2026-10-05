/** Estudiar a fondo: documentos anotados (motor estudio-profundo, :8011)
 * con lector + pila de fichas, y quiz/flashcards con progreso persistente. */

import { study, ApiError } from "./api.js";
import { el } from "./dom.js";
import { icon } from "./icons.js";
import { renderPassage } from "./annotated.js";
import { openEntity } from "./cards.js";
import { sourceLink } from "./source-link.js";
import { navigate } from "./router.js";
import { setTopbarContext, refreshRailStreak } from "./main.js";
import { showStudyHome } from "./subjects.js";

const root = document.getElementById("study-root");

export function documentCard(doc, { compact = false } = {}) {
  const masteryPct = doc.mastery === null ? null : Math.round(doc.mastery * 100);
  const meterFill = el("div", {});
  meterFill.style.width = `${masteryPct ?? 0}%`;

  const card = el(
    "article",
    { className: "study-card" + (compact ? " compact" : "") },
    el("h3", {}, doc.title),
    !compact ? el("div", { className: "hint" }, `${doc.passage_count} pasajes · ${doc.entity_count} entidades`) : null,
    el(
      "div",
      { className: "mastery-row" },
      el("div", { className: "meter" }, meterFill),
      el("span", { className: "mono-tag" }, masteryPct === null ? "sin practicar" : `${masteryPct}%`),
    ),
    doc.open_inconsistencies
      ? el(
          "div",
          { className: "study-warning" },
          `⚠ ${doc.open_inconsistencies} incoherencia${doc.open_inconsistencies === 1 ? "" : "s"} sin resolver`,
        )
      : null,
    el(
      "div",
      { className: "study-card-actions" },
      el("button", { className: "btn-mark", onClick: () => navigate(`estudiar/${doc.id}`) }, icon("book-open", { size: 15 }), "Leer"),
      el("button", { className: "btn-ghost", onClick: () => navigate(`estudiar/${doc.id}/quiz`) }, icon("layers", { size: 15 }), "Estudiar"),
    ),
  );
  return card;
}

// Cuadrícula de todos los documentos anotados (la vista original de Estudiar); ahora se llega
// desde «Todos los documentos anotados», en #/estudiar/documentos.
export async function showDocumentGrid() {
  root.replaceChildren(el("p", { className: "hint" }, "Cargando…"));
  setTopbarContext(el("a", { href: "#/estudiar" }, "← Estudiar por asignatura"));
  let docs;
  try {
    docs = await study.listDocuments();
  } catch {
    root.replaceChildren(
      el(
        "div",
        { className: "error-banner" },
        "No se pudo contactar con el motor de estudio en :8011. ¿Está arrancado? Abre la web con Iniciar.bat (o iniciar.sh).",
      ),
    );
    return;
  }
  if (!docs.length) {
    root.replaceChildren(
      el(
        "div",
        { className: "empty-state" },
        el("h2", {}, "Todavía no hay documentos en profundidad"),
        el("p", { className: "hint" }, "Se autorían con Claude y se cargan con scripts/seed.py en estudio-profundo/."),
      ),
    );
    return;
  }
  root.replaceChildren(el("div", { className: "study-grid" }, ...docs.map((d) => documentCard(d))));
}

async function showReader(documentId, focus = {}) {
  root.replaceChildren(el("p", { className: "hint" }, "Cargando…"));
  void study.logAccess("document", documentId);
  try {
    const [document_, inconsistencies] = await Promise.all([
      study.getDocument(documentId),
      study.listInconsistencies(documentId, "open"),
    ]);
    setTopbarContext(el("span", {}, document_.title));
    const view = el(
      "div",
      { className: "reader" },
      el(
        "div",
        { className: "reader-header" },
        el("a", { href: "#/estudiar" }, "← Estudiar"),
        el("h2", { className: "pane-heading" }, document_.title),
      ),
    );
    if (inconsistencies.length) view.append(inconsistencyPanel(inconsistencies));
    document_.passages.forEach((p) => view.append(renderPassage(p, openEntity)));
    root.replaceChildren(view);
    focusPassage(documentId, focus);
  } catch (error) {
    root.replaceChildren(
      el("div", { className: "error-banner" }, error instanceof ApiError ? error.message : "No se pudo cargar el documento."),
    );
  }
}

/** Llegada desde "Ver en el texto": desplaza al pasaje, lo resalta un momento y abre la idea. */
function focusPassage(documentId, { passageId, entityId } = {}) {
  if (!passageId) return;
  // El API cualifica los ids como "<documento>::<id>"; la URL lleva solo el id corto.
  const qualify = (id) => `${documentId}::${id}`;
  const target = document.getElementById(`passage-${qualify(passageId)}`);
  if (target) {
    target.scrollIntoView({ block: "center", behavior: "smooth" });
    target.classList.add("passage-focus");
    setTimeout(() => target.classList.remove("passage-focus"), 2600);
  }
  if (entityId) openEntity(qualify(entityId));
}

function inconsistencyPanel(items) {
  const panel = el("details", { className: "inconsistency-panel", open: true });
  panel.append(
    el("summary", {}, `⚠ ${items.length} incoherencia${items.length === 1 ? "" : "s"} detectada${items.length === 1 ? "" : "s"} — pendientes de resolver`),
  );
  items.forEach((item) => panel.append(inconsistencyCard(item)));
  return panel;
}

function inconsistencyCard(item) {
  const status = el("span", { className: "hint" }, "");
  const actionsSlot = el("div", { className: "inconsistency-actions" });
  const card = el(
    "div",
    { className: "inconsistency-card" },
    el("div", { className: "inconsistency-summary" }, `${item.entity_name}: ${item.summary}`),
    el(
      "div",
      { className: "inconsistency-mentions" },
      el("div", { className: "mention" }, el("strong", {}, item.mention_a_location), el("p", {}, item.mention_a_quote)),
      el("div", { className: "mention" }, el("strong", {}, item.mention_b_location), el("p", {}, item.mention_b_quote)),
    ),
    actionsSlot,
  );

  const resolve = (resolution, note) => {
    void (async () => {
      try {
        await study.resolveInconsistency(item.id, resolution, note);
        card.remove();
      } catch {
        status.textContent = "No se pudo resolver.";
      }
    })();
  };

  const showAiForm = () => {
    const textarea = el("textarea", { className: "ai-note-input", placeholder: "Explica cómo debería resolverlo la IA (obligatorio)…" });
    actionsSlot.replaceChildren(
      textarea,
      el(
        "div",
        { className: "inconsistency-actions" },
        el("button", { className: "btn-mark", onClick: () => (textarea.value.trim() ? resolve("ai", textarea.value.trim()) : (status.textContent = "Escribe una explicación.")) }, "Confirmar"),
        el("button", { className: "btn-ghost", onClick: showDefault }, "Cancelar"),
      ),
    );
  };
  const showDefault = () => {
    actionsSlot.replaceChildren(
      el("button", { className: "btn-ghost", onClick: () => resolve("a") }, "Es correcto A"),
      el("button", { className: "btn-ghost", onClick: () => resolve("b") }, "Es correcto B"),
      el("button", { className: "btn-ghost", onClick: showAiForm }, "Que lo resuelva la IA"),
      el("button", { className: "btn-ghost", onClick: () => resolve("dismiss") }, "No es una incoherencia real"),
      status,
    );
  };
  showDefault();
  return card;
}

// --- Quiz / flashcards ---

function tagChips(question) {
  return el(
    "div",
    { className: "tag-row" },
    el("span", { className: "mono-tag" }, question.tags.difficulty),
    el("span", { className: "mono-tag" }, question.tags.typicality),
    ...question.tags.topics.map((t) => el("span", { className: "mono-tag" }, t)),
  );
}

async function reviewedTodayBaseline() {
  try {
    return (await study.engagementSummary()).reviewed_today;
  } catch {
    return null; // motor de engagement no disponible: se omite el contador, sin error visible
  }
}

async function startQuiz(track) {
  root.replaceChildren(el("p", { className: "hint" }, "Cargando…"));
  let session;
  try {
    session = await study.startSession({ track, level: 1, mode: "level" });
  } catch (error) {
    root.replaceChildren(
      el("div", { className: "error-banner" }, error instanceof ApiError ? error.message : "No se pudo iniciar la sesión."),
    );
    return;
  }
  runSession(session, 0, [], await reviewedTodayBaseline());
}

async function startReview() {
  root.replaceChildren(el("p", { className: "hint" }, "Cargando…"));
  setTopbarContext(el("span", {}, "Repasar hoy"));
  let session;
  try {
    session = await study.startSession({ mode: "review", limit: 20 });
  } catch (error) {
    root.replaceChildren(
      el(
        "div",
        { className: "error-banner" },
        error instanceof ApiError ? error.message : "No se pudo iniciar el repaso.",
      ),
    );
    return;
  }
  runSession(session, 0, [], await reviewedTodayBaseline());
}

function runSession(session, index, outcomes, reviewedTodayBase) {
  const question = session.questions[index];
  if (!question) {
    void showSummary(session, outcomes);
    return;
  }

  const back = el("div", { className: "card-face back" });
  const front = el("div", { className: "card-face front" }, tagChips(question), el("div", { className: "prompt" }, question.prompt));
  const card = el("div", { className: "card" }, front, back);

  const submit = async (answer) => {
    try {
      return await study.submitAnswer({ session_id: session.id, question_id: question.id, ...answer });
    } catch {
      return null;
    }
  };
  const next = () => runSession(session, index + 1, outcomes, reviewedTodayBase);

  if (question.type === "mc" && question.options) {
    const buttons = question.options.map((option, i) =>
      el(
        "button",
        {
          onClick: async () => {
            buttons.forEach((b) => (b.disabled = true));
            const result = await submit({ chosen_index: i });
            if (!result) return;
            outcomes.push({ question, result });
            fillMcBack(back, question, i, result, next);
            card.classList.add("flipped");
          },
        },
        `${String.fromCharCode(65 + i)}. ${option}`,
      ),
    );
    front.append(el("div", { className: "options" }, ...buttons));
  } else {
    front.append(
      el(
        "div",
        { className: "card-actions" },
        el(
          "button",
          {
            onClick: () => {
              fillFlashcardBack(back, question, async (rating) => {
                const result = await submit({ self_rating: rating });
                if (!result) return;
                outcomes.push({ question, result });
                next();
              });
              card.classList.add("flipped");
            },
          },
          "Girar tarjeta — ver respuesta",
        ),
      ),
    );
  }

  root.replaceChildren(
    el(
      "div",
      { className: "quiz-header" },
      el("a", { href: "#/estudiar" }, "← Estudiar"),
      el(
        "div",
        { style: "display:flex; align-items:center; gap:0.75rem;" },
        el("span", { className: "mono-tag" }, `Tarjeta ${index + 1} / ${session.questions.length}`),
        reviewedTodayBase === null
          ? null
          : el(
              "span",
              { className: "quiz-streak" },
              icon("flame", { size: 14 }),
              `${reviewedTodayBase + index} repasadas hoy`,
            ),
      ),
    ),
    el("div", { className: "card-scene" }, card),
  );
}

function fillMcBack(back, question, chosenIndex, result, next) {
  const options = question.options ?? [];
  const correctText = result.correct_index !== null ? options[result.correct_index] ?? "" : "";
  back.replaceChildren(
    el("div", { className: `verdict ${result.correct ? "good" : "bad"}` }, result.correct ? "✓ Correcto" : "✗ No exactamente"),
    el(
      "div",
      { className: "answer-notes" },
      result.correct ? "" : `Elegiste: ${options[chosenIndex] ?? ""}\nRespuesta correcta: ${correctText}\n\n`,
      result.answer_notes,
    ),
    sourceLink(question, { newTab: true }),
    el("div", { className: "card-actions" }, el("button", { onClick: next }, "Siguiente tarjeta →")),
  );
}

function fillFlashcardBack(back, question, onRate) {
  const ratingButton = (rating, label) => el("button", { className: `rating-${rating}`, onClick: () => onRate(rating) }, label);
  back.replaceChildren(
    el("div", { className: "verdict" }, "Respuesta modelo"),
    el("div", { className: "answer-notes" }, question.answer_notes),
    sourceLink(question, { newTab: true }),
    el("div", { className: "hint" }, "¿Cómo se compara con lo que habrías respondido? Sé honesto."),
    el(
      "div",
      { className: "card-actions" },
      ratingButton("again", "Otra vez (0)"),
      ratingButton("hard", "Difícil (0.4)"),
      ratingButton("good", "Bien (0.8)"),
      ratingButton("easy", "Fácil (1.0)"),
    ),
  );
}

async function showSummary(session, outcomes) {
  try {
    await study.finishSession(session.id);
  } catch {
    // el resumen se muestra igual
  }
  void refreshRailStreak(); // la racha/XP acaban de cambiar con estas respuestas

  const total = outcomes.reduce((sum, o) => sum + o.result.score, 0);
  const pct = outcomes.length ? Math.round((total / outcomes.length) * 100) : 0;
  const subjects = [...new Set(outcomes.map((o) => o.question.set_id))].length;

  const summary = el(
    "div",
    { className: "summary-card" },
    el("h2", { className: "pane-heading" }, "Sesión completada"),
    el("div", { className: "summary-score" }, `${pct}%`),
    el(
      "p",
      { className: "hint" },
      `Has repasado ${outcomes.length} tarjeta${outcomes.length === 1 ? "" : "s"}${subjects > 1 ? ` de ${subjects} documentos` : ""} hoy.`,
    ),
    el("div", { className: "summary-badges", id: "summary-badges" }),
    el(
      "ul",
      { className: "summary-list" },
      ...outcomes.map((o) =>
        el("li", {}, `${o.result.score >= 1 ? "✓" : o.result.score > 0 ? "±" : "✗"} [${o.question.topic}] ${o.question.prompt.slice(0, 90)}`),
      ),
    ),
    el("button", { className: "btn-mark", onClick: () => navigate("estudiar") }, "Volver a Estudiar"),
  );
  root.replaceChildren(summary);

  try {
    const { badges } = await study.engagementSummary();
    summary.querySelector("#summary-badges").replaceChildren(
      ...badges.map((b) => el("span", { className: "tag tag-accent" }, icon("flag-triangle-right", { size: 12 }), b.label)),
    );
  } catch {
    // sin insignias visibles si el motor de engagement no responde; el resto del resumen ya se ve
  }
}

export function initStudy() {
  document.addEventListener("activate-section", (ev) => {
    if (ev.detail.section !== "estudiar") return;
    const [documentId, sub, passageId, entityId] = ev.detail.rest;
    if (documentId === "repasar") startReview();
    else if (!documentId) showStudyHome(root, null);
    else if (documentId === "materia") showStudyHome(root, sub ?? null);
    else if (documentId === "documentos") showDocumentGrid();
    else if (sub === "quiz") startQuiz(documentId);
    else if (sub === "leer") showReader(documentId, { passageId, entityId });
    else showReader(documentId);
  });
}
