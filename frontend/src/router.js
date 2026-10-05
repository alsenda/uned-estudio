/** Hash-based routing: the address bar is the single source of truth for
 * "which section, which document/quiz" — before this, navigation only ever
 * toggled in-memory state, so the URL stayed at a bare "#" and there was no
 * way to bookmark, share, or use back/forward to reach a specific document. */

const listeners = new Set();

export function parseRoute() {
  const raw = location.hash.replace(/^#\/?/, "");
  const parts = raw.split("/").filter(Boolean).map(decodeURIComponent);
  const [section = "inicio", ...rest] = parts;
  return { section, rest };
}

export function navigate(path) {
  const target = "#/" + path.replace(/^\/+/, "");
  if (location.hash === target) {
    dispatch();
  } else {
    location.hash = target;
  }
}

function dispatch() {
  const route = parseRoute();
  for (const fn of listeners) fn(route);
}

export function onRoute(fn) {
  listeners.add(fn);
}

window.addEventListener("hashchange", dispatch);

export function startRouter() {
  dispatch();
}
