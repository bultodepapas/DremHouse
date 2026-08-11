"""Materiales de acero estructural para el modelo E0."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Steel:
    name: str
    fy_pa: float
    fu_pa: float
    e_pa: float
    density_kg_m3: float
    role: str

    @property
    def fy_mpa(self) -> float:
        return self.fy_pa / 1e6

    @property
    def fy_design_pa(self) -> float:
        return self.fy_pa


def materials_from_json(data: dict) -> dict[str, Steel]:
    """Construye el diccionario de materiales desde los datos canónicos."""
    out = {}
    for key, raw in data["materials"].items():
        out[key] = Steel(
            name=raw["name"],
            fy_pa=raw["fy_mpa"] * 1e6,
            fu_pa=raw["fu_mpa"] * 1e6,
            e_pa=raw["E_mpa"] * 1e6,
            density_kg_m3=raw["density_kg_m3"],
            role=raw["role"],
        )
    return out
