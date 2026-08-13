# Bases de la estructura metálica — predimensionamiento conceptual

**Estatus:** base de coordinación; hipótesis de ingeniería; no es memoria de cálculo
ni diseño profesional
**Versión:** 0.5
**Fecha de corte:** 2026-08-12
**Fuentes:** constitución del proyecto, programa arquitectónico v0.2, plano conceptual
v0.2, bases estructurales y civiles v0.2, presupuesto desglosado de control, auditoría de
costos 2026-08, herramientas digitales (modelos E0/E1), D-043/D-045/D-047/D-048 y técnicas que
abaratan costos.
**Aprobación pendiente:** ingeniero estructural, arquitecto coordinador, propietario.

## Propósito

Este documento fija las bases conceptuales para abrir la decisión **D-019** (sistema
estructural conceptual y modulación) y producir el **predimensionamiento de comparación**
que exige la puerta económica PE-1. Establece qué se comparará, con qué hipótesis de
carga y con qué criterios de peso, para que el ingeniero estructural, y no un motor
automático, fije el tonelaje real.

> **Regla del expediente:** aquí no se seleccionan perfiles finales, no se escribe una
> biblioteca NSR-10 y ningún resultado numérico es apto para construir.

## Current E1 integration status — 2026-08-12

The active visual synthesis is
[DH-EST-E1-001 — Integrated Structural E1 Screening](../../planos/estructura/DH-EST-E1-001_SINTESIS-ESTRUCTURAL.svg),
with the focused
[DH-EST-E1-002 — Vertical Continuity and Stair-Enclosure Frame](../../planos/estructura/DH-EST-E1-002_CONTINUIDAD-VERTICAL-ESCALERA.svg),
supported by the updated
[structural-to-drawing integration study](estudio_integracion_estructura_planos.md) and
the [E1 screening report](../08_investigacion/e1_structural_screening.md).

The sheet does **not** select M60 or the modified-Warren roof. D-047 defines that truss as
a neutral computational specimen. D-043 fixes only the P2 Great Wall gravity intent, and
D-045 retains six continuous-overhang beam lines only as an E0 hypothesis. The integrated
sheet exposes member, connection, lateral, diaphragm, fire, erection, base-plate, and
foundation evidence while every system-level design gate remains blocked.

D-048 adds a geometry-controlled study: continue the Great Wall stair-jamb columns at
(31.50, 7.40) and (31.50, 11.00) and add rear enclosure columns at (36.00, 7.40) and
(36.00, 11.00). The enclosure frame—not the stair flights—is the preferred structural
study. No section, bracing topology, collector, drift joint, base, foundation, fire
protection, or roof gravity role is selected.

Revision 0.4 also records a precedence correction: earlier derived prose describing
three P2 beams, an assigned longitudinal shear-core role, or an adopted strip foundation
is superseded by D-043/D-045 and `structure_system.json` v0.3. No foundation type or
longitudinal lateral role is adopted.

## 1. Geometría de referencia

| Parámetro | Valor | Estatus |
|---|---:|---|
| Nave | 18,00 × 36,00 m | DCV fuerte, no hard rule dimensional |
| Huella PB | 648 m² | DCV |
| P2 posterior | 18,00 × 15,00 m = 270 m² | DCV |
| Inicio de P2 | X = 21,00 m | DCV |
| Doble altura delantera | 18,00 × 21,00 m = 378 m² | DCV |
| Nivel terminado P2 | ≈ +3,80 m | DCV, ajustar con canto real |
| Altura libre bajo P2 | ≈ 3,05–3,20 m | DCV |
| Altura interior de nave | ≈ 7,20–7,80 m | DCV |
| Eave baja / eave alta | 7,20 m / 7,80 m (cubierta de un solo faldón) | hipótesis de sección |
| Cubierta | única, continua, simple; sin tragaluces por defecto | hard rule |
| Retícula de coordinación | 6 × 6 m | coordinación; no obliga columnas interiores |

La cubierta es de **un solo faldón** (mono-pitch): la diferencia 7,80 − 7,20 = 0,60 m
sobre 18,00 m de luz transversal da una pendiente de **1:30 = 3,33 %**. Esta pendiente debe
verificarse con el fabricante de cubierta y el drenaje; si no basta para lámina estándar,
se evalúa ajustar la eave alta (la unidad formal de la cubierta es hard rule, la cota no).

