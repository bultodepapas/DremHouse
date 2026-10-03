"""English labels for legacy Spanish text in current coordination SVGs.

Translations are deliberately applied to SVG character data only.  The lexical
rewrite keeps the original markup and attributes byte-for-byte, so IDs, metadata,
dimensions, and geometry are not part of this translation layer.
"""

from __future__ import annotations

import html
import re

_MARKUP_OR_TEXT = re.compile(
    r"<!--.*?-->|<!\[CDATA\[.*?\]\]>|<\?.*?\?>|<![^>]*>|<[^>]+>|[^<]+",
    re.DOTALL,
)
_OPEN_TAG = re.compile(r"<([A-Za-z_][\w:.-]*)\b[^>]*>", re.DOTALL)
_CLOSE_TAG = re.compile(r"</([A-Za-z_][\w:.-]*)\s*>")
_VISIBLE_TEXT_TAGS = {"text", "tspan", "title", "desc"}

# These are intentional phrase translations for current E0 and PB coordination
# consumers.  Numeric values, units, identifiers, and revision tokens are kept as
# written in the source drawing.
_TRANSLATIONS = {
    "ALTERNATIVAS ESTRUCTURALES + CORTE B-B (E0)": "STRUCTURAL ALTERNATIVES + SECTION B-B (E0)",
    "PLANTA BAJA DETALLADA · ANTEPROYECTO": "DETAILED GROUND FLOOR · CONCEPT DESIGN",
    "espesores y equipamiento de estudio": "study thicknesses and equipment",
    "cotas en metros": "dimensions in metres",
    "DETALLE AMPLIADO · NÚCLEO POSTERIOR PB": "ENLARGED DETAIL · REAR GROUND-FLOOR CORE",
    "FACHADA FRONTAL DETALLADA · TRES ACCESOS": "DETAILED FRONT ELEVATION · THREE ENTRANCES",
    "PORTÓN CAR PROJECT": "PROJECT-CAR DOOR",
    "PUERTA PRINCIPAL": "MAIN ENTRANCE",
    "PORTÓN TALLER RC / AVIONES": "RC / AIRCRAFT WORKSHOP DOOR",
    "PLATAFORMA CONTINUA DE CONCRETO · canal lineal / pendiente alejándose de portones": "CONTINUOUS CONCRETE APRON · linear channel / fall away from doors",
    "LATERAL A": "SIDE A",
    "LATERAL B": "SIDE B",
    "ELEVACIÓN INTERIOR · GRAN MURO POSTERIOR": "INTERIOR ELEVATION · REAR GREAT WALL",
    "MURO INTERIOR AL FONDO DE LA NAVE — NO ES LA FACHADA FRONTAL · vista hacia pantry, bodega, escalera, baño y homelab": "INTERIOR WALL AT THE REAR OF THE HALL — NOT THE FRONT ELEVATION · view toward pantry, storage, stair, bathroom, and homelab",
    "ZÓCALO TÉCNICO CONTINUO / RETORNO DE SOMBRA · registrable por módulos": "CONTINUOUS TECHNICAL BASE / SHADOW REVEAL · accessible by module",
    "LISTÓN DE MADERA SOBRE SUBESTRUCTURA + ABSORCIÓN NEGRA · patrón continuo a coordinar con puertas": "WOOD SLATS OVER SUBFRAME + BLACK ACOUSTIC ABSORBER · continuous pattern to coordinate with doors",
    "INTENCIÓN": "DESIGN INTENT",
    "El wall debe leerse como un solo testero cálido y acústico. Las juntas de puertas continúan el ritmo; solo la escalera se anuncia mediante portal profundo y span.": "The wall should read as a single warm, acoustically absorptive end wall. Door joints continue the rhythm; only the stair is signalled by a deep portal and clear span.",
    "Acabado, reacción al fuego, absorción, acceso técnico, herrajes y estabilidad requieren muestra 1:1 y especificación profesional.": "Finish, fire performance, acoustic absorption, technical access, hardware, and stability require a 1:1 sample and professional specification.",
    "Planta de coordinación 1:50 conceptual · áreas netas provisionales con cerramientos de estudio": "Concept coordination plan 1:50 · provisional net areas with study enclosures",
    "ALTERNATIVAS ESTRUCTURALES": "STRUCTURAL ALTERNATIVES",
    "ALTERNATIVAS": "ALTERNATIVES",
    "Camino gravitacional": "Gravity load path",
    "activo": "active",
    "perfiles/subtotales no adoptados": "member sizes/subtotals not adopted",
    "sin diseño lateral": "no lateral design",
    "correas c/1,5 m (secundaria)": "secondary purlins at 1,5 m centres",
    "correas": "purlins",
    "ZONA DE ESTUDIO": "STUDY ZONE",
    "ARRIOSTRAMIENTO NO DISEÑADO": "BRACING NOT DESIGNED",
    "CONFLICTO VANOS/CLARABOYAS": "OPENING/ROOFLIGHT CONFLICT",
    "ALTERNATIVA CERCHA": "TRUSS ALTERNATIVE",
    "LÍNEAS": "LINES",
    "SIN ANÁLISIS LATERAL": "NO LATERAL ANALYSIS",
    "MÍNIMO GRAVITACIONAL, NO DISEÑO": "GRAVITY MINIMUM, NOT A DESIGN",
    "PARED HÍBRIDA": "HYBRID WALL",
    "OCULTAS": "HIDDEN",
    "ocultas": "concealed",
    "DE PRUEBA": "TRIAL",
    "CERCHA DE BORDE": "EDGE TRUSS",
    "luz": "span",
    "CONTINUAS": "CONTINUOUS",
    "VOLADIZO": "CANTILEVER",
    "franja": "strip",
    "NO ANALIZADOS": "NOT ANALYSED",
    "CORTE TRANSVERSAL ESTRUCTURAL": "STRUCTURAL TRANSVERSE SECTION",
    "alternativas de cribado": "screening alternatives",
    "NO ADOPTADAS": "NOT ADOPTED",
    "losa prueba": "trial slab",
    "cielo objetivo": "target ceiling",
    "apoyo gravitacional activo": "active gravity support",
    "uniones y cimentación sin diseño": "connections and foundation not designed",
    "LADO BAJO": "LOW SIDE",
    "LADO ALTO": "HIGH SIDE",
    "mínimo gravitacional": "gravity minimum",
    "estabilidad/lateral NO verificados": "stability/lateral action NOT verified",
    "VISTA LATERAL A": "SIDE ELEVATION A",
    "Trazos para conflicto/coord.": "Traces for clash/coordination",
    "no son perfiles ni arriostramientos de diseño": "are not designed member sizes or bracing",
    "ELEVACIÓN ESTRUCTURAL": "STRUCTURAL ELEVATION",
    "muro Y=0": "wall Y=0",
    "Largo": "Length",
    "alero bajo": "low eave",
    "toda el agua descarga aquí": "all roof water discharges here",
    "solo estructura": "structural frame only",
    "CRIBADO GRAVITACIONAL": "GRAVITY SCREENING",
    "TRAZO NO DISEÑADO": "UNSIZED TRACE",
    "CONFLICTO CON VANO": "CLASH WITH OPENING",
    "CONFLICTO CON P2": "CLASH WITH P2",
    "DE CRIBADO": "SCREENING",
    "DECK NO ANALIZADO": "DECK NOT ANALYSED",
    "FRECUENCIA": "FREQUENCY",
    "VIGAS": "BEAMS",
    "nivel": "level",
    "BORDE": "EDGE",
    "GRAVEDAD SÍ": "GRAVITY SUPPORT ONLY",
    "LATERAL X NO": "NO X-DIRECTIONAL LATERAL ACTION",
    "VENTANAL TÉCNICO": "TECHNICAL GLAZING",
    "VENTANAL TALLER RC / AVIONES": "RC / AIRCRAFT WORKSHOP GLAZING",
    "VENTANAL CAR PROJECT": "PROJECT-CAR GLAZING",
    "CLARABOYA": "ROOFLIGHT",
    "vanos M60": "M60 bays",
    "SIN LATERAL/DECK/CONEXIONES": "NO LATERAL/DECK/CONNECTIONS",
    "DICTAMEN DE AUDITORÍA": "AUDIT FINDING",
    "modelo E0 · en vivo": "live E0 model",
    "Modelo E0": "E0 model",
    "en vivo": "live",
    "cribado geométrico y subtotales inferiores": "geometric screening and lower-bound subtotals",
    "no produce cantidades de diseño": "does not produce design quantities",
    "CERCHA M60": "M60 TRUSS",
    "D-043 GRAVEDAD: P2 IPE400 + IPE400 · SIN LATERAL/DECK/CONEXIONES": "D-043 GRAVITY LOAD PATH: P2 IPE400 + IPE400 · NO LATERAL/DECK/CONNECTIONS",
    "de subtotal": "subtotal",
    "NO tiene análisis lateral, estabilidad de barras ni conexiones": "has NO lateral, member-stability, or connection analysis",
    "GRAN-MURO": "GREAT WALL",
    "• Modelo E0 v0.3 en vivo: cribado geométrico y subtotales inferiores; no produce cantidades de diseño.": "• E0 model v0.3 live: geometric screening and lower-bound subtotals; it does not produce design quantities.",
    "• CERCHA M60: 16.7 t de subtotal; NO tiene análisis lateral, estabilidad de barras ni conexiones.": "• M60 TRUSS: 16.7 t subtotal; it has NO lateral, member-stability, or connection analysis.",
    "• GRAN-MURO D-043/D-045: vigas continuas con voladizo; HSS150x150x8 ocultas + IPE400 son pruebas de cabida, no perfiles seleccionados.": "• GREAT WALL D-043/D-045: continuous beams with cantilever; HSS150x150x8 concealed + IPE400 are fit tests, not selected member sizes.",
    "• STAGGERED/DECK: alternativas no adoptadas; panel compuesto, vibración, diafragma y fuego no analizados.": "• STAGGERED/DECK: alternatives not adopted; composite slab, vibration, diaphragm, and fire have not been analysed.",
    "• D-043 FIJA EL CAMINO GRAVITACIONAL, NO EL TONELAJE. NO APTO PARA PRESUPUESTAR, FABRICAR O CONSTRUIR.": "• D-043 FIXES THE GRAVITY LOAD PATH, NOT THE STEEL TONNAGE. NOT FOR COST ESTIMATING, FABRICATION, OR CONSTRUCTION.",
    "vigas continuas con voladizo": "continuous beams with cantilever",
    "pruebas de cabida": "fit tests",
    "no perfiles seleccionados": "not selected member sizes",
    "alternativas no adoptadas": "unadopted alternatives",
    "panel compuesto, vibración, diafragma y fuego no analizados": "composite slab, vibration, diaphragm, and fire not analysed",
    "FIJA EL CAMINO GRAVITACIONAL, NO EL TONELAJE": "FIXES THE GRAVITY LOAD PATH, NOT THE STEEL TONNAGE",
    "NO APTO PARA PRESUPUESTAR, FABRICAR O CONSTRUIR": "NOT FOR COST ESTIMATING, FABRICATION, OR CONSTRUCTION",
    "BASTIDOR OCULTO": "CONCEALED FRAME",
    "Elevación de coordinación detrás del listonado": "Coordination elevation behind the slatted finish",
    "camino gravitacional activo": "active gravity load path",
    "dimensionamiento pendiente": "sizing pending",
    "REACCIONES DE VIGAS": "BEAM REACTIONS",
    "C/U EN CRIBADO": "EACH IN SCREENING",
    "APOYO LIMPIO": "CLEAN SUPPORT",
    "BODEGA": "STORAGE",
    "Bodega": "Storage",
    "ESCALERA PROTEGIDA": "PROTECTED STAIR",
    "Escalera protegida": "Protected stair",
    "BAÑO PB": "GROUND-FLOOR BATHROOM",
    "Baño PB": "Ground-floor bathroom",
    "HOMELAB / TÉCNICO": "HOMELAB / TECHNICAL",
    "Homelab / técnico": "Homelab / technical",
    "PANTRY / APOYO LIMPIO": "PANTRY / CLEAN SUPPORT",
    "Pantry / apoyo limpio": "Pantry / clean support",
    "CIELO": "CEILING",
    "ZONA ESTRUCTURAL HASTA": "STRUCTURAL ZONE TO",
    "TRANSFERENCIA": "TRANSFER",
    "columnas en límites": "columns at limits",
    "LECTURA OBLIGATORIA": "REQUIRED READING",
    "adopta gravedad": "adopts gravity support",
    "modela voladizo solo en E0": "models cantilever in E0 only",
    "solo demuestran cabida": "only demonstrate fit",
    "Sin pandeo, uniones, anclajes, fuego, cimentación ni función lateral. Las puertas y el portal de escalera permanecen libres.": "No buckling, connection, anchorage, fire, foundation, or lateral-action design is included. Doors and stair portal remain clear.",
    "muro": "wall",
    "y IPE400": "and IPE400",
    "son pruebas de cabida": "are fit tests",
    "PLANTA BAJA DETALLADA": "DETAILED GROUND FLOOR",
    "ANTEPROYECTO": "CONCEPT DESIGN",
    "áreas netas provisionales": "provisional net areas",
    "netos provisionales": "provisional net",
    "ESCRITORIO": "WORKSTATION",
    "TRABAJO 1": "WORKSTATION 1",
    "TRABAJO 2": "WORKSTATION 2",
    "BANCO AUTOMOTRIZ": "PROJECT-CAR WORKBENCH",
    "extracción en fuente": "source-capture extraction",
    "potencia dedicada": "dedicated power",
    "BANCO RC / ELECTRÓNICA": "RC / ELECTRONICS WORKBENCH",
    "FRÍO": "COLD STORAGE",
    "frío": "cold storage",
    "LIMPIEZA": "CLEANING",
    "limpieza": "cleaning",
    "contrahuellas aprox.": "risers approx.",
    "UPS / tableros": "UPS / distribution boards",
    "UPS / TAB": "UPS / PNL",
    "CAPAS DE ESTUDIO": "STUDY LAYERS",
    "Gran muro": "Great Wall",
    "total conceptual": "conceptual total",
    "subestructura": "subframe",
    "absorbente": "absorber",
    "acabado listonado registrable": "accessible slatted finish",
    "Particiones estándar": "Standard partitions",
    "con desempeño acústico por definir": "with acoustic performance to be selected",
    "cerramientos de": "enclosures of",
    "descarga posterior": "rear discharge",
    "resistencia al fuego pendiente": "fire rating pending",
    "Envolvente posterior": "Rear envelope",
    "panel aislado": "insulated panel",
    "puentes térmicos y reacción al fuego pendientes": "thermal bridges and fire reaction pending",
    "Profundidad libre resultante del núcleo": "Resulting core clear depth",
    "antes de trasdosados/equipos": "before linings/equipment",
    "Gran muro: 0,20 m total conceptual; subestructura, absorbente y acabado listonado registrable.": "Great Wall: 0,20 m conceptual total; subframe, absorber, and accessible slatted finish.",
    "Particiones estándar: 0,15 m con desempeño acústico por definir.": "Standard partitions: 0,15 m; acoustic performance remains to be selected.",
    "Escalera: cerramientos de 0,20 m y descarga posterior; resistencia al fuego pendiente.": "Stair: 0,20 m enclosures and rear discharge; fire rating pending.",
    "Envolvente posterior: 0,18 m conceptual de panel aislado; puentes térmicos y reacción al fuego pendientes.": "Rear envelope: 0,18 m conceptual insulated panel; thermal bridges and fire reaction pending.",
    "Profundidad libre resultante del núcleo: ≈4,12 m antes de trasdosados/equipos.": "Resulting core clear depth: ≈4,12 m before linings/equipment.",
    "No mezclar drenajes ni agua sobre rack/UPS; coordinar bandejas, detección, ventilación y acceso posterior.": "Do not route drains or water above rack/UPS; coordinate trays, detection, ventilation, and rear access.",
    "Bodega y homelab quedan separados por escalera y baño; pantry queda contiguo a cocina.": "Storage and homelab remain separated by the stair and bathroom; the pantry remains adjacent to the kitchen.",
    "Todas las áreas netas son aproximadas y se recalculan después de estructura y especificaciones.": "All net areas are approximate and must be recalculated after structural design and specifications.",
    "COORDINACIONES BLOQUEANTES": "BLOCKING COORDINATION",
    "huella/contrahuella/gálibo y puertas de escalera": "stair tread/riser/headroom and door clearances",
    "extracción y aire de reposición del baño/homelab": "extract and make-up air for the bathroom/homelab",
    "rutas hidráulicas y sanitarias hacia P2": "water and sanitary routes to P2",
    "protección contra incendio y segunda salida": "fire protection and second exit",
    "equipos reales, registros y radios de mantenimiento": "actual equipment, access panels, and maintenance clearances",
}

