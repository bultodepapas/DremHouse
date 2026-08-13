# Técnicas constructivas y materiales para abaratar costos

**Estatus:** borrador de investigación; no constituye decisión, requisito congelado ni
presupuesto  
**Versión:** 0.1  
**Fecha de corte:** 2026-08-11  
**Fuentes:** investigación web (lista al final) + expediente interno: constitución,
presupuesto de control v0.2, bases estructurales y civiles, bases MEP, estrategia de dos
fases y plan maestro.  
**Aprobación pendiente:** propietario, arquitecto coordinador, ingeniero estructural e
ingeniero MEP.  
**Advertencia:** ningún valor de ahorro aquí es cotización. Todas las cifras porcentuales
provienen de fuentes genéricas de mercado (mayoritariamente EE. UU. y fabricantes
asiáticos de acero) y deben contrastarse con cantidades, ingeniería y cotizaciones
colombianas antes de influir en el presupuesto.

## Resultado ejecutivo

El target v0.2 de $941 M de obra física se concentra en pocos capítulos. Cuatro de ellos
suman más de la mitad del presupuesto:

| Capítulo                                | Control v0.2 | Participación |
| --------------------------------------- | -----------: | ------------: |
| 05+06 Estructura principal + secundaria |       $200 M |          21 % |
| 08+09 Cubierta + fachadas aisladas      |       $165 M |          18 % |
| 04 Losa PB industrial                   |        $83 M |           9 % |
| 12+13 Vidrio + ventanas/puerta          |        $58 M |           6 % |
| Resto                                   |       $435 M |          46 % |

Por tanto, el ahorro más grande no está en recortar acabados sino en **estructura,
envolvente y cimentación**, y se decide casi por completo en el diseño (las fuentes de
fabricación estiman que hasta el 70 % del costo de una estructura metálica queda
determinado en la fase de diseño).

Las oportunidades con mejor relación ahorro/esfuerzo, coherentes con la estética de nave
industrial y con el clima frío de Boyacá:

1. **Modulación y estandarización de la nave** (bays 6 m, perfiles estándar, pocos tipos
   de conexión): menos tonelaje, menos horas de taller y montaje.
2. **Comparar pórticos vs. cerchas sin prejuicio**, y optimizar la altura de cumbrera y
   los apoyos del P2: el peso por m² cae notablemente.
3. **Ingeniero estructural desde el inicio**: las fuentes reportan ahorros de 10–20 % del
   costo total evitando sobrediseño y cambios tardíos.
4. **Sistema de aislamiento por capas en vez de solo panel sándwich**: teja metálica +
   lana de vidrio con facing de vapor + liner interior es sustancialmente más barato que
   paneles aislados importados, mantiene la estética industrial y controla condensación si
   se instala bien. (El presupuesto v0.2 asume "panel metálico aislado".)
5. **Geotecnia y losa de espesor realista**: la cimentación y la losa se sobredimensionan
   cuando no hay datos; un estudio temprano suele pagarse varias veces.
6. **No climatizar la nave como una sola zona**: calefacción local/radiante donde vive la
   gente + ventiladores HVLS/destratificación, en vez de acondicionar los 7 m de altura.
7. **Control de humedad y punto de rocío** como requisito, no como accesorio: evita el
   "lluvia interior" de las naves metálicas, que destruye aislamiento, oxida el acero y
   obliga a rehacer (retrofit cuesta 30–60 % más que hacerlo bien la primera vez).
8. **Portones y vidrio en tamaños estándar de mercado** y con 2–3 cotizaciones; son
   capítulos pequeños pero de alto desperdicio si se vuelven "especiales".
9. **Construcción en dos fases ya decidida (D-016)**: mantiene el ahorro de caja, pero no
   debe usarse para reducir especificación de envolvente ni estructura.

## Principios que gobiernan esta investigación

- El lujo del proyecto es proporción, altura, luz, estructura, detalle y desempeño. Las
  técnicas deben **reducir costo sin tocar esos valores** y sin disfrazar la nave como
  chalet.
