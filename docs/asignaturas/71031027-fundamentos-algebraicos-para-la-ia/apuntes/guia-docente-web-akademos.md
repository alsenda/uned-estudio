# Fundamentos Algebraicos para la IA — guía docente (versión web)

Código 71031027 · curso 2026/2027. Texto de la guía publicada en la web de la UNED, que es la que enlaza el botón «Guía de la asignatura» de Akademos Web. Volcado el 2026-10-05.

Fuente: https://www.uned.es/universidad/inicio/estudios/grados/cursos/2027/titulacion/asignatura.html?codAsignatura=71031027&idContenido=1

> **ATENCIÓN — errata:** en el apartado «¿Cómo se obtiene la nota final?» esta versión web (igual que el
> PDF) dice «Si Npra ≥ 2.5 y Npec < 4, entonces Nf = Npra», que es incorrecto. El equipo docente corrigió
> el 30-sep-2026: «Si Npra ≥ 2.5 y **Np < 4**, entonces Nf = **Np**; si Npra ≥ 2.5 y **Np ≥ 4**, entonces
> Nf = mín{Np + 0.1·Npec + 0.1·Npra, 10}». Ver `agora-avisos-y-fechas.md`.

---

Presentación y contextualización

- 

 Requisitos y/o recomendaciones para cursar esta asignatura

- 

 Equipo docente

- 

 Horario de atención al estudiante

- 

 Competencias que adquiere el estudiante

- 

 Resultados de aprendizaje

- 

 Contenidos

- 

 Metodología

- 

 Sistema de evaluación

- 

 Bibliografía básica

- 

 Bibliografía complementaria

- 

 Recursos de apoyo y webgrafía

 MATRICÚLATE GRADO Y MÁSTER 

 Código Asignatura: 71031027

 NO EXISTEN CAMBIOS

 La guía de la asignatura ha sido actualizada con los cambios que aquí se mencionan.

 Nombre y apellidos

 FERNANDO JIMENEZ ALBURQUERQUE
 (Coordinador/a de asignatura)

 Correo electrónico

 fjimenez@ind.uned.es

 Teléfono
 91398-9600

 Facultad

 ESCUELA TÉCN.SUP INGENIEROS INDUSTRIALES

 Departamento

 MATEMÁTICA APLICADA I

 Nombre y apellidos

 JUAN JACOBO PERAN MAZON

 Correo electrónico

 jperan@ind.uned.es

 Teléfono
 91398-7915

 Facultad

 ESCUELA TÉCN.SUP INGENIEROS INDUSTRIALES

 Departamento

 MATEMÁTICA APLICADA I

 Nombre y apellidos

 ESTIBALITZ DURAND CARTAGENA

 Correo electrónico

 edurand@ind.uned.es

 Teléfono
 91398-6439

 Facultad

 ESCUELA TÉCN.SUP INGENIEROS INDUSTRIALES

 Departamento

 MATEMÁTICA APLICADA I

 NOMBRE DE LA ASIGNATURA

 NOMBRE DE LA ASIGNATURA
 FUNDAMENTOS ALGEBRAICOS PARA LA IA

 CÓDIGO

 CÓDIGO
 71031027

 CURSO ACADÉMICO

 CURSO ACADÉMICO
 2026/2027

 DEPARTAMENTO

 DEPARTAMENTO

 MATEMÁTICA APLICADA I

 TÍTULO EN QUE SE IMPARTE

 TÍTULO EN QUE SE IMPARTE

 GRADO EN INGENIERÍA EN INTELIGENCIA ARTIFICIAL

 CURSO

 CURSO

 PRIMER

 CURSO

 PERIODO

 SEMESTRE 1

 TIPO
 FORMACIÓN BÁSICA

 Nº ECTS

 Nº ECTS
 6

 HORAS

 HORAS
 150

 IDIOMAS EN QUE SE IMPARTE

 IDIOMAS EN QUE SE IMPARTE
 CASTELLANO

La asignatura Fundamentos Algebraicos para la IA es una asignatura de Formación Básica que forma parte de la materia Matemáticas para la IA y se imparte durante el primer semestre del primer curso del plan de estudios del Grado en Inteligencia Artificial.

