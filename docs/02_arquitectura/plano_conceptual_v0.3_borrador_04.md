# Plano conceptual v0.3 — borrador 04

**Estatus:** anteproyecto / hipótesis activa de coordinación; no apto para construir  
**Versión:** 0.3-borrador-04  
**Fecha:** 2026-08-11  
**Fuente:** auditoría integral del borrador 03, constitución y documentos activos.  
**Aprobación pendiente:** propietario, arquitecto coordinador y consultores.

## Objeto

Corregir problemas de lógica detectados en R02 sin alterar las hard rules: circulación,
continuidad de la suite principal, separación constructiva F1/F2, descarga posterior,
cabida de escalera, equipamiento de cocina y verificaciones automáticas.

## Cambios principales

### Planta baja

- El sofá sale del eje peatonal libre de 4,00 m.
- La isla de prueba se racionaliza a 3,60 × 1,20 m y el muro equipado se traslada al
  borde exterior de la cocina, liberando los accesos del núcleo.
- La bodega representa salida posterior propia.
- La caja de escalera representa descarga posterior directa. Su condición protegida,
  resistencia, ventilación y herrajes siguen sujetos al concepto de incendio.
- Se mantienen los 81 m² nominales del núcleo y los tres accesos frontales exactos.

### Segundo piso

- La suite principal pasa a un territorio conectado de 76,24 m² nominales. La secuencia
  propuesta es hall → vestíbulo → vestidor/baño/dormitorio, con estar propio conectado.
- La caja de escalera conserva 4,50 × 3,60 m = 16,20 m² y queda íntegramente en Fase 1.
- La Fase 2 se concentra detrás de una frontera transversal continua en Y=11,00 m:
  vestíbulo aislable, hijo 2, huéspedes, shaft de apoyo y wellness/sauna.
- Los dormitorios de hijos conservan 26,00 m² útiles nominales y las suites 38,00 m²
  brutos cada una. La equivalencia cualitativa aún debe probarse con espesores y fachada.
- Los cuatro baños privados representan ducha, inodoro y lavamanos.

## Resultado de cumplimiento

La emisión registra **15 PASS, 0 FAIL y 1 OPEN**. El asunto abierto es la necesidad de
una segunda salida independiente desde P2. La descarga posterior de la escalera mejora
la estrategia, pero no sustituye la clasificación de uso, el cálculo de recorridos ni el
concepto profesional de protección contra incendio.

Los controles nuevos verifican:

- igualdad nominal de dormitorios y suites de hijos;
- ausencia de solapes y permanencia dentro de la envolvente;
- localización completa de Fase 2 detrás de una frontera única;
- salidas posteriores de bodega y escalera;
- aparatos básicos en cuatro baños privados;
- continuidad territorial de la suite principal;
- eje peatonal sin equipamiento superpuesto.

## Archivos

- `planos/conceptual_v0.3_b04/DH-ARQ-PLN-001-R03_PB.svg`
- `planos/conceptual_v0.3_b04/DH-ARQ-PLN-002-R03_P2.svg`
- `planos/conceptual_v0.3_b04/DH-ARQ-SEC-001-R03_LONGITUDINAL.svg`
- `planos/conceptual_v0.3_b04/DH-ARQ-SEC-002-R03_TRANSVERSAL.svg`
- `planos/conceptual_v0.3_b04/DH-ARQ-ELE-001-R03_FRONTAL.svg`
- `planos/conceptual_v0.3_b04/compliance.json`

Se regeneran mediante `python dreamhouse/generate_b04.py`. Los datos diferenciales están
en `dreamhouse/revision_b04.json`; el modelo base v0.2 se preserva.

## Límites y siguiente puerta

R03 no congela espesores, estructura, fachada ni cumplimiento normativo. Antes de una
revisión R04 se requieren: predimensionamiento de estructura/entrepiso, concepto de
incendio y egreso, shafts coordinados, baños con distancias reglamentarias, mobiliario
real, envolvente según predio y medición económica del cambio.
