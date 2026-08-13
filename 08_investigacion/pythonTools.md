Sí. Después de revisar documentación oficial, repositorios activos y herramientas AEC/estructurales, **Python nos puede servir muchísimo**. De hecho, para nuestro caso, creo que es mejor construir un pequeño **motor arquitectónico paramétrico propio** que depender de una IA que simplemente “dibuje” una planta.

La idea clave sería esta:

> **La casa existe primero como datos + geometría + reglas en Python.**
> El plano DXF, el modelo IFC, el 3D, las tablas de áreas y eventualmente el modelo estructural serían distintas representaciones generadas desde ese mismo modelo.

## 1. El stack que recomiendo

| Capa                        | Herramienta                  | Para qué la usaríamos                                                                                                                                                                                                                                                          |
| --------------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Geometría arquitectónica 2D | **Shapely**                  | Habitaciones, muros, offsets, intersecciones, áreas, perímetros, comprobar solapes y distancias. Es una librería específicamente orientada a manipulación y análisis geométrico planar. ([Shapely][1])                                                                         |
| Relaciones espaciales       | **NetworkX**                 | Convertir la planta en un grafo: dormitorio → pasillo → baño; cocina → comedor; recorridos, proximidades, conexiones y circulación. ([NetworkX][2])                                                                                                                            |
| Optimización de planta      | **Google OR-Tools / CP-SAT** | Resolver automáticamente restricciones: habitaciones que deben tocarse, dimensiones mínimas, áreas objetivo, no superposición, ubicación por piso, minimizar pasillos, etc. OR-Tools soporta programación de restricciones y optimización entera. ([Google for Developers][3]) |
| Plano CAD 2D                | **ezdxf**                    | Crear automáticamente planos `.dxf` con layers, cotas, líneas, textos, puertas, mobiliario, etc. Actualmente soporta creación, lectura y modificación de DXF y exportación gráfica. ([ezdxf][4])                                                                               |
| BIM / IFC                   | **IfcOpenShell**             | Crear paredes, losas, puertas, ventanas, propiedades y cantidades BIM; leer/escribir IFC y obtener geometría y cantidades. ([IfcOpenShell][5])                                                                                                                                 |
| CAD paramétrico 3D          | **CadQuery**                 | Estructuras metálicas, perfiles, conexiones, muebles, gabinetes, detalles y componentes paramétricos. Genera geometría BREP y formatos como STEP. ([CadQuery Documentation][6])                                                                                                |
| CAD paramétrico alternativo | **build123d**                | Muy interesante para CAD-as-code moderno; también usa OpenCascade y trabaja nativamente con geometría precisa 2D/3D. ([Build123D][7])                                                                                                                                          |
| Framework AEC               | **COMPAS**                   | Puente más avanzado entre Python, Rhino, Grasshopper, Blender, geometría, estructuras, fabricación y BIM. Está concebido específicamente para Architecture, Engineering, Fabrication and Construction. ([Compas][8])                                                           |
| GUI CAD abierta             | **FreeCAD + Python**         | Poder abrir nuestra geometría, editarla visualmente y automatizar objetos mediante Python. FreeCAD permite scripts externos, macros y creación/modificación de objetos CAD desde Python. ([FreeCAD Wiki][9])                                                                   |
| Estructuras, nivel inicial  | **PyNite**                   | Análisis elástico 3D de pórticos, miembros, placas, combinaciones de carga, estabilidad y P-Delta. Muy cómodo para nuestros primeros modelos estructurales. ([Pynite][10])                                                                                                     |
| Estructuras avanzadas       | **OpenSeesPy**               | Análisis estructural y sísmico mucho más avanzado, análisis no lineal, sensibilidad, confiabilidad, etc. ([OpenSeesPy][11])                                                                                                                                                    |
| Perfiles estructurales      | **sectionproperties**        | Calcular área, centroides, inercias, torsión, warping y esfuerzos de secciones arbitrarias mediante elementos finitos. ([sectionproperties][12])                                                                                                                               |
| Mallado FEM                 | **Gmsh**                     | Generar mallas 2D/3D para elementos finitos mediante API Python; incluye motor CAD, mallado y postprocesamiento. ([Gmsh][13])                                                                                                                                                  |
| Luz/clima/energía           | **Ladybug + Honeybee**       | Habitaciones 3D, aberturas, radiación solar, daylighting y posteriormente simulaciones energéticas. Honeybee representa explícitamente cada `Room` como volumen cerrado. ([Ladybug Tools][14])                                                                                 |

