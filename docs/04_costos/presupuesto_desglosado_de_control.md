# Presupuesto desglosado de control

**Estatus:** borrador de control; hipótesis de cantidades y precios; no es presupuesto
contractual  
**Versión:** 0.3.11
**Fecha de precios:** 2026-08-11  
**Document update:** 2026-08-21
**Fuente activa:** `BORN/Dream House — Presupuesto Técnico y Control de Costos v0.2.docx`
**Origen:** desglose atómico del target de obra física v0.2 ($941 M) y del reparto de
fases F1/F2 de la estrategia de dos fases.  
**Regla de gobierno:** este documento **no aumenta la confianza del target**. Es una
decomposición de hipótesis para encontrar dónde están las cantidades, los precios
agresivos y las oportunidades de ahorro. Toda partida se reemplaza por APU con
cotización en las puertas PE-1/PE-2/PE-3. Ninguna cifra aquí es un requisito congelado.

## Cómo leer este desglose

- Cada partida tiene código jerárquico `capítulo.partida` (ej. `05.02` = capítulo 05,
  partida 2).
- **Cantidad** y **precio unitario** son hipótesis de medición sobre la geometría del
  programa (648 m² PB, 270 m² P2, envolvente ≈810 m² brutos, dos portones 4,80 × 4,80 m,
  etc.). Sirven para auditar el control y para cotizar; no reemplazan medición por
  planos.
- **Fase 1 / Fase 2** reparten cada partida entre las fases constructivas (suma de fase
  1 = $867 M; fase 2 = $74 M). Los repartos 14–19, 21, 23 y 25 son hipótesis, igual que
  en la estrategia de dos fases.
- **Confianza:** escala del expediente (alta / media-alta / media / baja-media / baja)
  para el precio unitario y su aplicación local.
- **Fuente/supuesto:** referencia de precio observada (CYPE, proveedores), dato del
  v0.1/v0.2 o hipótesis de control. Las URLs de CYPE están al final del documento.
- Los totales se presentan redondeados a $1.000; el subtotal de capítulo gobierna.

## Resumen por capítulo

| Código | Capítulo                                          | Control    |     Fase 1 |    Fase 2 |  Confianza |
| ------ | ------------------------------------------------- | ---------- | ---------: | --------: | ---------: |
| 01     | Preliminares, campamento, replanteo               | $15 M      |      $15 M |        $0 |      media |
| 02     | Excavaciones y movimientos menores                | $7 M       |       $7 M |        $0 |      media |
| 03     | Cimentaciones, pedestales y anclajes              | $35 M      |      $35 M |        $0 |      media |
| 04     | Losa PB industrial endurecida y pulida            | $83 M      |      $83 M |        $0 |      media |
| 05     | Estructura metálica principal nave + P2           | $145 M     |     $145 M |        $0 | baja-media |
| 06     | Correas, secundaria y arriostramientos            | $55 M      |      $55 M |        $0 | baja-media |
| 07     | Losa metaldeck P2                                 | $41 M      |      $41 M |        $0 | media-alta |
| 08     | Cubierta metálica aislada                         | $70 M      |      $70 M |        $0 |      media |
| 09     | Fachadas de panel metálico aislado                | $95 M      |      $95 M |        $0 |      media |
| 10     | Canales, remates, flashing y sellos               | $20 M      |      $20 M |        $0 |      media |
| 11     | Dos portones industriales grandes                 | $24 M      |      $24 M |        $0 | baja-media |
| 12     | Gran evento principal de vidrio                   | $38 M      |      $38 M |        $0 | baja-media |
| 13     | Ventanas restantes + puerta peatonal              | $20 M      |      $20 M |        $0 | baja-media |
| 14     | Divisiones P2/núcleo + acústica                   | $38 M      |      $26 M |     $12 M |      media |
| 15     | Redes hidrosanitarias principales                 | $20 M      |      $17 M |      $3 M |       baja |
| 16     | Cinco baños + ducha/sauna + húmedos               | $35 M      |      $22 M |     $13 M | baja-media |
| 17     | Electricidad, tableros, iluminación y potencia    | $42 M      |      $35 M |      $7 M |       baja |
| 18     | Datos, red y preparación Home Assistant           | $8 M       |       $7 M |      $1 M |       baja |
| 19     | Extracción, ventilación y climatización selectiva | $25 M      |      $20 M |      $5 M |       baja |
| 20     | Cocina fija, muebles, mesones y herrajes          | $25 M      |      $25 M |        $0 | baja-media |
| 21     | Closets + cajoneras y bancos fijos del taller     | $30 M      |      $17 M |     $13 M | baja-media |
| 22     | Escalera metálica + barandas                      | $12 M      |      $12 M |        $0 |      media |
| 23     | Acabados residenciales P2 y pintura puntual       | $25 M      |      $16 M |      $9 M | baja-media |
| 24     | Terraza inmediata de concreto + drenajes          | $18 M      |      $18 M |        $0 |      media |
| 25     | Elevador automotriz + provisión civil             | $15 M      |       $4 M |     $11 M |      media |
|        | **Total obra física**                             | **$941 M** | **$867 M** | **$74 M** | baja-media |

---

## 01 — Preliminares, campamento y replanteo — $15 M

| Código | Partida                                              | Un  | Cant | P. unitario |   Subtotal | Confianza | Fuente/supuesto                                       |
| ------ | ---------------------------------------------------- | --- | ---: | ----------: | ---------: | --------- | ----------------------------------------------------- |
| 01.01  | Replanteo y localización de obra                     | gl  |    1 |  $2.000.000 | $2.000.000 | media     | Incluye comisión topográfica y ejes de los 648 m²     |
| 01.02  | Campamento, cerramiento temporal y servicios de obra | gl  |    1 |  $3.500.000 | $3.500.000 | media     | Baños portátiles, cerramiento, bodega de herramientas |
| 01.03  | Instalaciones provisionales (agua, energía, red)     | gl  |    1 |  $3.000.000 | $3.000.000 | media     | Acometidas provisionales y consumos                   |
| 01.04  | Movilización/desmovilización y grúa de montaje       | gl  |    1 |  $3.500.000 | $3.500.000 | media     | Incluye izaje de estructura y vidrio; logística rural |
| 01.05  | Seguros y pólizas de obra                            | gl  |    1 |  $2.000.000 | $2.000.000 | media     | Todo riesgo construcción + RC                         |
| 01.06  | Control topográfico y ensayos iniciales              | gl  |    1 |  $1.000.000 | $1.000.000 | media     | Nivelaciones, conos, ensayos de compactación inicial  |

**Nota:** la remobilización de Fase 2 **no** está aquí; se presupuesta aparte con
escalamiento (ver estrategia de dos fases).

---

## 02 — Excavaciones y movimientos menores — $7 M

| Código | Partida                                            | Un  | Cant | P. unitario |   Subtotal | Confianza  | Fuente/supuesto                                     |
| ------ | -------------------------------------------------- | --- | ---: | ----------: | ---------: | ---------- | --------------------------------------------------- |
| 02.01  | Descapote y retiro de tierra vegetal               | m³  |  130 |     $20.000 | $2.600.000 | media      | 648 m² × 0,20 m de descapote                        |
| 02.02  | Excavación de zapatas, vigas y localizada          | m³  |   80 |     $25.000 | $2.000.000 | media      | Sin máquina mayor; movimientos "menores" según v0.2 |
| 02.03  | Relleno, mejoramiento y compactación de subrasante | m³  |  150 |     $12.000 | $1.800.000 | baja-media | Depende de geotecnia del predio                     |
| 02.04  | Manejo de aguas de obra y drenaje temporal         | gl  |    1 |    $600.000 |   $600.000 | baja       | Hipótesis; el agua del lote es riesgo R-05/R-14     |

**Riesgo de control:** si el predio exige rellenos, retiro de materiales o drenajes
mayores, este capítulo puede crecer; validar con geotecnia antes de la compra (PE-1).

---

## 03 — Cimentaciones, pedestales y anclajes — $35 M

| Código | Partida                                       | Un  | Cant | P. unitario |    Subtotal | Confianza  | Fuente/supuesto                                     |
| ------ | --------------------------------------------- | --- | ---: | ----------: | ----------: | ---------- | --------------------------------------------------- |
| 03.01  | Concreto 25 MPa en zapatas y pedestales       | m³  |   24 |    $730.000 | $17.520.000 | media      | CYPE zapata armada ≈$727.665/m³ (v0.1)              |
| 03.02  | Concreto 25 MPa en vigas de amarre            | m³  |   12 |    $680.000 |  $8.160.000 | media      | Menor encofrado que zapata                          |
| 03.03  | Acero de refuerzo (incl. despuntes)           | kg  |  950 |      $6.500 |  $6.175.000 | media      | Ratio ≈1,8 % del volumen; verificar por cálculo     |
| 03.04  | Formaleta y encofrado de cimentación          | m²  |   90 |     $30.000 |  $2.700.000 | media      | Supuesto de control                                 |
| 03.05  | Placas base y pernos de anclaje de estructura | gl  |    1 |    $445.000 |    $445.000 | baja-media | Patrón de anclajes del lift **no** embebido (regla) |

