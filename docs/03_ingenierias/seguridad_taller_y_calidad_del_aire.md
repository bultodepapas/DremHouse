# Seguridad, taller y calidad del aire

**Estatus:** requisito de diseño; evaluación especializada pendiente  
**Versión:** 0.1  
**Fecha:** 2026-08-11

## Principio

La integración visual del taller no significa mezclar riesgos. El proyecto mantendrá la
lectura de nave abierta hasta donde la normativa y el análisis de peligro lo permitan,
pero introducirá contención, separación, detección, extracción o cerramientos locales si
son necesarios para proteger vida y propiedad.

## Inventario de peligros por confirmar

- Vehículo: gases de escape, combustibles, aceites, baterías, partes calientes, caída de
  objetos y operación del lift.
- RC/DIY: baterías LiPo, cargadores, soldadura electrónica, adhesivos, solventes, resinas,
  pinturas, polvo, corte y herramientas.
- Impresión 3D: partículas/ultrafinos, VOC, superficies calientes y operación prolongada.
- Homelab: carga eléctrica continua, calor, baterías UPS, humo y agua.
- Cocina/sauna: calor, humedad, superficies calientes y drenaje.
- Gran nave: trayectos de evacuación, humo en altura, portones, vidrio y posible
  estratificación de contaminantes.

## Zonas funcionales

- **Zona automotriz:** piso resistente, orden de circulación, extracción de escape en la
  fuente, almacenamiento químico controlado, paro y desconexión del lift.
- **Zona RC limpia:** electrónica y ensamblaje.
- **Procesos emisores:** extracción local o recinto técnico específico si inventario real
  incluye pintura, resina, composite, CNC, soldadura u otros.
- **Carga/almacenamiento LiPo:** ubicación dedicada y no combustible, lejos de dormitorios
  y rutas de salida; método final definido por especialista y fabricante.
- **Homelab:** recinto separado de bodega húmeda/sucia, con monitoreo y control térmico.

## Reglas preliminares LiPo

- No congelar un “gabinete seguro” por imagen o marketing; verificar comportamiento,
  ventilación, propagación, detección y acceso de emergencia.
- Seguir especificaciones de batería/cargador y no cargar sin estrategia de supervisión.
- Separar baterías dañadas o hinchadas y definir protocolo de retiro.
- Evitar que la automatización doméstica sea la única protección.
- Registrar inventario, capacidades máximas y procesos reales antes de diseñar el área.

## Vehículo y lift

- Seleccionar equipo certificado y compatible con vehículo/cargas.
- Coordinar cimentación, anclajes, altura, puertas, iluminación y clearances.
- Delimitar zona de exclusión y circulación.
- Prever extracción de gases en la fuente; abrir portones no sustituye una estrategia.
- Almacenar combustibles/solventes según cantidad, ficha de seguridad y requisitos
  aplicables; no asumir que un mueble común es suficiente.

## Calidad del aire

La jerarquía de control será: eliminar/sustituir proceso, contener, capturar en fuente,
ventilar, monitorear y finalmente usar protección personal. Los sensores ayudan a detectar
tendencias, pero no reemplazan diseño de extracción ni prácticas seguras.

Parámetros de interés: CO, CO₂, VOC, PM2.5/partículas, temperatura y humedad. Los umbrales,
ubicaciones, calibración y respuesta serán definidos por el diseño de seguridad/ventilación.

## Incendio y evacuación

- Clasificar correctamente los usos residencial, taller/garaje y almacenamiento con la
  autoridad y profesionales del proyecto.
- Determinar separaciones, resistencia al fuego, detección/alarma, medios de egreso,
  señalización, extinción y acceso de emergencia exigibles.
- Mantener rutas desde P2 independientes de la operación del lift, bancos y portones.
- No colocar carga LiPo, químicos o equipo crítico en rutas de salida.
- Coordinar penetraciones y sellos de barreras que resulten exigidas.

## Información que debe entregar el propietario

Inventario de químicos y cantidades; procesos (pintura, soldadura, resina, CNC, composite);
modelos y número de impresoras; inventario/capacidad LiPo; herramientas y cargas; vehículo;
lift; frecuencia y simultaneidad de uso; número máximo de ocupantes/eventos.

## Puerta de aprobación

No se emite diseño para construcción hasta tener una matriz de peligros cerrada, estrategia
de incendio/egreso aprobada, ventilación calculada, fichas de equipos coordinadas y
responsabilidades de operación documentadas.
