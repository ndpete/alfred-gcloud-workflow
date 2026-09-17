import json

from src.projects import run_projects


def test_system_commands():
    fb_ver = run_projects("-version")
    items_ver = fb_ver.to_dict()["items"]
    assert len(items_ver) >= 1
    assert any("Workflow version" in i["title"] for i in items_ver)

    fb_ref = run_projects("-refresh")
    items_ref = fb_ref.to_dict()["items"]
    assert len(items_ref) >= 1
    assert any("Refresh projects" in i["title"] for i in items_ref)


def test_empty_cache_shows_banner(tmp_path, monkeypatch):
    monkeypatch.setenv("alfred_workflow_data", str(tmp_path))
    monkeypatch.setattr("src.projects.check_gcloud_auth", lambda: (True, "test@example.com"))
    fb = run_projects("")
    items = fb.to_dict()["items"]
    assert len(items) == 1
    assert "No projects cached" in items[0]["title"]


def test_empty_cache_shows_unauthenticated_banner(tmp_path, monkeypatch):
    monkeypatch.setenv("alfred_workflow_data", str(tmp_path))
    monkeypatch.setattr("src.projects.check_gcloud_auth", lambda: (False, "Not logged in"))
    fb = run_projects("")
    items = fb.to_dict()["items"]
    assert len(items) == 1
    assert "not authenticated" in items[0]["title"].lower()


def test_project_search(tmp_path, monkeypatch):
    monkeypatch.setenv("alfred_workflow_data", str(tmp_path))
    cache_file = tmp_path / "google-projects.json"
    cache_file.write_text(json.dumps([
        {"name": "my-cool-project-prod", "id": "my-cool-project-prod", "number": 12345},
        {"name": "test-sandbox", "id": "test-sandbox", "number": 67890},
    ]))

    fb = run_projects("cool")
    items = fb.to_dict()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "my-cool-project-prod"
    assert items[0]["arg"] == "my-cool-project-prod"