> **Alerta de compatibilidad (hallazgo H-02).** 3,33 % sobre un faldón continuo de 18,00 m
> está por debajo del mínimo habitual de los paneles sándwich con solapes (del orden de
> 5–10 % según fabricante), que es el sistema declarado en `bases_de_diseno.md` y el que
> carga `structure_system.json`. Con esta pendiente el sistema tiende a forzarse hacia junta
> alzada engatillada en paños de 18 m con clips deslizantes: otro sistema, otro precio y
> otro detalle de alero y de curb de claraboya. **Subir la eave alta a ≈ 8,10–8,30 m lleva la
> pendiente a 5–6 % sin tocar el faldón único, ni las alturas libres, ni la eave baja.** Es
> una decisión de cota (DCV), no de forma, y requiere registro del propietario antes de
> aplicarse: este documento no la adopta.

## 2. Sistemas y modulaciones a comparar (D-019)

Matriz de predimensionamiento recomendada: **2 sistemas × 3 modulaciones**.

### 2.1 Sistemas

1. **Pórticos portal de luz completa (18 m).** Columnas HEA/HEB + viga de cubierta
   (IPE) con cartela de alero; bases articuladas típicas para naves; arriostramiento
   longitudinal en cubierta y paños opacos. Favorito por simplicidad de fabricación en
   naves de luz media.
2. **Cercha / viga reticulada de 18 m sobre columnas.** Cuerdas IPE o HEA con
   diagonalizado; menor peso de acero en luz larga, mayor detalle y costo de
   fabricación/conexiones. Decidir por datos (tonelaje + costo fabricado/montado), no por
   preferencia estética.

### 2.2 Modulaciones longitudinales

| ID | Bay | N.º de pórticos (líneas) | Observación |
|---|---|---|---|
| M-45 | 4,50 m | 9 | Más pórticos, piezas ligeras; más cimentaciones |
| M-60 | 6,00 m | 7 | Referencia de la auditoría y del radar de costos |
| M-90 | 9,00 m | 5 | Pórticos más pesados, menos fundaciones; vigas P2 mayores |

Se comparará kg/m² (sobre 918 m² conceptuales), tonelaje total, costo fabricado/montado
estimado y compatibilidad con el programa (P2, lift, vidrios, portones).

### 2.3 Sistemas adicionales investigados — eliminar columnas interiores (insumo E1)

Investigación externa (SCI / steelconstruction.info, AISC / US Steel) para ampliar la
matriz de D-019. Todo es **hipótesis para el modelo E1**: el ingeniero estructural fija el
sistema con tonelaje y costo fabricado/montado. Principio rector: **todas las columnas se
concentran en los dos muros laterales (Y = 0 y Y = 18) o dentro de las particiones del P2;
la nave queda 100 % libre.**

**Cubierta de 18 m — un solo faldón:**

1. **Cercha tubular expuesta (Warren/Pratt), canto L/12–L/15 (≈ 1,20–1,50 m).**
   Opción más liviana del E0 (36–40 t vs. 49–58 t del pórtico). Columnas solo en muros
   laterales (HEA/HEB200), bases articuladas. Servicios pasan por el alma. Es la estética
   "estructura visible" del concepto. El pórtico mono-pitch eficiente suele limitarse a
   ≈ 15 m; con 18 m y pendiente 1:30 la cercha es más racional.
2. **Pórtico portal atado (*tied portal*).** Un tirante/tensor horizontal entre las
   cabezas de columna reduce el desplazamiento de alero (deriva de viento) y los momentos
   de columna y viga; requiere análisis de segundo orden. Permite bajar de HEA500 a
   secciones menores conservando la continuidad del pórtico. El tirante es visible:
   estudiarlo como recurso arquitectónico o llevarlo oculto en el plano de cubierta.
3. **Pórtico con cartela de alero (haunch ≈ 10 % de la luz) + columnas laced/battened.**
   La cartela aumenta rigidez y resistencia donde el momento es máximo; la columna de
   celosía (dos perfiles con presillas) es mucho más rígida en plano por igual peso, lo
   que ataca la deriva sin columnas interiores.
4. **Cable-stayed (mast + tensores).** Se descarta como solución principal: bracing muy
   conspicuo, mantenimiento alto y puntos de paso por la envolvente; no encaja en la
   lectura de "nave simple" del concepto.
5. **Space frame sobre la doble altura (18 × 21 m).** Posible gesto moderno con apoyos
   solo en perímetro; nudos esféricos, costo y complejidad de fabricación altos; solo si
   el propietario lo valida como pieza arquitectónica deliberada.

