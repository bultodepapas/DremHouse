# Bases de diseño arquitectónico

**Estatus:** activo para anteproyecto  
**Versión:** 0.15
**Fecha:** 2026-08-21

## Forma y modulación

- Caja rectangular simple y repetitiva.
- Retícula arquitectónica inicial 6 × 6 m; no implica columnas interiores cada 6 m.
- Una cubierta continua, con pendiente y drenaje definidos por ingeniería/fabricante.
- No añadir volúmenes, porches, lucernarios, balcones o cubiertas secundarias sin beneficio
  medible.

## Sección

- P2 empieza nominalmente en X=21 m.
- Nivel P2 ≈+3,80 m, sujeto a canto real de estructura y redes.

### Shared stair-core control — D-074 / SC-01

- PB and P2 use the same enclosure at X=31.50–36.00 m and Y=7.40–11.00 m.
- The schematic dogleg uses 22 equal 172.7 mm risers, 20 equal 270 mm goings, two
  1.40 m flights and a 1.40 m intermediate landing at +1.90 m.
- PB reads the lower flight up to P2; P2 reads the upper flight down to PB. Neither plan
  may redraw the stair independently of `dreamhouse/stair_core.json`.
- The four D-048 column reservations remain exact at the enclosure corners. Stair flights
  have no primary lateral-system role and require drift-compatible interfaces.
- CF-011 is a blocking section-level conflict: the rear door plane meets the +1.90 m
  intermediate landing, not PB grade. Do not claim direct discharge until a coordinated
  alternative is professionally accepted.
- Bajo P2: 3,05–3,20 m libres.
- Habitaciones: 3,00–3,15 m libres.
- Nave: 7,20–7,80 m interiores de estudio.

Las cotas se congelan solo después de coordinar estructura, vibración, acústica, drenajes,
HVAC, iluminación, portones y lift.

## Luz y fachadas

La estrategia es **máximo efecto por unidad de vidrio**:

1. evento principal de sala/paisaje;
2. apertura social vinculada a comedor/cocina/plataforma según orientación;
3. paños generosos y controlados en dormitorios.

Los servicios pueden ser opacos. Se exigirán orientación real, control de deslumbramiento,
privacidad, ganancias/pérdidas, riesgo de condensación, sellos, drenajes y mantenimiento.

## Materialidad

- Estructura metálica oscura visible y uniones deliberadas.
- Losa PB industrial como estructura/sustrato/acabado cuando el diseño técnico lo permita.
- Panel metálico aislado como envolvente terminada.
- Madera concentrada en pared posterior, cocina, piezas técnicas seleccionadas y P2.
- Textiles y absorción donde mejoren acústica y escala doméstica.

The exposed-industrial rule is spatially selective under D-059. It remains strong in the
hall, workshops, exterior rainscreen and the deliberate hall-side X=21 truss. Private P2
interiors instead use smooth finished walls and conceal framing, primary steel, bracing,
membranes and services. This is a hierarchy of experiences, not a rejection of the
project's industrial identity.

## Pared posterior

Debe leerse como el testero final de la nave y resolver simultáneamente puertas ocultas,
orientación, calidez y absorción acústica. Una solución de listones/madera con respaldo
absorbente es preferida, no especificada aún.

## Acústica

No aceptar “acústica de hangar”. Distribuir absorción entre pared posterior, intradós o
bandas de cubierta, grandes textiles, cortinas compatibles, mobiliario y desacople de P2.
Un estudio preliminar debe definir objetivos y áreas absorbentes antes de acabados.

### P2 wall-thickness control — D-080

D-080 assigns thickness by duty instead of repeating an enhanced wall everywhere. The
active schematic schedule is:

| Type | Nominal thickness | Controlled use |
| --- | ---: | --- |
| P2-W01A | 90 mm | Dry boundary entirely within one suite |
| P2-W01B | 200 mm | Suite-to-suite or suite-to-common privacy boundary |
| P2-W02 | 150 mm | Wet/service partition; increase locally for confirmed shafts |
| P2-W02S | 200 mm | Sauna/hot-side coordination reserve; separate assembly pending |
| P2-W03 | 200 mm | Stair/protected-core reserve; tested fire/smoke system pending |
| P2-W04R | 200 mm | Retained bedroom ends at the open X=21 hall edge; use W01B intent |
| P2-W05 | 230 mm | Three exterior P2 edges: insulated industrial panel plus inner lining |
| P2-W06 | 90 mm | Reversible F1/F2 closure; upgrade if fire/smoke strategy requires it |

