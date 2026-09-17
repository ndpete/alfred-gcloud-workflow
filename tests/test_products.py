from src.products import append_url_parameters, run_products


def test_append_url_parameters():
    url = "https://console.cloud.google.com/run?project=my-proj"
    res = append_url_parameters(url, {"authuser": "1"})
    assert "authuser=1" in res
    assert "project=my-proj" in res


def test_run_products_substitution():
    fb = run_products("Cloud Run", "my-test-proj")
    items = fb.to_dict()["items"]
    assert len(items) > 0
    top = items[0]
    assert "Cloud Run" in top["title"]
    assert "my-test-proj" in top["arg"]
    assert top["subtitle"] == "my-test-proj"


def test_run_products_empty_query():
    fb = run_products("", "my-test-proj")
    items = fb.to_dict()["items"]
    assert len(items) > 0