**Riesgo de control:** 36 m³ de concreto + 950 kg de acero es una cimentación ligera
para una nave de 18 m de luz; depende totalmente de la geotecnia. Si el suelo es pobre,
este capítulo es de los primeros en superar el control (R-05).

---

## 04 — Losa PB industrial, endurecida y pulida — $83 M

| Código | Partida                                         | Un  | Cant | P. unitario |    Subtotal | Confianza | Fuente/supuesto                                       |
| ------ | ----------------------------------------------- | --- | ---: | ----------: | ----------: | --------- | ----------------------------------------------------- |
| 04.01  | Subbase granular (rajón/mejoramiento)           | m³  |   97 |    $120.000 | $11.640.000 | media     | 648 m² × 0,15 m                                       |
| 04.02  | Losa de concreto 21 MPa, e=15 cm                | m³  |   97 |    $420.000 | $40.740.000 | media     | Concreto obra gruesa + vaciado; verificar por cálculo |
| 04.03  | Malla electro-soldada o fibra sintética         | m²  |  648 |     $12.000 |  $7.776.000 | media     | Según diseño de juntas y cargas                       |
| 04.04  | Barrera de vapor y polietileno                  | m²  |  648 |      $6.000 |  $3.888.000 | media     | Clima frío; requisito de envolvente/higrotermia       |
| 04.05  | Endurecedor, fratasado y curado                 | m²  |  648 |      $8.000 |  $5.184.000 | media     | Sistema piso industrial, no mortero posterior         |
| 04.06  | Pulido y sellado zona doméstica/monumental      | m²  |  400 |     $15.000 |  $6.000.000 | media     | El taller/car bay no se pule; zona social sí          |
| 04.07  | Juntas de aserrado y sellado                    | ml  |  250 |     $12.000 |  $3.000.000 | media     | Juntas cada ~6×6 m + perimetrales                     |
| 04.08  | Densificador y acabado final                    | m²  |  400 |      $8.000 |  $3.200.000 | media     | Refuerzo del pulido residencial                       |
| 04.09  | Engrosamiento local del lift y cargas puntuales | gl  |    1 |  $1.572.000 |  $1.572.000 | baja      | No sobredimensionar los 648 m²; resolver local        |

**Nota técnica:** el CYPE "piso industrial tratado" (RSI007) ronda $177.239/m². Aquí la
losa es a la vez estructura + acabado, por eso el control se descompone en subbase,
estructura y tratamiento superficial. Si se exigiera pulido total (648 m²) en vez de
parcial, el capítulo crecería ≈$4–6 M.

---

## 05 — Estructura metálica principal nave + P2 — $145 M

| Código | Partida                                | Un  |  Cant | P. unitario |    Subtotal | Confianza  | Fuente/supuesto                                           |
| ------ | -------------------------------------- | --- | ----: | ----------: | ----------: | ---------- | --------------------------------------------------------- |
| 05.01  | Columnas y pórticos principales        | kg  | 8.500 |      $7.200 | $61.200.000 | baja-media | Supone ≈31 kg/m² total proyecto; requiere cálculo (D-019) |
| 05.02  | Vigas y cerchas de cubierta (luz 18 m) | kg  | 7.000 |      $7.200 | $50.400.000 | baja-media | Pórtico vs. cercha por comparación estructural            |
| 05.03  | Vigas de entrepiso P2                  | kg  | 3.000 |      $7.200 | $21.600.000 | baja-media | Incluye continuidad de cargas                             |
| 05.04  | Placas base, rigidizadores y detalles  | kg  |   700 |      $7.000 |  $4.900.000 | baja-media | Conexiones apernadas preferidas                           |
| 05.05  | Protección anticorrosiva y acabado     | gl  |     1 |  $6.900.000 |  $6.900.000 | media      | Esquema por exposición; no "premium" sin estudio          |

**Riesgo de control (el mayor del proyecto):** 19.200 kg de acero principal equivalen a
un orden de magnitud optimista para una luz de 18 m en zona sísmica. El rango real
podría ser 30–45 t y mover este capítulo (y el 06) a $180–260 M. **Este es el primer
lugar donde el target v0.2 puede romperse.** PE-1 exige predimensionamiento estructural
y kg/m² con 3 modulaciones antes de congelar.

---

## 06 — Correas, estructura secundaria y arriostramientos — $55 M

| Código | Partida                                 | Un  |  Cant | P. unitario |    Subtotal | Confianza  | Fuente/supuesto                           |
| ------ | --------------------------------------- | --- | ----: | ----------: | ----------: | ---------- | ----------------------------------------- |
| 06.01  | Correas de cubierta (C/Z estándar)      | kg  | 4.000 |      $6.000 | $24.000.000 | baja-media | Módulos 6 m; perfiles de stock            |
| 06.02  | Girts y estructura de fachada           | kg  | 3.000 |      $6.000 | $18.000.000 | baja-media | Vanos de panel sándwich                   |
| 06.03  | Arriostramientos, diagonales y tensores | kg  | 1.500 |      $6.000 |  $9.000.000 | baja-media | Aberturas frontales reducen paños rígidos |
| 06.04  | Largueros de vidrio y portones          | kg  |   400 |      $6.000 |  $2.400.000 | baja-media | Soportes de los eventos grandes           |
| 06.05  | Ménsulas y soportes de instalaciones    | kg  |   250 |      $6.000 |  $1.500.000 | baja-media | MEP coordinado con estructura visible     |
| 06.06  | Protección de secundarios y misceláneos | gl  |     1 |    $100.000 |    $100.000 | media      | Ajuste de redondeo                        |

**Nota:** 9.150 kg de secundaria + 19.200 kg de principal = 28.350 kg totales
(≈$7.054/kg combinado, dentro del rango CYPE A36/A572 de $6.587–7.376/kg instalado).
La incertidumbre no está en el precio por kg sino en el **tonelaje**.

---

## 07 — Losa metaldeck P2 — $41 M

| Código | Partida                               | Un  | Cant | P. unitario |    Subtotal | Confianza  | Fuente/supuesto                       |
| ------ | ------------------------------------- | --- | ---: | ----------: | ----------: | ---------- | ------------------------------------- |
| 07.01  | Lámina deck colaborante 0,9 mm        | m²  |  270 |     $85.000 | $22.950.000 | media-alta | 18 × 15 m = 270 m²                    |
| 07.02  | Concreto vertido sobre deck (e=10 cm) | m³  |   27 |    $450.000 | $12.150.000 | media-alta | 270 × 0,10 m                          |
| 07.03  | Malla de repartición y refuerzo       | m²  |  270 |      $8.000 |  $2.160.000 | media-alta | Según diseño                          |
| 07.04  | Conectores y anclajes de cortante     | un  |  270 |      $4.000 |  $1.080.000 | media-alta | 1/panel aprox.                        |
| 07.05  | Apuntalamiento y formaleta de borde   | gl  |    1 |  $1.460.000 |  $1.460.000 | media-alta | Incluye vigas de borde del entrepiso  |
| 07.06  | Curado y nivelación                   | gl  |    1 |  $1.200.000 |  $1.200.000 | media-alta | Acabado apto para acabado residencial |

**Nota:** consistente con CYPE metaldeck ≈$150.400/m² (270 m² ≈ $40,6 M). Es de los
capítulos con mejor respaldo de precio.

---

## 08 — Cubierta metálica aislada — $70 M

| Código | Partida                                                      | Un  | Cant | P. unitario |    Subtotal | Confianza | Fuente/supuesto                                                                         |
| ------ | ------------------------------------------------------------ | --- | ---: | ----------: | ----------: | --------- | --------------------------------------------------------------------------------------- |
| 08.01  | Panel sándwich de cubierta 50 mm                             | m²  |  620 |    $101.000 | $62.620.000 | media     | CYPE cubierta sándwich ≈$101.010/m²                                                     |
| 08.02  | Remates continuos de alero alto/bajo y cierres de panel      | ml  |   40 |     $60.000 |  $2.400.000 | media     | Cubierta mono-pendiente: no existe cumbrera central ni limatesa; cantidad por verificar |
| 08.03  | Fijaciones, soportes y sellos de cubierta                    | m²  |  648 |      $6.000 |  $3.888.000 | media     | Tornillería y sellos de vapor                                                           |
| 08.04  | Reserva de ventilación alta por fachada/equipo, sin cumbrera | gl  |    1 |    $540.000 |    $540.000 | baja      | Estrategia higrotérmica pendiente; no perforar cubierta por defecto                     |
| 08.05  | Bajantes de aguas lluvias                                    | gl  |    1 |    $552.000 |    $552.000 | media     | Desagües de cubierta a canales                                                          |

