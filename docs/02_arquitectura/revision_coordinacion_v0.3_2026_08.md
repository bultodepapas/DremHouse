# Revisión de coordinación arquitectónica — emisión v0.3 (b04 → b08)

**Estatus:** revisión independiente de coordinación; insumo técnico para la v0.4 y para las
puertas de fase. Las correcciones de defecto verificable **ya están aplicadas al modelo**
(§8). La Fase 2 del P2 se reorganizó bajo **D-042**; **no** modifica el target económico
ni la línea base.  
**Versión:** 0.3  
**Fecha de corte:** 2026-08-11  
**Fuentes revisadas:** constitución del proyecto, programa arquitectónico v0.2, bases de
diseño, borradores b04/R03 a b08/R07, `bases_estructura_metalica.md`, modelo E0
(`planos/estructura_e0/`), `base_y_control_de_costos.md` v0.3, `registro_decisiones.md` v0.4
y `fuentes_precedencia_y_conflictos.md` v0.2.  
**Método:** (1) lectura del expediente de gobierno y del programa; (2) medición directa de
los modelos paramétricos `pb_b05.json`, `p2_b06.json` y `rooflight_b08.json`; (3) medición
de los polígonos y coordenadas de las láminas SVG emitidas, con verificación de escala
sobre las cotas rotuladas de cada lámina; (4) lectura del código de validación en
`dreamhouse/generate_*.py`; (5) contraste de todo lo anterior contra el programa y las hard
rules.  
**Aprobación pendiente:** propietario, arquitecto coordinador, ingeniero estructural y
especialista en protección contra incendio.

**Advertencia de método:** esta revisión es documental y geométrica. No es diseño
profesional, memoria de cálculo ni verificación normativa, y no sustituye a ningún
consultor competente. Toda cifra citada procede de los modelos y láminas del propio
expediente; donde se estima, se declara como estimación.

---

## 1. Resumen ejecutivo

### 1.1 Veredicto general

La idea rectora del proyecto **sobrevive íntegra a la revisión**: nave única, cubierta
continua, planta baja abierta, núcleo oculto tras un solo muro, P2 anclado al fondo y eje
peatonal libre de 31,5 m. Las láminas no han diluido el concepto.

Lo que la revisión sí encuentra es un **problema de coordinación entre emisiones**. Los
borradores b04 a b08 se produjeron corrigiendo un asunto por vez, y cada corrección se
verificó contra su propio modelo. El resultado es que hoy hay láminas activas que se
contradicen entre sí, y un motor de validación automática que no puede detectarlo porque
compara cada archivo consigo mismo.

### 1.2 Cuadro de hallazgos

| ID | Hallazgo | Severidad | Estado al 2026-08-11 |
|---|---|---|---|
| H-01 | Sentido del faldón contradictorio dentro de la emisión activa | **Crítico** | **Corregido** |
| H-02 | Pendiente 3,33 % incompatible con el sistema de envolvente adoptado | **Crítico** | Aritmética corregida; **cota abierta** |
| H-03 | El primer módulo estructural no tiene dónde arriostrarse | **Crítico** | Abierto — ingeniero |
| H-04 | El cuadro de áreas del P2 es un teselado sin espesores | **Crítico** | **Corregido**; los 3 FAIL resultantes, resueltos |
| H-05 | La segunda salida del P2 es un generador de planta, no un pendiente | **Crítico** | Abierto — concepto de incendio |
| H-06 | Ventanas de la suite principal intercambiadas entre emisiones | Importante | **Corregido** |
| H-07 | Jerarquía del vidrio invertida respecto del brief y del programa | Importante | Abierto — propietario |
| H-08 | Cocina al 60 % del programa; banda doméstica sin proyectar | Importante | Abierto — propietario |
| H-09 | Suite principal bajo programa; huéspedes sobre programa | Importante | Huéspedes **corregido**; principal **abierto** |
| H-10 | Claraboyas geométricamente iguales e hidráulicamente opuestas | Importante | **Cuantificado y registrado**; detalle abierto |
| H-11 | Vestíbulo F2 de 1,00 m rotulado como 1,20 m | Importante | **Corregido** (1,25 m libres) |
| H-12 | El alcance crece sin precio mientras el target permanece fijo | Importante | Abierto — gobierno |
| H-13 | Tabiques del núcleo dibujados a 0,36 m, declarados a 0,15 m | Menor | **Corregido** |
| H-14 | Los chequeos automáticos validan el JSON contra sí mismo | Menor | **Corregido** (6 reglas nuevas) |
| H-15 | `D-037` duplicado; aleros de cubierta no decididos | Menor | **Corregido** (→ `D-041`) |

**Total: 5 críticos · 7 importantes · 3 menores.** **Nueve corregidos**, uno cuantificado y
publicado, cinco abiertos porque son decisiones del propietario o de un consultor
competente. Detalle de lo aplicado en la §8.

### 1.3 Conclusiones principales

1. **El hallazgo H-01 bloquea la envolvente completa.** Mientras el modelo no tenga un solo
   lado bajo, no se pueden dimensionar canal, reboses, bajantes, descarga a terreno, franja
   perimetral ni los desvíos de agua de las claraboyas.
2. **Siete de los quince hallazgos pertenecen a clases que el motor de validación no
   verifica** (cierre de áreas con muros, coherencia entre emisiones, sentido de cubierta y
   comparación contra el programa). El motor es una buena idea mal apuntada.
3. **El conflicto estructural–arquitectónico que el modelo E0 dejó abierto no es un
   problema a resolver: es la oportunidad de proyecto de la v0.4.** Ver sección 5.
4. **La disciplina de no tocar el target está protegiendo el número mientras el alcance se
   aleja de él.** Las últimas cuatro decisiones son aditivas y ninguna tiene precio.

---

## 2. Hallazgos críticos

### H-01 — Sentido del faldón contradictorio dentro de la emisión activa

