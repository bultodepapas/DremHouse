# Herramientas digitales para planos, BIM y estructuras

**Estatus:** borrador de investigación; no constituye decisión de software ni diseño técnico  
**Versión:** 0.1  
**Fecha de corte:** 2026-08-11  
**Fuentes internas:** `08_investigacion/pythonTools.md`, constitución, programa v0.2,
bases de arquitectura y estructura, plan maestro y ruta normativa.  
**Aprobación pendiente:** propietario, arquitecto coordinador e ingeniero estructural.

## Resultado ejecutivo

Conviene desarrollar un **modelo paramétrico pequeño, determinista y auditable**, no un
clon de Revit ni un generador de plantas por imagen. La primera meta es producir borradores
v0.3 que prueben geometría, programa y reglas; el cálculo estructural inicial solo debe
comparar esquemas y revelar incompatibilidades.

La arquitectura recomendada es:

```text
entradas versionadas (JSON/YAML, SI, fuentes y estatus)
                    │
          modelo de dominio Python
                    │
       geometría + reglas + validaciones
          ┌─────────┼──────────┐
          │         │          │
     SVG/HTML      DXF        IFC + IDS
     revisión      CAD       BIM y auditoría
          │                    │
      PDF/PNG              Bonsai/visores
                    │
       modelo estructural separado
                    │
     resultados + supuestos + revisión profesional
```

**No debe ser canónico `building.py`.** El código es el motor; los datos versionados son
la entrada canónica. Así un agente puede proponer un cambio mediante un diff pequeño sin
reescribir lógica ni ocultar una decisión dimensional.

## Correcciones y precisiones a `pythonTools.md`

1. **Shapely no es un sistema CAD ni BIM.** Es adecuado para topología y medición 2D,
   pero no resuelve restricciones paramétricas, muros constructivos, unidades ni
   documentación por sí solo.
2. **OR-Tools debe posponerse.** Antes de optimizar hay que tener una variante manual
   válida, reglas comprobables y una función objetivo aceptada. De lo contrario optimiza
   proxies que no equivalen a calidad arquitectónica.
3. **IFC no debe generarse primero.** El MVP debe estabilizar IDs, unidades, coordenadas y
   semántica en un esquema propio; luego exportar IFC.
4. **CadQuery/build123d no son necesarios para la planta v0.3.** Reservarlos para piezas,
   envolventes o detalles paramétricos donde una BREP aporte valor.
5. **PyNite/OpenSeesPy son motores de análisis, no verificadores NSR-10 completos.** Las
   cargas, combinaciones, criterios de servicio, diseño de miembros, conexiones,
   cimentaciones y revisión normativa siguen siendo trabajo del ingeniero competente.
6. **Gmsh no es una necesidad temprana.** Solo entra si un modelo continuo o una malla
   especializada tiene una pregunta de ingeniería definida.

## Stack mínimo recomendado

| Función                 | Herramienta/formato      | Adopción propuesta               | Motivo                                                                 |
| ----------------------- | ------------------------ | -------------------------------- | ---------------------------------------------------------------------- |
| Datos canónicos         | JSON + JSON Schema       | MVP                              | Diff legible, validación, interoperabilidad y uso simple por agentes   |
| Modelo Python           | `dataclasses` o Pydantic | MVP                              | Tipos, unidades explícitas, mensajes de error y serialización          |
| Geometría 2D            | Shapely                  | MVP                              | Áreas, intersecciones, contención, distancias y offsets                |
| Vista inmediata         | SVG + HTML               | MVP                              | Abre en navegador, inspeccionable, liviano y apto para CI              |
| Tablas/reportes         | CSV + Markdown/HTML      | MVP                              | Áreas, reglas, trazabilidad y cantidades preliminares                  |
| CAD 2D                  | ezdxf                    | Piloto 2                         | Layers, cotas y entrega interoperable; DXF es salida, no fuente        |
| BIM abierto             | IfcOpenShell + IFC       | Piloto 3                         | Objetos y propiedades AEC; lectura/escritura y validación              |
| Requisitos BIM          | IDS + IfcTester          | Piloto 3                         | Requisitos IFC comprobables y reportes automáticos                     |
| Revisión BIM            | Bonsai                   | Piloto 3                         | Interfaz gráfica recomendada por IfcOpenShell para no programadores    |
| Relaciones              | NetworkX                 | Cuando haya puertas/recorridos   | Egreso, accesibilidad y conectividad; no sustituye distancias métricas |
| Optimización            | OR-Tools CP-SAT          | Después de v0.3 válida           | Variantes restringidas y reproducibles, con objetivos aprobados        |
| Estructura exploratoria | PyNite                   | Piloto paralelo controlado       | Pórticos 3D, combinaciones, estabilidad, P-Delta y visualización       |
| Estructura avanzada     | OpenSeesPy               | Solo por necesidad del ingeniero | No linealidad/dinámica; complejidad y licencia requieren control       |

