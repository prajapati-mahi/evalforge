import pytest
import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_evaluation_workflow():
    # 1. Register a user
    user_email = f"lead_engineer_{int(time.time())}@evalforge.dev"
    reg_res = client.post("/api/v1/auth/register", json={
        "email": user_email,
        "password": "Password123!",
        "full_name": "Senior AI Tester"
    })
    assert reg_res.status_code == 200
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create a project
    proj_res = client.post("/api/v1/projects", json={
        "name": "Integration Test Project",
        "description": "End-to-end integration test workspace",
        "project_type": "rag",
        "default_model": "mock-gpt-4o"
    }, headers=headers)
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]

    # 3. Seed sample dataset
    ds_res = client.post(f"/api/v1/datasets/seed-sample?project_id={project_id}", headers=headers)
    assert ds_res.status_code == 200
    dataset_id = ds_res.json()["id"]
    assert ds_res.json()["num_cases"] > 0

    # 4. Verify mock provider is available
    prov_res = client.post("/api/v1/providers/test/mock", headers=headers)
    assert prov_res.status_code == 200
    assert prov_res.json()["status"] == "connected"

    # 5. Create an experiment
    exp_res = client.post("/api/v1/experiments", json={
        "project_id": project_id,
        "name": "E2E Benchmark Run",
        "dataset_id": dataset_id,
        "config": {
            "models": ["mock-gpt-4o", "mock-claude-3-5-sonnet"],
            "evaluators": ["correctness", "faithfulness", "relevance"],
            "temperature": 0.3
        }
    }, headers=headers)
    assert exp_res.status_code == 201
    experiment_id = exp_res.json()["id"]

    # 6. Execute the experiment
    run_res = client.post(f"/api/v1/experiments/{experiment_id}/run", headers=headers)
    assert run_res.status_code == 200
    assert run_res.json()["status"] in ("queued", "running", "completed")

    # Give background execution a moment to complete
    time.sleep(1.5)

    # 7. Check experiment results & metrics
    results_res = client.get(f"/api/v1/experiments/{experiment_id}/results", headers=headers)
    assert results_res.status_code == 200
    runs = results_res.json()["runs"]
    assert len(runs) >= 1

    # 8. Check traces stored
    traces_res = client.get(f"/api/v1/traces?project_id={project_id}", headers=headers)
    assert traces_res.status_code == 200

    # 9. View dashboard results
    dash_res = client.get(f"/api/v1/dashboard/metrics?project_id={project_id}", headers=headers)
    assert dash_res.status_code == 200
    data = dash_res.json()
    assert "total_evaluations" in data

    # 10. Generate CSV and PDF reports
    report_res = client.post("/api/v1/reports", json={
        "experiment_id": experiment_id,
        "format": "csv"
    }, headers=headers)
    assert report_res.status_code == 200
    assert report_res.json()["filename"].endswith(".csv")

    pdf_res = client.post("/api/v1/reports", json={
        "experiment_id": experiment_id,
        "format": "pdf"
    }, headers=headers)
    assert pdf_res.status_code == 200
    assert pdf_res.json()["filename"].endswith(".pdf")
