# test_api.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# --- Valid payloads ---
valid_payloads = [
    {
        "repo_url": "https://github.com/potpie-ai/potpie/",
        "pr_number": 305,
        "github_token": "string"
    },
    {
        "repo_url": "https://github.com/potpie-ai/potpie/",
        "pr_number": 396,
        "github_token": "string"
    },
    {
        "repo_url": "https://github.com/potpie-ai/potpie/",
        "pr_number": 232,
        "github_token": "string"
    }
]


@pytest.mark.parametrize("payload", valid_payloads)
def test_analyze_pr(payload):
    """Ensure /analyze-pr accepts valid payloads"""
    response = client.post("/analyze-pr", json=payload)
    assert response.status_code in [200, 202]

    data = response.json()
    assert "task_id" in data
    assert "status" in data


def test_analyze_pr_invalid_payload():
    """Test /analyze-pr with invalid/missing fields"""
    bad_payloads = [
        {},  # completely empty
        {"repo_url": "https://github.com/potpie-ai/potpie/"},  # missing fields
        {"pr_number": "not_a_number", "repo_url": 123},  # wrong types
    ]

    for bad in bad_payloads:
        response = client.post("/analyze-pr", json=bad)
        assert response.status_code == 422  # Unprocessable Entity


@pytest.mark.parametrize("payload", valid_payloads)
def test_status_and_results_with_valid_task(payload):
    """Test status + results with a valid task_id"""
    analyze_response = client.post("/analyze-pr", json=payload)
    assert analyze_response.status_code in [200, 202]
    task_id = analyze_response.json()["task_id"]

    # Check status
    status_response = client.get(f"/status/{task_id}")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["task_id"] == task_id
    assert "status" in status_data

    # Check results
    results_response = client.get(f"/results/{task_id}")
    assert results_response.status_code in [200, 202, 500]
    results_data = results_response.json()
    assert "task_id" in results_data
    assert "status" in results_data


def test_status_with_invalid_task():
    """Test /status with an invalid task_id"""
    response = client.get("/status/invalid-task-id-123")
    assert response.status_code == 200  # API returns 200 with status info
    data = response.json()
    assert "task_id" in data
    assert "status" in data
    assert data["status"] in ["FAILURE", "PENDING", "SUCCESS"]


def test_results_with_invalid_task():
    """Test /results with an invalid task_id"""
    response = client.get("/results/invalid-task-id-123")
    assert response.status_code in [200, 404, 500]  # allow 200 since API returns it
    data = response.json()
    assert "task_id" in data
    assert "status" in data
    assert data["status"] in ["FAILURE", "PENDING", "SUCCESS"]
