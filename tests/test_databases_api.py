import importlib.util
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


API = load_module("database_api", ROOT / "api" / "databases.py")


class DatabaseApiTests(unittest.TestCase):
    def test_api_selects_latest_version_by_region(self):
        history = {
            "entries": [
                {"region": "cn", "version": "2", "url": "new"},
                {"region": "tw", "version": "5", "url": "tw"},
                {"region": "cn", "version": "1", "url": "old"},
            ]
        }
        latest = API.latest_by_region(API.select_entries(history))
        self.assertEqual(latest["cn"]["url"], "new")
        self.assertEqual(latest["tw"]["url"], "tw")

    def test_auto_source_uses_proxy_only_for_mainland_china(self):
        self.assertEqual(API.select_download_source("auto", "CN"), "proxy")
        self.assertEqual(API.select_download_source("auto", "US"), "github")
        self.assertEqual(API.select_download_source("github", "CN"), "github")
        self.assertEqual(API.select_download_source("proxy", "US"), "proxy")

    def test_api_exposes_proxy_and_github_urls(self):
        github_url = (
            "https://github.com/owner/repo/releases/download/database-jp-1/"
            "master_jp.db"
        )
        entry = API.add_download_urls(
            [{"region": "jp", "version": "1", "url": github_url}], "proxy"
        )[0]
        self.assertEqual(entry["urls"]["github"], github_url)
        self.assertEqual(entry["urls"]["proxy"], API.GITHUB_PROXY + github_url)
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
                "entries": [{"region": "jp", "version": "1", "url": github_url}]
            },
        ):
            request.do_GET()

        self.assertEqual(statuses, [302])
        self.assertEqual(headers["Location"], API.GITHUB_PROXY + github_url)
        self.assertEqual(headers["Vary"], "X-Vercel-IP-Country")


if __name__ == "__main__":
    unittest.main()
