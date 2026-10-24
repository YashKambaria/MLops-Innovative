"""Dataset acquisition and validation for PhishGuard."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd

UCI_PHIUSIIL_URL = "https://archive.ics.uci.edu/static/public/967/phiusiil+phishing+url+dataset.zip"


def download_uci_dataset(destination: Path, source_url: str = UCI_PHIUSIIL_URL) -> Path:
    """Download the UCI archive, without dereferencing values inside the data."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(source_url, headers={"User-Agent": "PhishGuard/0.1"})
    with urlopen(request, timeout=60) as response:  # noqa: S310 - explicit dataset source
        payload = response.read()
    destination.write_bytes(payload)
    return destination


def load_csv(source: Path) -> pd.DataFrame:
    """Load a CSV or the first CSV in a ZIP archive as inert tabular data."""
    if source.suffix.lower() == ".zip":
        with zipfile.ZipFile(source) as archive:
            csv_names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
            if not csv_names:
                raise ValueError(f"No CSV found in {source}")
            with archive.open(csv_names[0]) as handle:
                return pd.read_csv(handle)
    return pd.read_csv(source)


def _find_column(columns: list[str], candidates: tuple[str, ...]) -> str:
    normalized = {column.strip().lower(): column for column in columns}
    for candidate in candidates:
        if candidate in normalized:
            return normalized[candidate]
    raise ValueError(f"Could not find one of {candidates}; columns were {columns}")


def validate_and_select(data: pd.DataFrame, positive_label: str | None = None) -> tuple[pd.Series, pd.Series]:
    """Return clean URL and binary phishing-label series.

    String labels accept common names. Numeric labels default to 1=phishing,
    0=legitimate; pass ``positive_label`` to make a source-specific mapping
    explicit.
    """
    url_column = _find_column(list(data.columns), ("url", "uri", "link", "website"))
    label_column = _find_column(list(data.columns), ("label", "class", "target", "status"))
    selected = data[[url_column, label_column]].copy()
    selected[url_column] = selected[url_column].astype("string").str.strip()
    selected = selected.dropna()
    selected = selected[selected[url_column].str.len() > 0]
    raw = selected[label_column]
    if positive_label is not None:
        labels = (raw.astype(str).str.strip().str.lower() == positive_label.lower()).astype(int)
    elif pd.api.types.is_numeric_dtype(raw):
        labels = (raw.astype(float) == 1).astype(int)
    else:
        normalized = raw.astype(str).str.strip().str.lower()
        positive = {"1", "phishing", "malicious", "bad", "fraud", "yes", "true"}
        negative = {"0", "legitimate", "benign", "good", "safe", "no", "false"}
        unknown = sorted(set(normalized) - positive - negative)
        if unknown:
            raise ValueError(f"Unknown label values: {unknown}")
        labels = normalized.isin(positive).astype(int)
    if labels.nunique() != 2:
        raise ValueError("Dataset must contain both phishing and legitimate labels")
    return selected[url_column].reset_index(drop=True), labels.reset_index(drop=True)
