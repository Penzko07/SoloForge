#!/usr/bin/env python3
"""Create metadata-only SoloForge records from a public GitHub repository.

This importer records names, URLs, and file counts. It intentionally does not
download or bundle trainer logic.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "registry" / "sources"
ID_RE = re.compile(r"[^a-z0-9]+")


def slug(value: str) -> str:
    cleaned = ID_RE.sub("-", value.lower()).strip("-")
    return cleaned or "source"


def github_json(url: str, token: str | None) -> Any:
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def repo_metadata(owner: str, repo: str, token: str | None) -> dict[str, Any]:
    repo_url = f"https://api.github.com/repos/{owner}/{repo}"
    tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"

    repo_info = github_json(repo_url, token)
    tree_info = github_json(tree_url, token)
    items = tree_info.get("tree", [])
    ct_files = [item for item in items if item.get("type") == "blob" and item.get("path", "").lower().endswith(".ct")]

    license_info = repo_info.get("license") or {}
    license_name = license_info.get("spdx_id") or license_info.get("name") or "unknown"

    return {
        "schemaVersion": "0.1.0",
        "id": slug(f"{owner}-{repo}"),
        "kind": "source",
        "name": repo_info.get("full_name", f"{owner}/{repo}"),
        "source": {
            "name": repo_info.get("full_name", f"{owner}/{repo}"),
            "url": repo_info.get("html_url", f"https://github.com/{owner}/{repo}"),
            "importMode": "metadata-only",
            "license": license_name,
            "lastChecked": date.today().isoformat(),
        },
        "safety": {
            "singleplayerOnly": True,
            "offlineOnly": True,
            "multiplayerBlocked": True,
            "reviewStatus": "requiresManualReview",
        },
        "attribution": {
            "required": True,
            "text": f"Metadata references {owner}/{repo}. Found {len(ct_files)} Cheat Engine table file path(s); table redistribution requires license and safety review.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repository", help="GitHub repository in owner/name form")
    parser.add_argument("--token", default=None, help="Optional GitHub token")
    parser.add_argument("--output-dir", default=str(OUT_DIR))
    args = parser.parse_args()

    if "/" not in args.repository:
        print("repository must be in owner/name form", file=sys.stderr)
        return 2

    owner, repo = args.repository.split("/", 1)
    try:
        record = repo_metadata(owner, repo, args.token)
    except urllib.error.URLError as exc:
        print(f"GitHub request failed: {exc}", file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{record['id']}.json"
    output_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
