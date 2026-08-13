# Auditoría de costos — verificación de precios, cantidades y estructura de control

**Estatus:** borrador de auditoría independiente; insumo técnico para las puertas PE-1/PE-2/PE-3;
**no** modifica el target v0.2 ni autoriza cambios de alcance.  
**Versión:** 0.1  
**Fecha de corte:** 2026-08-11  
**Fuente auditada:** `BORN/Dream House — Presupuesto Técnico y Control de Costos v0.2.docx` y
[Presupuesto desglosado de control](presupuesto_desglosado_de_control.md).  
**Método:** (1) verificación de precios unitarios contra fuentes vivas consultadas el 11-08-2026
(CYPE Colombia, DANE ICOCED, proveedor de elevador, guías de mercado 2026); (2) chequeo de
cantidades contra la geometría del programa (648 m² PB, 270 m² P2, envolvente ≈810 m² brutos,
6 bays de 6 m, dos portones 4,80 × 4,80 m, evento de vidrio ≈7 × 4 m); (3) cálculo paramétrico
independiente del tonelaje estructural y volúmenes; (4) conciliación con las referencias CYPE
ya citadas en v0.1/v0.2.

**Advertencia de método:** toda cifra CYPE es una configuración de referencia de APU, no una
cotización. Las guías de mercado por m² son órdenes de magnitud. Ningún valor de esta auditoría
es un precio contractual; sirve para decidir qué cotizar primero y dónde está el riesgo real.

---

## 1. Resumen ejecutivo

### 1.1 Veredicto por frente

| Frente                    | Capítulos      | Veredicto                                                                                                      |
| ------------------------- | -------------- | -------------------------------------------------------------------------------------------------------------- |
| Precio del acero $/kg     | 05, 06         | **Alineado** ($7.054/kg del desglose dentro del rango CYPE verificado $6.587–7.376/kg)                         |
| **Tonelaje de acero**     | 05, 06         | **Subestimado** (el riesgo no es el $/kg, es el peso: 28,35 t asumidas vs. 30–45 t realistas)                  |
| Concreto $/m³ y volúmenes | 02, 03, 04, 07 | **Precio alineado** (CYPE $520.985/m³ 21 MPa; zapata $727.665/m³); **volumen de cimentación ligero**           |
| Losa PB sistema           | 04             | **Apretado** (≈$128.000/m² vs. CYPE sistema industrial $177.239/m²; explicado por losa = estructura + acabado) |
| Panel fachada $/m²        | 09             | **Subestimado** ($140.000 vs. CYPE verificado $152.266; más perfiles térmicos y remates)                       |
| Cubierta sándwich $/m²    | 08             | **Alineado** ($101.010 CYPE = $101.000 del desglose)                                                           |
| Metaldeck                 | 07             | **Alineado** ($150.400 CYPE = $152.000 del desglose)                                                           |
| Vidrio principal          | 12             | **Apretado a subestimado** ($1.180.000 vs. CYPE muro cortina $1.290.000–1.485.000)                             |
| Drywall                   | 14             | **Alineado** ($95.000 con lana vs. CYPE básico $83.630)                                                        |
| Elevador automotriz       | 25             | **Alineado** (equipo verificado $10,9 M vs. $10,0 M del desglose)                                              |
| Partidas ausentes         | 01, 16, 17     | **Faltan o están bajas:** SG-SST/ensayos, detección de incendios, sauna, seguros                               |
| Contingencia              | —              | **Baja para la etapa** (5 % sobre confianza baja-media; práctica 10–15 % hasta PE-2)                           |

### 1.2 Conclusiones principales

1. **El target de $988,05 M es una meta de ingeniería, no un precio de mercado validado.** La
   auditoría no lo rompe por sí sola, pero confirma con evidencia los tres frentes optimistas
   que el propio v0.2 declaraba: tonelaje de acero (05/06), fachada aislada (09) y vidrio (12).
2. **Una estimación independiente, con precios verificados hoy, sitúa la obra física probable
   en ≈$1.050–1.150 M** (central ≈$1.090 M), es decir **+$110–210 M sobre el target** antes de
   aplicar las oportunidades del radar. Los ahorros del radar (−$48 a −$101 M) pueden compensar
   parte, pero exigen cotización y cálculo; no se contabilizan hasta documentarse.
3. **El equivalente de $1.076.000/m² está por debajo de la franja VIS de mercado
   ($1,6–2,5 M/m²).** Eso es defendible solo porque ≈648 m² de PB son nave industrial abierta y
   sin acabados; el P2 residencial (270 m²) y los baños/cocina no pueden leerse con esa tarifa
   única. La descomposición por capítulo es la única lectura honesta.
