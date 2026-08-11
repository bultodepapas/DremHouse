# Modelo E0 — comparación estructural (D-019)

**Estatus:** hipótesis de esquema · **NO APTO PARA CONSTRUIR**
**Fecha:** 2026-08-11 · **Revisión:** 0.1

> Altiplano de Boyaca sin nieve de diseno: NO se incluye carga de nieve. Gobiernan viento (NSR-10 B.6), sismo (Titulo A) y lluvia/drenaje. Envoltura responde al frio nocturno, condensacion e infiltracion, no a carga de nieve.

| Sistema × Modulación | Columnas | Viga/cercha | Pórticos | Acero total (metaldeck) | Total (gran muro) | kg/m² |
|---|---|---|---|---:|---:|---:|
| M45 · PORTICO | HEA500 | IPE450 | 9 | **59.4 t** | 52.9 t | 57.6 |
| M45 · PORTICO-T | HEA500 | IPE450 | 9 | **60.9 t** | 54.4 t | 59.2 |
| M45 · PORTICO-F | HEA300 | IPE450 | 9 | **48.6 t** | 42.1 t | 45.9 |
| M45 · CERCHA | HEA200 | IPE220 | 9 | **41.4 t** | 34.9 t | 38.0 |
| M60 · PORTICO | HEA500 | IPE500 | 7 | **52.9 t** | 46.0 t | 50.1 |
| M60 · PORTICO-T | HEA500 | IPE500 | 7 | **54.1 t** | 47.2 t | 51.4 |
| M60 · PORTICO-F | HEA300 | IPE450 | 7 | **42.6 t** | 35.8 t | 38.9 |
| M60 · CERCHA | HEA200 | IPE220 | 7 | **37.0 t** | 30.1 t | 32.8 |
| M90 · PORTICO | HEA500 | IPE550 | 5 | **49.5 t** | 38.2 t | 41.7 |
| M90 · PORTICO-T | HEA500 | IPE550 | 5 | **50.3 t** | 39.1 t | 42.5 |
| M90 · PORTICO-F | HEA300 | IPE550 | 5 | **43.5 t** | 32.3 t | 35.1 |
| M90 · CERCHA | HEA200 | IPE220 | 5 | **36.6 t** | 25.3 t | 27.6 |

## Desglose por componente (t)

| Sistema × Modulación | Marcos principales | Entrepiso P2 (metaldeck) | Entrepiso P2 (staggered) | Entrepiso P2 (gran muro) | Secundaria | Total metaldeck | Total gran muro |
|---|---|---:|---:|---:|---:|---:|---:|
| M45 · PORTICO | 39.5 | 12.4 | 3.8 | 5.9 | 7.5 | 59.4 | 52.9 |
| M45 · PORTICO-T | 41.0 | 12.4 | 3.8 | 5.9 | 7.5 | 60.9 | 54.4 |
| M45 · PORTICO-F | 28.7 | 12.4 | 3.8 | 5.9 | 7.5 | 48.6 | 42.1 |
| M45 · CERCHA | 21.5 | 12.4 | 3.8 | 5.9 | 7.5 | 41.4 | 34.9 |
| M60 · PORTICO | 32.6 | 12.8 | 3.8 | 5.9 | 7.5 | 52.9 | 46.0 |
| M60 · PORTICO-T | 33.8 | 12.8 | 3.8 | 5.9 | 7.5 | 54.1 | 47.2 |
| M60 · PORTICO-F | 22.3 | 12.8 | 3.8 | 5.9 | 7.5 | 42.6 | 35.8 |
| M60 · CERCHA | 16.7 | 12.8 | 3.8 | 5.9 | 7.5 | 37.0 | 30.1 |
| M90 · PORTICO | 24.8 | 17.1 | 3.8 | 5.9 | 7.5 | 49.5 | 38.2 |
| M90 · PORTICO-T | 25.6 | 17.1 | 3.8 | 5.9 | 7.5 | 50.3 | 39.1 |
| M90 · PORTICO-F | 18.8 | 17.1 | 3.8 | 5.9 | 7.5 | 43.5 | 32.3 |
| M90 · CERCHA | 11.9 | 17.1 | 3.8 | 5.9 | 7.5 | 36.6 | 25.3 |

## Entrepiso P2 — opciones comparadas

