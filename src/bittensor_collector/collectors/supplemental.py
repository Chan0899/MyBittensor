from __future__ import annotations

import re

from bs4 import BeautifulSoup

from bittensor_collector.utils.http_client import HttpClient


class SupplementalCollector:
    def __init__(self, github_api_base_url: str, http_client: HttpClient) -> None:
        self.github_api_base_url = github_api_base_url.rstrip("/")
        self.http = http_client

    def collect_project_page(self, url: str) -> dict:
        html = self.http.get_text(url)
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        desc_tag = soup.find("meta", attrs={"name": "description"})
        desc = desc_tag.get("content", "").strip() if desc_tag else ""
        return {
            "title": title,
            "description": desc,
        }

    def collect_github_summary(self, repo_url: str) -> dict:
        match = re.search(r"github\.com/([^/]+)/([^/#?]+)", repo_url)
        if not match:
            return {}

        owner, repo = match.group(1), match.group(2)
        api_url = f"{self.github_api_base_url}/repos/{owner}/{repo}"
        payload = self.http.get_json(api_url, cache_key=f"github_repo_{owner}_{repo}")
        return {
            "full_name": payload.get("full_name", ""),
            "stargazers_count": payload.get("stargazers_count"),
            "forks_count": payload.get("forks_count"),
            "open_issues_count": payload.get("open_issues_count"),
            "pushed_at": payload.get("pushed_at", ""),
        }

    def collect_discord_public_info(self, invite_url: str) -> dict:
        # 首版以非阻塞为目标，只记录输入来源，避免因权限/API变化导致中断。
        return {
            "invite_url": invite_url,
            "status": "manual_or_public_only",
            "note": "Discord采集未启用机器人权限，需人工补录社区反馈。",
        }
