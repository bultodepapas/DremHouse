"""System-level E1 research checks for fire, diaphragm, erection, and foundations."""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import pairwise


class SystemCheckError(ValueError):
    """A system-screening input is invalid or physically inconsistent."""


def _positive_finite(**values: float) -> None:
    invalid = {
        name: value for name, value in values.items() if not math.isfinite(value) or value <= 0
    }
    if invalid:
        raise SystemCheckError(f"Expected positive finite values, received {invalid!r}")


# ANSI/AISC 360-22 Appendix 4 retention-factor temperatures.  Linear
# interpolation is suitable only for this screening layer; a fire design needs
# a thermal analysis and the complete elevated-temperature member equations.
_FIRE_RETENTION = (
    (20.0, 1.000, 1.000),
    (100.0, 1.000, 1.000),
    (200.0, 1.000, 0.900),
    (300.0, 1.000, 0.800),
    (400.0, 1.000, 0.700),
    (500.0, 0.780, 0.600),
    (600.0, 0.470, 0.310),
    (700.0, 0.230, 0.130),
    (800.0, 0.110, 0.090),
    (900.0, 0.060, 0.0675),
    (1000.0, 0.040, 0.0450),
    (1100.0, 0.020, 0.0225),
    (1200.0, 0.000, 0.0000),
)


def fire_retention_factors(temperature_c: float) -> tuple[float, float]:
    if not math.isfinite(temperature_c) or not 20.0 <= temperature_c <= 1200.0:
        raise SystemCheckError("Steel temperature must be between 20 and 1200 degC")
    for left, right in pairwise(_FIRE_RETENTION):
        if left[0] <= temperature_c <= right[0]:
            fraction = (temperature_c - left[0]) / (right[0] - left[0])
            ky = left[1] + fraction * (right[1] - left[1])
            ke = left[2] + fraction * (right[2] - left[2])
            return ky, ke
    return _FIRE_RETENTION[-1][1], _FIRE_RETENTION[-1][2]


@dataclass(frozen=True)
class FireCapacityScreen:
    temperature_c: float
    yield_retention: float
    stiffness_retention: float
    ambient_utilization: float
    conservative_strength_utilization: float | None
    conservative_stiffness_utilization: float | None
    trial_temperature_pass: bool
    fire_resistance_period_defined: bool
    thermal_protection_system_defined: bool
    overall_fire_design_resolved: bool


def fire_capacity_screen(
    ambient_utilization: float,
    temperature_c: float,
    *,
    fire_resistance_period_defined: bool = False,
    thermal_protection_system_defined: bool = False,
) -> FireCapacityScreen:
    if not math.isfinite(ambient_utilization) or ambient_utilization < 0.0:
        raise SystemCheckError("Ambient utilization must be finite and nonnegative")
    ky, ke = fire_retention_factors(temperature_c)
    strength_ratio = ambient_utilization / ky if ky > 0.0 else None
    stiffness_ratio = ambient_utilization / ke if ke > 0.0 else None
    passes = strength_ratio is not None and strength_ratio <= 1.0 + 1e-9
    resolved = fire_resistance_period_defined and thermal_protection_system_defined and passes
    return FireCapacityScreen(
        temperature_c=temperature_c,
        yield_retention=ky,
        stiffness_retention=ke,
        ambient_utilization=ambient_utilization,
        conservative_strength_utilization=strength_ratio,
        conservative_stiffness_utilization=stiffness_ratio,
        trial_temperature_pass=passes,
        fire_resistance_period_defined=fire_resistance_period_defined,
        thermal_protection_system_defined=thermal_protection_system_defined,
        overall_fire_design_resolved=resolved,
    )


@dataclass(frozen=True)
class DiaphragmScreen:
    total_lateral_force_kn: float
    diaphragm_length_m: float
    diaphragm_depth_m: float
    required_unit_shear_kn_m: float
    required_chord_force_kn: float
    nominal_capacity_kn_m: float | None
    strength_ratio: float | None
    assembled_shear_stiffness_kn_mm: float | None
    estimated_shear_displacement_mm: float | None
    manufacturer_system_defined: bool
    collectors_defined: bool
    connections_defined: bool
    overall_diaphragm_resolved: bool