> **Estado: CORREGIDO.** El sentido vive ahora una sola vez en `roof` de `pb_b05.json` y las cinco láminas lo derivan de ahí. Lo que sigue es el registro de lo encontrado.

**Láminas:** `ELE-001/002/003/004-R06` (b07) y `PLN-CUB-001-R07` (b08).

El borrador 07 nació de una corrección acertada del propietario: las elevaciones anteriores
aplanaban el desnivel hasta hacerlo imperceptible. La corrección de escala vertical se
aplicó bien. Pero al reemitir las cuatro caras, **la fachada posterior quedó espejada
respecto de las otras tres**, y la planta de cubierta del borrador 08 heredó ese mismo
espejo.

| Lámina | Declara en Y = 0 | Declara en Y = 18 |
|---|---|---|
| `ELE-001-R06` fachada frontal | lado bajo ≈ 7,20 m | lado alto ≈ 7,80 m |
| `ELE-003-R06` lateral A | alero bajo ≈ 7,20 m | — |
| `ELE-004-R06` lateral B | — | alero alto ≈ 7,80 m |
| `ELE-002-R06` fachada posterior | **lado alto ≈ 7,80 m** | **lado bajo ≈ 7,20 m** |
| `PLN-CUB-001-R07` planta de cubierta | **subida hacia lado alto** | — |

**Verificación.** En `ELE-001-R06` el polígono de fachada mide 446,4 px de alto en el
vértice de Y = 0 y 483,6 px en el de Y = 18; en `ELE-002-R06` esos dos valores están
invertidos. La correspondencia de bordes no es interpretación: se estableció con las
ventanas, que sí coinciden en las cinco láminas —el ventanal del car project (X 1,50–8,70)
identifica el lateral A, y la ventana de wellness (Y 13,00–17,00) identifica el borde
izquierdo de la fachada posterior como Y = 0.

**Consecuencia.** Tal como está dibujada, la cubierta no es un faldón: es una superficie
alabeada. Y el efecto no es de representación. El b07 establece que *«la totalidad del agua
se concentra en el alero bajo»*: son unos **660 m² de captación descargando sobre una sola
fachada**, y el expediente hoy no sabe cuál.

**Acción.** Congelar el lado bajo como enmienda registrada a D-039 y regenerar las cinco
láminas afectadas. El criterio de decisión no es geométrico sino de uso: el alero bajo debe
caer del lado opuesto a la plataforma social y a la vida exterior de la familia.

---

### H-02 — Pendiente 3,33 % incompatible con el sistema de envolvente adoptado

> **Estado: aritmética CORREGIDA; la cota sigue ABIERTA** — subir la eave alta es decisión del propietario.

**Fuentes:** `bases_de_diseno.md`, `structure_system.json`, `cubierta_v0.3_borrador_07.md`.

Las bases de diseño especifican *«panel metálico aislado como envolvente terminada»* y el
modelo estructural carga *panel sándwich ≈ 50 mm*. Los paneles sándwich de cubierta con
solapes suelen exigir del orden de **5–10 % de pendiente** para conservar garantía de
fabricante. Aquí hay 3,33 % sobre un faldón continuo de 18,00 m sin cumbrera intermedia, en
clima andino de lluvia intensa: recorrido muy largo con pendiente muy baja.

Esto obliga, en la práctica, a junta alzada engatillada mecánicamente en paños de 18 m con
clips deslizantes por dilatación. Es otro sistema, otro precio y otro detalle de alero y de
curb de claraboya.

**Error aritmético asociado.** `bases_estructura_metalica.md` §1 dice *«≈ 1:30 (≈ 1,9 %)»*.
1:30 es 3,33 %; 1,9 % sería ≈ 1:53. El resto del expediente usa 3,33 % correctamente; el
paréntesis es el que está mal y debe corregirse para que nadie predimensione drenaje con él.

**Acción propuesta.** La unidad formal de la cubierta es hard rule; la cota no lo es, y el
propio documento lo dice. Subir el alero alto a **≈ 8,10–8,30 m** lleva la pendiente a
5–6 %, mantiene el faldón único, no toca alturas libres interiores ni el alero bajo, y
devuelve el sistema al rango donde existe garantía. Es el ajuste de menor daño.

---

### H-03 — El primer módulo estructural no tiene dónde arriostrarse

> **Estado: ABIERTO.** Requiere al ingeniero estructural; no es corregible desde el modelo.

**Láminas:** `PLN-001-R04`, `ELE-001/003/004-R06`, `PLN-CUB-001-R07`.

Este hallazgo no aparece en ninguna lámina porque está repartido entre cinco. Las bases
estructurales fijan la estrategia de estabilidad: *«arriostramiento en paños opacos …
recomendada como primera línea»*. Al superponer todo lo decidido, **en los primeros 8,70 m
de nave no queda un solo paño opaco**.

| Elemento | Extensión | Fuente |
|---|---|---|
| Portón car project | 4,80 × 4,80 m | D-008 |
| Puerta peatonal central | 1,60 × 2,50 m | D-008 |
| Portón taller RC | 4,80 × 4,80 m | D-008 |
| Machones del testero frontal | 1,20 m en esquinas · 2,20 m intermedios | programa |
| Ventanal lateral A | 7,20 × 2,90 m · X 1,50 → 8,70 · antepecho 0,90 | D-035 |
| Ventanal lateral B | 7,20 × 2,90 m · X 1,50 → 8,70 · antepecho 0,90 | D-035 |
| Claraboyas | 23,04 m² · X 2,40 → 4,80 | D-040 |
| **Paño arriostrable restante** | **solo por encima de +3,80 m en los laterales** | — |

Y esta es exactamente la crujía donde el modelo E0 concluyó que **la deriva de viento
gobierna** y empujó las columnas a HEA500.