- Las hard rules (nave única, estructura visible, tres accesos, P2 posterior, cuatro
  suites, etc.) **no se modifican** con esta investigación.
- Ninguna técnica puede degradar seguridad, desempeño térmico/acústico esencial, ni
  durabilidad. El propio brief lo prohíbe.
- Los renders, imágenes de IA y folletos comerciales nunca son autoridad dimensional ni
  técnica. Esta investigación es orientación de mercado, no diseño.

---

## 1. Estructura metálica (capítulos 05, 06, 07, 22 — $208 M)

### 1.1 Optimizar el bay y la modulación

Las fuentes de fabricación indican que **bays de 6,0–7,5 m son los más costo-eficientes**
para naves industriales, y que coordinar vanos con módulos estándar (1,2 m / 1,5 m) reduce
desperdicio y simplifica panel metálico, correas y arriostramiento. La nave de 18 × 36 m
se modula naturalmente en 6 bays de 6 m; conviene que el predimensionamiento estructural
pruebe esa opción contra alternativas de 4,5 m (más pórticos) y 9 m (pórticos más
pesados), comparando peso total y costo de fabricación/montaje.

Recomendación de investigación: **comparar 3 modulaciones con el mismo sistema** (E1 del
plan de herramientas) y registrar kg/m², costo fabricado/montado y número de piezas.

### 1.2 Pórticos vs. cerchas: decidir con datos, no con imagen

Hay consenso en la industria en dos direcciones opuestas según el caso:

- Los **pórticos portal** suelen ser más económicos en naves bajas y de luz media porque
  simplifican fabricación y conexiones.
- Las **cerchas** reducen peso de acero en luces largas y cubiertas livianas, pero suman
  detalle de fabricación y puntos de conexión, que pueden costar más que el acero
  ahorrado.

La decisión debe salir del predimensionamiento del ingeniero (alternativas que ya pide
`bases_estructurales_y_civiles.md`), no de una preferencia estética. El criterio incluye
tonelaje, costo fabricado/montado, transporte, izaje, altura útil, protección y
mantenimiento.

### 1.3 Acero de mayor resistencia en elementos críticos

Las guías de fabricación recomiendan **usar grado superior (p. ej. S355/Q355B) en
elementos principales** porque reduce secciones y tonelaje total, y **grado inferior
(S235/Q235B) en secundarios** (correas, arriostramientos). La decisión es del ingeniero
con cantidades, pero es un lugar clásico donde "comprar acero más caro por tonelada" sale
más barato por m² construido.

### 1.4 Estandarizar perfiles, conexiones y detalles

- Reducir el número de perfiles únicos; los proveedores tienen en stock secciones
  estándar (viga H, canal C/Z para correas) con plazos cortos y mejores precios. Los
  perfiles especiales pueden costar 15–25 % más y tardar semanas adicionales.
- Preferir **conexiones apernadas** sobre soldadas donde sea posible; reducir gussets y
  placas decorativas sin función estructural.
- Agrupar componentes similares en lotes de fabricación; repetir detalles evita errores
  de taller.
- Diseñar piezas para **longitudes de transporte estándar** (en importación, 5,8 m y
  11,8 m) y para ser apiladas "flat-pack", reduciendo flete y daños.

### 1.5 Prefabricación y montaje eficiente

- La prefabricación en taller corre en paralelo con cimentación en obra; las fuentes
  citan construcciones 30–50 % más rápidas, con menos mano de obra en sitio.
- Los planos de taller claros y la secuencia de izaje coordinada (grúa, logística) evitan
  retrabajos; el costo de un error en obra es mucho mayor que en dibujo.
- **Ingeniería temprana:** traer al estructural y al fabricante desde el esquema reduce
  10–20 % del costo total (fuentes de fabricantes), sobre todo evitando choques MEP vs.
  estructura y fundaciones mal dimensionadas.

### 1.6 Transporte y compras