4. **El conflicto CF-001 se explica por alcance:** v0.1 estimaba _todo_ el proyecto (obra +
   equipamiento + blandos + exteriores) con precios altos; v0.2 es _solo obra física_ con precios
   optimistas. La inversión total del promotor, con esta auditoría, se estima en **≈$1.800–2.500 M**.
5. **Fase 1 concentra todos los frentes de riesgo** (acero, fachada, vidrio, cimentación están en
   F1). El ahorro de caja F2 ($77,7 M) no protege a F1. Validar estructura → envolvente → vidrio
   primero (ya es el orden del protocolo v0.2) es la acción de mayor retorno.

### 1.3 Escenarios de obra física (control, sin costos blandos)

| Escenario              |    Obra física |      Contingencia |      Control total | Condición                                                 |
| ---------------------- | -------------: | ----------------: | -----------------: | --------------------------------------------------------- |
| A — optimista (target) |         $941 M |       5 % ($47 M) |             $988 M | Se cumplen precios verificados bajos y el 100 % del radar |
| B — más probable       | $1.050–1.150 M |    8 % ($84–92 M) | **$1.135–1.240 M** | Precios reales en los 3 frentes + faltantes incorporados  |
| C — adverso            | $1.200–1.320 M | 10 % ($120–132 M) |     $1.320–1.450 M | Acero 45 t, geotecnia pobre, envolvente/vidrio crecen     |

---

## 2. Verificación de precios — evidencia consultada el 2026-08-11

Todas las referencias CYPE fueron consultadas directamente en el Generador de Precios Colombia
en esta fecha.

| Ítem                                   |       Precio del desglose |                                                                                                                                  Referencia verificada |                   Brecha | Veredicto                                                                            |
| -------------------------------------- | ------------------------: | -----------------------------------------------------------------------------------------------------------------------------------------------------: | -----------------------: | ------------------------------------------------------------------------------------ |
| Acero A36 estructural instalado        |     $7.054/kg (combinado) |                                                                       **$6.587,26/kg** — CYPE EAP020 (perfil laminado A36, imprimación, soldado, ≤3 m) |         dentro del rango | OK; el riesgo es el peso                                                             |
| Acero A572 Gr. 50 instalado            |     $7.054/kg (combinado) |                                                                                        **$7.375,64/kg** — CYPE EAP020 (piezas compuestas, atornillado) |         dentro del rango | OK                                                                                   |
| Concreto 21 MPa (21 MPa)               |  $420.000/m³ (losa 04.02) |                                                                                  **$520.984,68/m³** — CYPE CHH030 (losas de cimentación, obra, manual) |                    −19 % | Apretado; ver §3.4                                                                   |
| Zapata de concreto armado              |       $730.000/m³ (03.01) |                                                                                                                   **$727.665/m³** — CYPE CSZ010 (v0.1) |                     ≈0 % | OK                                                                                   |
| Piso industrial tratado/pulido         | ≈$128.000/m² sistema (04) |                                                                     **$177.239,20/m²** — CYPE RSI007 (solera 20 cm + endurecedor + fratasado + pulido) |                    −28 % | Sistema del desglose más delgado (15 cm, pulido parcial); explicable, apretado       |
| Panel sándwich fachada 50 mm           |       $140.000/m² (09.01) |                                                                                **$152.266,44/m²** — CYPE FLA030 (50 mm, lana de roca, fijación oculta) |                 **−8 %** | **Subestimado**; sin perfiles térmicos ni puntos singulares                          |
| Panel sándwich cubierta 50 mm          |       $101.000/m² (08.01) |                                                                                **$101.009,74/m²** — CYPE QTM010 (50 mm, lana de roca, pendiente >10 %) |                     ≈0 % | OK                                                                                   |
| Losa metaldeck e=10 cm                 |          $152.000/m² (07) |                                                                                  **$150.399,51/m²** — CYPE EHX011 (lámina 0,75 mm, 21 MPa, conectores) |                     ≈0 % | OK                                                                                   |
| Muro divisorio drywall                 |        $95.000/m² (14.01) |                                                                                              **$83.629,82/m²** — CYPE FBY010 (básico, sin aislamiento) |                    +14 % | OK; el +14 % es lana y refuerzo acústico                                             |
| Muro cortina de aluminio               |     $1.180.000/m² (12.01) |                                                                                                **$1.290.363,67/m²** — CYPE FMC010 (sistema de tapetas) |         **−8 % a −20 %** | **Apretado**; solo sostiene si el evento es ventana fija industrial, no muro cortina |
| Elevador automotriz 2 columnas ≈4 t    |       $10.000.000 (25.01) |                                                                                         **$10.900.000** — Protalleres PT-240SC (sin instalación/envío) |                     +9 % | OK; el desglose suma obra civil + instalación aparte                                 |
| Variación ICOCED (contexto de fecha)   |                         — |                                                             **+0,20 % mensual jun-2026**; casas +0,12 %; bodegas +0,19 % (DANE, publicado 31-jul-2026) |                        — | Inflación de costos estable; no corrige precios base                                 |
| Costo por m² 2026 (referencia externa) |    $1.076.000/m² (target) | VIS **$1,6–2,5 M/m²**; estrato medio **$2,2–3,2 M/m²**; residencial **$3,2–5,0 M/m²** (CalculaConstrucción); VIS $1,8–2,5 M, media $2,8–4,2 M (Exacon) | target por debajo de VIS | Explicable por PB de nave industrial; ver §3.6                                       |

