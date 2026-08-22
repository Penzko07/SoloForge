#!/usr/bin/env python3
"""Publish the current committed HEAD through the GitHub Git API.

This is useful when normal `git push` has no local HTTPS credentials. It uses
the token from `SOLOFORGE_GITHUB_TOKEN` or `GITHUB_TOKEN` and does not persist it.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

API_ROOT = "https://api.github.com"


@dataclass(frozen=True)
class GitEntry:
    mode: str
    path: str


def git_output(args: list[str], text: bool = True) -> str | bytes:
    return subprocess.check_output(["git", *args], text=text)


def require_clean_worktree() -> None:
    status = git_output(["status", "--porcelain"])
    if status:
        raise RuntimeError("working tree has uncommitted changes; commit first or pass --allow-dirty")


def local_tree_entries() -> list[GitEntry]:
    raw = git_output(["ls-tree", "-r", "-z", "HEAD"])
    entries: list[GitEntry] = []
    for item in raw.split("\0"):
        if not item:
            continue
        metadata, path = item.split("\t", 1)
        mode, kind, _sha = metadata.split(" ", 2)
        if kind == "blob":
            entries.append(GitEntry(mode=mode, path=path))
    return entries


def local_file_bytes(path: str) -> bytes:
    return git_output(["show", f"HEAD:{path}"], text=False)


def github_request(method: str, endpoint: str, token: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        f"{API_ROOT}{endpoint}",
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API error {exc.code}: {body}") from exc


def remote_branch(repo: str, branch: str, token: str) -> tuple[str, str]:
    ref = github_request("GET", f"/repos/{repo}/git/ref/heads/{branch}", token)
    commit_sha = ref["object"]["sha"]
    commit = github_request("GET", f"/repos/{repo}/git/commits/{commit_sha}", token)
    return commit_sha, commit["tree"]["sha"]


def remote_blob_paths(repo: str, tree_sha: str, token: str) -> set[str]:
    tree = github_request("GET", f"/repos/{repo}/git/trees/{tree_sha}?recursive=1", token)
    return {item["path"] for item in tree.get("tree", []) if item.get("type") == "blob"}


def tree_element(repo: str, entry: GitEntry, token: str) -> dict[str, Any]:
    content = local_file_bytes(entry.path)
    element: dict[str, Any] = {
        "path": entry.path,
        "mode": entry.mode,
        "type": "blob",
    }

    try:
        element["content"] = content.decode("utf-8")
    except UnicodeDecodeError:
        blob = github_request(
            "POST",
            f"/repos/{repo}/git/blobs",
            token,
            {
                "content": base64.b64encode(content).decode("ascii"),
                "encoding": "base64",
            },
        )
        element["sha"] = blob["sha"]

    return element


def create_tree(repo: str, base_tree_sha: str, local_entries: list[GitEntry], delete_paths: set[str], token: str) -> str:
    elements = [tree_element(repo, entry, token) for entry in local_entries]
    elements.extend({"path": path, "mode": "100644", "type": "blob", "sha": None} for path in sorted(delete_paths))
    tree = github_request(
        "POST",
        f"/repos/{repo}/git/trees",
        token,
        {
            "base_tree": base_tree_sha,
            "tree": elements,
        },
    )
    return tree["sha"]


def publish(repo: str, branch: str, message: str, token: str, dry_run: bool) -> str | None:
    local_entries = local_tree_entries()
    remote_commit_sha, remote_tree_sha = remote_branch(repo, branch, token)
    remote_paths = remote_blob_paths(repo, remote_tree_sha, token)
    local_paths = {entry.path for entry in local_entries}
    delete_paths = remote_paths - local_paths

    print(f"Remote {branch}: {remote_commit_sha}")
    print(f"Local files: {len(local_entries)}")
    print(f"Deleted remote files: {len(delete_paths)}")

    if dry_run:
        return None

    tree_sha = create_tree(repo, remote_tree_sha, local_entries, delete_paths, token)
    commit = github_request(
        "POST",
        f"/repos/{repo}/git/commits",
        token,
        {
            "message": message,
            "tree": tree_sha,
            "parents": [remote_commit_sha],
        },
    )
    github_request(
        "PATCH",
        f"/repos/{repo}/git/refs/heads/{branch}",
        token,
        {
            "sha": commit["sha"],
            "force": False,
        },
    )
    return commit["sha"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish the current committed HEAD to GitHub through the Git API.")
    parser.add_argument("--repo", default="Penzko07/SoloForge", help="Repository in owner/name form.")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--message", default=None, help="Commit message. Defaults to the local HEAD subject.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-dirty", action="store_true", help="Publish committed HEAD even if the worktree is dirty.")
    args = parser.parse_args()

    if not args.allow_dirty:
        try:
            require_clean_worktree()
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 2

    token = os.environ.get("SOLOFORGE_GITHUB_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("set SOLOFORGE_GITHUB_TOKEN or GITHUB_TOKEN first", file=sys.stderr)
        return 2

    message = args.message or str(git_output(["log", "-1", "--format=%s"])).strip()
    try:
        commit_sha = publish(args.repo, args.branch, message, token, args.dry_run)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if commit_sha:
        print(f"Published {commit_sha}")
    else:
        print("Dry run complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
