#!/usr/bin/env python3
"""Fetch contribution and repo data from the GitHub GraphQL API.

Writes data/contributions.json and data/profile.json.
Needs a token in GH_TOKEN or GITHUB_TOKEN (the default Actions token works
for public data). Uses only the Python standard library.
"""
import datetime
import json
import os
import pathlib
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / "config.json").read_text())
API = "https://api.github.com/graphql"

REPO_FIELDS = (
    "name description url stargazerCount forkCount "
    "primaryLanguage { name color }"
)


def graphql(query, variables, token):
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        API,
        data=body,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "profile-readme-cards",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    # A missing featured repo returns a partial result plus an "errors" list.
    # That is fine as long as the user data itself came back.
    if not (payload.get("data") or {}).get("user"):
        raise SystemExit(f"GitHub API error: {payload.get('errors') or payload}")
    return payload["data"]


def build_query(featured):
    aliases = "\n".join(
        f'    f{i}: repository(name: {json.dumps(name)}) {{ {REPO_FIELDS} }}'
        for i, name in enumerate(featured)
    )
    return f"""
query($login: String!) {{
  user(login: $login) {{
    name
    followers {{ totalCount }}
    publicRepos: repositories(ownerAffiliations: OWNER, privacy: PUBLIC) {{ totalCount }}
    top: repositories(first: 6, ownerAffiliations: OWNER, privacy: PUBLIC,
                      isFork: false, orderBy: {{field: STARGAZERS, direction: DESC}}) {{
      nodes {{ {REPO_FIELDS} }}
    }}
{aliases}
    contributionsCollection {{
      contributionCalendar {{
        totalContributions
        weeks {{ contributionDays {{ date contributionCount }} }}
      }}
    }}
  }}
}}
"""


def clean_repo(node):
    lang = node.get("primaryLanguage") or {}
    return {
        "name": node["name"],
        "description": node.get("description") or "",
        "url": node["url"],
        "stars": node["stargazerCount"],
        "forks": node["forkCount"],
        "language": lang.get("name") or "",
        "language_color": lang.get("color") or "#8A93A8",
    }


def main():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Set GH_TOKEN or GITHUB_TOKEN to a GitHub token first.")

    featured = CONFIG.get("featured_repos", [])
    user = graphql(build_query(featured), {"login": CONFIG["username"]}, token)["user"]

    calendar = user["contributionsCollection"]["contributionCalendar"]
    days = [
        {"date": d["date"], "count": d["contributionCount"]}
        for week in calendar["weeks"]
        for d in week["contributionDays"]
    ]

    # Featured repos that exist, in config order; otherwise the most starred.
    repos = [clean_repo(user[f"f{i}"]) for i in range(len(featured)) if user.get(f"f{i}")]
    if not repos:
        repos = [clean_repo(n) for n in user["top"]["nodes"][:4]]

    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    data_dir = ROOT / "data"
    data_dir.mkdir(exist_ok=True)
    (data_dir / "contributions.json").write_text(json.dumps({
        "user": CONFIG["username"],
        "fetched_at": now,
        "total": calendar["totalContributions"],
        "days": days,
    }, indent=1))
    (data_dir / "profile.json").write_text(json.dumps({
        "public_repos": user["publicRepos"]["totalCount"],
        "followers": user["followers"]["totalCount"],
        "repos": repos,
    }, indent=1))
    print(f"Saved {len(days)} days, {calendar['totalContributions']} contributions, "
          f"{len(repos)} repos.")


if __name__ == "__main__":
    main()
