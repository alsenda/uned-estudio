# Agenda

Calendario y tareas del día a día del curso. Cada evento y cada tarea es un fichero
Markdown independiente, con metadatos en cabecera (front matter YAML) — mismo patrón que
`feed/entries/` (ver `backend/app/agenda/store.py`). Se sirven en la sección "Calendario"
de la web: vista mensual (eventos + tareas con fecha límite) y vista de tareas (todas,
filtrables por hecho/pendiente y asignatura).

## `events/` — exámenes, reuniones, sesiones de estudio...

Nombre de fichero: `YYYY-MM-DD-slug.md`

```markdown
---
title: Examen Fundamentos de Programación
date: 2026-09-15
time: "10:00"          # opcional — sin hora, se trata como todo el día
type: examen            # tutoria | entrega | examen | reunion | estudio | otro
subject: 71031027-fundamentos-algebraicos-para-la-ia   # opcional, carpeta de la asignatura en docs/asignaturas/
links: [https://...]     # opcional, lista de enlaces a recursos relacionados (guía, formulario...)
location: UNED Cádiz, Plaza San Antonio 2 — Aula 1.1   # opcional, se muestra con 📍 y en el aviso
remind: [60, 15]         # opcional, solo con hora: minutos antes para los avisos (ver "Avisos")
---

Descripción libre en Markdown.
```

## `todos/` — tareas con o sin fecha límite

Nombre de fichero: `{due_date o fecha de creación}-slug.md`

```markdown
---
title: Entregar PEC 1
due_date: 2026-09-10    # opcional — sin fecha, solo aparece en la vista de Tareas
done: false
done_at:                 # se rellena solo al marcarla hecha
subject: fundamentos-de-programacion   # opcional
created: 2026-08-04
links: [https://...]     # opcional, lista de enlaces a recursos relacionados
---

Descripción libre en Markdown.
```

## Avisos (notificaciones de Windows)

`scripts/avisos_agenda.py` lee `events/` y `todos/` y lanza notificaciones de Windows; el Programador
de tareas lo ejecuta cada 5 minutos (`./scripts/registrar-avisos-agenda.ps1` crea la tarea
`UNED-AvisosAgenda`; funciona sin el servidor web). Un resumen a las 08:00 con todo lo de hoy y, además:

| Evento | Avisos |
|---|---|
| con hora: `tutoria` | 30 min antes |
| con hora: `reunion`, `estudio`, `otro` | 15 min antes |
| con hora: `entrega` | 1 día y 1 h antes |
| con hora: `examen` | 7 días, 1 día y 1 h antes |
| sin hora: `entrega`, `examen` y tareas con fecha | 08:00 del día anterior (exámenes: también 7 días antes) |

Lo ya enviado se anota en `backend/data/avisos_enviados.json`. Pruebas:
`python scripts/avisos_agenda.py --prueba` (notificación de prueba) y
`python scripts/avisos_agenda.py --simular --ahora=2026-10-06T17:40` (qué avisaría a esa hora).

Se añaden a mano, editando directamente estos ficheros, o desde la web
(`POST /api/agenda/events` / `POST /api/agenda/todos`, y sus correspondientes `PATCH`/
`DELETE` por id — el id es el nombre de fichero sin extensión).
