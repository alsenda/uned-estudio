/** Documentos: árbol navegable de docs/, con PDFs, Markdown y texto plano.
 * Cuando el path abierto coincide con el `source_path` de un documento en
 * estudio-profundo, se muestra un aviso enlazando a su versión anotada +
 * quiz — la única conexión que existe hoy entre "el original" y "el
 * resumen/flashcards que ya hice de él". */

import { uned, study } from "./api.js";
import { el } from "./dom.js";
import { icon } from "./icons.js";
import { parseFrontMatter, renderMarkdown } from "./markdown.js";
import { navigate } from "./router.js";
import { setTopbarContext } from "./main.js";
import { subjectByFolder } from "./plan-semestre.js";

const docsTree = document.getElementById("docs-tree");
const docsViewer = document.getElementById("docs-viewer");
let treeLoaded = false;
let selectedEl = null;
const nodesByPath = new Map();
const dirsByPath = new Map();
let importantDirs = []; // rutas bajo docs/ de las asignaturas del semestre actual ("asignaturas/<carpeta>")
let recentItems = [];
let pinsEl = null;

const RECENT_COUNT = 6;

const isImportant = (path) => importantDirs.some((dir) => path === dir || path.startsWith(`${dir}/`));

function extOf(path) {
  const idx = path.lastIndexOf(".");
  return idx === -1 ? "" : path.slice(idx).toLowerCase();
}

async function ensureTreeLoaded() {
  if (treeLoaded) return;
  treeLoaded = true;
  docsTree.textContent = "Cargando árbol…";
  try {
    const [tree, subjectsRes, recentRes] = await Promise.all([
      uned.getTree(),
      uned.getSubjects().catch(() => []),
      uned.recent(1, 30).catch(() => ({ items: [] })),
    ]);
    const current = subjectsRes.filter((s) => s.current);
    importantDirs = current.map((s) => `asignaturas/${s.folder}`);
    recentItems = recentRes.items ?? [];
    docsTree.replaceChildren();
    nodesByPath.clear();
    dirsByPath.clear();
    pinsEl = el("div", { className: "docs-pins" });
    docsTree.append(pinsEl, renderNode(tree, true));
    renderPins(current);
    markRecent();
  } catch {
    docsTree.textContent = "Error cargando docs/. ¿Está el servidor arrancado?";
  }
}

// Marcas de «importante»: arriba, accesos al primer semestre y a lo último abierto; en el árbol,
// las carpetas del semestre llevan ★ y van las primeras, y lo abierto hace poco lleva un punto.
function renderPins(currentSubjects) {
  if (!pinsEl) return;
  const recent = recentItems.slice(0, RECENT_COUNT);
  pinsEl.replaceChildren(
    el("div", { className: "docs-pins-title" }, "★ Primer semestre"),
    el(
      "div",
      { className: "docs-pins-list" },
      ...currentSubjects.map((s) => {
        const btn = el("button", { className: "docs-pin", type: "button", title: s.name, onClick: () => revealDir(`asignaturas/${s.folder}`) }, s.name);
        const plan = subjectByFolder(s.folder);
        if (plan) btn.style.setProperty("--c", plan.color);
        return btn;
      }),
    ),
    el("div", { className: "docs-pins-title" }, "🕒 Abiertos últimamente"),
    recent.length
      ? el(
          "div",
          { className: "docs-recent-list" },
          ...recent.map((r) =>
            el("a", { className: "docs-recent", href: `#/documentos/${encodeURIComponent(r.path)}`, title: r.path }, r.title || r.path.split("/").pop()),
          ),
        )
      : el("div", { className: "hint" }, "Nada abierto todavía."),
  );
}

function markRecent() {
  const recentPaths = new Set(recentItems.slice(0, RECENT_COUNT).map((r) => r.path));
  for (const [path, node] of nodesByPath) node.classList.toggle("recent", recentPaths.has(path));
}

function revealDir(path) {
  const target = dirsByPath.get(path);
  if (!target) return;
  let parent = target;
  while (parent) {
    if (parent.tagName === "DETAILS") parent.open = true;
    parent = parent.parentElement;
  }
  target.scrollIntoView({ block: "start", behavior: "smooth" });
}

