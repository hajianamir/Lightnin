import math
from typing import List, Optional, Tuple
from aegislps_domain.models import (
    CalculationStatus,
    Project,
    SeparationCalculationResult,
    SeparationPoint,
)
from aegislps_standards.repository import StandardsRepository

STANDARD_KEY = "IEC 62305-3:2024"


class SeparationDistanceEngine:
    """
    IEC 62305-3:2024, Clause 6.3.2 ("Simplified approach"), Equation (6):
        "s = (k_i / k_m) x k_c x l (m) (6)"
    with k_i from Table 11, k_m from Table 12, k_c from Table 13, and:
        "l is the length, in metres, along the air termination and the down
        conductor from the point, where the separation distance shall be
        considered, to the nearest equipotential bonding point or the earth
        termination (see D.6.3)."
    Table 13 condition:
        "If the earth resistances of single earth electrodes differ by more
        than a factor of 2, k_c = 1 shall be assumed."
    """

    def __init__(self, standards_repo: Optional[StandardsRepository] = None):
        self.standards_repo = standards_repo or StandardsRepository()

    def _require_parameter(self, param_id: str) -> float:
        param = self.standards_repo.get_parameter(STANDARD_KEY, param_id)
        if param is None:
            raise ValueError(
                f"Missing required parameter {param_id!r} in StandardsRepository for {STANDARD_KEY!r}."
            )
        return float(param.value)

    def _get_ki(self, lps_class: str) -> float:
        if not isinstance(lps_class, str):
            raise ValueError(
                f"Unknown LPS class {lps_class!r}. Expected 'I', 'II', 'III', or 'IV' (IEC 62305-3:2024 Table 11)."
            )
        if lps_class == "I":
            return self._require_parameter("ki_class_I")
        if lps_class == "II":
            return self._require_parameter("ki_class_II")
        if lps_class in ("III", "IV"):
            return self._require_parameter("ki_class_III_IV")
        raise ValueError(
            f"Unknown LPS class {lps_class!r}. Expected 'I', 'II', 'III', or 'IV' (IEC 62305-3:2024 Table 11)."
        )

    def _get_km(self, medium: str) -> float:
        if not isinstance(medium, str):
            raise ValueError(
                f"Unknown insulation medium {medium!r}. Expected 'air', 'solid', or 'insulating_standoff' (IEC 62305-3:2024 Table 12)."
            )
        if medium == "air":
            return self._require_parameter("km_air")
        if medium == "solid":
            return self._require_parameter("km_solid")
        if medium == "insulating_standoff":
            return self._require_parameter("km_insulating_standoff")
        raise ValueError(
            f"Unknown insulation medium {medium!r}. Expected 'air', 'solid', or 'insulating_standoff' (IEC 62305-3:2024 Table 12)."
        )

    def _resolve_kc(self, project: Project) -> Tuple[float, str, List[str]]:
        n = project.down_conductor_count
        within_factor_2 = project.earth_resistances_within_factor_2
        warnings: List[str] = []

        if n is None or within_factor_2 is None or within_factor_2 is False:
            kc = self._require_parameter("kc_earth_resistance_fallback")
            if n is None:
                warnings.append(
                    "down_conductor_count was not given; kc = 1.0 assumed per Table 13"
                )
            elif within_factor_2 is None:
                warnings.append(
                    "earth_resistances_within_factor_2 was not given; kc = 1.0 assumed per Table 13"
                )
            else:
                warnings.append(
                    "earth resistances of single earth electrodes differ by more than a factor of 2; kc = 1.0 assumed per Table 13"
                )
            if n == 1:
                warnings.append(
                    "n = 1 in Table 13 applies only in the case of an isolated LPS"
                )
            return kc, "Table 13 fallback (kc=1.0)", warnings

        if n == 1:
            kc = self._require_parameter("kc_n_1_isolated")
            warnings.append(
                "n = 1 in Table 13 applies only in the case of an isolated LPS"
            )
            return kc, "Table 13 (n=1, isolated LPS)", warnings

        if n == 2:
            kc = self._require_parameter("kc_n_2")
            return kc, "Table 13 (n=2)", warnings

        kc = self._require_parameter("kc_n_3_or_more")
        return kc, f"Table 13 (n={n}, 3 and more)", warnings

    def _resolve_length_l(
        self, sp: SeparationPoint, project: Project, node_map: dict
    ) -> Tuple[float, str, List[str]]:
        if sp.route_length_to_bonding_m is not None:
            if (
                isinstance(sp.route_length_to_bonding_m, bool)
                or not isinstance(sp.route_length_to_bonding_m, (int, float))
                or not math.isfinite(float(sp.route_length_to_bonding_m))
                or float(sp.route_length_to_bonding_m) <= 0.0
            ):
                raise ValueError(
                    f"route_length_to_bonding_m must be finite and > 0, got {sp.route_length_to_bonding_m!r}."
                )
            return (
                float(sp.route_length_to_bonding_m),
                "route_length_to_bonding_m",
                [],
            )

        if not isinstance(sp.associated_node_id, str) or not sp.associated_node_id:
            raise ValueError(
                f"SeparationPoint {sp.id!r}: associated_node_id is required when route_length_to_bonding_m is not given."
            )
        assoc_node = node_map.get(sp.associated_node_id)
        if assoc_node is None:
            raise ValueError(
                f"SeparationPoint {sp.id!r}: associated_node_id {sp.associated_node_id!r} not found in project nodes."
            )

        if (
            isinstance(assoc_node.z, bool)
            or not isinstance(assoc_node.z, (int, float))
            or not math.isfinite(float(assoc_node.z))
            or float(assoc_node.z) <= 0.0
        ):
            raise ValueError("associated node must be above ground for route length")

        l_m = float(assoc_node.z)
        l_source = f"node.z vertical approximation (node {assoc_node.id})"
        reason = (
            "route length was not given; approximated l = max(0, node.z), "
            "valid only for a straight vertical down conductor from the point to earth"
        )
        return l_m, l_source, [reason]

    def calculate_project(self, project: Project) -> List[SeparationCalculationResult]:
        if project.building is None:
            raise ValueError("Project.building is required.")

        results: List[SeparationCalculationResult] = []
        ki = self._get_ki(project.lps_class)
        kc, kc_source, kc_warnings = self._resolve_kc(project)

        node_map = {n.id: n for n in project.nodes}

        for sp in project.separation_points:
            if (
                isinstance(sp.physical_distance_m, bool)
                or not isinstance(sp.physical_distance_m, (int, float))
                or not math.isfinite(float(sp.physical_distance_m))
                or float(sp.physical_distance_m) < 0.0
            ):
                raise ValueError(
                    f"physical_distance_m must be finite and >= 0, got {sp.physical_distance_m!r}."
                )
            km = self._get_km(sp.insulation_medium)
            l_m, l_source, l_warnings = self._resolve_length_l(sp, project, node_map)

            # IEC 62305-3:2024, Clause 6.3.2, Eq. (6): s = (k_i / k_m) * k_c * l
            s_m = (ki / km) * kc * l_m

            actual_m = float(sp.physical_distance_m)
            pass_comp = actual_m >= s_m
            margin_m = actual_m - s_m

            all_warnings = kc_warnings + l_warnings
            status = (
                CalculationStatus.WARNING
                if all_warnings
                else CalculationStatus.CALCULATED
            )

            base_trace = (
                f"IEC 62305-3:2024 Clause 6.3.2 Eq. (6): "
                f"s = (ki / km) * kc * l = ({ki} / {km}) * {kc} * {l_m:.2f}m = {s_m:.4f}m "
                f"[kc: {kc_source}; l: {l_source}]"
            )
            trace = (
                f"{base_trace} | WARNING: {'; '.join(all_warnings)}"
                if all_warnings
                else base_trace
            )

            res = SeparationCalculationResult(
                separation_point_id=sp.id,
                required_distance_s_m=s_m,
                actual_distance_m=actual_m,
                pass_compliance=pass_comp,
                safety_margin_m=margin_m,
                lps_class=project.lps_class,
                ki_used=ki,
                kc_used=kc,
                km_used=km,
                length_l_m=l_m,
                formula_trace=trace,
                status=status,
            )
            results.append(res)

        return results