---

## 3. Auditoría de cantidades

### 3.1 Tonelaje de acero — el hallazgo más crítico

El desglose asume **28.350 kg** totales (19.200 principal + 9.150 secundaria), equivalente a
≈31 kg/m² de proyecto. Cálculo paramétrico independiente sobre la geometría del programa:

**Pórticos principales (nave 18 × 36 m, 6 bays de 6 m, cumbrera ≈7,8 m):**

- 7 líneas de pórticos (6 bays + 2 testeros).
- Columnas: 2 × 6 m × ~88 kg/m (HEA 300) ≈ 1.060 kg/pórtico → ≈7,4 t.
- Vigas de cubierta 18 m con cartelas: ~18 m × ~90 kg/m (IPE 500) ≈ 1.630 kg/pórtico + cartelas
  ≈ 1.900 kg/pórtico → ≈13,3 t.
- Placas base, rigidizadores, cartelas y detalles: ≈15 % → ≈3,1 t.
- **Subtotal pórticos y columnas: ≈23–24 t** (el desglose tiene 15,5 t en 05.01+05.02).

**Entrepiso P2 (270 m², luces de 6 m entre pórticos, carga residencial + particiones):**

- Viguetas cada 1,5 m: ≈180 ml × ~26 kg/m (IPE 220) ≈ 4,7 t.
- Vigas de borde y apoyos en la línea abierta (X=21) + columnas auxiliares: ≈4–6 t.
- **Subtotal entrepiso: ≈9–11 t** (el desglose tiene 3,0 t en 05.03).

**Secundaria (correas, girts, arriostramientos):** ≈9 t — el desglose está razonable (9.150 kg).

**Rango resultante de acero total: ≈41–44 t** con perfiles estándar. El propio v0.2 declara
"30–45 t" como rango real. Con punto medio ≈37 t a $7.054/kg combinado: **05+06 ≈ $260 M**
(rango $212–317 M), vs. los $200 M del target. **Delta probable: +$55–100 M.**

> Nota: el v0.1 estimaba estructura en $650 M (≈88 t a $7.376/kg). Ese extremo es un
> sobredimensionamiento; el extremo v0.2 (28,35 t) es optimista. La verdad estructural está en
> medio, y solo el predimensionamiento (D-019) la fijará.

### 3.2 Envolvente — áreas netas

- Muro bruto: perímetro 108 m × ~7,5 m = **810 m²**.
- Vanos: 2 portones (2 × 23) + vidrio principal (28) + ventanas P2 (40) + ventanas de servicio
  (12) + puerta peatonal (≈4) = **≈130 m²**.
- **Panel neto de fachada: ≈680 m²** → el desglose usa 640 m² (**−6 %, ≈−$5–6 M**).
- Cubierta: 648 m² + solape/pendiente ≈ **655–665 m²** → el desglose usa 620 m² (**−5 %,
  ≈−$3–4 M**).

### 3.3 Cimentación

- 16 columnas de pórticos/entrepiso × (zapata ≈1,8 × 1,8 × 0,5 + pedestal 0,5 × 0,5 × 1,0)
  ≈ 30 m³ → el desglose usa 24 m³ (**−20 %**). Con vigas de amarre 12 m³, el total realista es
  ≈42–50 m³ vs. 36 m³ del control. Si la geotecnia del predio es pobre, crece más (R-05).
- El 03 del control ($35 M) es defendible solo con suelo bueno y cargas ligeras; la
  cimentación de un entrepiso de 270 m² y una luz de 18 m debe verificarse con reacciones
  conceptuales antes de congelar.

### 3.4 Losa PB — precio del concreto

