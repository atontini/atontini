# Profile generator

Run from the repository root with Python 3.10 or newer:

```sh
python3 -m unittest discover -s .github/scripts -p 'test_*.py' -v
python3 .github/scripts/update_activity.py
```

`GITHUB_REPOSITORY_OWNER` defaults to `atontini`. `GH_TOKEN` is optional for
local public API reads; the workflow uses its built-in `github.token`. No
personal access token or private-repository access is required.

The project list searches public merged PRs authored by the account, excluding
repositories owned by that account. It groups results by the PR's base
repository, so deleted source forks do not remove historical contributions.
It links current forks beside matching contributed projects and lists other
forks separately, without claiming they are contributions. Open/unmerged PRs,
issues, reviews and direct commits are not part of this list. Search visibility
and indexing delays apply; deleted or now-private upstream projects cannot be
recovered through public search.

Repository lists and PR search use 100-item pages. Creation-time windows split
recursively when a search exceeds GitHub's 1,000-result ceiling. Missing,
duplicate, changing or incomplete search results fail the run instead of
publishing a partial list. The existing recent-activity section still uses the
public events feed's maximum of 300 events; it is not the historical source.

Requests are serial, with bounded retries for network/transient server errors
and primary/secondary rate limits, respecting reset and retry headers. The
15-minute workflow timeout bounds execution; rerun after a persistent API
failure. Both sections are generated before an atomic UTF-8 README replacement.
Rendering is sorted and adds no changing timestamp, avoiding no-op commits.

The workflow grants `contents: write` only to the updating job, for committing
README changes to this repository. It needs no `pull-requests: write` permission
to search public PRs. Repository/organization policies must allow Actions to
write, and branch protection must allow the existing direct-push publishing
step; this change does not bypass those policies. Runs remain weekly, manual,
or triggered by generator/workflow/test changes on `main`. Concurrency serializes
updates. Tests run before any API reads or publishing.

References:
- https://docs.github.com/en/rest/search/search
- https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api
- https://docs.github.com/en/actions/tutorials/authenticate-with-github_token
