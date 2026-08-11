# Modelo E0 — comparación estructural (D-019)

**Estatus:** hipótesis de esquema · **NO APTO PARA CONSTRUIR**
**Fecha:** 2026-08-11 · **Revisión:** 0.1

> Altiplano de Boyaca sin nieve de diseno: NO se incluye carga de nieve. Gobiernan viento (NSR-10 B.6), sismo (Titulo A) y lluvia/drenaje. Envoltura responde al frio nocturno, condensacion e infiltracion, no a carga de nieve.

| Sistema × Modulación | Columnas | Viga/cercha | Pórticos | Acero total | kg/m² |
|---|---|---|---|---:|---:|
| M45 · PORTICO | HEA500 | IPE450 | 9 | **58.5 t** | 63.7 |
| M45 · CERCHA | HEA200 | IPE220 | 9 | **40.4 t** | 44.1 |
| M45 · PORTICO | HEA500 | IPE450 | 9 | **58.5 t** | 63.7 |
| M45 · CERCHA | HEA200 | IPE220 | 9 | **40.4 t** | 44.1 |
| M60 · PORTICO | HEA500 | IPE500 | 7 | **52.1 t** | 56.8 |
| M60 · CERCHA | HEA200 | IPE220 | 7 | **36.2 t** | 39.4 |
| M60 · PORTICO | HEA500 | IPE500 | 7 | **52.1 t** | 56.8 |
| M60 · CERCHA | HEA200 | IPE220 | 7 | **36.2 t** | 39.4 |
| M90 · PORTICO | HEA500 | IPE550 | 5 | **49.1 t** | 53.4 |
| M90 · CERCHA | HEA200 | IPE220 | 5 | **36.2 t** | 39.4 |
| M90 · PORTICO | HEA500 | IPE550 | 5 | **49.1 t** | 53.4 |
| M90 · CERCHA | HEA200 | IPE220 | 5 | **36.2 t** | 39.4 |

## Desglose por componente (t)

| Sistema × Modulación | Marcos principales | Entrepiso P2 | Secundaria | Total |
|---|---|---:|---:|---:|---:|
| M45 · PORTICO | 39.5 | 11.4 | 7.5 | 58.5 |
| M45 · CERCHA | 21.5 | 11.4 | 7.5 | 40.4 |
| M45 · PORTICO | 39.5 | 11.4 | 7.5 | 58.5 |
| M45 · CERCHA | 21.5 | 11.4 | 7.5 | 40.4 |
| M60 · PORTICO | 32.6 | 12.0 | 7.5 | 52.1 |
| M60 · CERCHA | 16.7 | 12.0 | 7.5 | 36.2 |
| M60 · PORTICO | 32.6 | 12.0 | 7.5 | 52.1 |
| M60 · CERCHA | 16.7 | 12.0 | 7.5 | 36.2 |
| M90 · PORTICO | 24.8 | 16.7 | 7.5 | 49.1 |
| M90 · CERCHA | 11.9 | 16.7 | 7.5 | 36.2 |
| M90 · PORTICO | 24.8 | 16.7 | 7.5 | 49.1 |
| M90 · CERCHA | 11.9 | 16.7 | 7.5 | 36.2 |

## Objetivos de control (auditoría)

- Acero total realista: **30.0–45.0 t** (desglose v0.2: 28,35 t, subestimado).
- Equivalente: **31.0–48.0 kg/m²** sobre 918 m².

## Supuestos críticos de este modelo

- Cargas y combinaciones son **hipótesis de ingeniero**, versionadas en `structure_system.json`; no es biblioteca NSR-10.
- Sin carga de nieve (Boyacá). Viento y sismo como hipótesis E0 hasta definir municipio.
- Pórticos con bases articuladas; entrepiso P2 con viguetas continuas, vigas transversales de 18 m y viga de borde en X=21 con dos apoyos interiores.
- Factor de detalle 15 % y desperdicio 5 %; perfiles de stock IPE/HEA.
- Cada resultado debe ser revisado por el ingeniero estructural antes de cruzar PE-1.
