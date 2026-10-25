from pathlib import Path

from fastapi.testclient import TestClient

from phishguard.api import create_app
from phishguard.pipeline import run_pipeline


def test_prometheus_metrics_expose_prediction_counts(tmp_path: Path):
    run_pipeline(Path("data/sample/phishing_urls.csv"), tmp_path)
    client = TestClient(create_app(tmp_path / "model.joblib"))
    client.post("/predict", json={"url": "https://www.google.com"})

    response = client.get("/metrics")
    assert response.status_code == 200
    assert "phishguard_requests_total" in response.text
    assert "phishguard_predictions_total" in response.text
    assert "phishguard_prediction_latency_seconds" in response.text
