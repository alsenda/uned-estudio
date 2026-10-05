/** Minimal Markdown renderer (headers, lists, tables, code, links, front
 * matter) — no dependency, matching this project's "no build step, no
 * external CDN" rule. Internal relative links become real `#/documentos/...`
 * anchors, so they're plain hash-routed links (bookmarkable, openable in a
 * new tab) rather than JS-intercepted "#" placeholders. */

import { escapeHtml } from "./dom.js";

export function parseFrontMatter(text) {
  if (!text.startsWith("---")) return { meta: null, body: text };
  const end = text.indexOf("\n---", 3);
  if (end === -1) return { meta: null, body: text };
  const raw = text.slice(3, end).trim();
  const body = text.slice(end + 4).replace(/^\r?\n/, "");
  const meta = {};
  raw.split("\n").forEach((line) => {
    const m = line.match(/^(\w+):\s*(.*)$/);
    if (m) meta[m[1]] = m[2].trim();
  });
  return { meta, body };
}

export function resolveRelativePath(baseDir, link) {
  const clean = link.split("#")[0].split("?")[0];
  const segments = (baseDir ? baseDir.split("/") : []).concat(clean.split("/"));
  const stack = [];
  for (const seg of segments) {
    if (seg === "" || seg === ".") continue;
    if (seg === "..") stack.pop();
    else stack.push(seg);
  }
  return stack.join("/");
}

function inlineMarkdown(text, baseDir) {
  let out = escapeHtml(text);
  out = out.replace(/`([^`]+)`/g, "<code>$1</code>");
  out = out.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  out = out.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, "<em>$1</em>");
  out = out.replace(
    /(?<!\]\()(https?:\/\/[^\s<>()]+)/g,
    (m) => `<a href="${m}" target="_blank" rel="noopener">${m}</a>`,
  );
  out = out.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, label, url) => {
    if (/^(https?:|mailto:)/i.test(url)) {
      return `<a href="${url}" target="_blank" rel="noopener">${label}</a>`;
    }
    const resolved = resolveRelativePath(baseDir || "", url);
    return `<a href="#/documentos/${encodeURIComponent(resolved)}">${label}</a>`;
  });
  return out;
}

export function renderMarkdown(md, baseDir) {
  const codeBlocks = [];
  md = md.replace(/```[a-zA-Z0-9]*\n([\s\S]*?)```/g, (_, code) => {
    const idx = codeBlocks.length;
    codeBlocks.push(`<pre><code>${escapeHtml(code)}</code></pre>`);
    return `\n@@CODEBLOCK${idx}@@\n`;
  });

  const lines = md.split("\n");
  const html = [];
  let paragraph = [];
  let listBuffer = [];
  let listType = null;
  let tableBuffer = [];

  const flushParagraph = () => {
    if (paragraph.length) {
      html.push(`<p>${inlineMarkdown(paragraph.join(" "), baseDir)}</p>`);
      paragraph = [];
    }
  };
  const flushList = () => {
    if (listBuffer.length) {
      const tag = listType === "ol" ? "ol" : "ul";
      html.push(`<${tag}>${listBuffer.map((li) => `<li>${inlineMarkdown(li, baseDir)}</li>`).join("")}</${tag}>`);
      listBuffer = [];
      listType = null;
    }
  };
  const flushTable = () => {
    if (tableBuffer.length >= 2) {
      const header = tableBuffer[0].split("|").map((c) => c.trim()).filter((c) => c !== "");
      const rows = tableBuffer.slice(2).map((r) => r.split("|").map((c) => c.trim()).filter((c) => c !== ""));
      html.push(
        "<table><thead><tr>" +
          header.map((h) => `<th>${inlineMarkdown(h, baseDir)}</th>`).join("") +
          "</tr></thead><tbody>" +
          rows.map((r) => "<tr>" + r.map((c) => `<td>${inlineMarkdown(c, baseDir)}</td>`).join("") + "</tr>").join("") +
          "</tbody></table>",
      );
    }
    tableBuffer = [];
  };

  for (const line of lines) {
    const codeToken = line.trim().match(/^@@CODEBLOCK(\d+)@@$/);
    if (codeToken) {
      flushParagraph();
      flushList();
      flushTable();
      html.push(codeBlocks[Number(codeToken[1])]);
      continue;
    }

    const headerMatch = line.match(/^(#{1,4})\s+(.*)$/);
    if (headerMatch) {
      flushParagraph();
      flushList();
      flushTable();
      const level = headerMatch[1].length;
      html.push(`<h${level}>${inlineMarkdown(headerMatch[2], baseDir)}</h${level}>`);
      continue;
    }

    if (/^\s*\|.*\|\s*$/.test(line)) {
      flushParagraph();
      flushList();
      tableBuffer.push(line.trim());
      continue;
    } else if (tableBuffer.length) {
      flushTable();
    }

    if (line.trim() === "") {
      flushParagraph();
      flushList();
      continue;
    }

    const ulMatch = line.match(/^[-*]\s+(.*)$/);
    const olMatch = line.match(/^\d+\.\s+(.*)$/);
    if (ulMatch || olMatch) {
      flushParagraph();
      const type = ulMatch ? "ul" : "ol";
      if (listType && listType !== type) flushList();
      listType = type;
      listBuffer.push(ulMatch ? ulMatch[1] : olMatch[1]);
      continue;
    }

    if (listBuffer.length) {
      listBuffer[listBuffer.length - 1] += " " + line.trim();
      continue;
    }

    paragraph.push(line.trim());
  }
  flushParagraph();
  flushList();
  flushTable();

  return html.join("\n");
}
