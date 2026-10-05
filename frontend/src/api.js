/** Typed-in-spirit API clients: `uned` for this app's own backend (same
 * origin), `study` for the estudio-profundo engine (separate service, own
 * port — see estudio-profundo/README.md for why it stays a standalone repo). */

const STUDY_BASE = "http://localhost:8011";

export class ApiError extends Error {
  constructor(status, detail) {
    super(detail);
    this.status = status;
  }
}

async function request(base, path, init) {
  const response = await fetch(`${base}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      if (body && typeof body === "object" && "detail" in body) {
        detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      // non-JSON error body; keep status text
    }
    throw new ApiError(response.status, detail);
  }
  if (response.status === 204) return null;
  return response.json();
}

export const uned = {
  getFeed: (type) => request("", `/api/feed${type ? `?type=${encodeURIComponent(type)}` : ""}`),
  refreshNews: () => request("", "/api/feed/refresh-news", { method: "POST" }),
  // `subject` (carpeta de la asignatura) limita la búsqueda a sus documentos; `topic` orienta al modelo.
  ragQuery: (q, { subject, topic, k } = {}) => {
    const qs = new URLSearchParams({ q });
    if (subject) qs.set("subject", subject);
    if (topic) qs.set("topic", topic);
    if (k) qs.set("k", String(k));
    return request("", `/api/rag/query?${qs}`);
  },
  getSubjects: () => request("", "/api/library/subjects"),
  getTree: () => request("", "/api/library/tree"),
  getFile: (path) => `/api/library/file?path=${encodeURIComponent(path)}`,
  getText: (path) => request("", `/api/library/text?path=${encodeURIComponent(path)}`),
  logAccess: (path, title) =>
    request("", "/api/library/access", { method: "POST", body: JSON.stringify({ path, title }) }).catch(() => {}),
  recent: (page = 1, pageSize = 8) => request("", `/api/library/recent?page=${page}&page_size=${pageSize}`),

  listEvents: (params = {}) => {
    const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v != null && v !== ""));
    const query = qs.toString();
    return request("", `/api/agenda/events${query ? `?${query}` : ""}`);
  },
  createEvent: (body) => request("", "/api/agenda/events", { method: "POST", body: JSON.stringify(body) }),
  updateEvent: (id, body) =>
    request("", `/api/agenda/events/${encodeURIComponent(id)}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteEvent: (id) => request("", `/api/agenda/events/${encodeURIComponent(id)}`, { method: "DELETE" }),

  listTodos: (params = {}) => {
    const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v != null && v !== ""));
    const query = qs.toString();
    return request("", `/api/agenda/todos${query ? `?${query}` : ""}`);
  },
  createTodo: (body) => request("", "/api/agenda/todos", { method: "POST", body: JSON.stringify(body) }),
  updateTodo: (id, body) =>
    request("", `/api/agenda/todos/${encodeURIComponent(id)}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteTodo: (id) => request("", `/api/agenda/todos/${encodeURIComponent(id)}`, { method: "DELETE" }),

  listTerms: (params = {}) => {
    const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v != null && v !== ""));
    const query = qs.toString();
    return request("", `/api/glossary/terms${query ? `?${query}` : ""}`);
  },
  createTerm: (body) => request("", "/api/glossary/terms", { method: "POST", body: JSON.stringify(body) }),
  updateTerm: (id, body) =>
    request("", `/api/glossary/terms/${encodeURIComponent(id)}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteTerm: (id) => request("", `/api/glossary/terms/${encodeURIComponent(id)}`, { method: "DELETE" }),
  listTags: () => request("", "/api/glossary/tags"),

  listPeople: (params = {}) => {
    const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v != null && v !== ""));
    const query = qs.toString();
    return request("", `/api/contacts/people${query ? `?${query}` : ""}`);
  },
  createPerson: (body) => request("", "/api/contacts/people", { method: "POST", body: JSON.stringify(body) }),
  updatePerson: (id, body) =>
    request("", `/api/contacts/people/${encodeURIComponent(id)}`, { method: "PATCH", body: JSON.stringify(body) }),
  deletePerson: (id) => request("", `/api/contacts/people/${encodeURIComponent(id)}`, { method: "DELETE" }),
  listInteractions: (personId) =>
    request("", `/api/contacts/people/${encodeURIComponent(personId)}/interactions`),
  createInteraction: (personId, body) =>
    request("", `/api/contacts/people/${encodeURIComponent(personId)}/interactions`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  deleteInteraction: (id) => request("", `/api/contacts/interactions/${encodeURIComponent(id)}`, { method: "DELETE" }),
};

export const study = {
  available: async () => {
    try {
      await request(STUDY_BASE, "/api/health");
      return true;
    } catch {
      return false;
    }
  },
  listDocuments: () => request(STUDY_BASE, "/api/documents"),
  listSets: () => request(STUDY_BASE, "/api/sets"),
  listSetQuestions: (setId) => request(STUDY_BASE, `/api/sets/${encodeURIComponent(setId)}/questions`),
  getDocument: (id) => request(STUDY_BASE, `/api/documents/${encodeURIComponent(id)}`),
  deleteDocument: (id) => request(STUDY_BASE, `/api/documents/${encodeURIComponent(id)}`, { method: "DELETE" }),
  getEntity: (id) => request(STUDY_BASE, `/api/entities/${encodeURIComponent(id)}`),
  confirmImage: (id) => request(STUDY_BASE, `/api/images/${encodeURIComponent(id)}/confirm`, { method: "POST" }),
  discardImage: (id) => request(STUDY_BASE, `/api/images/${encodeURIComponent(id)}/discard`, { method: "POST" }),
  imageFile: (id) => `${STUDY_BASE}/api/images/${encodeURIComponent(id)}/file`,
  listInconsistencies: (documentId, status) =>
    request(
      STUDY_BASE,
      `/api/documents/${encodeURIComponent(documentId)}/inconsistencies${status ? `?status=${status}` : ""}`,
    ),
  resolveInconsistency: (id, resolution, note) =>
    request(STUDY_BASE, `/api/inconsistencies/${id}/resolve`, {
      method: "POST",
      body: JSON.stringify({ resolution, note }),
    }),
  startSession: (body) => request(STUDY_BASE, "/api/quiz/start", { method: "POST", body: JSON.stringify(body) }),
  submitAnswer: (body) => request(STUDY_BASE, "/api/quiz/answer", { method: "POST", body: JSON.stringify(body) }),
  finishSession: (id) => request(STUDY_BASE, `/api/quiz/${id}/finish`, { method: "POST" }),
  logAccess: (itemType, itemId) =>
    request(STUDY_BASE, "/api/access", {
      method: "POST",
      body: JSON.stringify({ item_type: itemType, item_id: itemId }),
    }).catch(() => {}),
  recentAccess: (page = 1, pageSize = 8) => request(STUDY_BASE, `/api/access/recent?page=${page}&page_size=${pageSize}`),
  dueReview: (limit = 20, track) =>
    request(STUDY_BASE, `/api/review/due?limit=${limit}${track ? `&track=${encodeURIComponent(track)}` : ""}`),
  engagementSummary: () => request(STUDY_BASE, "/api/engagement/summary"),
  setDailyGoal: (value) =>
    request(STUDY_BASE, "/api/engagement/daily-goal", { method: "PUT", body: JSON.stringify({ value }) }),
};