**Entrepiso P2 (18 × 15 m) sin columnas en la zona doméstica:**

1. **Staggered truss (cerchas escalonadas de canto completo)** — desarrollado por MIT /
   US Steel para hoteles y apartamentos. Cerchas de piso que cruzan el ancho (18 m)
   apoyadas **solo en las columnas de los dos muros largos**, escalonadas en planta (media
   crujía), con **canto igual a la altura del muro** (d/L ≈ 0,13–0,19; aquí ≈ 3,0 m); la
   losa apoya entre el cordón inferior de una cercha y el superior de la adyacente, con
   paneles de deck profundo (sin viguetas) de hasta ≈ 6 m sin apuntalar.
   Ventajas: áreas libres de hasta ≈ 18 m sin columnas interiores, altura de piso compacta,
   deriva pequeña, gran resistencia al viento y fundaciones concentradas. En el P2 las
   cerchas se esconden dentro de las particiones de las suites (closets, baños, hall), de
   modo que cocina y comedor en PB quedan 100 % libres. La frecuencia del panel no se
   calcula sin ficha de deck y sección compuesta; vibración y carga muerta se verifican
   en E1 con el criterio normativo aplicable.
2. **Cercha compuesta de piso (*composite truss*).** Luces > 18 m con la losa como cordón
   superior; más ligera que viga llena, pero exige apuntalamiento temporal y más superficie
   de protección contra incendio.
3. **Vigas celulares (10–16 m) y girders de canto variable (10–20 m).** Integran servicios
   en su propio canto; respaldo para vigas secundarias y de borde.
4. **Mezzanine colgado de la cubierta.** El P2 se apoya en la estructura de techo en vez de
   en columnas de PB; útil si la frontera de P2 debe quedar totalmente despejada; coordinar
   cargas colgadas con la cercha de cubierta.
5. **Viga de borde en X = 21,00 m (luz ≈ 18 m).** D-043 exige una **cercha de borde de
   canto completo** integrada por encima de +3,80 m. No puede invadir la altura libre de
   PB; montantes y diagonales se coordinan con el frente del P2.

## 3. Hipótesis de carga — sin nieve

**Contexto climático:** altiplano boyacense (Tunja–Paipa–Duitama, ≈ 2.600–2.800 m s. n. m.).
**No existe nieve de diseño** en la zona; **no se incluye carga de nieve**. Las acciones
que gobiernan son: peso propio, cargas de uso, **viento** (corredores del altiplano) y
**sismo** (Colombia es país sísmico; Boyacá riesgo sísmico moderado). La respuesta al
clima es de envolvente (frío nocturno, condensación, infiltración, radiación solar de
altura), no de carga.

### 3.1 Cargas permanentes (hipótesis)

| Elemento | Valor de hipótesis | Fuente/observación |
|---|---:|---|
| Cubierta (panel sándwich ≈ 50 mm o sistema por capas) | 0,15–0,25 kN/m² | CYPE QTM010/FLA030; sistema por capas más liviano |
| Correas y soportes de cubierta | 0,10 kN/m² | derivado |
| Cielo, instalaciones, ductos colgados | 0,15 kN/m² | coordinación MEP |
| Entrepiso P2 (metaldeck + loseta + acabado) | 2,3–2,6 kN/m² | metaldeck 10 cm ≈ 2,5 kN/m² |
| Particiones y acabados P2 | 1,0–1,5 kN/m² | uso residencial |
| Fachada/panel sobre girts | 0,15–0,25 kN/m² | vertical |

### 3.2 Cargas vivas (hipótesis)

| Elemento | Valor | Observación |
|---|---:|---|
| Cubierta | 0,50 kN/m² | cubierta liviana; sin mantenimiento frecuente |
| Entrepiso P2 residencial | 1,80–2,00 kN/m² | dormitorios, hall, wellness |
| Zona técnica PB (carro + taller + racks) | 3,00–5,00 kN/m² | uso industrial-liviano; verificar con equipos |
| Lift automotriz | carga puntual por poste según ficha (≈ 4 t nominal) | **dato obligatorio pendiente (D-022)** |
| Sauna/jacuzzi opcional | carga operativa + agua (jacuzzi ≈ 300–500 kg/m² si se adopta) | decisión D-025 |

### 3.3 Viento (hipótesis de altura y presión, por definir con norma)

- Velocidad básica de viento de referencia para el interior del altiplano: orden de
  **25–30 m/s** (ráfaga 3 s a 10 m), a confirmar con NSR-10 B.6 y el municipio del predio.