- 97 m³ a $420.000/m³ = $40,7 M. La referencia CYPE de concreto 21 MPa preparado en obra es
  $520.985/m³ (incluye mano de obra de fundida). Si el precio real es $460–500/m³ (planta +
  vaciado), el capítulo 04 crece **≈+$4–8 M**.
- El sistema completo del desglose ($83 M ≈ $128.000/m²) es coherente con la filosofía
  "losa = estructura + acabado", pero es ~28 % inferior al sistema industrial CYPE
  ($177.239/m²) porque usa 15 cm (vs. 20 cm), pulido parcial (400 de 648 m²) y concreto más
  barato. Es el capítulo donde el target confía más en cantidades reales de diseño.

### 3.5 Vidrio y portones

- Evento 28 m² a $1.180.000/m² = $33 M. A precio CYPE de muro cortina ($1.290.364/m²) serían
  $36,1 M. Si el evento es una ventana fija de perfil industrial (no muro cortina), el precio
  de desglose puede sostenerse; si exige templado/laminado por tamaño, sube a $38–42 M.
- Portones 2 × 23 m² a $480.000/m²: dentro del rango comercial colombiano de seccionales
  aislados ($400–700.000/m²), pero la altura de 4,80 m y la motorización deben cotizarse en
  2–3 marcas; un "especial" duplica plazo y precio (R-12).

### 3.6 Lectura del costo por m² (descomposición honesta)

| Zona                                                                 |   Área | Costo unitario implícito realista | Lectura                                |
| -------------------------------------------------------------------- | -----: | --------------------------------: | -------------------------------------- |
| PB nave industrial abierta (cáscara: cim., losa, acero, envolvente)  | 648 m² |                  ≈$700–900.000/m² | Coherente con naves metálicas aisladas |
| P2 residencial (4 suites, 4 baños, wellness, acabados, MEP asociado) | 270 m² |                    ≈$1,6–2,2 M/m² | Se acerca a VIS/media residencial      |
| Frentes singulares (vidrio, portones, escalera, terraza)             |      — |                                 — | Distribuidos sobre el total            |

El blended de $1.076.000/m² del target y el de ≈$1.190.000/m² del escenario B son bajos _en
promedio_ precisamente por la participación de la PB industrial; no son comparables con una
vivienda convencional del mismo metraje. La descomposición por capítulo es la métrica de control.

---

## 4. Hallazgos y problemas — con severidad

### 4.1 Severidad ALTA

| ID       | Hallazgo                                                                                                                                        | Evidencia                       | Impacto estimado                        |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------- | --------------------------------------- |
| **A-01** | Tonelaje de acero subestimado (28,35 t vs. 30–45 t realistas)                                                                                   | §3.1; el propio v0.2 lo declara | **+$55–100 M** (cap. 05/06)             |
| **A-02** | Fachada a $140.000/m², −8 % bajo CYPE verificado $152.266/m²; falta perfilería térmica                                                          | §2, CYPE FLA030 vivo            | **+$10–25 M** (cap. 09)                 |
| **A-03** | Vidrio principal apretado ($1,18 M/m² vs. $1,29–1,49 M/m² muro cortina)                                                                         | §2, CYPE FMC010 vivo            | **+$3–10 M** (cap. 12)                  |
| **A-04** | Entrepiso P2 con 3.000 kg de vigas; cálculo paramétrico ≈9–11 t                                                                                 | §3.1                            | **+$45–60 M** (dentro de A-01)          |
| **A-05** | **Detección de incendios ausente** del desglose (taller, car bay, homelab, sauna, P2); el v0.2 declara "sistemas de incendio" en F1 sin partida | DOCX §2 y estrategia F1         | **+$8–15 M** (cap. 17 o capítulo nuevo) |

### 4.2 Severidad MEDIA

