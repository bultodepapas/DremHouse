# Fuentes, precedencia y conflictos

**Estatus:** activo  
**Versión:** 0.1  
**Fecha:** 2026-08-11

## Precedencia

En caso de contradicción gobierna, en este orden:

1. Decisión expresa posterior del propietario, registrada y fechada.
2. Constitución activa del proyecto.
3. Documento activo más reciente de la disciplina correspondiente.
4. Plano conceptual v0.2 para control dimensional.
5. Documento conceptual consolidado para intención y hard rules.
6. Presupuesto técnico v0.2 para el target económico de trabajo.
7. Documentos históricos.
8. Renders, croquis evocativos e imágenes de IA.

La normativa, la seguridad y los diseños firmados por profesionales competentes prevalecen
sobre una preferencia incompatible.

## Clasificación de las fuentes originales

| Fuente | Rol | Estado |
|---|---|---|
| `casa_bodega_boyaca_conclusiones_anteproyecto.md` | Intención, hard rules y síntesis | Activa como fuente conceptual |
| `Dream_House_Plano_Conceptual_v0.2.md` | Geometría y áreas nominales | Activa para control dimensional |
| `Dream House — Presupuesto Técnico y Control de Costos v0.2.docx` | Target y capítulos de obra | Activa, confianza baja-media |
| `Dream_House_Presupuesto_Preliminar_v0.1.md` | Prefactibilidad económica anterior | Histórica / superada |

## Conflictos detectados

### CF-001 — Presupuesto total

- v0.1: rango de planeación $4,3–4,8 B COP; reserva $5,0 B.
- v0.2: obra $941 M + 5% = $988,05 M; techo de control $1,0 B.
- **Regla temporal:** v0.2 es el target activo porque se declara sustituto, pero no es una
  cifra validada. No comprometer alcance, contrato ni financiación con ella hasta superar
  la puerta económica definida en el plan maestro.
- **Estado:** crítico, abierto.

### CF-002 — “Sin presupuesto rígido” frente a techo de $1,0 B

El concepto declara eficiencia sin restricción rígida; costos v0.2 establece techo. Se
trata el $1,0 B como restricción de diseño provisional, no como precio garantizado ni como
permiso para degradar desempeño.

- **Decisión requerida:** confirmar si $1,0 B es aspiración, techo de obra física o techo
  total de inversión.
- **Estado:** abierto.

### CF-003 — Áreas de suites

El texto conceptual menciona inicialmente 28–32 m² por suite de hijo y 23–26 m² para
huéspedes; el plano v0.2 asigna ≈38 m² por hijo y ≈32–33 m² a huéspedes.

- **Regla temporal:** gobiernan las áreas brutas del plano v0.2; la igualdad exacta aplica
  al área útil de los dormitorios de hijos.
- **Estado:** resuelto por precedencia, validar en planta neta v0.3.

### CF-004 — Áreas del núcleo posterior

La narrativa temprana propone bodega 16–20 m², homelab 7–9 m² y baño PB 5–6 m². El plano
v0.2 distribuye los 81 m² así: 22,5 + 10,8 + 20,7 + 10,8 + 16,2 m².

- **Regla temporal:** gobierna el plano v0.2 como reserva bruta nominal; en v0.3 debe
  demostrarse que el homelab y el baño no están sobredimensionados a costa de la nave.
- **Estado:** resuelto provisionalmente.

### CF-005 — Aritmética del núcleo

Una revisión del concepto afirma que 5,0 m de profundidad producirían ≈70 m² y que 4,5 m
producirían ≈63 m². Esas cifras corresponden a 14 m de ancho. Con 18 m, los valores son
90 m² y 81 m² respectivamente.

- **Regla:** el núcleo nominal activo es 18 × 4,5 = **81 m²**.
- **Estado:** error identificado; corregir en la siguiente consolidación de la fuente.

### CF-006 — Isla de cocina

La narrativa propone 3,6–4,0 × 1,10–1,25 m; el plano v0.2 propone 4,80 × 1,40 m.

- **Regla temporal:** 4,80 × 1,40 m es la envolvente de prueba; solo se adopta si la
  ergonomía, servicios, uso cotidiano y costo justifican su tamaño.
- **Estado:** abierto hasta layout de cocina v0.3.

### CF-007 — Alcance real del total de $988,05 M

El documento v0.2 lo denomina “total de construcción”, no costo total del proyecto. No
queda demostrado que incluya honorarios, estudios, licencia, conexiones, impuestos,
logística especial, seguros, interventoría, escalamiento o contingencias de predio.

- **Regla:** separar siempre obra física, costos blandos, equipamiento, predio/exteriores
  y reserva del promotor.
- **Estado:** crítico, abierto.

## Regla de resolución

Cada conflicto debe cerrarse con evidencia, responsable, fecha y decisión. “Usar el dato
más conveniente” no es un método válido.