**Oportunidad de ahorro:** comparar panel sándwich vs. sistema por capas
(teja + lana con facing + liner interior) según `tecnicas_que_abaratan_costos.md`
(§3.2). Solo con cotización local y cálculo de punto de rocío.

---

## 09 — Fachadas de panel metálico aislado — $95 M

| Código | Partida                         | Un  | Cant | P. unitario |    Subtotal | Confianza | Fuente/supuesto                              |
| ------ | ------------------------------- | --- | ---: | ----------: | ----------: | --------- | -------------------------------------------- |
| 09.01  | Panel sándwich de fachada 50 mm | m²  |  640 |    $140.000 | $89.600.000 | media     | Envolvente ≈810 m² brutos − vanos            |
| 09.02  | Fijaciones, sellos y juntas     | m²  |  640 |      $6.000 |  $3.840.000 | media     | Cintas de vapor y sellos de puentes térmicos |
| 09.03  | Esquineros y cierres de panel   | ml  |   60 |     $26.000 |  $1.560.000 | media     | Remates de esquinas y encuentros             |
| 09.04  | D-080 P2 panel-core and inner-lining reconciliation | m² | TBC | TBC | not included | baja | Compare selected 80–120 mm P2 panel and inner lining with `09.01`, `14.01`, `14.03` and Chapter 23; prevent double counting |

**Riesgo de control:** el precio implícito de $140.000/m² está por debajo del rango CYPE
observado de $150.000–200.000/m². Si la fachada neta real supera 640 m² o el sistema
exige perfiles térmicos (que si), el capítulo puede crecer $10–30 M. Cotizar localmente
antes de PE-2.

`09.04` is a D-080 measurement/reconciliation alert and does not change the $95 M chapter
subtotal. Price the selected P2 insulated panel, girts, fasteners, air/water seals, window
interfaces and inner lining once across chapters 09/10/14/23.

---

## 10 — Canales, remates, flashing y sellos — $20 M

| Código | Partida                                   | Un  | Cant | P. unitario |   Subtotal | Confianza | Fuente/supuesto                         |
| ------ | ----------------------------------------- | --- | ---: | ----------: | ---------: | --------- | --------------------------------------- |
| 10.01  | Canales y canaletas de aguas lluvias      | ml  |   72 |     $80.000 | $5.760.000 | media     | Perímetro de cubierta 2 × 36 m          |
| 10.02  | Remates perimetrales (flashing)           | ml  |  100 |     $45.000 | $4.500.000 | media     | Cubierta + fachada + encuentros         |
| 10.03  | Sellos, siliconas y cinta de vapor        | ml  |  600 |     $12.000 | $7.200.000 | media     | Sellado de aire: requisito higrotérmico |
| 10.04  | Transiciones en vanos de puertas y vidrio | gl  |    1 |  $2.540.000 | $2.540.000 | media     | Perfiles de transición portones/vidrio  |

**Nota:** no diferir estanqueidad a Fase 2. Es capítulo completo en F1.

---

## 11 — Dos portones industriales grandes — $24 M

| Código | Partida                                      | Un  | Cant | P. unitario |    Subtotal | Confianza  | Fuente/supuesto                        |
| ------ | -------------------------------------------- | --- | ---: | ----------: | ----------: | ---------- | -------------------------------------- |
| 11.01  | Portón seccional aislado car bay 4,80 × 4,80 | m²  |   23 |    $480.000 | $11.040.000 | baja-media | Modelo de catálogo; cotizar 2–3 marcas |
| 11.02  | Portón seccional aislado RC/DIY 4,80 × 4,80  | m²  |   23 |    $480.000 | $11.040.000 | baja-media | Idéntico al 11.01 para repetición      |
| 11.03  | Motorización, rieles y controles             | un  |    2 |    $700.000 |  $1.400.000 | baja-media | Maniobra y sistema comercial a probar  |
| 11.04  | Sellos perimetrales y guías                  | gl  |    1 |    $520.000 |    $520.000 | media      | Estanqueidad y aislamiento             |

**Nota:** medidas estándar de catálogo (hard rule de composición); evitar versiones
"especiales" que duplican plazo y precio (R-12).

---

## 12 — Gran evento principal de vidrio — $38 M

| Código | Partida                                            | Un  | Cant | P. unitario |    Subtotal | Confianza  | Fuente/supuesto                            |
| ------ | -------------------------------------------------- | --- | ---: | ----------: | ----------: | ---------- | ------------------------------------------ |
| 12.01  | Sistema modular de vidrio fijo low-e (perfiles)    | m²  |   28 |  $1.180.000 | $33.040.000 | baja-media | D-083 measures 21,96 m² Side A within the retained allowance; final system pending |
| 12.02  | Estructura secundaria de soporte del vidrio        | gl  |    1 |  $2.760.000 |  $2.760.000 | baja-media | Largueros/travesaños coordinados con acero |
| 12.03  | Herrajes, sellos y drenaje del sistema             | gl  |    1 |  $1.200.000 |  $1.200.000 | baja-media | Termopanel + low-e según modelo térmico    |
| 12.04  | Montaje e izaje                                    | gl  |    1 |  $1.000.000 |  $1.000.000 | baja-media | Logística rural (R-19)                     |

**D-083 measurement update:** the active Side A opening is **7.20 × 3.05 m = 21.96 m²**.
It replaces the former 18.495 m² combined Side A workstation/main-glazing geometry and
remains below the 28 m² control allowance. This apparent area reserve is not a saving:
safe glass, economical module widths, mullions, header/jamb steel, seals, drainage and
installation must be specified and quoted first. The exterior is performance-first;
there is no allowance for a decorative facade frame or premium curtain-wall expression.

**Riesgo de control:** el precio implícito de $1.180.000/m² está por debajo de la
referencia de muro cortina CYPE ($1.290.000–1.485.000/m²). Es un paño "contenido" (28
m²), pero si el evento crece o exige vidrio de desempeño especial, el capítulo sube
fácilmente $8–15 M. Es hard rule: no eliminar; optimizar dimensión y especificación.

---

## 13 — Ventanas restantes + puerta peatonal — $20 M

| Código | Partida                             | Un  | Cant | P. unitario |    Subtotal | Confianza  | Fuente/supuesto                   |
| ------ | ----------------------------------- | --- | ---: | ----------: | ----------: | ---------- | --------------------------------- |
| 13.01  | Ventanas P2 (aluminio + vidrio)     | m²  |   40 |    $350.000 | $14.000.000 | baja-media | 4 suites + hall; tamaños estándar |
| 13.02  | Ventanas cocina/núcleo/fachadas     | m²  |   12 |    $300.000 |  $3.600.000 | baja-media | Vanos de servicio                 |
| 13.03  | Puerta peatonal central 1,60 × 2,50 | un  |    1 |  $1.400.000 |  $1.400.000 | baja-media | Perfil de catálogo                |
| 13.04  | Persianas y mosquiteros selectivos  | gl  |    1 |    $500.000 |    $500.000 | baja       | Solo donde aportan                |
| 13.05  | Soportes y sellos de carpintería    | gl  |    1 |    $500.000 |    $500.000 | media      | Fijaciones y sellos               |
| 13.06  | D-083 Side B workstation window         | m²  | 5,40 |      TBC | not included | baja     | 3,00 × 1,80 m; sill +0,75 m; Side A remains joined to 12.01 |
| 13.07  | D-082 operable P2 rescue window    | un  |    1 |          TBC | not included | baja     | 1.00 × 1.20 m schematic opening; clear opening, hardware, safe glass, flashing and transfer pending |
| 13.08  | D-083 net additional vertical glazing variance | m² | 5,565 | TBC | not included | baja | 4,035 m² bedroom + 1,530 m² desk delta; reconcile with 12.01/13.01/13.06; no duplication |

`13.06` is an unpriced measurement alert for the retained Side B window only. D-078 moves
the former Side A member into the unified opening controlled under `12.01`; it must not be
counted twice. The line does not change the $20 M chapter control subtotal until
duplication against `13.02`, facade scope, selected systems and comparable quotations are
resolved.

