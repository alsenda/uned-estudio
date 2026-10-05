/** Buscar en apuntes: consulta al RAG local (ChromaDB + Ollama). */

import { uned } from "./api.js";
import { el } from "./dom.js";
import { icon } from "./icons.js";

const form = document.getElementById("rag-form");
const questionInput = document.getElementById("rag-question");
const statusEl = document.getElementById("rag-status");
const answerEl = document.getElementById("rag-answer");
const searchIconSlot = document.getElementById("rag-search-icon");

export function initRag() {
  searchIconSlot.append(icon("search", { size: 18 }));
  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const q = questionInput.value.trim();
    if (!q) return;
    statusEl.textContent = "Buscando…";
    answerEl.replaceChildren();
    try {
      const data = await uned.ragQuery(q);
      statusEl.textContent = "";
      answerEl.replaceChildren(
        el("div", { className: "answer-text panel" }, data.answer),
        data.sources?.length
          ? el(
              "div",
              { className: "sources" },
              "Fuentes:",
              ...data.sources.map((s) =>
                el(
                  "div",
                  {},
                  "— ",
                  el("a", { href: `#/documentos/${encodeURIComponent(s.source)}` }, s.source),
                ),
              ),
            )
          : null,
      );
    } catch {
      statusEl.textContent = "Error al consultar el RAG. ¿Está el servidor arrancado?";
    }
  });
}