P2-W01A uses one nominal 64 mm light-gauge frame, 50 mm wool and one new 12.5 mm board
per face, producing an 89 mm illustrative sum within the 90 mm coordination value.
Restrict it to same-suite dry boundaries. P2-W01B retains the economical privacy logic:
two independent 64 mm frames, 50 mm wool in each, a 20 mm clear gap, one accepted
reclaimed concealed board and one new visible board at each outer face. Its illustrative
sum is 198 mm within a 200 mm coordination value. No tested acoustic or fire rating is
claimed. Select locally available tested systems, compatible doors, seals, head tracks,
penetrations and junctions before construction.

### P2 hall/workshop edge — D-063 / D-080

The X=21 family frontage remains open from Y=5.00 to 12.45 under D-063, with one
continuous guard. P2-W04R remains full height only at the two bedroom ends, totals
10.55 m in plan and uses the 200 mm P2-W01B separation intent. The exposed D-052 truss,
wall heads, edge beam, guard, anchors, roof movement, smoke movement and fire protection
require one coordinated professional detail. Do not infer guard, truss or fire capacity
from the architectural wall line.

### P2 integrated exterior envelope — D-080

P2-W05 applies to the south Y=0, north Y=18 and rear/east X=36 edges. Coordinate 230 mm
nominal as an integrated system: a 100 mm insulated corrugated metal facade-panel test
value, a 40 mm clear service/decoupling zone, one independent 64 mm frame with nominal
50 mm wool, one accepted reclaimed concealed 12.5 mm board and one new smooth 12.5 mm
finish board. The illustrative layer sum is 229 mm. This avoids constructing a redundant
second exterior stud frame behind a panel already carried in the global envelope strategy.

The panel is not selected and 100 mm is not a frozen core thickness. Compare locally
available 80–120 mm panel options after Boyacá climate, indoor-humidity, condensation,
vapour/air-control, wind, fire and acoustic analyses. Choose core type from the fire and
building-physics strategy, then engineer spans, girts, fasteners, corners, base, eaves,
windows, drainage, flashings and thermal bridges. Local boxes around primary columns may
project beyond 230 mm. Corrugated metal remains outside; private P2 retains the smooth,
concealed-service experience established by D-059.

See [P2 wall-thickness coordination — b25/R22](p2_wall_thickness_coordination_v0.3_b25.md).

## Detalle y mantenibilidad

### PB integrated workstation and workshop-bench family

D-068 requires two permanent PB workstations as one mirrored pair: one against each long
wall, both facing equal nominal landscape windows and both carried by dedicated bolted
secondary-steel service rails. The 3 × 3 m workstation reservations remain clearance
envelopes, not rooms or raised floor zones. The workstations and technical benches share
an economical steel-rail / replaceable-timber-worktop grammar, while their dimensions and
design loads may differ by use.

Do not assign primary gravity, lateral, facade or window-support functions to this fixed
furniture family. Coordinate local loads, deflection, vibration, trimmers, connections,
fire/corrosion protection, flashing, thermal bridges, condensation, power/data access,
glare and shading through the D-068 hold points. See
[PB integrated workstations — draft 24](pb_integrated_workstations_v0.3_b24.md).

D-069 retains this family and enlarges each workstation to a 3.00 × 0.90 m full-bay
worktop with two 0.70 m-wide suspended steel three-drawer cabinets and a 1.60 m clear
central knee/chair opening. The increased storage makes loaded-drawer, impact, racking,
deflection and cable-access checks more important. Treat these as test dimensions pending
the real equipment schedule and a full-scale joinery mock-up. See
[PB enlarged workstation cabinets — draft 25](pb_enlarged_workstation_cabinets_v0.3_b25.md).

D-078 replaces the Side A member of that pair with one 5.40 × 0.90 m two-person
worktop centred at X=15.75 m below one 7.20 × 2.90 m work/hall opening. Three 0.70 m
suspended cabinets create two equal 1.65 m clear positions. The Side B D-069 single
workstation remains unchanged. This intentional asymmetry follows different interior
programmes; exterior symmetry is not a design objective.

The Side A opening is controlled from the interior and may not become a premium facade
gesture. Outside, use a direct rugged industrial envelope with repeatable replaceable
modules, durable coatings, simple protected flashings and drainage. Resistance,
weathering, safe replacement, maintenance and whole-life cost govern appearance. The
7.20 m opening still requires a professionally designed header, jambs, stability path,
facade rails, safe glass, seals, thermal-bridge control and low-eave drainage. See
[PB Side A shared workstation and unified opening — draft 35](pb_side_a_shared_workstation_v0.3_b35.md).

