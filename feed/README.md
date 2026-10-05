# Feed

Cada entrada del feed es un fichero Markdown independiente en `feed/entries/`, con
metadatos en cabecera (front matter YAML). El backend (`backend/app/feed/store.py`) los
lee todos y los sirve ordenados por fecha descendente.

## Formato

Nombre de fichero: `YYYY-MM-DD-slug.md`

```markdown
---
title: Título de la entrada
date: 2026-08-02
type: diario          # diario | noticia
subject: fundamentos-de-programacion   # opcional, slug de la asignatura relacionada
tags: [recursividad, listas]           # opcional
source_url: https://...                # opcional, solo tiene sentido en noticias
---

Contenido de la entrada en Markdown libre.
```

## Diario de aprendizaje

Entradas tipo `diario`: qué se ha estudiado, conceptos clave, dudas resueltas, enlaces a
los resúmenes en `docs/`. Se añaden a mano o pidiéndomelo a mí (Claude) mientras trabajamos
sobre la documentación — las escribo directamente como fichero nuevo aquí, o vía
`POST /api/feed/entries`.

## Noticias

Entradas tipo `noticia`: se generan automáticamente al refrescar los feeds RSS
configurados en `backend/app/feed/sources.yaml` (`POST /api/feed/refresh-news`). Añade ahí
las fuentes RSS relacionadas con tus asignaturas cuando las identifiques — el fichero
empieza vacío a propósito.