**Naturaleza del hallazgo.** No es un error de cálculo: es un vacío de coordinación. D-008,
D-035 y D-040 se tomaron por separado y su efecto combinado sobre la estabilidad no está
registrado en ninguna parte. Es el tipo de vacío que reaparece en obra como tonelaje mayor
o como una diagonal que nadie quería ver.

**Acción.** Resolver el primer módulo como un problema único —portones, dos ventanales,
claraboyas y arriostramiento sobre la misma lámina— con el ingeniero estructural presente,
antes de congelar cualquiera de los tres.

---

### H-04 — El cuadro de áreas del P2 es un teselado sin espesores

> **Estado: CORREGIDO.** El modelo descuenta espesores reales. Los tres FAIL que esto destapó quedaron resueltos reorganizando la Fase 2 bajo D-042 (§8.3).

**Lámina:** `PLN-002-R05` · **modelo:** `p2_b06.json`.

Los veintidós recintos del segundo piso suman **exactamente 270,000 m²**, que es el área
nominal exterior completa de 18,00 × 15,00 m. No hay holgura para un solo muro. La lámina
dibuja tabiques y la memoria declara espesores de 0,18 / 0,20 / 0,15 m, pero el modelo que
produce las cifras no los descuenta en ninguna parte.

| Concepto | Valor |
|---|---:|
| Σ recintos de `p2_b06.json` | 270,000 m² |
| Interior real con muro exterior 0,18 m | 17,64 × 14,64 = 258,25 m² |
| Neto estimado con tabiques 0,15 m | ≈ 240–245 m² |
| Superficie rotulada que no existe | **≈ 10–11 %** |

**Efecto sobre la hard rule 9.** La lámina rotula *«Dormitorios hijos: 26,0 m² exactos cada
uno»* y el chequeo `P2-CHILD-EQUAL` pasa. Pero uno es 5,20 × 5,00 y el otro 6,50 × 4,00:

| Dormitorio | Bruto | Neto estimado (0,15/lado) | Proporción |
|---|---:|---:|---|
| Hijo 1 (`H1-D`) | 26,00 m² | 23,03 m² | 1,04 : 1 — casi cuadrado |
| Hijo 2 (`H2-D`) | 26,00 m² | 22,94 m² | 1,63 : 1 — alargado |

La igualdad exacta que el propietario congeló como hard rule **aún no está demostrada**, ni
en área neta ni en equivalencia cualitativa, y la lámina afirma que sí. Esto también invalida
la resolución provisional de CF-003, que remitía la comprobación a la planta neta v0.3.

**Acción.** Incorporar espesores reales al modelo del P2 y volver a medir antes de cualquier
reasignación de superficie.

---

### H-05 — La segunda salida del P2 es un generador de planta, no un pendiente

> **Estado: ABIERTO.** Requiere concepto profesional de incendio.

**Láminas:** `DIA-001-R05`, `PLN-002-R05`. **Estado actual:** `LIFE-EGRESS-2 = OPEN`.

El expediente registra este punto como abierto, y eso es correcto. Lo que subestima es su
capacidad de mover el proyecto.

Midiendo sobre la planta emitida, el recorrido desde el rincón más lejano del dormitorio de
hijo 1 hasta la puerta de la escalera es de **≈ 20 m en fondo de saco**, encadenando cuatro
recintos (dormitorio → galería interior → hall privado → vestíbulo principal → escalera),
con ocupación de dormitorio y una sola escalera al final. En Fase 2 se añade la sauna en el
extremo opuesto: fuente de calor en el punto más profundo del recorrido.

En un P2 con cuatro dormitorios sobre un taller con vehículo, batería LiPo y extracción, lo
más probable es que el concepto de incendio exija una segunda salida. La respuesta más
económica sería una escalera exterior metálica en la fachada posterior.

**Por qué es urgente.** La escalera está rígidamente alineada con el núcleo y con el gran
muro en X = 31,50 m (D-032, D-033). Si el concepto de incendio mueve la escalera, mueve el
núcleo y mueve el gran muro. **Este dato debe entrar antes de la v0.4, no después.**
Concuerda con R-03 y R-10 de la matriz de riesgos, ambos ya calificados como críticos.

---

## 3. Hallazgos importantes

### H-06 — Ventanas de la suite principal intercambiadas entre emisiones

> **Estado: CORREGIDO**, con prueba negativa: al reponer los valores antiguos los chequeos los rechazan.

Los dos modelos activos coinciden en que la suite principal tiene un paño de 5,50 m y otro
de 2,50 m. Discrepan en cuál va dónde, y las elevaciones siguen a uno mientras la planta
sigue al otro.

| Modelo | Identificador | Fachada | Rango | Ancho |
|---|---|---|---|---:|
| `pb_b05.json` | `GLZ-M-R` | posterior (X=36) | Y 1,00 → 6,50 | 5,50 m |
| `pb_b05.json` | `GLZ-M-A` | lateral A (Y=0) | X 33,00 → 35,50 | 2,50 m |
| `p2_b06.json` | `W-M-REAR` | lateral A (*edge* `south`) | X 30,00 → 35,50 | 5,50 m |
| `p2_b06.json` | `W-M-SIDE` | posterior (*edge* `east`) | Y 0,80 → 3,30 | 2,50 m |

Nótese que el identificador `W-M-REAR` de b06 está asignado a una fachada lateral, mientras
las memorias de b05 y b06 describen ambas el paño de 5,50 m como *posterior*. Las
elevaciones `ELE-002-R06` y `ELE-003-R06` siguen a b05.

**Segundo problema dentro del primero.** El dormitorio principal ocupa Y 0,00 → 4,20 y el
vestidor ocupa Y 4,20 → 7,40. El ventanal posterior de b05 va de Y 1,00 a 6,50: son
**2,30 m de vidrio de piso a techo dando al interior del walk-in closet**. Está dibujado así
en `ELE-002-R06`, rotulado «SUITE PRINCIPAL · PISO A TECHO».

---

### H-07 — Jerarquía del vidrio invertida respecto del brief y del programa