## 2. El núcleo debería ser Shapely, no AutoCAD

Esto me parece la decisión técnica más importante.

Una habitación podría existir internamente simplemente como:

```python
Room(
    name="Master Bedroom",
    x=10.0,
    y=22.0,
    width=5.2,
    depth=6.0,
    floor=2
)
```

Y Python genera su polígono:

```python
from shapely.geometry import box

room = box(10.0, 22.0, 15.2, 28.0)

print(room.area)
# 31.2 m²

print(room.length)
# perímetro
```

Shapely puede hacer automáticamente operaciones como áreas, buffers, uniones, intersecciones, contención y relaciones espaciales. ([Shapely][1])

Eso significa que podríamos preguntarle al programa:

```python
assert bedroom.area >= 18
assert bathroom.area >= 5
assert not bedroom.overlaps(bathroom)
assert corridor.width >= 1.20
assert kitchen.distance(pantry) <= 1.0
```

Ahí comienza a volverse muy potente.

---

# 3. Crearíamos un verdadero **Dream House Engine**

Yo lo estructuraría aproximadamente así:

```text
dreamhouse/
│
├── model/
│   ├── building.py
│   ├── floor.py
│   ├── room.py
│   ├── wall.py
│   ├── door.py
│   ├── window.py
│   ├── column.py
│   └── beam.py
│
├── geometry/
│   ├── polygons.py
│   ├── offsets.py
│   ├── intersections.py
│   └── circulation.py
│
├── rules/
│   ├── hard_rules.py
│   ├── dimensions.py
│   ├── adjacencies.py
│   └── code_checks.py
│
├── optimization/
│   ├── floorplanner.py
│   ├── adjacency_solver.py
│   └── scoring.py
│
├── structure/
│   ├── grid.py
│   ├── loads.py
│   ├── steel.py
│   ├── pynite_model.py
│   └── opensees_model.py
│
├── exporters/
│   ├── dxf.py
│   ├── ifc.py
│   ├── svg.py
│   └── json.py
│
└── visualization/
    ├── floorplan.py
    ├── structure.py
    └── model3d.py
```

Lo importante es que **el DXF no sea el proyecto**.

El proyecto sería `building.py`.

---

# 4. Cada espacio tendría inteligencia

Por ejemplo:

```python
Room(
    id="bed_master",
    type="bedroom",
    floor=2,

    target_area=30,
    min_area=26,
    max_area=34,

    min_width=4.5,
    min_depth=5.0,

    needs_exterior_wall=True,
    needs_daylight=True,

    adjacent_to=[
        "master_bath",
        "walk_in_closet"
    ],

    avoid_adjacent_to=[
        "workshop",
        "mechanical_room"
    ]
)
```

Después podemos modificar el ancho total del edificio y pedirle al sistema:

> Encuentra otra distribución que siga cumpliendo las reglas.

Ahí entra OR-Tools.

OR-Tools está específicamente diseñado para problemas donde existen **variables, restricciones y una función objetivo**; además ofrece CP-SAT, programación lineal, entera, asignación, scheduling, packing, routing y otros solucionadores. ([Google for Developers][3])

Para arquitectura podemos definir:

```text
minimizar:
    área de circulación
    + distancia cocina-comedor
    + distancia dormitorio-baño
    + desperdicio geométrico

maximizar:
    área útil
    + fachada disponible
    + iluminación
    + privacidad
```

