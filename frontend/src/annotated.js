/** Shared renderer for any annotated passage (document content or an
 * entity's own description): highlighted spans open another card via
 * `onEntityClick`, and images carry the external-source confirm/discard
 * banner when still pending. Reused recursively by the card stack, which is
 * what gives lookups real depth instead of a single fixed-level modal. */

import { study } from "./api.js";
import { el } from "./dom.js";

export function renderPassage(passage, onEntityClick) {
  const text = passage.text_es;
  const inline = el("div", { className: "annotated-text" });
  let cursor = 0;
  for (const span of passage.spans) {
    if (span.start > cursor) inline.append(text.slice(cursor, span.start));
    inline.append(
      el(
        "mark",
        { className: "highlight", title: span.entity_name, onClick: () => onEntityClick(span.entity_id) },
        text.slice(span.start, span.end),
      ),
    );
    cursor = span.end;
  }
  if (cursor < text.length) inline.append(text.slice(cursor));

  const wrapper = el("div", { className: "passage" });
  if (passage.heading) wrapper.append(el("h3", { className: "passage-heading" }, passage.heading));
  wrapper.append(inline);
  if (passage.images?.length) wrapper.append(el("div", { className: "passage-images" }, ...passage.images.map(imageCard)));
  return wrapper;
}

function imageCard(image) {
  const img = el("img", { src: image.display_url, alt: image.caption || "" });
  const figure = el("figure", { className: "image-card" + (image.pending ? " pending" : "") }, img);
  if (image.caption) figure.append(el("figcaption", {}, image.caption));

  if (image.pending) {
    const status = el("span", { className: "hint" }, "");
    const banner = el(
      "div",
      { className: "pending-banner" },
      "Imagen de fuente externa — sin confirmar",
      el(
        "div",
        { className: "pending-actions" },
        el("button", {
          className: "btn-mark",
          onClick: async () => {
            try {
              await study.confirmImage(image.id);
              figure.classList.remove("pending");
              banner.remove();
            } catch {
              status.textContent = "Error al confirmar.";
            }
          },
        }, "Confirmar"),
        el("button", {
          className: "btn-ghost",
          onClick: async () => {
            try {
              await study.discardImage(image.id);
              figure.remove();
            } catch {
              status.textContent = "Error al descartar.";
            }
          },
        }, "Descartar"),
        status,
      ),
    );
    figure.append(banner);
  }
  return figure;
}