def diaphragm_screen(
    total_lateral_force_kn: float,
    diaphragm_length_m: float,
    diaphragm_depth_m: float,
    *,
    nominal_capacity_kn_m: float | None = None,
    assembled_shear_stiffness_kn_mm: float | None = None,
    collectors_defined: bool = False,
    connections_defined: bool = False,
) -> DiaphragmScreen:
    if not math.isfinite(total_lateral_force_kn) or total_lateral_force_kn < 0.0:
        raise SystemCheckError("Lateral force must be finite and nonnegative")
    _positive_finite(diaphragm_length_m=diaphragm_length_m, diaphragm_depth_m=diaphragm_depth_m)
    if nominal_capacity_kn_m is not None:
        _positive_finite(nominal_capacity_kn_m=nominal_capacity_kn_m)
    if assembled_shear_stiffness_kn_mm is not None:
        _positive_finite(assembled_shear_stiffness_kn_mm=assembled_shear_stiffness_kn_mm)

    unit_shear = total_lateral_force_kn / diaphragm_depth_m
    # Deep-beam screening for a uniformly distributed lateral action along the
    # diaphragm length: Mmax = W*L/8 and chord force = M/depth.
    chord_force = total_lateral_force_kn * diaphragm_length_m / (8.0 * diaphragm_depth_m)
    ratio = unit_shear / nominal_capacity_kn_m if nominal_capacity_kn_m is not None else None
    displacement = (
        total_lateral_force_kn / assembled_shear_stiffness_kn_mm
        if assembled_shear_stiffness_kn_mm is not None
        else None
    )
    manufacturer_defined = nominal_capacity_kn_m is not None
    resolved = (
        manufacturer_defined
        and ratio is not None
        and ratio <= 1.0 + 1e-9
        and assembled_shear_stiffness_kn_mm is not None
        and collectors_defined
        and connections_defined
    )
    return DiaphragmScreen(
        total_lateral_force_kn=total_lateral_force_kn,
        diaphragm_length_m=diaphragm_length_m,
        diaphragm_depth_m=diaphragm_depth_m,
        required_unit_shear_kn_m=unit_shear,
        required_chord_force_kn=chord_force,
        nominal_capacity_kn_m=nominal_capacity_kn_m,
        strength_ratio=ratio,
        assembled_shear_stiffness_kn_mm=assembled_shear_stiffness_kn_mm,
        estimated_shear_displacement_mm=displacement,
        manufacturer_system_defined=manufacturer_defined,
        collectors_defined=collectors_defined,
        connections_defined=connections_defined,
        overall_diaphragm_resolved=resolved,
    )


@dataclass(frozen=True)
class BracedBayScreen:
    total_lateral_force_kn: float
    force_per_active_bay_kn: float
    brace_angle_deg_from_horizontal: float
    tension_brace_demand_kn: float
    tension_yield_capacity_kn: float
    strength_ratio: float
    trial_strength_pass: bool
    brace_locations_validated: bool
    connections_and_collectors_resolved: bool
    overall_lateral_path_resolved: bool


def braced_bay_screen(
    total_lateral_force_kn: float,
    *,
    parallel_braced_lines: int,
    active_bays_per_line: int,
    bay_width_m: float,
    bay_height_m: float,
    brace_area_m2: float,
    brace_fy_pa: float,
    phi_t: float = 0.9,
    brace_locations_validated: bool = False,
    connections_and_collectors_resolved: bool = False,
) -> BracedBayScreen:
    """Screen one tension-active diagonal per braced bay under load reversal."""

    if not math.isfinite(total_lateral_force_kn) or total_lateral_force_kn < 0.0:
        raise SystemCheckError("Lateral force must be finite and nonnegative")
    if parallel_braced_lines < 1 or active_bays_per_line < 1:
        raise SystemCheckError("At least one braced line and active bay are required")
    _positive_finite(
        bay_width_m=bay_width_m,
        bay_height_m=bay_height_m,
        brace_area_m2=brace_area_m2,
        brace_fy_pa=brace_fy_pa,
        phi_t=phi_t,
    )
    if phi_t > 1.0:
        raise SystemCheckError("phi_t cannot exceed one")
    active_bays = parallel_braced_lines * active_bays_per_line
    force_per_bay = total_lateral_force_kn / active_bays
    angle = math.atan2(bay_height_m, bay_width_m)
    demand = force_per_bay / math.cos(angle)
    capacity = phi_t * brace_fy_pa * brace_area_m2 / 1000.0
    ratio = demand / capacity
    strength_pass = ratio <= 1.0 + 1e-9
    resolved = strength_pass and brace_locations_validated and connections_and_collectors_resolved
    return BracedBayScreen(
        total_lateral_force_kn=total_lateral_force_kn,
        force_per_active_bay_kn=force_per_bay,
        brace_angle_deg_from_horizontal=math.degrees(angle),
        tension_brace_demand_kn=demand,
        tension_yield_capacity_kn=capacity,
        strength_ratio=ratio,
        trial_strength_pass=strength_pass,
        brace_locations_validated=brace_locations_validated,
        connections_and_collectors_resolved=connections_and_collectors_resolved,
        overall_lateral_path_resolved=resolved,
    )


