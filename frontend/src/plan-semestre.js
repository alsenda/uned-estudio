/** Datos del semestre que usa el panel de Inicio (dashboard.js) y los colores del
 * calendario. Se edita a mano: aquí solo vive lo que NO está en `agenda/events`
 * (que da tutorías, entregas y exámenes). Cada tema semanal lleva `official`:
 *   true  → fecha publicada por el equipo docente en Agora
 *   false → plan orientativo (sugerencia propia o del curso, sin fecha oficial)
 * Fuentes: Agora (cronograma de Álgebra, planificación de Lógica), guías docentes. */

import { SYLLABUS } from "./syllabus.js";

export const SEMESTER_START = "2026-10-05"; // lunes de la semana 1
export const SEMESTER_WEEKS = 16;

export const SUBJECTS = [
  {
    key: "fp",
    code: "71901020",
    folder: "71901020-fundamentos-de-programacion",
    name: "Fundamentos de Programación",
    short: "Programación",
    ects: 6,
    color: "#c2413b",
    pending: "Pendiente de reconocimiento de créditos: sin tutorías ni planificación.",
    topics: [],
  },
  {
    key: "computadores",
    code: "7103104-",
    folder: "7103104--fundamentos-de-computadores",
    name: "Fundamentos de Computadores",
    short: "Computadores",
    ects: 6,
    color: "#dd7a12",
    defaultTopic: "Sin temporalización publicada.",
    topics: [
      { from: "2026-10-05", to: "2026-10-31", title: "Temas 1–2 · Componentes e interconexión; memoria (apuntes: Tema 1, parte I)", official: false },
      { from: "2026-11-01", to: "2026-11-29", title: "Temas 3–6 · Entrada/salida, CPU, introducción a los SO y procesos", official: false },
      { from: "2026-11-30", to: "2026-12-20", title: "Temas 7–8 · Planificación de procesos y memoria · PED", official: false },
      { from: "2026-12-21", to: "2027-01-24", title: "Temas 9–10 · E/S y archivos del sistema operativo · repaso", official: false },
    ],
  },
  {
    key: "logica",
    code: "71031033",
    folder: "71031033-logica-y-estructuras-discretas",
    name: "Lógica y Estructuras Discretas",
    short: "Lógica",
    ects: 6,
    color: "#1f9d63",
    defaultTopic: "Sin temporalización publicada.",
    note: "PEC: 16 tests abiertos todo el curso; realiza o repite el test del bloque que estés estudiando.",
    topics: [
      { from: "2026-10-05", to: "2026-10-31", title: "Bloque 1 · Lógica proposicional (octubre)", official: true },
      { from: "2026-11-01", to: "2026-11-30", title: "Bloque 2 · Lógica de predicados (noviembre)", official: true },
      { from: "2026-12-01", to: "2026-12-31", title: "Bloque 3 · Conjuntos, relaciones, funciones y combinatoria (diciembre)", official: true },
      { from: "2027-01-01", to: "2027-01-24", title: "Bloque 4 · Grafos y árboles (enero)", official: true },
    ],
  },
  {
    key: "algebra",
    code: "71031027",
    folder: "71031027-fundamentos-algebraicos-para-la-ia",
    name: "Fundamentos Algebraicos para la IA",
    short: "Álgebra",
    ects: 6,
    color: "#7a4cc2",
    defaultTopic: "Sin temporalización publicada.",
    topics: [
      { from: "2026-10-05", to: "2026-10-11", title: "Tema 1 · Escalares (5–11 oct.)", official: true },
      { from: "2026-10-12", to: "2026-11-01", title: "Tema 2 · Tensores, matrices y vectores (12 oct.–1 nov.)", official: true },
      { from: "2026-11-02", to: "2026-11-22", title: "Tema 3 · Matrices y tensores como aplicaciones lineales (2–22 nov.)", official: true },
      { from: "2026-11-23", to: "2026-12-06", title: "Tema 4 · Procesos de triangulación (fecha sin publicar)", official: false },
      { from: "2026-12-07", to: "2027-01-24", title: "Tema 5 · Procesos de diagonalización (7 dic.–17 ene.)", official: true },
    ],
  },
  {
    key: "calculo",
    code: "71031010",
    folder: "71031010-fundamentos-de-calculo-para-la-ia",
    name: "Fundamentos de Cálculo para la IA",
    short: "Cálculo",
    ects: 6,
    color: "#3556e0",
    defaultTopic: "Sin temporalización específica publicada para esta semana.",
    topics: [
      { from: "2026-10-05", to: "2026-10-31", title: "Temas 1–2 · Números reales y funciones (plan orientativo)", official: false },
      { from: "2026-11-01", to: "2026-11-29", title: "Temas 3–5 · Límites, derivadas y aplicaciones (plan orientativo)", official: false },
      { from: "2026-11-30", to: "2026-12-20", title: "Temas 6–7 · Integrales · PEC (plan orientativo)", official: false },
      { from: "2026-12-21", to: "2027-01-24", title: "Temas 8–10 · Series, métodos numéricos y varias variables (plan orientativo)", official: false },
    ],
  },
];

/** Color y nombre corto por código de asignatura (los usa también calendar.js). */
for (const subject of SUBJECTS) subject.syllabus = SYLLABUS[subject.key] ?? [];

export function subjectByFolder(folder) {
  if (!folder) return null;
  return SUBJECTS.find((s) => String(folder).startsWith(s.code)) ?? null;
}
