"""Catálogo de perfiles de stock para el predimensionamiento E0.

Valores estándar de mercado (IPE, HEA/HEB, canal C para correas, ángulo para
arriostramiento). Unidades SI derivadas de tablas métricas. El perfil C es una
aproximación de correa conformada en frío para cuantificación preliminar.
"""

from __future__ import annotations

from dataclasses import dataclass

_TABLE = {
    "IPE200": {"A_cm2": 28.5, "Iy_cm4": 1943.0, "Wy_cm3": 194.0, "mass_kg_m": 22.4},
    "IPE220": {"A_cm2": 33.4, "Iy_cm4": 2772.0, "Wy_cm3": 252.0, "mass_kg_m": 26.2},
    "IPE240": {"A_cm2": 39.1, "Iy_cm4": 3892.0, "Wy_cm3": 324.0, "mass_kg_m": 30.7},
    "IPE270": {"A_cm2": 45.9, "Iy_cm4": 5790.0, "Wy_cm3": 429.0, "mass_kg_m": 36.1},
    "IPE300": {"A_cm2": 53.8, "Iy_cm4": 8356.0, "Wy_cm3": 557.0, "mass_kg_m": 42.2},
    "IPE330": {"A_cm2": 62.6, "Iy_cm4": 11770.0, "Wy_cm3": 713.0, "mass_kg_m": 49.1},
    "IPE360": {"A_cm2": 72.7, "Iy_cm4": 16270.0, "Wy_cm3": 904.0, "mass_kg_m": 57.1},
    "IPE400": {"A_cm2": 84.5, "Iy_cm4": 23130.0, "Wy_cm3": 1160.0, "mass_kg_m": 66.3},
    "IPE450": {"A_cm2": 98.8, "Iy_cm4": 33740.0, "Wy_cm3": 1500.0, "mass_kg_m": 77.6},
    "IPE500": {"A_cm2": 115.5, "Iy_cm4": 48200.0, "Wy_cm3": 1930.0, "mass_kg_m": 90.7},
    "IPE550": {"A_cm2": 134.4, "Iy_cm4": 67120.0, "Wy_cm3": 2440.0, "mass_kg_m": 105.5},
    "IPE600": {"A_cm2": 156.0, "Iy_cm4": 92080.0, "Wy_cm3": 3070.0, "mass_kg_m": 122.4},
    "HEA200": {"A_cm2": 53.8, "Iy_cm4": 3692.0, "Wy_cm3": 389.0, "mass_kg_m": 42.3},
    "HEA240": {"A_cm2": 76.8, "Iy_cm4": 7763.0, "Wy_cm3": 675.0, "mass_kg_m": 60.3},
    "HEA300": {"A_cm2": 112.5, "Iy_cm4": 18260.0, "Wy_cm3": 1260.0, "mass_kg_m": 88.3},
    "HEA340": {"A_cm2": 133.5, "Iy_cm4": 27690.0, "Wy_cm3": 1680.0, "mass_kg_m": 104.8},
    "HEA400": {"A_cm2": 159.0, "Iy_cm4": 45070.0, "Wy_cm3": 2310.0, "mass_kg_m": 124.8},
    "HEA500": {"A_cm2": 197.5, "Iy_cm4": 86970.0, "Wy_cm3": 3550.0, "mass_kg_m": 155.0},
    "HEB200": {"A_cm2": 78.1, "Iy_cm4": 5696.0, "Wy_cm3": 570.0, "mass_kg_m": 61.3},
    "HEB240": {"A_cm2": 106.0, "Iy_cm4": 9383.0, "Wy_cm3": 938.0, "mass_kg_m": 83.2},
    "HEB300": {"A_cm2": 149.1, "Iy_cm4": 25170.0, "Wy_cm3": 1680.0, "mass_kg_m": 117.0},
    "HEB340": {"A_cm2": 170.9, "Iy_cm4": 36660.0, "Wy_cm3": 2160.0, "mass_kg_m": 134.0},
    "HEB400": {"A_cm2": 197.8, "Iy_cm4": 57680.0, "Wy_cm3": 2880.0, "mass_kg_m": 155.3},
    "HSS100x100x6": {"A_cm2": 21.4, "Iy_cm4": 280.0, "Wy_cm3": 56.0, "mass_kg_m": 16.8},
    "HSS120x120x6": {"A_cm2": 26.4, "Iy_cm4": 560.0, "Wy_cm3": 93.0, "mass_kg_m": 20.7},
    "HSS150x150x8": {"A_cm2": 45.4, "Iy_cm4": 1530.0, "Wy_cm3": 204.0, "mass_kg_m": 35.7},
    "HSS200x150x8": {"A_cm2": 52.6, "Iy_cm4": 2600.0, "Wy_cm3": 300.0, "mass_kg_m": 41.3},
    "HSS250x150x10": {"A_cm2": 74.8, "Iy_cm4": 5000.0, "Wy_cm3": 480.0, "mass_kg_m": 58.7},
    "HSS300x200x10": {"A_cm2": 94.0, "Iy_cm4": 13200.0, "Wy_cm3": 880.0, "mass_kg_m": 73.8},
    "C200": {"A_cm2": 8.1, "Iy_cm4": 390.0, "Wy_cm3": 48.0, "mass_kg_m": 6.4},
    "L50x5": {"A_cm2": 4.8, "Iy_cm4": 11.0, "Wy_cm3": 3.2, "mass_kg_m": 3.8},
}


