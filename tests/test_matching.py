from src.matching import fuzzy_match


def test_fuzzy_match_exact():
    matched, score = fuzzy_match("cloud run", "cloud run")
    assert matched is True
    assert score >= 500


def test_fuzzy_match_prefix():
    matched, score = fuzzy_match("cloud", "cloud storage")
    assert matched is True
    assert score >= 300


def test_fuzzy_match_delimiter():
    matched, score = fuzzy_match("prod", "ut-udot-broadband-prod")
    assert matched is True
    assert score >= 200


def test_fuzzy_match_subsequence():
    # "bql" matches "bigquery"
    matched, score = fuzzy_match("bqu", "bigquery")
    assert matched is True
    assert score > 0


def test_fuzzy_match_negative():
    matched, score = fuzzy_match("xyz", "bigquery")
    assert matched is False
    assert score == 0


def test_fuzzy_match_empty_query():
    matched, score = fuzzy_match("", "any target")
    assert matched is True
    assert score == 0