| ID       | Hallazgo                                                                                                                                           | Evidencia                                               | Impacto estimado                         |
| -------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- | ---------------------------------------- |
| **A-06** | SG-SST, laboratorio/ensayos y gestión de residuos sin partida explícita (obligatorio en obra colombiana: Decreto 1072/2015, Resolución 0141, etc.) | DOCX cap. 01 solo $2 M seguros + $1 M ensayos iniciales | **+$8–15 M** (cap. 01)                   |
| **A-07** | Seguros bajos: $2 M para todo riesgo + RC de una obra de $941 M (≈0,3–0,5 % del valor)                                                             | Cap. 01.05                                              | **+$2–4 M**                              |
| **A-08** | Sauna F2 en $3 M (16.08); una sauna finlandesa para 6 personas (cabina, calefactor, bancas, barrera de vapor, ventilación) cuesta $8–15 M          | §2 y mercado                                            | **+$5–8 M** (F2)                         |
| **A-09** | Calentamiento de agua $2,3 M para todo el programa (clima frío de altura exige más potencia)                                                       | Cap. 15.04                                              | **+$2–4 M**                              |
| **A-10** | Cubierta medida en 620 m² cuando el área real es ≈655–665 m²                                                                                       | §3.2                                                    | **+$3–4 M** (cap. 08)                    |
| **A-11** | Cimentación ligera (36 m³) vs. ≈42–50 m³ paramétrico; depende de geotecnia                                                                         | §3.3                                                    | **+$5–10 M** (cap. 03)                   |
| **A-12** | Acometida eléctrica rural y posible transformador no modelados (R-09); el DOCX asume "capacidad para programa final"                               | DOCX §2                                                 | +$10–30 M si aplica (costo de predio)    |
| **A-13** | Fase 2 con $74 M sin remobilización, escalamiento ni protección de casa ocupada                                                                    | Estrategia F1/F2 §"costos que F2 debe presupuestar"     | F2 real ≈$90–120 M                       |
| **A-14** | Contingencia 5 % baja para confianza baja-media; práctica 10–15 % hasta PE-2                                                                       | Guías 2026 (mín. 15 % con imprevistos)                  | +$45–90 M sobre el control si se corrige |

### 4.3 Severidad BAJA / notas

| ID   | Nota                                                                                                                                                                              |
| ---- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A-15 | Impacto de la revisión b04 (puerta posterior de bodega, descarga de escalera, frontera F1/F2, isla 3,60 × 1,20 m) sigue sin cuantificar; afecta 10, 14, 19, 20, 22 y 24 (v0.3-A). |
| A-16 | Puertas interiores: 9 en el desglose; un programa de 4 suites + wellness + lavandería + núcleo razonablemente necesita 12–14.                                                     |
| A-17 | Tabiques P2: 200 m² + 80 m² PB = 280 m²; las particiones reales de P2 pueden requerir 250–300 m².                                                                                 |
| A-18 | Protección anticorrosiva (05.05 $6,9 M) calculada para 19,2 t; si el acero crece, crece con él. Decidir galvanizado vs. pintura por exposición (clima seco de altura interior).   |
| A-19 | CCTV en $500.000 (18.05): insuficiente para una propiedad rural de 918 m² si se incluyen cámaras (puede considerarse equipamiento, fuera de obra).                                |
| A-20 | Venta de excedentes de excavación/relleno y manejo de aguas de obra (02.04 $600.000) dependen del predio.                                                                         |

---

## 5. Estimación ajustada por capítulo (escenario B — más probable)

| Código | Capítulo                               | Control v0.2 |      Ajuste |    Control ajustado | Evidencia principal                          |
| ------ | -------------------------------------- | -----------: | ----------: | ------------------: | -------------------------------------------- |
| 01     | Preliminares, campamento, replanteo    |        $15 M |      +$10 M |               $25 M | Seguros +$3 M; SG-SST/ensayos/residuos +$7 M |
| 02     | Excavaciones y movimientos             |         $7 M |       +$3 M |               $10 M | Mejoramiento/rellenos según geotecnia        |
| 03     | Cimentaciones, pedestales y anclajes   |        $35 M |      +$10 M |               $45 M | Volumen 36→~46 m³; suelo incierto (R-05)     |
| 04     | Losa PB industrial                     |        $83 M |       +$5 M |               $88 M | Concreto $460–500 k/m³ vs. $420 k            |
| 05     | Estructura principal nave + P2         |       $145 M |      +$65 M |              $210 M | Acero 19,2→~28 t (pórticos + entrepiso)      |
| 06     | Correas, secundaria, arriostramientos  |        $55 M |       +$3 M |               $58 M | Áreas reales de girts/correas                |
| 07     | Losa metaldeck P2                      |        $41 M |          $0 |               $41 M | CYPE $150.400/m² ✓                           |
| 08     | Cubierta metálica aislada              |        $70 M |       +$3 M |               $73 M | 620→~660 m² reales                           |
| 09     | Fachadas de panel aislado              |        $95 M |      +$15 M |              $110 M | 680 m² × $152 k (CYPE) + remates             |
| 10     | Canales, remates, flashing y sellos    |        $20 M |       +$2 M |               $22 M | Perímetro y encuentros reales                |
| 11     | Dos portones industriales              |        $24 M |       +$2 M |               $26 M | Altura 4,80 m + motorización; cotizar        |
| 12     | Gran evento de vidrio                  |        $38 M |       +$4 M |               $42 M | Sistema real $1,29 M/m² o templado           |
| 13     | Ventanas restantes + puerta peatonal   |        $20 M |       +$2 M |               $22 M | Cotización de carpintería                    |
| 14     | Divisiones P2/núcleo + acústica        |        $38 M |       +$4 M |               $42 M | 280→~330 m² + puertas 12–14                  |
| 15     | Redes hidrosanitarias                  |        $20 M |       +$4 M |               $24 M | Calentamiento +$2 M; red según predio        |
| 16     | Baños + ducha/sauna + húmedos          |        $35 M |       +$7 M |               $42 M | Sauna real +$5 M; griferías/aparatos         |
| 17     | Electricidad, tableros, iluminación    |        $42 M |       +$5 M |               $47 M | Detección de incendios +$5 M (A-05)          |
| 18     | Datos, red, Home Assistant             |         $8 M |       +$1 M |                $9 M | Puntos/cámaras mínimos reales                |
| 19     | Extracción, ventilación, climatización |        $25 M |       +$2 M |               $27 M | Balanceo y ductería reales                   |
| 20     | Cocina fija, muebles, mesones          |        $25 M |          $0 |               $25 M | Fabricación nacional modular ✓               |
| 21     | Closets + cajoneras + bancos taller    |        $30 M |          $0 |               $30 M | Nacional modular ✓                           |
| 22     | Escalera metálica + barandas           |        $12 M |          $0 |               $12 M | Rango de mercado ✓                           |
| 23     | Acabados P2 y pintura puntual          |        $25 M |       +$2 M |               $27 M | P2 residencial real                          |
| 24     | Terraza inmediata + drenajes           |        $18 M |          $0 |               $18 M | Rango de mercado ✓                           |
| 25     | Elevador automotriz + provisión civil  |        $15 M |          $0 |               $15 M | Equipo $10,9 M verificado ✓                  |
|        | **Total obra física**                  |   **$941 M** | **+$149 M** |       **≈$1.090 M** | rango $1.050–1.150 M                         |
|        | Contingencia 5 % v0.2                  |        $47 M |           — |                   — | recomendado 8 % → $87 M                      |
|        | **Control de obra**                    |   **$988 M** |             | **≈$1.135–1.240 M** | según contingencia                           |

