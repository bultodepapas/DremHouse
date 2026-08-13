"""Análisis elástico 2D de pórticos por matriz de rigidez (E0).

Modelo plano con nudos, miembros axiales+flexión, apoyos fijos/articulados y
cargas nodales más cargas uniformes equivalentes. Unidades SI internas (m, N,
Pa). Hipótesis de esquema; no sustituye el análisis del ingeniero.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

G = 9.81


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
        return float(np.hypot(x2 - x1, z2 - z1))

    def member_dir(self, m: FrameMember) -> tuple[float, float]:
        x1, z1 = self.nodes[m.i]
        x2, z2 = self.nodes[m.j]
        length = self.member_length(m)
        return (x2 - x1) / length, (z2 - z1) / length

    def solve(self, f_global: np.ndarray):
        n = 3 * len(self.nodes)
        free = [d for d in range(n) if not self.is_fixed(d)]
        k = np.zeros((n, n))
        for m in self.members:
            dofs = self._member_dofs(m)
            k[np.ix_(dofs, dofs)] += self._member_global_stiffness(m)
        kff = k[np.ix_(free, free)]
        ff = f_global[free]
        d_free = np.linalg.solve(kff, ff)
        d = np.zeros(n)
        d[free] = d_free
        return d, k

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