- Presión dinámica qz ≈ 0,40–0,55 kN/m² a la altura de eave (7–8 m).
- Coeficientes de presión para la nave: barlovento +0,8; sotavento −0,3 a −0,5; cubierta
  −0,9 a −0,3 según pendiente y zona. Los valores finales son del ingeniero.
- Efectos: succión de cubierta (controla correas/anclajes), viento transversal sobre
  pórticos (controla deriva y columnas) y viento longitudinal (arriostramiento de
  fachadas opacas).

### 3.4 Sismo (hipótesis de espectro, por definir con norma)

- Zona de amenaza sísmica intermedia del altiplano: aceleración espectral de referencia
  en el orden de Aa ≈ Av ≈ 0,15–0,25 g (confirmar con NSR-10 Título A y microzonificación).
- Estructura metálica liviana de gran luz con P2 pesado: la masa concentrada del entrepiso
  a +3,80 m y la deriva de columnas de 7 m controlan.
- Para el predimensionamiento de comparación (modelo E0/E1) se usa un coeficiente de cortante
  basal **hipótesis Cs ≈ 0,08–0,12** aplicado a la masa, marcado como supuesto de ingeniero.

### 3.5 Combinaciones de carga (hipótesis típicas de LRFD; el ingeniero las define)

- `1,4·D`
- `1,2·D + 1,6·L (+ 0,5·Lr)`
- `1,2·D + 1,0·W + 0,5·L`
- `0,9·D + 1,0·W`
- `1,2·D + 1,0·E + 0,5·L`
- `0,9·D + 1,0·E`

No se incorpora S (nieve). Estas combinaciones se almacenan como hipótesis versionadas,
**no como biblioteca NSR-10**.

## 4. Estrategia de estabilidad

Se comparan las tres estrategias que pide el concepto (sección 35.2 del documento
original):

1. **Arriostramiento en paños opacos** (fachadas de servicio, testeros y cubierta) —
   libera los grandes eventos de vidrio; recomendada como primera línea.
2. **Diagonales visibles deliberadas** en algunos paños (recurso arquitectónico estudiado
   por las visualizaciones, no decoración).
3. **Pórticos resistentes a momento** solo si el costo lo justifica; la nave de 18 m con
   bases articuladas y arriostramiento suele ser más eficiente.

La longitud de 36 m y los dos testeros opacos permiten colocar el arriostramiento
longitudinal (cubierta + muros) en los paños de servicio. Los eventos de vidrio (ventanales
técnicos 7,20 m, vidrio de sala) reducen paños de arriostramiento disponibles y deben
coordinarse simultáneamente (regla del concepto: estructura, fachada y luz se diseñan juntos).

Medidas adicionales para controlar la deriva **sin columnas interiores expuestas o arbitrarias** (todas hipótesis
E1; el E0 mostró que la deriva de viento gobierna las columnas):

- **Cordón / viga longitudinal de cubierta (wind girder)** en el plano del faldón para
  repartir el viento transversal hacia los arriostramientos de testeros y reducir la
  deriva individual de cada pórtico.
- **Tirante de alero (*tied portal*)** si se conserva la continuidad de pórtico: atar las
  cabezas de columna reduce el desplazamiento lateral y los momentos de base.
- **Knee braces / diagonales cortas** en el encuentro columna–cercha en pórticos testeros
  (refuerzo local sin ocupar la nave).
- **Bases fijas en los pórticos testeros (gable frames) / portalized bays** en las
  fachadas opacas: entregan rigidez longitudinal sin columnas en el interior.
- **La caja rígida del P2 como diafragma**: con staggered truss o cerchas de piso, el
  volumen P2 actúa como núcleo rígido (celosía de gran altura) que rigidiza todo el
  edificio en dirección longitudinal y reduce la deriva general — beneficio estructural
  adicional del sistema.

## 5. Entrepiso P2

- Sistema de referencia: **losa compuesta metaldeck** (lámina + loseta ≈ 10 cm, conectores)
  con viguetas cada ≈ 1,5 m y vigas principales entre pórticos (bay longitudinal).
- El frente abierto en X = 21,00 m (borde del P2 hacia la doble altura) requiere una **viga
  de borde** de luz ≈ 18 m con apoyos puntuales integrados al núcleo/cocina; esta línea es
  un punto crítico de coordinación con la PB abierta (sin columnas arbitrarias en la nave).