Los fundamentos algebraicos constituyen una herramienta esencial para el desarrollo de la Inteligencia Artificial moderna. Buena parte de los métodos actuales de aprendizaje automático, procesamiento de datos, visión artificial, modelos generativos o representación semántica de la información se apoyan en estructuras algebraicas como vectores, matrices y tensores, así como en operaciones lineales y multilineales sobre dichos objetos. Por ello, esta asignatura proporciona una base matemática imprescindible para comprender los modelos y algoritmos que el estudiante encontrará posteriormente en otras materias del grado, relacionadas con aprendizaje automático, minería de datos, optimización, visión por computador, procesamiento del lenguaje natural o redes neuronales.

La orientación de la asignatura es eminentemente aplicada y computacional. Aunque se introducen los conceptos matemáticos fundamentales del álgebra lineal y multilineal (se presentará el concepto de tensor), el objetivo principal no es el desarrollo formal abstracto, sino la adquisición de intuición estructural y capacidad operativa sobre los objetos matemáticos que aparecen de manera natural en Inteligencia Artificial. Se pondrá especial énfasis en la interpretación geométrica y computacional de los conceptos estudiados, así como en su conexión con problemas reales relacionados con representación de datos, reducción de dimensionalidad, similitud entre objetos, aproximación numérica y tratamiento eficiente de información.

Por su carácter instrumental, la asignatura se sitúa en los primeros cursos del Grado, ya que proporciona herramientas matemáticas básicas que sirven de apoyo a otras materias del grado. En particular, ofrece los fundamentos algebraicos necesarios para la representación, transformación y análisis de datos, así como para la comprensión de modelos y algoritmos de inteligencia artificial. El estudiantado podrá interpretar los datos como elementos de espacios vectoriales de gran dimensión, comprenderá el papel de las transformaciones lineales en los modelos de IA y utilizará descomposiciones matriciales fundamentales en el análisis y procesamiento de datos.

La inclusión de la asignatura en el plan de estudios persigue, entre otros, los siguientes objetivos:

- 
Proporcionar una base algebraica sólida para el estudio de técnicas modernas de Inteligencia Artificial.

- 
Desarrollar capacidad de razonamiento matemático y abstracción estructural aplicada a problemas computacionales.

- 
Familiarizar al estudiante con el lenguaje matemático utilizado en aprendizaje automático y ciencia de datos.

- 
Introducir herramientas algebraicas fundamentales para el tratamiento eficiente de datos de alta dimensión.

- 
Ayudar a adquirir competencias analíticas y computacionales necesarias en el desarrollo de modelos de IA.

La asignatura introduce desde el inicio el concepto general de tensor como estructura de datos multidimensional indexada, interpretando vectores, matrices y escalares como casos particulares. A partir de esta perspectiva unificada, se estudian operaciones fundamentales, aplicaciones lineales, ortogonalidad, mínimos cuadrados y factorizaciones matriciales. Especial relevancia tendrán las descomposiciones espectrales y la descomposición en valores singulares (SVD), debido a su importancia en técnicas actuales de reducción de dimensionalidad, recomendación, compresión y aprendizaje automático.

Asimismo, el enfoque de la asignatura pretende mostrar que muchas herramientas aparentemente distintas de la Inteligencia Artificial comparten una misma estructura algebraica subyacente. Por ejemplo:

- 
En aprendizaje automático supervisado, los modelos lineales y las redes neuronales utilizan operaciones matriciales y transformaciones lineales de forma sistemática.

- 
En sistemas de recomendación y análisis semántico, la factorización matricial y la SVD permiten detectar estructuras latentes en grandes conjuntos de datos.

- 
En procesamiento del lenguaje natural y representación de embeddings, la similitud entre vectores y las nociones geométricas de distancia y ángulo desempeñan un papel central.

- 
En visión artificial, las imágenes y vídeos se representan como tensores multidimensionales sobre los que se aplican transformaciones algebraicas.

- 
En optimización y ajuste de modelos, los problemas de mínimos cuadrados y pseudoinversa aparecen de manera recurrente.

La asignatura pretende, en definitiva, proporcionar al estudiante una comprensión conceptual y práctica de las estructuras algebraicas fundamentales sobre las que se construyen muchas de las herramientas actuales de Inteligencia Artificial.

Además, esta asignatura contribuye al perfil profesional del graduado/a en Inteligencia Artificial proporcionando los fundamentos matemáticos necesarios para la representación, transformación y análisis de datos. Los conceptos de vectores, matrices, espacios vectoriales, transformaciones lineales, valores y vectores propios constituyen la base de numerosos métodos de aprendizaje automático, aprendizaje profundo, visión artificial, procesamiento del lenguaje natural y análisis de datos. Asimismo, la asignatura desarrolla capacidades de abstracción, modelización matemática y razonamiento lógico, esenciales para diseñar, implementar y evaluar sistemas de inteligencia artificial.

