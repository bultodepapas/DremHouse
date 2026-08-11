# Claraboyas sobre talleres v0.3 — borrador 08

**Estatus:** anteproyecto / hipótesis activa solicitada por el propietario; no apto para construir  
**Versión:** 0.3-borrador-08-CLARABOYAS  
**Fecha:** 2026-08-11  
**Fuente:** instrucción del propietario, cubierta b07 y programa de talleres.  
**Aprobación pendiente:** propietario, arquitectura, estructura, envolvente e hidráulica.

## Decisión espacial

Se incorporan **dos claraboyas de vidrio iguales**, una sobre el taller del carro y otra
sobre el taller RC/aviones. Cada reserva mide **2,40 × 4,80 m = 11,52 m²**; el área total
de vidrio cenital es **23,04 m²**.

Se prefieren dos eventos separados frente a una franja continua porque:

- llevan luz directamente a ambos territorios de trabajo;
- preservan el eje peatonal central y la lectura de la cubierta única;
- reducen el tamaño individual de los vidrios y permiten repetir sistema;
- pueden coordinarse dentro de un módulo estructural sin cortar pórticos;
- limitan la propagación de una eventual falla de estanqueidad.

La posición X=2,40–4,80 m dentro de la primera crujía de 6 m es una reserva preliminar.
No autoriza cortar correas ni modificar un pórtico sin cálculo.

## Desempeño mínimo a estudiar

- Unidad de vidrio aislante con hoja interior laminada de seguridad y retención mecánica.
- Hoja exterior templada y ensayada, con control solar o frita cerámica.
- Curb elevado, aislado y drenado; altura conceptual mínima de 0,20 m.
- Continuidad de barreras de aire, vapor, agua y aislamiento.
- Rebose secundario y ruta de agua visible hacia el alero bajo.
- Claraboyas fijas por defecto; la ventilación se resuelve separadamente.
- Acceso seguro para limpieza, inspección y sustitución del paño.

No se acepta como solución equivalente un domo acrílico simple ni un marco sin rotura
térmica. En clima frío, una claraboya mal resuelta puede producir condensación, goteo,
ruido de lluvia, pérdidas térmicas y filtraciones.

## Control de luz

La frita o serigrafía del **40–60 %** se conserva como rango de estudio, no como
especificación. El objetivo es luz difusa útil sobre talleres, evitando deslumbramiento,
reflejos en pantallas, calentamiento localizado y deterioro UV de vehículos o modelos.
La selección final depende de orientación, trayectoria solar y simulación lumínica.

## Archivos

- `planos/conceptual_v0.3_b08_claraboyas/DH-ARQ-PLN-CUB-001-R07_CLARABOYAS.svg`
- `planos/conceptual_v0.3_b08_claraboyas/DH-ARQ-SEC-CUB-003-R07_LUZ-CENITAL.svg`
- `planos/conceptual_v0.3_b08_claraboyas/DH-ARQ-DET-CUB-001-R07_BORDE-CLARABOYA.svg`
- `planos/conceptual_v0.3_b08_claraboyas/compliance.json`

Se regeneran con `python dreamhouse/generate_rooflight_b08.py`.