- Los pesos históricos de E0 v0.1 (**5,9 t** gran muro, 3,8 t staggered y 12,8 t metaldeck) quedan
  **supersedidos como cifras de selección**: el gran muro omitía su propio bastidor de
  acero y el deck se trató como una losa maciza incompatible con la carga muerta. E0 v0.3
  solo reporta subtotales inferiores y separa la pared híbrida.
- Vibración: no se reporta frecuencia hasta seleccionar deck, sección compuesta,
  conectores, apoyos y masa real. El objetivo se fija en E1 con el criterio aplicable.
- El lift queda en doble altura (X ≈ 5,5–6,0 m), fuera de la proyección del P2: no carga
  sobre el entrepiso, solo sobre losa PB local (regla vigente).
- **Camino gravitacional adoptado para estudiar en E1 — PARED HÍBRIDA D-043 / vigas D-045:** el gran
  muro de X = 31,50 conserva el acabado continuo de madera/absorción de D-033, delante
  de una viga superior de transferencia y columnas HSS ocultas. Las columnas se prueban
  en los límites Y = 0/2,4/7,4/11,0/13,4/18,0 m, dejando libre el portal de escalera y
  coordinando las puertas enrasadas. Se estudian seis líneas longitudinales cada 3,00 m
  (Y ≈ 1,5/4,5/7,5/10,5/13,5/16,5). E0 v0.3 las modela como IPE400 continuas de
  15,00 m, apoyadas en X=21,00 y X=31,50, con voladizo libre de 4,50 m sobre el núcleo
  hasta X=36,00. No se supone apoyo en la fachada posterior. El momento negativo y la
  continuidad sobre el muro vuelven la conexión viga–transferencia un elemento crítico;
  la transferencia superior es un elemento real, no un detalle menor.
  Los perfiles que arroja E0 son pruebas de cabida por fluencia bruta, no selección.
  El espesor 0,20 m es arquitectónico y puede crecer a una envolvente preliminar de
  0,25–0,35 m por acero, uniones, tolerancias, acústica y fuego.
- **Frontera en X = 21,00 m (viga de borde de ≈ 18 m):** se resuelve como **cercha de
  canto completo**, apoyada en dos columnas perimetrales de prueba e integrada por encima
  de +3,80 m dentro del frente del P2. No se permite descontar canto hacia la altura libre
  de PB; diagonales y montantes deben coordinarse con puertas, mini deck y cerramientos.
- **Separación de funciones laterales:** la pared X=31,50 se extiende en Y y no sustituye
  el sistema longitudinal X de las fachadas largas. Su eventual aporte en Y, el
  diafragma, los colectores y la torsión de una línea excéntrica se resuelven en E1.
- **Continuidad vertical D-048 alrededor de la escalera:** se estudian como líneas
  continuas cimentación–P2–cubierta las dos columnas del gran muro en Y=7,40/11,00 y dos
  columnas nuevas posteriores en X=36,00. Las caras laterales pueden estudiar diagonales;
  el portal protegido y la salida posterior obligan a estudiar pórticos de momento o
  soluciones segmentadas en la dirección ortogonal. Las zancas y tramos de escalera no
  reciben crédito lateral salvo modelación explícita y deben admitir la deriva relativa.
  Alcanzar la cubierta no asigna automáticamente una reacción gravitacional de cubierta.

## 6. Materiales y protección

| Elemento | Hipótesis de material | Observación |
|---|---|---|
| Columnas y vigas principales | **S355 / A572 Gr.50** (Fy ≈ 345–355 MPa) | reduce tonelaje; radar de costos #1 |
| Correas, girts, arriostramiento | **S235 / A36** (Fy ≈ 235–250 MPa) | secundarios económicos |
| Pernos | Gr. 8.8 / A325 | conexiones apernadas preferidas |
| E | 200 GPa; densidad 7850 kg/m³ | acero estructural |

**Durabilidad:** clima seco de altura interior = corrosión moderada, pero la estética de
acero visible no exime protección. Comparar galvanizado vs. pintura con criterio de
exposición y mantenimiento; no asumir "premium" ni omitir. Coordinar punto de rocío y
barrera de vapor para evitar condensación sobre el acero (sección 3 de técnicas de costo).

## 7. Criterios de peso y de desempeño para el comparativo

### 7.1 Objetivos de peso (hipótesis de control)