Sujetos a:

```text
habitación dentro del edificio
habitaciones no se superponen
escalera conecta pisos
puertas tienen espacio libre
columnas coinciden verticalmente
baños agrupados
instalaciones alineadas
dimensiones mínimas
hard rules obligatorias
```

Eso ya es **generative design**, pero determinista y auditable.

---

# 5. NetworkX nos permitiría evaluar arquitectura, no solamente geometría

Podemos representar:

```text
GARAGE
   |
SOCIAL
 /    \
KITCHEN  STAIRS
   |       |
PANTRY   FLOOR 2
```

Cada habitación es un nodo y cada conexión una arista.

NetworkX trabaja precisamente con nodos, aristas y algoritmos de grafos. ([NetworkX][15])

Entonces podemos calcular programáticamente:

- cuántas puertas hay entre dos espacios;
- longitud aproximada de circulación;
- dormitorios demasiado conectados con zona pública;
- espacios sin salida;
- recorridos;
- accesibilidad;
- redundancia de circulación.

Y podríamos definir algo como:

```python
distance("master_bedroom", "kitchen") == 4
distance("garage", "kitchen") <= 2
```

No como metros necesariamente, sino como **saltos espaciales**.

Arquitectónicamente eso es muy útil.

---

# 6. Después Python dibuja el plano

Una vez resuelta la geometría, **ezdxf** convertiría el modelo en un plano CAD real.

El repositorio está activo y está diseñado expresamente para crear y manipular documentos DXF desde Python. ([GitHub][16])

Podríamos tener layers:

```text
A-WALL
A-DOOR
A-WIND
A-FURN
A-DIMS
A-TEXT

S-COLS
S-BEAM
S-GRID
```

Y generar:

```text
dream_house_v001.dxf
dream_house_v002.dxf
dream_house_v003.dxf
```

Automáticamente.

Además, ezdxf dispone de funcionalidad para representar el modelspace y exportarlo a SVG/PDF/PNG. ([GitHub][17])

---

# 7. Y simultáneamente generar IFC

Aquí **IfcOpenShell** me parece una de las herramientas más importantes de toda la investigación.

IFC no guarda simplemente líneas. Guarda objetos:

```text
IfcWall
IfcSlab
IfcDoor
IfcWindow
IfcBeam
IfcColumn
IfcSpace
IfcBuildingStorey
```

IfcOpenShell expone estas entidades desde Python y tiene tanto API geométrica como utilidades para obtener cantidades y formas. ([IfcOpenShell][5])

Por lo tanto podríamos transformar:

```python
Room(...)
```

en:

```text
IfcSpace
```

y:

```python
Wall(...)
```

en:

```text
IfcWall
```

Después abrir el IFC en software BIM compatible.

El ecosistema de IfcOpenShell además incluye **Bonsai**, un entorno gráfico IFC dentro de Blender. ([GitHub][18])

Eso nos da algo muy interesante:

```text
                 PYTHON MODEL
                      │
        ┌─────────────┼─────────────┐
        │             │             │
      SHAPELY        DXF           IFC
        │             │             │
     cálculo        AutoCAD      BIM/Bonsai
        │
     STRUCTURE
```

Un solo modelo.

---

# 8. CadQuery/build123d los reservaría para los detalles

No utilizaría CadQuery como motor principal de la planta.

Sí lo usaría muchísimo para:

```text
columnas
perfiles I
perfiles tubulares
cerchas
conexiones
placas base
gabinetes
mesones
racks
mobiliario
escaleras
detalles metálicos
```

CadQuery está específicamente diseñado para modelos CAD paramétricos 3D programados en Python y puede exportar STEP, DXF y otros formatos. ([CadQuery Documentation][6])

**build123d** es otra opción muy interesante y bastante Python-native; también utiliza el kernel OpenCascade. ([Build123D][7])

Para este proyecto probablemente escogería **CadQuery primero** por madurez/ecosistema, aunque mantendría build123d bajo observación.