> **Estado: ABIERTO.** Decisión de diseño del propietario.

El brief coloca la sala en doble altura y el evento principal de vidrio como tercer valor
del proyecto, y describe el momento rector de entrar y descubrir *«la sala monumental y el
principal evento de vidrio»*. El programa le asigna 7–9 m de ancho. Lo dibujado es otra cosa.

| Paño | Dibujado | Área | Dintel | Programa |
|---|---|---:|---:|---|
| Evento principal · sala | 4,30 × 3,15 m | 13,5 m² | +3,15 m | **7,00–9,00 m** |
| Ventanal taller carro | 7,20 × 2,90 m | 20,9 m² | +3,80 m | — |
| Ventanal taller RC | 7,20 × 2,90 m | 20,9 m² | +3,80 m | — |

Cada ventanal de taller es **un 55 % más grande** que el gran evento de la sala, y su dintel
está 0,65 m más alto. En un recinto de 7,20 m de altura, un vano que muere a 3,15 m deja
cuatro metros de panel ciego encima: la doble altura se percibirá como una caja alta y
sorda, no como el espacio luminoso que el brief promete.

Esto no es un incumplimiento de cota. Es el proyecto contradiciendo su propia tesis y su
propia jerarquía de valor.

---

### H-08 — Cocina al 60 % del programa; banda doméstica sin proyectar

> **Estado: ABIERTO.** Decisión de diseño del propietario.

El programa pide un muro equipado de **7,00–7,50 m** para una familia que declara uso
frecuente de cocina. `PLN-001-R04` dibuja **4,50 m**. Descontando refrigeración,
lavavajillas, hornos y placa quedan del orden de 1,60 m de mesón libre.

El problema mayor está alrededor. La banda doméstica bajo el P2 son 189 m² brutos, y el
único mobiliario definido son el frente de 4,50 m, una isla de 3,60 × 1,20 y una mesa de
3,60 × 1,30. **La planta baja sigue siendo un diagrama de bandas, no una planta.**

El chequeo `PB-KITCHEN-CLEAR` pasa porque compara el paso de 1,20 m contra el valor
`operating_clearance` que el propio JSON declara; nunca mira el programa. Ver H-14.

---

### H-09 — Suite principal bajo programa; huéspedes sobre programa

> **Estado: la suite de huéspedes alcanza el programa por primera vez** (§8.3). La suite principal sigue **ABIERTA**: su déficit no es corregible dentro de la planta.

La hard rule 10 exige que la principal sea claramente dominante, con gran vestidor y el baño
de mayor jerarquía. Lo es en total, pero sus dos piezas nobles quedaron cortas mientras la
suite de huéspedes creció.

| Recinto | Dibujado | Programa | Δ |
|---|---:|---:|---:|
| Suite principal · total | 65,2 m² | ≈ 76 m² | −10,8 |
| Vestidor principal | 10,24 m² | 15–16 m² | −5,3 |
| Baño principal | 13,44 m² | 17–18 m² | −4,1 |
| Dormitorio principal | 31,08 m² | 30–32 m² | dentro de rango |
| Dormitorio huéspedes | 22,00 m² | 17–18 m² | +4,5 |

Hay 4,5 m² de más en huéspedes y 9,4 m² de menos entre vestidor y baño principal. La
corrección es un ajuste interno de tabiques, sin tocar la envolvente. Pero mientras el
modelo no descuente muros (H-04), cualquier reasignación se hará sobre cifras que no son
las reales.

**Asunto asociado.** Los baños de hijo 2 y huéspedes tienen 2,00 m de profundidad bruta,
≈ 1,70 m libres. El b06 lo reconoce como compacto y pide detalle 1:25; conviene resolverlo
en el mismo movimiento.

---

### H-10 — Claraboyas geométricamente iguales e hidráulicamente opuestas

> **Estado: CUANTIFICADO Y REGISTRADO** como `RL-DRAINAGE-ASYMMETRY`; el detalle de cada curb sigue pendiente.

El b08 justifica dos paños iguales en parte porque *«permiten repetir sistema»*.
Geométricamente es cierto. Pero el faldón es transversal y las claraboyas están en extremos
opuestos de la pendiente.

| Paño | Recorrido aguas arriba | Cuenca aproximada |
|---|---:|---:|
| Claraboya junto al alero alto | 1,20 m | ≈ 3 m² |
| Claraboya junto al alero bajo | 12,00 m | ≈ 29 m² |

Una necesita desvío tipo *cricket*, rebose secundario y curb reforzado; la otra
prácticamente no. **Y hoy no se sabe cuál es cuál, porque depende de H-01.** Repetir el
mismo detalle en ambas es la vía directa a una filtración sobre el car project.

---

### H-11 — Vestíbulo F2 de 1,00 m rotulado como 1,20 m

> **Estado: CORREGIDO.** 1,25 m libres, por encima del mínimo propio de 1,20 m, sin quitárselo a los baños (§8.3).

El recinto `F2-HALL` tiene profundidad `d = 1,0` en `p2_b06.json`, se rotula «Vestíbulo F2
aislable 1,20 m» en la lámina, y el propio documento fija *«circulación libre objetivo
≥ 1,20 m»*. Con tabiques descontados quedan del orden de 0,70–0,85 m libres.

Es el único acceso a dos suites y a la zona de bienestar, y es además el plano donde va el
cierre temporal estanco entre fases (D-038).

---

### H-12 — El alcance crece sin precio mientras el target permanece fijo

> **Estado: ABIERTO.** Gobierno de costos; decisión del propietario.

La auditoría propia estima la obra física real en **$1.050–1.150 M** frente a un target de
$988,05 M, y el costo total del promotor en $1.800–2.500 M. La regla de no tocar el target
hasta PE-1 es correcta y disciplinada. El problema es lo que ha ocurrido *debajo* de esa
regla: las últimas cuatro decisiones son todas aditivas y ninguna tiene precio incorporado.

