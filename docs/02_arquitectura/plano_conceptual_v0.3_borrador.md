# Plano conceptual v0.3 — primer borrador paramétrico

**Estatus:** borrador / hipótesis; no apto para construir  
**Versión:** 0.3-borrador-01  
**Fecha:** 2026-08-11  
**Fuente:** programa v0.2, constitución activa y relaciones espaciales.  
**Responsables de aprobación pendientes:** propietario y arquitecto coordinador.

## Propósito de esta emisión

Probar que la envolvente nominal, las cuatro bandas de PB, el núcleo de 81 m² y el
programa global de P2 pueden representarse en un modelo reproducible. Esta emisión es una
zonificación inicial: todavía no define muros, espesores, estructura, puertas interiores,
baños dentro de suites, fachadas laterales, shafts, evacuación ni mobiliario definitivo.

## Hipótesis nuevas de dibujo

- Origen en esquina frontal izquierda; X avanza hacia el fondo y Y hacia la derecha.
- Car project a la izquierda y RC/DIY a la derecha. D-023 continúa abierta.
- Eje peatonal central de 4,00 m representado como territorio perceptual, no como recinto.
- Sala centrada tras una franja de respiración de 2,00 m.
- Comedor y cocina ocupan el inicio del territorio bajo P2.
- P2 usa una zonificación compacta por áreas objetivo, con servicios próximos a la
  escalera y wellness agrupado con la zona diferida de Fase 2.
- La suite principal se dibuja como territorio compuesto de 76 m²; su distribución
  interna queda pendiente.

Estas hipótesis no modifican las decisiones activas. Deben evaluarse contra estructura,
egreso/incendio, privacidad, luz, acústica, MEP, mobiliario y predio.

## Archivos emitidos

- `planos/conceptual_v0.3/DH-ARQ-PLN-001-R00_PB.svg`
- `planos/conceptual_v0.3/DH-ARQ-PLN-002-R00_P2.svg`
- `planos/conceptual_v0.3/reporte_cumplimiento.md`
- `planos/conceptual_v0.3/compliance.json`
- `planos/conceptual_v0.3/manifest.json`

La entrada canónica de esta emisión es `dreamhouse/project.json`; los planos son salidas
regenerables mediante `python dreamhouse/generate_plans.py`.

## Revisión requerida para el siguiente borrador

1. Confirmar o espejar car bay y RC/DIY.
2. Dibujar lift, vehículo, bancos, avión RC, escritorios y muebles a escala real.
3. Resolver P2 internamente: dormitorio, baño, closet, puertas, luz y aislamiento.
4. Verificar escalera, egreso y posible segunda ruta exigida.
5. Introducir espesores y retícula estructural sin sacrificar PB abierta.
6. Coordinar shafts y apilamiento sanitario.
7. Probar la frontera continua de Fase 2.