async function refreshRecent() {
  if (!treeLoaded || !pinsEl) return;
  try {
    const [subjects, recent] = await Promise.all([uned.getSubjects().catch(() => []), uned.recent(1, 30)]);
    recentItems = recent.items ?? [];
    renderPins(subjects.filter((s) => s.current));
    markRecent();
  } catch {
    // sin cambios visibles si falla: las marcas anteriores siguen valiendo
  }
}

async function loadStudyIndex() {
  // Sin caché: el motor de estudio puede ganar documentos nuevos mientras la
  // pestaña sigue abierta (se autorían e importan aparte), y la lista es
  // pequeña — más barato repetir la petición que arriesgarse a un índice
  // obsoleto que nunca vuelve a cruzar un documento recién importado.
  try {
    const docs = await study.listDocuments();
    // source_path se autoría incluyendo el prefijo "docs/"; los paths de este
    // árbol son relativos a DOCS_DIR (sin ese prefijo) — se normalizan igual
    // para poder cruzarlos.
    return new Map(docs.filter((d) => d.source_path).map((d) => [d.source_path.replace(/^docs\//, ""), d]));
  } catch {
    return new Map(); // motor no disponible: sin aviso, sin error visible
  }
}

function renderNode(node, open) {
  const important = Boolean(node.path) && isImportant(node.path);
  if (node.type === "dir") {
    const isSubjectDir = importantDirs.includes(node.path);
    const details = el("details", { className: "tree-node tree-dir" + (isSubjectDir ? " important" : "") });
    // Las carpetas de las asignaturas del semestre y la de «asignaturas/» se abren solas
    const isKeyFolder = important && /\/(apuntes|resumenes)$/.test(node.path); // donde están los documentos
    if (open || isSubjectDir || isKeyFolder || node.path === "asignaturas") details.open = true;
    details.append(
      el(
        "summary",
        {},
        icon("folder", { size: 15 }),
        node.name,
        isSubjectDir ? el("span", { className: "tree-star", title: "Asignatura del primer semestre" }, "★") : null,
      ),
    );
    dirsByPath.set(node.path, details);
    // Dentro de «asignaturas/», primero las del semestre actual (después el orden de siempre)
    const children =
      node.path === "asignaturas"
        ? [...node.children].sort((a, b) => Number(isImportant(b.path)) - Number(isImportant(a.path)))
        : node.children;
    children.forEach((child) => details.append(renderNode(child, false)));
    return details;
  }
  const div = el("div", {
    className: "tree-node tree-file" + (node.viewable ? "" : " not-viewable") + (important ? " important" : ""),
    title: node.path,
  }, icon("file-text", { size: 15 }), el("span", {}, node.name));
  if (node.viewable) {
    nodesByPath.set(node.path, div);
    div.addEventListener("click", () => navigate("documentos/" + encodeURIComponent(node.path)));
  }
  return div;
}

function reveal(path) {
  const target = nodesByPath.get(path);
  if (!target) return;
  let parent = target.parentElement;
  while (parent) {
    if (parent.tagName === "DETAILS") parent.open = true;
    parent = parent.parentElement;
  }
  selectedEl?.classList.remove("selected");
  target.classList.add("selected");
  selectedEl = target;
  target.scrollIntoView({ block: "nearest" });
}

async function openPath(path) {
  await ensureTreeLoaded();
  reveal(path);
  setTopbarContext(el("span", {}, path));
  await renderByPath(path, extOf(path));
}

async function renderByPath(path, ext) {
  const [studyIndex] = await Promise.all([
    loadStudyIndex(),
    (async () => {
      if (ext === ".pdf") {
        void uned.logAccess(path, path.split("/").pop());
        docsViewer.replaceChildren(el("iframe", { className: "docs-pdf-frame", src: uned.getFile(path) }));
        return;
      }
      docsViewer.textContent = "Cargando…";
      try {
        const data = await uned.getText(path);
        if (ext === ".md") {
          renderMarkdownInto(data.content, path);
        } else {
          docsViewer.replaceChildren(el("pre", { className: "markdown-body panel" }, data.content));
        }
        void uned.logAccess(path, titleFor(path, data.content, ext));
      } catch {
        docsViewer.textContent = "Error cargando el fichero. Puede que no exista o esté fuera de docs/.";
      }
    })(),
  ]);
  const match = studyIndex.get(path);
  if (match) docsViewer.prepend(studyCrosslink(match));
}

function studyCrosslink(doc) {
  return el(
    "div",
    { className: "study-crosslink" },
    el(
      "div",
      { className: "study-crosslink-text" },
      "Ya tienes un resumen de este documento en ",
      el("strong", {}, "Estudiar a fondo"),
      ": pasajes anotados y flashcards de ",
      el("strong", {}, doc.title),
      ".",
    ),
    el(
      "div",
      { className: "study-crosslink-actions" },
      el("button", { className: "btn-mark", onClick: () => navigate(`estudiar/${doc.id}`) }, "Leer resumen"),
      el("button", { className: "btn-ghost", onClick: () => navigate(`estudiar/${doc.id}/quiz`) }, "Practicar"),
    ),
  );
}

function titleFor(path, content, ext) {
  if (ext === ".md") {
    const { meta } = parseFrontMatter(content);
    if (meta?.title) return meta.title;
    const h1 = content.match(/^#\s+(.*)$/m);
    if (h1) return h1[1];
  }
  return path.split("/").pop();
}

function renderMarkdownInto(raw, currentPath) {
  const { meta, body } = parseFrontMatter(raw);
  const baseDir = currentPath.includes("/") ? currentPath.slice(0, currentPath.lastIndexOf("/")) : "";
  const metaRow = meta
    ? el(
        "div",
        { className: "docs-frontmatter" },
        ...Object.entries(meta)
          .filter(([k]) => k !== "lector" && k !== "lector_etiqueta") // van en el botón, no como etiquetas
          .map(([k, v]) => el("span", { className: "badge" }, `${k}: ${v}`)),
      )
    : null;
  const body_ = el("div", { className: "markdown-body panel", html: renderMarkdown(body, baseDir) });
  const reader = meta?.lector ? readerCard(String(meta.lector), meta.title, meta.lector_etiqueta) : null;
  docsViewer.replaceChildren(...[metaRow, reader, body_].filter(Boolean));
}

// Libros que no se pueden incrustar (Kindle y Scribd envían X-Frame-Options: SAMEORIGIN): la ficha
// .md lleva `lector: <url>` (y, opcional, `lector_etiqueta: <texto del botón>`) en la cabecera y aquí
// se ofrece abrirlo en una ventana junto a la web. Solo se admiten enlaces https.
function readerCard(url, title, label) {
  if (!/^https:\/\//i.test(url)) return null;
  const openWindow = () => {
    const w = Math.min(980, Math.round(window.screen.availWidth * 0.55));
    const features = `popup=yes,width=${w},height=${window.screen.availHeight - 80},left=${window.screen.availWidth - w},top=20`;
    window.open(url, "lector-externo", features);
  };
  return el(
    "div",
    { className: "docs-reader-card" },
    el("div", { className: "docs-reader-text" }, el("strong", {}, `📖 ${title || "Libro"}`), el("span", { className: "hint" }, "Se abre en una ventana a la derecha (necesitas tener la sesión iniciada).")),
    el("div", { className: "docs-reader-actions" },
      el("button", { className: "btn-mark", type: "button", onClick: openWindow }, label || "Abrir el libro en una ventana"),
      el("a", { className: "dash-link-btn", href: url, target: "_blank", rel: "noopener" }, "Abrir en una pestaña ↗")),
  );
}

export function initLibrary() {
  document.addEventListener("activate-section", (ev) => {
    if (ev.detail.section !== "documentos") return;
    void refreshRecent(); // «abiertos últimamente» cambia mientras se estudia
    const [path] = ev.detail.rest;
    if (path) {
      openPath(path);
    } else {
      ensureTreeLoaded();
      docsViewer.replaceChildren(el("p", { className: "hint" }, "Selecciona un documento del árbol de la izquierda."));
    }
  });
}