`13.07` is an unpriced measurement alert for the D-082 rescue-opening package. Reconcile
it with `13.01`, the P2 facade opening deduction, safe glazing, hardware operable without
a key, flashing, seals and any transfer handhold or platform. The line does not change
the $20 M chapter control subtotal.

`13.08` records the net D-083 change against the immediately preceding geometry; it is
not an additional glazing package to sum again. Active P2 windows now measure 54.72 m²,
the Side A desk opening 21.96 m² and Side B 5.40 m². Reconcile the 4.035 m² bedroom
delta and 1.530 m² desk delta one-to-one against `12.01`, `13.01` and `13.06`, including
facade deductions, repeated modules, safe glass, fall protection, frames, structure,
curtains, seals and drainage. The optional 8.64 m² dining study is excluded. The line
does not change the $20 M chapter control subtotal.

---

## 14 — Divisiones P2/núcleo + acústica selectiva — $38 M (F1 $26 M / F2 $12 M)

| Código | Partida                                 | Un  | Cant | P. unitario |    Subtotal |          F1 |         F2 | Confianza | Fuente/supuesto                                     |
| ------ | --------------------------------------- | --- | ---: | ----------: | ----------: | ----------: | ---------: | --------- | --------------------------------------------------- |
| 14.01  | Tabiques drywall P2 (estructura + lana) | m²  |  200 |     $95.000 | $19.000.000 | $12.500.000 | $6.500.000 | media     | CYPE drywall ≈$83.630/m² + lana; F2 = zona diferida |
| 14.02  | Divisiones del núcleo PB                | m²  |   80 |     $83.750 |  $6.700.000 |  $6.700.000 |         $0 | media     | Baño, homelab, bodega, pantry, escalera             |
| 14.03  | Aislamiento acústico selectivo          | m²  |  120 |     $45.000 |  $5.400.000 |  $2.700.000 | $2.700.000 | media     | Lana + barrera de masa en colchones                 |
| 14.04  | Puertas interiores P2                   | un  |    7 |    $700.000 |  $4.900.000 |  $2.400.000 | $2.500.000 | media     | Suites + lavandería + hall; F2 = zona diferida      |
| 14.05  | Puertas interiores PB                   | un  |    2 |    $500.000 |  $1.000.000 |  $1.000.000 |         $0 | media     | Núcleo + bodega                                     |
| 14.06  | Remates, ajustes y sellos               | gl  |    1 |  $1.000.000 |  $1.000.000 |    $700.000 |   $300.000 | media     | Igualación de acabados en F2                        |
| 14.07  | D-071 Side B acoustic TV mounting field | m²  | 16,72 |          TBC | not included | not included | $0 | baja | 4,40 × 3,80 m finish + local backing within existing exterior wall |
| 14.08  | D-080 P2 wall schedule remeasurement    | m²  | TBC |          TBC | not included | not included | $0 | baja | Separate W01A/W01B/W02/W02S/W03/W04R/W05 lining/W06 by height, phase and opening |

`14.07` is an unpriced Phase 1 measurement alert. It excludes the television and active
AV equipment. Do not add it to the $38 M chapter subtotal until its local backing,
acoustic/fire/enclosure interfaces, sealed penetrations and overlap with `14.03` are
reconciled. D-071 deletes rather than prices D-070's freestanding partition.

`14.08` is an unpriced D-080 measurement alert. The centreline screen records 82.30 m of
opaque internal shared boundaries, 10.55 m of retained hall edge and 48.00 m of gross P2
exterior perimeter before openings. Convert these runs to wall-face areas using confirmed
heights and openings; price tested assemblies, doors, seals, heads, fire stopping, access,
waste and mock-ups without duplicating `09.04` or Chapter 23. The line does not change the
$38 M chapter subtotal.

---

## 15 — Redes hidrosanitarias principales — $20 M (F1 $17 M / F2 $3 M)

| Código | Partida                           | Un  | Cant | P. unitario |   Subtotal |         F1 |         F2 | Confianza | Fuente/supuesto                               |
| ------ | --------------------------------- | --- | ---: | ----------: | ---------: | ---------: | ---------: | --------- | --------------------------------------------- |
| 15.01  | Red de agua fría/caliente troncal | ml  |  120 |     $60.000 | $7.200.000 | $6.600.000 |   $600.000 | baja      | Troncales y shafts F1; ramales F2             |
| 15.02  | Red sanitaria y ventilaciones     | ml  |  100 |     $55.000 | $5.500.000 | $5.200.000 |   $300.000 | baja      | Bajantes agrupadas sin sacrificar acústica    |
| 15.03  | Bajantes y montantes              | un  |    4 |    $500.000 | $2.000.000 | $2.000.000 |         $0 | baja      | Programa final completo en F1                 |
| 15.04  | Calentamiento de agua             | gl  |    1 |  $2.300.000 | $2.300.000 | $2.300.000 |         $0 | baja      | Capacidad para el programa final              |
| 15.05  | Válvulas, accesorios y soportes   | gl  |    1 |  $1.800.000 | $1.800.000 |   $900.000 |   $900.000 | baja      | Válvulas de corte accesibles en troncales     |
| 15.06  | Pruebas y sellos finales          | gl  |    1 |  $1.200.000 | $1.200.000 |         $0 | $1.200.000 | baja      | F2 repite pruebas de redes de zonas diferidas |

**Riesgo de control:** la solución de agua/saneamiento depende del predio (red pública,
pozo, PTAR, bombeo). Lo que el predio imponga es costo **externo** que aún no está
presupuestado (R-14).

---

## 16 — Cinco baños + ducha/sauna + acabados húmedos — $35 M (F1 $22 M / F2 $13 M)

| Código | Partida                                  | Un  | Cant | P. unitario |    Subtotal |         F1 |         F2 | Confianza  | Fuente/supuesto                     |
| ------ | ---------------------------------------- | --- | ---: | ----------: | ----------: | ---------: | ---------: | ---------- | ----------------------------------- |
| 16.01  | Sanitarios y lavamanos                   | un  |    6 |    $550.000 |  $3.300.000 | $2.270.000 | $1.030.000 | baja-media | 5 baños + ducha sauna               |
| 16.02  | Griferías de baño                        | un  |    6 |    $700.000 |  $4.200.000 | $2.890.000 | $1.310.000 | baja-media | Ducha + vanitory por baño           |
| 16.03  | Duchas y cabinas                         | un  |    6 |    $450.000 |  $2.700.000 | $1.860.000 |   $840.000 | baja-media | Incluye ducha doble de la principal |
| 16.04  | Impermeabilización de áreas húmedas      | m²  |   60 |     $55.000 |  $3.300.000 | $2.270.000 | $1.030.000 | media      | Requisito, no accesorio             |
| 16.05  | Enchapes y acabados                      | m²  |  180 |     $60.000 | $10.800.000 | $7.420.000 | $3.380.000 | baja-media | Comerciales de buena relación       |
| 16.06  | Mesones y vanitorios                     | gl  |    1 |  $3.200.000 |  $3.200.000 | $2.200.000 | $1.000.000 | baja-media | Doble vanity principal              |
| 16.07  | Accesorios de baño                       | gl  |    1 |  $1.500.000 |  $1.500.000 | $1.030.000 |   $470.000 | baja-media | Espejos, toalleros, repisas         |
| 16.08  | Ducha/sauna húmeda + transición wellness | gl  |    1 |  $3.000.000 |  $3.000.000 |         $0 | $3.000.000 | baja-media | Solo F2; sauna es decisión D-011    |
| 16.09  | Ventilación localizada de baños          | gl  |    1 |  $1.500.000 |  $1.500.000 | $1.030.000 |   $470.000 | media      | Extracción a techo/exterior         |
| 16.10  | Soportes y misceláneos                   | gl  |    1 |  $1.500.000 |  $1.500.000 | $1.030.000 |   $470.000 | baja-media | Anclajes, sellos, ajustes           |

---

## 17 — Electricidad, tableros, iluminación y potencia — $42 M (F1 $35 M / F2 $7 M)