| Componente | Control desglose v0.2 | Rango realista (auditoría) |
|---|---:|---:|
| Pórticos principales + columnas | 15,5 t | ≈ 23–24 t |
| Entrepiso P2 | 3,0 t | ≈ 9–11 t |
| Correas, girts, arriostramientos | 9,15 t | ≈ 9 t |
| **Total estructura metálica** | **≈ 28,35 t** | **≈ 41–44 t** (central ≈ 37 t) |
| Equivalente | ≈ 31 kg/m² | ≈ 40–48 kg/m² |

El comparativo E0 debe producir un valor de kg/m² por sistema×modulación y un rango total,
para reconciliar el capítulo 05/06 antes de PE-1.

### 7.2 Criterios de servicio (hipótesis para pre-dimensionar)

- Flecha total de cubierta: ≤ L/180 (bajo combinaciones de servicio).
- Flecha de entrepiso P2: ≤ L/240 (total) y L/360 (viva) para uso residencial.
- Deriva de pórtico bajo viento/sismo de servicio: ≤ H/200 (hipótesis; la deriva real es
  del análisis del ingeniero).
- Deflexiones compatibles con vidrio fijo y paneles (diferencial entre apoyos ≤ 1/2 de la
  tolerancia del sistema).

### 7.3 Reglas de cuantificación

- Cotas calculadas de la geometría, nunca escritas dos veces.
- Perfiles de stock estándar (IPE, HEA/HEB, HSS tubulares) para plazos cortos y mejor
  precio.
- Factor de detalle (placas base, rigidizadores, cartelas, conexiones): ≈ 12–15 % del peso
  de principales.
- Desperdicio de taller: separado del peso teórico (≈ 3–5 %).
- Los resultados se reportan como hipótesis E0, con unidades SI y fuentes declaradas.

## 8. Entregables por puerta (replica de bases estructurales y civiles)

| Puerta | Entregable estructural |
|---|---|
| **E0 — esquema (actual)** | ejes, luces, alturas, apoyos hipotéticos, matriz de comparación, lista de datos faltantes (predio, geotecnia, lift, viento/sismo de norma) |
| **E1 — comparación por ingeniero** | modelo paramétrico (sistemas de cubierta × modulaciones; entrepiso P2 con pared híbrida D-043 frente a alternativas), camino lateral completo, kg/m², costo fabricado/montado, estabilidad y entrepiso compuesto |
| **E2 — diseño profesional** | memorias firmadas, planos de cimentación/losa/estructura/conexiones, revisión independiente |

## 9. Resultados históricos E0 v0.1 y auditoría v0.2 (12-08-2026)

> **Advertencia de vigencia:** la tabla que sigue conserva la corrida del 11-08-2026
> únicamente como trazabilidad. No es una matriz válida de selección ni de presupuesto.
> La auditoría v0.2 detectó omisión de pandeo/segundo orden/conexiones, aceptación
> silenciosa del perfil máximo, momento nulo erróneo bajo succión, sistema lateral de
> cercha inexistente, frecuencia ficticia del deck y tonelaje del gran muro sin bastidor.
> La salida vigente es `docs/03_ingenierias/modelo_estructural_e0.md` y debe fallar cerrado.

Matriz ejecutada con el motor `dreamhouse/structure/` (datos en
`structure_system.json`; salidas en `planos/estructura_e0/`). Hipótesis E0,
**no apto para construir**. "Acero total" usa el entrepiso METALDECK (línea
base); el total con GRAN-MURO se indica en la última columna. Auditoría de
física 11-08-2026: corregidos signos de gravedad (el pórtico ya no "flota"
bajo carga muerta), proyección trigonométrica de cargas en miembros inclinados
(componente horizontal nula) y límites de flecha L/180–L/240 en metros (antes
1000× más permisivos).

