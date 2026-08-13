# Modelo E0 — cribado estructural auditado (D-019)

**Estatus:** hipótesis de esquema · **NO APTO PARA SELECCIONAR SISTEMA, PRESUPUESTAR PE-1, DIMENSIONAR PERFILES NI CONSTRUIR**
**Fecha:** 2026-08-12 · **Revisión:** 0.2

> Altiplano de Boyaca sin nieve de diseno: NO se incluye carga de nieve. Gobiernan viento (NSR-10 B.6), sismo (Titulo A) y lluvia/drenaje. Envoltura responde al frio nocturno, condensacion e infiltracion, no a carga de nieve.

> **Dictamen:** ninguna fila es elegible para cerrar D-019 o fijar tonelaje. Son subtotales inferiores que omiten estados límite y componentes críticos.

| Sistema × modulación | Columnas* | Cubierta* | Líneas | Subtotal metaldeck* | Subtotal gran muro* | Estado |
|---|---|---|---:|---:|---:|---|
| M45 · PORTICO | HEA500 | IPE450 | 9 | 59.4 t | 57.0 t | pasa cribado 2D limitado; no demuestra diseño |
| M45 · PORTICO-T | HEA500 | IPE450 | 9 | 60.9 t | 58.5 t | pasa cribado 2D limitado; no demuestra diseño |
| M45 · PORTICO-F | HEA300 | IPE450 | 9 | 48.6 t | 46.2 t | pasa cribado 2D limitado; no demuestra diseño |
| M45 · CERCHA | HEA200 | IPE220 | 9 | 41.4 t | 39.0 t | INCOMPLETO: sin análisis lateral/estabilidad |
| M60 · PORTICO | HEA500 | IPE500 | 7 | 52.9 t | 50.1 t | pasa cribado 2D limitado; no demuestra diseño |
| M60 · PORTICO-T | HEA500 | IPE500 | 7 | 54.1 t | 51.3 t | pasa cribado 2D limitado; no demuestra diseño |
| M60 · PORTICO-F | HEA300 | IPE450 | 7 | 42.6 t | 39.9 t | pasa cribado 2D limitado; no demuestra diseño |
| M60 · CERCHA | HEA200 | IPE220 | 7 | 37.0 t | 34.2 t | INCOMPLETO: sin análisis lateral/estabilidad |
| M90 · PORTICO | HEB400 | IPE550 | 5 | 49.5 t | 42.4 t | FALLA cribado o agota catálogo E0 |
| M90 · PORTICO-T | HEB400 | IPE550 | 5 | 50.3 t | 43.2 t | FALLA cribado o agota catálogo E0 |
| M90 · PORTICO-F | HEA300 | IPE550 | 5 | 43.5 t | 36.4 t | pasa cribado 2D limitado; no demuestra diseño |
| M90 · CERCHA | HEA200 | IPE220 | 5 | 36.6 t | 29.4 t | INCOMPLETO: sin análisis lateral/estabilidad |

\* Perfil y masa de cribado; no son selección ni cantidad de diseño. D-043 adopta el camino gravitacional GRAN-MURO, no los perfiles ni el tonelaje del E0.

## Desglose de subtotales inferiores (t)

| Sistema × modulación | Marcos | P2 metaldeck | P2 staggered* | P2 gran muro* | Secundaria/reserva* | Total metaldeck | Total gran muro* |
|---|---:|---:|---:|---:|---:|---:|---:|
| M45 · PORTICO | 39.5 | 12.4 | 3.8 | 10.0 | 7.5 | 59.4 | 57.0 |
| M45 · PORTICO-T | 41.0 | 12.4 | 3.8 | 10.0 | 7.5 | 60.9 | 58.5 |
| M45 · PORTICO-F | 28.7 | 12.4 | 3.8 | 10.0 | 7.5 | 48.6 | 46.2 |
| M45 · CERCHA | 21.5 | 12.4 | 3.8 | 10.0 | 7.5 | 41.4 | 39.0 |
| M60 · PORTICO | 32.6 | 12.8 | 3.8 | 10.0 | 7.5 | 52.9 | 50.1 |
| M60 · PORTICO-T | 33.8 | 12.8 | 3.8 | 10.0 | 7.5 | 54.1 | 51.3 |
| M60 · PORTICO-F | 22.3 | 12.8 | 3.8 | 10.0 | 7.5 | 42.6 | 39.9 |
| M60 · CERCHA | 16.7 | 12.8 | 3.8 | 10.0 | 7.5 | 37.0 | 34.2 |
| M90 · PORTICO | 24.9 | 17.1 | 3.8 | 10.0 | 7.5 | 49.5 | 42.4 |
| M90 · PORTICO-T | 25.7 | 17.1 | 3.8 | 10.0 | 7.5 | 50.3 | 43.2 |
| M90 · PORTICO-F | 18.8 | 17.1 | 3.8 | 10.0 | 7.5 | 43.5 | 36.4 |
| M90 · CERCHA | 11.9 | 17.1 | 3.8 | 10.0 | 7.5 | 36.6 | 29.4 |

## Entrepiso P2 — estado de alternativas

