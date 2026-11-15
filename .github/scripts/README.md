# Profile generator

Run from the repository root with Python 3.10 or newer:

```sh
python3 -m unittest discover -s .github/scripts -p 'test_*.py' -v
python3 .github/scripts/update_activity.py
```

`GITHUB_REPOSITORY_OWNER` defaults to `atontini`. `GH_TOKEN` is optional for
local public API reads; the workflow uses its built-in `github.token`. No
personal access token or private-repository access is required.

The profile README has two automatically maintained sections:

| README section | Markers | Generated content |
| :--- | :--- | :--- |
| Upstream contributions | `<!-- PROJECTS:START -->` / `<!-- PROJECTS:END -->` | Upstream repository links and merged PR counts, grouped case-insensitively and sorted by count, then repository name |
| Recent public activity | `<!-- ACTIVITY:START -->` / `<!-- ACTIVITY:END -->` | Up to five recent public PR, push or release entries, newest first |

Keep exactly one ordered pair of each marker. The introduction, Technical focus,
Selected Open-Source Contributions and Connect sections are manually maintained
and remain outside these markers. Curated PR summaries are never overwritten.

The project list searches public merged PRs authored by the account, excluding
repositories owned by that account. Counts use unique PR IDs and the upstream
base repository, independent of whether the source repository still exists.
The generator does not fetch or collect fork information and cannot render fork
listings. Open/unmerged PRs, issues, reviews and direct commits are not part of
the project counts. Search visibility and indexing delays apply; deleted or
now-private upstream projects cannot be recovered through public search.

PR search and public events use 100-item pages. Creation-time windows split
recursively when a search exceeds GitHub's 1,000-result ceiling. Missing,
duplicate, changing or incomplete search results fail the run instead of
publishing a partial list. The existing recent-activity section still uses the
public events feed's maximum of 300 events; it is not the historical source.
Activity distinguishes opened, reopened, closed and merged PRs. Repeated events
for the same PR are collapsed to the latest event, with case-insensitive
repository matching; pushes and releases are deduplicated per repository and
event type. Private events and activity in the profile repository are omitted.

Requests are serial, with bounded retries for network/transient server errors
and primary/secondary rate limits, respecting reset and retry headers. The
15-minute workflow timeout bounds execution; rerun after a persistent API
failure. Both sections are generated before an atomic UTF-8 README replacement.
Rendering is deterministic and adds no changing timestamp, avoiding no-op commits.

The workflow grants `contents: write` only to the updating job, for committing
README changes to this repository. It needs no `pull-requests: write` permission
to search public PRs. Repository/organization policies must allow Actions to
write, and branch protection must allow the existing direct-push publishing
step; this change does not bypass those policies. Runs remain weekly, manual,
or triggered by generator/workflow/test changes on `main`. The weekly schedule
is Monday at 06:23 UTC. README-only documentation changes do not trigger a run.
Concurrency serializes
updates. Tests run before any API reads or publishing.

References:

- https://docs.github.com/en/rest/search/search
- https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api
- https://docs.github.com/en/actions/tutorials/authenticate-with-github_token
