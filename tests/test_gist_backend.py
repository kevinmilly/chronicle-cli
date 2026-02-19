"""Tests for chronicle.sync.gist_backend — GistBackend with mocked urllib."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from chronicle.sync.gist_backend import GIST_FILENAME, GistBackend


def _mock_response(data: dict) -> MagicMock:
    """Create a mock urllib response with JSON data."""
    resp = MagicMock()
    resp.read.return_value = json.dumps(data).encode()
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


class TestGistBackendRead:
    @patch("chronicle.sync.gist_backend.urllib.request.urlopen")
    def test_read_content(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({
            "files": {
                GIST_FILENAME: {"content": "encrypted-token-1\nencrypted-token-2\n"}
            }
        })
        backend = GistBackend("gist123", "ghp_token")
        result = backend.read()
        assert result == "encrypted-token-1\nencrypted-token-2\n"

    @patch("chronicle.sync.gist_backend.urllib.request.urlopen")
    def test_read_empty_gist(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"files": {}})
        backend = GistBackend("gist123", "ghp_token")
        assert backend.read() == ""

    @patch("chronicle.sync.gist_backend.urllib.request.urlopen")
    def test_read_missing_file(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({
            "files": {"other_file.txt": {"content": "stuff"}}
        })
        backend = GistBackend("gist123", "ghp_token")
        assert backend.read() == ""


class TestGistBackendWrite:
    @patch("chronicle.sync.gist_backend.urllib.request.urlopen")
    def test_write_sends_patch(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"files": {}})
        backend = GistBackend("gist123", "ghp_token")
        backend.write("new-content\n")

        # Verify the request
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        assert req.method == "PATCH"
        assert "gist123" in req.full_url
        body = json.loads(req.data.decode())
        assert body["files"][GIST_FILENAME]["content"] == "new-content\n"


class TestGistBackendAppend:
    @patch("chronicle.sync.gist_backend.urllib.request.urlopen")
    def test_append_to_existing(self, mock_urlopen):
        # First call (read) returns existing content, second call (write) succeeds
        read_resp = _mock_response({
            "files": {GIST_FILENAME: {"content": "line1\n"}}
        })
        write_resp = _mock_response({"files": {}})
        mock_urlopen.side_effect = [read_resp, write_resp]

        backend = GistBackend("gist123", "ghp_token")
        backend.append("line2")

        # Verify write was called with combined content
        write_req = mock_urlopen.call_args_list[1][0][0]
        body = json.loads(write_req.data.decode())
        content = body["files"][GIST_FILENAME]["content"]
        assert "line1" in content
        assert "line2" in content

    @patch("chronicle.sync.gist_backend.urllib.request.urlopen")
    def test_append_to_empty(self, mock_urlopen):
        read_resp = _mock_response({"files": {}})
        write_resp = _mock_response({"files": {}})
        mock_urlopen.side_effect = [read_resp, write_resp]

        backend = GistBackend("gist123", "ghp_token")
        backend.append("first-line")

        write_req = mock_urlopen.call_args_list[1][0][0]
        body = json.loads(write_req.data.decode())
        assert body["files"][GIST_FILENAME]["content"] == "first-line\n"


class TestCreateGist:
    @patch("chronicle.sync.gist_backend.urllib.request.urlopen")
    def test_create_returns_id(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response({"id": "new-gist-id-123"})
        gist_id = GistBackend.create_gist("ghp_token")
        assert gist_id == "new-gist-id-123"

        # Verify the request
        req = mock_urlopen.call_args[0][0]
        assert req.method == "POST"
        assert "api.github.com/gists" in req.full_url
        body = json.loads(req.data.decode())
        assert body["public"] is False
        assert GIST_FILENAME in body["files"]
