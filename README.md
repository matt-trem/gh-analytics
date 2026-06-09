# gh-analytics

Personal GitHub contribution stats — daily, weekly, monthly, yearly — pulled from the GitHub Events API.

## Setup

### 1. Get a Personal Access Token (PAT)

1. Go to **github.com → Settings → Developer settings → Personal access tokens → Tokens (classic)**
   (direct URL: `https://github.com/settings/tokens`)
2. Click **Generate new token (classic)**
3. Give it a name (e.g. `gh-analytics`)
4. Select scopes:
   - `read:user` — required to read your profile and events
   - No other scopes needed (public events are enough for contribution counts)
5. Click **Generate token** and copy it — you won't see it again

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Or with a virtualenv:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
GITHUB_TOKEN=ghp_yourtoken python gh_stats.py
```

To use a different username than the default (`matt-trem`):

```bash
GITHUB_TOKEN=ghp_yourtoken GITHUB_USER=other-user python gh_stats.py
```

### Storing the token (optional)

Add to your shell profile (`~/.zshrc` or `~/.bash_profile`):

```bash
export GITHUB_TOKEN=ghp_yourtoken
```

Then just run:

```bash
python gh_stats.py
```

## Output

```
=== DAILY (last 30 days) ===
DATE         CONTRIBUTIONS
--------------------------
2026-05-10       2  ##
2026-05-11       0
...

=== WEEKLY (last 12 weeks) ===
WEEK START   CONTRIBUTIONS
--------------------------
2026-03-16       8
...

=== MONTHLY (last 12 months) ===
MONTH        CONTRIBUTIONS
------------------------
2025-07         12
...

=== YEARLY ===
YEAR   CONTRIBUTIONS
--------------------
2024       134
2025       201
```

## Limitations

- The GitHub Events API returns **at most 300 events** going back ~90 days. Events older than ~3 months may not appear, so the yearly/monthly totals for older periods will be 0 or incomplete.
- Private repo events are included only if your PAT has `repo` scope.
- This counts *events* (pushes, PRs, reviews, issues, comments), not raw commits — similar to but not identical to the green squares on your GitHub profile.
