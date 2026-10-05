/**
 * The card stack — the signature interaction, and the answer to "más
 * niveles de detalle que footnoted": opening a highlighted term pulls a new
 * index card forward; earlier cards stay stacked behind it with just their
 * tab showing, like drawing cards from a catalog drawer. Click any visible
 * tab to jump back to that level. Depth is whatever the data supports, not
 * a fixed limit — each card's own body is rendered by the same annotated
 * passage renderer, so its highlights are just as clickable.
 */

import { study, ApiError } from "./api.js";
import { el } from "./dom.js";
import { icon } from "./icons.js";
import { renderPassage } from "./annotated.js";

const container = document.getElementById("card-stack");
let stack = [];

export function openEntity(entityId) {
  void (async () => {
    container.classList.add("open");
    try {
      const entity = await study.getEntity(entityId);
      stack.push(entity);
      render();
    } catch (error) {
      renderError(error instanceof ApiError ? error.message : "No se pudo cargar la referencia.");
    }
  })();
}

function popTo(index) {
  stack = stack.slice(0, index + 1);
  render();
}

function closeAll() {
  stack = [];
  container.classList.remove("open");
  container.replaceChildren();
}

function renderError(message) {
  container.replaceChildren(el("div", { className: "stack-card", style: "--depth:0" }, el("div", { className: "error-banner" }, message)));
}

function render() {
  if (!stack.length) {
    closeAll();
    return;
  }
  const nodes = [el("div", { className: "card-stack-backdrop", onClick: closeAll })];
  stack.forEach((entity, i) => {
    const depth = stack.length - 1 - i;
    nodes.push(buildCard(entity, i, depth));
  });
  container.replaceChildren(...nodes);
}

function buildCard(entity, index, depth) {
  const isTop = depth === 0;
  const card = el("div", { className: "stack-card" + (isTop ? " top" : "") });
  card.style.setProperty("--depth", depth);
  card.style.setProperty("--z", 100 - depth);

  const tab = el(
    "div",
    { className: "stack-card-tab", onClick: isTop ? undefined : () => popTo(index) },
    el("span", { className: "stack-card-eyebrow" }, entity.document_title),
    el("span", { className: "stack-card-name" }, entity.name),
    isTop ? el("button", { className: "stack-card-close", onClick: closeAll, title: "Cerrar" }, icon("x", { size: 15 })) : null,
  );
  card.append(tab);

  if (isTop) {
    const body = el("div", { className: "stack-card-body" });
    body.append(renderPassage(entity.description, openEntity));

    if (entity.relationships?.length) {
      body.append(
        el(
          "div",
          { className: "stack-card-relations" },
          el("h4", {}, "Relacionado"),
          el(
            "div",
            { className: "chip-row" },
            ...entity.relationships.map((rel) =>
              el(
                "button",
                {
                  className: "chip",
                  title: rel.label,
                  onClick: () => openEntity(rel.target_entity_id),
                },
                rel.target_document_id !== entity.document_id
                  ? `${rel.target_entity_name} · ${rel.target_document_title}`
                  : rel.target_entity_name,
              ),
            ),
          ),
        ),
      );
    }

    if (entity.external_references?.length) {
      body.append(
        el(
          "div",
          { className: "stack-card-refs" },
          el("h4", {}, "Referencias externas"),
          ...entity.external_references.map((ref) =>
            el("a", { href: ref.url, target: "_blank", rel: "noopener" }, ref.label),
          ),
        ),
      );
    }
    card.append(body);
  }

  return card;
}