@dataclass(frozen=True)
class ErectionLiftScreen:
    truss_length_m: float
    lifted_mass_kg: float
    dynamic_factor: float
    lift_point_count: int
    sling_angle_deg_from_horizontal: float
    required_hook_load_kn: float
    reaction_per_lift_point_kn: float
    sling_tension_each_kn: float
    minimum_transport_piece_count: int
    shop_or_field_splice_required: bool
    crane_capacity_kn: float | None
    crane_capacity_ratio: float | None
    temporary_bracing_installed: bool
    weather_limit_defined: bool
    overall_release_from_crane_ready: bool


def erection_lift_screen(
    truss_length_m: float,
    lifted_mass_kg: float,
    *,
    dynamic_factor: float,
    lift_point_count: int,
    sling_angle_deg_from_horizontal: float,
    maximum_transport_piece_length_m: float,
    crane_capacity_kn: float | None = None,
    temporary_bracing_installed: bool = False,
    weather_limit_defined: bool = False,
) -> ErectionLiftScreen:
    _positive_finite(
        truss_length_m=truss_length_m,
        lifted_mass_kg=lifted_mass_kg,
        dynamic_factor=dynamic_factor,
        maximum_transport_piece_length_m=maximum_transport_piece_length_m,
    )
    if lift_point_count < 2:
        raise SystemCheckError("At least two lift points are required for this screen")
    if not 0.0 < sling_angle_deg_from_horizontal < 90.0:
        raise SystemCheckError("Sling angle must lie strictly between 0 and 90 degrees")
    if crane_capacity_kn is not None:
        _positive_finite(crane_capacity_kn=crane_capacity_kn)

    gravity = 9.80665
    hook_load = lifted_mass_kg * gravity * dynamic_factor / 1000.0
    reaction = hook_load / lift_point_count
    sling_tension = reaction / math.sin(math.radians(sling_angle_deg_from_horizontal))
    piece_count = math.ceil(truss_length_m / maximum_transport_piece_length_m)
    crane_ratio = hook_load / crane_capacity_kn if crane_capacity_kn is not None else None
    ready = (
        crane_ratio is not None
        and crane_ratio <= 1.0 + 1e-9
        and temporary_bracing_installed
        and weather_limit_defined
    )
    return ErectionLiftScreen(
        truss_length_m=truss_length_m,
        lifted_mass_kg=lifted_mass_kg,
        dynamic_factor=dynamic_factor,
        lift_point_count=lift_point_count,
        sling_angle_deg_from_horizontal=sling_angle_deg_from_horizontal,
        required_hook_load_kn=hook_load,
        reaction_per_lift_point_kn=reaction,
        sling_tension_each_kn=sling_tension,
        minimum_transport_piece_count=piece_count,
        shop_or_field_splice_required=piece_count > 1,
        crane_capacity_kn=crane_capacity_kn,
        crane_capacity_ratio=crane_ratio,
        temporary_bracing_installed=temporary_bracing_installed,
        weather_limit_defined=weather_limit_defined,
        overall_release_from_crane_ready=ready,
    )


@dataclass(frozen=True)
class PadFoundationScreen:
    applied_vertical_kn: float
    applied_horizontal_kn: float
    applied_moment_knm: float
    foundation_dead_load_kn: float
    soil_cover_dead_load_kn: float
    net_vertical_kn: float
    eccentricity_m: float | None
    maximum_bearing_kpa: float | None
    minimum_bearing_kpa: float | None
    bearing_ratio: float | None
    sliding_ratio: float | None
    full_contact: bool
    overturning_stable: bool
    bearing_pass: bool
    sliding_pass: bool
    uplift_pass: bool
    geotechnical_parameters_approved: bool
    reinforced_concrete_design_resolved: bool
    overall_foundation_resolved: bool