Tres esquemas sin columnas interiores en la zona doméstica (el metaldeck con apoyos intermedios NO es viable sin columnas en cocina/núcleo):
- **GRAN-MURO (preferido):** el gran muro de X=31,5 (núcleo) es portante y recibe el P2; 3 vigas longitudinales IPE550 de 10.5 m en el plenum (Y≈3/9/15) apoyan en la cercha de borde X=21 (luz 18 m, cordón HSS150x150x8) y en el muro; franja del núcleo con losa sobre el muro (luz 4.5 m). Acero ≈ 5.1 t, axial del muro ≈ 76.4 kN/m, fn del panel ≈ 10.4 Hz. El muro aporta núcleo de corte longitudinal.
- **STAGGERED:** cerchas de canto completo de 18 m ocultas en particiones; requiere re-articular las particiones del P2 (hoy no existe línea continua de 18 m).
- **METALDECK:** línea base; introduce columnas en cocina/núcleo.
- Staggered truss: 3 cerchas de 18 m de canto completo (≈ 3.0 m, d/L ≈ 0.167), paneles de losa de 5.0 m entre cerchas, cordones HSS100x100x6, flecha de cercha ≈ 0.02 m, frecuencia del panel ≈ 14.9 Hz (criterio DG11 ≥ 5 Hz).

## Objetivos de control (auditoría)

- Acero total realista: **30.0–45.0 t** (desglose v0.2: 28,35 t, subestimado).
- Equivalente: **31.0–48.0 kg/m²** sobre 918 m².

## Hallazgos del modelo E0 (11-08-2026)

1. **Los pórticos con bases articuladas quedan gobernados por la deriva de viento (H/200):** columnas HEA500 en las tres modulaciones (marcos ≈ 25–41 t). El control de la auditoría (HEA300) no cumple la deriva de servicio con el viento de hipótesis E0; es una decisión del ingeniero en E1 si relaja el límite o introduce arriostramiento/rigidización.
2. **El sistema de cerchas con columnas articuladas y arriostramiento pesa ≈ 37–41 t** (ahorro ≈ 25–40 % sobre pórticos) y resuelve la deriva con columnas HEA200; el costo extra de fabricación de la cercha debe cotizarse antes de decidir (E1, puerta PE-1).
3. **Pórtico atado (PORTICO-T):** el tirante entre los apoyos de la cercha queda casi inactivo (≈ 1,4 kN) porque el faldón 1:30 es casi plano y la deriva de viento es un sway en la misma dirección de ambos muros; el tirante solo resistiría la apertura de aleros por empuje gravitatorio, que aquí no gobierna. Añade peso (≈ 1–2 t/pórtico) sin beneficio de deriva: **no es competitivo en este caso de carga.**
4. **Pórtico con bases fijas (PORTICO-F):** es el control efectivo de deriva para el sistema de pórticos. Permite columna HEA300 con deriva ≈ 0,016–0,021 m (vs. HEA500 articulado) y un marco ≈ 25–35 % más liviano; el costo pasa a la cimentación (momento en la base).
5. **Entrepiso P2:** tres esquemas sin columnas interiores — METALDECK (12,4–17,1 t según modulación, con columnas en cocina/núcleo y vigas de 6 m entre apoyos), STAGGERED (≈ 3,8 t, exige re-articular particiones) y **GRAN-MURO (≈ 5,9 t, preferido): el gran muro de X=31,5 trabaja como apoyo del P2**, con 3 vigas longitudinales en el plenum + cercha de borde X=21; sin re-articular particiones y con el muro actuando como núcleo de corte longitudinal. El peso de la losa de deck profundo se verifica en E1.
6. **Cubierta de un solo faldón ≈ 1:30:** verificada por el modelo: la viga de cubierta del pórtico queda gobernada por flecha y resistencia con IPE450/500/550 según modulación (M45/M60/M90); la cercha IPE220 con flecha despreciable (d/L = 1/16).
7. **Auditoría de física del modelo (11-08-2026):** corregidos signos de gravedad en cargas puntuales y uniformes (antes el pórtico 'flotaba' bajo carga muerta), proyección trigonométrica de cargas sobre miembros inclinados (la carga equivalente ahora es exactamente vertical) y límites de flecha L/180–L/240 comparados en metros (antes se comparaban con un límite 1000× más permisivo, dejando la flecha sin efecto).

## Supuestos críticos de este modelo

- Cargas y combinaciones son **hipótesis de ingeniero**, versionadas en `structure_system.json`; no es biblioteca NSR-10.
- Sin carga de nieve (Boyacá). Viento y sismo como hipótesis E0 hasta definir municipio.
- Pórticos con bases articuladas por defecto; PORTICO-T añade tirante de alero; PORTICO-F empotra las bases.
- Entrepiso P2: METALDECK (viguetas + vigas de 18 m + apoyos intermedios) vs. STAGGERED (cerchas escalonadas sin columnas interiores).
- Factor de detalle 15 % y desperdicio 5 %; perfiles de stock IPE/HEA/HSS.
- Cada resultado debe ser revisado por el ingeniero estructural antes de cruzar PE-1.