- Cotizar acero en volumen y con ventanas de compra (el precio del acero fluctúa por
  ciclos); evaluar compra anticipada cuando el precio esté bajo, siempre con memoria de
  cantidades y riesgo de cambio de diseño.
- En Colombia, cotejar con la lista de insumos de Construdata (APU por ciudad, ICOCED de
  DANE) en vez de precios genéricos internacionales.

### 1.7 Protección contra corrosión con criterio

En clima seco de altura interior la demanda de corrosión puede ser moderada, pero la
estética de acero visible no exime protección. Comparar galvanizado vs. pintura según
exposición, costo y mantenimiento; no asumir "premium". El estudio de durabilidad es del
ingeniero.

---

## 2. Cimentación y losa PB (capítulos 02, 03, 04 — $125 M)

### 2.1 Geotecnia temprana: el ahorro con mayor retorno

Las fuentes de fabricación insisten en que **el estudio de suelo permite dimensionar la
cimentación real**, evitando excavación y concreto de más. El presupuesto v0.2 reserva
$35 M en cimentación + $7 M en excavaciones sobre una base de 648 m². Un estudio
geotécnico cuesta una fracción de esa cifra y evita tanto el sobrediseño como el riesgo de
falla. Es prerequisito de las puertas PE-1/PE-2 del plan de costos.

### 2.2 Losa de espesor y refuerzo realistas

La losa industrial endurecida/pulida ya está contemplada ($83 M, capítulo 04). Los
ahorros válidos están en:

- dimensionar espesor y refuerzo/fibras con el uso real (carro + lift + taller, no cargas
  de bodega logística);
- resolver el lift con cimentación/engrosamiento local y no sobredimensionar los 648 m²;
- juntas de aserrado y curado correctos para no pagar reparaciones.

El concreto pulido es además el acabado final: evita otro piso encima. Es coherente con la
estética industrial y con el brief.

### 2.3 Cargas puntuales documentadas (lift, sauna, racks)

Antes de la losa debe existir la familia de lift y la envolvente de cargas aprobada
(regla de la estrategia de dos fases). No colocar pernos embebidos genéricos sin patrón
congelado. Esto no ahorra dinero, pero evita demoler después, que es la pérdida más
costosa.

---

## 3. Envolvente: cubierta, fachadas, aislamiento y condensación (capítulos 08, 09, 10 — $185 M)

Este es el frente con mayor potencial de ahorro **sin cambiar la apariencia**, y el de
mayor riesgo si se hace mal por el clima frío y húmedo de Boyacá.

### 3.1 La condensación es el enemigo número uno de las naves metálicas

El acero conduce calor muy rápido y las naves sufren "lluvia interior" cuando el aire
interior cálido y húmedo toca el acero frío (por debajo del punto de rocío). Esto oxida
estructura, moja aislamiento (pierde R, se cuelga) y genera moho. Las reglas de control,
según la ciencia del edificio:

- **Aislar lo suficiente para que el acero quede por encima del punto de rocío.**
- Colocar la **barrera de vapor en el lado cálido** (interior, en clima frío). En clima
  frío dominante: barrera clase I o II en el interior.
- **No poner barrera de vapor en ambos lados** del mismo ensamble (atrapa humedad).
- Sellar todas las costuras con cinta de sellado de vapor (no cinta de ductos).
- Controlar la humedad interior (ventilar baños, cocina, sauna y procesos del taller;
  objetivo referencial <60 % RH).
- Evitar puentes térmicos en correas/girts: el acero de la estructura puede reducir el
  R efectivo 30–50 % si no se interrumpe.

### 3.2 Comparar el sistema de panel sándwich con el sistema por capas

El presupuesto v0.2 asume **fachada y cubierta de panel metálico aislado**. En el mercado
internacional, los paneles aislados (IMP, PUR/PIR) son de los sistemas más caros por m²
(p. ej. rangos de $12–35 USD/ft² instalado en guías de EE. UU.), mientras que el sistema
**teja metálica + lana de vidrio con facing de vapor + liner interior** es el más
económico y es el estándar de fábricas y bodegas. Los rangos referenciales de instalación:

| Sistema                               | Costo instalado ref. (USD/ft²) | Notas                                                                  |
| ------------------------------------- | -----------------------------: | ---------------------------------------------------------------------- |
| Lana de vidrio con facing (blanket)   |                     $0,45–1,15 | La opción más barata; R-3,2–3,8 por pulgada                            |
| Barrera reflectiva/radiant            |                     $0,15–0,50 | Suplementaria, no sustituye aislamiento en clima frío                  |
| Tablero rígido (rigid foam, continuo) |                     $0,80–2,00 | R-5,0–6,5 por pulgada; elimina puentes térmicos                        |
| Espuma cerrada (spray foam)           |                     $1,50–3,50 | Sella aire y vapor, pero la más cara y puede anular garantías de panel |
| Panel aislado IMP (PUR/PIR)           |                         $12–35 | El más caro; R alto en perfil delgado                                  |

Esto sugiere una **línea de investigación de cantidades** para el capítulo 09: comparar
"panel aislado" contra "teja/lámina + lana con facing + liner interior", manteniendo la
lectura industrial. Un liner interior metálico blanco (26 ga) da acabado limpio, refleja
luz y aguanta impacto en el taller; la lana con facing cuesta menos y se instala entre
correas y girts. Esta comparación debe hacerse con precios locales (Construdata /
proveedores de Boyacá), no con los rangos USD genéricos.

### 3.2.1 Precios colombianos verificados (CYPE Colombia, acceso 11-08-2026)

La [auditoría de costos 2026-08](../04_costos/auditoria_de_costos_2026_08.md) re-consultó en
vivo las referencias CYPE que cierran la comparación con precios locales:

| Sistema de fachada (0,6 mm + aislamiento)                                | Ref. CYPE |                             Costo/m² | Delta vs. panel |
| ------------------------------------------------------------------------ | --------: | -----------------------------------: | --------------: |
| Fachada simple de lámina perfilada de acero (sin aislamiento)            |    FLA010 |                              $29.438 |           −81 % |
| Fachada de doble hoja: bandeja + lana de vidrio 100 mm (R=2,25) + lámina |    FLA020 |                              $91.466 |       **−40 %** |
| Panel sándwich aislante 50 mm, lana de roca, fijación oculta             |    FLA030 |                             $152.266 |            base |
| Cubierta sándwich 50 mm, lana de roca                                    |    QTM010 |                             $101.010 |               — |
| Cubierta de lámina perfilada simple (sin aislamiento)                    |    QTA010 | ≈$29.000–31.000 (estimado de FLA010) |               — |

**Aplicado a la envolvente real de la nave (fachada neta ≈680 m², cubierta ≈660 m²):**

| Escenario                                                                                           | Fachada (680 m²) | Cubierta (660 m²) | Total envolvente |
| --------------------------------------------------------------------------------------------------- | ---------------: | ----------------: | ---------------: |
| Control v0.2 (panel sándwich en ambas)                                                              |            $95 M |             $70 M |       **$165 M** |
| Fachada por capas (doble hoja FLA020) + barrera de vapor/separadores térmicos/remates (+$8–12 k/m²) |     **$70–75 M** |             $70 M |   **$140–145 M** |
| Envolvente por capas en fachada **y** cubierta (lámina + lana facing + liner)                       |     **$70–75 M** |      **$59–63 M** |  **≈$130–140 M** |