@dataclass(frozen=True)
class BasePlateScreen:
    compression_kn: float
    uplift_kn: float
    concrete_bearing_capacity_kn: float
    concrete_bearing_ratio: float
    plate_projection_mm: float
    required_plate_thickness_mm: float
    provided_plate_thickness_mm: float
    plate_bending_ratio: float
    anchor_group_tension_capacity_kn: float | None
    anchor_tension_ratio: float | None
    compression_components_pass: bool
    anchor_tension_resolved: bool
    shear_transfer_resolved: bool
    moment_transfer_resolved: bool
    overall_base_plate_resolved: bool


def base_plate_screen(
    compression_kn: float,
    uplift_kn: float,
    *,
    plate_width_mm: float,
    plate_length_mm: float,
    plate_thickness_mm: float,
    column_width_mm: float,
    column_depth_mm: float,
    plate_fy_mpa: float,
    concrete_fc_mpa: float,
    supporting_area_ratio: float = 1.0,
    anchor_group_tension_capacity_kn: float | None = None,
    shear_transfer_resolved: bool = False,
    moment_transfer_resolved: bool = False,
) -> BasePlateScreen:
    """Screen centred bearing and plate cantilever bending under compression.

    The calculation is intentionally inapplicable to moment bases until the
    anchor layout, grout, pedestal, shear-transfer mechanism, and concrete
    breakout/pullout/pryout limit states are supplied.
    """

    if not all(math.isfinite(value) and value >= 0.0 for value in (compression_kn, uplift_kn)):
        raise SystemCheckError("Base-plate compression and uplift must be finite magnitudes")
    _positive_finite(
        plate_width_mm=plate_width_mm,
        plate_length_mm=plate_length_mm,
        plate_thickness_mm=plate_thickness_mm,
        column_width_mm=column_width_mm,
        column_depth_mm=column_depth_mm,
        plate_fy_mpa=plate_fy_mpa,
        concrete_fc_mpa=concrete_fc_mpa,
        supporting_area_ratio=supporting_area_ratio,
    )
    if column_width_mm >= plate_width_mm or column_depth_mm >= plate_length_mm:
        raise SystemCheckError("The trial base plate must project beyond the column footprint")
    if anchor_group_tension_capacity_kn is not None:
        _positive_finite(anchor_group_tension_capacity_kn=anchor_group_tension_capacity_kn)

    phi_bearing = 0.65
    bearing_increase = min(2.0, math.sqrt(supporting_area_ratio))
    area_mm2 = plate_width_mm * plate_length_mm
    bearing_capacity = phi_bearing * 0.85 * concrete_fc_mpa * area_mm2 * bearing_increase / 1000.0
    bearing_ratio = compression_kn / bearing_capacity
    bearing_pressure_mpa = compression_kn * 1000.0 / area_mm2
    projection = max(
        (plate_width_mm - column_width_mm) / 2.0,
        (plate_length_mm - column_depth_mm) / 2.0,
    )
    required_thickness = projection * math.sqrt(2.0 * bearing_pressure_mpa / (0.9 * plate_fy_mpa))
    bending_ratio = required_thickness / plate_thickness_mm
    compression_pass = bearing_ratio <= 1.0 + 1e-9 and bending_ratio <= 1.0 + 1e-9
    if anchor_group_tension_capacity_kn is None:
        anchor_ratio = None
        anchor_resolved = False
    else:
        anchor_ratio = uplift_kn / anchor_group_tension_capacity_kn
        anchor_resolved = anchor_ratio <= 1.0 + 1e-9
    overall = (
        compression_pass
        and anchor_resolved
        and shear_transfer_resolved
        and moment_transfer_resolved
    )
    return BasePlateScreen(
        compression_kn=compression_kn,
        uplift_kn=uplift_kn,
        concrete_bearing_capacity_kn=bearing_capacity,
        concrete_bearing_ratio=bearing_ratio,
        plate_projection_mm=projection,
        required_plate_thickness_mm=required_thickness,
        provided_plate_thickness_mm=plate_thickness_mm,
        plate_bending_ratio=bending_ratio,
        anchor_group_tension_capacity_kn=anchor_group_tension_capacity_kn,
        anchor_tension_ratio=anchor_ratio,
        compression_components_pass=compression_pass,
        anchor_tension_resolved=anchor_resolved,
        shear_transfer_resolved=shear_transfer_resolved,
        moment_transfer_resolved=moment_transfer_resolved,
        overall_base_plate_resolved=overall,
    )


