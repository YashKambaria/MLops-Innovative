from phishguard.features import FEATURE_NAMES, build_feature_frame, extract_url_features


def test_feature_extraction_is_offline_and_stable():
    features = extract_url_features("https://example.com/a/b?q=1#top")
    assert set(features) == set(FEATURE_NAMES)
    assert features["has_https"] == 1
    assert features["path_depth"] == 2
    assert features["has_query"] == 1
    assert features["has_fragment"] == 1


def test_feature_frame_shape():
    frame = build_feature_frame(__import__("pandas").Series(["example.com", "192.0.2.1/login"]))
    assert list(frame.columns) == FEATURE_NAMES
    assert frame.shape == (2, len(FEATURE_NAMES))
