# Estudio a fondo

Motor genérico y reutilizable para estudiar documentación en profundidad: recrea cada
documento en una versión legible en español con ideas/entidades resaltadas, un modal
anidado real (sin límite de profundidad fijo, a diferencia de apps de referencia como
footnoted) al hacer clic en un resaltado, y un quiz + flashcards asociado con progreso
persistente.

No contiene nada específico de ningún proyecto: apunta a cualquier carpeta de
`content/<slug>/{document,quiz}.json` vía `CONTENT_DIR`. El repo `UNED` es quien lo usa,
apuntándolo a su propia documentación — este repo es el motor, no el contenido.

## Estructura

```
estudio-profundo/
├── backend/           FastAPI + SQLAlchemy + SQLite, puerto 8011
│   └── app/
│       ├── models.py       Quiz (vendorizado de quiz-app) + lector anotado
│       ├── schemas.py      Contratos de importación: QuestionSetFile, DocumentFile
│       ├── routers/        documents, entities, images, access, sets, quiz, results
│       └── services/       grading/question_sets/stats (vendorizados) + content_import
├── content/            <slug>/document.json + quiz.json — el contenido autoría, versionado
└── frontend/            Vite + TS, sin framework (flip-cards de quiz-app + lector nuevo)
```

## Puesta en marcha

```powershell
./scripts/run.ps1
```

Arranca el backend en `http://localhost:8011` y el frontend (Vite) en
`http://localhost:5174`. Requiere Python 3.11+ y Node.

Para cargar contenido tras añadir `content/<slug>/document.json` y/o `quiz.json`:

```powershell
cd backend
./.venv/Scripts/python.exe scripts/seed.py            # todo el contenido
./.venv/Scripts/python.exe scripts/seed.py --validate  # solo validar
```

## Cómo se genera el contenido

`document.json` y `quiz.json` los genera Claude de forma interactiva, documento a
documento, consultando el RAG del proyecto de contenido (en el caso de UNED,
`backend/app/rag/query.py`) para enriquecer descripciones de entidades y preguntas con
relaciones entre documentos. Ver los schemas `DocumentFile`/`QuestionSetFile` en
`backend/app/schemas.py` para el contrato exacto. No hay pipeline automatizado con un
modelo local — ver la discusión en el historial del proyecto UNED sobre por qué (modelos
pequeños no son fiables generando grafos de entidades ni preguntas con sentido sin
supervisión).

## Enlace de cada pregunta al texto («Ver en el texto»)

Cada pregunta de `quiz.json` puede llevar un campo opcional `source` que dice en qué parte del
documento anotado se apoya. En la web aparece como un enlace «Ver en el texto» (en la lista de
preguntas y en el reverso de cada tarjeta) que abre «Leer» desplazado a ese pasaje y con la ficha de
la idea ya abierta:

```json
"source": { "passage_id": "p-funciones", "entity_id": "inyectiva" }
```

- `passage_id` y `entity_id` son los ids **cortos** de `document.json` (sin `documento::`).
  `entity_id` es opcional. `document_id` también, y por defecto es el del propio conjunto de preguntas.
- `scripts/seed.py` lo valida: falla si el pasaje o la idea no existen en el documento.
- Convención al crear preguntas: toda respuesta debe poder comprobarse en «Leer» (pasajes o fichas).
  Si una pregunta necesita un dato que no está en el libro, añádelo a la ficha marcado como
  «Complemento (no está en el libro)».

## Densidad de contenido (repetición espaciada)

Desde que existe repaso espaciado real (`CardState`/FSRS, ver `services/scheduling.py`),
la densidad de `quiz.json` importa: un documento con solo un puñado de preguntas para
decenas de entidades no da material suficiente para que el repaso espaciado tenga sentido
a largo plazo. Convención para autoría **a partir de ahora** (no aplica en retroactivo a
los documentos ya existentes, que se quedan como están):

- Cada `Entity` identificada en `document.json` debe producir **1 a 3** preguntas o
  flashcards propias en `quiz.json` — la extracción de entidades del lector ya es, en la
  práctica, la lista de qué merece memorizarse.
- Además, una pregunta de tipo `mc` por cada idea marcada `typicality: staple` que no
  tenga ya cobertura vía lo anterior.

Como referencia de orden de magnitud: un documento con 25-30 entidades debería producir
más cerca de 40-80 preguntas que de las ~13 que tenían los primeros documentos autoriados
antes de esta convención.

## Imágenes

- Extraídas del PDF de origen: se colocan en `content/<slug>/images/` y se referencian en
  `document.json` con `"source": "document"` — no requieren confirmación.
- De internet: se registran con `"source": "external_pending"` y una `url`, sin descargar
  nada. El frontend las previsualiza por hotlink dentro de un aviso de confirmación; solo
  tras confirmar (`POST /api/images/{id}/confirm`) se descargan y persisten. Si se
  descartan (`POST /api/images/{id}/discard`), se borra el registro sin haber descargado
  nada.

## Incoherencias intradocumentales

Al autoría un documento, cada entidad debe quedar enlazada con todas sus menciones dentro
del texto (no solo el primer resaltado) — al escribir `document.json` reviso todas las
menciones de cada entidad entre sí y, si dos partes del documento se contradicen (p. ej.
dos valores distintos para el mismo umbral), lo declaro como una entrada en
`inconsistencies` (ver `InconsistencyFile` en `schemas.py`): a qué entidad afecta, un
resumen del conflicto, y las dos citas textuales enfrentadas con su ubicación.

El lector muestra un panel de avisos con las incoherencias abiertas de cada documento.
Para cada una, el usuario puede resolverla:
- **Es correcto A / Es correcto B** — zanja el conflicto a favor de una de las dos citas.
- **Que lo resuelva la IA** — requiere una nota explicando el porqué (pensado para que yo
  revise el documento, corrija el contenido real, y esta incoherencia deje de aparecer en
  el siguiente reimport).
- **No es una incoherencia real** — la descarta.

`GET /api/documents/{id}/inconsistencies?status=open` lista las pendientes;
`POST /api/inconsistencies/{id}/resolve` aplica una resolución.

## Borrar un documento por completo

Si un documento resulta estar basado en fuentes poco fiables o en una hipótesis errónea,
`DELETE /api/documents/{id}` (o el botón "Eliminar documento" del dashboard, con
confirmación en línea) lo borra por completo: todo su contenido del lector, su quiz y
*todo* el historial de respuestas asociado, sus imágenes, sus incoherencias, y la carpeta
`content/<slug>/` en disco — no es una edición, es que el documento deja de existir.
