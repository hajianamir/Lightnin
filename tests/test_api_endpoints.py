from fastapi.testclient import TestClient
from services.api.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"

def test_separation_distance_endpoint():
    payload = {
        "name": "API Test Project",
        "lps_class": "I",
        "building": {"length_m": 20, "width_m": 10, "height_m": 15, "roof_type": "flat"},
        "nodes": [{"id": "n1", "x": 0, "y": 0, "z": 15, "node_type": "air_termination"}],
        "segments": [],
        "separation_points": [{
            "id": "sp1",
            "name": "Test Point",
            "x": 1, "y": 1, "z": 15,
            "associated_node_id": "n1",
            "insulation_medium": "air",
            "physical_distance_m": 2.0
        }]
    }
    response = client.post("/api/v1/calculations/separation-distance", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["required_distance_s_m"] == 1.2
    assert data[0]["pass_compliance"] is True

def test_pdf_report_endpoint():
    payload = {
        "name": "PDF Test Project",
        "lps_class": "I",
        "building": {"length_m": 20, "width_m": 10, "height_m": 15, "roof_type": "flat"},
        "nodes": [{"id": "n1", "x": 0, "y": 0, "z": 15, "node_type": "air_termination"}],
        "segments": [],
        "separation_points": [{
            "id": "sp1",
            "name": "Test Point",
            "x": 1, "y": 1, "z": 15,
            "associated_node_id": "n1",
            "insulation_medium": "air",
            "physical_distance_m": 2.0
        }]
    }
    response = client.post("/api/v1/reports/pdf", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 1000
