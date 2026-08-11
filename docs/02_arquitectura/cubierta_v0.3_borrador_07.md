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

> **Corrección 2026-08-11 (hallazgo H-01).** La reemisión R06 corrigió la escala vertical
> pero dejó la **fachada posterior espejada** respecto de la frontal y de los dos laterales,
> y la planta de cubierta R07 heredó ese espejo con la flecha de subida apuntando al lado
> bajo. Tres láminas cotaban el borde Y=0 a 7,20 m y dos a 7,80 m: la cubierta dibujada no
> era un faldón sino una superficie alabeada. El corte de claraboyas tenía además un error
> de signo que dibujaba el alero alto a 6,60 m.
>
> La causa raíz era que cada lámina declaraba los aleros por su cuenta. Ahora el sentido
> vive **una sola vez**, en `roof` de `dreamhouse/pb_b05.json`, y las cinco láminas lo
> derivan de ahí; el chequeo `RL-ROOF-DIRECTION` verifica que b08 no se separe de esa
> fuente. **Invertir el faldón es cambiar `roof.low_side` y regenerar**, no editar cinco
> archivos. La reversibilidad que este documento exige es ahora una operación de un dato.

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
