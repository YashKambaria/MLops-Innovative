"""FastAPI inference service for the saved PhishGuard model."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from .features import build_feature_frame

DEFAULT_MODEL_PATH = Path("artifacts/model.joblib")
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


class PredictionRequest(BaseModel):
    """A URL string to classify; it is treated as data and never visited."""

    url: str = Field(min_length=1, max_length=4096)


class PredictionResponse(BaseModel):
    url: str
    prediction: str
    is_phishing: bool
    confidence: float


def _load_model(model_path: Path) -> Any:
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model not found at {model_path}. Run `python -m phishguard.pipeline` first."
        )
    return joblib.load(model_path)


def create_app(model_path: Path | None = None) -> FastAPI:
    """Create an application using a saved model artifact."""
    resolved_path = model_path or Path(os.environ.get("PHISHGUARD_MODEL_PATH", DEFAULT_MODEL_PATH))
    model = _load_model(resolved_path)
    app = FastAPI(title="PhishGuard API", version="0.1.0")
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

    def classify_url(url: str) -> PredictionResponse:
        try:
            features = build_feature_frame(pd.Series([url]))
            prediction = int(model.predict(features)[0])
            probabilities = model.predict_proba(features)[0]
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=422, detail=f"Invalid URL input: {exc}") from exc
        return PredictionResponse(
            url=url,
            prediction="phishing" if prediction == 1 else "legitimate",
            is_phishing=prediction == 1,
            confidence=float(max(probabilities)),
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "model": str(resolved_path)}

    @app.get("/", include_in_schema=False)
    def home(request: Request):
        return templates.TemplateResponse(request=request, name="index.html", context={"result": None, "error": None})

    @app.post("/check", include_in_schema=False)
    def check_url(request: Request, url: str = Form(default="")):
        url = url.strip()
        if not url:
            return templates.TemplateResponse(
                request=request,
                name="index.html",
                context={"result": None, "error": "Please enter a URL."},
                status_code=400,
            )
        try:
            result = classify_url(url)
        except HTTPException as exc:
            return templates.TemplateResponse(
                request=request,
                name="index.html",
                context={"result": None, "error": str(exc.detail)},
                status_code=exc.status_code,
            )
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"result": result.model_dump(), "error": None},
        )

    @app.post("/predict", response_model=PredictionResponse)
    def predict(request: PredictionRequest) -> PredictionResponse:
        return classify_url(request.url)

    return app


app = create_app()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the PhishGuard prediction API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--model", type=Path, default=None)
    args = parser.parse_args()
    import uvicorn

    uvicorn.run(create_app(args.model), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