Conciliación con el radar v0.2: las oportunidades 1–6 suman −$48 a −$101 M potenciales sobre los
capítulos que hoy están apretados. Si la ingeniería y las cotizaciones las confirman, el
escenario B podría acercarse al target; si no, el control supera los $1.050 M y se activa el
value engineering formal (banda declarada del propio v0.2).

---

## 6. Costo total del proyecto — estructura obligatoria (CF-001 / CF-007)

La auditoría refuerza la regla del expediente: no mezclar "obra física" con "costo total del
promotor". Estimación de rango con esta auditoría (no cotización):

| Componente                                                                                            |          Estimación | Observaciones                                                                                |
| ----------------------------------------------------------------------------------------------------- | ------------------: | -------------------------------------------------------------------------------------------- |
| Obra física de control (escenario B)                                                                  |      $1.135–1.240 M | incluye contingencia 8 %                                                                     |
| Costos blandos (diseños, geotecnia, topografía, licencia, interventoría/supervisión, seguros finales) |          $250–400 M | arquitectura 8–10 %, estructura, MEP, geotecnia $8–15 M, licencia 1–3 %, interventoría 4–6 % |
| Conexiones y soluciones del predio (acometida/transformador, agua pozo o red, PTAR, acceso)           |          $100–280 M | dependen 100 % del predio; externos a obra                                                   |
| Equipamiento (electrodomésticos, taller, homelab, mobiliario suelto)                                  |          $160–400 M | separado por regla v0.2 §6.6                                                                 |
| Exteriores no inmediatos (cerramiento, vías, paisaje)                                                 |           $70–180 M | fuera de la obra inmediata                                                                   |
| Escalamiento temporal + reserva del promotor                                                          |          $180–300 M | 10–15 % del subtotal; la Fase 2 tendrá su propia fecha base                                  |
| **Total promotor estimado**                                                                           | **≈$1.800–2.500 M** | central ≈$2.100 M; lote en $0 (propiedad del promotor)                                       |

Lectura del conflicto: v0.1 ($4,3–4,8 B) era una capacidad de planeación con precios altos y
alcance total; v0.2 ($988 M) es un objetivo de _obra física_ optimista. El rango probable está
entre ambos y mucho más cerca de v0.2 para la obra física, con el total del promotor en el
rango de $1,8–2,5 B. **Ninguna de las dos cifras heredadas es un precio de mercado validado.**

---

## 7. Racionalización y mejoras propuestas a la estructura de costos

### 7.1 Acciones de mayor retorno (orden sugerido)

