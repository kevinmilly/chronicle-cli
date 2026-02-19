"""GitHub Gist sync backend — uses urllib (no external HTTP dependency)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from chronicle.sync.backend import SyncBackend

GIST_FILENAME = "chronicle_sync.enc"


class GistBackend(SyncBackend):
    """Sync backend that stores encrypted data in a GitHub Gist."""

    def __init__(self, gist_id: str, github_token: str) -> None:
        self.gist_id = gist_id
        self.github_token = github_token

    def _api_url(self) -> str:
        return f"https://api.github.com/gists/{self.gist_id}"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _request(
        self, url: str, *, method: str = "GET", data: dict | None = None
    ) -> dict:
        body = json.dumps(data).encode() if data else None
        headers = self._headers()
        if body:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            msg = e.read().decode()
            raise RuntimeError(f"GitHub API error ({e.code}): {msg}") from e

    def read(self) -> str:
        """Fetch the encrypted content from the Gist."""
        data = self._request(self._api_url())
        files = data.get("files", {})
        file_info = files.get(GIST_FILENAME)
        if not file_info:
            return ""
        return file_info.get("content", "")

    def write(self, content: str) -> None:
        """Overwrite the Gist file content."""
        self._request(
            self._api_url(),
            method="PATCH",
            data={"files": {GIST_FILENAME: {"content": content}}},
        )

    def append(self, line: str) -> None:
        """Append a line to the existing Gist content."""
        existing = self.read()
        if existing and not existing.endswith("\n"):
            new_content = existing + "\n" + line + "\n"
        elif existing:
            new_content = existing + line + "\n"
        else:
            new_content = line + "\n"
        self.write(new_content)

    @classmethod
    def create_gist(cls, github_token: str, description: str = "Chronicle sync") -> str:
        """Create a new secret Gist and return its ID."""
        url = "https://api.github.com/gists"
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        payload = json.dumps({
            "description": description,
            "public": False,
            "files": {GIST_FILENAME: {"content": "# chronicle sync\n"}},
        }).encode()
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            msg = e.read().decode()
            raise RuntimeError(f"GitHub API error ({e.code}): {msg}") from e
        return data["id"]
