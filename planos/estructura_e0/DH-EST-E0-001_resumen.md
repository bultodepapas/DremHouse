# Modelo E0 — comparación estructural (D-019)

**Estatus:** hipótesis de esquema · **NO APTO PARA CONSTRUIR**
**Fecha:** 2026-08-11 · **Revisión:** 0.1

> Altiplano de Boyaca sin nieve de diseno: NO se incluye carga de nieve. Gobiernan viento (NSR-10 B.6), sismo (Titulo A) y lluvia/drenaje. Envoltura responde al frio nocturno, condensacion e infiltracion, no a carga de nieve.

| Sistema × Modulación | Columnas | Viga/cercha | Pórticos | Acero total | kg/m² |
|---|---|---|---|---:|---:|
| M45 · PORTICO | HEA500 | IPE450 | 9 | **57.3 t** | 62.5 |
| M45 · PORTICO-T | HEA500 | IPE450 | 9 | **58.8 t** | 64.1 |
| M45 · PORTICO-F | HEA300 | IPE450 | 9 | **46.6 t** | 50.7 |
| M45 · CERCHA | HEA200 | IPE220 | 9 | **39.3 t** | 42.8 |
| M60 · PORTICO | HEA500 | IPE500 | 7 | **49.8 t** | 54.2 |
| M60 · PORTICO-T | HEA500 | IPE500 | 7 | **50.9 t** | 55.4 |
| M60 · PORTICO-F | HEA300 | IPE450 | 7 | **39.5 t** | 43.0 |
| M60 · CERCHA | HEA200 | IPE220 | 7 | **33.8 t** | 36.9 |
| M90 · PORTICO | HEA500 | IPE550 | 5 | **42.3 t** | 46.1 |
| M90 · PORTICO-T | HEA500 | IPE550 | 5 | **43.2 t** | 47.0 |
| M90 · PORTICO-F | HEA300 | IPE550 | 5 | **36.4 t** | 39.6 |
| M90 · CERCHA | HEA200 | IPE220 | 5 | **29.4 t** | 32.1 |

## Desglose por componente (t)

| Sistema × Modulación | Marcos principales | Entrepiso P2 (metaldeck) | Entrepiso P2 (staggered) | Entrepiso P2 (gran muro) | Secundaria | Total |
|---|---|---:|---:|---:|---:|---:|
| M45 · PORTICO | 39.5 | 10.3 | 3.8 | 6.1 | 7.5 | 57.3 |
| M45 · PORTICO-T | 41.0 | 10.3 | 3.8 | 6.1 | 7.5 | 58.8 |
| M45 · PORTICO-F | 28.7 | 10.3 | 3.8 | 6.1 | 7.5 | 46.6 |
| M45 · CERCHA | 21.5 | 10.3 | 3.8 | 6.1 | 7.5 | 39.3 |
| M60 · PORTICO | 32.6 | 9.6 | 3.8 | 6.1 | 7.5 | 49.8 |
| M60 · PORTICO-T | 33.8 | 9.6 | 3.8 | 6.1 | 7.5 | 50.9 |
| M60 · PORTICO-F | 22.3 | 9.6 | 3.8 | 6.1 | 7.5 | 39.5 |
| M60 · CERCHA | 16.7 | 9.6 | 3.8 | 6.1 | 7.5 | 33.8 |
| M90 · PORTICO | 24.8 | 10.0 | 3.8 | 6.1 | 7.5 | 42.3 |
| M90 · PORTICO-T | 25.6 | 10.0 | 3.8 | 6.1 | 7.5 | 43.2 |
| M90 · PORTICO-F | 18.8 | 10.0 | 3.8 | 6.1 | 7.5 | 36.4 |
| M90 · CERCHA | 11.9 | 10.0 | 3.8 | 6.1 | 7.5 | 29.4 |

## Entrepiso P2 — opciones comparadas