1. **Predimensionamiento estructural con 3 modulaciones y 2 sistemas (D-019)** — es la acción
   que más mueve el presupuesto: fija tonelaje real, entrepiso y cimentación. Reemplaza 05 y 03.
2. **Geotecnia conceptual del predio candidato antes de PE-1** — decide cimentación y losa
   (02, 03, 04) y ahorra el sobrediseño más común.
3. **Cotizar panel aislado vs. sistema por capas (teja + lana con facing + liner)** con cálculo
   de punto de rocío (D-020) — el frente con mayor ahorro sin cambiar la apariencia (−$15 a
   −$30 M) y el de mayor riesgo si se hace mal.
4. **Cotizar vidrio principal y portones en medidas estándar con 2–3 proveedores** antes de
   congelar dimensiones (11, 12, 13).
5. **Incorporar al modelo las partidas ausentes** (A-05 a A-09): detección de incendios,
   SG-SST/ensayos, seguros, sauna y calentamiento reales. Son obligaciones de obra y de vida
   segura, no acabados.
6. **Separar contingencia de diseño (hasta PE-2) de contingencia de obra**: proponer 5 % de
   obra + 3–5 % de incertidumbre de diseño hasta cerrar cantidades.

### 7.2 Mejoras de estructura del presupuesto (v0.4 sugerida)

- **Agregar capítulo 26 "Protección contra incendio y vida segura"** (detección, alarma,
  extintores/red en taller y car bay, señalización) — hoy sin partida explícita.
- **Agregar capítulo 27 "Seguridad y salud, laboratorio y ensayos, gestión de residuos"** con
  partidas obligatorias de obra colombiana; sacarlas del capítulo 01 implícito.
- **Desagregar el 05 en "nave (pórticos + columnas)" y "entrepiso P2"** para controlar por
  separado el frente de mayor riesgo.
- **Presupuestar la Fase 2 con su propia estructura**: remobilización, escalamiento ICOCED,
  protección de casa ocupada y re-ensayos; no ejecutar con los $74 M nominales de 2026.
- **Registrar el costo de predio (conexiones) como "costo de predio", no como obra**, en la
  estructura obligatoria del promotor.

### 7.3 Notas de ingeniería para el estructural (D-019)

- Preferir bays de 6 m, perfiles estándar de stock y acero S355 en principales / S235 en
  secundarios; comparar pórticos vs. cerchas sin prejuicio estético.
- No sobredimensionar los 648 m² por el lift ni por el entrepiso: resolver localmente (regla ya
  vigente). El entrepiso merece su propia cuantía: esperar **9–11 t de viguetas + vigas**, no 3 t.
- La estructura se calcula para el edificio final y se ejecuta completa en F1 (regla vigente);
  la auditoría confirma que F1 es donde están todos los frentes de riesgo.
- Coordinar la envolvente con los girts reales y los perfiles térmicos: el panel a $140 k/m² no
  incluye la estructura soporte ni los puntos singulares (CYPE FLA030 lo excluye explícitamente).

### 7.4 Qué no debe tocarse para ahorrar

- No reducir seguridad estructural, resistencia al fuego ni egreso (segunda salida P2 abierta).
- No diferir envolvente, cubierta ni estanqueidad a F2.
- No elegir aislamiento solo por precio sin barrera de vapor en lado cálido y punto de rocío.
- No eliminar el gran evento de vidrio (hard rule); optimizar dimensión y especificación.

---

## 8. Protocolo de cotización recomendado (reemplaza de forma ordenada las partidas)

1. **Estructura (05/06):** predimensionamiento con 3 modulaciones y 2 sistemas; kg/m² y costo
   fabricado/montado. Reemplaza 05.01–05.05 y 06.01–06.06.
2. **Losa/cimentación (02/03/04):** geotecnia del predio candidato; m³, refuerzo, subbase,
   juntas y acabado. Reemplaza 02.01–04.09.
3. **Envolvente (08/09/10):** m² netos por fachada y cubierta, espesores, remates y puentes
   térmicos; cotizar panel aislado vs. sistema por capas.
4. **Vidrio/portones (11/12/13):** dimensiones y desempeño; 2–3 cotizaciones en medidas
   estándar.
5. **MEP (15/17/18/19) + nuevo 26:** cargas, puntos, circuitos, tuberías, equipos, detección
   de incendios y commissioning.
6. **Baños/sauna/cocina/carpintería (16/20/21/23):** aparatos, herrajes, metros lineales y
   prototipos; separar equipamiento.

Cada partida reemplazada conserva: código, cantidad, precio, fuente, municipio, fecha,
confianza y variación frente a este desglose (regla v0.2).

---

## 9. Fuentes consultadas (acceso 2026-08-11)