| Decisión | Alcance añadido | Precio incorporado |
|---|---|---|
| D-033 · gran muro | ≈ 58 m² de listón + respaldo acústico registrable | no |
| D-035 · ventanales técnicos | 2 × 7,20 × 2,90 m ≈ 41,8 m² | no |
| D-036 · ventanas de dormitorio | 4 paños de 2,70 m + guardas laminadas | no |
| D-040 · claraboyas | 23,04 m² de vidrio cenital + curbs aislados | no |

Las claraboyas solas —unidad aislante laminada sobre curb aislado y drenado, con acceso de
mantenimiento en altura— son plausiblemente del orden del 3–4 % del target completo. La
bitácora de `base_y_control_de_costos.md` lo dice con todas las letras (*«es incremento de
alcance sin precio incorporado»*) y aun así el borrador siguiente continuó añadiendo.

**El expediente está protegiendo el número y dejando que el alcance se aleje de él.**

**Acción.** Abrir un registro de alcance añadido con orden de magnitud —aunque sea grueso y
declarado como hipótesis— para que PE-1 no reciba el acumulado de golpe. Concuerda con R-02.

---

## 4. Hallazgos menores y de consistencia

### H-13 — Tabiques del núcleo dibujados a 0,36 m, declarados a 0,15 m

> **Estado: CORREGIDO.** Tabiques verificados a 0,150 y 0,200 m sobre la lámina generada.

Midiendo las separaciones entre los cinco recintos del núcleo en `PLN-001-R04`, todas son de
**0,36 m**: el generador aplica un retranqueo de 0,18 m por lado en vez del tabique de
0,15 m que fija D-034. La lámina es internamente consistente —los cinco recintos más las
cuatro separaciones dan los 17,64 m interiores— pero no representa el espesor decidido, y
las áreas rotuladas como «brutas» son netas de otra cosa.

### H-14 — Los chequeos automáticos validan el JSON contra sí mismo

> **Estado: CORREGIDO.** Seis reglas nuevas, de las cuatro clases que faltaban (§8.3).

Los «12 PASS / 0 FAIL» de la planta baja y los «8 PASS» del P2 transmiten una conformidad
que la revisión manual no confirma. La razón es estructural: los tests leen el modelo y lo
comparan con constantes del mismo modelo.

| Regla | Qué verifica realmente |
|---|---|
| `PB-KITCHEN-CLEAR` | compara el paso contra `operating_clearance` del propio JSON |
| `PB-CORE-SUM` | suma el campo `gross_area` declarado, no la geometría dibujada |
| `PB-TECH-GLAZING` | comprueba que existen dos ventanales, no su efecto sobre estabilidad |
| `P2-CHILD-EQUAL` | compara `w × d` bruto, sin muros |
| `P2-ENV` | comprueba que los recintos caben, no que quede sitio para tabiques |

Reglas ausentes que habrían atrapado siete de los quince hallazgos:

1. **Cierre de áreas:** Σ recintos + espesores ≤ envolvente (atrapa H-04, H-11).
2. **Coherencia entre emisiones:** los vanos de `pb_b05.json` y `p2_b06.json` deben coincidir
   en fachada, rango y ancho (atrapa H-06).
3. **Coherencia de cubierta:** todas las láminas deben declarar el mismo lado bajo (atrapa
   H-01, y hace determinista H-10).
4. **Contraste contra el programa:** comparar frente de cocina, evento de vidrio, vestidor y
   baño principal contra `programa_arquitectonico.md` (atrapa H-07, H-08, H-09).

Hoy el motor verifica que el archivo dice lo que dice. Debería verificar que el **edificio**
cumple el programa.

### H-15 — `D-037` duplicado; aleros de cubierta no decididos

> **Estado: CORREGIDO.** La base estructural pasó a `D-041`; próximo identificador libre `D-042`.

`registro_decisiones.md` v0.4 asigna **`D-037` dos veces**: a la adopción del P2 b06/R05
(estado *Activa*) y a las bases de estructura metálica (estado *Propuesta*). En un
expediente cuya precedencia se apoya en «decisión expresa posterior, registrada y fechada»,
un identificador duplicado es un defecto de la columna vertebral, no una errata de formato.

Aparte: `PLN-CUB-001-R07` dibuja el faldón exactamente a 18,00 × 36,00 m, **sin alero en
ninguna de las cuatro caras**. Para una nave metálica en clima de lluvia andina, con
portones de 4,80 m de alto en el testero, el vuelo cero es una decisión de peso —defendible
por el carácter monolítico buscado— pero hoy está implícita. Debe registrarse como decisión.

---

## 5. Lectura de proyecto — el problema que debería generar la v0.4

Si hubiera que elegir un solo asunto para ordenar el siguiente borrador, no sería ninguno de
los quince. Sería este, y ya está escrito en el propio modelo E0:

> El borde del P2 en X = 21,00 m necesita una viga de 18 m de luz. Sin apoyos intermedios el
> entrepiso pasa de 12,0 a 16,2 t y compromete las alturas libres. Con apoyos intermedios,
> **esos apoyos caen en la zona doméstica**. El E0 lo registra como *«conflicto
> estructural–arquitectónico abierto»*.

El expediente lo trata como un problema a resolver. Esta revisión propone leerlo al revés:
**es la oportunidad de que la planta baja deje de ser un diagrama de bandas.**

Hoy existen dos vacíos que se corresponden exactamente:

- la estructura pide dos apoyos en la franja X 21,00 → 31,50 m;
- esa misma franja son 189 m² con ocho metros lineales de mobiliario definido y una cocina
  al 60 % del programa (H-08).

La estructura está pidiendo precisamente lo que a la arquitectura le falta: **materia en la
banda doméstica.**

Los dos apoyos no tienen que ser columnas sueltas en medio de la nave —lo que la hard rule 3
prohíbe con razón. Pueden ser dos elementos con espesor y programa:

