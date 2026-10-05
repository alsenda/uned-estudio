# Glosario

Términos y definiciones filtrables por asignatura y por tag, accesibles desde la sección
"Glosario" de la web. Cada término es un fichero Markdown independiente en `terms/`, con
metadatos en cabecera (front matter YAML) — mismo patrón que `feed/entries/` y `agenda/`
(ver `backend/app/glossary/store.py`), sin base de datos.

## Formato

Nombre de fichero: `slug-del-termino.md`

```markdown
---
term: ECTS
subject: fundamentos-de-programacion   # opcional, slug de la asignatura
tags: [normativa, grado-ia]             # opcional
---

Definición libre en Markdown.
```

Se añaden a mano, editando directamente estos ficheros, o desde la web
(`POST /api/glossary/terms`, y sus correspondientes `PATCH`/`DELETE` por id — el id es el
nombre de fichero sin extensión).
