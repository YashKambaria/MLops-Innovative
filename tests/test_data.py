import pandas as pd
import pytest

from phishguard.data import validate_and_select


def test_labels_are_validated_and_normalized():
    urls, labels = validate_and_select(pd.DataFrame({"url": ["a.example", "bad.invalid"], "label": ["legitimate", "phishing"]}))
    assert urls.tolist() == ["a.example", "bad.invalid"]
    assert labels.tolist() == [0, 1]


def test_unknown_labels_fail():
    with pytest.raises(ValueError, match="Unknown label"):
        validate_and_select(pd.DataFrame({"url": ["a.example", "b.example"], "label": ["safe", "mystery"]}))
