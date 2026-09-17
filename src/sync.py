from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from src.models import Feedback, Item
from src.updater import get_data_dir


def get_cache_paths() -> tuple[Path, Path]:
    data_dir = get_data_dir()
    return data_dir / "google-projects.json", data_dir / "google-projects"


def get_sync_lock_path() -> Path:
    return get_data_dir() / "sync.lock"


def is_sync_in_progress() -> bool:
    lock_file = get_sync_lock_path()
    if not lock_file.exists():
        return False

    try:
        data = json.loads(lock_file.read_text())
        pid = data.get("pid")
        started_at = data.get("started_at", 0)

        # Stale lock cleanup (if older than 3 minutes)
        if time.time() - started_at > 180:
            lock_file.unlink(missing_ok=True)
            return False

        if pid:
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                lock_file.unlink(missing_ok=True)
                return False
        return True
    except Exception:
        lock_file.unlink(missing_ok=True)
        return False


def check_gcloud_auth() -> tuple[bool, str]:
    """Check if gcloud is installed and has an active authenticated account."""
    gcloud_bin = shutil.which("gcloud")
    if not gcloud_bin:
        return False, "Google Cloud CLI ('gcloud') not found in PATH."

    try:
        proc = subprocess.run(
            [gcloud_bin, "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"],
            capture_output=True,
            text=True,
            timeout=3.0,
            check=False,
        )
        account = proc.stdout.strip()
        if proc.returncode == 0 and account:
            return True, account
        return False, "Not authenticated. Run 'gcloud auth login' in Terminal."
    except Exception as e:
        return False, f"Auth check failed: {e}"


def sync_projects() -> list[dict[str, Any]]:
    gcloud_bin = shutil.which("gcloud")
    if not gcloud_bin:
        raise RuntimeError("Google Cloud CLI ('gcloud') is not found in PATH.")

    # Check active login before calling API
    is_authed, auth_msg = check_gcloud_auth()
    if not is_authed:
        raise RuntimeError(auth_msg)

    lock_file = get_sync_lock_path()
    try:
        lock_file.parent.mkdir(parents=True, exist_ok=True)
        lock_file.write_text(json.dumps({"pid": os.getpid(), "started_at": time.time()}))

        cmd = [
            gcloud_bin,
            "projects",
            "list",
            "--format=json(projectId,name,projectNumber)",
        ]

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        if proc.returncode != 0:
            err_msg = proc.stderr.strip() or proc.stdout.strip() or f"gcloud exited with code {proc.returncode}"
            lower_err = err_msg.lower()
            if "reauth" in lower_err or "credential" in lower_err or "login" in lower_err or "unauthenticated" in lower_err:
                raise RuntimeError("gcloud session expired. Run 'gcloud auth login' in Terminal.")
            raise RuntimeError(err_msg)

        raw_projects = json.loads(proc.stdout)
        normalized: list[dict[str, Any]] = []
        for p in raw_projects:
            proj_id = p.get("projectId") or p.get("id", "")
            name = p.get("name") or proj_id
            try:
                num = int(p.get("projectNumber") or p.get("number") or 0)
            except ValueError:
                num = 0

            if proj_id:
                normalized.append({
                    "name": name,
                    "id": proj_id,
                    "number": num,
                })

        # Save to data directory
        path_json, path_raw = get_cache_paths()
        with open(path_json, "w") as f:
            json.dump(normalized, f, indent=2)

        with open(path_raw, "w") as f:
            json.dump(normalized, f)

        return normalized
    finally:
        lock_file.unlink(missing_ok=True)


def sync_feedback() -> Feedback:
    fb = Feedback()
    try:
        projects = sync_projects()
        fb.add_item(
            Item(
                title=f"✓ Synced {len(projects)} projects successfully",
                subtitle="Google Cloud projects cached. Press ⏎ to open Console or start searching with 'g'",
                arg="https://console.cloud.google.com",
                valid=True,
            )
        )
    except Exception as e:
        err_msg = str(e)
        fb.add_item(
            Item(
                title=f"⚠️ {err_msg}",
                subtitle="Run 'gcloud auth login' in Terminal or check network connection",
                arg="https://cloud.google.com/sdk/gcloud/reference/auth/login",
                valid=True,
            )
        )
    return fb


def main() -> None:
    if "--alfred" in sys.argv:
        fb = sync_feedback()
        sys.stdout.write(fb.to_json() + "\n")
        return

    try:
        projects = sync_projects()
        sys.stdout.write(f"✓ Synced {len(projects)} projects successfully.\n")
    except Exception as e:
        # Write to stdout so Alfred displays the notification banner to the user
        err_str = str(e)
        sys.stdout.write(f"{err_str}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
