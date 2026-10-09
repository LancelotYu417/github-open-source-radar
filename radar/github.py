"""GitHub API client. Calls are made only during explicit sync."""
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import json
from datetime import datetime, timezone, timedelta

BASE = "https://api.github.com"

class GithubError(RuntimeError):
    pass

class GitHubClient:
    def __init__(self, token: str | None = None):
        self.token = token or os.getenv("GITHUB_TOKEN", "")

    def get(self, path: str, params: dict | None = None):
        qs = "?" + urllib.parse.urlencode(params) if params else ""
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10",
            "User-Agent": "github-open-source-radar/0.1",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(BASE + path + qs, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=25) as res:
                return json.load(res)
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 429):
                wait = exc.headers.get("Retry-After") or exc.headers.get("X-RateLimit-Reset") or "unknown"
                raise GithubError(f"GitHub API rate limit/access failure HTTP {exc.code}, retry info: {wait}") from exc
            raise GithubError(f"GitHub API HTTP {exc.code}: {path}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise GithubError(f"GitHub API network failure: {exc}") from exc

    def discover(self, per_query: int = 30):
        # Diversified search strata. Not an exhaustive index of GitHub.
        now = datetime.now(timezone.utc).date()
        recent = (now - timedelta(days=30)).isoformat()
        new = (now - timedelta(days=365)).isoformat()
        queries = [
            "stars:>5000 archived:false fork:false",
            f"created:>{new} stars:>100 archived:false fork:false",
            f"pushed:>{recent} stars:>200 archived:false fork:false",
            "topic:ai-agent stars:>100 archived:false fork:false",
        ]
        found = {}
        for q in queries:
            response = self.get("/search/repositories", {"q": q, "sort": "stars", "order": "desc", "per_page": per_query})
            for item in response.get("items", []):
                found[item["full_name"].lower()] = item
            time.sleep(0.25)
        return list(found.values())

    def history(self, full_name: str, max_weeks: int = 54):
        owner, repo = full_name.split("/", 1)
        path = f"/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/stargazers/history"
        output = []
        pages = (max_weeks + 29) // 30
        for page in range(1, pages + 1):
            data = self.get(path, {"per_page": min(30, max_weeks - len(output)), "page": page})
            if not isinstance(data, list):
                raise GithubError(f"Unexpected star history payload for {full_name}")
            output.extend(data)
            if len(data) < 30:
                break
        return output[:max_weeks]