| Código | Partida                                    | Un     | Cant | P. unitario |    Subtotal |          F1 |         F2 | Confianza | Fuente/supuesto                         |
| ------ | ------------------------------------------ | ------ | ---: | ----------: | ----------: | ----------: | ---------: | --------- | --------------------------------------- |
| 17.01  | Acometida, tablero general y sub-tableros  | gl     |    1 |  $8.000.000 |  $8.000.000 |  $8.000.000 |         $0 | baja      | Capacidad para el programa final (R-09) |
| 17.02  | Circuitos derivados y tomas                | puntos |  120 |     $90.000 | $10.800.000 |  $8.800.000 | $2.000.000 | baja      | Densidad alta en taller/homelab         |
| 17.03  | Iluminación general PB industrial          | un     |   45 |    $250.000 | $11.250.000 | $11.250.000 |         $0 | baja      | Capas: general integrada a estructura   |
| 17.04  | Iluminación P2 y de tarea                  | gl     |    1 |  $5.000.000 |  $5.000.000 |  $3.000.000 | $2.000.000 | baja      | Residencial + escritorios + cocina      |
| 17.05  | Circuitos dedicados taller/lift/cocina     | gl     |    1 |  $3.000.000 |  $3.000.000 |  $3.000.000 |         $0 | baja      | Impresoras 3D, herramientas, lift       |
| 17.06  | Puesta a tierra, RETIE/RETILAP             | gl     |    1 |  $2.000.000 |  $2.000.000 |    $950.000 | $1.050.000 | media     | Certificación y pruebas                 |
| 17.07  | Protección contra sobretensiones y reserva | gl     |    1 |  $1.950.000 |  $1.950.000 |          $0 | $1.950.000 | baja      | Respaldo/solar según D-020              |

**Riesgo de control:** MEP es el capítulo con confianza **baja** del v0.2. Un estudio de
cargas real del homelab, taller y cocina puede mover este capítulo ±$10 M. Los
conductores finales de F2 se adaptan al diseño vigente.

---

## 18 — Datos, red y preparación Home Assistant — $8 M (F1 $7 M / F2 $1 M)

| Código | Partida                                 | Un     | Cant | P. unitario |   Subtotal |         F1 |       F2 | Confianza | Fuente/supuesto                       |
| ------ | --------------------------------------- | ------ | ---: | ----------: | ---------: | ---------: | -------: | --------- | ------------------------------------- |
| 18.01  | Cableado estructurado y puntos Ethernet | puntos |   40 |     $70.000 | $2.800.000 | $2.500.000 | $300.000 | baja      | Abundantes en taller y escritorios    |
| 18.02  | Rack, patch panels y switches PoE       | gl     |    1 |  $2.200.000 | $2.200.000 | $2.200.000 |       $0 | baja      | Homelab núcleo posterior              |
| 18.03  | Conduits de reserva y guías             | ml     |  150 |     $10.000 | $1.500.000 | $1.500.000 |       $0 | baja      | Rutas estratégicas; prioridad de obra |
| 18.04  | Sensores y preparación Home Assistant   | gl     |    1 |  $1.000.000 | $1.000.000 |   $500.000 | $500.000 | baja      | Vida segura autónoma; confort después |
| 18.05  | Cámaras y puntos de acceso              | gl     |    1 |    $500.000 |   $500.000 |   $300.000 | $200.000 | baja      | NVR en homelab                        |

**Nota:** equipos activos finales (servidores, computadores, dispositivos) son
**equipamiento**, fuera de obra (regla v0.2 §6.6).

---

## 19 — Extracción, ventilación y climatización selectiva — $25 M (F1 $20 M / F2 $5 M)

| Código | Partida                                   | Un  | Cant | P. unitario |   Subtotal |         F1 |         F2 | Confianza | Fuente/supuesto                         |
| ------ | ----------------------------------------- | --- | ---: | ----------: | ---------: | ---------: | ---------: | --------- | --------------------------------------- |
| 19.01  | Extracción localizada taller y car bay    | gl  |    1 |  $6.500.000 | $6.500.000 | $6.500.000 |         $0 | baja      | Captura en fuente (escape, vapores, 3D) |
| 19.02  | Ventiladores HVLS/destratificación        | un  |    2 |  $2.000.000 | $4.000.000 | $4.000.000 |         $0 | baja      | Silenciosos; no climatizar la nave      |
| 19.03  | Extracción baños/wellness/sauna           | gl  |    1 |  $3.000.000 | $3.000.000 | $1.500.000 | $1.500.000 | baja      | Terminación de zonas F2 después         |
| 19.04  | Calefacción selectiva (local/radiante P2) | gl  |    1 |  $5.000.000 | $5.000.000 | $4.000.000 | $1.000.000 | baja      | Donde vive la gente (D-020)             |
| 19.05  | Aire de reposición (make-up air)          | gl  |    1 |  $3.000.000 | $3.000.000 | $2.000.000 | $1.000.000 | baja      | Compatible con presión y combustión     |
| 19.06  | Ductería y difusión                       | ml  |   60 |     $42.000 | $2.520.000 | $1.500.000 | $1.020.000 | baja      | Rutas coordinadas con estructura        |
| 19.07  | Controles, sensores y balanceo            | gl  |    1 |    $980.000 |   $980.000 |   $500.000 |   $480.000 | baja      | Commissioning por zonas                 |

---

## 20 — Cocina fija, muebles, mesones y herrajes — $25 M

| Código | Partida                                  | Un  | Cant | P. unitario |   Subtotal |  Confianza | Fuente/supuesto                        |
| ------ | ---------------------------------------- | --- | ---: | ----------: | ---------: | ---------: | -------------------------------------- |
| 20.01  | Muebles bajos y altos de cocina          | ml  |   12 |    $800.000 | $9.600.000 | baja-media | Fabricación nacional modular           |
| 20.02  | Isla de cocina 4,80 × 1,40               | ml  |  4,8 |    $708.333 | $3.400.000 | baja-media | Con lavaplatos/residuos/almacenamiento |
| 20.03  | Mesones (cuarzo/granito nacional)        | ml  |   14 |    $400.000 | $5.600.000 | baja-media | Mesón + isla                           |
| 20.04  | Herrajes (correderas, bisagras, cajones) | gl  |    1 |  $2.000.000 | $2.000.000 | baja-media | Robustos, reparables                   |
| 20.05  | Lavaplatos y grifería                    | gl  |    1 |  $1.400.000 | $1.400.000 | baja-media | De cocina + isla                       |
| 20.06  | Iluminación de cocina y nichos           | gl  |    1 |  $1.000.000 | $1.000.000 | baja-media | Tarea sobre mesones                    |
| 20.07  | Chute de residuos y mecánicos de ascenso | gl  |    1 |  $1.000.000 | $1.000.000 | baja-media | Mecanismos simples sin motor           |
| 20.08  | Soportes y ajustes                       | gl  |    1 |  $1.000.000 | $1.000.000 |      media | Niveles, fijaciones                    |

**Nota:** electrodomésticos (nevera >700 L, hornos, lavavajillas, congelador) se
registran como **equipamiento**, fuera de obra.

---

## 21 — Closets + cajoneras y bancos fijos del taller — $30 M (F1 $17 M / F2 $13 M)

| Código | Partida                                       | Un  | Cant | P. unitario |   Subtotal |         F1 |         F2 | Confianza  | Fuente/supuesto                    |
| ------ | --------------------------------------------- | --- | ---: | ----------: | ---------: | ---------: | ---------: | ---------- | ---------------------------------- |
| 21.01  | Walk-in closet principal                      | gl  |    1 |  $9.000.000 | $9.000.000 | $9.000.000 |         $0 | baja-media | Vestidor 15–16 m², obra            |
| 21.02  | Closets de suites de hijos                    | un  |    2 |  $2.500.000 | $5.000.000 | $2.500.000 | $2.500.000 | baja-media | Hijo 1 en F1; hijo 2 en F2         |
| 21.03  | Closet de huéspedes                           | gl  |    1 |  $1.500.000 | $1.500.000 |         $0 | $1.500.000 | baja-media | F2                                 |
| 21.04  | D-079 Project Car six-module wall bench       | ml  |    9 |    $722.222 | $6.500.000 | $4.000.000 | $2.500.000 | baja-media | Six 1.50 m modules; one lower heavy-force bay; existing allowance retained pending complete reconciliation |
| 21.05  | D-079 central RC island 4,50 × 1,60           | gl  |    1 |  $3.000.000 | $3.000.000 | $1.500.000 | $1.500.000 | baja-media | Three 1.50 m two-sided modules; +0.84 m test top; mobility and storage open |
| 21.06  | Cajoneras y gabinetes técnicos adicionales    | gl  |    1 |  $3.000.000 | $3.000.000 |         $0 | $3.000.000 | baja-media | F2                                 |
| 21.07  | Almacenamiento de aviones/lavandería/linen    | gl  |    1 |  $2.000.000 | $2.000.000 |         $0 | $2.000.000 | baja-media | F2                                 |
| 21.08  | D-078 Side A shared + D-069 Side B workstation assemblies | un | 2 | TBC | not included | not included | $0 | baja | 7.56 m² total worktop + 5 suspended steel cabinets; reconcile allowances |
| 21.09  | D-071 fixed Side B AV console                | gl  |    1 |          TBC | not included | not included | $0 | baja | 3.40 m accessible console; D-070 reverse-face sideboard deleted; equipment excluded |
| 21.10  | D-079 RC/electronics six-module wall bench   | ml  |    9 |          TBC | not included | not included | $0 | baja | Three fixed + three manual-adjustable modules; localized ESD, solder extraction and services; not traceable in priced subtotal |