- CYPE Generador de Precios Colombia — acero EAP020 A36 ($6.587,26/kg) y A572 Gr.50
  ($7.375,64/kg): https://colombia.generadordeprecios.info/obra_nueva/Estructuras/Acero/Perfiles_estructurales/
- CYPE — concreto 21 MPa CHH030 ($520.984,68/m³):
  https://colombia.generadordeprecios.info/sika/obra_nueva/Cimentaciones/Concretos__aceros_y_encofrados/Concretos/CHH030_Concreto_para_armar_en_losas_de_cim.html
- CYPE — piso industrial RSI007 ($177.239,20/m²):
  https://colombia.generadordeprecios.info/obra_nueva/Revestimientos/Pisos/RSI_Sistemas_de_pisos_industriales/RSI007_Piso_industrial_de_concreto_tratado.html
- CYPE — fachada panel sándwich FLA030 ($152.266,44/m²):
  https://colombia.generadordeprecios.info/rehabilitacion/Fachadas_y_muros_divisorios/Fachadas_ligeras/Metalicas/FLA030_Fachada_de_paneles_sandwich_aislant.html
- CYPE — cubierta sándwich QTM010 ($101.009,74/m²):
  https://colombia.generadordeprecios.info/rehabilitacion/Cubiertas/Inclinadas/QTM_Paneles_sandwich_aislantes_met/QTM010_Cubierta_inclinada_de_paneles_sandw_0_0_0_0_0_0_0_0_0_0_1_0.html
- CYPE — losa metaldeck EHX011 ($150.399,51/m²):
  https://colombia.generadordeprecios.info/obra_nueva/Estructuras/Concreto_armado/Losas_compuestas_metaldeck/EHX011_Losa_compuesta_metaldeck_con_lamina.html
- CYPE — drywall FBY010 ($83.629,82/m²):
  https://colombia.generadordeprecios.info/obra_nueva/Fachadas_y_muros_divisorios/FB_Muros_divisorios_interiores_de/De_placas_de_yeso_laminado/FBY010_Muro_divisorio_interior_de_placas_d.html
- CYPE — muro cortina FMC010 ($1.290.363,67/m²):
  https://colombia.generadordeprecios.info/rehabilitacion/Fachadas_y_muros_divisorios/Muros_cortina/Aluminio/Muro_cortina_de_aluminio.html
- Protalleres — elevador 2 columnas 4 t PT-240SC ($10.900.000):
  https://protalleres.com/product/elevador-dos-columnas-4tl/
- DANE — ICOCED junio 2026 (variación mensual +0,20 %; casas +0,12 %; bodegas +0,19 %):
  https://www.dane.gov.co/index.php/estadisticas-por-tema/precios-y-costos/indice-de-costos-de-la-construccion-de-edificaciones-icoced
- CalculaConstrucción — costo por m² Colombia 2026 (VIS $1,6–2,5 M; medio $2,2–3,2 M;
  residencial $3,2–5,0 M; imprevistos mín. 15 %):
  https://calculaconstruccion.com/co/centro-consultas/cuanto-cuesta-construir-casa-colombia-2026
- Exacon — guía de costo por m² Colombia 2026 (VIS $1,8–2,5 M; media $2,8–4,2 M; premium $5,5 M+):
  https://exaconcompany.com/2026/04/09/cuanto-cuesta-construir-una-casa-en-colombia-2026/
- Gobernación de Boyacá — Resolución 0033 de 2026 (lista regional de precios unitarios):
  https://www.boyaca.gov.co/resolucion-0033-de-24-de-abril-de-2026/
- Internas: v0.1, v0.2, desglose de control, bases estructurales y civiles, estrategia F1/F2,
  plan maestro, registro de decisiones, tecnicas_que_abaratan_costos.md.

---

## 10. Notas finales

- Esta auditoría **no cambia el target v0.2** ($941 M / $988,05 M) ni la distribución F1/F2.
  Su propósito es que la siguiente puerta económica (PE-1) se cruce con cantidades y precios
  verificados, no con un objetivo.
- Si el propietario desea mantener el techo de $1.000 M como meta de obra física, la ruta es
  ejecutar el protocolo de cotización §8 con prioridad estricta en estructura → envolvente →
  vidrio, y no abrir F1 hasta que esas tres estén cotizadas.
- Responsable de aprobación: propietario, arquitecto coordinador, ingeniero estructural e
  ingeniero MEP (pendiente). Cualquier adopción de los ajustes se registrará como decisión y
  actualizará [Base y control de costos](base_y_control_de_costos.md) con control de cambios.

**Fin — Auditoría de costos v0.1**
