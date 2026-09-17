from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from src.sync import check_gcloud_auth, sync_projects


def test_sync_projects_parses_json(tmp_path, monkeypatch):
    monkeypatch.setenv("alfred_workflow_data", str(tmp_path))
    monkeypatch.setattr("shutil.which", lambda cmd: "/usr/local/bin/gcloud")
    monkeypatch.setattr("src.sync.check_gcloud_auth", lambda: (True, "test@example.com"))

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = json.dumps([
        {"projectId": "proj-1", "name": "Project One", "projectNumber": "1001"},
        {"projectId": "proj-2", "name": "Project Two", "projectNumber": "1002"},
    ])
    mock_proc.stderr = ""

    with patch("subprocess.run", return_value=mock_proc):
        projects = sync_projects()

    assert len(projects) == 2
    assert projects[0]["id"] == "proj-1"
    assert projects[0]["name"] == "Project One"
    assert projects[0]["number"] == 1001

    cache_file = tmp_path / "google-projects.json"
    assert cache_file.exists()
    saved = json.loads(cache_file.read_text())
    assert len(saved) == 2


def test_check_gcloud_auth_not_logged_in(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda cmd: "/usr/local/bin/gcloud")

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = ""  # No active account

    with patch("subprocess.run", return_value=mock_proc):
        is_authed, msg = check_gcloud_auth()

    assert not is_authed
    assert "Not authenticated" in msg


def test_sync_projects_raises_when_not_authenticated(tmp_path, monkeypatch):
    monkeypatch.setenv("alfred_workflow_data", str(tmp_path))
    monkeypatch.setattr("shutil.which", lambda cmd: "/usr/local/bin/gcloud")
    monkeypatch.setattr("src.sync.check_gcloud_auth", lambda: (False, "Not authenticated."))

    with pytest.raises(RuntimeError, match="Not authenticated"):
        sync_projects()


def test_sync_projects_detects_session_expiry(tmp_path, monkeypatch):
    monkeypatch.setenv("alfred_workflow_data", str(tmp_path))
    monkeypatch.setattr("shutil.which", lambda cmd: "/usr/local/bin/gcloud")
    monkeypatch.setattr("src.sync.check_gcloud_auth", lambda: (True, "test@example.com"))

    mock_proc = MagicMock()
    mock_proc.returncode = 1
    mock_proc.stdout = ""
    mock_proc.stderr = "ERROR: (gcloud.projects.list) Reauthentication required. Please run 'gcloud auth login'."

    with patch("subprocess.run", return_value=mock_proc), pytest.raises(RuntimeError, match="gcloud session expired"):
        sync_projects()