El nivel de conocimientos recomendado para afrontar con éxito el estudio de la asignatura es el correspondiente a la formación matemática básica adquirida en Bachillerato, especialmente en los bloques relacionados con álgebra elemental, funciones y geometría analítica.

Se recomienda especialmente que el estudiante repase previamente:

- 
Operaciones algebraicas básicas.

- 
Resolución de sistemas de ecuaciones lineales sencillos.

- 
Manipulación elemental de matrices.

- 
Interpretación gráfica y geométrica de vectores.

- 
Nociones básicas de funciones y representación matemática.

Para refrescar estos contenidos en un contexto próximo a las matemáticas universitarias, se recomienda al estudiante emplear el Curso 0 de Matemáticas (abierto y gratuito), especialmente el bloque Álgebra y Geometría:

https://www.uned.es/universidad/inicio/unidad/IUED/innovacion/grupos-innovacion/grupo-20/recursos.html

Las dificultades más frecuentes en esta materia suelen estar relacionadas con:

- 
Dificultades de lenguaje matemático y notación.

La Inteligencia Artificial utiliza de manera intensiva notación matricial y vectorial. En muchos casos, las dificultades iniciales proceden más de la familiarización con el lenguaje simbólico que de la complejidad conceptual de los contenidos.

- 
Falta de intuición geométrica o estructural.

Conceptos como dimensión, dependencia lineal, transformación lineal o ortogonalidad requieren desarrollar una cierta intuición espacial y estructural. Esta capacidad se adquiere progresivamente mediante ejemplos, visualizaciones y práctica continuada.

- 
Escasa experiencia computacional con objetos algebraicos.

Una parte importante del aprendizaje consistirá en interpretar matrices y tensores como estructuras de datos utilizadas en computación e Inteligencia Artificial. Por ello, se fomentará una visión práctica y computacional de los contenidos.

- 
Poca destreza en algoritmos algebraicos básicos.

La soltura en operaciones matriciales y resolución de problemas se adquiere fundamentalmente mediante la realización de ejercicios y actividades prácticas.

Se recomienda al estudiante (en caso de que no lo haya hecho) iniciarse en el manejo de lenguajes de programación orientados al cálculo matemático (tanto simbólico como numérico) y al tratamiento de datos. Se proporcionarán manuales básicos a tal propósito. 

En general, se recomienda al estudiante mantener un trabajo continuo y regular desde el comienzo del curso, ya que los contenidos presentan una fuerte dependencia conceptual y se construyen progresivamente unos sobre otros.

CONTACTO CON EL EQUIPO DOCENTE

I. Consultas con contenido matemático o sobre el funcionamiento de la asignatura, por orden de preferencia:

- 
Foros del curso virtual. Con la única excepción de las consultas en las que se deba resguardar la privacidad, este es el procedimiento prioritario.

- 
Correo electrónico.

- 
Reunión por Teams. Se ruega concertar cita mediante correo electrónico.

- 
Teléfono.

- 
Entrevista. Departamento de Matemática Aplicada I, Escuela de Ingenieros Industriales de la UNED, 2ª planta, calle de Juan del Rosal 12, Madrid. Se ruega concertar cita mediante correo electrónico.

II. Consultas privadas (evaluación, orientaciones metodológicas, bibliografía, etc.), por orden de preferencia:

- 
Correo electrónico.

- 
Reunión por Teams. Se ruega concertar cita.

- 
Teléfono.

- 
Entrevista. Se ruega concertar cita.

HORARIO DE ATENCIÓN:

Departamento de Matemática Aplicada, ETSI Industriales de la UNED, c/ Juan del Rosal, 12, 28040 Madrid.

Fernando Jiménez (coordinador): Martes de 15 a 19h.

Estibalitz Durand: Miércoles de 10 a 14h.

Juan Perán: Miércoles de 10 a 14h.

Téngase en cuenta que durante las semanas de exámenes el equipo docente puede estar en comisión de servicios en alguno de los tribunales, por lo que no sería posible la atención durante estos perio­dos.

Si necesitan contactar con el coordinador antes de la apertura del curso virtual o después de la segunda semana de exámenes, deben utilizar el correo electrónico. 

 Las sesiones de tutoría se imparten presencialmente y en línea desde el Centro Asociado de referencia o, en su defecto, desde otro Centro Asociado. A continuación se muestran los centros asociados y extensiones en las que se imparten tutorías de la asignatura. 

