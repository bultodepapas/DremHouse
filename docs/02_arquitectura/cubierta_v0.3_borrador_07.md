# Cubierta v0.3 — borrador 07

**Estatus:** anteproyecto / corrección de representación; no apto para construir  
**Versión:** 0.3-borrador-07-CUBIERTA  
**Fecha:** 2026-08-11  
**Fuente:** concepto consolidado §§27–29, constitución y esquema estructural E0.  
**Aprobación pendiente:** propietario, arquitecto, estructura, envolvente e hidráulica.

## Hallazgo

El propietario identificó correctamente una inconsistencia. Las elevaciones R04 y las
secciones anteriores reducían el desnivel hasta hacerlo casi imperceptible y sugerían una
pendiente longitudinal sobre los 36 m. La fuente canónica define otra lógica:

- una sola cubierta exterior continua y simple;
- **un faldón**, sin cumbrera central ni gesto a dos aguas;
- lado bajo interior aproximado: **7,20 m**;
- lado alto interior aproximado: **7,80 m**;
- desnivel transversal aproximado: **0,60 m sobre 18,00 m = 3,33 %**.

Por tanto, los laterales de 36 m deben mostrar aleros horizontales: uno bajo y otro alto.
El frente y el posterior son los que deben mostrar claramente el plano inclinado.

## Hipótesis de coordinación

Para poder dibujar las cuatro caras, R06 denomina provisionalmente el lateral A como lado
bajo y el B como lado alto. Esta asignación es **reversible**: no se congela hasta conocer
predio, vistas, vientos, orientación, punto de descarga, drenaje exterior y estrategia de
mantenimiento.

El valor 3,33 % tampoco es todavía una especificación contractual. La pendiente final debe
cumplir el sistema de panel seleccionado, longitud máxima de faldón, solapes, tolerancias,
deformación, lluvia de diseño y garantía del fabricante. No se agregan cubiertas
secundarias, limatesas, lucernarios ni cumbrera ventilada.

## Drenaje y borde

- La totalidad del agua se concentra en el alero bajo; canal, rebose de emergencia,
  bajantes y descarga deben dimensionarse hidráulicamente.
- El alero alto requiere remate contra viento y lluvia, no una cumbrera central.
- Las penetraciones deben minimizarse y agruparse; ventilaciones sanitarias y extracción
  se coordinarán sin convertir la cubierta en un campo de equipos.
- Los cielos de dormitorios permanecen horizontales a aproximadamente 3,00–3,10 m,
  dejando un plenum variable bajo el faldón.

## Archivos corregidos

- `planos/conceptual_v0.3_b07_cubierta/DH-ARQ-SEC-001-R06_LONGITUDINAL-CUBIERTA.svg`
- `planos/conceptual_v0.3_b07_cubierta/DH-ARQ-SEC-002-R06_TRANSVERSAL-CUBIERTA.svg`
- `planos/conceptual_v0.3_b07_cubierta/DH-ARQ-ELE-001-R06_FACHADA-FRONTAL-CUBIERTA.svg`
- `planos/conceptual_v0.3_b07_cubierta/DH-ARQ-ELE-002-R06_FACHADA-POSTERIOR-CUBIERTA.svg`
- `planos/conceptual_v0.3_b07_cubierta/DH-ARQ-ELE-003-R06_FACHADA-LATERAL-A-CUBIERTA.svg`
- `planos/conceptual_v0.3_b07_cubierta/DH-ARQ-ELE-004-R06_FACHADA-LATERAL-B-CUBIERTA.svg`

Se regeneran con `python dreamhouse/generate_roof_b07.py`.
