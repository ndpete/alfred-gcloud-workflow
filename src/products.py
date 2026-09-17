from __future__ import annotations

import argparse
import json
import os
import urllib.parse
from pathlib import Path

from src.matching import fuzzy_match
from src.models import Feedback, Item


def load_products() -> list[dict[str, str]]:
    # Look in current working directory or relative to src/
    paths = [
        Path.cwd() / "products.json",
        Path(__file__).parent.parent / "products.json",
    ]
    for p in paths:
        if p.exists():
            try:
                with open(p, encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
            except Exception:
                pass
    return []


def append_url_parameters(url_str: str, params: dict[str, str]) -> str:
    parsed = urllib.parse.urlsplit(url_str)
    query_dict = dict(urllib.parse.parse_qsl(parsed.query, keep_blank_values=True))
    for k, v in params.items():
        if v:
            query_dict[k] = v
    new_query = urllib.parse.urlencode(query_dict)
    return urllib.parse.urlunsplit((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        new_query,
        parsed.fragment,
    ))


def run_products(query: str, project: str) -> Feedback:
    fb = Feedback()
    products = load_products()
    q = query.strip()

    authuser = os.environ.get("authuser", "").strip()
    extra_params: dict[str, str] = {}
    if authuser:
        extra_params["authuser"] = authuser

    scored_products: list[tuple[int, dict[str, str], str, str]] = []
    for p in products:
        name = p.get("name", "")
        raw_url = p.get("url", "")
        formatted_url = raw_url.replace("{{.ProjectID}}", project)
        final_url = append_url_parameters(formatted_url, extra_params) if extra_params else formatted_url

        if not q:
            scored_products.append((0, p, final_url, raw_url))
            continue

        matched, score = fuzzy_match(q, name)
        if matched:
            scored_products.append((score, p, final_url, raw_url))

    if q:
        scored_products.sort(key=lambda x: x[0], reverse=True)

    for _, p, final_url, raw_url in scored_products[:40]:
        name = p.get("name", "")
        fb.add_item(
            Item(
                title=name,
                subtitle=project,
                arg=final_url,
                uid=raw_url,
                valid=True,
            )
        )

    return fb


def main() -> None:
    parser = argparse.ArgumentParser(description="Google Cloud Products search")
    parser.add_argument("-query", "--query", default="", help="Search query")
    parser.add_argument("-project", "--project", default="", help="Active GCP project ID")
    args, unknown = parser.parse_known_args()

    # Fallback to positional arguments if flags were not used
    query = args.query
    project = args.project
    if not query and unknown:
        query = unknown[0]

    fb = run_products(query, project)
    fb.emit()


if __name__ == "__main__":
    main()
