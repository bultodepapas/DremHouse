"""Análisis elástico 2D de pórticos por matriz de rigidez (E0).

Modelo plano con nudos, miembros axiales+flexión, apoyos fijos/articulados y
cargas nodales más cargas uniformes equivalentes. Unidades SI internas (m, N,
Pa). Hipótesis de esquema; no sustituye el análisis del ingeniero.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math

import numpy as np

G = 9.81


class FrameAnalysisError(RuntimeError):
    """El modelo matricial no puede resolverse de forma físicamente válida."""


@dataclass(frozen=True)
class SimplySupportedBeamResponse:
    reaction_left_n: float
    reaction_right_n: float
    max_abs_moment_nm: float
    max_abs_deflection_m: float | None


@dataclass(frozen=True)
class OverhangingBeamResponse:
    reaction_left_n: float
    reaction_support_n: float
    max_abs_moment_nm: float
    support_moment_nm: float
    max_main_span_deflection_m: float
    max_overhang_deflection_m: float


@dataclass
class FrameMember:
    i: int
    j: int
    e_pa: float
    area_m2: float
    iy_m4: float
    w_y_n_m: float = 0.0
    w_x_n_m: float = 0.0
    w_cases: dict = field(default_factory=dict)


@dataclass
class Frame2D:
    nodes: list[tuple[float, float]] = field(default_factory=list)
    members: list[FrameMember] = field(default_factory=list)
    fixes: dict[int, set[str]] = field(default_factory=dict)

    def dof_of(self, node: int, comp: str) -> int:
        return 3 * node + ("ux", "uz", "ry").index(comp)

    def is_fixed(self, dof: int) -> bool:
        node, comp = divmod(dof, 3)
        comp_name = ("ux", "uz", "ry")[comp]
        return comp_name in self.fixes.get(node, set())

    def member_length(self, m: FrameMember) -> float:
        x1, z1 = self.nodes[m.i]
        x2, z2 = self.nodes[m.j]
        length = float(np.hypot(x2 - x1, z2 - z1))
        if not math.isfinite(length) or length <= 0.0:
            raise FrameAnalysisError(
                f"Miembro degenerado entre nudos {m.i} y {m.j}: longitud={length!r}"
            )
        return length

    def member_dir(self, m: FrameMember) -> tuple[float, float]:
        x1, z1 = self.nodes[m.i]
        x2, z2 = self.nodes[m.j]
        length = self.member_length(m)
        return (x2 - x1) / length, (z2 - z1) / length

    def solve(self, f_global: np.ndarray):
        n = 3 * len(self.nodes)
        self._validate_model()
        f_global = np.asarray(f_global, dtype=float)
        if f_global.shape != (n,):
            raise FrameAnalysisError(
                f"Vector de cargas con forma {f_global.shape}; se esperaba ({n},)"
            )
        if not np.all(np.isfinite(f_global)):
            raise FrameAnalysisError("El vector de cargas contiene NaN o infinito")
        free = [d for d in range(n) if not self.is_fixed(d)]
        if not free:
            raise FrameAnalysisError("El modelo no tiene grados de libertad libres")
        k = np.zeros((n, n))
        for m in self.members:
            dofs = self._member_dofs(m)
            k[np.ix_(dofs, dofs)] += self._member_global_stiffness(m)
        kff = k[np.ix_(free, free)]
        ff = f_global[free]
        try:
            d_free = np.linalg.solve(kff, ff)
        except np.linalg.LinAlgError as exc:
            raise FrameAnalysisError(
                "Matriz de rigidez singular o mal condicionada: revise apoyos, "
                "conectividad y propiedades de los miembros"
            ) from exc
        d = np.zeros(n)
        d[free] = d_free
        return d, k

    def _validate_model(self) -> None:
        if not self.nodes:
            raise FrameAnalysisError("El modelo no contiene nudos")
        for idx, coords in enumerate(self.nodes):
            if len(coords) != 2 or not all(math.isfinite(float(v)) for v in coords):
                raise FrameAnalysisError(f"Coordenadas inválidas en el nudo {idx}: {coords!r}")
        valid_components = {"ux", "uz", "ry"}
        for node, components in self.fixes.items():
            if node < 0 or node >= len(self.nodes):
                raise FrameAnalysisError(f"Apoyo referido a nudo inexistente: {node}")
            unknown = set(components) - valid_components
            if unknown:
                raise FrameAnalysisError(f"Grados de libertad desconocidos en nudo {node}: {sorted(unknown)}")
        for idx, m in enumerate(self.members):
            if m.i < 0 or m.j < 0 or m.i >= len(self.nodes) or m.j >= len(self.nodes):
                raise FrameAnalysisError(f"Miembro {idx} refiere nudos inexistentes: {m.i}, {m.j}")
            if m.i == m.j:
                raise FrameAnalysisError(f"Miembro {idx} conecta el nudo {m.i} consigo mismo")
            for label, value in (("E", m.e_pa), ("A", m.area_m2), ("Iy", m.iy_m4)):
                if not math.isfinite(value) or value <= 0.0:
                    raise FrameAnalysisError(
                        f"Propiedad {label} inválida en miembro {idx}: {value!r}"
                    )
            self.member_length(m)

    def _member_dofs(self, m: FrameMember) -> list[int]:
        return [self.dof_of(m.i, c) for c in ("ux", "uz", "ry")] + [self.dof_of(m.j, c) for c in ("ux", "uz", "ry")]

    def _member_local_k(self, m: FrameMember) -> np.ndarray:
        length = self.member_length(m)
        ea = m.e_pa * m.area_m2
        ei = m.e_pa * m.iy_m4
        a = ea / length
        b = 12.0 * ei / length**3
        c = 6.0 * ei / length**2
        d = 4.0 * ei / length
        e = 2.0 * ei / length
        return np.array([
            [a, 0, 0, -a, 0, 0],
            [0, b, c, 0, -b, c],
            [0, c, d, 0, -c, e],
            [-a, 0, 0, a, 0, 0],
            [0, -b, -c, 0, b, -c],
            [0, c, e, 0, -c, d],
        ])

    def _member_transform(self, m: FrameMember) -> np.ndarray:
        c, s = self.member_dir(m)
        return np.array([
            [c, s, 0, 0, 0, 0],
            [-s, c, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0],
            [0, 0, 0, c, s, 0],
            [0, 0, 0, -s, c, 0],
            [0, 0, 0, 0, 0, 1],
        ])

    def _member_global_stiffness(self, m: FrameMember) -> np.ndarray:
        t = self._member_transform(m)
        return t.T @ self._member_local_k(m) @ t

    def fixed_end_forces(self, m: FrameMember) -> np.ndarray:
        length = self.member_length(m)
        return np.array([
            -m.w_x_n_m * length / 2.0,
            m.w_y_n_m * length / 2.0,
            m.w_y_n_m * length**2 / 12.0,
            -m.w_x_n_m * length / 2.0,
            m.w_y_n_m * length / 2.0,
            -m.w_y_n_m * length**2 / 12.0,
        ])

    def equivalent_nodal_loads(self) -> np.ndarray:
        n = 3 * len(self.nodes)
        f = np.zeros(n)
        for m in self.members:
            t = self._member_transform(m)
            fef = self.fixed_end_forces(m)
            f[self._member_dofs(m)] += t.T @ (-fef)
        return f

    def member_end_forces(self, m: FrameMember, d: np.ndarray) -> np.ndarray:
        t = self._member_transform(m)
        d_local = t @ d[self._member_dofs(m)]
        return self._member_local_k(m) @ d_local + self.fixed_end_forces(m)


def max_moment_in_member(frame: Frame2D, m: FrameMember, f_local: np.ndarray) -> float:
    n1, v1, m1 = f_local[0], f_local[1], f_local[2]
    m2 = f_local[5]
    wy = m.w_y_n_m
    candidates = [abs(m1), abs(m2)]
    # El extremo interior existe con carga uniforme de cualquier signo. La
    # condición anterior (wy > 0) omitía por completo el momento máximo bajo
    # succión/carga ascendente cuando los momentos de extremo eran nulos.
    if abs(wy) > 1e-9:
        x_star = v1 / wy
        if 0.0 < x_star < frame.member_length(m):
            m_star = m1 + v1 * x_star - 0.5 * wy * x_star**2
            candidates.append(abs(m_star))
    return max(candidates)


def max_axial_in_member(f_local: np.ndarray) -> float:
    return max(abs(f_local[0]), abs(f_local[3]))


def simply_supported_max_moment(q_n_m: float, span_m: float) -> float:
    return q_n_m * span_m**2 / 8.0


def simply_supported_deflection(q_n_m: float, span_m: float, ei: float) -> float:
    return 5.0 * q_n_m * span_m**4 / (384.0 * ei)


def simply_supported_beam_response(
    span_m: float,
    point_loads_n: list[tuple[float, float]] | tuple[tuple[float, float], ...] = (),
    *,
    udl_n_m: float = 0.0,
    ei_n_m2: float | None = None,
    stations: int = 401,
) -> SimplySupportedBeamResponse:
    """Respuesta elástica de una viga simple con cargas puntuales y UDL.

    Las cargas positivas actúan hacia abajo. La fórmula de Macaulay conserva
    equilibrio exacto; la flecha máxima se busca en una malla uniforme más las
    posiciones de carga. Se usa para transferencias E0, no para diseño final.
    """

    if not math.isfinite(span_m) or span_m <= 0.0:
        raise ValueError("La luz de la viga debe ser positiva y finita")
    if not math.isfinite(udl_n_m):
        raise ValueError("La carga uniforme debe ser finita")
    if stations < 2:
        raise ValueError("Se requieren al menos dos estaciones de evaluación")
    loads: list[tuple[float, float]] = []
    for position, load in point_loads_n:
        position = float(position)
        load = float(load)
        if not math.isfinite(position) or not 0.0 <= position <= span_m:
            raise ValueError(f"Carga puntual fuera de la luz: x={position!r}")
        if not math.isfinite(load):
            raise ValueError("La carga puntual debe ser finita")
        loads.append((position, load))
    if ei_n_m2 is not None and (not math.isfinite(ei_n_m2) or ei_n_m2 <= 0.0):
        raise ValueError("EI debe ser positivo y finito")

    reaction_left = (
        sum(load * (span_m - position) for position, load in loads)
        + udl_n_m * span_m**2 / 2.0
    ) / span_m
    reaction_right = sum(load for _position, load in loads) + udl_n_m * span_m - reaction_left
    xs = {span_m * step / (stations - 1) for step in range(stations)}
    xs.update(position for position, _load in loads)
    max_moment = max(
        abs(
            reaction_left * x
            - udl_n_m * x**2 / 2.0
            - sum(load * (x - position) for position, load in loads if position <= x)
        )
        for x in xs
    )

    max_deflection: float | None = None
    if ei_n_m2 is not None:
        c1 = -(
            reaction_left * span_m**3 / 6.0
            - udl_n_m * span_m**4 / 24.0
            - sum(load * (span_m - position) ** 3 / 6.0 for position, load in loads)
        ) / span_m
        max_deflection = max(
            abs(
                (
                    reaction_left * x**3 / 6.0
                    - udl_n_m * x**4 / 24.0
                    - sum(
                        load * (x - position) ** 3 / 6.0
                        for position, load in loads
                        if position <= x
                    )
                    + c1 * x
                )
                / ei_n_m2
            )
            for x in xs
        )
    return SimplySupportedBeamResponse(
        reaction_left_n=reaction_left,
        reaction_right_n=reaction_right,
        max_abs_moment_nm=max_moment,
        max_abs_deflection_m=max_deflection,
    )


def overhanging_uniform_beam_response(
    support_span_m: float,
    overhang_m: float,
    udl_n_m: float,
    ei_n_m2: float,
    *,
    stations: int = 801,
) -> OverhangingBeamResponse:
    """Viga con apoyos en x=0 y x=a, y voladizo uniforme hasta x=a+b."""

    for label, value in (("luz entre apoyos", support_span_m), ("voladizo", overhang_m)):
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError(f"{label} debe ser positivo y finito")
    if not math.isfinite(udl_n_m) or udl_n_m < 0.0:
        raise ValueError("La carga uniforme gravitacional debe ser no negativa y finita")
    if not math.isfinite(ei_n_m2) or ei_n_m2 <= 0.0:
        raise ValueError("EI debe ser positivo y finito")
    if stations < 3:
        raise ValueError("Se requieren al menos tres estaciones de evaluación")

    a = support_span_m
    total_length = a + overhang_m
    reaction_support = udl_n_m * total_length**2 / (2.0 * a)
    reaction_left = udl_n_m * total_length - reaction_support
    support_moment = -udl_n_m * overhang_m**2 / 2.0
    c1 = -reaction_left * a**2 / 6.0 + udl_n_m * a**3 / 24.0

    max_moment = 0.0
    max_main_deflection = 0.0
    max_overhang_deflection = 0.0
    for step in range(stations):
        x = total_length * step / (stations - 1)
        macaulay = max(x - a, 0.0)
        moment = (
            reaction_left * x
            + reaction_support * macaulay
            - udl_n_m * x**2 / 2.0
        )
        deflection = (
            reaction_left * x**3 / 6.0
            + reaction_support * macaulay**3 / 6.0
            - udl_n_m * x**4 / 24.0
            + c1 * x
        ) / ei_n_m2
        max_moment = max(max_moment, abs(moment))
        if x <= a:
            max_main_deflection = max(max_main_deflection, abs(deflection))
        else:
            max_overhang_deflection = max(max_overhang_deflection, abs(deflection))

    return OverhangingBeamResponse(
        reaction_left_n=reaction_left,
        reaction_support_n=reaction_support,
        max_abs_moment_nm=max_moment,
        support_moment_nm=support_moment,
        max_main_span_deflection_m=max_main_deflection,
        max_overhang_deflection_m=max_overhang_deflection,
    )
