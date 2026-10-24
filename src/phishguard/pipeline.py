"""Train and evaluate the Step 1 baseline model."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (confusion_matrix, f1_score, precision_score,
                             recall_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .data import UCI_PHIUSIIL_URL, download_uci_dataset, load_csv, validate_and_select
from .features import FEATURE_NAMES, build_feature_frame


def run_pipeline(source: Path, output_dir: Path, test_size: float = 0.2, random_state: int = 42) -> dict:
    data = load_csv(source)
    # PhiUSIIL defines 0=phishing and 1=legitimate. The local fixture uses
    # the conventional 0=legitimate and 1=phishing mapping.
    is_phiusiil = {str(column).strip().lower() for column in data.columns} >= {"url", "label", "filename"}
    urls, labels = validate_and_select(data, positive_label="0" if is_phiusiil else None)
    features = build_feature_frame(urls)
    x_train, x_test, y_train, y_test = train_test_split(
        features, labels, test_size=test_size, random_state=random_state, stratify=labels
    )
    model = Pipeline([
        ("scale", StandardScaler()),
        ("classifier", RandomForestClassifier(n_estimators=150, random_state=random_state, class_weight="balanced")),
    ])
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    tn, fp, fn, tp = confusion_matrix(y_test, predictions, labels=[0, 1]).ravel()
    metrics = {
        "precision": float(precision_score(y_test, predictions, zero_division=0)),
        "recall": float(recall_score(y_test, predictions, zero_division=0)),
        "f1": float(f1_score(y_test, predictions, zero_division=0)),
        "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
        "false_negative_rate": float(fn / max(1, fn + tp)),
        "n_samples": int(len(labels)),
        "n_test_samples": int(len(y_test)),
        "positive_label": "phishing",
        "source_label_mapping": "0=phishing, 1=legitimate" if is_phiusiil else "1=phishing, 0=legitimate",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_dir / "model.joblib")
    metadata = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_source": UCI_PHIUSIIL_URL if source.suffix == ".zip" else str(source),
        "feature_names": FEATURE_NAMES,
        "model": "StandardScaler + RandomForestClassifier",
        "random_state": random_state,
        "metrics": metrics,
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="Optional CSV or ZIP dataset path")
    parser.add_argument("--download", action="store_true", help="Download the UCI archive before training")
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    args = parser.parse_args()
    source = args.source
    if args.download:
        source = Path("data/raw/phius iil.zip".replace(" ", ""))
        download_uci_dataset(source)
    elif source is None:
        raw_files = sorted([*Path("data/raw").glob("*.csv"), *Path("data/raw").glob("*.zip")])
        source = raw_files[0] if raw_files else Path("data/sample/phishing_urls.csv")
    metadata = run_pipeline(source, args.output_dir)
    print(json.dumps(metadata["metrics"], indent=2))


if __name__ == "__main__":
    main()
