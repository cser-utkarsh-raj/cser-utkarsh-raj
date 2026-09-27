from __future__ import annotations

import datetime as dt
import json
import os
import urllib.request
from pathlib import Path

USERNAME = "cser-utkarsh-raj"
DAYS = 30
OUTPUT = Path("assets/github-activity.svg")

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!, $maxRepositories: Int!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      commitContributionsByRepository(maxRepositories: $maxRepositories) {
        repository { nameWithOwner }
        contributions(first: 100) {
          nodes {
            occurredAt
            commitCount
          }
        }
      }
    }
  }
}
"""


def github_graphql(query: str, variables: dict) -> dict:
    token = os.environ["GITHUB_TOKEN"]
    body = json.dumps({"query": query, "variables": variables}).encode()
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "cser-utkarsh-raj-profile-activity",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]


def esc(value: object) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def build_svg(days: list[tuple[str, int]], total: int) -> str:
    width, height = 760, 300
    chart_x, chart_y, chart_w, chart_h = 36, 76, 688, 158
    max_count = max((count for _, count in days), default=1)
    slot = chart_w / len(days)
    bar_w = max(4, slot - 4)

    bars = []
    labels = []
    for i, (date, count) in enumerate(days):
        x = chart_x + i * slot + (slot - bar_w) / 2
        bar_h = 0 if max_count == 0 else (count / max_count) * chart_h
        y = chart_y + chart_h - bar_h
        fill = "#20B2AA" if count else "#21262D"
        bars.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{max(bar_h, 1):.1f}" rx="2" fill="{fill}">' 
            f'<title>{esc(date)}: {count} commit{"s" if count != 1 else ""}</title></rect>'
        )
        if i in (0, 7, 14, 21, 29):
            labels.append(f'<text x="{x + bar_w/2:.1f}" y="255" text-anchor="middle" class="axis">{date[5:]}</text>')

    active = sum(1 for _, count in days if count > 0)
    peak = max_count
    peak_day = next((date for date, count in days if count == peak), days[-1][0] if days else "")
    generated = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Daily GitHub commit activity for {USERNAME}">
<rect width="100%" height="100%" rx="20" fill="#0D1117"/>
<style>
.title {{ font: 600 17px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill:#E6EDF3; }}
.meta {{ font: 400 12px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill:#8B949E; }}
.stat {{ font: 600 13px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill:#C9D1D9; }}
.axis {{ font: 400 10px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill:#6E7681; }}
</style>
<text x="28" y="30" class="title">Daily GitHub commits · {USERNAME}</text>
<text x="28" y="50" class="meta">Last 30 days · refreshed automatically at 01:00 IST</text>
<text x="735" y="30" text-anchor="end" class="stat">{total} commits</text>
<line x1="{chart_x}" y1="{chart_y + chart_h}" x2="{chart_x + chart_w}" y2="{chart_y + chart_h}" stroke="#30363D"/>
{''.join(bars)}
{''.join(labels)}
<text x="36" y="281" class="meta">Active days: {active}</text>
<text x="735" y="281" text-anchor="end" class="meta">Peak: {peak} on {peak_day[5:]}</text>
<text x="735" y="298" text-anchor="end" class="meta">Generated {generated}</text>
</svg>
'''


def main() -> None:
    today = dt.datetime.now(dt.timezone.utc).date()
    start = today - dt.timedelta(days=DAYS - 1)
    data = github_graphql(
        QUERY,
        {
            "login": USERNAME,
            "from": f"{start.isoformat()}T00:00:00Z",
            "to": f"{(today + dt.timedelta(days=1)).isoformat()}T00:00:00Z",
            "maxRepositories": 100,
        },
    )

    raw_days: dict[str, int] = {}
    repositories = data["user"]["contributionsCollection"]["commitContributionsByRepository"]
    for repository in repositories:
        for contribution in repository["contributions"]["nodes"]:
            date = contribution["occurredAt"][:10]
            raw_days[date] = raw_days.get(date, 0) + contribution["commitCount"]

    days = [(str(start + dt.timedelta(days=i)), raw_days.get(str(start + dt.timedelta(days=i)), 0)) for i in range(DAYS)]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(build_svg(days, sum(count for _, count in days)), encoding="utf-8")
    print(f"Wrote {OUTPUT} for {start} through {today}")


if __name__ == "__main__":
    main()