| Sistema × Modulación | Columnas | Viga / cercha | Tirante | Marcos | P2 metaldeck / staggered / gran muro | Acero total (metaldeck) | kg/m² | Total con gran muro | Lectura |
|---|---|---|---|---|---|---:|---:|---:|---|
| PÓRTICO · M45 (4,5 m) | HEA500 | IPE450 | — | 39,5 t | 12,3 / 3,9 / 11,6 t | **59,3 t** | 64,6 | 58,6 t | deriva de viento gobierna |
| PÓRTICO · M60 (6,0 m) | HEA500 | IPE500 | — | 32,6 t | 12,5 / 3,9 / 11,6 t | **52,7 t** | 57,4 | 51,7 t | referencia de la auditoría |
| PÓRTICO · M90 (9,0 m) | HEA500 | IPE550 | — | 24,8 t | 17,0 / 3,9 / 11,6 t | **49,3 t** | 53,7 | 44,0 t | **falla H/200; catálogo agotado** |
| PÓRTICO-T · M45 | HEA500 | IPE450 | 10 cm² | 41,0 t | 12,3 / 3,9 / 11,6 t | **60,7 t** | 66,2 | 60,1 t | tirante casi inactivo: no competitivo |
| PÓRTICO-T · M60 | HEA500 | IPE500 | 10 cm² | 33,8 t | 12,5 / 3,9 / 11,6 t | **53,8 t** | 58,6 | 52,9 t | tirante ≈ 2,3 kN; no controla deriva |
| PÓRTICO-T · M90 | HEA500 | IPE550 | 10 cm² | 25,6 t | 17,0 / 3,9 / 11,6 t | **50,1 t** | 54,6 | 44,8 t | **falla H/200; catálogo agotado** |
| PÓRTICO-F · M45 | **HEA300** | IPE450 | — | 28,7 t | 12,3 / 3,9 / 11,6 t | **48,5 t** | 52,9 | 47,9 t | bases fijas: deriva 0,015 m |
| PÓRTICO-F · M60 | **HEA300** | IPE450 | — | 22,3 t | 12,5 / 3,9 / 11,6 t | **42,4 t** | 46,2 | 41,5 t | marco ≈ 27 % más liviano que articulado |
| PÓRTICO-F · M90 | **HEA300** | IPE550 | — | 18,8 t | 17,0 / 3,9 / 11,6 t | **43,3 t** | 47,2 | 38,0 t | deriva 0,025 m en cribado |
| CERCHA · M45 | HEA200 | IPE220 (L/16) | — | 21,5 t | 12,3 / 3,9 / 11,6 t | **41,3 t** | 45,0 | 40,6 t | sin análisis lateral |
| CERCHA · M60 | HEA200 | IPE220 (L/16) | — | 16,7 t | 12,5 / 3,9 / 11,6 t | **36,7 t** | 40,0 | 35,8 t | sin análisis lateral |
| CERCHA · M90 | HEA200 | IPE220 (L/16) | — | 11,9 t | 17,0 / 3,9 / 11,6 t | **36,4 t** | 39,7 | 31,1 t | sin análisis lateral |

Desglose por componente (M60): marcos 32,6 t (cerchas 16,7 t) + entrepiso
P2 metaldeck ≈ 12,5 t / staggered ≈ 3,9 t / **gran muro ≈ 11,6 t** + secundaria
≈ 7,5 t. El metaldeck subió de ≈ 9,6 t a ≈ 12,8 t al corregir el límite de
flecha L/240 (antes inoperante) y la luz de viga entre apoyos (18/3 = 6 m); el
gran muro subió a ≈11,6 t al eliminar el apoyo posterior no definido, modelar seis
IPE400 continuas de 15 m con voladizo, sumar pesos propios, viga de transferencia y
dos columnas perimetrales de la cercha X=21.

### Hallazgos

1. **Deriva de viento gobierna los pórticos (H/200):** con bases articuladas y
   el viento de hipótesis (qz ≈ 0,45 kPa), las columnas suben a HEA500 y el
   peso principal a 30–40 t; el HEA300 de la auditoría no cumple la deriva de
   servicio; M90 articulado todavía falla H/200 con HEA500. En E1 el ingeniero decide: relajar el límite (H/150–180),
   rigidizar, o asumir columnas mayores.
2. **Cercha con columnas articuladas + arriostramiento ≈ 30 % más liviana**
   (36–40 t vs. 49–58 t). El ahorro de acero debe contrastarse con el costo
   extra de fabricación/montaje antes de decidir (criterio del radar de
   costos y de `bases_estructurales_y_civiles.md`).
3. **Pórtico atado (PORTICO-T):** el tirante entre los apoyos de la cercha
   queda casi inactivo (≈ 2 kN) porque la deriva de viento es un sway en la
   misma dirección de ambos muros; el tirante solo resiste la apertura de
   aleros por empuje gravitatorio, que aquí no gobierna. Añade peso
   (≈ 1,4 t/pórtico) sin beneficio de deriva: **no es competitivo en este caso
   de carga**. Su papel clásico (empuje de cubierta en edificios con grúa) no
   aplica. Requeriría análisis de segundo orden si se usara.
4. **Pórtico con bases fijas (PORTICO-F):** es el control efectivo de deriva
   para el sistema de pórticos. Permite columna HEA300 con deriva
   ≈ 0,015–0,025 m (vs. HEA500 articulado) y un marco ≈ 27 % más liviano; el
   costo pasa a la cimentación (momento en la base).
