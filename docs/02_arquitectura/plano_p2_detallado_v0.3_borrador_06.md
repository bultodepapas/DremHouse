# Segundo piso detallado v0.3 — borrador 06

**Estatus:** anteproyecto / hipótesis activa de coordinación; no apto para construir  
**Versión:** 0.3-borrador-06-P2  
**Fecha:** 2026-08-11  
**Fuente:** constitución, programa activo, b04/R03 y ventanas de fachada b05/R04.  
**Aprobación pendiente:** propietario, arquitecto coordinador y consultores.

## Objeto

Precisar la lógica del P2 dentro de su envolvente nominal de **18,00 × 15,00 m**, sin
convertirlo en mezzanine abierto. La emisión coordina privacidad, jerarquía de la suite
principal, cuatro baños privados, ventanas altas, zona wellness y ejecución F1/F2.

## Correcciones de arquitectura

- El dormitorio principal deja de ser una franja angosta: se plantea en **7,40 × 4,20 m
  = 31,1 m² brutos**, con paño dominante de 5,50 m en el **lateral A** y paño posterior
  secundario de 2,50 m (corrección H-06: antes se describía al revés).
- Los dormitorios de hijos tienen **26,0 m² brutos exactos** cada uno, pero al descontar
  espesores reales quedan **23,46 m² (H1) y 24,04 m² (H2)**: la hard rule 9 **todavía no se
  cumple**. Ver «Resultado de control».
- La llegada de escalera, el hall, la galería interior y el mini deck son recintos
  cerrados acústicamente hacia la nave. No existe corredor abierto tipo hotel.
- La Fase 2 permanece detrás de una frontera única en Y=11,00 m. El cierre temporal debe
  resolver polvo, ruido, incendio e instalaciones durante la ocupación de F1.
- Los baños H2 y huéspedes recuperan **2,00 m de profundidad bruta**; siguen siendo
  compactos y requieren un detalle 1:25 antes de congelarse.
- El wellness ocupa 18,0 m² brutos —**15,6 m² netos**, por debajo de la reserva mínima de
  16 m²— e integra sauna familiar, ducha y zona de relajación.
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

**Estado al 2026-08-11: 7 PASS · 3 FAIL · 3 OPEN.** La emisión **no cierra**, y eso es
deliberado.

Hasta esta fecha el modelo teselaba la envolvente completa: los veintidós recintos sumaban
exactamente 270,00 m², es decir, declaraban áreas que no dejaban sitio para un solo muro
(hallazgo H-04). Al incorporar los espesores que este mismo documento declara —0,18 m de
envolvente, 0,20 m en húmedos y escalera, 0,15 m en divisiones— la superficie neta real
resulta ser **239,2 m²**, un 11 % menos que lo rotulado. Tres condiciones que antes
«pasaban» dejaron de hacerlo:

| Regla | Estado | Lectura |
|---|---|---|
| `P2-AREA-CLOSURE` | PASS | 239,2 m² netos ≤ 258,2 m² de interior útil. El modelo ya deja sitio a sus muros. |
| `P2-CHILD-EQUAL` | **FAIL** | H1 23,46 m² vs. H2 24,04 m² (Δ 0,58 m²). Hard rule 9 incumplida. |
| `P2-CIRC-MIN` | **FAIL** | `F2-HALL` da 0,85 m libres frente al mínimo propio de 1,20 m. |
| `P2-WELLNESS` | **FAIL** | 15,6 m² netos frente a los 16 m² de reserva mínima. |
| `P2-CHILD-PROPORTION` | OPEN | H1 1,04:1 vs. H2 1,62:1. Igualar área no iguala la habitación. |
| `P2-MASTER-PROGRAM` | OPEN | Vestidor 9,0 m² frente a 15–16; baño principal 12,0 m² frente a 17–18. |
| `LIFE-EGRESS-2` | OPEN | Segunda salida sujeta a concepto profesional de incendio. |

**Estos tres FAIL no se corrigen moviendo cifras: exigen una decisión de planta.** Y no son
independientes entre sí. Llevar `F2-HALL` a 1,20 m dentro de la envolvente actual obliga a
restar 0,20 m a los dormitorios de la Fase 2 o a los baños de 2,00 m, que ya son el punto
más comprometido de la planta. Igualar los dormitorios de hijos con un ajuste de pocos
centímetros haría pasar el chequeo sin resolver la diferencia real de proporción, que es lo
que un hijo notaría al entrar. La revisión de coordinación recomienda **no** hacer ninguna
de las dos cosas hasta que se decida la vía estructural del entrepiso, porque una planta
sin apoyos interiores admite un reparto distinto del fondo.

Se mantiene **abierta** la segunda salida independiente del P2: la escalera protegida y su
descarga posterior no demuestran por sí solas cumplimiento de recorridos, ocupación o
evacuación.

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
