# Estudio preliminar — integración de la estructura (E0) con los planos arquitectónicos

**Estatus:** pre-estudio de coordinación; ni el plano ni la estructura están en su forma
final; ninguna cifra ni trazado aquí es apto para construir.
**Versión:** 0.1
**Fecha de corte:** 2026-08-11
**Fuentes:** planos conceptual v0.3 borradores 05 (PB), 06 (P2), 07 (cubierta), 08
(claraboyas); modelo estructural E0 (`dreamhouse/structure/`, salidas en
`planos/estructura_e0/`); `dreamhouse/pb_b05.json`; `dreamhouse/p2_b06.json`;
`docs/03_ingenierias/bases_estructura_metalica.md`.
**Aprobación pendiente:** arquitecto coordinador, ingeniero estructural, propietario.

> **Aclaración de no-finalidad.** Este documento es un **pre-estudio de coordinación**.
> Los planos consultados (b05–b08) son borradores de anteproyecto y **no son la versión
> definitiva de los planos**; el modelo estructural E0 es un esquema de comparación y
> **no es la estructura final** ni una memoria de cálculo. El objetivo es detectar temprano
> los puntos donde estructura y arquitectura deberán coordinarse, para que la versión
> definitiva de ambos se diseñe conjuntamente (regla del concepto: estructura, fachada y
> luz se diseñan juntos). Nada de este documento es requisito congelado.

## Propósito

Comparar la geometría dibujada en los planos arquitectónicos con el esquema estructural
E0 (sistemas y modulación) y registrar, con trazabilidad de datos, qué encaja y qué
conflictos de coordinación deben resolverse. No se propone solución: se registran los
puntos de decisión para que arquitectura y estructura se coordinen en la versión
definitiva.

## 1. Estado actual: la estructura no está dibujada en los planos