5. **Entrepiso P2 — pared híbrida D-043:** se adopta el camino gravitacional,
   no las cifras v0.1/v0.2. E0 v0.3 modela el voladizo posterior sin apoyo X=36,
   añade peso propio, viga de transferencia, seis columnas HSS ocultas y dos
   columnas perimetrales bajo la cercha X=21. Las cifras siguen siendo subtotales porque
   faltan pandeo, uniones, deck, fuego y cimentación. El muro transversal no se
   contabiliza como núcleo longitudinal X.
6. **Cubierta de un solo faldón ≈ 1:30:** la viga de cubierta queda controlada
   por resistencia (succión de viento), no por flecha: IPE450–IPE550 según
   modulación.
7. **Segunda auditoría numérica E0 v0.3:** el viento intercambia correctamente
   Cp=0,8/0,5 entre barlovento y sotavento; M90 articulado agota el catálogo por
   deriva H/200. Los pórticos y vigas P2 se evalúan línea por línea con tributarios
   reales, se verifica flecha total L/240 y viva L/360, y se incluyen pesos propios.

Estos resultados son insumo de la puerta PE-1 y de la decisión D-019; no
sustituyen el modelo E1 del ingeniero estructural.

## 10. Datos faltantes que bloquean el predimensionamiento definitivo

1. Predio, municipio, coordenadas, altitud y topografía (D-017).
2. Estudio geotécnico (cimentación y losa).
3. Parámetros normativos de viento y sismo del municipio (NSR-10 B.6 / Título A).
4. Ficha del lift automotriz: cargas por poste, anclajes y envolvente (D-022).
5. Vehículo de diseño y equipos del taller (D-022, inventario del propietario).
6. Decisión jacuzzi (D-025): carga de agua si se adopta.
7. Sistema de cubierta/fachada y peso real por m² (CYPE local / proveedor Boyacá).

## 11. Regla anti-falsa-precisión

Toda cifra aquí es hipótesis o DCV. Un valor con decimales no es más confiable que su
fuente. Nada de este documento autoriza compra de acero, cotización contractual ni
construcción. El cierre de D-019 y la reconciliación del capítulo 05/06 pasan por la
puerta PE-1 con cantidades y dos precios de mercado.

## 12. Próximos pasos

1. Abrir D-019 con este documento como base.
2. Validar el modelo E0 en `dreamhouse/structure/` (matriz 4 sistemas × 3 modulaciones:
   PORTICO, PORTICO-T, PORTICO-F, CERCHA; entrepiso P2 METALDECK vs. STAGGERED).
3. Extender la matriz E1 con costo fabricado/montado de cada sistema (kg/m² ya
   calculados en E0) y con geotecnia, viento y sismo de norma cuando exista predio.
4. Definir con el arquitecto la integración del staggered truss en las particiones
   del P2 (closets, baños, hall) y la cercha de borde en X = 21,00 m.
5. Registrar el resultado en el registro de decisiones y en la base de costos como
   insumo PE-1, sin modificar el target.

## 13. Fuentes externas de la investigación (acceso 2026-08-11)

- steelconstruction.info — Trusses (tipos Pratt/Warren/Fink, canto L/10–L/15, wind
  girders, integración de servicios). https://www.steelconstruction.info/Trusses
- steelconstruction.info — Portal frames (cartelas de alero ≈ 10 % de la luz, tied
  portal, propped portal, bases articuladas/fijas, bracing). https://www.steelconstruction.info/Portal_frames
- steelconstruction.info — Single storey industrial buildings (pórtico como opción
  económica hasta ≈ 50 m, costo mínimo a 30–35 m de luz, mezzanines apoyados en
  cubierta, hit-and-miss). https://www.steelconstruction.info/Single_storey_industrial_buildings
- steelconstruction.info — Long-span beams (vigas celulares 10–16 m, tapered girders
  10–20 m, cerchas y vigas compuestas > 20 m, stub girders). https://www.steelconstruction.info/Long-span_beams
- Wikipedia — Staggered truss system (MIT / US Steel; cerchas de piso completo,
  columnas solo en fachadas, áreas libres hasta ≈ 18 m, deriva pequeña, hoteles).
  https://en.wikipedia.org/wiki/Staggered_truss_system

Todas las técnicas citadas son referencias conceptuales para el comparativo E1; la
verificación normativa y la decisión final corresponden al ingeniero estructural según
NSR-10.