def pad_foundation_screen(
    applied_vertical_kn: float,
    applied_horizontal_kn: float,
    applied_moment_knm: float,
    *,
    width_m: float,
    length_m: float,
    thickness_m: float,
    embedment_m: float,
    allowable_bearing_kpa: float,
    base_friction_coefficient: float,
    concrete_unit_weight_kn_m3: float = 24.0,
    soil_unit_weight_kn_m3: float = 18.0,
    geotechnical_parameters_approved: bool = False,
    reinforced_concrete_design_resolved: bool = False,
) -> PadFoundationScreen:
    """Screen gross bearing, sliding, contact, and uplift for one load case.

    Applied vertical load is positive downward and may be negative for uplift.
    The check excludes settlement, groundwater, passive resistance, punching,
    one-way shear, flexure, reinforcement, anchors, and group interaction.
    """

    if not all(
        math.isfinite(value)
        for value in (applied_vertical_kn, applied_horizontal_kn, applied_moment_knm)
    ):
        raise SystemCheckError("Foundation actions must be finite")
    _positive_finite(
        width_m=width_m,
        length_m=length_m,
        thickness_m=thickness_m,
        embedment_m=embedment_m,
        allowable_bearing_kpa=allowable_bearing_kpa,
        base_friction_coefficient=base_friction_coefficient,
        concrete_unit_weight_kn_m3=concrete_unit_weight_kn_m3,
        soil_unit_weight_kn_m3=soil_unit_weight_kn_m3,
    )
    if thickness_m > embedment_m:
        raise SystemCheckError("Foundation thickness cannot exceed embedment in this screen")

    area = width_m * length_m
    foundation_weight = area * thickness_m * concrete_unit_weight_kn_m3
    soil_cover_weight = area * (embedment_m - thickness_m) * soil_unit_weight_kn_m3
    net_vertical = applied_vertical_kn + foundation_weight + soil_cover_weight
    uplift_pass = net_vertical > 0.0
    eccentricity = abs(applied_moment_knm) / net_vertical if net_vertical > 0.0 else None
    qmax: float | None = None
    qmin: float | None = None
    full_contact = False
    overturning_stable = eccentricity is not None and eccentricity < width_m / 2.0
    if eccentricity is not None and overturning_stable:
        if eccentricity <= width_m / 6.0:
            average = net_vertical / area
            qmax = average * (1.0 + 6.0 * eccentricity / width_m)
            qmin = average * (1.0 - 6.0 * eccentricity / width_m)
            full_contact = True
        else:
            contact_width = 3.0 * (width_m / 2.0 - eccentricity)
            qmax = 2.0 * net_vertical / (length_m * contact_width)
            qmin = 0.0
    bearing_ratio = qmax / allowable_bearing_kpa if qmax is not None else None
    sliding_resistance = base_friction_coefficient * max(net_vertical, 0.0)
    sliding_ratio = (
        abs(applied_horizontal_kn) / sliding_resistance if sliding_resistance > 0.0 else None
    )
    bearing_pass = bearing_ratio is not None and bearing_ratio <= 1.0 + 1e-9
    sliding_pass = sliding_ratio is not None and sliding_ratio <= 1.0 + 1e-9
    overall = (
        bearing_pass
        and sliding_pass
        and uplift_pass
        and overturning_stable
        and geotechnical_parameters_approved
        and reinforced_concrete_design_resolved
    )
    return PadFoundationScreen(
        applied_vertical_kn=applied_vertical_kn,
        applied_horizontal_kn=applied_horizontal_kn,
        applied_moment_knm=applied_moment_knm,
        foundation_dead_load_kn=foundation_weight,
        soil_cover_dead_load_kn=soil_cover_weight,
        net_vertical_kn=net_vertical,
        eccentricity_m=eccentricity,
        maximum_bearing_kpa=qmax,
        minimum_bearing_kpa=qmin,
        bearing_ratio=bearing_ratio,
        sliding_ratio=sliding_ratio,
        full_contact=full_contact,
        overturning_stable=overturning_stable,
        bearing_pass=bearing_pass,
        sliding_pass=sliding_pass,
        uplift_pass=uplift_pass,
        geotechnical_parameters_approved=geotechnical_parameters_approved,
        reinforced_concrete_design_resolved=reinforced_concrete_design_resolved,
        overall_foundation_resolved=overall,
    )
