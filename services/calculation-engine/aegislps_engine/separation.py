import math
from typing import List
from aegislps_domain.models import Project, SeparationPoint, SeparationCalculationResult, CalculationStatus
from aegislps_standards.repository import StandardsRepository

class SeparationDistanceEngine:
    def __init__(self, standards_repo: StandardsRepository = None):
        self.standards_repo = standards_repo or StandardsRepository()

    def _get_ki(self, lps_class: str) -> float:
        if lps_class == "I":
            param = self.standards_repo.get_parameter("IEC 62305-3:2024", "ki_class_I")
            return param.value if param else 0.08
        elif lps_class == "II":
            param = self.standards_repo.get_parameter("IEC 62305-3:2024", "ki_class_II")
            return param.value if param else 0.06
        else:
            param = self.standards_repo.get_parameter("IEC 62305-3:2024", "ki_class_III_IV")
            return param.value if param else 0.04

    def _get_km(self, medium: str) -> float:
        if medium == "solid":
            param = self.standards_repo.get_parameter("IEC 62305-3:2024", "km_solid")
            return param.value if param else 0.5
        param = self.standards_repo.get_parameter("IEC 62305-3:2024", "km_air")
        return param.value if param else 1.0

    def calculate_project(self, project: Project) -> List[SeparationCalculationResult]:
        results = []
        ki = self._get_ki(project.lps_class)

        # Map nodes for spatial lookup
        node_map = {n.id: n for n in project.nodes}

        for sp in project.separation_points:
            km = self._get_km(sp.insulation_medium)

            # Find effective path length l (from associated node z-height to ground z=0)
            assoc_node = node_map.get(sp.associated_node_id)
            if assoc_node:
                l_m = max(0.0, assoc_node.z)
            else:
                l_m = project.building.height_m

            # Default kc factor (simplified single/dual down-conductor assumption if not solved via graph)
            kc = 1.0 if len(project.segments) <= 1 else 0.5

            # Governing IEC equation: s = ki * (kc / km) * l
            s_m = ki * (kc / km) * l_m

            actual_m = sp.physical_distance_m
            pass_comp = actual_m >= s_m
            margin_m = actual_m - s_m

            trace = f"s = ki * (kc / km) * l = {ki} * ({kc} / {km}) * {l_m:.2f}m = {s_m:.4f}m"

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
                status=CalculationStatus.CALCULATED
            )
            results.append(res)

        return results
