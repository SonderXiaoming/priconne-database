import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


HISTORY = load_module("update_history", ROOT / "scripts" / "update_history.py")
API = load_module("database_api", ROOT / "api" / "databases.py")


class HistoryApiTests(unittest.TestCase):
    def test_history_records_each_version_once(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            for region, version in (("cn", 3), ("tw", 2), ("jp", 1)):
                (root / "data" / f"master_{region}_unhash.db").write_bytes(b"db")
                (root / "data" / f"version_{region}.json").write_text(
                    json.dumps({"version": version}), encoding="utf-8"
                )

            with patch.dict(os.environ, {"GITHUB_REPOSITORY": "owner/repo"}):
                first = HISTORY.update_history(root, "2026-08-05")
                second = HISTORY.update_history(root, "2026-08-06")

            self.assertEqual(len(first), 3)
            self.assertEqual(second, [])
            document = json.loads(
                (root / "data" / "history.json").read_text(encoding="utf-8")
            )
            self.assertEqual(len(document["entries"]), 3)
            self.assertTrue(all(entry["date"] == "2026-08-05" for entry in first))
            self.assertTrue(
                all((root / ".cache" / "releases" / entry["filename"]).exists() for entry in first)
            )

    def test_api_selects_latest_version_by_region(self):
        history = {
            "entries": [
                {"region": "cn", "version": "2", "url": "new"},
                {"region": "tw", "version": "5", "url": "tw"},
                {"region": "cn", "version": "1", "url": "old"},
            ]
        }
        entries = API.select_entries(history)
        latest = API.latest_by_region(entries)
        self.assertEqual(latest["cn"]["url"], "new")
        self.assertEqual(latest["tw"]["url"], "tw")

    def test_auto_source_uses_proxy_only_for_mainland_china(self):
        self.assertEqual(API.select_download_source("auto", "CN"), "proxy")
        self.assertEqual(API.select_download_source("auto", "US"), "github")
        self.assertEqual(API.select_download_source("auto", ""), "github")
        self.assertEqual(API.select_download_source("github", "CN"), "github")
        self.assertEqual(API.select_download_source("proxy", "US"), "proxy")

    def test_api_exposes_proxy_and_github_urls(self):
        github_url = (
            "https://github.com/owner/repo/releases/download/database-jp-1/"
            "master_jp.db"
        )
        entries = API.add_download_urls(
            [{"region": "jp", "version": "1", "url": github_url}],
            "proxy",
        )

        entry = entries[0]
        self.assertEqual(entry["source"], "proxy")
        self.assertEqual(entry["urls"]["github"], github_url)
        self.assertEqual(
            entry["urls"]["proxy"],
            "https://gh.rem.asia/" + github_url,
        )
        self.assertEqual(entry["url"], entry["urls"]["proxy"])

    def test_cn_download_redirect_uses_proxy(self):
        github_url = (
            "https://github.com/owner/repo/releases/download/database-jp-1/"
            "master_jp.db"
        )
        request = object.__new__(API.handler)
        request.path = "/api/databases?region=jp&download=1"
        request.headers = {"x-vercel-ip-country": "CN"}
        statuses = []
        headers = {}
        request.send_response = statuses.append
        request.send_header = headers.__setitem__
        request.end_headers = lambda: None

        with patch.object(
            API,
            "load_history",
            return_value={
                "entries": [
                    {"region": "jp", "version": "1", "url": github_url}
                ]
            },
        ):
            request.do_GET()

        self.assertEqual(statuses, [302])
        self.assertEqual(headers["Location"], "https://gh.rem.asia/" + github_url)
        self.assertEqual(headers["Vary"], "X-Vercel-IP-Country")


if __name__ == "__main__":
    unittest.main()
