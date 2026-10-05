import re
import sys

import ollama

from ..config import LLM_MODEL, OLLAMA_HOST
from .store import get_collection

_client = ollama.Client(host=OLLAMA_HOST)

SYSTEM_PROMPT = (
    "Eres un asistente que responde preguntas de estudio usando ÚNICAMENTE el contexto "
    "proporcionado, extraído de los apuntes del usuario. Si el contexto no contiene la "
    "respuesta, dilo claramente en vez de inventar. Responde SIEMPRE y SOLO en español "
    "(nunca en chino ni en inglés), de forma clara y concisa, y cita las fuentes entre "
    "corchetes, p. ej. [asignatura/apuntes/tema1.pdf]. No uses LaTeX: escribe las fórmulas "
    "y los conjuntos en texto plano con símbolos Unicode (∈, ⊂, ∅, {a, b})."
)
_CJK = re.compile(r"[぀-ヿ㐀-鿿가-힯]")

# Palabras de pregunta o muy generales que no sirven como pista léxica
_STOP = {
    "cuáles", "cuales", "cuántos", "cuantos", "cuántas", "cuantas", "significa", "según", "segun", "libro",
    "explica", "explicar", "define", "definir", "definición", "definicion", "diferencia", "entre", "sobre",
    "donde", "dónde", "porque", "cómo", "como", "tiene", "tienen", "puede", "pueden", "hacer", "cuando",
    "cuándo", "estas", "estos", "ejemplo", "ejemplos", "algún", "alguna", "asignatura", "tema", "temas",
}
_LEXICAL_MAX_MATCHES = 25  # una palabra en más fragmentos que esto no discrimina


_FUNCTION_WORDS = {"que", "qué", "los", "las", "del", "con", "por", "una", "uno", "unos", "unas", "para", "más",
                   "mas", "son", "ser", "hay", "sus", "cual", "cuál", "esa", "ese", "eso", "ella", "este"}


def _keywords(question: str) -> list[str]:
    """Pistas léxicas de la pregunta: pares de palabras consecutivas («conjunto potencia») y
    palabras sueltas de 5+ letras. Los pares son mucho más específicos que una palabra sola."""
    tokens = re.findall(r"[^\W\d_]{3,}", question.lower())
    seen, terms = set(), []

    def add(term: str) -> None:
        if term not in seen:
            seen.add(term)
            terms.append(term)

    for a, b in zip(tokens, tokens[1:]):
        if not ({a, b} & (_STOP | _FUNCTION_WORDS)):
            add(f"{a} {b}")
    for w in tokens:
        if len(w) >= 5 and w not in _STOP and w not in _FUNCTION_WORDS:
            add(w)
    return terms


def _lexical_hits(collection, question: str, subject: str | None, per_term: int = 2, max_terms: int = 3) -> list[dict]:
    """Fragmentos que contienen literalmente las palabras más raras de la pregunta. La búsqueda
    semántica sola puede no subir un fragmento que explica un término concreto (p. ej. «conjunto
    potencia») si lo tapan otros del mismo tema; esto lo rescata."""
    candidates = []
    for word in _keywords(question):
        clause = {"$or": [{"$contains": word}, {"$contains": word.capitalize()}]}
        where = {"subject": subject} if subject else None
        found = collection.get(where=where, where_document=clause, limit=_LEXICAL_MAX_MATCHES + 1, include=[])
        n = len(found["ids"])
        if 0 < n <= _LEXICAL_MAX_MATCHES:
            candidates.append((n, clause))
    candidates.sort(key=lambda c: c[0])  # primero las palabras más raras
    hits = []
    for n, clause in candidates[:max_terms]:
        kwargs = {"query_texts": [question], "n_results": min(per_term, n), "where_document": clause}
        if subject:
            kwargs["where"] = {"subject": subject}
        res = collection.query(**kwargs)
        for cid, doc, meta, dist in zip(res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]):
            hits.append({"id": cid, "text": doc, "source": meta.get("source"), "subject": meta.get("subject"), "distance": dist})
    return hits


def retrieve(question: str, k: int = 5, subject: str | None = None) -> list[dict]:
    """Top-k fragmentos, híbrido: los que contienen las palabras raras de la pregunta primero y
    el resto por similitud semántica. Con `subject` (carpeta bajo docs/asignaturas/) solo busca
    en los documentos de esa asignatura, para no mezclar materias."""
    collection = get_collection()
    if collection.count() == 0:
        return []
    kwargs = {"query_texts": [question], "n_results": min(k, collection.count())}
    if subject:
        kwargs["where"] = {"subject": subject}
    results = collection.query(**kwargs)
    dense = [
        {"id": cid, "text": doc, "source": meta.get("source"), "subject": meta.get("subject"), "distance": dist}
        for cid, doc, meta, dist in zip(results["ids"][0], results["documents"][0], results["metadatas"][0], results["distances"][0])
    ]
    merged, seen = [], set()
    for hit in _lexical_hits(collection, question, subject) + dense:
        if hit["id"] in seen:
            continue
        seen.add(hit["id"])
        merged.append(hit)
    return merged[:k]


def _unique_sources(hits: list[dict]) -> list[dict]:
    """Una entrada por documento (con un fragmento de muestra), en orden de relevancia."""
    seen, sources = set(), []
    for h in hits:
        if h["source"] in seen:
            continue
        seen.add(h["source"])
        sources.append({"source": h["source"], "subject": h["subject"], "snippet": " ".join(h["text"].split())[:200]})
    return sources


def answer(question: str, k: int = 5, subject: str | None = None, topic: str | None = None) -> dict:
    """Responde con el LLM local usando SOLO los fragmentos recuperados. `topic` (un tema del
    temario) solo se le indica al modelo: usarlo como prefijo de búsqueda empeoraba la recuperación."""
    hits = retrieve(question, k=k, subject=subject)
    if not hits:
        where = "esta asignatura" if subject else "los documentos"
        return {
            "answer": f"No hay documentación indexada de {where} todavía. Añade ficheros a docs/ y ejecuta la ingesta.",
            "sources": [],
        }

    context = "\n\n---\n\n".join(f"[{h['source']}]\n{h['text']}" for h in hits)
    focus = f"Tema del temario: {topic}\n\n" if topic else ""
    prompt = f"Contexto:\n\n{context}\n\n{focus}Pregunta: {question}"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    options = {"temperature": 0.2}
    text = _client.chat(model=LLM_MODEL, messages=messages, options=options)["message"]["content"]
    if _CJK.search(text):  # qwen a veces se pasa al chino: se reintenta una vez, avisándole
        messages.append({"role": "assistant", "content": text})
        messages.append({"role": "user", "content": "Repite la respuesta completa SOLO en español."})
        text = _client.chat(model=LLM_MODEL, messages=messages, options=options)["message"]["content"]
        text = _CJK.sub("", text)  # último recurso: sin caracteres CJK sueltos
    return {
        "answer": text,
        "sources": _unique_sources(hits),
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python -m backend.app.rag.query \"pregunta\"")
        sys.exit(1)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    result = answer(" ".join(sys.argv[1:]))
    print(result["answer"])
    if result["sources"]:
        print("\nFuentes:")
        for s in result["sources"]:
            print(f"  - {s['source']}")