Speckle puede evaluarse más adelante para colaboración y automatizaciones remotas. Su SDK
Python intercambia objetos y geometría y su plataforma ejecuta funciones ante cambios de
modelo; no se necesita para generar la primera planta y añade servidor, cuentas y gobierno
de datos.

## Contrato de datos amigable con agentes

Cada entidad debe tener como mínimo:

```json
{
  "id": "P2-HAB-HIJO-01",
  "type": "room",
  "name": "Dormitorio hijo 1",
  "storey": "P2",
  "geometry": { "kind": "rectangle", "x_m": 0, "y_m": 21, "width_m": 4.6, "depth_m": 4.4 },
  "requirements": { "target_area_m2": 20.2, "equal_area_group": "HIJOS" },
  "status": "hypothesis",
  "source": "docs/01_brief/programa_arquitectonico.md#reglas-de-p2",
  "revision": "0.1"
}
```

Reglas del contrato:

- sistema internacional internamente; sufijo de unidad en campos públicos;
- origen, ejes y orientación declarados; nunca coordenadas implícitas;
- IDs estables que no dependan del nombre visible;
- valores clasificados como `hard_rule`, `dcv`, `hypothesis` o `derived`;
- fuente y revisión por entidad o propiedad crítica;
- tolerancia numérica explícita; no comparar flotantes por igualdad exacta;
- esquema versionado y migraciones, sin cambios silenciosos;
- errores estructurados con `rule_id`, entidad, valor observado, límite y fuente;
- resultados generados en carpeta separada y reproducibles desde datos + versión del motor.

## Validaciones del primer prototipo

El MVP no necesita resolver toda la casa. Debe reproducir la envolvente y bandas de
control y fallar de forma legible cuando se viola una regla.

### Geometría y programa

- envolvente PB 18 × 36 m y P2 posterior nominal 18 × 15 m;
- P2 comienza nominalmente en X=21 m;
- espacios contenidos, sin solapes no autorizados y con área calculada;
- núcleo PB nominal 18 × 4,5 m y suma interna consistente;
- exactamente cuatro suites permanentes en P2;
- dormitorios útiles de hijos con igualdad dentro de tolerancia declarada;
- exactamente tres accesos frontales con anchos de prueba;
- sala en doble altura y cocina/comedor bajo P2;
- zona diferida de Fase 2 contigua y separable.

### Salidas

- planta PB y P2 en SVG con ejes, cotas globales, IDs y leyenda de estatus;
- reporte de cumplimiento en JSON y HTML/Markdown;
- tabla de áreas brutas y netas calculadas;
- manifest con hash de entradas, versión del motor, fecha y archivos emitidos;
- pruebas automatizadas de hard rules y casos deliberadamente inválidos.

SVG debe ser la primera visualización: es preciso, revisable en navegador, fácil de
comparar y no confunde un borrador con un render fotorrealista. PDF/PNG se derivan para
distribución; DXF e IFC se agregan cuando la geometría base pase las pruebas.

## Ruta para estructura sin falsa precisión

### Modelo E0 — esquema, no cálculo de diseño

Representar ejes, luces, alturas, apoyos hipotéticos, sistemas alternativos y caminos de
carga. Salida: diagramas, lista de datos faltantes y conflicto con arquitectura. No asignar
perfiles finales.

### Modelo E1 — comparación paramétrica por ingeniero

Una vez haya predio preliminar, cargas y criterios: comparar pórticos de luz completa,
cerchas, estabilidad lateral y entrepiso. Registrar unidades, signos, liberaciones,
diafragmas, imperfecciones, combinaciones, versión del solver y controles manuales.
Validar cada familia con problemas simples de referencia y revisión independiente.

### Modelo E2 — diseño profesional

Con topografía, geotecnia, norma aplicable confirmada, equipos y arquitectura coordinada:
modelo y memoria firmados, diseño de miembros/conexiones/cimentación, planos y revisión que
corresponda. Un resultado numérico del motor interno nunca se rotula “apto para construir”.

No crear todavía bibliotecas NSR-10 propias: existe riesgo alto de omisiones, versiones
obsoletas y criterios mal interpretados. El motor puede almacenar casos y resultados,
pero la definición y aceptación de cargas/combinaciones debe pertenecer al ingeniero.

## Plan de implementación por prototipos

