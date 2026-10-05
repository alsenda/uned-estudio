/** Tiny DOM helper — builds elements without innerHTML, so text content is
 * always safe, and lets components stay declarative without a framework. */

export function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value === undefined || value === null || value === false) continue;
    if (key === "className") node.className = value;
    else if (key === "onClick") node.addEventListener("click", value);
    else if (key === "onInput") node.addEventListener("input", value);
    else if (key === "onSubmit") node.addEventListener("submit", value);
    else if (key === "html") node.innerHTML = value;
    else if (key in node) node[key] = value;
    else node.setAttribute(key, value);
  }
  for (const child of children.flat()) {
    if (child === undefined || child === null || child === false || child === "") continue;
    node.append(child instanceof Node ? child : document.createTextNode(child));
  }
  return node;
}

export function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

export function clear(node) {
  node.replaceChildren();
}