`21.08` is an unpriced Phase 1 scope alert. D-078 replaces only the Side A portion of the
former mirrored pair: the current scope is one **5.40 × 0.90 m** shared Side A worktop
with three cabinets plus one retained **3.00 × 0.90 m** Side B worktop with two cabinets.
The total is **7.56 m² of worktop, five 0.70 × 0.75 × 0.62 m suspended steel cabinets and
fifteen drawers**. Do not add it to the $30 M chapter control subtotal until fixed-joinery
and workshop-bench allowances are reconciled and the secondary steel, worktops, brackets,
trays, cabinets and storage loads are specified and quoted.

`21.09` is an unpriced Phase 1 fixed-joinery alert. Coordinate service access, equipment
ventilation and local backing with `14.07`, electrical/data chapters and existing
allowances. The D-070 sideboard is deleted and was never priced. The 100-inch television,
speakers and active AV remain owner equipment outside the physical-works subtotal.

`21.10` exposes rather than adds the existing 9.00 m RC/electronics wall-bench scope. Its
six 1.50 m modules include three fixed modules and three manual-adjustable 0.80 m-deep
clean-electronics modules, localized ESD, one solder source-extraction position and a
removable service spine. Reconcile possible overlap with `21.06`, chapters 17/18/19 and
the inherited workshop allowance before pricing. Do not add the line to the $30 M chapter
subtotal or claim a target increase until local modular quotations and a mock-up exist.

---

## 22 — Escalera metálica + barandas — $12 M

| Código | Partida                                       | Un  | Cant | P. unitario |   Subtotal | Confianza | Fuente/supuesto                     |
| ------ | --------------------------------------------- | --- | ---: | ----------: | ---------: | --------: | ----------------------------------- |
| 22.01  | Estructura metálica de la escalera (2 tramos) | gl  |    1 |  $5.000.000 | $5.000.000 |     media | U con descanso; oculta en núcleo    |
| 22.02  | Peldaños y descansos                          | gl  |    1 |  $2.500.000 | $2.500.000 |     media | Acero antideslizante/madera puntual |
| 22.03  | Barandas y pasamanos                          | ml  |   20 |    $125.000 | $2.500.000 |     media | Vida segura; completa en F1         |
| 22.04  | Iluminación integrada                         | gl  |    1 |    $800.000 |   $800.000 |     media | Integrada a estructura              |
| 22.05  | Protección y pintura                          | gl  |    1 |  $1.200.000 | $1.200.000 |     media | Esquema por exposición              |
| 22.06  | D-082 vertical foldout escape-ladder package | gl  |    1 |          TBC | not included | baja | Proprietary ladder, release, brackets, facade reinforcement, anchors, freight, installation and inspection |

`22.06` is an unpriced supplementary rescue-equipment alert, not part of the required
permanent-stair allowance in `22.01`–`22.05`. Price the complete installed package and
reconcile secondary steel, corrosion protection, facade access and transfer aids with
Chapters 05/06/09/10/13. Do not add it to the $12 M chapter subtotal or credit it as a
code-compliant second exit before CF-012 is resolved.

---

## 23 — Acabados residenciales P2 y pintura puntual — $25 M (F1 $16 M / F2 $9 M)

| Código | Partida                         | Un  | Cant | P. unitario |    Subtotal |         F1 |         F2 | Confianza  | Fuente/supuesto                        |
| ------ | ------------------------------- | --- | ---: | ----------: | ----------: | ---------: | ---------: | ---------- | -------------------------------------- |
| 23.01  | Piso P2 (porcelanato/laminado)  | m²  |  200 |     $55.000 | $11.000.000 | $6.500.000 | $4.500.000 | baja-media | Zonas ocupadas F1; diferidas F2        |
| 23.02  | Paredes P2 (pintura y paneles)  | m²  |  600 |     $12.000 |  $7.200.000 | $5.000.000 | $2.200.000 | baja-media | Calidad por proporción, no por acabado |
| 23.03  | Cielos falsos selectivos P2     | m²  |  120 |     $40.000 |  $4.800.000 | $2.500.000 | $2.300.000 | baja-media | Donde aportan valor técnico            |
| 23.04  | Pintura puntual PB y estructura | gl  |    1 |  $1.000.000 |  $1.000.000 | $1.000.000 |         $0 | media      | Pared posterior y retoques             |
| 23.05  | Rodapiés y remates              | ml  |  100 |     $10.000 |  $1.000.000 | $1.000.000 |         $0 | media      | F1                                     |

---

## 24 — Terraza inmediata de concreto + drenajes — $18 M

| Código | Partida                          | Un  | Cant | P. unitario |    Subtotal | Confianza | Fuente/supuesto                          |
| ------ | -------------------------------- | --- | ---: | ----------: | ----------: | --------: | ---------------------------------------- |
| 24.01  | Losa de plataforma frontal       | m²  |  120 |    $120.000 | $14.400.000 |     media | Extensión de la PB; barbecue y reuniones |
| 24.02  | Drenajes perimetrales y canaleta | ml  |   60 |     $40.000 |  $2.400.000 |     media | Protección del edificio (R-05)           |
| 24.03  | Juntas, sello y acabado          | gl  |    1 |  $1.200.000 |  $1.200.000 |     media | Continuidad visual con piso interior     |

---

## 25 — Elevador automotriz + instalación/provisión civil — $15 M (F1 $4 M / F2 $11 M)

| Código | Partida                                       | Un  | Cant | P. unitario |    Subtotal |         F1 |          F2 | Confianza | Fuente/supuesto                         |
| ------ | --------------------------------------------- | --- | ---: | ----------: | ----------: | ---------: | ----------: | --------- | --------------------------------------- |
| 25.01  | Equipo elevador 2 postes ≈4 t                 | un  |    1 | $10.000.000 | $10.000.000 |         $0 | $10.000.000 | media     | Referencia comercial $9,5–10,9 M (v0.2) |
| 25.02  | Obra civil local (cimentación/engrosamiento)  | gl  |    1 |  $1.500.000 |  $1.500.000 | $1.500.000 |          $0 | media     | Engrosamiento local, no global (regla)  |
| 25.03  | Instalación, alineación y ensayos             | gl  |    1 |  $1.000.000 |  $1.000.000 |         $0 |  $1.000.000 | media     | F2                                      |
| 25.04  | Alimentación eléctrica dedicada y desconexión | gl  |    1 |  $1.000.000 |  $1.000.000 | $1.000.000 |          $0 | media     | Ruta y desconexión visible              |
| 25.05  | Iluminación y seguridad de la zona            | gl  |    1 |  $1.500.000 |  $1.500.000 | $1.500.000 |          $0 | media     | Zona de doble altura                    |

**Regla:** el modelo o envolvente de cargas debe aprobarse **antes de vaciar la losa**
(D-022); no colocar pernos embebidos genéricos.

---

## Radar de reducción de costos

Priorizado por relación ahorro/esfuerzo, sobre las partidas atómicas. Los porcentajes
son órdenes de magnitud de investigación; ningún ahorro se contabiliza hasta cotizar.

| #   | Oportunidad                                                                                       | Partidas afectadas         | Control actual | Potencial estimado         | Riesgo                    | Acción                                                                                                                                          |
| --- | ------------------------------------------------------------------------------------------------- | -------------------------- | -------------- | -------------------------- | ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Modulación bays 6 m, perfiles estándar, acero S355 en principales                                 | 05.01, 05.02, 06.01–06.03  | $200 M         | −$15 a −$30 M              | bajo                      | Predimensionar 3 modulaciones (D-019)                                                                                                           |
| 2   | Envolvente por capas (teja + lana facing + liner) vs. panel aislado — **precios verificados** [V] | 08.01, 09.01               | $165 M         | −$20 a −$35 M              | medio-alto (condensación) | Doble hoja FLA020 $91.466/m² vs. panel FLA030 $152.266/m²; ver `tecnicas_que_abaratan_costos.md` §3.2.1; cotizar local + punto de rocío (D-020) |
| 3   | Geotecnia temprana; espesor y refuerzo realistas; engrosamiento local                             | 03.01–03.03, 04.02, 04.09  | $125 M         | −$5 a −$15 M               | bajo                      | Estudio de suelo antes de PE-1                                                                                                                  |
| 4   | Vidrio/portones en medidas estándar con 2–3 cotizaciones                                          | 11.01–11.03, 12.01, 13.01  | $82 M          | −$5 a −$10 M               | bajo                      | Cotizaciones comparables PE-2                                                                                                                   |
| 5   | No climatizar la nave; HVLS + calefacción local; iluminación por capas                            | 17.03, 17.04, 19.02, 19.04 | $67 M          | −$5 a −$10 M               | bajo                      | Modelo térmico por zonas                                                                                                                        |
| 6   | Cocina y carpintería nacional modular ampliable                                                   | 20.01–20.04, 21.04         | $55 M          | −$3 a −$6 M                | bajo                      | Fábrica nacional; prototipos                                                                                                                    |
| 7   | Fases F1/F2 ya decidida (D-016)                                                                   | Fase 2                     | $74 M          | ahorro de caja F1 ≈$77,7 M | medio                     | Remobilización y escalamiento F2 presupuestados                                                                                                 |