---

# 9. COMPAS es el “nivel universitario/profesional” de esta idea

Encontré algo particularmente alineado con lo que queremos.

ETH Zürich y la comunidad COMPAS han desarrollado un ecosistema Python específicamente orientado a:

**Architecture + Engineering + Fabrication + Construction.**

El framework incluye geometría, estructuras de datos y visualización, y su ecosistema contempla extensiones para elementos finitos, form finding, IFC, Gmsh, Rhino, Grasshopper y Blender. ([Compas][8])

Repositorio:

**`compas-dev/compas`** ([GitHub][19])

Yo estudiaría bastante su arquitectura de software aunque finalmente construyamos nuestro propio motor.

---

# 10. Cálculo estructural: aquí Python también puede entrar

Hay dos niveles.

### Nivel A — dimensionamiento conceptual

Para nuestras iteraciones arquitectónicas usaría **PyNite**.

Puede trabajar con modelos estructurales 3D, miembros, placas, mallas, combinaciones de carga, análisis modal, estabilidad y efectos P-Δ/P-δ. ([Pynite][10])

Así podemos detectar temprano cosas como:

```text
vano demasiado grande
columna mal posicionada
viga exageradamente profunda
deriva elevada
pórtico demasiado flexible
```

Sin esperar a que el diseño arquitectónico esté terminado.

### Nivel B — análisis estructural avanzado

Para análisis sísmicos o no lineales pasaría a **OpenSeesPy**.

OpenSeesPy expone desde Python el motor OpenSees y contiene comandos de modelado, análisis, sensibilidad, confiabilidad, procesamiento y paralelización. ([OpenSeesPy][11])

Hay una consideración importante: su documentación indica que es libre para investigación, educación y uso interno, pero **la redistribución comercial de una aplicación que incorpore OpenSeesPy exige revisar su licencia comercial**. Para nosotros como herramienta interna no sería el mismo escenario que venderla como SaaS. ([GitHub][20])

---

# 11. Para perfiles de acero: sectionproperties

Esta me gustó particularmente para nuestra herramienta.

**sectionproperties** permite crear una sección arbitraria y obtener mediante FEM:

```text
A
Ix
Iy
Ixy
J
centroide
warping
tensiones
```

Está específicamente diseñada para análisis de secciones transversales estructurales. ([sectionproperties][12])

Entonces podríamos definir una biblioteca:

```python
SteelColumn(
    section="HEB300",
    length=6.0,
    steel="..."
)
```

y hacer comprobaciones preliminares sistemáticas.

---

# 12. Gmsh entra cuando necesitemos FEM serio

Gmsh dispone de API oficial de Python y puede crear geometría y mallas 1D/2D/3D. La versión estable publicada en marzo de 2026 es 4.15.2. ([Gmsh][13])

Nos permitiría pasar de:

```text
geometría estructural
```

a:

```text
nodos
elementos
malla
```

para alimentar distintos solvers.

No lo necesitamos todavía, pero es una ruta perfectamente viable.

---

# 13. Incluso podemos introducir iluminación y energía

Ladybug/Honeybee tiene librerías Python de geometría 2D y 3D y objetos específicamente destinados a representar habitaciones arquitectónicas. ([Ladybug Tools][14])

Honeybee permite representar:

```text
Room
Face
Aperture
Door
Shade
```

y su ecosistema integra análisis energético y daylighting. Por ejemplo, Honeybee Energy incluye controles de iluminación basados en sensores y niveles de iluminancia. ([Ladybug Tools][21])

Eso significa que, posteriormente, cada variante podría recibir puntuaciones como:

```text
Plan A
área útil             91%
circulación            6%
fachada vidriada       24%
iluminación natural    87/100
estructura             90/100

Plan B
área útil             88%
circulación            9%
iluminación natural    95/100
estructura             83/100
```

Eso sí sería muy potente.

---

# 14. Lo que NO haría

