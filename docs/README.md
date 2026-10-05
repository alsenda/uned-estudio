# Documentación

Toda la documentación de estudio vive aquí. Es la fuente que se indexa en el sistema RAG
(`backend/app/rag/ingest.py` la recorre recursivamente), así que cuanto más consistente sea
la organización, mejor calidad de recuperación.

## Convención por asignatura

Cada asignatura tiene su propia carpeta bajo `docs/asignaturas/`, con el nombre:

```
<codigo-asignatura>-<nombre-en-slug>/
```

Ejemplo: `65023102-fundamentos-de-programacion/`.

Dentro, la misma subestructura siempre (ver plantilla en `docs/asignaturas/_plantilla/`):

```
<asignatura>/
├── README.md      # Nombre completo, curso, créditos, enlaces (guía docente, campus...)
├── apuntes/        # Material original: PDFs, transcripciones, diapositivas
├── resumenes/       # Resúmenes propios en Markdown
├── ejercicios/       # Ejercicios y prácticas resueltas
└── examenes/          # Exámenes de convocatorias anteriores
```

Para dar de alta una asignatura nueva, copia la carpeta `_plantilla/` y renómbrala.

Formatos soportados por la ingesta: `.md`, `.txt`, `.pdf`. Si en el futuro hace falta otro
formato (p. ej. `.docx`), se añade soporte en `backend/app/rag/ingest.py` cuando surja la
necesidad, no antes.

## `general/`

Documentación transversal que no pertenece a una asignatura concreta: normativa UNED, guías
de matrícula, plantillas de TFG, etc.
