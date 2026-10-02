# Matriz inicial de riesgos

**Estatus:** activa; revisar en cada puerta de fase  
**Versión:** 0.5
**Fecha:** 2026-10-02
**Documentation update source:** D-084 workflow, CF-013 and current source/consumer audit;
existing qualitative ratings remain unchanged.

Escala cualitativa: probabilidad (P) e impacto (I): baja, media, alta, crítica.

| ID   | Riesgo                                                         | P     | I       | Respuesta inicial                                                         |
| ---- | -------------------------------------------------------------- | ----- | ------- | ------------------------------------------------------------------------- |
| R-01 | Predio inexistente/incompatible                                | Alta  | Crítica | Debida diligencia y G1 antes de congelar diseño                           |
| R-02 | Target v0.2 subestima costo real                               | Alta  | Crítica | Cantidades, prediseño y cotizaciones en PE-1/G3                           |
| R-03 | Clasificación de uso/incendio contradice PB totalmente abierta | Media | Crítica | Consulta temprana y estrategia especializada                              |
| R-04 | Estructura de 18 m + P2 exige apoyos/costo no previstos        | Alta  | Alta    | Comparar sistemas y ejes antes de v0.3 final                              |
| R-05 | Suelo/drenaje encarece cimentación y losa                      | Media | Crítica | Geotecnia y topografía antes de compra/diseño                             |
| R-06 | Condensación, infiltración o puentes térmicos                  | Alta  | Alta    | Verificar P2-W05 con higrotermia climática, detalles de vanos y mock-up   |
| R-07 | Aire del taller/vehículo afecta vivienda                       | Alta  | Crítica | Inventario de procesos, captura en fuente y make-up air                   |
| R-08 | Ruido/reverberación invade P2                                  | Alta  | Alta    | Seleccionar/ensayar P2-W01B/W04R, puertas, sellos, vanos y flancos; no inferir desempeño del espesor |
| R-09 | Potencia/servicios del predio insuficientes                    | Media | Alta    | Disponibilidad escrita y estudio de cargas temprano                       |
| R-10 | Egreso desde P2 o rutas interferidas por taller                | Media | Crítica | Estrategia de evacuación desde anteproyecto                               |
| R-11 | Redes ocultas colisionan con estructura visible                | Alta  | Alta    | Coordinación 3D/rutas antes de fabricar/cerrar                            |
| R-12 | Portones/vidrio especiales dominan plazo                       | Media | Alta    | Selección temprana, submittals y compras críticas                         |
| R-13 | Lift cambia después de diseñar losa                            | Media | Alta    | Congelar ficha antes de cimentación                                       |
| R-14 | Agua/saneamiento rural no presupuestado                        | Media | Alta    | Resolver con el predio y separar costo externo                            |
| R-15 | Sauna/jacuzzi causan humedad/carga/fugas                       | Media | Alta    | Sauna coordinado; jacuzzi solo tras decisión técnica                      |
| R-16 | Home Assistant se vuelve punto único de fallo                  | Media | Alta    | Separar vida segura y controles locales autónomos                         |
| R-17 | Cambios tardíos del propietario/equipos                        | Media | Alta    | Congelaciones por fase y control de cambios                               |
| R-18 | Losa industrial falla estética/funcionalmente                  | Media | Alta    | Mockup, especificación integral, juntas y curado                          |
| R-19 | Logística rural/izaje/transporte no considerada                | Media | Alta    | Incluir acceso y logística en lote, diseño y ofertas                      |
| R-20 | Documentos conceptuales se usan para construir                 | Media | Crítica | Sellos de estado, control documental y G5                                 |
| R-21 | Fase 2 cuesta más por tiempo/remobilización/protecciones       | Alta  | Alta    | Presupuesto separado, escalamiento y reserva antes de F1                  |
| R-22 | Rough-ins o shell diferido se degradan/quedan obsoletos        | Media | Alta    | Acceso, tapas, identificación, control ambiental e inspección antes de F2 |
| R-23 | Fase 2 queda fuera de vigencia de licencia                     | Media | Alta    | Cronograma legal, alertas y consulta con autoridad competente             |

## Riesgos críticos que bloquean avance

R-01, R-02, R-03, R-05, R-07, R-10 y R-20. R-21/R-23 deben incluirse en la decisión de
financiación y calendario. Cada uno necesita responsable profesional,
fecha objetivo, evidencia de cierre y riesgo residual antes de la puerta correspondiente.

## Connected coordination controls — D-084

The implemented [workflow](connected_coordination_workflow.md) supplies evidence for
existing risks; software checks do not close the risks themselves.

| Existing risk | Current control/evidence | Remaining action and responsible role |
| --- | --- | --- |
| R-04 / R-11 — Structural and spatial interfaces | Known extents are checked; plan reservations and missing heights remain OPEN; affected entity pairs retain source references | Architect/structural/MEP designers must supply supported member/route geometry and actual engineering checks; the broader discipline adapters remain pending |
| R-10 — Egress and access | CF-011/CF-012 remain visible; CF-013 documents inconsistent PB door anchors | Architect and fire/egress reviewer must reconcile door endpoints/heights, stair discharge and rescue roles before relying on route clearance |
| R-17 — Late changes | Pinned study deltas, explicit source ownership, full candidate regeneration and stale-artifact checks | Review the proposed change and its affected discipline evidence; the 27 published consumers still require controlled migration |
| R-20 — Schematic evidence used for construction | Read-only generated views, authority labels and separate candidate/publication states | Publication coordinator must prevent candidate or historical results from being described as a construction-approved current issue |
| R-02 — Unsupported cost certainty | Workstation glazing mapped separately; nominal quantities and unpriced/ineligible rates explicit | Cost planner must reconcile scope, measurement basis, products and comparable quotations before budget adoption |

The [source inventory](connected_source_inventory.md) records which current views remain
outside the shared model. The implementation has no installed/commissioned asset record
yet; R-21–R-23 retain their original construction-phase controls. No risk rating or closure
is changed by this documentation reconciliation.

## Regla de actualización

Para cada riesgo añadir: causa, evento, consecuencia, dueño, acción, plazo, costo de
respuesta, evidencia, estado y riesgo residual. Un riesgo no se cierra porque “parece poco
probable”.
