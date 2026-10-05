# Contactos

Profesores, tutores, secretaría y demás personas relacionadas con el grado, con notas y un
historial de interacciones por persona. Mismo patrón que `agenda/`/`glossary/`: cada
persona y cada interacción es un fichero Markdown independiente, con metadatos en cabecera
(front matter YAML) — ver `backend/app/contacts/store.py`, sin base de datos.

## `people/` — personas

Nombre de fichero: `slug-del-nombre.md`

```markdown
---
name: Jorge Pérez Martín
role: profesor              # texto libre — sugerencias: profesor, tutor, secretaría, alumno, otro
subject: 71031033-logica-y-estructuras-discretas   # opcional, slug de la asignatura
email: jperezmartin@dia.uned.es
phone: "91398-9387"
created: 2026-08-06
---

Notas libres en Markdown (despacho, horario de tutoría, contexto de cómo se conoció...).
```

## `interactions/` — historial de interacciones

Nombre de fichero: `YYYY-MM-DD-persona-slug.md` (mismo patrón que `feed/entries/`)

```markdown
---
person_id: jorge-perez-martin   # stem del fichero de la persona
title: Consulta por email
date: 2026-08-06
channel: email                    # opcional: email, llamada, presencial, foro, otro
---

Detalle libre en Markdown.
```

Borrar una persona (`DELETE /api/contacts/people/{id}`) borra también todas sus
interacciones asociadas.

Se añaden a mano, editando directamente estos ficheros, o desde la web
(`POST /api/contacts/people`, `POST /api/contacts/people/{id}/interactions`, y sus
correspondientes `PATCH`/`DELETE` — el id es el nombre de fichero sin extensión).
