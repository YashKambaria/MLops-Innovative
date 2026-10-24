import json
from pathlib import Path

from phishguard.pipeline import run_pipeline


def test_pipeline_writes_reproducible_artifacts(tmp_path: Path):
    metadata = run_pipeline(Path("data/sample/phishing_urls.csv"), tmp_path)
    assert (tmp_path / "model.joblib").exists()
    saved = json.loads((tmp_path / "metadata.json").read_text())
    assert saved["metrics"] == metadata["metrics"]
    assert 0 <= saved["metrics"]["false_negative_rate"] <= 1


def test_phiusiil_numeric_labels_map_zero_to_phishing(tmp_path: Path):
    import pandas as pd
    from phishguard.data import validate_and_select

    urls, labels = validate_and_select(
        pd.DataFrame({"URL": ["bad.invalid", "good.example"], "label": [0, 1], "FILENAME": ["a", "b"]}),
        positive_label="0",
    )
    assert urls.tolist() == ["bad.invalid", "good.example"]
    assert labels.tolist() == [1, 0]
