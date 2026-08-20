# Bases MEP, confort y automatización

**Estatus:** base de coordinación; no es diseño ejecutable  
**Versión:** 0.8
**Fecha:** 2026-08-20

## Filosofía

Infraestructura abundante, ordenada, medible y mantenible; equipos solo donde agregan
desempeño. Estructura visible, servicios visualmente silenciosos. Ningún sistema de vida
segura dependerá exclusivamente de Home Assistant o de internet.

## Electricidad e iluminación

El estudio de cargas debe inventariar al menos:

- lift y herramientas automotrices;
- 2–3 impresoras 3D, electrónica, cargadores LiPo y bancos RC;
- dos estaciones de trabajo;
- homelab/rack, UPS, PoE, CCTV y red;
- cocina y refrigeración abundante;
- cinco baños, lavandería y sauna;
- calefacción, ventilación, extracción y destratificación;
- portones, bombas, exteriores, futuro solar/baterías y cargas de reserva.

Definir capacidad de acometida, tableros, selectividad/protecciones, puesta a tierra,
protección contra sobretensiones, circuitos dedicados, desconexiones visibles de equipos,
caída de tensión, emergencia y expansión. La obra y certificación deberán cumplir el
RETIE/RETILAP vigentes y ser realizadas por personal competente.

La iluminación se organizará por capas: general integrada a estructura, tarea en talleres
y cocina, ambiental residencial, circulación/seguridad y exterior. Evitar que una pieza
decorativa compita con la nave o sea indispensable para iluminarla.

Under D-068, each fixed PB workstation receives an accessible task-power and lighting
interface below the worktop. Keep outlet boxes, drivers and cable trays removable without
disturbing the facade air/water seals, window drainage or structural connections. Final
outlet counts and equipment loads require the real computer and peripheral schedule.

## Datos, red y automatización

- Rack con acceso frontal/posterior, energía, ventilación y detección.
- Topología cableada; patch panels; switches/PoE; router/firewall; NVR y gateways.
- Puntos Ethernet en habitaciones, escritorios, televisores, taller y access points.
- Separación y cruces controlados entre potencia y datos.
- Conduits vacíos con guía y capacidad de reserva.
- Etiquetado extremo a extremo y planos as-built.
- Sensores de temperatura, humedad, CO, CO₂, VOC, partículas, fugas, presencia, puertas,
  energía, lluvia y condiciones exteriores según análisis de riesgo.

Route dedicated data to both D-068 workstations through the accessible steel service-rail
zone. Maintain power/data separation, bond exposed metal where required, retain spare
conduit capacity and avoid inaccessible cables inside primary steel or window frames.

D-069 cabinet banks may not block that accessible service zone. Coordinate cable entries,
drawer extension, ventilation for equipment stored in cabinets and removable access
panels with the full-scale workstation mock-up; bond the powder-coated steel carcasses
where required by the electrical design.

Under D-072, route project-car task power, lighting, source extraction, controls and any
compressed-air service through an accessible Side A bench zone. Keep isolators reachable,
protect services from vehicle/tool impact and preserve technical-window drainage and
facade air/water seals. The selected lift and vehicle must govern final outlet, hose,
duct, emergency-stop and equipment-clearance positions.

Under D-073, start both accessible bench-service rails at the front interior corners but
keep isolators, bends and removable covers clear of industrial-door jambs, tracks, guards
and seals. Do not create concealed dead-end service pockets at either corner.

Under D-071, provide an accessible service zone at the Side B perimeter wall for dedicated
power, data, spare AV conduits, speakers, controls and equipment ventilation. Keep
connectors, power supplies and active devices replaceable without opening the exterior
wall or compromising insulation, vapour, air/water, fire and acoustic layers. Coordinate
screen glare and motorized blackout control with the selected site, retain autonomous
manual operation and do not treat the 100-inch test envelope as a selected product.

Home Assistant coordinará confort, alertas y eficiencia, pero detección/alarma exigida,
protecciones eléctricas, controles de seguridad de equipos y paro de emergencia conservarán
funcionamiento autónomo y conforme.

## Hidráulica y sanitaria

Coordinar cuatro baños P2, lavandería, wellness/ducha, baño PB, cocina, pantry/bodega y
puntos exteriores. Agrupar bajantes y shafts sin comprometer acústica, mantenimiento o
habitabilidad. Definir presión, calentamiento, recirculación si se justifica, tratamiento,
drenajes, ventilaciones, registros, impermeabilización y pruebas.

La solución de agua/saneamiento depende del predio: redes públicas, almacenamiento,
bombeo, pozo o tratamiento rural no pueden presupuestarse aún.

## Preparación de zonas diferidas

La Fase 1 dimensionará acometida, tableros, montantes, shafts, bajantes, ventilaciones y
rutas para el programa final. En las suites/wellness de Fase 2:

- dejar conduits con guía y cajas/espacios accesibles, no cableado abandonado sin uso;
- probar y documentar redes troncales antes de cerrar;
- terminar ramales de agua cerca de válvulas accesibles para evitar largos tramos
  estancados;
- tapar y proteger desagües/ventilaciones con identificación y coordenadas as-built;
- reservar potencia, extracción y drenaje del sauna según equipo de diseño, sin comprarlo;
- mantener condiciones mínimas de ventilación/humedad del shell para no degradar la
  envolvente.

La Fase 2 repetirá pruebas y commissioning; no se asumirá que una reserva guardada durante
años continúa limpia, estanca o conforme a la norma vigente.

## Clima, ventilación y envolvente

Antes de seleccionar equipos se requiere:

1. clima y orientación del predio;
2. modelo térmico por zonas;
3. especificación de envolvente, infiltración y puentes térmicos;
4. análisis de condensación superficial e intersticial;
5. cargas internas de personas/equipos;
6. estrategia de aire exterior y extracción.

La nave no se climatizará como un único dormitorio. Estudiar calor solar útil, calefacción
local o radiante donde convenga, control por zonas, ventiladores HVLS silenciosos y
destratificación basada en sensores bajos/altos.

## Extracción y aire de reposición

Capturar en la fuente: escape vehicular, soldadura/procesos si existieran, impresión 3D,
vapores, partículas y calor. Toda extracción necesita aire de reposición compatible con
confort, presión del edificio y combustión/equipos. No descargar contaminantes cerca de
ventanas, tomas de aire o áreas exteriores ocupadas.

## Acústica y vibración MEP

- Silenciadores, velocidades y soportes adecuados.
- Desacople de equipos y tuberías.
- Evitar cuartos ruidosos contra dormitorios.
- No atravesar separaciones acústicas sin sellado.
- Coordinar ruido de lluvia, portones, herramientas y HVAC.

## Energía y resiliencia

Preparar, sin sobredimensionar a ciegas, rutas y espacios para solar, medición, respaldo y
posibles baterías. Cualquier almacenamiento energético debe tener evaluación específica de
ubicación, incendio, ventilación, mantenimiento y normativa.

## Entregables mínimos

- Bases de diseño y cálculos por disciplina.
- Diagramas unifilares/esquemas y planos coordinados.
- Matriz de cargas y equipos con consumos, conexiones y responsables.
- Modelos/rutas sin colisiones con estructura.
- Especificaciones, cantidades y secuencias de pruebas.
- Plan de commissioning: presión, estanqueidad, balanceo, extracción, controles, red,
  sensores, alarmas, iluminación y consumo.
- Manuales y planos as-built.
