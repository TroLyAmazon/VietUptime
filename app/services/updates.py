# app/services/updates.py
import os
import re
from dataclasses import dataclass
from typing import Optional

import requests

from .. import __version__


@dataclass
class UpdateInfo:
    local_version: str
    latest_version: str
    has_update: bool
    notes: str
    repo_url: str
    release_url: str
    asset_url: str  # optional


def _norm_ver(v: str) -> tuple[int, int, int]:
    v = (v or "").strip()
    v = v[1:] if v.lower().startswith("v") else v
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)", v)
    if not m:
        return (0, 0, 0)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def _is_newer(remote: str, local: str) -> bool:
    return _norm_ver(remote) > _norm_ver(local)


def check_update(app) -> Optional[UpdateInfo]:
    """
    Uses GitHub Releases latest endpoint:
      https://api.github.com/repos/{owner}/{repo}/releases/latest
    Needs env/config:
      GITHUB_REPO="TroLyAmazon/VietUptime"
      optional GITHUB_TOKEN (private repo / higher rate limit)
    """
    repo = app.config.get("GITHUB_REPO", "") or os.getenv("GITHUB_REPO", "")
    if not repo:
        return None

    local = __version__
    repo_url = f"https://github.com/{repo}"
    release_url = f"https://github.com/{repo}/releases/latest"

    token = app.config.get("GITHUB_TOKEN", "") or os.getenv("GITHUB_TOKEN", "")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "DotStatus",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    api = f"https://api.github.com/repos/{repo}/releases/latest"
    r = requests.get(api, headers=headers, timeout=12)

    if r.status_code == 404:
        # no release yet
        return UpdateInfo(
            local_version=local,
            latest_version="",
            has_update=False,
            notes="No releases published yet on GitHub.",
            repo_url=repo_url,
            release_url=release_url,
            asset_url="",
        )

    r.raise_for_status()
    data = r.json()

    latest = (data.get("tag_name") or data.get("name") or "").strip()
    notes = (data.get("body") or "").strip()

    # prefer first asset if exists
    asset_url = ""
    assets = data.get("assets") or []
    if assets:
        asset_url = (assets[0].get("browser_download_url") or "").strip()

    return UpdateInfo(
        local_version=local,
        latest_version=latest,
        has_update=_is_newer(latest, local),
        notes=notes,
        repo_url=repo_url,
        release_url=release_url,
        asset_url=asset_url,
    )
