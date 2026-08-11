# Plano conceptual v0.3 — borrador 02

**Estatus:** anteproyecto / hipótesis; no apto para construir  
**Versión:** 0.3-borrador-02  
**Fecha:** 2026-08-11  
**Fuente:** constitución activa, programa v0.2, relaciones espaciales y borrador 01.  
**Aprobación pendiente:** propietario, arquitecto coordinador y consultores.

## Avance de esta emisión

El borrador 02 reemplaza la zonificación del borrador 01 como propuesta de trabajo, sin
congelar geometría. Incorpora mobiliario y equipos de control, subdivisión interna de las
cuatro suites, baños y closets, wellness, lavandería, hall, corte longitudinal y fachada
frontal.

## Hipótesis arquitectónica principal

Se reordena el núcleo posterior PB manteniendo exactamente sus reservas y 81 m² totales:

`bodega → baño PB → escalera → homelab → pantry`, medidos de izquierda a derecha sobre
el ancho representado en planta.

La escalera central mejora la llegada al P2, permite un hall compacto y elimina la suite
principal fragmentada del borrador 01. Este orden abre una alternativa para D-019 y la
coordinación MEP; no es todavía una decisión adoptada.

## Áreas de control resultantes

| Conjunto | Área bruta de reserva |
|---|---:|
| Suite hijo 1 | 38,00 m² |
| Suite hijo 2 | 38,00 m² |
| Suite huéspedes | 33,00 m² |
| Suite principal | 75,01 m² |
| Núcleo PB | 81,00 m² |

La igualdad se comprueba sobre reservas brutas de suite. La regla congelada exige igualdad
del área útil de los dormitorios; esa comprobación se hará al introducir espesores reales.

## Lectura espacial

- PB mantiene técnica → respiración → sala → doméstica → núcleo.
- El eje peatonal de 4,00 m sigue siendo perceptual y no un corredor construido.
- La isla se reduce a 4,00 × 1,30 m como alternativa más plausible; CF-006 sigue abierta.
- El P2 coloca dormitorios sobre perímetro y concentra baños/closets como amortiguadores.
- La zona Fase 2 permanece identificada mediante línea discontinua: hijo 2, huéspedes y
  wellness; su frontera real de obra todavía debe resolverse.

## Limitaciones conocidas

- Los polígonos representan caras nominales, no muros con espesor.
- Puertas interiores, giros, ventanas y aparatos sanitarios detallados son el próximo paso.
- La escalera solo reserva 4,50 × 3,60 m: falta calcular huellas, contrahuellas, descansos,
  gálibo, barandas y egreso.
- No existe predio, norte, asoleación, vista ni norma municipal aplicable.
- La retícula de 6 m es referencia gráfica, no sistema estructural aprobado.
- El corte usa +3,80 m y 7,50 m como valores de estudio.

## Entregables

- `planos/conceptual_v0.3_b02/DH-ARQ-PLN-001-R01_PB.svg`
- `planos/conceptual_v0.3_b02/DH-ARQ-PLN-002-R01_P2.svg`
- `planos/conceptual_v0.3_b02/DH-ARQ-SEC-001-R01_LONGITUDINAL.svg`
- `planos/conceptual_v0.3_b02/DH-ARQ-ELE-001-R01_FRONTAL.svg`
- `planos/conceptual_v0.3_b02/compliance.json`

Todos se regeneran desde `dreamhouse/project_b02.json` mediante
`python dreamhouse/generate_detailed_plans.py`.
