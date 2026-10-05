// Temario de cada asignatura del semestre (títulos de las guías docentes), por clave de asignatura
// (la misma `key` que en plan-semestre.js).
//   official: true  → fechas publicadas por el equipo docente en Agora
//   official: false → fechas orientativas (sin temporalización oficial)
//   doc: id del documento anotado en el motor de estudio, si existe; `docNote` dice qué parte cubre.

export const SYLLABUS = {
  algebra: [
    { id: "t1", title: "Tema 1 · Escalares", from: "2026-10-05", to: "2026-10-11", official: true, doc: "algebra-t1-conjuntos-tuplas-funciones", docNote: "secciones 1.1–1.4 (conjuntos, tuplas, funciones)" },
    { id: "t2", title: "Tema 2 · Tensores, matrices y vectores", from: "2026-10-12", to: "2026-11-01", official: true },
    { id: "t3", title: "Tema 3 · Matrices y tensores como aplicaciones lineales y multilineales", from: "2026-11-02", to: "2026-11-22", official: true },
    { id: "t4", title: "Tema 4 · Procesos de triangulación", from: "2026-11-23", to: "2026-12-06", official: false },
    { id: "t5", title: "Tema 5 · Procesos de diagonalización", from: "2026-12-07", to: "2027-01-17", official: true },
  ],
  calculo: [
    { id: "t1", title: "Tema 1 · Los números reales", from: "2026-10-05", to: "2026-10-18", official: false },
    { id: "t2", title: "Tema 2 · Funciones de una variable real", from: "2026-10-19", to: "2026-10-31", official: false },
    { id: "t3", title: "Tema 3 · Límites y continuidad", from: "2026-11-01", to: "2026-11-08", official: false },
    { id: "t4", title: "Tema 4 · Derivadas", from: "2026-11-09", to: "2026-11-22", official: false },
    { id: "t5", title: "Tema 5 · Aplicaciones de la derivada", from: "2026-11-23", to: "2026-11-29", official: false },
    { id: "t6", title: "Tema 6 · Integrales indefinidas", from: "2026-11-30", to: "2026-12-10", official: false },
    { id: "t7", title: "Tema 7 · Integrales definidas", from: "2026-12-11", to: "2026-12-20", official: false },
    { id: "t8", title: "Tema 8 · Sucesiones y series numéricas", from: "2026-12-21", to: "2027-01-03", official: false },
    { id: "t9", title: "Tema 9 · Métodos numéricos de cálculo", from: "2027-01-04", to: "2027-01-10", official: false },
    { id: "t10", title: "Tema 10 · Funciones de dos o más variables reales", from: "2027-01-11", to: "2027-01-24", official: false },
  ],
  logica: [
    { id: "b1", title: "Bloque 1 · Lógica proposicional", from: "2026-10-05", to: "2026-10-31", official: true },
    { id: "b2", title: "Bloque 2 · Lógica de predicados", from: "2026-11-01", to: "2026-11-30", official: true },
    { id: "b3", title: "Bloque 3 · Conjuntos, relaciones y funciones. Combinatoria", from: "2026-12-01", to: "2026-12-31", official: true },
    { id: "b4", title: "Bloque 4 · Grafos y árboles", from: "2027-01-01", to: "2027-01-24", official: true },
  ],
  computadores: [
    { id: "t1", title: "Tema 1 · Componentes básicos de un computador e interconexión", from: "2026-10-05", to: "2026-10-18", official: false, doc: "computadores-t1-representacion-informacion", docNote: "parte I: representación de la información" },
    { id: "t2", title: "Tema 2 · Unidad de memoria", from: "2026-10-19", to: "2026-10-31", official: false },
    { id: "t3", title: "Tema 3 · Unidad de Entrada/Salida", from: "2026-11-01", to: "2026-11-08", official: false },
    { id: "t4", title: "Tema 4 · Unidad central de procesamiento", from: "2026-11-09", to: "2026-11-15", official: false },
    { id: "t5", title: "Tema 5 · Consideraciones generales de los sistemas operativos", from: "2026-11-16", to: "2026-11-22", official: false },
    { id: "t6", title: "Tema 6 · Descripción y control de procesos", from: "2026-11-23", to: "2026-11-29", official: false },
    { id: "t7", title: "Tema 7 · Planificación de procesos", from: "2026-11-30", to: "2026-12-09", official: false },
    { id: "t8", title: "Tema 8 · Administración de memoria", from: "2026-12-10", to: "2026-12-20", official: false },
    { id: "t9", title: "Tema 9 · Gestión de la Entrada/Salida", from: "2026-12-21", to: "2027-01-10", official: false },
    { id: "t10", title: "Tema 10 · Gestión de archivos", from: "2027-01-11", to: "2027-01-24", official: false },
  ],
};

/** ¿Cae `dateIso` (AAAA-MM-DD) dentro del rango del tema? */
export function isNow(item, dateIso) {
  return Boolean(item.from && item.to && dateIso >= item.from && dateIso <= item.to);
}