1. el **testero del muro equipado de la cocina**, llevado a los 7,00–7,50 m que pide el
   programa, resolviendo H-08 y absorbiendo un apoyo;
2. una **pieza de despensa o alacena** alineada con el gran muro, absorbiendo el segundo.

Son elementos que la casa necesita de todos modos; aportan rigidez donde el primer módulo no
puede darla (H-03); mejoran la acústica del comedor frente al riesgo R-08; y convierten el
apoyo estructural en la frontera suave entre sala monumental y cocina que la secuencia
rectora reclama.

Ese es el movimiento que hace que la v0.4 sea un proyecto y no una corrección de erratas.

### 5.1 Nota de estado — vía alternativa en curso

A la fecha de corte hay trabajo estructural en curso sobre una tercera vía:
`dreamhouse/structure/staggered.py` explora **cerchas escalonadas** (*staggered truss*) para
el entrepiso del P2, un sistema que resuelve luces del orden de 18 m **sin apoyos interiores
de ningún tipo**.

Si esa vía se confirma, invalida la premisa de esta sección: no habría dos apoyos que
convertir en arquitectura, porque no habría apoyos. Las dos rutas son legítimas y llevan a
plantas distintas:

| Vía | Efecto en la banda doméstica | Riesgo principal |
|---|---|---|
| Apoyos intermedios convertidos en programa (§5) | obliga a proyectar cocina y despensa; aporta rigidez al conjunto | condiciona la libertad de la planta abierta |
| Cerchas escalonadas sin apoyos interiores | libera la planta por completo | canto, fabricación, costo y coordinación MEP a verificar |

**Esta sección debe releerse cuando el modelo E0 entregue tonelaje y canto de la vía
escalonada.** El hallazgo H-08 (cocina bajo programa, banda doméstica sin proyectar) es
independiente de cuál de las dos gane: hay que proyectar esa franja de todos modos.

---

## 6. Orden de trabajo propuesto

| # | Acción | Desbloquea |
|---|---|---|
| 1 | **Congelar el lado bajo de la cubierta** como enmienda registrada a D-039 y regenerar las cinco láminas afectadas. Criterio: el alero bajo debe caer del lado opuesto a la plataforma social. | H-01, H-10, drenaje, bajantes, franja perimetral |
| 2 | **Subir el alero alto a ≈ 8,10–8,30 m** para llevar la pendiente a 5–6 %. Corregir el «1,9 %» de las bases estructurales. | H-02, selección de sistema de cubierta |
| 3 | **Incorporar espesores reales al modelo del P2** y volver a medir todas las áreas. | H-04, H-09, H-11, CF-003, hard rule 9 |
| 4 | **Consultar el concepto profesional de incendio antes de dibujar la v0.4.** | H-05, D-021, D-028, R-03, R-10 |
| 5 | **Resolver el primer módulo como un problema único** con el ingeniero estructural: portones, ventanales, claraboyas y arriostramiento en una sola lámina. | H-03, D-019 |
| 6 | **Crecer el evento principal de vidrio a programa** (7–9 m de ancho, altura acorde a un recinto de 7,20 m) y ajustar el protagonismo relativo de los ventanales de taller. | H-07, jerarquía de valor del brief |
| 7 | **Proyectar la banda doméstica** aplicando la estrategia de la sección 5. | H-08, conflicto E0 abierto |
| 8 | **Reapuntar el motor de verificación** con las cuatro reglas de H-14. | H-14, y prevención sistemática |
| 9 | **Abrir el registro de alcance añadido** con orden de magnitud para D-033, D-035, D-036 y D-040, sin tocar el target. | H-12, PE-1, R-02 |
| 10 | **Corregir el `D-037` duplicado** y registrar la decisión de aleros. | H-15, integridad del registro |

---

## 7. Qué no debe tocarse

Conviene declararlo con la misma claridad, porque en una revisión larga es fácil que se
pierda.

- **La idea rectora aguanta.** Nave única, cubierta continua, planta baja abierta, núcleo
  oculto tras un solo muro, P2 anclado al fondo. Es un concepto fuerte y las láminas no lo
  han diluido.
- **El eje peatonal está bien construido.** Entra por el centro exacto de la fachada,
  atraviesa 31,5 m sin un muro y muere en el portal de la escalera, la única puerta que el
  gran muro se permite mostrar. Es la mejor decisión de la planta.
- **El gran muro es la operación acertada.** Resolver cinco servicios, la acústica del fondo
  y el remate de la perspectiva con una sola superficie de madera es exactamente la clase de
  gesto que este proyecto necesita: mucho efecto, poca complejidad.
- **La frontera única de fases en Y = 11,00 m** es una decisión constructiva madura, poco
  común en un proyecto de vivienda.
- **La auditoría de costos que contradice el target del propio expediente** vale más que el
  target.
- **El aparato de gobierno** —precedencia explícita, registro de conflictos abiertos, sellos
  de estado, generación paramétrica con `sha256` en manifiesto— es superior al de muchas
  oficinas. Es justamente lo que permite corregir todo lo anterior de forma trazable.

Nada de esta revisión cuestiona el proyecto. Cuestiona el estado de coordinación entre
láminas que se han ido corrigiendo de a una. El expediente ya tiene el aparato para
arreglarlo; lo que le falta es apuntar la verificación al edificio en vez de al archivo.

---

## 8. Correcciones aplicadas al modelo

Se corrigió únicamente lo que es **defecto verificable**: documentos que se contradicen
entre sí, o que contradicen una decisión ya registrada. **No se tomó ninguna decisión de
diseño**: donde la corrección exigía elegir entre alternativas legítimas, el hallazgo se
dejó abierto con los números sobre la mesa.

### 8.1 Defectos corregidos

