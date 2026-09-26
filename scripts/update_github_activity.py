import json
import math
import os
import urllib.request

USERNAME = "cser-utkarsh-raj"
TOKEN = os.environ["GITHUB_TOKEN"]

query = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
    }
  }
}
"""

payload = json.dumps({"query": query, "variables": {"login": USERNAME}}).encode()
request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "github-profile-activity",
    },
    method="POST",
)

with urllib.request.urlopen(request) as response:
    result = json.load(response)

if result.get("errors"):
    raise RuntimeError(result["errors"])

contrib = result["data"]["user"]["contributionsCollection"]
values = [
    ("Commits", contrib["totalCommitContributions"]),
    ("Pull requests", contrib["totalPullRequestContributions"]),
    ("Issues", contrib["totalIssueContributions"]),
    ("Reviews", contrib["totalPullRequestReviewContributions"]),
]
values = [(name, int(value)) for name, value in values if int(value) > 0]
total = sum(value for _, value in values)

if not total:
    values = [("No activity yet", 1)]
    total = 1

cx, cy, radius = 140, 120, 82
colors = ["#20B2AA", "#A78BFA", "#60A5FA", "#F59E0B"]

def polar(angle):
    rad = math.radians(angle - 90)
    return cx + radius * math.cos(rad), cy + radius * math.sin(rad)

def arc_path(start, end):
    x1, y1 = polar(end)
    x2, y2 = polar(start)
    large = 1 if end - start > 180 else 0
    return f"M {cx} {cy} L {x1:.2f} {y1:.2f} A {radius} {radius} 0 {large} 0 {x2:.2f} {y2:.2f} Z"

parts = []
angle = 0
for index, (name, value) in enumerate(values):
    sweep = value / total * 360
    parts.append(f'<path d="{arc_path(angle, angle + sweep)}" fill="{colors[index % len(colors)]}"/>')
    angle += sweep

legend = []
for index, (name, value) in enumerate(values):
    y = 48 + index * 30
    pct = value / total * 100
    legend.append(
        f'<circle cx="282" cy="{y - 5}" r="5" fill="{colors[index % len(colors)]}"/>'
        f'<text x="296" y="{y}" class="label">{name}</text>'
        f'<text x="400" y="{y}" text-anchor="end" class="value">{value} · {pct:.0f}%</text>'
    )

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="440" height="260" viewBox="0 0 440 260" role="img" aria-label="GitHub contribution activity for {USERNAME}">
<rect width="440" height="260" rx="18" fill="#0D1117"/>
<style>
.title {{ font: 600 15px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: #E6EDF3; }}
.label {{ font: 400 13px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: #C9D1D9; }}
.value {{ font: 600 12px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: #8B949E; }}
.sub {{ font: 400 11px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: #6E7681; }}
</style>
<text x="24" y="28" class="title">Contribution activity · {USERNAME}</text>
<g>{''.join(parts)}</g>
<circle cx="140" cy="120" r="48" fill="#0D1117"/>
<text x="140" y="116" text-anchor="middle" class="title" font-size="18">{sum(v for _, v in values)}</text>
<text x="140" y="134" text-anchor="middle" class="sub">contributions</text>
<g>{''.join(legend)}</g>
<text x="24" y="240" class="sub">Updated automatically by GitHub Actions</text>
</svg>
'''

os.makedirs("assets", exist_ok=True)
with open("assets/github-activity.svg", "w", encoding="utf-8") as file:
    file.write(svg)