Tres esquemas sin columnas interiores en la zona doméstica (el metaldeck con apoyos intermedios NO es viable sin columnas en cocina/núcleo):
- **GRAN-MURO (preferido):** el gran muro de X=31,5 (núcleo) es portante y recibe el P2; 3 vigas longitudinales IPE450 de 10.5 m en el plenum (Y≈3/9/15) apoyan en la cercha de borde X=21 (luz 18 m, cordón HSS150x150x8) y en el muro; franja del núcleo con losa sobre el muro (luz 4.5 m). Acero ≈ 5.3 t, axial del muro ≈ 76.4 kN/m, fn del panel ≈ 10.4 Hz. El muro aporta núcleo de corte longitudinal.
- **STAGGERED:** cerchas de canto completo de 18 m ocultas en particiones; requiere re-articular las particiones del P2 (hoy no existe línea continua de 18 m).
- **METALDECK:** línea base; introduce columnas en cocina/núcleo.
- Staggered truss: 3 cerchas de 18 m de canto completo (≈ 3.0 m, d/L ≈ 0.167), paneles de losa de 5.0 m entre cerchas, cordones HSS100x100x6, flecha de cercha ≈ 0.02 m, frecuencia del panel ≈ 14.9 Hz (criterio DG11 ≥ 5 Hz).

## Objetivos de control (auditoría)

- Acero total realista: **30.0–45.0 t** (desglose v0.2: 28,35 t, subestimado).
- Equivalente: **31.0–48.0 kg/m²** sobre 918 m².

## Hallazgos del modelo E0 (11-08-2026)

1. **Los pórticos con bases articuladas quedan gobernados por la deriva de viento (H/200):** columnas HEA500 en las tres modulaciones (peso principal ≈ 30–40 t). El control de la auditoría (HEA300, 23–24 t) no cumple la deriva de servicio con el viento de hipótesis E0; es una decisión del ingeniero en E1 si relaja el límite o introduce arriostramiento/rigidización.
2. **El sistema de cerchas con columnas articuladas y arriostramiento pesa ≈ 36–40 t** (ahorro ≈ 30 % sobre pórticos) y resuelve la deriva con columnas HEA200; el costo extra de fabricación de la cercha debe cotizarse antes de decidir (E1, puerta PE-1).
3. **Pórtico atado (PORTICO-T):** el tirante entre los apoyos de la cercha queda casi inactivo (≈ 2 kN) porque la deriva de viento es un sway en la misma dirección de ambos muros; el tirante solo resiste la apertura de aleros por empuje gravitatorio, que aquí no gobierna. Añade peso (≈ 1,4 t/pórtico) sin beneficio de deriva: **no es competitivo en este caso de carga.** Su papel clásico (empuje de cubierta en edificios con grúa) no aplica.
4. **Pórtico con bases fijas (PORTICO-F):** es el control efectivo de deriva para el sistema de pórticos. Permite columna HEA300 con deriva ≈ 0,016–0,021 m (vs. HEA500 articulado) y un marco ≈ 27 % más liviano; el costo pasa a la cimentación (momento en la base).
5. **Entrepiso P2:** tres esquemas sin columnas interiores — METALDECK (12,0 t, con columnas en cocina/núcleo), STAGGERED (≈ 3,8 t, exige re-articular particiones) y **GRAN-MURO (≈ 6 t, preferido): el gran muro de X=31,5 trabaja como apoyo del P2**, con 3 vigas longitudinales en el plenum + cercha de borde X=21; sin re-articular particiones y con el muro actuando como núcleo de corte longitudinal. El peso de la losa de deck profundo se verifica en E1.
6. **Cubierta de un solo faldón ≈ 1:30:** la flecha de la viga de cubierta queda controlada por resistencia (viento/succión), no por flecha, con IPE450–IPE550 según modulación.

## Supuestos críticos de este modelo

- Cargas y combinaciones son **hipótesis de ingeniero**, versionadas en `structure_system.json`; no es biblioteca NSR-10.
- Sin carga de nieve (Boyacá). Viento y sismo como hipótesis E0 hasta definir municipio.
- Pórticos con bases articuladas por defecto; PORTICO-T añade tirante de alero; PORTICO-F empotra las bases.
- Entrepiso P2: METALDECK (viguetas + vigas de 18 m + apoyos intermedios) vs. STAGGERED (cerchas escalonadas sin columnas interiores).
- Factor de detalle 15 % y desperdicio 5 %; perfiles de stock IPE/HEA/HSS.
- Cada resultado debe ser revisado por el ingeniero estructural antes de cruzar PE-1.