No empezaría intentando construir un clon de Revit.

Tampoco empezaría con redes neuronales para que una IA dibuje plantas aleatoriamente.

Primero construiría:

**geometría determinista + hard rules + métricas.**

Después:

**optimización.**

Y solamente posteriormente utilizaría IA para proponer objetivos o modificar parámetros.

Es muchísimo más controlable.

---

# 15. La primera versión que construiría

Nuestro **Dream House Engine 0.1** solo tendría cinco capacidades:

**1. Modelo paramétrico**

```python
Building
Floor
Room
Wall
Opening
Column
```

**2. Geometría Shapely**

Calcula:

```text
áreas
perímetros
solapes
distancias
adyacencias
```

**3. Motor de reglas**

Ejemplo:

```python
MASTER.area >= 25
GARAGE.cars == 1
STAIRS.width >= x
ROOMS.with_exterior_window == True
```

**4. Dibujo automático**

```text
Matplotlib/SVG → revisión rápida
DXF → CAD
```

**5. Reporte**

```text
Área construida
Área útil
Área por espacio
Área de circulación
Área técnica
Área de vidrio
Longitudes de muro
Número de puertas
Número de ventanas
```

Eso ya nos permitiría generar plantas muchísimo más rigurosas que dibujándolas manualmente una por una.

---

# 16. Segunda versión

Luego agregaría:

```text
NetworkX
    ↓
relaciones espaciales

OR-Tools
    ↓
optimización automática

IfcOpenShell
    ↓
BIM

CadQuery
    ↓
estructura/mobiliario 3D

PyNite
    ↓
estructura conceptual
```

Y finalmente:

```text
OpenSeesPy
Ladybug/Honeybee
Gmsh
COMPAS
```

---

## 17. Un punto crítico sobre el cálculo estructural en Colombia

Python puede hacer perfectamente el análisis matemático, pero **no debemos confundir “solver” con “diseño estructural aprobado”**.

En fuentes oficiales encontré que la NSR-10 fue adoptada mediante el Decreto 926 de 2010 y ha tenido modificaciones posteriores. En particular, el Decreto 1401 de agosto de 2023 enumera modificaciones previas de 2010, 2011, 2012, 2017, 2019 y 2021; posteriormente el Decreto 1580 de 2023 corrigió un anexo del Decreto 1401. ([Función Pública][22])

Por tanto, yo diseñaría nuestra librería estructural así:

```text
GEOMETRÍA
      ↓
CARGAS
      ↓
MODELO FEM
      ↓
RESULTADOS
      ↓
VERIFICACIONES NORMATIVAS
      ↓
REVISIÓN INGENIERO ESTRUCTURAL
```

Nunca introduciría en el código una versión congelada de la norma y asumiría que seguirá vigente indefinidamente.

---

# Mi selección final

Si solo pudiera escoger **7 herramientas**, serían:

1. **Shapely** — corazón geométrico. ([Shapely][1])
2. **ezdxf** — planos CAD. ([ezdxf][4])
3. **OR-Tools** — generative floor planning. ([Google for Developers][3])
4. **NetworkX** — relaciones/circulación. ([NetworkX][2])
5. **IfcOpenShell** — BIM. ([GitHub][18])
6. **CadQuery** — 3D paramétrico. ([CadQuery Documentation][6])
7. **PyNite + posteriormente OpenSeesPy** — estructura. ([Pynite][10])

Y estudiaría **COMPAS** como referencia de cómo profesionales e investigadores AEC organizan este tipo de ecosistemas Python. ([Compas][23])

**Creo que este camino vale mucho la pena para el proyecto.** El siguiente paso que yo haría sería construir el primer `dreamhouse` en Python: el modelo de datos, Shapely, las hard rules y un render 2D con cotas. A partir de ahí podríamos hacer que cada cambio en dimensiones regenere toda la planta y nos diga inmediatamente qué reglas cumple, cuáles rompe y cuántos metros cuadrados resultan.