| ID | Qué se hizo | Verificación |
|---|---|---|
| H-01 | El sentido del faldón vivía hardcodeado en cada lámina. Ahora vive **una sola vez** en `roof` de `pb_b05.json` y las cinco láminas lo derivan de ahí. Corregidos el espejo de la fachada posterior, la flecha de la planta de cubierta y un **error de signo en el corte de claraboyas** que dibujaba el alero alto a 6,60 m. | Medición de los cinco polígonos generados: Y=0 → 7,20 m y Y=18 → 7,80 m en todas. Invertir el faldón es hoy cambiar `roof.low_side` y regenerar. |
| H-02 | Corregido «≈ 1:30 (≈ 1,9 %)» → **1:30 = 3,33 %** y añadida alerta de compatibilidad con el panel sándwich. | La cota sigue **abierta**: subir la eave alta es decisión del propietario (§8.2). |
| H-04 | El modelo teselaba 270,00 m² exactos sin sitio para muros. Añadidos `net_dims()` / `net_area()`, que descuentan envolvente en el perímetro y medio tabique en los bordes interiores. Los rótulos de la lámina se calculan; ya no se escriben a mano. | Σ neta **239,2 m²** ≤ 258,2 m² de interior útil. Regla `P2-AREA-CLOSURE` en PASS. |
| H-06 | Decide la geometría: el dormitorio principal tiene 7,40 m de muro en el lateral A y 4,20 m en el posterior, así que el paño de 5,50 m sólo cabe en el lateral. Alineado `pb_b05.json` con `p2_b06.json` y renombrado `W-M-REAR`→`W-M-LAT-A`. | **Prueba negativa ejecutada**: al reponer los valores antiguos, `PB-P2-WINDOW-SYNC` y `PB-GLAZING-IN-ROOM` los rechazan señalando el desborde de 2,30 m sobre el vestidor. |
| H-10 | El desequilibrio hidráulico entre las dos claraboyas se calcula y se publica en cada emisión. | `RL-DRAINAGE-ASYMMETRY`: 12,00 m (≈28,8 m²) frente a 1,20 m (≈2,9 m²). |
| H-13 | Los recintos del núcleo descontaban 0,18 m a ambos lados. Añadido `core_net_y()`, que distingue borde de envolvente (0,18) de tabique interior (0,15, o 0,20 contra la escalera). | Medición de la lámina: tabiques de **0,150 y 0,200 m** exactos; cierre 16,94 + 0,70 + 0,36 = 18,00 m. |
| H-14 | Seis reglas nuevas, de las cuatro clases que faltaban. | Ver §8.5. |
| H-15 | `D-037` duplicado: se conserva para el P2 b06/R05 y la base estructural pasa a **`D-041`**. Añadida sección de correcciones de registro. | Próximo identificador libre: `D-042`. |

### 8.2 Lo que la primera pasada dejó abierto a propósito

Cuatro correcciones eran técnicamente triviales y aun así **no se aplicaron**, porque
hacerlo habría sido decidir en nombre del propietario:

| Hallazgo | Por qué no se corrigió |
|---|---|
| H-02 · pendiente | Subir la eave alta a 8,10–8,30 m altera un DCV. La forma es hard rule, la cota no, pero el cambio necesita registro del propietario. |
| H-04 · igualdad de dormitorios | Igualar el área neta requiere ~9 cm de ajuste. Pero H1 es 1,04:1 y H2 es 1,62:1: **el ajuste haría pasar el chequeo sin igualar la habitación**, que es exactamente el vicio denunciado en H-14. |
| H-11 · vestíbulo F2 | Llevarlo a 1,20 m dentro de la envolvente actual obliga a restar 0,20 m a los dormitorios de F2 o a unos baños que ya son el punto más comprometido. Es una permuta, no un arreglo. |
| H-09 · suite principal | Reasignar 9,4 m² entre vestidor, baño y huéspedes es proyecto, no corrección. Ahora está medido y publicado como `P2-MASTER-PROGRAM`. |

Tras esa primera pasada `generate_p2_b06.py` terminaba con código 1 y tres FAIL. Era el
comportamiento correcto: tres condiciones reales incumplidas —una de ellas una hard rule—
que antes quedaban ocultas tras cifras brutas. **Los tres quedaron resueltos después**, al
autorizar el propietario la tolerancia de D-042; el cierre se documenta en la §8.3. La
suite principal (H-09) es la única de las cuatro que sigue abierta, y la §8.4 explica por
qué no es corregible dentro de la planta.

### 8.3 Cierre de los tres FAIL — reorganización de la Fase 2 (D-042)

Con la tolerancia de ±1,00 m² que el propietario autorizó en **D-042**, los tres FAIL que
la §8.2 había dejado abiertos se resolvieron **reorganizando la planta**, no relajando los
umbrales. Uno de los tres, además, no era un defecto del proyecto sino un error de esta
revisión.

**Corrección de esta revisión.** `P2-WELLNESS` comparaba el área **neta** del wellness
(15,6 m²) contra los 16 m² de la reserva de programa. Pero el programa arquitectónico
declara en su cabecera que sus áreas son **brutas** («sin descontar estructura,
cerramientos y acabados»). Medido como corresponde, el wellness siempre estuvo dentro de
la reserva. El FAIL era mío, no del diseño. Todas las reglas declaran ahora su base de
medida y el modelo la documenta en `p2_b06.json`.

**El movimiento de proyecto: girar la suite de hijo 2.** El dormitorio pasa de
6,50 × 4,00 a 4,60 × 5,60 m brutos y su baño se coloca al costado, replicando el esquema
de hijo 1 en vez de una franja transversal al fondo. Ese giro libera la franja posterior y
paga por sí solo las tres mejoras:

