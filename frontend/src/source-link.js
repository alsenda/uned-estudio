/** Enlace "Ver en el texto" de una pregunta: lleva al pasaje del lector anotado
 * ("Leer") que respalda la pregunta y, si la pregunta apunta a una idea concreta,
 * abre su tarjeta. `question.source` lo rellena el motor de estudio (campo
 * opcional `source` de cada pregunta en quiz.json). */

import { el } from "./dom.js";

export function sourceHref(question) {
  const s = question.source;
  if (!s) return null;
  const doc = s.document_id || question.set_id;
  const parts = ["estudiar", doc, "leer", s.passage_id, ...(s.entity_id ? [s.entity_id] : [])];
  return "#/" + parts.map(encodeURIComponent).join("/");
}

/** `newTab`: abre el lector en otra pestaña (para no perder una sesión de preguntas en curso). */
export function sourceLink(question, { newTab = false } = {}) {
  const href = sourceHref(question);
  if (!href) return null;
  return el(
    "a",
    {
      className: "source-link",
      href: newTab ? location.pathname + href : href,
      target: newTab ? "_blank" : false,
      rel: newTab ? "noopener" : false,
    },
    "📖 Ver en el texto →",
  );
}
