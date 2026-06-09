#!/usr/bin/env python3
"""GitHub contribution stats for a personal account using the GraphQL API."""

import os
import sys
from datetime import date, timedelta
from collections import defaultdict
import requests

GITHUB_GRAPHQL = "https://api.github.com/graphql"

CONTRIBUTIONS_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""


def get_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def fetch_year(username: str, token: str, year: int) -> dict[date, int]:
    """Fetch contribution counts for a single calendar year."""
    from_dt = f"{year}-01-01T00:00:00Z"
    to_dt = f"{year}-12-31T23:59:59Z"

    resp = requests.post(
        GITHUB_GRAPHQL,
        headers=get_headers(token),
        json={"query": CONTRIBUTIONS_QUERY, "variables": {"login": username, "from": from_dt, "to": to_dt}},
    )
    resp.raise_for_status()
    payload = resp.json()

    if "errors" in payload:
        for err in payload["errors"]:
            print(f"GraphQL error: {err['message']}", file=sys.stderr)
        sys.exit(1)

    weeks = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    counts: dict[date, int] = {}
    for week in weeks:
        for day in week["contributionDays"]:
            counts[date.fromisoformat(day["date"])] = day["contributionCount"]
    return counts


def fetch_all(username: str, token: str, since_year: int) -> dict[date, int]:
    """Fetch contributions from since_year through today."""
    today = date.today()
    all_counts: dict[date, int] = {}
    for year in range(since_year, today.year + 1):
        print(f"  Fetching {year}...")
        all_counts.update(fetch_year(username, token, year))
    return all_counts


def print_daily(counts: dict[date, int], days: int = 30) -> None:
    print(f"\n{'DATE':<12} {'COUNT':>5}  CHART")
    print("-" * 50)
    today = date.today()
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        c = counts.get(d, 0)
        bar = "#" * min(c, 40)
        print(f"{d!s:<12} {c:>5}  {bar}")


def print_weekly(counts: dict[date, int], weeks: int = 12) -> None:
    print(f"\n{'WEEK START':<12} {'COUNT':>5}")
    print("-" * 18)
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    for i in range(weeks - 1, -1, -1):
        ws = week_start - timedelta(weeks=i)
        total = sum(counts.get(ws + timedelta(days=d), 0) for d in range(7))
        print(f"{ws!s:<12} {total:>5}")


def print_monthly(counts: dict[date, int], months: int = 12) -> None:
    print(f"\n{'MONTH':<10} {'COUNT':>5}")
    print("-" * 16)
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
    print(f"\n{'YEAR':<6} {'COUNT':>5}")
    print("-" * 12)
    by_year: dict[int, int] = defaultdict(int)
    for d, c in counts.items():
        by_year[d.year] += c
    for year in sorted(by_year):
        print(f"{year:<6} {by_year[year]:>5}")


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: set GITHUB_TOKEN environment variable.", file=sys.stderr)
        sys.exit(1)

    username = os.environ.get("GITHUB_USER", "matt-trem")
    since_year = int(os.environ.get("GITHUB_SINCE_YEAR", date.today().year - 2))

    print(f"Fetching GitHub contributions for @{username} (since {since_year})...")
    counts = fetch_all(username, token, since_year)
    print(f"  {sum(counts.values())} total contributions across {len(counts)} days.")

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
