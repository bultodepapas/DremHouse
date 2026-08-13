"""Fail-closed steel-member and trial-connection checks for the E1 research layer.

The equations mirror common LRFD forms in ANSI/AISC 360-22.  They are used to
expose governing phenomena and missing inputs, not to certify Colombian code
compliance.  Nominal HSS dimensions are parsed from the project profile names;
catalogue gross area and strong-axis inertia remain authoritative for mass and
global stiffness.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from .materials import Steel
from .profiles import Profile

_HSS_PATTERN = re.compile(r"^HSS(?P<depth>\d+)x(?P<width>\d+)x(?P<thickness>\d+)$")


class SteelCheckError(ValueError):
    """A steel-screening input is missing, unsupported, or physically invalid."""


def _positive_finite(**values: float) -> None:
    invalid = {
        name: value for name, value in values.items() if not math.isfinite(value) or value <= 0
    }
    if invalid:
        raise SteelCheckError(f"Expected positive finite values, received {invalid!r}")


@dataclass(frozen=True)
class HSSGeometry:
    """Nominal rectangular HSS geometry with the AISC design-wall reduction."""

    name: str
    outer_depth_m: float
    outer_width_m: float
    nominal_thickness_m: float
    design_thickness_m: float

    @classmethod
    def from_name(cls, name: str, design_thickness_factor: float = 0.93) -> HSSGeometry:
        match = _HSS_PATTERN.fullmatch(name)
        if match is None:
            raise SteelCheckError(f"Unsupported HSS designation: {name!r}")
        if not 0.0 < design_thickness_factor <= 1.0:
            raise SteelCheckError("The HSS design-thickness factor must be in (0, 1]")
        depth, width, thickness = (
            float(match.group("depth")) / 1000.0,
            float(match.group("width")) / 1000.0,
            float(match.group("thickness")) / 1000.0,
        )
        design_thickness = thickness * design_thickness_factor
        _positive_finite(
            outer_depth_m=depth,
            outer_width_m=width,
            nominal_thickness_m=thickness,
            design_thickness_m=design_thickness,
        )
        if 2.0 * design_thickness >= min(depth, width):
            raise SteelCheckError(f"Impossible wall thickness in {name}")
        return cls(name, depth, width, thickness, design_thickness)

    @property
    def flat_depth_m(self) -> float:
        return self.outer_depth_m - 3.0 * self.design_thickness_m

    @property
    def flat_width_m(self) -> float:
        return self.outer_width_m - 3.0 * self.design_thickness_m

    @property
    def sharp_corner_area_m2(self) -> float:
        d, b, t = self.outer_depth_m, self.outer_width_m, self.design_thickness_m
        return b * d - (b - 2.0 * t) * (d - 2.0 * t)

    @property
    def sharp_corner_ix_m4(self) -> float:
        d, b, t = self.outer_depth_m, self.outer_width_m, self.design_thickness_m
        return (b * d**3 - (b - 2.0 * t) * (d - 2.0 * t) ** 3) / 12.0

    @property
    def sharp_corner_iy_m4(self) -> float:
        d, b, t = self.outer_depth_m, self.outer_width_m, self.design_thickness_m
        return (d * b**3 - (d - 2.0 * t) * (b - 2.0 * t) ** 3) / 12.0

    @property
    def sharp_corner_zx_m3(self) -> float:
        d, b, t = self.outer_depth_m, self.outer_width_m, self.design_thickness_m
        return (b * d**2 - (b - 2.0 * t) * (d - 2.0 * t) ** 2) / 4.0

    @property
    def sharp_corner_zy_m3(self) -> float:
        d, b, t = self.outer_depth_m, self.outer_width_m, self.design_thickness_m
        return (d * b**2 - (d - 2.0 * t) * (b - 2.0 * t) ** 2) / 4.0

    def principal_properties(self, profile: Profile) -> tuple[float, float, float, float]:
        """Return strong/weak I and Z while retaining the catalogue strong-axis I.

        The project catalogue stores one inertia and elastic modulus.  The nominal
        geometry supplies only the axis ratio; this avoids silently treating a
        rectangular HSS as square.
        """

        ix_raw, iy_raw = self.sharp_corner_ix_m4, self.sharp_corner_iy_m4
        if ix_raw >= iy_raw:
            i_strong = profile.iy_m4
            i_weak = profile.iy_m4 * iy_raw / ix_raw
            z_strong = profile.zx_m3
            z_weak = profile.zx_m3 * self.sharp_corner_zy_m3 / self.sharp_corner_zx_m3
        else:
            i_strong = profile.iy_m4
            i_weak = profile.iy_m4 * ix_raw / iy_raw
            z_strong = profile.zx_m3
            z_weak = profile.zx_m3 * self.sharp_corner_zx_m3 / self.sharp_corner_zy_m3
        return i_strong, i_weak, z_strong, z_weak


@dataclass(frozen=True)
class LocalSlendernessCheck:
    compression_ratio: float
    flexural_flange_ratio: float
    flexural_web_ratio: float
    compression_class: str
    flexural_class: str
    effective_area_m2: float


def _effective_flat_width(
    width_m: float, thickness_m: float, e_pa: float, stress_pa: float
) -> float:
    """Effective width for a slender uniformly compressed stiffened element."""

    _positive_finite(width_m=width_m, thickness_m=thickness_m, e_pa=e_pa, stress_pa=stress_pa)
    slenderness = width_m / thickness_m
    root = math.sqrt(e_pa / stress_pa)
    effective = 1.92 * thickness_m * root * (1.0 - 0.38 * root / slenderness)
    return min(width_m, max(0.0, effective))


def hss_local_slenderness(
    profile: Profile,
    steel: Steel,
    compressive_stress_pa: float | None = None,
) -> LocalSlendernessCheck:
    _positive_finite(e_pa=steel.e_pa, fy_pa=steel.fy_pa, area_m2=profile.area_m2)
    geometry = HSSGeometry.from_name(profile.name)
    root = math.sqrt(steel.e_pa / steel.fy_pa)
    t = geometry.design_thickness_m
    width_ratio = geometry.flat_width_m / t
    depth_ratio = geometry.flat_depth_m / t

    compression_limit = 1.40 * root
    flange_compact_limit = 1.12 * root
    flange_noncompact_limit = 1.40 * root
    web_compact_limit = 2.42 * root
    web_noncompact_limit = 5.70 * root

    compression_ratio = max(width_ratio, depth_ratio) / compression_limit
    flange_ratio = width_ratio / flange_compact_limit
    web_ratio = depth_ratio / web_compact_limit
    compression_class = "nonslender" if compression_ratio <= 1.0 else "slender"
    if width_ratio <= flange_compact_limit and depth_ratio <= web_compact_limit:
        flexural_class = "compact"
    elif width_ratio <= flange_noncompact_limit and depth_ratio <= web_noncompact_limit:
        flexural_class = "noncompact"
    else:
        flexural_class = "slender"

    effective_area = profile.area_m2
    if compression_class == "slender":
        stress = compressive_stress_pa or steel.fy_pa
        _positive_finite(compressive_stress_pa=stress)
        effective_width = _effective_flat_width(geometry.flat_width_m, t, steel.e_pa, stress)
        effective_depth = _effective_flat_width(geometry.flat_depth_m, t, steel.e_pa, stress)
        lost_area = (
            2.0
            * t
            * (geometry.flat_width_m - effective_width + geometry.flat_depth_m - effective_depth)
        )
        scale = profile.area_m2 / geometry.sharp_corner_area_m2
        effective_area = max(0.0, profile.area_m2 - lost_area * scale)

    return LocalSlendernessCheck(
        compression_ratio=compression_ratio,
        flexural_flange_ratio=flange_ratio,
        flexural_web_ratio=web_ratio,
        compression_class=compression_class,
        flexural_class=flexural_class,
        effective_area_m2=effective_area,
    )


@dataclass(frozen=True)
class CompressionStrength:
    phi_pn_n: float
    fcr_pa: float
    fe_pa: float
    effective_area_m2: float
    kl_over_r_in_plane: float
    kl_over_r_out_of_plane: float
    governing_axis: str
    local_slenderness_ratio: float


def hss_compression_strength(
    profile: Profile,
    steel: Steel,
    length_in_plane_m: float,
    length_out_of_plane_m: float,
    *,
    k_in_plane: float = 1.0,
    k_out_of_plane: float = 1.0,
    phi_c: float = 0.9,
) -> CompressionStrength:
    _positive_finite(
        length_in_plane_m=length_in_plane_m,
        length_out_of_plane_m=length_out_of_plane_m,
        k_in_plane=k_in_plane,
        k_out_of_plane=k_out_of_plane,
        phi_c=phi_c,
    )
    if phi_c > 1.0:
        raise SteelCheckError("phi_c cannot exceed one")
    geometry = HSSGeometry.from_name(profile.name)
    i_strong, i_weak, _z_strong, _z_weak = geometry.principal_properties(profile)
    r_strong = math.sqrt(i_strong / profile.area_m2)
    r_weak = math.sqrt(i_weak / profile.area_m2)
    slender_in = k_in_plane * length_in_plane_m / r_strong
    slender_out = k_out_of_plane * length_out_of_plane_m / r_weak
    governing_slenderness = max(slender_in, slender_out)
    governing_axis = "in_plane" if slender_in >= slender_out else "out_of_plane"
    fe = math.pi**2 * steel.e_pa / governing_slenderness**2
    fy_over_fe = steel.fy_pa / fe
    if fy_over_fe <= 2.25:
        fcr = (0.658**fy_over_fe) * steel.fy_pa
    else:
        fcr = 0.877 * fe
    local = hss_local_slenderness(profile, steel, fcr)
    capacity = phi_c * fcr * local.effective_area_m2
    return CompressionStrength(
        phi_pn_n=capacity,
        fcr_pa=fcr,
        fe_pa=fe,
        effective_area_m2=local.effective_area_m2,
        kl_over_r_in_plane=slender_in,
        kl_over_r_out_of_plane=slender_out,
        governing_axis=governing_axis,
        local_slenderness_ratio=local.compression_ratio,
    )


@dataclass(frozen=True)
class FlexuralStrength:
    phi_mn_nm: float
    nominal_moment_nm: float
    section_class: str
    flange_slenderness_ratio: float
    web_slenderness_ratio: float
    resolved: bool


def hss_flexural_strength(
    profile: Profile,
    steel: Steel,
    *,
    axis: str = "strong",
    phi_b: float = 0.9,
) -> FlexuralStrength:
    if axis not in {"strong", "weak"}:
        raise SteelCheckError("HSS flexural axis must be 'strong' or 'weak'")
    _positive_finite(phi_b=phi_b)
    if phi_b > 1.0:
        raise SteelCheckError("phi_b cannot exceed one")
    geometry = HSSGeometry.from_name(profile.name)
    _i_strong, _i_weak, z_strong, z_weak = geometry.principal_properties(profile)
    z = z_strong if axis == "strong" else z_weak
    # The catalogue elastic modulus is strong-axis; scale it with the same
    # geometric axis ratio used for Z when weak-axis bending is requested.
    s = profile.wy_m3 if axis == "strong" else profile.wy_m3 * z_weak / z_strong
    root = math.sqrt(steel.e_pa / steel.fy_pa)
    t = geometry.design_thickness_m
    if axis == "strong":
        flange_slenderness = geometry.flat_width_m / t
        web_slenderness = geometry.flat_depth_m / t
    else:
        flange_slenderness = geometry.flat_depth_m / t
        web_slenderness = geometry.flat_width_m / t
    flange_compact_limit = 1.12 * root
    flange_noncompact_limit = 1.40 * root
    web_compact_limit = 2.42 * root
    web_noncompact_limit = 5.70 * root
    if flange_slenderness <= flange_compact_limit and web_slenderness <= web_compact_limit:
        section_class = "compact"
    elif flange_slenderness <= flange_noncompact_limit and web_slenderness <= web_noncompact_limit:
        section_class = "noncompact"
    else:
        section_class = "slender"
    mp = min(steel.fy_pa * z, 1.6 * steel.fy_pa * s)
    if section_class == "compact":
        nominal = mp
        resolved = True
    elif section_class == "noncompact":
        transition = 3.57 * flange_slenderness * math.sqrt(steel.fy_pa / steel.e_pa) - 4.0
        nominal = mp - (mp - steel.fy_pa * s) * min(1.0, max(0.0, transition))
        resolved = True
    else:
        # Effective-section flexure needs a full effective-width iteration and
        # corner geometry.  A zero capacity prevents silent acceptance.
        nominal = 0.0
        resolved = False
    return FlexuralStrength(
        phi_mn_nm=phi_b * nominal,
        nominal_moment_nm=nominal,
        section_class=section_class,
        flange_slenderness_ratio=flange_slenderness / flange_compact_limit,
        web_slenderness_ratio=web_slenderness / web_compact_limit,
        resolved=resolved,
    )


def beam_column_interaction_ratio(
    required_axial_n: float,
    available_axial_n: float,
    required_moment_nm: float,
    available_moment_nm: float,
) -> float:
    """AISC H1 uniaxial interaction, using positive demand magnitudes."""

    if min(required_axial_n, required_moment_nm) < 0.0:
        raise SteelCheckError("Interaction demands must be nonnegative magnitudes")
    _positive_finite(
        available_axial_n=available_axial_n,
        available_moment_nm=available_moment_nm,
    )
    axial_ratio = required_axial_n / available_axial_n
    moment_ratio = required_moment_nm / available_moment_nm
    if axial_ratio >= 0.2:
        return axial_ratio + (8.0 / 9.0) * moment_ratio
    return axial_ratio / 2.0 + moment_ratio


@dataclass(frozen=True)
class SecondOrderScreen:
    euler_load_n: float
    compression_to_euler_ratio: float
    moment_magnifier: float | None
    stable: bool


def second_order_screen(
    compression_n: float,
    e_pa: float,
    inertia_m4: float,
    length_m: float,
    *,
    effective_length_factor: float = 1.0,
    stiffness_reduction: float = 0.8,
    cm: float = 1.0,
) -> SecondOrderScreen:
    if compression_n < 0.0:
        raise SteelCheckError("Compression must be supplied as a positive magnitude")
    _positive_finite(
        e_pa=e_pa,
        inertia_m4=inertia_m4,
        length_m=length_m,
        effective_length_factor=effective_length_factor,
        stiffness_reduction=stiffness_reduction,
        cm=cm,
    )
    if stiffness_reduction > 1.0:
        raise SteelCheckError("The second-order stiffness-reduction factor cannot exceed one")
    pe = (
        math.pi**2
        * stiffness_reduction
        * e_pa
        * inertia_m4
        / (effective_length_factor * length_m) ** 2
    )
    ratio = compression_n / pe
    stable = ratio < 1.0
    magnifier = max(1.0, cm / (1.0 - ratio)) if stable else None
    return SecondOrderScreen(pe, ratio, magnifier, stable)


@dataclass(frozen=True)
class TrialGussetConnection:
    demand_kn: float
    bolt_shear_capacity_kn: float
    plate_bearing_capacity_kn: float
    plate_gross_yield_capacity_kn: float
    plate_net_rupture_capacity_kn: float
    plate_block_shear_capacity_kn: float
    weld_capacity_kn: float
    governing_trial_capacity_kn: float
    trial_ratio: float
    trial_components_pass: bool
    hss_local_limit_states_resolved: bool
    overall_design_resolved: bool


def trial_gusset_connection(
    demand_kn: float,
    *,
    bolt_count: int,
    bolt_diameter_mm: float,
    hole_diameter_mm: float,
    bolt_fu_mpa: float,
    plate_thickness_mm: float,
    plate_width_mm: float,
    plate_fy_mpa: float,
    plate_fu_mpa: float,
    end_distance_mm: float,
    pitch_mm: float,
    weld_size_mm: float,
    weld_length_each_side_mm: float,
    electrode_fu_mpa: float,
) -> TrialGussetConnection:
    """Screen a one-line bolt group plus double fillet weld and gusset plate.

    The result deliberately excludes HSS face yielding, wall plastification,
    punching, shear lag, connection eccentricity, fatigue, and seismic detailing.
    Consequently the generic component check can pass while the overall joint
    remains unresolved.
    """

    if demand_kn < 0.0 or bolt_count < 1:
        raise SteelCheckError("Connection demand must be nonnegative and bolt count positive")
    values = {
        "bolt_diameter_mm": bolt_diameter_mm,
        "hole_diameter_mm": hole_diameter_mm,
        "bolt_fu_mpa": bolt_fu_mpa,
        "plate_thickness_mm": plate_thickness_mm,
        "plate_width_mm": plate_width_mm,
        "plate_fy_mpa": plate_fy_mpa,
        "plate_fu_mpa": plate_fu_mpa,
        "end_distance_mm": end_distance_mm,
        "pitch_mm": pitch_mm,
        "weld_size_mm": weld_size_mm,
        "weld_length_each_side_mm": weld_length_each_side_mm,
        "electrode_fu_mpa": electrode_fu_mpa,
    }
    _positive_finite(**values)
    if hole_diameter_mm <= bolt_diameter_mm:
        raise SteelCheckError("The standard hole must exceed the nominal bolt diameter")
    if end_distance_mm <= hole_diameter_mm / 2.0 or pitch_mm <= hole_diameter_mm:
        raise SteelCheckError("Bolt edge distance or pitch leaves no clear bearing length")

    phi_bolt = 0.75
    bolt_area_mm2 = math.pi * bolt_diameter_mm**2 / 4.0
    bolt_shear = phi_bolt * bolt_count * 0.48 * bolt_fu_mpa * bolt_area_mm2 / 1000.0

    clear_end = end_distance_mm - hole_diameter_mm / 2.0
    clear_pitch = pitch_mm - hole_diameter_mm

    def bearing_one(clear_length: float) -> float:
        nominal = min(
            1.2 * clear_length * plate_thickness_mm * plate_fu_mpa,
            2.4 * bolt_diameter_mm * plate_thickness_mm * plate_fu_mpa,
        )
        return phi_bolt * nominal / 1000.0

    bearing = bearing_one(clear_end) + (bolt_count - 1) * bearing_one(clear_pitch)
    gross_yield = 0.9 * plate_fy_mpa * plate_width_mm * plate_thickness_mm / 1000.0
    net_width = plate_width_mm - hole_diameter_mm
    if net_width <= 0.0:
        raise SteelCheckError("Bolt hole consumes the trial gusset net section")
    net_rupture = 0.75 * plate_fu_mpa * net_width * plate_thickness_mm / 1000.0

    shear_length = end_distance_mm + (bolt_count - 1) * pitch_mm
    agv = 2.0 * shear_length * plate_thickness_mm
    anv = 2.0 * max(0.0, shear_length - (bolt_count - 0.5) * hole_diameter_mm) * plate_thickness_mm
    ant = net_width * plate_thickness_mm
    block_nominal = min(
        0.6 * plate_fu_mpa * anv + plate_fu_mpa * ant,
        0.6 * plate_fy_mpa * agv + plate_fu_mpa * ant,
    )
    block_shear = 0.75 * block_nominal / 1000.0
    weld = (
        2.0
        * 0.75
        * 0.60
        * electrode_fu_mpa
        * 0.707
        * weld_size_mm
        * weld_length_each_side_mm
        / 1000.0
    )
    capacities = (bolt_shear, bearing, gross_yield, net_rupture, block_shear, weld)
    governing = min(capacities)
    ratio = demand_kn / governing
    passes = ratio <= 1.0 + 1e-9
    return TrialGussetConnection(
        demand_kn=demand_kn,
        bolt_shear_capacity_kn=bolt_shear,
        plate_bearing_capacity_kn=bearing,
        plate_gross_yield_capacity_kn=gross_yield,
        plate_net_rupture_capacity_kn=net_rupture,
        plate_block_shear_capacity_kn=block_shear,
        weld_capacity_kn=weld,
        governing_trial_capacity_kn=governing,
        trial_ratio=ratio,
        trial_components_pass=passes,
        hss_local_limit_states_resolved=False,
        overall_design_resolved=False,
    )
