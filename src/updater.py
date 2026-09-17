from __future__ import annotations

import json
import os
import plistlib
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any

REPO = "ndpete/alfred-gcloud-workflow"
BUNDLE_ID = "com.github.ndpete.alfred-gcloud-workflow"


def get_data_dir() -> Path:
    env_dir = os.environ.get("alfred_workflow_data")
    if env_dir:
        path = Path(env_dir)
    else:
        path = Path.home() / "Library" / "Application Support" / "Alfred" / "Workflow Data" / BUNDLE_ID
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_cache_dir() -> Path:
    env_dir = os.environ.get("alfred_workflow_cache")
    if env_dir:
        path = Path(env_dir)
    else:
        path = Path.home() / "Library" / "Caches" / "com.runningwithcrayons.Alfred" / "Workflow Data" / BUNDLE_ID
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_current_version() -> str:
    env_ver = os.environ.get("alfred_workflow_version")
    if env_ver:
        return env_ver.strip()

    info_plist = Path(__file__).parent.parent / "info.plist"
    if info_plist.exists():
        try:
            with open(info_plist, "rb") as f:
                data = plistlib.load(f)
                ver = data.get("version")
                if ver:
                    return str(ver).strip()
        except Exception:
            pass
    return "0.0.0"


def parse_version(v: str) -> tuple[int, ...]:
    clean = v.lstrip("v").strip().split("-")[0]
    parts: list[int] = []
    for part in clean.split("."):
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def is_newer_version(latest: str, current: str) -> bool:
    return parse_version(latest) > parse_version(current)


def get_update_state_path() -> Path:
    return get_cache_dir() / "update_state.json"


def check_for_updates(force: bool = False) -> dict[str, Any] | None:
    state_file = get_update_state_path()
    now = time.time()

    if not force and state_file.exists():
        try:
            with open(state_file) as f:
                state = json.load(f)
            last_checked = float(state.get("last_checked", 0))
            if now - last_checked < 86400:  # Check once per 24 hours
                return state.get("update_info")
        except Exception:
            pass

    release_info: dict[str, Any] | None = None

    # Try gh CLI first
    try:
        proc = subprocess.run(
            ["gh", "release", "view", "--repo", REPO, "--json", "tagName,url,assets"],
            capture_output=True,
            text=True,
            timeout=5.0,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            release_info = json.loads(proc.stdout)
    except Exception:
        pass

    # Fallback to GitHub REST API
    if not release_info:
        try:
            url = f"https://api.github.com/repos/{REPO}/releases/latest"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": f"alfred-gcloud-shortcuts/{get_current_version()}"},
            )
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                data = json.loads(resp.read().decode())
                release_info = {
                    "tagName": data.get("tag_name"),
                    "url": data.get("html_url"),
                    "assets": [
                        {
                            "name": a.get("name"),
                            "url": a.get("browser_download_url"),
                        }
                        for a in data.get("assets", [])
                    ],
                }
        except Exception:
            pass

    update_info: dict[str, Any] | None = None
    if release_info and release_info.get("tagName"):
        latest_tag = str(release_info["tagName"]).lstrip("v")
        current_ver = get_current_version()
        if is_newer_version(latest_tag, current_ver):
            download_url = ""
            for asset in release_info.get("assets", []):
                name = asset.get("name", "")
                if name.endswith(".alfredworkflow"):
                    download_url = asset.get("url", "")
                    break
            update_info = {
                "version": latest_tag,
                "release_url": release_info.get("url", f"https://github.com/{REPO}/releases/latest"),
                "download_url": download_url,
            }

    try:
        with open(state_file, "w") as f:
            json.dump({"last_checked": now, "update_info": update_info}, f)
    except Exception:
        pass

    return update_info


def trigger_background_update_check() -> None:
    state_file = get_update_state_path()
    if state_file.exists():
        try:
            with open(state_file) as f:
                state = json.load(f)
            if time.time() - float(state.get("last_checked", 0)) < 86400:
                return
        except Exception:
            pass

    subprocess.Popen(
        ["/usr/bin/python3", "-c", "from src.updater import check_for_updates; check_for_updates(force=True)"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def notify(message: str, title: str = "Google Cloud") -> None:
    """Display a native desktop notification using Alfred's workflow notification (with Google Cloud icon)."""
    escaped = message.replace('"', '\\"')
    script = (
        f'tell application id "com.runningwithcrayons.Alfred" to '
        f'run trigger "notify" in workflow "{BUNDLE_ID}" '
        f'with argument "{escaped}"'
    )
    try:
        res = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            return
    except OSError:
        pass

    fallback = (
        f'tell application id "com.runningwithcrayons.Alfred" to '
        f'display notification "{escaped}" with title "{title}"'
    )
    try:
        subprocess.run(
            ["osascript", "-e", fallback],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        pass


def download_and_install_update() -> tuple[bool, str]:
    """Download the latest .alfredworkflow asset and prompt Alfred to install it."""
    state_file = get_update_state_path()
    update_info = None

    if state_file.exists():
        try:
            with open(state_file) as f:
                state = json.load(f)
            update_info = state.get("update_info")
        except Exception:
            pass

    if not update_info or not update_info.get("download_url"):
        update_info = check_for_updates(force=True)

    if not update_info or not update_info.get("download_url"):
        notify("No update available or download asset missing.")
        return False, "No update available."

    download_url = update_info["download_url"]
    latest_ver = update_info["version"]

    notify(f"Downloading update v{latest_ver}...")

    dest_dir = get_cache_dir()
    dest_file = dest_dir / "alfred-gcloud-workflow.alfredworkflow"

    req = urllib.request.Request(
        download_url,
        headers={"User-Agent": f"alfred-gcloud-workflow/{get_current_version()}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30.0) as resp, open(dest_file, "wb") as f:
            f.write(resp.read())
    except Exception as e:
        msg = f"Failed to download update: {e}"
        notify(msg)
        return False, msg

    # Clear update flags from cache
    try:
        if state_file.exists():
            with open(state_file) as f:
                state = json.load(f)
            state["update_info"] = None
            with open(state_file, "w") as f:
                json.dump(state, f)
    except Exception:
        pass

    notify(f"Update v{latest_ver} ready. Opening Alfred to install...")

    # Launch native Alfred workflow updater dialog
    subprocess.run(["open", str(dest_file)], check=False)
    return True, f"Opened installer for v{latest_ver}"


def run_manual_update_check() -> tuple[bool, str]:
    """Manually force check for updates and notify the user."""
    notify("Checking GitHub for updates...")
    update_info = check_for_updates(force=True)
    cur_ver = get_current_version()
    if update_info and update_info.get("version"):
        latest = update_info["version"]
        msg = f"Update available: v{latest}! Type 'g' to install."
        notify(msg)
        return True, msg
    else:
        msg = f"Workflow is up to date (v{cur_ver})."
        notify(msg)
        return False, msg