**Conclusión de cantidades:** el ahorro real de la envolvente por capas está **en la fachada
(−$20–25 M)**, no tanto en la cubierta (−$7–10 M, porque el sándwich QTM010 ya cotiza bajo).
El total potencial **$165 M → ≈$130–140 M (−$25–35 M)** confirma el radar v0.2 (oportunidad
#2, −$15 a −$30 M) y lo sube al borde superior con la doble hoja.

**Requisitos no negociables si se adopta (clima frío de Boyacá):**

- Barrera de vapor/facing en el **lado cálido (interior)**: el FLA020 no la incluye; hay que
  sumarla (cinta de sellado de vapor en todas las costuras).
- Separadores térmicos en girts/correas: el acero de la estructura reduce el R efectivo
  30–50 % si no se interrumpe (BSD-163).
- Lana con facing clase I o II solo en un lado del ensamble; nunca en ambos.
- La fachada de doble hoja con lámina exterior **refuerza la lectura industrial de nave**,
  coherente con la constitución; el liner/bandeja interior da acabado plano y limpio.

### 3.2.2 Economía del vidrio y los lucernarios (respuesta a "más vidrio")

El vidrio es el material **más caro por m²** de toda la envolvente: muro cortina CYPE FMC010
verificado en **$1.290.364/m²** — es decir **8–14 veces** el costo del panel sándwich
($152 k/m²) o de la doble hoja ($91 k/m²). Por tanto:

- **Aumentar fachada de vidrio encarece la envolvente**, no la abarata: 1 m² más de muro
  cortina equivale a ~8–14 m² de envolvente opaca por capas. La constitución descartó además
  "fachadas indiscriminadamente acristaladas" (hard rule) y D-013 fija "pocos eventos de vidrio
  de alto impacto".
- **La vía barata de "más luz" son lucernarios/tragaluces de policarbonato celular** en
  cubierta o paneles translúcidos de policarbonato en la zona monumental: rango orientativo
  $250–400 k/m² instalado — mucho menor que muro cortina, y se financia con una fracción del
  ahorro de la envolvente por capas. Ejemplo: 20 m² de lucernarios = $5–8 M, cubiertos por el
  ahorro de la fachada por capas.
- El gran evento de vidrio (28 m²) sigue siendo hard rule: optimizar dimensión y especificación
  (ventana fija industrial, no muro cortina) para mantenerse cerca de $1,18 M/m², y destinar
  cualquier ahorro neto de envolvente a luz estratégica si el propietario lo desea.

### 3.3 Aislamiento continuo vs. cavidad en clima frío

Según Building Science (BSD-163), en clima frío el **aislamiento continuo exterior
calienta las superficies sensibles** (cara trasera de la lámina) y elimina la condensación
por fuga de aire y por difusión, incluso con menos R interior. Para estructura liviana de
acero (el caso de la nave) la recomendación técnica es colocar una parte importante del
aislamiento como **capa continua sobre la estructura**, no solo entre correas. Un panel
sándwich con núcleo aislante actúa exactamente así; el sistema por capas requiere más
cuidado de detalle (girts con separadores térmicos, sellos). El ingeniero MEP/building
science debe calcular el R necesario según clima real del predio y humedad interior.

### 3.4 Cubierta: color, pendiente y ventilación

- En clima frío altoandino la **ganancia solar diurna es un recurso útil** (calor solar
  gratuito) pero las noches son frías; la decisión de color de cubierta debe salir del
  modelo térmico, no de una regla de clima cálido.
- Pendiente suficiente para drenar lluvia y nieve de altura; no empozamientos.
- Ventilación controlada de cumbrera (ridge vents, turbinas sin electricidad, louvers)
  ayuda a igualar temperatura y a evacuar humedad; en espacios climatizados debe
  compatibilizarse con el sellado de aire.

### 3.5 Retrofits: instalar bien la primera vez

Las guías estiman que **aislar después cuesta 30–60 % más** que hacerlo durante la
construcción. La Fase 1 debe dejar la envolvente completa y estanca (ya es política del
proyecto); esto no es un gasto diferible.

---

## 4. Vidrio, ventanas y portones (capítulos 11, 12, 13 — $82 M)

- **El gran evento de vidrio es una hard rule** y vale su presupuesto; los ahorros deben
  buscarse en el resto de carpinterías.
- **Tamaños estándar de mercado** en ventanas y puerta peatonal, perfiles de aluminio
  disponibles en Colombia (con rotura de puente térmico si el clima lo exige), en vez de
  piezas "especiales".
- **2–3 cotizaciones comparables** para el vidrio principal y los dos portones (ya lo pide
  el plan de costos). Comparar termopanel vs. laminado con low-e según el modelo térmico y
  la radiación UV intensa de altura; no pagar triple vidrio si el clima no lo justifica.
- Portones industriales: modelos de catálogo en las medidas del programa (4,80 × 4,80 m)
  en vez de personalizados; la maniobra y los sistemas comerciales deben probarse.

---

## 5. Climatización, ventilación y destratificación (capítulo 19 — $25 M)

El proyecto no climatizará la nave como un único dormitorio (bases MEP). Las técnicas
internacionales para naves de gran altura coinciden con esa filosofía:

- **Ventiladores HVLS (gran volumen, baja velocidad)** o destratificación para devolver el
  aire caliente acumulado en altura a la zona ocupada; mucho más barato que calentar los
  7 m de altura. Ya contemplado en bases MEP como "HVLS silenciosos".
- **Calefacción local/radiante donde se vive** (P2 y zona doméstica), no acondicionar toda
  la nave.
- Ventilación natural asistida (cumbreras, turbinas, louvers) + extracción localizada en
  fuentes de contaminación (escape del vehículo, impresión 3D, soldadura/vapores).
- Modelo térmico por zonas antes de comprar equipos (lo exige bases MEP): evita
  sobredimensionar, que es la forma más común de pagar de más.

---

## 6. Acabados, carpintería y obra doméstica (capítulos 20, 21, 23 — $80 M)

- **Concreto pulido como piso único** (ya presupuestado): sin alfombras, sin sobrepisos,
  coherente con taller y nave.
- Carpintería y closets **modulares de fabricación nacional** (política ya indicada en la
  estrategia de dos fases): ampliables, no "a medida costoso" en todo.
- Pintura y acabados puntuales; la madera en operaciones concentradas (pared posterior,
  cocina, P2), no convierte la nave en chalet.
- Baños/sauna: enchapados comerciales de buena relación, impermeabilización y aparatos
  estándar; la complejidad (ducha doble de la principal) se mantiene solo donde el
  programa la pide.

---

## 7. Método de entrega, compras y ejecución

1. **Contratación por paquetes con el mismo alcance** (puerta PE-3): no elegir solo el
   total más bajo; normalizar exclusiones, transporte, impuestos y garantías.
2. **Compras en volumen y ventanas de mercado** (acero, panel, vidrio, aislamiento).
3. **Bases de precios colombianas**: Construdata (APU y precios de insumos por ciudad),
   ICOCED de DANE y la lista regional vigente de Boyacá, en lugar de precios genéricos de
   EE. UU. o Asia.
4. **Ingeniería de valor en diseño, no en obra**: un cambio en plano cuesta fracciones de
   un cambio en sitio.
5. **Construcción en dos fases** (D-016): ahorra caja de F1 ($77,7 M dentro del modelo
   v0.2) y el total no se reduce; la Fase 2 debe presupuestar remobilización y
   escalamiento.

---

## 8. Tabla resumen: técnicas priorizadas

| #   | Técnica                                                      | Capítulo v0.2 | Impacto estimado         | Riesgo                    | Esencia preservada | Estado     |
| --- | ------------------------------------------------------------ | ------------- | ------------------------ | ------------------------- | ------------------ | ---------- |
| 1   | Modulación bays 6 m + perfiles estándar                      | 05, 06        | Alto (tonelaje)          | Bajo                      | Sí                 | Investigar |
| 2   | Pórticos vs. cerchas por cálculo                             | 05            | Alto                     | Medio                     | Sí                 | Investigar |
| 3   | Acero grado superior en principales, inferior en secundarios | 05, 06        | Medio                    | Bajo                      | Sí                 | Ingeniero  |
| 4   | Ingeniero estructural desde el esquema                       | 05–07         | 10–20 % reportado        | Bajo                      | Sí                 | Acción     |
| 5   | Geotecnia temprana                                           | 02, 03        | Alto (evita sobrediseño) | Bajo                      | Sí                 | Acción     |
| 6   | Envolvente por capas vs. panel aislado                       | 08, 09        | Alto                     | Medio-alto (condensación) | Sí                 | Cotizar    |
| 7   | Barrera de vapor lado cálido + sellos                        | 08, 09, 10    | Medio (vida útil)        | Alto si se omite          | Sí                 | Requisito  |
| 8   | Lana con facing + liner interior (taller)                    | 09            | Medio                    | Medio                     | Sí                 | Cotizar    |
| 9   | Vidrio/portones estándar, 2–3 cotizaciones                   | 11, 12, 13    | Medio                    | Bajo                      | Sí                 | Cotizar    |
| 10  | HVLS + calefacción local, no climatizar la nave              | 19            | Medio                    | Bajo                      | Sí                 | Mantener   |
| 11  | Concreto pulido único piso                                   | 04            | Bajo (ya en plan)        | Bajo                      | Sí                 | Mantener   |
| 12  | Bases de precios colombianas                                 | Todos         | Control                  | Bajo                      | Sí                 | Acción     |

**Lectura del riesgo en el clima de Boyacá:** la técnica #6 ahorra dinero pero cambia el
detalle de la envolvente; solo se adopta con cálculo de punto de rocío, sellado de aire y
control de humedad, y con precios locales. Si las cotizaciones muestran que el panel
aislado cuesta poco más por m², puede no valer la pena el riesgo. Es una decisión de
cantidades, no de opinión.

---

## 9. Límites: lo que esta investigación no autoriza

- No reducir seguridad estructural, resistencia al fuego, egreso ni protección contra
  riesgos del taller para ahorrar.
- No diferir estructura, envolvente, cubierta ni estanqueidad en Fase 1.
- No elegir aislamiento solo por precio sin barrera de vapor correcta: en clima frío eso
  se paga con moho y corrosión.
- No usar precios internacionales genéricos como si fueran cotizaciones colombianas.
- No congelar ninguna técnica aquí hasta validarla con cantidades, ingeniería y 2–3
  cotizaciones (puertas PE-1/PE-2 del plan de costos).

---

## 10. Qué investigar a continuación

1. Predimensionamiento estructural con 3 modulaciones y 2 sistemas (pórtico vs. cercha)
   con kg/m² y costo fabricado/montado (D-019).
2. Geotecnia conceptual del predio candidato para cimentación/losa.
3. Cotización local: panel aislado vs. teja + lana con facing + liner interior
   (capítulos 08–10), con precios de Construdata/Boyacá.
4. Modelo térmico por zonas y cálculo de punto de rocío para elegir R de envolvente y
   ubicación de barrera de vapor (D-020).
5. Cotizaciones comparables de vidrio principal y portones en medidas estándar.
6. Registro de cualquier adopción como decisión (plantilla de decisión) y actualización
   de costos en `base_y_control_de_costos.md`.

---

## 11. Fuentes web verificadas (acceso 2026-08-11)

### Estructura metálica y ahorro de costos

- Havit Steel Structure, "How to Reduce Steel Building Cost: 21 Proven Ways to Save",
  https://havitsteelstructure.com/steel-building-costs/ — bays 6–7,5 m, alturas, grados de
  acero, conexiones apernadas, estandarización, prefabricación, transporte flat-pack.
- Havit Steel Structure, "Steel Structure Cost Control: Design vs Material Efficiency",
  https://havitsteelstructure.com/steel-structure-cost-control/ — hasta el 70 % del costo
  se decide en diseño; pórticos vs. cerchas; perfiles estándar; lotes de fabricación.
- Meichen Steel Structure, "How to Reduce the Construction Budget for Steel Warehouses",
  https://www.meichensteel.com/a/procurement-guides/reduce-the-construction-budget-for-steel-warehouses.html
  — modulación, grados de acero, fundaciones optimizadas, prefabricación, minimizar
  cambios.
- Meichen Steel Structure, "Why Early Structural Engineering Support Can Save 10–20%
  Project Cost", https://www.meichensteel.com/a/industry-insights/early-structural-engineering-cost-savings.html
  — ingeniería temprana, perfiles estándar vs. especiales (15–25 % y semanas), compras
  tempranas.
- Meichen Steel Structure, "S235, S275, and S355 Steel: Which One Should You Choose?",
  https://www.meichensteel.com/a/news/how-to-choose-s235-s275-s355-steel.html
- Your Building Team, "10 Tips to Slash Your Steel Building Costs",
  https://yourbuildingteam.com/saving-on-steel-costs/ — compras por volumen, temporadas,
  incentivos, preparación de sitio.
- IBeehive Steel Structures, "Steel Structure Warehouse Building for Fast Construction
  and Lower Cost", https://www.ibeehivesteelstructures.com/blog/steel-structure-warehouse-2/
  — prefabricación 30–50 % más rápida.

### Envolvente, aislamiento y condensación

- Building Science Corporation, "BSD-163: Controlling Cold-Weather Condensation Using
  Insulation" (J. Straube),
  https://buildingscience.com/documents/digests/bsd-controlling-cold-weather-condensation-using-insulation
  — aislamiento continuo exterior calienta superficies sensibles; ratio de aislamiento
  exterior/interior; puentes térmicos de acero; barra de vapor en lado cálido.
- Ameribuilds, "Ultimate Guide to Steel Building Insulation and Vapor Barriers",
  https://ameribuilds.com/steel-building-insulation-vapor-barriers-guide/ — comparativa de
  costos instalados por tipo de aislamiento; clases de barrera de vapor; puentes térmicos
  30–50 %; retrofit 30–60 % más caro.
- CMI Specialty Insulation, "The Best Vapor Barrier Setup to Prevent Condensation in
  Metal Buildings", https://cmi-insulation.com/best-vapor-barrier-setup-in-metal-buildings/
  — sistema integral aislamiento + barrera + ventilación; clases de vapor retarder.
- ROI Metal Buildings, "Condensation in Metal Buildings: Problems and How to Stop It",
  https://roimetalbuildings.com/condensation-in-metal-buildings/ — oscilaciones térmicas,
  punto de rocío, ventilación.
- ZT Steel Structure, "Metal Building Insulation and Condensation Control",
  https://ztsteelstructure.com/metal-building-insulation-and-condensation-control/ —
  tabla de R requerido vs. temperatura exterior; barrera de vapor lado cálido; puentes
  térmicos; fallas típicas.
- Ameribuilds, "Liner Systems for Steel Building Walls",
  https://ameribuilds.com/liner-systems-steel-building-walls/ — liner de tela/polietileno
  vs. panel metálico interior vs. IMP con rangos de costo instalado; liner parcial de
  6–8 ft en zona de impacto.
- Havit Steel Structure, "How to Keep a Steel Warehouse Cool: 7 Practical Solutions",
  https://havitsteelstructure.com/keep-a-steel-warehouse-cool/ — aislamiento de cubierta,
  color reflectivo, ventilación de cumbrera, altura, iluminación natural.

### Mercado colombiano y precios

- Construdata / Legis, portal de precios unitarios e insumos por ciudad (Bogotá, Cali,
  Medellín, Barranquilla) y módulo Presupuestar, https://www.construdata.com/
- DANE, Índice de Costos de la Construcción de Edificaciones (ICOCED),
  https://www.dane.gov.co/index.php/estadisticas-por-tema/precios-y-costos/indice-de-costos-de-la-construccion-de-edificaciones-icoced
- Boyacá, resolución regional de costos vigente (referida en el expediente),
  https://www.boyaca.gov.co/resolucion-0033-de-24-de-abril-de-2026/

### Nota de confiabilidad

Los rangos de costo en USD/ft² y los porcentajes provienen de artículos comerciales y de
fabricantes, no de mediciones colombianas. Se incluyen solo como **órdenes de magnitud
relativos** (qué sistema tiende a ser más caro que otro), nunca como precios de obra. Toda
cifra que llegue al presupuesto debe originarse en Construdata, cotizaciones locales y
APU con cantidades.
