"""Linear-elastic 2D pin-jointed truss analysis for structural exploration.

Internal units are metres, newtons, and pascals. This solver deliberately has
only translational degrees of freedom: it must not be used to approximate a
Vierendeel frame, semi-rigid joints, or local chord bending.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np


class TrussAnalysisError(RuntimeError):
    """The truss cannot be solved as a physically valid axial model."""


@dataclass(frozen=True)
class TrussMember:
    i: int
    j: int
    e_pa: float
    area_m2: float
    group: str = "member"
    profile_name: str = ""


@dataclass(frozen=True)
class TrussResults:
    displacements_m: np.ndarray
    reactions_n: np.ndarray
    member_forces_n: np.ndarray


@dataclass
class Truss2D:
    nodes: list[tuple[float, float]] = field(default_factory=list)
    members: list[TrussMember] = field(default_factory=list)
    fixes: dict[int, set[str]] = field(default_factory=dict)

    def dof_of(self, node: int, component: str) -> int:
        if component not in {"ux", "uz"}:
            raise TrussAnalysisError(f"Unknown truss degree of freedom: {component!r}")
        return 2 * node + (0 if component == "ux" else 1)

    def is_fixed(self, dof: int) -> bool:
        node, component = divmod(dof, 2)
        name = "ux" if component == 0 else "uz"
        return name in self.fixes.get(node, set())

    def member_length(self, member: TrussMember) -> float:
        x1, z1 = self.nodes[member.i]
        x2, z2 = self.nodes[member.j]
        length = float(np.hypot(x2 - x1, z2 - z1))
        if not math.isfinite(length) or length <= 0.0:
            raise TrussAnalysisError(
                f"Degenerate truss member {member.i}-{member.j}: length={length!r}"
            )
        return length

    def member_direction(self, member: TrussMember) -> tuple[float, float]:
        x1, z1 = self.nodes[member.i]
        x2, z2 = self.nodes[member.j]
        length = self.member_length(member)
        return (x2 - x1) / length, (z2 - z1) / length

    def _member_dofs(self, member: TrussMember) -> list[int]:
        return [
            self.dof_of(member.i, "ux"),
            self.dof_of(member.i, "uz"),
            self.dof_of(member.j, "ux"),
            self.dof_of(member.j, "uz"),
        ]

    def _member_stiffness(self, member: TrussMember) -> np.ndarray:
        length = self.member_length(member)
        c, s = self.member_direction(member)
        scale = member.e_pa * member.area_m2 / length
        return scale * np.array(
            [
                [c * c, c * s, -c * c, -c * s],
                [c * s, s * s, -c * s, -s * s],
                [-c * c, -c * s, c * c, c * s],
                [-c * s, -s * s, c * s, s * s],
            ],
            dtype=float,
        )

    def _validate_model(self) -> None:
        if not self.nodes:
            raise TrussAnalysisError("The truss has no nodes")
        for index, coordinates in enumerate(self.nodes):
            if len(coordinates) != 2 or not all(
                math.isfinite(float(value)) for value in coordinates
            ):
                raise TrussAnalysisError(
                    f"Invalid coordinates at truss node {index}: {coordinates!r}"
                )
        for node, components in self.fixes.items():
            if node < 0 or node >= len(self.nodes):
                raise TrussAnalysisError(f"Support references missing node {node}")
            unknown = set(components) - {"ux", "uz"}
            if unknown:
                raise TrussAnalysisError(f"Unknown restraints at node {node}: {sorted(unknown)}")
        if not self.members:
            raise TrussAnalysisError("The truss has no members")
        seen: set[tuple[int, int]] = set()
        for index, member in enumerate(self.members):
            if not 0 <= member.i < len(self.nodes) or not 0 <= member.j < len(self.nodes):
                raise TrussAnalysisError(
                    f"Member {index} references missing nodes {member.i}, {member.j}"
                )
            if member.i == member.j:
                raise TrussAnalysisError(f"Member {index} connects node {member.i} to itself")
            pair = tuple(sorted((member.i, member.j)))
            if pair in seen:
                raise TrussAnalysisError(f"Duplicate truss member between nodes {pair}")
            seen.add(pair)
            for label, value in (("E", member.e_pa), ("A", member.area_m2)):
                if not math.isfinite(value) or value <= 0.0:
                    raise TrussAnalysisError(f"Invalid {label} in truss member {index}: {value!r}")
            self.member_length(member)

    def stiffness_matrix(self) -> np.ndarray:
        self._validate_model()
        stiffness = np.zeros((2 * len(self.nodes), 2 * len(self.nodes)))
        for member in self.members:
            dofs = self._member_dofs(member)
            stiffness[np.ix_(dofs, dofs)] += self._member_stiffness(member)
        return stiffness

    def solve(self, loads_n: np.ndarray) -> TrussResults:
        stiffness = self.stiffness_matrix()
        loads = np.asarray(loads_n, dtype=float)
        expected = (2 * len(self.nodes),)
        if loads.shape != expected:
            raise TrussAnalysisError(f"Load vector has shape {loads.shape}; expected {expected}")
        if not np.all(np.isfinite(loads)):
            raise TrussAnalysisError("The truss load vector contains NaN or infinity")

        free = [dof for dof in range(len(loads)) if not self.is_fixed(dof)]
        if not free:
            raise TrussAnalysisError("The truss has no free degrees of freedom")
        reduced = stiffness[np.ix_(free, free)]
        if np.linalg.matrix_rank(reduced) < len(free):
            raise TrussAnalysisError(
                "Singular truss stiffness matrix: the free degrees of freedom contain a mechanism"
            )
        try:
            free_displacements = np.linalg.solve(reduced, loads[free])
        except np.linalg.LinAlgError as exc:
            raise TrussAnalysisError(
                "Singular truss stiffness matrix: check supports, connectivity, and mechanisms"
            ) from exc
        if not np.all(np.isfinite(free_displacements)):
            raise TrussAnalysisError("The truss solution contains NaN or infinity")

        displacements = np.zeros_like(loads)
        displacements[free] = free_displacements
        reactions = stiffness @ displacements - loads
        member_forces = np.array(
            [self.member_axial_force(member, displacements) for member in self.members]
        )
        return TrussResults(displacements, reactions, member_forces)

    def member_axial_force(self, member: TrussMember, displacements_m: np.ndarray) -> float:
        displacements = np.asarray(displacements_m, dtype=float)
        expected = (2 * len(self.nodes),)
        if displacements.shape != expected:
            raise TrussAnalysisError(
                f"Displacement vector has shape {displacements.shape}; expected {expected}"
            )
        c, s = self.member_direction(member)
        length = self.member_length(member)
        local_extension = np.array([-c, -s, c, s]) @ displacements[self._member_dofs(member)]
        return member.e_pa * member.area_m2 * local_extension / length
