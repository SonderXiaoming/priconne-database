"""Vercel API for discovering and downloading current or historical databases."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse


HISTORY_PATH = Path(__file__).parents[1] / "data" / "history.json"
VALID_REGIONS = {"cn", "tw", "jp"}
VALID_SOURCES = {"auto", "proxy", "github"}
VALID_COMPRESSIONS = {"none", "br"}
GITHUB_PROXY = "https://gh.rem.asia/"


def load_history() -> dict:
    return json.loads(HISTORY_PATH.read_text(encoding="utf-8"))


def select_entries(history: dict, region: str | None = None) -> list[dict]:
    entries = history.get("entries", [])
    if region:
        entries = [entry for entry in entries if entry.get("region") == region]
    return sorted(
        entries,
        key=lambda entry: (entry.get("region", ""), int(entry.get("version", 0))),
        reverse=True,
    )


def latest_by_region(entries: list[dict]) -> dict[str, dict]:
    latest: dict[str, dict] = {}
    for entry in entries:
        latest.setdefault(entry["region"], entry)
    return latest


def select_download_source(requested: str, country: str = "") -> str:
    if requested == "proxy":
        return "proxy"
    if requested == "github":
        return "github"
    return "proxy" if country.upper() == "CN" else "github"


def github_proxy_url(url: str) -> str:
    if url.startswith("https://github.com/"):
        return GITHUB_PROXY + url
    return url


def add_download_urls(
    entries: list[dict], source: str, compression: str = "none"
) -> list[dict]:
    result: list[dict] = []
    for entry in entries:
        github_url = entry.get("br_url") if compression == "br" else entry["url"]
        if not github_url:
            continue
        proxy_url = github_proxy_url(github_url)
        value = dict(entry)
        value["source"] = source
        value["compression"] = compression
        value["urls"] = {"github": github_url, "proxy": proxy_url}
        value["url"] = value["urls"][source]
        if value.get("filename"):
            value["download_filename"] = value["filename"] + (
                ".br" if compression == "br" else ""
            )
        result.append(value)
    return result


class handler(BaseHTTPRequestHandler):
    def send_json(self, status: int, value: dict) -> None:
        body = json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "public, max-age=300, s-maxage=300")
        self.send_header("Vary", "X-Vercel-IP-Country")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        query = parse_qs(urlparse(self.path).query)
        region = query.get("region", [None])[0]
        version = query.get("version", [None])[0]
        download = query.get("download", ["0"])[0].lower() in {"1", "true", "yes"}
        requested_source = query.get("source", ["auto"])[0].lower()
        compression = query.get("compression", ["none"])[0].lower()
        if region and region not in VALID_REGIONS:
            self.send_json(400, {"error": "region must be cn, tw, or jp"})
            return
        if requested_source not in VALID_SOURCES:
            self.send_json(400, {"error": "source must be auto, proxy, or github"})
            return
        if compression not in VALID_COMPRESSIONS:
            self.send_json(400, {"error": "compression must be none or br"})
            return

        history = load_history()
        entries = select_entries(history, region)
        if version:
            entries = [entry for entry in entries if str(entry["version"]) == version]
        country = self.headers.get("x-vercel-ip-country", "")
        source = select_download_source(requested_source, country)
        entries = add_download_urls(entries, source, compression)
        selected = entries[0] if entries else None
        if download:
            if selected is None:
                self.send_json(
                    404, {"error": "database version or compression not found"}
                )
                return
            self.send_response(302)
            self.send_header("Location", selected["url"])
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Vary", "X-Vercel-IP-Country")
            self.end_headers()
            return

        self.send_json(
            200,
            {
                "repository": history.get("repository"),
                "download_source": source,
                "compression": compression,
                "latest": latest_by_region(entries),
                "history": entries,
            },
        )

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Vary", "X-Vercel-IP-Country")
        self.end_headers()
