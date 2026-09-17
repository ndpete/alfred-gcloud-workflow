from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from src.updater import (
    check_for_updates,
    download_and_install_update,
    is_newer_version,
    notify,
    parse_version,
)


def test_parse_version():
    assert parse_version("v2.2.0") == (2, 2, 0)
    assert parse_version("2.3.1-rc1") == (2, 3, 1)
    assert parse_version("1.0") == (1, 0)


def test_is_newer_version():
    assert is_newer_version("2.3.0", "2.2.0")
    assert is_newer_version("3.0.0", "2.9.9")
    assert not is_newer_version("2.2.0", "2.2.0")
    assert not is_newer_version("2.1.0", "2.2.0")


def test_check_for_updates_detects_new_release(tmp_path, monkeypatch):
    monkeypatch.setenv("alfred_workflow_cache", str(tmp_path))
    monkeypatch.setattr("src.updater.get_current_version", lambda: "0.1.0")

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = json.dumps({
        "tagName": "v0.2.0",
        "url": "https://github.com/ndpete/alfred-gcloud-workflow/releases/tag/v0.2.0",
        "assets": [
            {
                "name": "alfred-gcloud-workflow.alfredworkflow",
                "url": "https://github.com/ndpete/.../download/alfred-gcloud-workflow.alfredworkflow",
            }
        ],
    })

    with patch("subprocess.run", return_value=mock_proc):
        update = check_for_updates(force=True)

    assert update is not None
    assert update["version"] == "0.2.0"
    assert update["download_url"].endswith(".alfredworkflow")


def test_download_and_install_update(tmp_path, monkeypatch):
    monkeypatch.setenv("alfred_workflow_cache", str(tmp_path))
    state_file = tmp_path / "update_state.json"
    state_file.write_text(json.dumps({
        "last_checked": 1000,
        "update_info": {
            "version": "2.3.0",
            "download_url": "https://example.com/workflow.alfredworkflow",
        },
    }))

    mock_resp = MagicMock()
    mock_resp.__enter__.return_value.read.return_value = b"PKmockzipcontent"

    mock_open_proc = MagicMock()

    with (
        patch("urllib.request.urlopen", return_value=mock_resp),
        patch("subprocess.run", return_value=mock_open_proc) as mock_run,
    ):
        ok, msg = download_and_install_update()

    assert ok
    assert "2.3.0" in msg
    # Verify open was called with downloaded workflow file
    opened_calls = [c for c in mock_run.call_args_list if c[0][0][0] == "open"]
    assert len(opened_calls) == 1
    assert str(opened_calls[0][0][0][1]).endswith(".alfredworkflow")


def test_notify(monkeypatch):
    with patch("subprocess.run") as mock_run:
        notify("Test notification")
    assert mock_run.called