**Advertencias del radar:**

- Las técnicas 1 y 3 **no reducen seguridad**: deciden estructura y cimentación por
  cálculo, no por recorte.
- La técnica 2 solo se adopta con cálculo de punto de rocío, sellado de aire y control
  de humedad; si el panel aislado cotiza poco más por m², puede no valer el riesgo.
- Ninguna partida se reduce por etiqueta; toda reducción exige alcance eliminado
  documentado (control de cambios).

## Precios implícitos vs. referencias de mercado

Detección de "sorpresas" potenciales: dónde el control v0.2 es más agresivo que la
referencia observada. Las referencias marcadas **[V]** fueron re-consultadas en vivo en
CYPE Colombia / proveedores el **2026-08-11** (ver [auditoría](auditoria_de_costos_2026_08.md)):

| Material/sistema                    | Precio implícito del desglose | Referencia CYPE/market                                  | Brecha           | Lectura                                                                                                      |
| ----------------------------------- | ----------------------------- | ------------------------------------------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------ |
| Acero estructural instalado (kg)    | $7.054/kg combinado           | [V] $6.587,26 (A36) / $7.375,64 (A572 Gr.50)            | dentro del rango | El riesgo es el **tonelaje**, no el $/kg                                                                     |
| Concreto cimentación (m³)           | $730.000                      | [V] $520.984,68 (21 MPa) / $727.665 (zapata armada)     | ≈0 %             | Alineado (zapata); el 21 MPa del desglose es más caro que la referencia                                      |
| Losa PB (648 m², sistema completo)  | ≈$128.000/m²                  | [V] $177.239,20/m² (piso industrial RSI007)             | menor            | La losa es a la vez estructura; desglose más delgado (15 cm, pulido parcial)                                 |
| Panel sándwich fachada (m²)         | $140.000                      | [V] $152.266,44 (FLA030)                                | **−8 %**         | **Subestimado**; cotizar antes de PE-2 (sin perfiles térmicos)                                               |
| Fachada por capas / doble hoja (m²) | — (alternativa)               | [V] $91.465,77 (FLA020, bandeja + lana 100 mm + lámina) | −40 % vs. panel  | **Oportunidad de ahorro** §3.2.1 de `tecnicas_que_abaratan_costos.md`; requiere barrera de vapor lado cálido |
| Fachada simple de lámina (m²)       | — (sin aislamiento)           | [V] $29.438,34 (FLA010)                                 | −81 % vs. panel  | Solo para zonas no acondicionadas o secundarias                                                              |
| Panel sándwich cubierta (m²)        | $101.000                      | [V] $101.009,74 (QTM010)                                | ≈0 %             | Alineado                                                                                                     |
| Evento principal de vidrio (m²)     | $1.180.000                    | [V] $1.290.363,67 (muro cortina FMC010)                 | **−8 % a −20 %** | Subestimado si el evento escala a muro cortina o vidrio templado                                             |
| Metaldeck P2 (m²)                   | $152.000                      | [V] $150.399,51 (EHX011)                                | ≈0 %             | Alineado                                                                                                     |
| Tabique drywall (m²)                | $95.000                       | [V] $83.629,82 (FBY010 básico)                          | +14 %            | Incluye lana y refuerzo acústico                                                                             |
| Elevador 2 postes 4 t               | $10.000.000                   | [V] $10.900.000 (Protalleres PT-240SC)                  | dentro del rango | Seleccionar antes de la losa                                                                                 |

**Conclusión del radar de precios:** los puntos donde el target es más optimista que el
mercado son **fachada aislada** (09) y **vidrio principal** (12). Junto con el tonelaje
de acero (05/06), son los tres frentes que pueden producir las "sorpresas" de la Fase 1.

## Indicadores de control por capítulo

| Capítulo            | Control |              Unidad física de control | Indicador implícito                 |
| ------------------- | ------- | ------------------------------------: | ----------------------------------- |
| 03 Cimentaciones    | $35 M   |         36 m³ concreto + 950 kg acero | ≈$972.000/m³ de obra de cimentación |
| 04 Losa PB          | $83 M   |                                648 m² | ≈$128.000/m²                        |
| 05+06 Estructura    | $200 M  |                             28.350 kg | ≈$7.054/kg; ≈31 kg/m² de proyecto   |
| 07 Metaldeck        | $41 M   |                                270 m² | ≈$152.000/m²                        |
| 08 Cubierta         | $70 M   |                                648 m² | ≈$108.000/m²                        |
| 09 Fachadas         | $95 M   |                          640 m² netos | ≈$148.000/m²                        |
| 12 Vidrio principal | $38 M   |                                 28 m² | ≈$1.357.000/m²                      |
| 14 Divisiones       | $38 M   |          ≈280 m² de tabique + puertas | ≈$136.000/m²                        |
| 20 Cocina           | $25 M   |           12 ml muebles + 4,8 ml isla | ≈$1.488.000/ml de cocina            |
| 21 Closets/taller   | $30 M   | 1 vestidor + 3 closets + 13 ml bancos | por pieza/metro                     |

## Reconciliación de fases

| Concepto                       |           Fase 1 |          Fase 2 |            Total |
| ------------------------------ | ---------------: | --------------: | ---------------: |
| Obra física (suma de partidas) |     $867.000.000 |     $74.000.000 |     $941.000.000 |
| Contingencia heredada 5 %      |      $43.350.000 |      $3.700.000 |      $47.050.000 |
| **Control por fase**           | **$910.350.000** | **$77.700.000** | **$988.050.000** |

El desglose F1/F2 de las partidas 14–19, 21, 23 y 25 es una hipótesis de reparto que
debe reemplazarse por medición de la zona diferida real. Los costos que la Fase 2
añade por remobilización, protección, escalamiento y trámites **no están en esta
tabla** (se presupuestan aparte en la estrategia de dos fases).

## Correcciones de medición y partidas ausentes — insumo v0.4 (D-030)

Sección incorporada por la [auditoría de costos 2026-08](auditoria_de_costos_2026_08.md).
**No cambia el target v0.2** ni la distribución F1/F2: registra los puntos donde la medición
o el alcance difieren de lo que se puede sostener con la geometría del programa y las
referencias verificadas. Cada ítem debe cotizarse o recalcularse en PE-1/PE-2 antes de
reemplazar la partida correspondiente.

### Correcciones de medición confirmadas

| Partida                         | Control v0.2                             | Corrección                                      | Evidencia                                                                                                      | Efecto                                 |
| ------------------------------- | ---------------------------------------- | ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| 05.03 Vigas de entrepiso P2     | 3.000 kg (≈11 kg/m²)                     | **9.000–11.000 kg** (≈35–40 kg/m² de entrepiso) | Cálculo paramétrico: viguetas cada 1,5 m + vigas de borde y apoyos; rango de entrepisos compuestos 35–55 kg/m² | +$45–60 M (dentro del riesgo de 05/06) |
| 05.01+05.02 Pórticos y cubierta | 15.500 kg                                | **≈23–24 t**                                    | 7 pórticos × (columnas HEA 300 + viga 18 m IPE 500 con cartelas) ≈23,3 t; cartelas y placas ≈15 %              | +$55–100 M total 05/06                 |
| 08.01 Cubierta                  | 620 m²                                   | **≈655–665 m²**                                 | 648 m² + solape/pendiente real                                                                                 | +$3–4 M                                |
| 09.01 Fachada neta              | 640 m²                                   | **≈680 m²**                                     | 810 m² brutos − ~130 m² de vanos                                                                               | +$5–6 M                                |
| 03 Cimentación                  | 36 m³ (24 zapatas/pedestales + 12 vigas) | **≈42–50 m³**                                   | 16 columnas × (zapata 1,8×1,8×0,5 + pedestal) ≈30 m³ + vigas                                                   | +$5–10 M si el suelo no es bueno       |

