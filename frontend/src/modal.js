/** Modal genérico (backdrop + panel), compartido por calendar.js y
 * contacts.js — un panel de detalle o un formulario a la vez, con Esc para
 * cerrar y un cuerpo actualizable in-place sin recrear el backdrop. */

import { el } from "./dom.js";
import { icon } from "./icons.js";

let modalKeyHandler = null;
let modalBodyEl = null;

export function showModal(title, body, extraActions) {
  closeModal();
  const backdrop = el("div", { className: "modal-backdrop", onClick: (ev) => { if (ev.target === backdrop) closeModal(); } });
  const bodyEl = el("div", { className: "modal-body" }, body);
  modalBodyEl = bodyEl;
  const panel = el(
    "div",
    { className: "modal-panel" },
    el(
      "div",
      { className: "modal-header" },
      el("h3", {}, title),
      el("button", { className: "modal-close", onClick: closeModal }, icon("x", { size: 16 })),
    ),
    bodyEl,
    extraActions?.length ? el("div", { className: "modal-actions" }, ...extraActions) : null,
  );
  backdrop.append(panel);
  document.body.append(backdrop);
  modalKeyHandler = (ev) => { if (ev.key === "Escape") closeModal(); };
  document.addEventListener("keydown", modalKeyHandler);
}

export function isModalOpen() {
  return modalBodyEl !== null;
}

export function updateModalBody(body) {
  modalBodyEl?.replaceChildren(body);
}

export function closeModal() {
  document.querySelector(".modal-backdrop")?.remove();
  if (modalKeyHandler) document.removeEventListener("keydown", modalKeyHandler);
  modalKeyHandler = null;
  modalBodyEl = null;
}