### P0 — contrato y dibujo de control (1–2 sesiones)

Definir esquema JSON, coordenadas, unidades, estatus y 10–15 reglas; generar dos SVG y un
reporte. Criterio de salida: reproduce exactamente las áreas globales activas y detecta
cinco violaciones sembradas.

### P1 — planta v0.3 manual paramétrica

Modelar espesores preliminares, puertas, mobiliario/equipos de control, áreas netas,
recorridos y secciones básicas. El arquitecto revisa la variante; el motor no “diseña”
autónomamente.

### P2 — DXF y documentación

Crear layers, estilos, unidades, cotas y cuadro de áreas. Abrir el DXF en al menos dos
aplicaciones y comparar medidas contra el reporte canónico.

### P3 — IFC/IDS

Exportar espacios, pisos, muros, aberturas y propiedades mínimas. Validar esquema y un IDS
del proyecto con IfcTester; revisar visualmente en Bonsai y un segundo visor IFC.

### P4 — estructura exploratoria

Solo con participación del ingeniero: modelo de referencia, tests analíticos y comparación
de alternativas. Mantener geometría analítica separada de la geometría física BIM.

### P5 — optimización limitada

Usar OR-Tools para una pregunta acotada —por ejemplo, distribución del P2 dentro de una
envolvente fija— y presentar varias soluciones con métricas, nunca una “ganadora” opaca.

## Criterios de precisión y control de calidad

- Las cotas se calculan de la geometría; no se escriben dos veces.
- Toda exportación se reabre y se mide automáticamente cuando sea posible.
- Cada salida visible incluye versión, estatus y “NO APTO PARA CONSTRUIR” mientras aplique.
- Los golden files visuales detectan desplazamientos; las pruebas numéricas gobiernan.
- Una segunda implementación simple comprueba áreas y dimensiones críticas.
- Las tolerancias de dibujo, fabricación y obra se mantienen separadas.
- Los modelos de arquitectura, análisis y fabricación tienen propósitos y responsables
  distintos aunque compartan identificadores.

## Riesgos antes de adoptar

| Riesgo                                          | Control propuesto                                            |
| ----------------------------------------------- | ------------------------------------------------------------ |
| Construir demasiada plataforma antes de diseñar | limitar P0 a una envolvente, bandas y reglas críticas        |
| IFC complejo/inestable para autoría temprana    | esquema interno pequeño; IFC como exportación validada       |
| Optimización produce plantas absurdas           | variante humana válida y objetivos aprobados antes de CP-SAT |
| Agente cambia una hard rule                     | estatus/fuente obligatorios, validación y revisión por diff  |
| Confundir análisis con diseño                   | rótulos, puertas de fase y aprobación profesional            |
| Dependencias/versiones rompen reproducibilidad  | lockfile, entorno aislado y manifest de generación           |
| Unidades/signos causan errores estructurales    | tipos/unidades explícitos y casos de referencia              |

## Decisiones pendientes antes de programar más allá de P0

1. Aprobar que JSON versionado sea fuente de datos del motor y no el archivo Python.
2. Aprobar sistema de coordenadas y orientación provisional antes del predio.
3. Definir qué geometría de v0.3 se modela primero: PB, P2 o ambas en baja resolución.
4. Nombrar quién aprueba reglas arquitectónicas y quién acepta supuestos estructurales.
5. Confirmar licencias de cualquier herramienta antes de redistribuir el motor; OpenSeesPy
   declara uso gratuito para investigación, educación e interno, pero exige licencia para
   redistribución comercial.

## Fuentes web verificadas

- [IfcOpenShell 0.8.5: documentación y utilidades](https://docs.ifcopenshell.org/)
- [IfcOpenShell: lectura y escritura con Python](https://docs.ifcopenshell.org/autoapi/ifcopenshell/index.html)
- [IfcTester: validación IFC mediante IDS](https://docs.ifcopenshell.org/ifctester.html)
- [buildingSMART: Information Delivery Specification](https://www.buildingsmart.org/standards/bsi-standards/information-delivery-specification-ids/)
- [FreeCAD: fundamentos de scripting](https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/FreeCAD_Scripting_Basics.md)
- [PyNite: alcance del análisis y visualización](https://pynite.readthedocs.io/en/stable/)
- [OpenSeesPy: alcance y condición de licencia](https://openseespydoc.readthedocs.io/en/latest/)
- [Speckle Python SDK](https://docs.speckle.systems/developers/sdks/python/introduction)

Las versiones se vuelven a verificar al crear el entorno. La investigación de software no
modifica por sí sola D-019 ni ninguna hard rule; una adopción se registra como decisión.