@dataclass(frozen=True)
class Profile:
    name: str
    area_m2: float
    iy_m4: float
    wy_m3: float
    mass_kg_m: float

    @property
    def zx_m3(self) -> float:
        return 1.14 * self.wy_m3

    def axial_capacity_kn(self, fy: float, phi: float) -> float:
        return phi * self.area_m2 * fy / 1e3

    def moment_capacity_knm(self, fy: float, phi: float) -> float:
        return phi * self.zx_m3 * fy / 1e3

    def elastic_deflection_ratio(self) -> float:
        return self.iy_m4


def _to_profile(name: str) -> Profile:
    raw = _TABLE[name]
    return Profile(
        name=name,
        area_m2=raw["A_cm2"] * 1e-4,
        iy_m4=raw["Iy_cm4"] * 1e-8,
        wy_m3=raw["Wy_cm3"] * 1e-6,
        mass_kg_m=raw["mass_kg_m"],
    )


CATALOG: dict[str, Profile] = {name: _to_profile(name) for name in _TABLE}


def profile(name: str) -> Profile:
    if name not in CATALOG:
        raise KeyError(f"Perfil no disponible: {name}")
    return CATALOG[name]


def series(prefix: str) -> list[Profile]:
    return [p for name, p in CATALOG.items() if name.startswith(prefix)]


def lightest_member(
    fy: float,
    phi_b: float,
    phi_c: float,
    required_moment_knm: float,
    required_axial_kn: float,
    length_m: float,
    series_name: str,
    deflection_limit_m: float | None,
    q_service_kn_m: float | None,
    *,
    e_pa: float = 2.0e11,
) -> tuple[Profile, float]:
    """Selecciona el perfil más liviano que cumple resistencia, interacción
    axial+flexión y flecha (viga con carga uniforme de servicio). Hipótesis E0.

    El límite de flecha se compara en metros (p. ej. L/240 = length_m/240.0);
    q_service_kn_m en kN/m.
    """
    best = None
    for cand in series(series_name):
        mcap = cand.moment_capacity_knm(fy, phi_b)
        acap = cand.axial_capacity_kn(fy, phi_c)
        if required_axial_kn >= 0 and required_axial_kn / max(acap, 1e-9) > 1.0:
            continue
        if required_moment_knm > mcap:
            continue
        interaction = max(
            (required_axial_kn / max(acap, 1e-9)) + (required_moment_knm / max(mcap, 1e-9)),
            required_moment_knm / max(mcap, 1e-9),
        )
        if interaction > 1.0 + 1e-9:
            continue
        if deflection_limit_m is not None and q_service_kn_m is not None:
            ei = e_pa * cand.iy_m4
            delta = 5.0 * q_service_kn_m * 1e3 * length_m**4 / (384.0 * ei)
            if delta > deflection_limit_m:
                continue
        best = cand
        break
    if best is None:
        best = series(series_name)[-1]
    return best, best.mass_kg_m