Los planos arquitectónicos b05 (PB) y b06 (P2) **no contienen capa estructural**: no hay
ejes, columnas, pórticos ni cerchas dibujados. Los propios generadores lo declaran
("estructura sigue pendiente de ingeniería", "áreas netas se recalculan después de
estructura"). El modelo E0 vive separado en `planos/estructura_e0/`. La verificación de
integración debe hacerse sobre los datos fuente (`pb_b05.json`, `p2_b06.json`) y la
retícula de coordinación (6 × 6 m, que no obliga columnas interiores).

## 2. Coherencias confirmadas entre planos y estructura

| Aspecto | Valor | Lectura |
|---|---|---|
| Luz transversal | 18,00 m (Y = 0 → 18) | E0 = 18 m; coincide |
| Largo de nave | 36,00 m (X = 0 → 36) | E0 = 36 m; coincide |
| P2 posterior | X = 21,00 → 36,00 m = 15,00 m de fondo | E0 usa X = 21–36; coincide |
| Nivel terminado P2 | ≈ +3,80 m | E0 = 3,80 m; coincide |
| Cubierta monopitch | 7,20 m (lado bajo) → 7,80 m (lado alto), 3,33 % | b05/b07/E0 coinciden; sentido reversible (D-039) |
| Columnas | solo en muros largos (Y = 0 / Y = 18) | nave libre; cumple la intención |
| Lift automotriz | X ≈ 5,5–6,0 m en doble altura | pórtico X = 6 pasa a 7,2–7,8 m: no interfiere |
| Gran muro + escalera P2 | X = 31,5 m (muro) / x 31,5–36, y 7,4–11 (escalera) | línea X = 31,5 = mejor candidata de cercha oculta |
| Claraboyas (b08) | X = 2,4–4,8 m en primera crujía 0–6 m | no cruzan el pórtico X = 6; ✓ |
| Banda bajo P2 | 3,05–3,20 → 3,80 m (≈ 0,6 m) | vigas de 18 m no caben en la banda; exige viguetas cortas o cerchas de muro |

## 3. Conflictos de coordinación (por resolver en la versión definitiva)

### 3.1 Módulo estructural 6 m vs. eventos de vidrio de 7,2 m

El ventanal técnico mide 7,20 m (6 módulos de 1,20 m) y cruza la línea de pórtico X = 6:

- GLZ-CAR (muro A, x = 1,5–8,7 m): la columna X = 6 quedaría **dentro del vidrio**.
- GLZ-RC (muro B, x = 1,5–8,7 m): igual.

Consecuencia: la columna de muro interrumpiría el evento de vidrio. Hay tres caminos de
decisión (sin elegir aquí): (a) re-modular el vidrio a 6,00 m exactos (una crujía),
(b) adoptar M90 (9 m) o hit-and-miss (12 m) para que la GLZ de 7,2 m quepa entre columnas,
(c) aceptar las columnas como montantes de la "estructura visible" y coordinar módulos.

### 3.2 Columnas de muro dentro de las ventanas de dormitorios P2

Las ventanas de P2 casi piso a techo (2,7 m, antepecho 0,1 m) cruzan líneas de pórtico de
la modulación M60 (columnas en X = 0, 6, 12, 18, 24, 30, 36):

- W-H1 (muro sur, 22,0–25,8 m): cruza la columna **X = 24**.
- W-H2 (muro norte, 21,8–26,5 m): cruza la columna **X = 24**.
- W-G (muro norte, 27,8–32,3 m): cruza la columna **X = 30**.

Consecuencia: en los dos muros largos las columnas caen dentro de los vanos de los
dormitorios. La modulación elegida para la versión definitiva debe dejar los vanos entre
columnas o absorber las columnas en la composición de fachada.

### 3.3 Particiones del P2 sin líneas continuas de ancho completo — RESUELTO con el gran muro

El sistema staggered truss (cerchas de piso de 18 m entre los muros largos, ocultas en
particiones) exige líneas de partición continuas en X a todo lo ancho (Y = 0 → 18).
Comparando las particiones reales por fase:

- F1 (y = 0–11): X = [21,0, 24,2, 25,0, 26,2, 26,6, 28,6, 31,5, 32,8, 36,0]
- F2 (y = 11–18): X = [21,0, 23,4, 27,5, 29,5, 33,0, 36,0]
- **Líneas comunes: solo X = 21,0 y X = 36,0 (los bordes).**

**Resolución (E0 · 11-08-2026):** el esquema **GRAN-MURO** elimina esta restricción. El
muro de X = 31,5 (que ya existe, separa baño/escalera/homelab) se convierte en **muro
portante del P2**: recibe la franja del núcleo (X = 31,5→36) y la mitad del frente
(X = 21→31,5). El frente se apoya en **3 vigas longitudinales en el plenum**
(3,20→3,80 m) + la cercha de borde X = 21. No se requieren cerchas de ancho completo ni
re-articular particiones: las vigas van ocultas en el plenum del cielo de PB.

### 3.4 Borde de P2 en X = 21,00 m (luz ≈ 18 m) sin resolver en los planos

En los planos no existe la viga/cercha de borde del P2 hacia la doble altura. Sobre ese
borde apoyan el mini deck (x = 21, y = 5–8,2), la lavandería (x = 21–25) y los dormitorios
H1/H2 (x = 21). En estructura debe definirse una **cercha de borde** (o primera línea del
staggered truss) apoyada en las columnas de los muros largos, dejando libre la
cocina/comedor de PB. Su canto debe absorber el plenum de la banda doméstica o expresarse
como pieza estructural legible.

### 3.5 Entrepiso METALDECK con apoyos intermedios = columnas en la zona doméstica

El esquema de entrepiso de la línea base E0 (viguetas + vigas transversales de 18 m + dos
apoyos intermedios por pórtico) introduce columnas en cocina/núcleo de PB. Es el conflicto
estructural–arquitectónico abierto del E0. La alternativa staggered (sección 3.3) elimina
esas columnas pero depende de la re-articulación de particiones.

## 4. Decisiones de coordinación para la versión definitiva

Estos puntos son las puertas de decisión; no se resuelven aquí:

1. **Módulo estructural compatible con los eventos de vidrio de 7,2 m** (M60 / M90 /
   hit-and-miss 12 m, o vidrio re-modulado a 6 m).
2. **Entrepiso P2 con el gran muro como apoyo (esquema GRAN-MURO, E0):** el muro de
   X = 31,5 se diseña portante (0,20–0,30 m, continuo al cimiento y hasta la cubierta por
   la caja de escalera); 3 vigas longitudinales en el plenum + cercha de borde X = 21.
   Ya no se requiere re-articular particiones del P2. Verificar en E1 la continuidad del
   muro (vanos de puertas del núcleo) y su fundación corrida.
3. **Viga/cercha de borde en X = 21,00 m** con apoyo en los muros largos y ménsula de
   media crujía.
4. **Sentido del faldón con el predio** (D-039) antes de fijar cargas de viento y drenaje.
5. **Retícula estructural superpuesta como capa de control** sobre PB y P2 en la próxima
   revisión de planos.

## 5. Método y trazabilidad

Análisis realizado sobre datos fuente programáticos (no sobre renders): `pb_b05.json`
(envelope, front_openings, technical_glazing, bedroom_glazing, core) y `p2_b06.json`
(rooms, windows, phase_boundary_y = 11). La retícula M60 asumida es la de coordinación
(columnas en X = 0, 6, 12, 18, 24, 30, 36 sobre los muros Y = 0 e Y = 18). Toda
verificación numérica es reproducible con el módulo `dreamhouse/structure/`.

## 6. Regla anti-falsa-precisión

Este pre-estudio usa cotas de borrador (planos b05–b08, no definitivos) y hipótesis de
esquema (E0, no diseño profesional). Las mediciones de conflicto son lecturas de
coordinación, no dimensiones de construcción. Nada de aquí autoriza compra, cotización ni
construcción; la versión definitiva de planos y estructura se coordinará en las puertas
E1/PE-1 con el ingeniero estructural y el arquitecto coordinador.
