# Estudio UNED — Grado en Ingeniería en IA

Una web que se abre en tu ordenador con **todo el material del grado en un solo sitio**:

- 📚 **Documentos**: guías docentes, apuntes y resúmenes de las asignaturas.
- 🔎 **Buscar con IA**: escribes una pregunta («¿qué es una función inyectiva?») y te responde
  usando solo los documentos, diciéndote de qué fichero lo ha sacado.
- 🧠 **Estudiar y repasar**: documentos anotados con ideas clave, preguntas tipo test, tarjetas
  (flashcards) y **repaso espaciado**: la web te recuerda qué repasar cada día justo antes de que lo olvides.
- 📅 **Calendario** del curso (tutorías, pruebas presenciales, plazos), **glosario** y **contactos** del profesorado.

**Es gratis, funciona sin internet una vez instalado y tus datos no salen de tu ordenador**
(la IA corre en tu propio PC, no se envía nada a ninguna nube).

🎬 **Míralo en acción** (2 min): [media/demo.mp4](media/demo.mp4) — pulsa «Download» o «View raw» para verlo.

---

## Qué necesita tu ordenador

Windows 10/11, unos **10 GB libres en disco**, conexión a internet **solo para la instalación**, y
**8 GB de RAM o más** para el buscador con IA (con menos, usa `--sin-ia`, ver más abajo). Sin tarjeta
gráfica potente las respuestas tardan entre 20 segundos y un par de minutos: es normal.

## Instalación paso a paso (solo se hace una vez)

