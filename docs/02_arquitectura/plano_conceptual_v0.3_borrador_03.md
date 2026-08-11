# Plano conceptual v0.3 — borrador 03

**Estatus:** anteproyecto / hipótesis; no apto para construir  
**Versión:** 0.3-borrador-03  
**Fecha:** 2026-08-11  
**Fuente:** borrador 02 y documentación canónica activa.  
**Aprobación pendiente:** propietario, arquitecto coordinador y consultores.

## Objeto de la revisión

Comprobar uso y habitabilidad básica mediante puertas, giros, ventanas provisionales,
aparatos sanitarios, escalera esquemática, cadenas de cotas y sección transversal. El
borrador conserva la geometría del 02 y añade una capa de detalle versionada en
`dreamhouse/details_b03.json`.

## Hallazgos de la auditoría visual del borrador 02

1. Las áreas y zonificación eran coherentes, pero no se demostraba cómo entrar a los
   recintos ni cómo conservar privacidad.
2. Los baños existían como superficies sin aparatos; no podía evaluarse su capacidad.
3. Los dormitorios no probaban luz exterior.
4. La caja de escalera no demostraba que pudiera alojar una configuración razonable.
5. El corte longitudinal no hacía visible la dificultad estructural de cubrir 18 m y
   soportar el P2 sin columnas arbitrarias.

## Respuestas incorporadas

- Cinco puertas en el núcleo PB y once accesos principales/interiores en P2.
- Ventanas provisionales para las cuatro suites; su posición final depende del predio.
- Ducha e inodoro en cada baño privado; doble ducha y vanity en baño principal.
- Escalera en U esquemática, con aproximadamente 21 contrahuellas para salvar +3,80 m.
- Cadenas de cotas de las bandas longitudinales y del vacío/P2.
- Corte transversal bajo P2 con luz completa de 18,00 m, sin adoptar columnas interiores.

## Advertencias de diseño

- Las puertas se representan con anchos preliminares de 0,80–1,00 m; falta verificar
  accesibilidad, evacuación, interferencias y herrajes.
- Las ventanas azules son reservas, no decisiones de fachada. Las dos alternativas de
  vidrio en PB no se construirían simultáneamente sin justificación de orientación.
- Los aparatos prueban cabida geométrica, no cumplimiento de distancias reglamentarias.
- La escalera requiere cálculo detallado de huella, contrahuella, descanso, gálibo,
  barandas, ancho útil y comportamiento en emergencia.
- El corte transversal es deliberadamente exigente: la estructura debe demostrar la luz
  de 18 m y el soporte del P2; el dibujo no selecciona pórtico, cercha ni perfiles.

## Verificación automática

La emisión pasa doce controles: nueve heredados del borrador 02 y tres nuevos sobre
accesos representados, ventanas exteriores de suites y cuatro duchas privadas.

## Archivos

- `planos/conceptual_v0.3_b03/DH-ARQ-PLN-001-R02_PB.svg`
- `planos/conceptual_v0.3_b03/DH-ARQ-PLN-002-R02_P2.svg`
- `planos/conceptual_v0.3_b03/DH-ARQ-SEC-001-R02_LONGITUDINAL.svg`
- `planos/conceptual_v0.3_b03/DH-ARQ-SEC-002-R02_TRANSVERSAL.svg`
- `planos/conceptual_v0.3_b03/DH-ARQ-ELE-001-R02_FRONTAL.svg`
- `planos/conceptual_v0.3_b03/compliance.json`

Se regeneran mediante `python dreamhouse/generate_b03.py`.

## Próxima revisión recomendada

El siguiente avance no debe añadir decoración. Debe introducir espesores constructivos,
áreas netas, puertas sin colisión, baños dimensionados, retícula/apoyos estructurales y
una prueba formal de egreso desde P2. Después podrá evaluarse orientación y fachada.
