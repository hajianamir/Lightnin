import json
import tempfile
import os
import pytest
from aegislps_domain.models import Project, Building, ConductorNode, SeparationPoint
from aegislps_domain.integrity import ProjectIntegrityEngine

def test_project_lps_json_serialization_and_deserialization():
    orig_proj = Project(
        name="Offshore Substation",
        lps_class="I",
        building=Building(length_m=45.0, width_m=30.0, height_m=18.0, roof_type="flat"),
        nodes=[
            ConductorNode(id="n1", x=0, y=0, z=18.0, node_type="air_termination"),
            ConductorNode(id="n2", x=45, y=30, z=0, node_type="earth_point")
        ],
        separation_points=[
            SeparationPoint(id="sp1", name="Control Room Rack", x=10, y=10, z=18.0, associated_node_id="n1", physical_distance_m=1.4)
        ]
    )

    proj_dict = orig_proj.model_dump()
    checksum = ProjectIntegrityEngine.compute_project_checksum(proj_dict)
    proj_dict["checksum"] = checksum

    with tempfile.NamedTemporaryFile(suffix=".lps", delete=False, mode="w") as f:
        json.dump(proj_dict, f, indent=2)
        f_path = f.name

    try:
        with open(f_path, "r") as f:
            loaded_data = json.load(f)

        loaded_proj = Project(**loaded_data)
        assert loaded_proj.name == "Offshore Substation"
        assert loaded_proj.lps_class == "I"
        assert loaded_proj.building.length_m == 45.0
        assert len(loaded_proj.nodes) == 2
        assert len(loaded_proj.separation_points) == 1

        # Checksum validation on loaded project
        is_valid = ProjectIntegrityEngine.verify_project_integrity(loaded_data, loaded_data["checksum"])
        assert is_valid is True
    finally:
        if os.path.exists(f_path):
            os.remove(f_path)
