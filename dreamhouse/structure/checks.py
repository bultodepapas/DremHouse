"""Controles de validez y cargas para el cribado estructural E0.

Este módulo no implementa NSR-10. Su función es impedir que un modelo parcial se
presente como diseño o como comparador concluyente cuando faltan entradas, estados
límite o autorización de la solución arquitectónico-estructural.
"""

from __future__ import annotations


def max_factored_gravity(cfg: dict, dead: float, live: float) -> float:
    """Máxima demanda gravitacional D/L entre las combinaciones configuradas.

    ``dead`` y ``live`` pueden ser presiones o cargas lineales, siempre que
    usen las mismas unidades. Los demás casos se ignoran deliberadamente para
    dimensionar el subtotal gravitacional de vigas/cerchas de piso.
    """

    return max(
        combo["factors"].get("D", 0.0) * dead
        + combo["factors"].get("L", 0.0) * live
        for combo in cfg["combinations"]
    )


def build_model_audit(cfg: dict) -> dict:
    """Devuelve el dictamen de uso permitido del modelo E0.

    Los bloqueadores son hechos del alcance del motor y del expediente, no una
    afirmación de incumplimiento de la estructura futura.
    """

    blockers = [
        {
            "id": "E0-AUTH-01",
            "severity": "critical",
            "description": (
                "D-043 adopta el GRAN-MURO como apoyo gravitacional híbrido, pero el E0 "
                "solo prueba un bastidor oculto idealizado. Falta diseñar la viga de "
                "transferencia, columnas, pandeo, uniones, anclajes, fuego y compatibilidad "
                "1:1 con las cinco aperturas antes de descontar apoyos o fijar acero."
            ),
        },
        {
            "id": "E0-DIR-01",
            "severity": "critical",
            "description": (
                "El gran muro está en X=31,50 y se extiende en Y: su plano no estabiliza "
                "automáticamente la dirección longitudinal X. El E0 anterior lo llamó "
                "erróneamente núcleo de corte longitudinal; las dos fachadas largas, el "
                "diafragma y los colectores siguen sin sistema lateral coordinado."
            ),
        },
        {
            "id": "E0-COORD-01",
            "severity": "critical",
            "description": (
                "Las X longitudinales dibujadas en los paños 0–12 y 24–36 atraviesan el "
                "ventanal técnico de 7,20 m, vanos casi piso a techo del P2 y zonas de "
                "claraboya. Son trazos de conflicto, no arriostramientos adoptados."
            ),
        },
        {
            "id": "E0-GEOM-01",
            "severity": "high",
            "description": (
                "El borde del P2 X=21,00 y el gran muro X=31,50 caen a mitad de vanos de "
                "la retícula M60. El modelo de pórticos tributarios no representa estas "
                "transferencias fuera de retícula ni sus efectos locales."
            ),
        },
        {
            "id": "E0-LAT-01",
            "severity": "critical",
            "description": (
                "La alternativa CERCHA no tiene modelo lateral, diafragma, colectores "
                "ni arriostramientos dimensionados; su peso es un subtotal inferior."
            ),
        },
        {
            "id": "E0-STAB-01",
            "severity": "critical",
            "description": (
                "El pórtico es elástico lineal de primer orden y usa límites de fluencia "
                "de sección bruta; faltan pandeo, P-Delta, imperfecciones, pandeo "
                "lateral-torsional, esbeltez local, cortante y conexiones."
            ),
        },
        {
            "id": "E0-SITE-01",
            "severity": "critical",
            "description": (
                "No hay predio, municipio, perfil de suelo, espectro, topografía ni "
                "presiones normativas de viento. qz y Cs siguen siendo hipótesis."
            ),
        },
        {
            "id": "E0-LOAD-01",
            "severity": "critical",
            "description": (
                "No se modelan lluvia/empozamiento ni el efecto estructural completo de "
                "las dos claraboyas D-040, grandes portones y ventanales sobre el camino "
                "de cargas y los arriostramientos."
            ),
        },
        {
            "id": "E0-P2-01",
            "severity": "critical",
            "description": (
                "El deck profundo no tiene ficha, geometría compuesta, apuntalamiento, "
                "conectores ni verificación de vibración; no se reporta una frecuencia "
                "numérica de panel."
            ),
        },
        {
            "id": "E0-CLEAR-01",
            "severity": "high",
            "description": (
                "La prueba D-043 usa seis IPE450 a 3,00 m y 0,15 m de armado de piso: "
                "canto total conceptual 0,60 m. Cabe con cielo cercano a +3,10 m, pero "
                "la reserva de 0,10 m para fuego, tolerancias y servicios debe demostrarse "
                "con deck y detalle compuesto reales; +3,20 m no deja reserva."
            ),
        },
        {
            "id": "E0-FOUND-01",
            "severity": "high",
            "description": (
                "Las bases fijas se comparan sin flexibilidad ni costo/peso de cimentación, "
                "placas base y anclajes; no son comparables económicamente con bases "
                "articuladas hasta tener geotecnia."
            ),
        },
        {
            "id": "E0-QTY-01",
            "severity": "high",
            "description": (
                "Correas, girts, arriostramientos, cartelas, conexiones, deck y protección "
                "se estiman por perfiles/factores o reservas; no son cantidades de diseño."
            ),
        },
    ]
    return {
        "revision": cfg["project"]["revision"],
        "status": "screening_only_not_eligible_for_selection_or_budget",
        "design_compliance_demonstrated": False,
        "ranking_eligible": False,
        "permitted_uses": [
            "coordinación geométrica preliminar",
            "detección de conflictos de caminos de carga",
            "subtotales inferiores para definir el alcance de E1",
        ],
        "prohibited_uses": [
            "cerrar D-019",
            "cruzar PE-1 con cantidades del E0",
            "seleccionar o comprar perfiles",
            "diseñar cimentaciones, conexiones o fabricar",
        ],
        "blockers": blockers,
    }