Horarios de 
 FUNDAMENTOS ALGEBRAICOS PARA LA IA

 Tipo de centro:

 Centros de España

 Centros en el extranjero

 Provincia:

 Seleccione una provincia

 A CORUÑA

 ALBACETE

 ALICANTE

 ALMERÍA

 ARABA / ÁLAVA

 ASTURIAS

 ÁVILA

 BADAJOZ

 BARCELONA

 BIZKAIA

 BURGOS

 CÁCERES

 CÁDIZ

 CANTABRIA

 CASTELLÓN

 CEUTA

 CIUDAD REAL

 CÓRDOBA

 CUENCA

 GIPUZKOA

 GIRONA

 GRANADA

 GUADALAJARA

 HUELVA

 HUESCA

 ILLES BALEARS

 JAÉN

 LA RIOJA

 LAS PALMAS

 LEÓN

 LLEIDA

 LUGO

 MADRID

 MÁLAGA

 MELILLA

 MURCIA

 NAVARRA

 OURENSE

 PALENCIA

 PONTEVEDRA

 SALAMANCA

 SANTA CRUZ DE TENERIFE

 SEGOVIA

 SEVILLA

 SORIA

 TARRAGONA

 TERUEL

 TOLEDO

 VALENCIA

 VALLADOLID

 ZAMORA

 ZARAGOZA

Cargando, esto puede tardar un poco...

 Cargando...

Ver apartado "Resultados de aprendizaje".

RA01: Al finalizar el aprendizaje, el o la estudiante será capaz de aplicar los conocimientos necesarios de álgebra, cálculo, análisis, matemática discreta, lógica y estadística para la resolución de los problemas propios de la inteligencia artificial. 

RA13: Al finalizar el aprendizaje, el o la estudiante será capaz de demostrar conocimientos y técnicas básicas de los diferentes enfoques de la inteligencia artificial y su integración como profesionales de inteligencia artificial en equipos multidisciplinares.

Escalares

- Naturales y enteros. Bases de numeración.

- Racionales y reales.

- Números complejos.

Tensores, matrices y vectores

- Tensores.

- Matrices.

- Vectores

- Suma y producto por escalares. Espacios vectoriales.

- Multiplicación de matrices.

- Ortogonalidad.

- Matriz inversa.

Matrices y tensores como aplicaciones lineales o multilineales

- Aplicaciones lineales y multilineales.

- Determinantes.

- Formas bilineales.

- Aplicaciones lineales entre espacios de vectores.

Procesos de triangulación

- Eliminación gaussiana y factorización PLU.

- Factorización QR.

- Resolución de sistemas y mínimos cuadrados.

- El teorema de Rouché Frobenius.

Procesos de diagonalización

- Casos particulares de la factorización PLU.

- Autovalores, autovectores y autovectores generalizados.

- Forma de Jordan.

- Teorema espectral para matrices simétricas.

- Descomposición en valores singulares (SVD).

- Pseudoinversa.

La asignatura Fundamentos algebraicos para la IA se impartirá conforme a la metodología no presencial que caracteriza a la UNED. En ella prima el autoprendizaje del alumno, asistido por el profesor mediante diversos sistemas de comunicación docente-discente. Mayoritariamente son asíncronos, si bien las tutorías pueden ser presenciales, impartidas en los Centros Asociados, o semipresenciales permitiendo la conexión del alumnado a las sesiones con independencia de su localización geográfica. Además, la docencia se imparte con apoyo de una plataforma virtual interactiva en la que se combinan distintos recursos, los medios impresos y los audiovisuales y virtuales. Más en concreto, la plataforma virtual contendrá: contenidos, foros de discusión, tareas y enlaces de interés.

Estrategias de aprendizaje recomendadas para la preparación de la asignatura

Para abordar con éxito esta asignatura, se recomienda adoptar un enfoque híbrido que conecte de forma inmediata la abstracción matemática con su traducción algorítmica. Se debe evitar la memorización puramente mecánica de teoremas y decantarse por la visualización geométrica de las operaciones, cuando sea posible, utilizando herramientas interactivas que les permitan "ver" cómo una matriz transforma el espacio de datos. Es fundamental basar el aprendizaje basado en problemas prácticos: cada concepto teórico (como una factorización o un autovector) se consolida al abordar casos de uso real, como la compresión de imágenes o el ajuste de un modelo de regresión.

