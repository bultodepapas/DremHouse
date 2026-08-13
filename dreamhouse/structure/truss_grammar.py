"""Manufacturable parametric roof-truss grammars for E0 exploration."""

from __future__ import annotations

import math
from dataclasses import dataclass

SUPPORTED_TOPOLOGIES = ("WARREN_MODIFIED", "PRATT", "HOWE", "X")
SUPPORTED_DEPTH_SHAPES = ("CONSTANT", "VARIABLE")


@dataclass(frozen=True)
class LayoutMember:
    i: int
    j: int
    group: str
    role: str


@dataclass(frozen=True)
class TrussLayout:
    topology: str
    depth_shape: str
    nodes: tuple[tuple[float, float], ...]
    members: tuple[LayoutMember, ...]
    top_nodes: tuple[int, ...]
    bottom_nodes: tuple[int, ...]
    support_nodes: tuple[int, int]
    crossing_count: int

    @property
    def member_count(self) -> int:
        return len(self.members)

    @property
    def joint_count(self) -> int:
        return len(self.nodes)

    @property
    def max_node_degree(self) -> int:
        degree = [0] * len(self.nodes)
        for member in self.members:
            degree[member.i] += 1
            degree[member.j] += 1
        return max(degree, default=0)


def _validate_geometry(
    topology: str,
    depth_shape: str,
    span_m: float,
    panel_count: int,
    centre_depth_m: float,
    end_depth_fraction: float,
) -> None:
    if topology not in SUPPORTED_TOPOLOGIES:
        raise ValueError(f"Unsupported truss topology: {topology!r}")
    if depth_shape not in SUPPORTED_DEPTH_SHAPES:
        raise ValueError(f"Unsupported depth shape: {depth_shape!r}")
    for label, value in (("span", span_m), ("centre depth", centre_depth_m)):
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError(f"Truss {label} must be positive and finite")
    if panel_count < 4 or panel_count % 2:
        raise ValueError("Roof trusses require an even panel count of at least four")
    if not math.isfinite(end_depth_fraction) or not 0.25 <= end_depth_fraction <= 1.0:
        raise ValueError("End-depth fraction must lie between 0.25 and 1.00")


def generate_roof_truss(
    *,
    topology: str,
    depth_shape: str,
    span_m: float,
    eave_low_m: float,
    eave_high_m: float,
    panel_count: int,
    centre_depth_m: float,
    end_depth_fraction: float = 0.55,
) -> TrussLayout:
    """Generate a mono-pitch truss without changing the canonical roof line.

    The top chord follows the low-to-high eave line. A VARIABLE truss keeps the
    roof straight while lowering the bottom chord towards midspan. All roof
    loads are applied at top-chord panel points, and supports occur at the two
    top-chord end nodes.
    """

    _validate_geometry(
        topology,
        depth_shape,
        span_m,
        panel_count,
        centre_depth_m,
        end_depth_fraction,
    )
    if not all(math.isfinite(value) for value in (eave_low_m, eave_high_m)):
        raise ValueError("Eave elevations must be finite")

    nodes: list[tuple[float, float]] = []
    top_nodes: list[int] = []
    bottom_nodes: list[int] = []
    for index in range(panel_count + 1):
        x = span_m * index / panel_count
        roof_z = eave_low_m + (eave_high_m - eave_low_m) * x / span_m
        if depth_shape == "CONSTANT":
            depth = centre_depth_m
        else:
            shape = 1.0 - abs(2.0 * x / span_m - 1.0)
            end_depth = centre_depth_m * end_depth_fraction
            depth = end_depth + (centre_depth_m - end_depth) * shape
        top_nodes.append(len(nodes))
        nodes.append((x, roof_z))
        bottom_nodes.append(len(nodes))
        nodes.append((x, roof_z - depth))

    members: list[LayoutMember] = []
    for index in range(panel_count):
        members.append(LayoutMember(top_nodes[index], top_nodes[index + 1], "chord", "top_chord"))
        members.append(
            LayoutMember(bottom_nodes[index], bottom_nodes[index + 1], "chord", "bottom_chord")
        )
    for index in range(panel_count + 1):
        members.append(LayoutMember(top_nodes[index], bottom_nodes[index], "web", "vertical"))

    crossings = 0
    for index in range(panel_count):
        centre_x = span_m * (index + 0.5) / panel_count
        if topology == "WARREN_MODIFIED":
            pair = (
                (top_nodes[index], bottom_nodes[index + 1])
                if index % 2 == 0
                else (bottom_nodes[index], top_nodes[index + 1])
            )
            members.append(LayoutMember(*pair, "web", "diagonal"))
        elif topology == "PRATT":
            pair = (
                (top_nodes[index], bottom_nodes[index + 1])
                if centre_x <= span_m / 2.0
                else (bottom_nodes[index], top_nodes[index + 1])
            )
            members.append(LayoutMember(*pair, "web", "diagonal"))
        elif topology == "HOWE":
            pair = (
                (bottom_nodes[index], top_nodes[index + 1])
                if centre_x <= span_m / 2.0
                else (top_nodes[index], bottom_nodes[index + 1])
            )
            members.append(LayoutMember(*pair, "web", "diagonal"))
        else:
            members.append(
                LayoutMember(top_nodes[index], bottom_nodes[index + 1], "web", "diagonal")
            )
            members.append(
                LayoutMember(bottom_nodes[index], top_nodes[index + 1], "web", "diagonal")
            )
            crossings += 1

    unique_pairs = {tuple(sorted((member.i, member.j))) for member in members}
    if len(unique_pairs) != len(members):
        raise ValueError("The generated truss contains duplicate members")
    return TrussLayout(
        topology=topology,
        depth_shape=depth_shape,
        nodes=tuple(nodes),
        members=tuple(members),
        top_nodes=tuple(top_nodes),
        bottom_nodes=tuple(bottom_nodes),
        support_nodes=(top_nodes[0], top_nodes[-1]),
        crossing_count=crossings,
    )
