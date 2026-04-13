"""GitHub repo / issues / PRs integration via REST API.

Requires env:
    GITHUB_TOKEN  - Personal Access Token (classic or fine-grained)
    GITHUB_REPO   - default repo (vd "techlaaidev/techly-assistant")
"""
import json
import os
import urllib.request
from ._common import _reply

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")
GH_API = "https://api.github.com"


def _gh_request(method: str, path: str, body: dict | None = None) -> dict | list:
    req = urllib.request.Request(
        f"{GH_API}{path}",
        method=method,
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "Techly-Assistant/1.0",
        },
    )
    if body is not None:
        req.data = json.dumps(body).encode("utf-8")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def register(mcp):
    @mcp.tool()
    def lay_pull_request_dang_mo(repo: str = "") -> str:
        """Liệt kê các Pull Request đang mở trong GitHub repo.

        GỌI TOOL NÀY KHI người dùng hỏi: "PR nào đang chờ review", "có PR nào mới",
        "danh sách pull request".

        Args:
            repo: dạng "owner/name" (mặc định dùng GITHUB_REPO trong .env)
        """
        if not GITHUB_TOKEN:
            return "GitHub chưa cấu hình. Set GITHUB_TOKEN trong .env"
        target = repo or GITHUB_REPO
        if not target:
            return "Chưa chỉ định repo. Truyền 'owner/name' hoặc set GITHUB_REPO."
        try:
            prs = _gh_request("GET", f"/repos/{target}/pulls?state=open&per_page=10")
            if not isinstance(prs, list) or not prs:
                return f"Repo {target} không có PR nào đang mở."
            lines = [
                f"#{p['number']} - {p['title']} (by {p['user']['login']})"
                for p in prs[:10]
            ]
            return _reply(f"Pull Requests đang mở ({target}):\n" + "\n".join(lines))
        except Exception as e:
            return f"Lỗi GitHub: {str(e)[:150]}"

    @mcp.tool()
    def lay_issue_moi_nhat(repo: str = "") -> str:
        """Liệt kê các issue mới nhất trong GitHub repo.

        GỌI TOOL NÀY KHI người dùng hỏi: "issue mới", "có bug nào không", "issue gần đây".
        """
        if not GITHUB_TOKEN:
            return "GitHub chưa cấu hình."
        target = repo or GITHUB_REPO
        if not target:
            return "Chưa chỉ định repo."
        try:
            issues = _gh_request(
                "GET",
                f"/repos/{target}/issues?state=open&per_page=10&sort=created",
            )
            issues = [i for i in issues if "pull_request" not in i]
            if not issues:
                return f"Repo {target} không có issue nào đang mở."
            lines = [
                f"#{i['number']} - {i['title']} (by {i['user']['login']})"
                for i in issues[:10]
            ]
            return _reply(f"Issues đang mở ({target}):\n" + "\n".join(lines))
        except Exception as e:
            return f"Lỗi GitHub: {str(e)[:150]}"

    @mcp.tool()
    def lay_commit_gan_day(repo: str = "") -> str:
        """Liệt kê 5 commit mới nhất của repo.

        GỌI TOOL NÀY KHI người dùng hỏi: "ai vừa commit", "commit mới nhất", "thay đổi gần đây".
        """
        if not GITHUB_TOKEN:
            return "GitHub chưa cấu hình."
        target = repo or GITHUB_REPO
        if not target:
            return "Chưa chỉ định repo."
        try:
            commits = _gh_request("GET", f"/repos/{target}/commits?per_page=5")
            if not isinstance(commits, list) or not commits:
                return "Không có commit nào."
            lines = []
            for c in commits[:5]:
                msg = c.get("commit", {}).get("message", "")[:80]
                author = c.get("commit", {}).get("author", {}).get("name", "?")
                lines.append(f"- {author}: {msg}")
            return _reply(f"5 commit gần nhất ({target}):\n" + "\n".join(lines))
        except Exception as e:
            return f"Lỗi GitHub: {str(e)[:150]}"