| Condición | Antes | Ahora | Límite |
|---|---|---|---|
| Igualdad de dormitorios (útil) | 23,46 vs 24,04 · Δ 0,58 | 23,46 vs 23,22 · **Δ 0,24** | ±1,00 (D-042) |
| Proporción de hijo 2 | **1,62:1** — habitación alargada | **1,23:1** | ≤ 1,35:1 |
| Vestíbulo de Fase 2 | 0,85 m libres | **1,25 m** | ≥ 1,20 m |
| Baño de hijo 2 | 1,70 m de fondo | **2,80 m**, idéntico al de hijo 1 | — |
| Dormitorio de huéspedes | 22,0 m² brutos (+4,5 sobre programa) | **17,0 m²** | 17–18 |
| Baño de huéspedes | 4,0 m² brutos (−1,5) | **5,7 m²** | 5,5 |

Lo relevante es que **la elasticidad de ±1,00 m² no se gastó en hacer pasar el chequeo**:
se gastó en enderezar la habitación de hijo 2 y en devolverle a la suite de huéspedes el
programa que tenía mal repartido. La diferencia final entre los dormitorios de los hijos es
de 0,24 m² —un cuarto de metro cuadrado sobre 23— con proporciones 1,04:1 y 1,23:1: ambas
son habitaciones, ninguna es un pasillo.

**Efecto secundario verificado.** Los aparatos sanitarios y las camas estaban dibujados con
coordenadas escritas a mano; al mover un baño habrían quedado fuera de su recinto. Ahora se
derivan de la geometría de cada cuarto, y se comprobó que los catorce elementos caen dentro
de su rectángulo neto.

### 8.4 Lo que sigue abierto, y por qué no es corregible

| Regla | Aritmética |
|---|---|
| `P2-MASTER-PROGRAM` | La banda del principal mide 7,40 × 11,00 = **81,4 m²** y la escalera ocupa **16,2**, dejando **65,2 m²** para un programa que pide **76**. Crecer el principal obliga a estrechar los dormitorios de los hijos por debajo de los 20,2 m² útiles de referencia. O baja el programa del principal, o crece el P2, o la escalera sale de esa huella: es decisión del propietario. |
| `LIFE-EGRESS-2` | Requiere concepto profesional de incendio. Ningún modelo puede cerrarlo. |

Conviene nombrar el fondo del asunto: **el programa del P2 suma 270 m² brutos dentro de una
envolvente de 270 m² brutos**, es decir, no reserva superficie para sus propios muros. Con
espesores reales el neto disponible es ≈239 m². El déficit del principal no es un error de
dibujo: es esa aritmética. Cerrarlo exige una decisión de programa, no una corrección.

### 8.5 Reglas de verificación añadidas

| Regla | Clase | Qué impide |
|---|---|---|
| `P2-AREA-CLOSURE` | cierre de áreas | Que los recintos ocupen la envolvente sin dejar sitio a los muros |
| `PB-CORE-CLOSURE` | cierre de áreas | Que los tabiques dibujados no coincidan con los declarados |
| `PB-P2-WINDOW-SYNC` | coherencia entre emisiones | Que un vano se describa distinto en b05 y en b06 |
| `PB-GLAZING-IN-ROOM` | contención geométrica | Que un vano desborde el muro del recinto que ilumina |
| `RL-ROOF-DIRECTION` | coherencia de cubierta | Que una lámina declare un sentido de faldón distinto al de la fuente única |
| `P2-CIRC-MIN`, `P2-MASTER-PROGRAM`, `P2-CHILD-PROPORTION` | contraste contra el programa | Que el dibujo se aleje del programa sin que nadie lo mida |

Severidad: **FAIL** para defecto del modelo o hard rule incumplida; **OPEN** para decisión
pendiente del propietario o de un consultor. La distinción importa: un OPEN no bloquea, un
FAIL sí.

### 8.6 Estado de los chequeos tras la corrección

| Emisión | PASS | FAIL | OPEN |
|---|---:|---:|---:|
| PB b05 | 15 | **0** | 0 |
| P2 b06 | 12 | **0** | 2 |
| Cubierta b07 | 4 | **0** | 2 |
| Claraboyas b08 | 6 | **0** | 3 |

**Sin fallos en ninguna emisión.** Los siete OPEN restantes no son defectos: son cuatro
asuntos que dependen del predio o de la orientación (sentido definitivo del faldón,
pendiente final, coordinación de claraboyas con pórticos, higrotermia del vidrio), el
déficit de programa de la suite principal, la asimetría hidráulica de las dos claraboyas y
la segunda salida del P2. Cada uno publica su aritmética en el `compliance.json`
correspondiente.

---

## 9. Registro de versiones

| Versión | Fecha | Cambio |
|---|---|---|
| 0.1 | 2026-08-11 | Emisión inicial. Revisión de coordinación sobre b04→b08 y modelo E0. 15 hallazgos (5 críticos, 7 importantes, 3 menores). No modifica target, decisiones ni línea base. |
| 0.3 | 2026-08-11 | **Cerrados los tres FAIL del P2** reorganizando la Fase 2 al amparo de **D-042** (tolerancia de ±1,00 m² útiles en los dormitorios de hijos, autorizada por el propietario): la suite de hijo 2 gira, su baño pasa de 1,70 a 2,80 m de fondo, la suite de huéspedes alcanza el programa y el vestíbulo F2 sube a 1,25 m libres. Corregido además un error **de esta revisión**: `P2-WELLNESS` medía en neto contra un objetivo bruto del programa. Todas las reglas declaran ahora su base de medida. Mobiliario sanitario derivado de la geometría. **Estado: 0 FAIL en las cuatro emisiones.** |
| 0.2 | 2026-08-11 | Aplicadas las correcciones de defecto verificable (§8): H-01, H-04, H-06, H-13, H-14 y H-15 corregidos en el modelo; H-02 corregido en su aritmética; H-10 cuantificado. Seis reglas de verificación nuevas. No se adoptó ninguna decisión de diseño: H-02 (cota), H-03, H-05, H-07, H-08, H-09, H-11 y H-12 siguen abiertos. Actualizadas las memorias b05, b06, b07 y b08 para que la prosa no contradiga las láminas corregidas. |
