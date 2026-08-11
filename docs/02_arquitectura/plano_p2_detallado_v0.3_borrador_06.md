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
  = 31,1 m² brutos**, con ventana posterior de 5,50 m y paño lateral de 2,50 m.
- Los dormitorios de hijos conservan exactamente **26,0 m² brutos** cada uno y ventanas
  casi piso a techo; la igualdad neta se deberá recalcular al definir muros y trasdosados.
- La llegada de escalera, el hall, la galería interior y el mini deck son recintos
  cerrados acústicamente hacia la nave. No existe corredor abierto tipo hotel.
- La Fase 2 permanece detrás de una frontera única en Y=11,00 m. El cierre temporal debe
  resolver polvo, ruido, incendio e instalaciones durante la ocupación de F1.
- Los baños H2 y huéspedes recuperan **2,00 m de profundidad bruta**; siguen siendo
  compactos y requieren un detalle 1:25 antes de congelarse.
- El wellness ocupa 18,0 m² brutos e integra sauna familiar, ducha y zona de relajación.
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

La emisión automatizada debe cerrar sin fallos geométricos. Se mantiene **abierta** la
segunda salida independiente del P2: la escalera protegida y su descarga posterior no
demuestran por sí solas cumplimiento de recorridos, ocupación o evacuación.

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
