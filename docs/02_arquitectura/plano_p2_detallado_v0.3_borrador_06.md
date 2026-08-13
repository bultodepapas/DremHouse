# Segundo piso detallado v0.3 — borrador 06

**Estatus:** antecedente superado por D-049 / b09-R08; no apto para construir
**Versión:** 0.3-borrador-06-P2  
**Fecha:** 2026-08-11  
**Fuente:** constitución, programa activo, b04/R03 y ventanas de fachada b05/R04.  
**Aprobación pendiente:** propietario, arquitecto coordinador y consultores.

> **Control de precedencia:** esta emisión se conserva como antecedente trazable. El
> modelo activo del segundo piso es b09/R08 bajo D-049.

## Objeto

Precisar la lógica del P2 dentro de su envolvente nominal de **18,00 × 15,00 m**, sin
convertirlo en mezzanine abierto. La emisión coordina privacidad, jerarquía de la suite
principal, cuatro baños privados, ventanas altas, zona wellness y ejecución F1/F2.

## Correcciones de arquitectura

- El dormitorio principal deja de ser una franja angosta: se plantea en **7,40 × 4,20 m
  = 31,1 m² brutos**, con paño dominante de 5,50 m en el **lateral A** y paño posterior
  secundario de 2,50 m (corrección H-06: antes se describía al revés).
- Los dormitorios de hijos quedan en **23,46 m² (H1) y 23,22 m² útiles (H2)**: diferencia
  de **0,24 m²**, dentro de la tolerancia de ±1,00 m² que fija **D-042**. Proporciones
  1,04:1 y 1,23:1, ambas por debajo del límite de 1,35:1.
- La llegada de escalera, el hall, la galería interior y el mini deck son recintos
  cerrados acústicamente hacia la nave. No existe corredor abierto tipo hotel.
- La Fase 2 permanece detrás de una frontera única en Y=11,00 m. El cierre temporal debe
  resolver polvo, ruido, incendio e instalaciones durante la ocupación de F1.
- **El baño de hijo 2 pasa de 1,70 m a 2,80 m de fondo libre** al girar la suite: deja de
  ser un baño-pasillo y repite exactamente el esquema del baño de hijo 1 (2,20 × 2,80 m
  útiles, idénticos). El de huéspedes queda en 2,40 × 2,00 m útiles.
- **La suite de huéspedes alcanza el programa por primera vez:** dormitorio 17,0 m² brutos
  (programa 17–18), baño 5,7 m² (programa 5,5) y closet 5,3 m² (programa 3,5–4). Antes el
  dormitorio estaba 4,5 m² por encima y el baño 1,5 m² por debajo.
- El wellness ocupa **16,8 m² brutos**, dentro de la reserva de programa de 16–22 m², con
  2,72 m de ancho libre: cabe la cabina de 2,40 m que pide el programa.
- **El vestíbulo de Fase 2 pasa de 1,00 a 1,40 m brutos = 1,25 m libres**, por encima del
  mínimo declarado de 1,20 m.
- Los aparatos húmedos se concentran por familias para facilitar bajantes, ventilación y
  mantenimiento. La coincidencia exacta con PB todavía debe verificarse mediante shafts.

## Espesores y desempeño de estudio

- Cerramiento exterior: 0,18 m.
- Caja de escalera y separaciones húmedas críticas: 0,20 m.
- Divisiones acústicas: 0,15 m.
- Puertas de suite: 0,90 m; puertas de baño: 0,80 m.
- Circulación libre objetivo: 1,20 m mínimo de anteproyecto, 1,50 m donde sea posible.
- Vidrio de dormitorio: 2,70 m de alto, antepecho técnico 0,10 m, paño inferior laminado
  y protección contra caída hasta aproximadamente 1,10 m.

Estos valores son reservas de coordinación, no especificaciones constructivas. El sistema
acústico, resistencia al fuego, condensación, perfiles y estructura deben ser diseñados y
firmados por los consultores correspondientes.

## Resultado de control

**Estado al 2026-08-11: 12 PASS · 0 FAIL · 2 OPEN.** La emisión cierra.

### Base de medida

La causa de fondo de los errores anteriores era mezclar bases. Ahora cada regla declara la
suya, y el modelo también:

| Qué se mide                                 | Base             | Fuente                                                                                                   |
| ------------------------------------------- | ---------------- | -------------------------------------------------------------------------------------------------------- |
| Contraste contra el programa arquitectónico | **bruta**        | El programa dice literalmente «áreas brutas/nominales sin descontar estructura, cerramientos y acabados» |
| Igualdad de los dormitorios de hijos        | **útil (neta)**  | Hard rule 9 y conflicto CF-003 hablan de «área útil»                                                     |
| Circulaciones mínimas                       | **libre (neta)** | Son luz libre de paso                                                                                    |

Aplicar una medida neta contra un objetivo bruto fue precisamente lo que hizo «fallar» al
wellness en la revisión previa: 16,8 m² brutos siempre estuvieron dentro de la reserva de
programa de 16–22 m².

### Cómo se cerraron las tres condiciones incumplidas

La revisión de coordinación dejó tres FAIL reales que no se podían corregir moviendo
cifras. Se resolvieron **reorganizando la Fase 2**, no relajando los umbrales:

| Regla                 | Antes                      | Ahora                          | Cómo                                                                                                                                                               |
| --------------------- | -------------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `P2-CHILD-EQUAL`      | 23,46 vs 24,04 m² · Δ 0,58 | 23,46 vs 23,22 m² · Δ **0,24** | La suite de hijo 2 gira: el dormitorio pasa de 6,50 × 4,00 a 4,60 × 5,60 brutos y el baño se coloca al costado, como en hijo 1. Tolerancia ±1,00 m² por **D-042**. |
| `P2-CHILD-PROPORTION` | 1,04:1 vs **1,62:1**       | 1,04:1 vs **1,23:1**           | El giro elimina la habitación alargada. Ambas por debajo del límite de 1,35:1.                                                                                     |
| `P2-CIRC-MIN`         | 0,85 m libres              | **1,25 m** libres              | El vestíbulo de obra pasa de 1,00 a 1,40 m brutos.                                                                                                                 |

El espacio para ensanchar el vestíbulo salió de la propia reorganización, no de restárselo
a los baños: al girar la suite de hijo 2, la franja de fondo dejó de necesitar los 2,00 m
de baño en toda su longitud.

### Lo que sigue abierto

| Regla               | Lectura                                                                                                                                                                                                                                                                                                                                                    |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `P2-MASTER-PROGRAM` | Vestidor 10,2 m² brutos frente a 15–16; baño principal 13,4 frente a 17–18. **No es corregible dentro de la planta:** la banda del principal mide 7,40 × 11,00 = 81,4 m² y la escalera ocupa 16,2, de modo que quedan 65,2 m² para un programa que pide 76. O baja el programa, o crece el P2, o la escalera sale de esa huella. Decisión del propietario. |
| `LIFE-EGRESS-2`     | Segunda salida independiente sujeta a concepto profesional de incendio (D-021, D-028). Puede mover la escalera y con ella el núcleo y el gran muro.                                                                                                                                                                                                        |

### Reserva de método

Un «PASS» significa que el modelo es internamente coherente, respeta las decisiones
registradas y cumple los mínimos declarados por el propio expediente. **No** significa
conformidad normativa ni aptitud para construir.

## Archivos

- `planos/conceptual_v0.3_b06_p2/DH-ARQ-PLN-002-R05_P2-DETALLADA.svg`
- `planos/conceptual_v0.3_b06_p2/DH-ARQ-DIA-001-R05_LOGICA-EGRESO-P2.svg`
- `planos/conceptual_v0.3_b06_p2/compliance.json`

Se regeneran con `python dreamhouse/generate_p2_b06.py` usando
`dreamhouse/p2_b06.json` como fuente paramétrica.

## Próxima precisión requerida

1. Detalles 1:25 de los cuatro baños y sauna.
2. Planta de cielos, iluminación, detección y ventilación.
3. Diagrama de shafts alineado con PB y cálculo de agua caliente simultánea.
4. Concepto profesional de incendio y decisión sobre segunda salida.
5. Modulación estructural del entrepiso y control de vibración/acústica.
6. Cuadro de vanos P2 con control solar definido después de conocer orientación/predio.