### Partidas ausentes confirmadas (falta partida o está por debajo de mercado)

| Partida                                                                                                                     | Situación en v0.2                                         | Corrección propuesta           | Nota                                                                                                 |
| --------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- | ------------------------------ | ---------------------------------------------------------------------------------------------------- |
| **Protección contra incendio y vida segura** (detección, alarma, extintores/red en taller, car bay y homelab, señalización) | Sin partida; el v0.2 declara "sistemas de incendio" en F1 | **Nuevo capítulo 26: $8–15 M** | Obligatorio (taller + car bay + sauna + P2); hoy inexistente                                         |
| **SG-SST, laboratorio/ensayos y gestión de residuos**                                                                       | Solo $1 M de "ensayos iniciales" en 01.06                 | **Nuevo capítulo 27: $8–15 M** | Obligaciones de obra colombiana (Decreto 1072/2015, Resolución 0141, RETIE/RETILAP ya está en 17.06) |
| Seguros todo riesgo + RC (01.05)                                                                                            | $2 M                                                      | **$5 M**                       | ≈0,3–0,5 % del valor de obra + RC                                                                    |
| Sauna familiar F2 (16.08)                                                                                                   | $3 M                                                      | **$8–15 M**                    | Cabina, calefactor, bancas, barrera de vapor, ventilación para 6 personas                            |
| Calentamiento de agua (15.04)                                                                                               | $2,3 M                                                    | **$4–5 M**                     | Clima frío de altura exige más potencia                                                              |
| Acometida eléctrica rural / transformador                                                                                   | No modelado (R-09)                                        | +$10–30 M                      | Costo de predio si el lote lo exige; fuera de obra hasta confirmarse                                 |
| CCTV mínimo (18.05)                                                                                                         | $500.000                                                  | $1–2 M o equipamiento          | Cámaras pueden clasificarse como equipamiento                                                        |

### Propuesta de estructura para v0.4

- **Capítulo 26 — Protección contra incendio y vida segura:** detección, alarma, extintores,
  red/agente en taller y car bay, señalización y egreso P2 (segunda salida abierta). Separa lo
  que hoy no tiene partida y es requisito, no acabado.
- **Capítulo 27 — Seguridad y salud, laboratorio, ensayos y residuos:** SG-SST, ensayos de
  concreto/suelos, certificaciones y manejo de residuos; sacarlo del capítulo 01 implícito.
- **Contingencia de diseño separada:** mantener 5 % de obra + reserva de 3–5 % por
  incertidumbre de diseño hasta PE-2, cuando se reemplace por contingencia real de cantidades.

Cualquier adopción de estas correcciones en los totales del capítulo será un **cambio de
alcance/costo** y debe pasar por el control de cambios y por la puerta PE-1/PE-2, no editarse
silenciosamente.

## Protocolo de validación (orden de cotización recomendado)

1. **Estructura (05/06):** predimensionamiento con 3 modulaciones y 2 sistemas;
   registrar kg/m² y costo fabricado/montado. Reemplaza 05.01–05.05 y 06.01–06.06.
2. **Losa/cimentación (02/03/04):** geotecnia del predio candidato; m³, refuerzo,
   subbase, juntas y acabado. Reemplaza 02.01–04.09.
3. **Envolvente (08/09/10):** m² netos por fachada y cubierta, espesores, remates y
   puentes térmicos; cotizar panel aislado vs. sistema por capas.
4. **Vidrio/portones (11/12/13):** dimensiones y desempeño; 2–3 cotizaciones
   comparables en medidas estándar.
5. **MEP (15/17/18/19):** cargas, puntos, circuitos, tuberías, equipos y
   commissioning; reemplaza las partidas globales por cantidades medidas.
6. **Baños/cocina/carpintería (16/20/21/23):** aparatos, herrajes, metros lineales y
   prototipos; separar equipamiento.

Cada partida reemplazada conserva: código, cantidad, precio, fuente, municipio, fecha,
confianza y variación frente a este desglose.

## Control de cambios y trazabilidad

- v0.2 → v0.3: desglose atómico del mismo target ($941 M). No cambia el total ni la
  contingencia; **no** mejora la confianza global (sigue baja-media).
- v0.3 (D-030/D-031): integración de la auditoría de costos — verificación de precios en
  vivo (CYPE/proveedores, 11-08-2026), correcciones de medición y partidas ausentes
  (cap. 26 incendio, cap. 27 SG-SST/ensayos, seguros, sauna, calentamiento) como insumo
  v0.4. **El target no cambia** hasta cotizar en PE-1/PE-2.
- v0.3.9 (D-080): adds unpriced reconciliation alerts `09.04` and `14.08` for the
  differentiated P2 wall schedule. **No subtotal, phase, contingency or target changes.**
- v0.3.10 (D-082): adds unpriced alerts `13.07` and `22.06` for the operable rescue
  window and complete vertical foldout-ladder package. **No subtotal, phase, contingency
  or target changes.**
- v0.3.11 (D-083): updates Side A/Side B desk-window measurements, records 54.72 m² of
  active P2 windows and adds the non-additive reconciliation alert `13.08` for the 5.565 m²
  net vertical-glazing variance. The optional dining study remains excluded. **No subtotal,
  phase, contingency or target changes.**
- Cambios futuros: registrar origen, necesidad, alternativas, costo, plazo, efecto
  técnico, decisión y partida afectada. Ningún ahorro se contabiliza hasta documentar
  el alcance eliminado.

## Fuentes de precio referenciadas (corte 2026-08-11)

Las fuentes CYPE y el elevador marcadas **[V]** fueron re-consultadas en vivo el 11-08-2026
en la [auditoría de costos](auditoria_de_costos_2026_08.md) y sus valores coinciden con los
usados en este desglose.

- DANE ICOCED: https://www.dane.gov.co/index.php/estadisticas-por-tema/precios-y-costos/indice-de-costos-de-la-construccion-de-edificaciones-icoced
- Boyacá, Resolución 0033 de 2026 (precios regionales):
  https://www.boyaca.gov.co/resolucion-0033-de-24-de-abril-de-2026/
- CYPE Colombia — acero estructural:
  https://colombia.generadordeprecios.info/obra_nueva/Estructuras/Acero/Perfiles_estructurales/
- CYPE Colombia — concreto y cimentaciones:
  https://colombia.generadordeprecios.info/obra_nueva/Cimentaciones/
- CYPE Colombia — piso industrial tratado (RSI007):
  https://colombia.generadordeprecios.info/obra_nueva/Revestimientos/Pisos/RSI_Sistemas_de_pisos_industriales/RSI007_Piso_industrial_de_concreto_tratado.html
- CYPE Colombia — panel sándwich de fachada (FLA030):
  https://colombia.generadordeprecios.info/rehabilitacion/Fachadas_y_muros_divisorios/Fachadas_ligeras/Metalicas/FLA030_Fachada_de_paneles_sandwich_aislant.html
- CYPE Colombia — cubierta sándwich (QTM010):
  https://colombia.generadordeprecios.info/rehabilitacion/Cubiertas/Inclinadas/QTM_Paneles_sandwich_aislantes_met/QTM010_Cubierta_inclinada_de_paneles_sandw_0_0_0_0_0_0_0_0_0_0_1_0.html
- CYPE Colombia — losa metaldeck (EHX011):
  https://colombia.generadordeprecios.info/obra_nueva/Estructuras/Concreto_armado/Losas_compuestas_metaldeck/EHX011_Losa_compuesta_metaldeck_con_lamina.html
- CYPE Colombia — muro divisorio de placas de yeso (FBY010):
  https://colombia.generadordeprecios.info/obra_nueva/Fachadas_y_muros_divisorios/FB_Muros_divisorios_interiores_de/De_placas_de_yeso_laminado/FBY010_Muro_divisorio_interior_de_placas_d.html
- CYPE Colombia — muro cortina de aluminio:
  https://colombia.generadordeprecios.info/rehabilitacion/Fachadas_y_muros_divisorios/Muros_cortina/Aluminio/Muro_cortina_de_aluminio.html
- Elevador automotriz 2 columnas ≈4 t (referencia comercial):
  https://protalleres.com/product/elevador-dos-columnas-4tl/

**Nota de confiabilidad:** los precios CYPE son configuraciones de referencia, no
cotizaciones. Toda cifra que llegue al presupuesto contractual debe originarse en
Construdata, cotizaciones locales de Boyacá y APU con cantidades medidas.