_TRANSLATIONS_BY_LENGTH = sorted(_TRANSLATIONS.items(), key=lambda pair: len(pair[0]), reverse=True)
_TRANSLATION_PATTERNS = []
for source, target in _TRANSLATIONS_BY_LENGTH:
    left = r"(?<!\w)" if source[0].isalnum() or source[0] == "_" else ""
    right = r"(?!\w)" if source[-1].isalnum() or source[-1] == "_" else ""
    _TRANSLATION_PATTERNS.append((re.compile(left + re.escape(source) + right), target))


def _translate_run(value: str) -> str:
    decoded = html.unescape(value)
    translated = decoded
    for pattern, target in _TRANSLATION_PATTERNS:
        translated = pattern.sub(target, translated)
    return html.escape(translated, quote=False) if translated != decoded else value


def translate_current_drawing_text(svg: str) -> str:
    """Translate mapped Spanish phrases within SVG text-bearing elements only.

    The function does not parse and re-serialize the SVG: tags, attributes, and
    all text that has no mapped phrase are returned exactly as supplied.
    """

    output: list[str] = []
    element_stack: list[str] = []
    for match in _MARKUP_OR_TEXT.finditer(svg):
        token = match.group()
        if not token.startswith("<"):
            output.append(
                _translate_run(token)
                if any(tag in _VISIBLE_TEXT_TAGS for tag in element_stack)
                else token
            )
            continue

        output.append(token)
        if token.startswith(("<!--", "<![", "<?", "<!")):
            continue

        close = _CLOSE_TAG.fullmatch(token)
        if close:
            name = close.group(1).split(":")[-1]
            for index in range(len(element_stack) - 1, -1, -1):
                if element_stack[index] == name:
                    del element_stack[index:]
                    break
            continue

        opened = _OPEN_TAG.fullmatch(token)
        if opened and not token[:-1].rstrip().endswith("/"):
            element_stack.append(opened.group(1).split(":")[-1])

    return "".join(output)
