# PhishGuard — Steps 1 and 2

Initial offline machine-learning pipeline for phishing URL classification.
The model uses lexical URL features and a scikit-learn Random Forest baseline.
It does not visit, resolve, or request any URL values from the dataset.

Step 2 adds a FastAPI inference service with a Jinja2 web frontend and Docker
packaging. It exposes `/health`, `/predict`, and a browser-based URL checker.

## Setup

Python 3.11 is recommended.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

## Run the verified local pipeline

The committed sample contains inert URL strings and is intended for a quick,
offline smoke test:

```bash
python -m phishguard.pipeline
```

This writes `artifacts/model.joblib` and `artifacts/metadata.json`.
The metadata records precision, recall, F1, the 2x2 confusion matrix, and the
false-negative rate.

## Use the public dataset

The default acquisition source is the UCI Machine Learning Repository's
PhiUSIIL Phishing URL Dataset:

<https://archive.ics.uci.edu/dataset/967/phiusiil+phishing+url+dataset>

To download the archive and train for the first time:

```bash
python -m phishguard.pipeline --download --output-dir artifacts/uci
```

After the dataset has been downloaded, the simple command below automatically
finds the CSV or ZIP file in `data/raw/` and trains on it:

```bash
python -m phishguard.pipeline
```

The download retrieves only the dataset archive. The pipeline reads URL values
as text for local feature extraction and never opens them. For a different CSV,
provide columns named `url` and `label`:

```bash
python -m phishguard.pipeline --source path/to/dataset.csv --output-dir artifacts/custom
```

Labels may be `0/1` (where `1` means phishing) or common text labels such as
`legitimate` and `phishing`. Unknown labels are rejected.

## Run the prediction API (Step 2)

After training has created `artifacts/model.joblib`, start the service from the
project root:

```bash
python -m phishguard.api
```

Open <http://127.0.0.1:8000/docs> for the interactive API page. You can also
check the service with:

```bash
curl http://127.0.0.1:8000/health
```

Submit a URL for classification:

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://secure-login.example.invalid/verify"}'
```

The service extracts the same features used in training, loads the saved model,
and returns the predicted class and confidence. It never visits the submitted
URL.

For the web frontend, open <http://127.0.0.1:8000/> and enter a URL in the
form. The Jinja2 page displays the prediction and confidence.

## Run with Docker

Make sure the trained model exists at `artifacts/model.joblib`, then build and
start the service from the project root:

```bash
docker compose up --build
```

Open <http://127.0.0.1:8000/> for the frontend. The API is available at
<http://127.0.0.1:8000/docs>, and the health endpoint is:

```bash
curl http://127.0.0.1:8000/health
```

Stop the service with:

```bash
docker compose down
```

The container includes the trained model and mounts the local `artifacts/`
directory read-only. The raw dataset and local virtual environment are excluded
from the image.

## Tests

```bash
pytest -q
```

## Output artifacts

- `model.joblib`: fitted scaler and Random Forest pipeline.
- `metadata.json`: feature list, dataset source, split seed, and evaluation metrics.