[1]: https://shapely.readthedocs.io/en/stable/?utm_source=chatgpt.com 'Shapely — Shapely 2.1.2 documentation'
[2]: https://networkx.org/documentation/stable/reference/introduction.html?utm_source=chatgpt.com 'Introduction — NetworkX 3.6.1 documentation'
[3]: https://developers.google.com/optimization/introduction/python?utm_source=chatgpt.com 'Get Started with OR-Tools for Python | Google for Developers'
[4]: https://ezdxf.readthedocs.io/?utm_source=chatgpt.com 'Quick-Info — ezdxf 1.4.4 documentation'
[5]: https://docs.ifcopenshell.org/autoapi/ifcopenshell/geom/index.html?utm_source=chatgpt.com 'ifcopenshell.geom - IfcOpenShell 0.8.5 documentation'
[6]: https://cadquery.readthedocs.io/en/latest/?utm_source=chatgpt.com 'CadQuery Documentation — CadQuery Documentation'
[7]: https://build123d.readthedocs.io/?utm_source=chatgpt.com 'About — build123d 0.11.2.dev201+g698198005 documentation'
[8]: https://compas.dev/compas/latest/index.html?utm_source=chatgpt.com 'COMPAS Documentation — COMPAS'
[9]: https://wiki.freecad.org/Python_scripting_tutorial?utm_source=chatgpt.com 'Python scripting tutorial - FreeCAD Documentation'
[10]: https://pynite.readthedocs.io/?utm_source=chatgpt.com 'Welcome to Pynite’s Documentation — Pynite 3.0.0 documentation'
[11]: https://openseespydoc.readthedocs.io/?utm_source=chatgpt.com 'The OpenSeesPy Library — OpenSeesPy 3.5.1.3 documentation'
[12]: https://sectionproperties.readthedocs.io/en/latest/?utm_source=chatgpt.com 'sectionproperties documentation'
[13]: https://gmsh.info/?utm_source=chatgpt.com 'Gmsh: a three-dimensional finite element mesh generator with built-in pre- and post-processing facilities'
[14]: https://www.ladybug.tools/ladybug-geometry/docs/?utm_source=chatgpt.com 'Welcome to Ladybug Geometry’s documentation! — ladybug geometry documentation'
[15]: https://networkx.org/documentation/stable/reference/classes/graph.html?utm_source=chatgpt.com 'Graph—Undirected graphs with self loops — NetworkX 3.6.1 documentation'
[16]: https://github.com/mozman/ezdxf/tree/master?utm_source=chatgpt.com 'GitHub - mozman/ezdxf: Python interface to DXF · GitHub'
[17]: https://github.com/mozman/ezdxf/blob/master/README.md?utm_source=chatgpt.com 'ezdxf/README.md at master · mozman/ezdxf · GitHub'
[18]: https://github.com/IfcOpenShell/IfcOpenShell/blob/v0.8.0/README.md?utm_source=chatgpt.com 'IfcOpenShell/README.md at v0.8.0 · IfcOpenShell/IfcOpenShell · GitHub'
[19]: https://github.com/compas-dev/compas/tree/main/src/compas?utm_source=chatgpt.com 'compas/src/compas at main · compas-dev/compas · GitHub'
[20]: https://github.com/zhuminjie/OpenSeesPy/blob/master/README.md?utm_source=chatgpt.com 'OpenSeesPy/README.md at openseespy · zhuminjie/OpenSeesPy · GitHub'
[21]: https://www.ladybug.tools/honeybee-energy/docs/honeybee_energy.load.daylight.html?utm_source=chatgpt.com 'honeybee_energy.load.daylight module — honeybee energy documentation'
[22]: https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=39255&utm_source=chatgpt.com 'Decreto 926 de 2010 - Gestor Normativo - Función Pública'
[23]: https://compas.dev/compas/latest/userguide/introduction.html?utm_source=chatgpt.com 'Introduction — COMPAS'
