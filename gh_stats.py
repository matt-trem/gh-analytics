#!/usr/bin/env python3
"""GitHub contribution stats for a personal account."""

import os
import sys
from datetime import date, timedelta
from collections import defaultdict
import requests

GITHUB_API = "https://api.github.com"


def get_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def fetch_events(username: str, token: str, days: int = 365) -> list[dict]:
    """Fetch public events for a user (up to 300, ~90 days of data via API)."""
    headers = get_headers(token)
    events = []
    page = 1
    cutoff = date.today() - timedelta(days=days)

    while True:
        url = f"{GITHUB_API}/users/{username}/events"
        resp = requests.get(url, headers=headers, params={"per_page": 100, "page": page})
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        for e in batch:
            event_date = date.fromisoformat(e["created_at"][:10])
            if event_date < cutoff:
                return events
            events.append(e)
        if len(batch) < 100:
            break
        page += 1
        if page > 3:  # GitHub caps at 300 events total
            break

    return events


def count_contributions(events: list[dict]) -> dict[date, int]:
    """Count contribution-type events per day."""
    contribution_types = {
        "PushEvent",
        "PullRequestEvent",
        "PullRequestReviewEvent",
        "IssuesEvent",
        "IssueCommentEvent",
        "CreateEvent",
        "CommitCommentEvent",
    }
    counts: dict[date, int] = defaultdict(int)
    for e in events:
        if e["type"] in contribution_types:
            d = date.fromisoformat(e["created_at"][:10])
            counts[d] += 1
    return counts


def print_daily(counts: dict[date, int], days: int = 30) -> None:
    print(f"\n{'DATE':<12} {'CONTRIBUTIONS':>13}")
    print("-" * 26)
    today = date.today()
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        c = counts.get(d, 0)
        bar = "#" * min(c, 40)
        print(f"{d!s:<12} {c:>5}  {bar}")


def print_weekly(counts: dict[date, int], weeks: int = 12) -> None:
    print(f"\n{'WEEK START':<12} {'CONTRIBUTIONS':>13}")
    print("-" * 26)
    today = date.today()
    # Start of current week (Monday)
    week_start = today - timedelta(days=today.weekday())
    for i in range(weeks - 1, -1, -1):
        ws = week_start - timedelta(weeks=i)
        total = sum(counts.get(ws + timedelta(days=d), 0) for d in range(7))
        print(f"{ws!s:<12} {total:>5}")


def print_monthly(counts: dict[date, int], months: int = 12) -> None:
    print(f"\n{'MONTH':<10} {'CONTRIBUTIONS':>13}")
    print("-" * 24)
    today = date.today()
    year, month = today.year, today.month
    results = []
    for _ in range(months):
        total = sum(v for k, v in counts.items() if k.year == year and k.month == month)
        results.append((f"{year}-{month:02d}", total))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    for label, total in reversed(results):
        print(f"{label:<10} {total:>5}")


def print_yearly(counts: dict[date, int]) -> None:
    print(f"\n{'YEAR':<6} {'CONTRIBUTIONS':>13}")
    print("-" * 20)
    by_year: dict[int, int] = defaultdict(int)
    for d, c in counts.items():
        by_year[d.year] += c
    for year in sorted(by_year):
        print(f"{year:<6} {by_year[year]:>5}")


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: set GITHUB_TOKEN environment variable.", file=sys.stderr)
        sys.exit(1)

    username = os.environ.get("GITHUB_USER", "matt-trem")

    print(f"Fetching GitHub activity for @{username}...")
    events = fetch_events(username, token, days=365)
    print(f"  {len(events)} events fetched.")

    counts = count_contributions(events)

    print("\n=== DAILY (last 30 days) ===")
    print_daily(counts, days=30)

    print("\n=== WEEKLY (last 12 weeks) ===")
    print_weekly(counts, weeks=12)

    print("\n=== MONTHLY (last 12 months) ===")
    print_monthly(counts, months=12)

    print("\n=== YEARLY ===")
    print_yearly(counts)


if __name__ == "__main__":
    main()
