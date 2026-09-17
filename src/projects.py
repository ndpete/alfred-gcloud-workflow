from __future__ import annotations

import json
import shutil
import subprocess
import sys
from typing import Any

from src.matching import fuzzy_match
from src.models import Feedback, Item
from src.sync import check_gcloud_auth
from src.updater import (
    REPO,
    check_for_updates,
    get_current_version,
    get_data_dir,
    trigger_background_update_check,
)


def load_cached_projects() -> list[dict[str, Any]]:
    data_dir = get_data_dir()
    for fname in ("google-projects.json", "google-projects"):
        fpath = data_dir / fname
        if fpath.exists():
            try:
                with open(fpath) as f:
                    data = json.load(f)
                    if isinstance(data, list) and data:
                        return data
            except Exception:
                pass
    return []


def get_gcloud_version() -> str | None:
    gcloud_bin = shutil.which("gcloud")
    if not gcloud_bin:
        return None
    try:
        proc = subprocess.run(
            [gcloud_bin, "version"],
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            # First line is typically "Google Cloud SDK 510.0.0"
            first_line = proc.stdout.strip().splitlines()[0]
            parts = first_line.split()
            if len(parts) >= 4 and parts[0] == "Google" and parts[1] == "Cloud":
                return parts[3]
            return first_line
    except Exception:
        pass
    return None


def run_projects(query: str) -> Feedback:
    fb = Feedback()
    q = query.strip()
    q_lower = q.lower()

    # Trigger background check for workflow updates once every 24h
    trigger_background_update_check()
    update_info = check_for_updates()

    # System / Utility Commands
    if q_lower.startswith("-") or q_lower in ("refresh", "update", "version", "check", "auth", "login"):
        # Auth command / status
        is_authed, auth_info = check_gcloud_auth()
        if is_authed:
            fb.add_item(
                Item(
                    title=f"✓ Logged in as {auth_info}",
                    subtitle="Active Google Cloud CLI account",
                    arg="https://console.cloud.google.com",
                    autocomplete="-auth",
                    valid=True,
                )
            )
        else:
            fb.add_item(
                Item(
                    title="⚠️ Not authenticated with gcloud",
                    subtitle="Run 'gcloud auth login' in Terminal to authenticate",
                    arg="https://cloud.google.com/sdk/gcloud/reference/auth/login",
                    autocomplete="-auth",
                    valid=True,
                )
            )

        # Refresh projects option
        fb.add_item(
            Item(
                title="Refresh projects",
                subtitle="Update cached GCP projects via gcloud CLI",
                arg="-refresh",
                autocomplete="-refresh",
                valid=False,
            )
        )

        # Update command option
        if update_info:
            update_title = f"🚀 Update available (v{update_info['version']})!"
            update_sub = "Press ⏎ to download and install update via Alfred"
            update_arg = "cmd:update"
        else:
            update_title = "Check for updates"
            update_sub = "Check GitHub for new workflow releases"
            update_arg = f"https://github.com/{REPO}/releases/latest"

        fb.add_item(
            Item(
                title=update_title,
                subtitle=update_sub,
                arg=update_arg,
                autocomplete="-update",
                valid=True,
            )
        )

        # Version command option
        cur_ver = get_current_version()
        gcloud_ver = get_gcloud_version()
        gcloud_desc = f" • gcloud v{gcloud_ver}" if gcloud_ver else ""
        fb.add_item(
            Item(
                title=f"Workflow version: v{cur_ver}",
                subtitle=f"Google Cloud Shortcuts{gcloud_desc}",
                arg=f"https://github.com/{REPO}",
                autocomplete="-version",
                valid=True,
            )
        )

        if q_lower not in ("-", ""):
            # Filter commands if user typed something specific (e.g. "-up")
            filtered_items: list[Item] = []
            for item in fb.items:
                matched, _ = fuzzy_match(q_lower.lstrip("-"), item.title.lower())
                if matched:
                    filtered_items.append(item)
            if filtered_items:
                fb.items = filtered_items

        return fb

    # Normal Project Search
    projects = load_cached_projects()
    if not projects:
        is_authed, auth_info = check_gcloud_auth()
        if not is_authed:
            fb.add_item(
                Item(
                    title="⚠️ Not authenticated with Google Cloud",
                    subtitle="Run 'gcloud auth login' in Terminal before refreshing projects",
                    arg="https://cloud.google.com/sdk/gcloud/reference/auth/login",
                    valid=True,
                )
            )
        else:
            fb.add_item(
                Item(
                    title="No projects cached",
                    subtitle="Run 'g-refresh' or type '-refresh' to fetch your GCP projects",
                    arg="-refresh",
                    autocomplete="-refresh",
                    valid=False,
                )
            )
        return fb

    # Show update banner at top of empty search when update is available
    if not q and update_info:
        fb.add_item(
            Item(
                title=f"🚀 Update available (v{update_info['version']})!",
                subtitle="Press ⏎ to download and install update via Alfred",
                arg="cmd:update",
                valid=True,
            )
        )

    scored_projects: list[tuple[int, dict[str, Any]]] = []
    for p in projects:
        if not q:
            scored_projects.append((0, p))
            continue

        p_id = p.get("id", "")
        p_name = p.get("name", "")

        m_id, score_id = fuzzy_match(q, p_id)
        m_name, score_name = fuzzy_match(q, p_name)

        if m_id or m_name:
            best_score = max(score_id, score_name)
            scored_projects.append((best_score, p))

    if q:
        scored_projects.sort(key=lambda x: x[0], reverse=True)

    for _, p in scored_projects[:30]:
        name = p.get("name") or p.get("id", "")
        proj_id = p.get("id", "")
        fb.add_item(
            Item(
                title=name,
                subtitle=proj_id,
                arg=proj_id,
                uid=proj_id,
                valid=True,
            )
        )

    return fb


def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else ""
    fb = run_projects(query)
    fb.emit()


if __name__ == "__main__":
    main()