D-072 applies the same permanent-infrastructure logic to the project-car bench: the
9.00 × 0.75 m worktop moves against Side A below its technical window, matching the
existing wall-side RC/electronics bench on Side B. The lift test envelope shifts 0.60 m
inward only to prove plan non-overlap; its 0.12 m gap is not an operational clearance.
Coordinate the real lift, vehicle, doors, cabinets, tool carts, extraction, services,
wall backing and facade seals before fabrication. See
[PB Side A project-car workbench — draft 28](pb_side_a_project_car_workbench_v0.3_b28.md).

D-073 moves both bench starts from X=0.55 m to the front interior corners at X=0.18 m,
without changing their 9.00 m lengths. Resolve each 0.27 m nominal bench/industrial-door
gap as one developed jamb, track, seal, guard and removable-service detail; the plan gap
does not authorize a product or safe clearance. See
[PB corner-start technical workbenches — draft 29](pb_corner_start_workbenches_v0.3_b29.md).

D-079 retains the two 9.00 × 0.75 m D-073 footprints and converts each into six
replaceable 1.50 m modules. The common grid is an economical local-fabrication and
phasing rule, not equal duty. Project Car tests five +0.90 m general modules and one
+0.84 m heavy-force/vice module. RC/electronics tests three 0.80 m-deep manual-adjustable
+0.70–1.10 m clean modules with localized ESD, while the remaining model/tool/landing
modules stay at +0.90 m. The central 4.50 × 1.60 m RC island becomes three 1.50 m
two-sided modules at a +0.84 m test height.

Reserve a 1.20 m operating strip at both wall benches. The Project Car strip overlaps the
generic lift/vehicle envelope by 1.10 m; do not resolve that conflict by silently moving
or shrinking unselected equipment. Select the real lift and vehicle, record owner
anthropometry, test full-scale modules and coordinate doors, windows, vice/impact loads,
drawers, RETIE, ESD, extraction, LiPo fire strategy and cost before fabrication. The
technical-window sill and worktop may align visually at +0.90 m but require independent
support, drainage, seals and a maintainable shadow/service gap. See
[PB modular technical workbenches — draft 36](pb_modular_technical_workbenches_v0.3_b36.md).

### PB living, dining, kitchen and media wall

D-070 removed the abstract PB sofa block, empty lounge/transition field and unassigned
Side B opening. D-071 retains those corrections but rejects D-070's freestanding X=21
media partition. The 100-inch television is fixed directly to a 4.40 m mounting field on
the Side B perimeter wall; the living group turns to face it beyond Y=11.00 m and east of
workstation 2. D-077 replaces only the inherited compact dining/kitchen relationship: one
centred 3.20 × 1.10 m table for 12 people now sits on Side B opposite the full-span Side A
kitchen across the clear axis. The kitchen uses a 10.05 m wall run and a dry
7.20 × 1.25 m island with eight schematic seats. The dining group retains a symmetric
1.10 m chair/walk envelope and remains independent of the media wall.

The mounting field is a local finish, backing and service zone within the existing
exterior-wall assembly, not a room divider or selected primary structure. Coordinate its
warm acoustic finish, matte screen background, AV console, local backing, sealed service
penetrations, 4.10 m sightline and site-dependent glare control. See
[PB Side B wall TV living — draft 27](pb_side_b_wall_tv_living_v0.3_b27.md). The
[superseded D-070 study](pb_living_dining_media_v0.3_b26.md) remains historical evidence.
See [PB b34 restored domestic layout](pb_restored_domestic_layout_v0.3_b34.md) for the
current kitchen/dining, centred Project Car/lift and retained SC-01 relationship. D-024,
appliance/MEP selection and Chapter 20 remeasurement remain open.

- Repetir familias de componentes.
- Diseñar encuentros panel–estructura–vidrio–portón antes de fabricar.
- Ocultar infraestructura sin volverla inaccesible.
- Coordinar drenajes, flashing, barreras, sellos y puentes térmicos como arquitectura.
- Diseñar reemplazo de impresoras, servidores, electrodomésticos y lift sin reconstrucción.

## Elementos aún no adoptados

- Fuego lineal en sala.
- X estructural visible dentro de un paño de vidrio.
- Jacuzzi.
- Lucernario excepcional.

Cada uno requiere decisión técnica, costo, mantenimiento y efecto sobre el concepto.
