from pathlib import Path

from fastapi.testclient import TestClient

from phishguard.api import create_app
from phishguard.pipeline import run_pipeline


def test_health_and_prediction_endpoints(tmp_path: Path):
    run_pipeline(Path("data/sample/phishing_urls.csv"), tmp_path)
    client = TestClient(create_app(tmp_path / "model.joblib"))

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    response = client.post("/predict", json={"url": "http://secure-login.example.invalid/verify"})
    assert response.status_code == 200
    body = response.json()
    assert body["url"].startswith("http://")
    assert body["prediction"] in {"phishing", "legitimate"}
    assert isinstance(body["confidence"], float)
    assert 0 <= body["confidence"] <= 1

    page = client.get("/")
    assert page.status_code == 200
    assert "Check a URL before you click" in page.text

    form = client.post("/check", data={"url": "https://www.google.com"})
    assert form.status_code == 200
    assert "Legitimate" in form.text or "Phishing" in form.text


def test_prediction_requires_url(tmp_path: Path):
    run_pipeline(Path("data/sample/phishing_urls.csv"), tmp_path)
    client = TestClient(create_app(tmp_path / "model.joblib"))
    assert client.post("/predict", json={}).status_code == 422