> Está explicado para **Windows**. Si usas Mac o Linux, mira el apartado [Mac y Linux](#mac-y-linux).
> No hace falta saber programar: solo hacer clic y esperar.

### Paso 1 · Instala Python

1. Entra en <https://www.python.org/downloads/release/python-3128/>, baja hasta el apartado **Files**
   y descarga **Windows installer (64-bit)**. (Usa esta versión, la 3.12: es con la que se ha probado todo.)
2. Abre el fichero descargado.
3. ⚠️ **MUY IMPORTANTE**: en la primera pantalla, marca la casilla de abajo que dice
   **«Add python.exe to PATH»** y después pulsa **Install Now**.
4. Cuando termine, pulsa **Close**.

### Paso 2 · Instala Ollama (la IA)

1. Entra en <https://ollama.com/download> y descarga la versión para Windows.
2. Ábrelo y pulsa **Install**. Cuando termine puede abrirse una ventana de Ollama: la puedes cerrar.

### Paso 3 · Descarga este proyecto

1. En esta misma página de GitHub, pulsa el botón verde **`<> Code`** y luego **Download ZIP**.
2. Ve a tu carpeta de Descargas, haz clic derecho sobre el ZIP → **Extraer todo…** → **Extraer**.
3. Mueve la carpeta resultante donde quieras (por ejemplo, a *Documentos*) y **no la borres**: ahí
   viven tus datos de estudio.

### Paso 4 · Ábrelo

1. Entra en la carpeta y haz **doble clic en `Iniciar.bat`**.
2. Si Windows muestra «Windows protegió su PC», pulsa **Más información → Ejecutar de todas formas**
   (es normal con cualquier programa que no viene de una tienda).
3. Se abrirá una ventana negra con texto. **La primera vez tarda bastante (de 10 a 30 minutos)**
   porque descarga la IA (unos 5 GB) y lee todos los documentos. Déjala trabajando.
   Verás mensajes como `Descargando modelos de IA…` y `Indexando los documentos…`.
4. Cuando ponga **`✔ Todo listo: http://localhost:8000`**, se abrirá sola la web en tu navegador.

🎉 ¡Ya está! Si no se abre sola, escribe `http://localhost:8000` en la barra de direcciones de tu navegador.

---

## Uso diario

1. Doble clic en **`Iniciar.bat`** (las siguientes veces tarda solo unos segundos).
2. Estudia en el navegador: <http://localhost:8000>
3. **No cierres la ventana negra mientras estudies.** Cuando termines, ciérrala y se apaga todo.

### Qué hay en cada sección (menú de la izquierda)

| Sección | Para qué sirve |
|---|---|
| **Inicio** | Resumen de tu semestre, qué toca esta semana y cuántas tarjetas tienes pendientes de repaso hoy. |
| **Documentos** | Navega por las carpetas de cada asignatura y abre PDFs, resúmenes y apuntes. |
| **Buscar** | Haz preguntas en lenguaje normal. Puedes limitar la búsqueda a una asignatura. |
| **Estudiar** | Elige asignatura → ves su temario, abres los documentos anotados (pulsa en las palabras resaltadas para ver su explicación) y haces el quiz y las tarjetas. |
| **Calendario** | Tutorías, pruebas presenciales y plazos del curso. Puedes añadir tus propios eventos y tareas. |
| **Glosario** | Definiciones de términos, que también puedes ampliar. |
| **Contactos** | Profesorado y negociados, con sus correos. |

### Cómo funciona el repaso espaciado

En **Estudiar** abre un documento y entra en su **repaso**. Te irá enseñando tarjetas: tú dices si la
sabías o no, y la web programa cuándo volver a enseñártela (las que fallas vuelven pronto, las que
dominas tardan semanas). En **Inicio** verás cuántas tienes pendientes hoy. Tu progreso se guarda
en tu ordenador.

---

## Añadir tus propios documentos

1. Copia tus ficheros (`.pdf`, `.md` o `.txt`) dentro de la carpeta de la asignatura:
   `docs/asignaturas/<asignatura>/apuntes/` (o `resumenes/`, `ejercicios/`, `examenes/`).
2. Cierra la ventana negra y vuelve a abrir **`Iniciar.bat`**. Al arrancar, los documentos nuevos se
   incorporan solos al buscador.

Más detalle sobre cómo organizar las carpetas en [docs/README.md](docs/README.md).

## Actualizar a una versión nueva

Si alguien publica mejoras o más documentos: descarga de nuevo el ZIP (Paso 3) y **copia encima** de tu
carpeta actual. Tus tareas, contactos y progreso de estudio **no se pierden** mientras no los borres a mano
(viven en `agenda/todos/`, `contacts/interactions/` y `estudio-profundo/backend/estudio.db`).

---

## Cambiar la IA que usa el buscador (opcional)

**Si tu ordenador es normal, no hace falta que toques nada**: todo viene ya preparado y probado con
los modelos que usamos nosotros. Lee esto solo si el buscador va muy lento, si tu PC es muy potente o si
quieres probar otra IA.

### Qué es cada cosa

El buscador con IA usa **dos «cerebros»** que se ejecutan dentro de **Ollama** (el programa del Paso 2):

| Pieza | Para qué sirve (con una analogía) | Qué usamos nosotros | Tamaño |
|---|---|---|---|
| **Modelo de búsqueda** (`UNED_EMBED_MODEL`) | El *bibliotecario*: lee todos tus documentos y los ordena por significado, para encontrar los párrafos que tratan de lo que preguntas. | `nomic-embed-text` | ~270 MB |
| **Modelo de respuesta** (`UNED_LLM_MODEL`) | El *redactor*: lee esos párrafos y te escribe la respuesta en español citando las fuentes. | `qwen2.5:7b-instruct` | ~4,7 GB |
| **Dirección de Ollama** (`OLLAMA_HOST`) | *Dónde* está Ollama. Casi siempre es tu propio ordenador. | `http://localhost:11434` (este mismo PC) | — |

Estos tres valores son los **de fábrica**, y son con los que se ha probado todo.

### Qué modelo elegir según tu ordenador

| Tu ordenador | Qué poner en `UNED_LLM_MODEL` | Notas |
|---|---|---|
| **Normal** (8 GB de RAM o más) | *No pongas nada* (usa `qwen2.5:7b-instruct`) | Es el probado. Responde en español de forma fiable. |
| **Modesto** (menos de 8 GB de RAM, o va muy lento) | `llama3.2` (~2 GB) | Más rápido y ligero. *Sin probar a fondo*: puede redactar peor en español o responder más corto. |
| **Potente** (16 GB de RAM o más, ideal con tarjeta gráfica) | `qwen2.5:14b-instruct` (~9 GB) | Respuestas más cuidadosas, pero más lentas y pesadas. *Sin probar*. |

Deja `UNED_EMBED_MODEL` como está salvo que sepas lo que haces: cambiarlo obliga a **volver a leer
todos los documentos** (el programa lo hace solo y avisa; tarda unos minutos).
Puedes ver todos los modelos disponibles en <https://ollama.com/library>.

### Cómo cambiarlo, paso a paso

1. En la carpeta del proyecto hay un fichero llamado **`ajustes.ejemplo.txt`**. Haz una **copia** y
   renombra la copia a **`ajustes.txt`** (si Windows oculta las extensiones, asegúrate de que no se
   queda como `ajustes.txt.txt`).
2. Ábrelo con el **Bloc de notas** (clic derecho → *Abrir con* → *Bloc de notas*).
3. Quita el `#` del principio de la línea que quieras usar. Por ejemplo, para un ordenador modesto
   el fichero quedaría así:

   ```
   UNED_LLM_MODEL=llama3.2
   ```

   Y si tienes Ollama en otro ordenador de tu casa (caso poco habitual), así:

   ```
   UNED_LLM_MODEL=qwen2.5:7b-instruct
   OLLAMA_HOST=http://192.168.1.50:11434
   ```

4. Guarda, cierra la ventana negra si estaba abierta y vuelve a abrir **`Iniciar.bat`**. Verás el
   mensaje `Ajuste de ajustes.txt: …` y, si el modelo es nuevo, **lo descargará él solo** (puede tardar).
5. **Para volver a lo de siempre**, borra `ajustes.txt` y reabre `Iniciar.bat`.

> Los modelos antiguos se quedan guardados en tu disco. Para liberar espacio, abre una consola
> (tecla Windows → escribe `cmd` → Intro) y ejecuta `ollama list` para verlos y
> `ollama rm nombre-del-modelo` para borrar uno.

---

## Si algo falla

| Problema | Solución |
|---|---|
| «No encuentro Python» al abrir `Iniciar.bat` | Repite el Paso 1 y **marca la casilla «Add python.exe to PATH»**. Después reinicia el ordenador. |
| Se abre la tienda de Microsoft pidiendo instalar Python | Instálalo como en el Paso 1 (desde python.org, no desde la tienda). |
| Falla al instalar dependencias | Comprueba tu conexión a internet y que usas Python 3.12. Vuelve a abrir `Iniciar.bat`: retoma donde se quedó. |
| Dice que Ollama no está instalado | Haz el Paso 2 y vuelve a abrir `Iniciar.bat`. |
| El buscador no responde o tarda mucho | Normal en la primera pregunta (la IA está «despertando»). La IA necesita unos 8 GB de RAM libres; cierra otros programas pesados. |
| La web dice «Motor de estudio apagado» | Cierra la ventana negra y vuelve a abrir `Iniciar.bat`. |
| «El puerto ya está en uso» o la web no carga | Cierra todas las ventanas negras de este programa, espera 10 segundos y vuelve a abrir `Iniciar.bat`. |
| Nada de lo anterior funciona | Abre una incidencia en la pestaña **Issues** de GitHub y adjunta el fichero `backend/data/logs/app.log`. |

**Sin la IA**: si tu ordenador es muy modesto, abre una consola en la carpeta y ejecuta
`python iniciar.py --sin-ia`: todo funciona excepto el buscador con IA.

---

## Mac y Linux

1. Instala Python 3.12+ (<https://www.python.org/downloads/>) y Ollama (<https://ollama.com/download>).
2. Descarga y descomprime el ZIP.
3. Abre una Terminal en la carpeta y ejecuta: `./iniciar.sh`
   (si da error de permisos: `chmod +x iniciar.sh` y de nuevo).

---

## Para quien sí programa

Todo el detalle técnico está en [CLAUDE.md](CLAUDE.md). Resumen:

```
UNED/
├── Iniciar.bat / iniciar.sh / iniciar.py   # lanzador todo-en-uno
├── docs/                # documentación de las asignaturas (fuente del RAG)
├── feed/                # diario + noticias RSS (un .md por entrada)
├── agenda/              # eventos (compartidos) y tareas (personales, no se suben a git)
├── contacts/  glossary/ # contactos y glosario, un .md por registro
├── backend/             # FastAPI :8000 — feed, RAG (ChromaDB + Ollama), biblioteca, agenda…
├── estudio-profundo/    # FastAPI :8011 — lector anotado, quiz, repaso espaciado (FSRS)
│   └── content/         # <slug>/document.json + quiz.json: el contenido de estudio
├── frontend/            # HTML/CSS/JS sin build (ES modules)
└── scripts/             # utilidades opcionales (PowerShell)
```

- Modelos de Ollama configurables con las variables de entorno `UNED_EMBED_MODEL` / `UNED_LLM_MODEL` y el host con
  `OLLAMA_HOST` (o, sin tocar el sistema, con `ajustes.txt`, que lee `iniciar.py`; ver la sección anterior).
  Si `iniciar.py` detecta otro `UNED_EMBED_MODEL`, borra `backend/data/chroma` y reindexa.
- Reindexar a mano: `.venv\Scripts\python.exe -m backend.app.rag.ingest`
- Consulta por CLI: `.venv\Scripts\python.exe -m backend.app.rag.query "pregunta"`
- Recargar el contenido de estudio: `cd estudio-profundo/backend && ..\..\.venv\Scripts\python.exe scripts/seed.py`
- `scripts/registrar-avisos-agenda.ps1` (opcional, Windows) crea avisos de escritorio para los eventos de la agenda.
- Convención de documentos: [docs/README.md](docs/README.md) · feed: [feed/README.md](feed/README.md) ·
  agenda: [agenda/README.md](agenda/README.md) · motor de estudio: [estudio-profundo/README.md](estudio-profundo/README.md).

## Aviso sobre el material

Los PDFs de `docs/` son guías docentes y materiales publicados por la UNED, y las fichas de estudio son
resúmenes de apoyo hechos por estudiantes: **no sustituyen a la guía de la asignatura ni al equipo docente**.
Comprueba siempre fechas y criterios de evaluación en el curso virtual (aLF/Ágora).

## Licencia

El **código** de este proyecto se publica con licencia [MIT](LICENSE): puedes usarlo, copiarlo y
modificarlo libremente. La licencia **no cubre** los materiales de terceros incluidos en `docs/`
(guías docentes y documentos de la UNED, apuntes y libros), que pertenecen a sus autores y a la UNED,
ni las tipografías de `frontend/fonts/` (licencia SIL OFL, cada una con la suya).