- **METALDECK con apoyos:** subtotal gravitacional; introduce apoyos en la banda doméstica y no incluye diseño compuesto, conectores, vibración ni fuego.
- **STAGGERED — NO ADOPTADO:** 3 cerchas de 18 m, canto 3.0 m. La frecuencia del panel queda sin calcular hasta definir deck y sección compuesta.
- **GRAN-MURO — CONCEPTO GRAVITACIONAL ACTIVO D-043:** superficie de madera/absorción delante de bastidor oculto HSS150x150x8 + viga de transferencia IPE400; 6 vigas IPE450 a 3.0 m dejan un canto conceptual de 0.60 m. El subtotal (8.7 t) es una prueba de cabida y no verifica pandeo, uniones, fuego, diafragma, cimentación ni acción lateral.

## Defectos corregidos en revisión 0.2

1. Se calcula el momento interior para carga uniforme de ambos signos; la revisión 0.1 devolvía cero en una viga simple bajo succión.
2. La succión `WU` se separa de `WX+`/`WX-`; el sismo conceptual usa `EX+`/`EX-`.
3. Los miembros de piso usan demanda factorizada para resistencia y servicio sin factor para flecha; se eliminó la reducción `/1,5` no sustentada.
4. El catálogo ya no acepta silenciosamente su perfil mayor y el pórtico no ignora deriva/interacción al llegar a HEA500/HEB400.
5. El rafter incorpora interacción axial-flexión en el cribado de fluencia bruta.
6. Se retiró la frecuencia ficticia del deck modelado como losa maciza de 220 mm. D-043 adopta el camino gravitacional del gran muro, pero no valida perfiles ni cantidades.

## Bloqueadores

- **E0-AUTH-01 · CRITICAL:** D-043 adopta el GRAN-MURO como apoyo gravitacional híbrido, pero el E0 solo prueba un bastidor oculto idealizado. Falta diseñar la viga de transferencia, columnas, pandeo, uniones, anclajes, fuego y compatibilidad 1:1 con las cinco aperturas antes de descontar apoyos o fijar acero.
- **E0-DIR-01 · CRITICAL:** El gran muro está en X=31,50 y se extiende en Y: su plano no estabiliza automáticamente la dirección longitudinal X. El E0 anterior lo llamó erróneamente núcleo de corte longitudinal; las dos fachadas largas, el diafragma y los colectores siguen sin sistema lateral coordinado.
- **E0-COORD-01 · CRITICAL:** Las X longitudinales dibujadas en los paños 0–12 y 24–36 atraviesan el ventanal técnico de 7,20 m, vanos casi piso a techo del P2 y zonas de claraboya. Son trazos de conflicto, no arriostramientos adoptados.
- **E0-GEOM-01 · HIGH:** El borde del P2 X=21,00 y el gran muro X=31,50 caen a mitad de vanos de la retícula M60. El modelo de pórticos tributarios no representa estas transferencias fuera de retícula ni sus efectos locales.
- **E0-LAT-01 · CRITICAL:** La alternativa CERCHA no tiene modelo lateral, diafragma, colectores ni arriostramientos dimensionados; su peso es un subtotal inferior.
- **E0-STAB-01 · CRITICAL:** El pórtico es elástico lineal de primer orden y usa límites de fluencia de sección bruta; faltan pandeo, P-Delta, imperfecciones, pandeo lateral-torsional, esbeltez local, cortante y conexiones.
- **E0-SITE-01 · CRITICAL:** No hay predio, municipio, perfil de suelo, espectro, topografía ni presiones normativas de viento. qz y Cs siguen siendo hipótesis.
- **E0-LOAD-01 · CRITICAL:** No se modelan lluvia/empozamiento ni el efecto estructural completo de las dos claraboyas D-040, grandes portones y ventanales sobre el camino de cargas y los arriostramientos.
- **E0-P2-01 · CRITICAL:** El deck profundo no tiene ficha, geometría compuesta, apuntalamiento, conectores ni verificación de vibración; no se reporta una frecuencia numérica de panel.
- **E0-CLEAR-01 · HIGH:** La prueba D-043 usa seis IPE450 a 3,00 m y 0,15 m de armado de piso: canto total conceptual 0,60 m. Cabe con cielo cercano a +3,10 m, pero la reserva de 0,10 m para fuego, tolerancias y servicios debe demostrarse con deck y detalle compuesto reales; +3,20 m no deja reserva.
- **E0-FOUND-01 · HIGH:** Las bases fijas se comparan sin flexibilidad ni costo/peso de cimentación, placas base y anclajes; no son comparables económicamente con bases articuladas hasta tener geotecnia.
- **E0-QTY-01 · HIGH:** Correas, girts, arriostramientos, cartelas, conexiones, deck y protección se estiman por perfiles/factores o reservas; no son cantidades de diseño.

## Uso permitido

El E0 sirve para coordinación geométrica, detección de conflictos y definición del alcance del E1. Los objetivos históricos de 30–45 t y 31–48 kg/m² no validan un resultado por coincidencia. D-019 y PE-1 siguen abiertos hasta contar con modelo normativo, camino lateral completo, entrepiso de fabricante, geotecnia y cantidades revisadas por ingeniero competente.