Se aconseja estudiar los procesos algebraicos de forma incremental, partiendo de las operaciones discretas y escalares para escalar progresivamente hacia estructuras multilineales y tensores complejos. Por último, resulta indispensable complementar el cálculo manual con el desarrollo en código, traduciendo las demostraciones analíticas a librerías de computación científica (como NumPy o PyTorch), lo que no solo afianza la comprensión del álgebra lineal, sino que mitiga la frustración ante el manejo de sistemas de gran dimensionalidad.

 TIPO DE PRUEBA PRESENCIAL

 Tipo de examen

 Tipo de examen
 Examen de desarrollo

 Preguntas desarrollo

 Preguntas desarrollo
 4

 Duración

 Duración
 120 (minutos)

 Material permitido en el examen

 Material permitido en el examen

Ninguno

 Criterios de evaluación

 Criterios de evaluación

Tanto en la convocatoria de febrero, como en la de septiembre, la prueba escrita presencial constará de varias preguntas que podrán ser teóricas, prácticas o teórico-prácticas y que podrán tener varios apartados. Cada pregunta se valora del 0 al 10 y la nota del examen es la media aritmética de todas las notas. 

Criterios de corrección:

- Es necesario desarrollar el proceso lógico que conduce al resultado numérico. Los resultados, parciales o finales, que no estén debidamente justificados no podrán ser valorados.

- Todos los errores conllevan una penalización. Los errores de concepto se penalizarán en mayor medida que los de cálculo y, entre estos últimos, tendrán mayor repercusión aquellos que conduzcan a resultados incoherentes. Un error grave de concepto podrá implicar la anulación del ejercicio correspondiente.

- Es obligatorio realizar los ejercicios por los procedimientos que se indiquen en el enunciado.

 % del examen sobre la nota final

 % del examen sobre la nota final
 80

 Nota mínima del examen para aprobar sin PEC

 Nota mínima del examen para aprobar sin PEC
 5

 Nota máxima que aporta el examen a la calificación final sin PEC

 Nota máxima que aporta el examen a la calificación final sin PEC
 10

 Nota mínima en el examen para sumar la PEC

 Nota mínima en el examen para sumar la PEC
 4

 Comentarios y observaciones

 Comentarios y observaciones

El 80% que aparece en el campo de "% del examen sobre la nota final% debe interpretarse como un valor mínimo. Por favor, consultar, el apartado "¿Cómo se obtiene la nota final?"

PRUEBAS DE EVALUACIÓN CONTINUA (PEC)

 ¿Hay PEC?

 ¿Hay PEC?
 Si

 Descripción

 Descripción

-La evaluación continua consistirá en una prueba de evaluación a distancia online. La prueba abarcará los contenidos correspondientes a los cuatro primeros bloques de la asignatura.

-El tiempo estimado de realización de la prueba es de 5 horas. Se abrirá un periodo de tiempo adecuado a esta estimación en el curso virtual para su realización y entrega.

-La prueba de evaluación continua no es obligatoria, pero es aconsejable realizarla para conseguir los objetivos de aprendizaje de la asignatura. El equipo docente informará sobre el calendario y otros detalles de la prueba de evaluación continua a través de los foros del curso virtual.

-Su calificación se conservará para la convocatoria extraordinaria.

 Criterios de evaluación

 Criterios de evaluación

-La prueba constará de 5 preguntas tipo test. Cada respuesta correcta suma 0,2 puntos. Las respuestas erróneas no descuentan puntos

-Se calificará la prueba de 0 a 10 puntos.

-La calificación de una prueba no presentada equivale a 0 puntos.

-Se tendrá en cuenta la nota de la PEC en caso de que la nota de la prueba presencial sea superior o igual a 4.

 Ponderación de la PEC en la nota final

 Ponderación de la PEC en la nota final
 La PEC aportará un máximo de 1 punto a la calificación final. Por favor, consultar el apartado "¿Cómo se obtiene la nota final?".

 Fecha aproximada de entrega

 Fecha aproximada de entrega
 Diciembre

 Comentarios y observaciones

 Comentarios y observaciones

OTRAS ACTIVIDADES EVALUABLES

 ¿Hay otra/s actividad/es evaluable/s?

 ¿Hay otra/s actividad/es evaluable/s?
 Si

 Descripción

 Descripción

Prácticas de programación

Los objetivos que se plantean en la realización de esta práctica son los siguientes:

Familiarización con la implementación computacional de los conceptos algebraicos estudiados en la asignatura.

Desarrollo de la capacidad para representar estructuras matemáticas abstractas mediante construcciones propias de un lenguaje de programación.

Aplicación práctica de herramientas algebraicas fundamentales en problemas relacionados con la Inteligencia Artificial.

Implementación de programas sencillos por medio de Python que permitan manipular y analizar objetos matemáticos de interés en el ámbito de la IA. Se aportará material básico sobre Phython en el curso virtual.

Las prácticas tienen carácter obligatorio. 

Quienes no entreguen las prácticas en la convocatoria ordinaria, tendrán la oportunidad de realizarlas en septiembre (para la convocatoria extraordinaria).

Se calificará la práctica de 0 a 10. Si la nota de prácticas es inferior a 2,5 puntos, la calificación de la convocatoria correspondiente (ordinaria o extraordinaria) será suspenso.

Se trendrá en cuenta la calificación de las prácticas para la nota final solo en caso de que la calificación de la prueba presencial sea superior o igual a 4.

 Criterios de evaluación

 Criterios de evaluación

- La práctica es un trabajo individual. La sospecha de copia o de empleo abusivo de herramientas de IA llevará a aplicar las medidas académicas y disciplinarias previstas en la normativa vigente.

- Cada tutor organizará una sesión de control (de unas tres horas) de la realización de la práctica. Esta sesión de control tiene carácter presencial y no obligatorio:

Será el tutor quien determine la fecha de dicha sesión y, en su caso, el procedimiento para su desarrollo.

El tutor podrá realizar preguntas relativas al diseño, implementación y funcionamiento de la práctica con el fin de comprobar la adquisición de las competencias previstas.

- Se habilitará un cuestionario en el curso virtual para la entrega de la documentación que se requiera (código y explicaciones). Ese cuestionario contendrá una batería de preguntas tipo test destinada a comprobar el funcionamiento del código pedido (medido por sus resultados), así como la autoría personal y la comprensión de los conceptos involucrados en el desarrollo. La evaluación del cuestionario será sumativa.

 Ponderación en la nota final

 Ponderación en la nota final
 Las prácticas aportarán un máximo de 1 punto a la calificación final. Consultar el apartado "¿Cómo se obtiene la nota final?"

 Fecha aproximada de entrega

 Fecha aproximada de entrega
 Enero

 Comentarios y observaciones

 Comentarios y observaciones

¿Cómo se obtiene la nota final?

Tendremos en cuenta las siguientes calificaciones:

Np = nota de la prueba presencial 

Npec = nota de la PEC, realizada en diciembre

Npra = representa la nota de la práctica entregada en enero, para la convocatoria ordinaria, y la nota de la práctica entregada en septiembre, para la convocatoria extraordinaria.

Nf = nota final

Las pruebas no realizadas se califican con cero puntos.

CALIFICACIÓN DE LAS CONVOCATORIAS ORDINARIA Y EXTRAORDINARIA

Si Npra < 2.5, entonces Nf = suspenso.

Si Npra ≥ 2.5 y Npec < 4, entonces Nf = Npra.

Si Npra ≥ 2.5 y Npec ≥ 4, entonces Nf = mín { Np + 0.1*Npec+ 0.1*Npra, 10}.

Se utilizarán materiales del propio curso virtual, la bibliografía complementaria y otros materiales en abierto. 

Se publicará en el campus virtual una amplia colección de ejercicios resueltos y se ofrecerá orientación a los estudiantes para resolver los ejercicios de la bibliografía complementaria.

Se recomiendan los siguientes libros como bibliografía complementaria:

-Álgebra Lineal y sus Aplicaciones, David C. Lay. Editorial Pearson Educación (ISBN 978-970-26-0906-3).

-Introduction to Linear Algebra, Gilbert Strang. Editorial Wellesley - Cambridge Press (ISBN 978-1-7331466-7-8).

-Introduction to Applied Linear Algebra, Stephen Boyd. Editorial Lieven Vandenberghe, Cambridge University Press & Assessment (ISBN 978-1-316-51896-0 )

-Álgebra para ingenieros, Ana María Díaz, Elvira Hernández, Luis Tejero. Editorial Sanz y Torres (ISBN 978-8-492-94824-6)

En el curso virtual se pondrá a disposición del estudiantado una guía de Python que le permitirá familiarizarse con el uso de esta herramienta informática.

 MATRICÚLATE
