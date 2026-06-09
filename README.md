# gh-analytics

Personal GitHub contribution stats — daily, weekly, monthly, yearly — pulled from the GitHub GraphQL API.

## Setup

### 1. Get a Personal Access Token (PAT)

1. Go to **github.com → Settings → Developer settings → Personal access tokens → Tokens (classic)**
2. Click **Generate new token (classic)**
3. Give it a name (e.g. `gh-analytics`)
4. Select scopes: `read:user` (includes private repo contributions in the calendar)
5. Click **Generate token** and copy it — you won't see it again

### 2. Create a `.env` file

```bash
cp .env.example .env
# then edit .env and paste your token
```

### 3. Run

```bash
node gh_stats.ts
```

Requires Node 23+ (native TypeScript support, no build step).

## Configuration

All settings go in `.env`:

| Variable            | Default      | Description                        |
|---------------------|--------------|------------------------------------|
| `GITHUB_TOKEN`      | *(required)* | Your PAT                           |
| `GITHUB_USER`       | `matt-trem`  | GitHub username to query           |
| `GITHUB_SINCE_YEAR` | 3 years ago  | Earliest year to fetch             |

## Output

```
=== DAILY (last 30 days) ===
DATE         COUNT  CHART
--------------------------------------------------
2026-05-10       2  ##
2026-05-11       0
...

=== WEEKLY (last 12 weeks) ===
WEEK START    COUNT
------------------
2026-03-16        8
...

=== MONTHLY (last 12 months) ===
MONTH          COUNT
----------------
2025-07           12
...

=== YEARLY ===
YEAR    COUNT
------------
2024      134
2025      201
```

## Notes

- Uses GitHub's `contributionsCollection` GraphQL API — same data as the green squares on your profile.
- Counts commits, PRs, reviews, issues, and issue comments.
- Private repo contributions are included when your PAT has `read:user` scope.
- Progress lines go to stderr; data goes to stdout — safe to pipe or redirect.
