"""Refresh public activity, merged upstream PRs, and current forks."""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.parse
import urllib.request

START = '<!-- ACTIVITY:START -->'
END = '<!-- ACTIVITY:END -->'
PROJECTS_START = '<!-- PROJECTS:START -->'
PROJECTS_END = '<!-- PROJECTS:END -->'
API = 'https://api.github.com'


class GitHub:
    """Serial requests with bounded retries; never publish a partial snapshot."""

    def __init__(self, token=None):
        self.headers = {
            'Accept': 'application/vnd.github+json',
            'User-Agent': 'profile-activity',
            'X-GitHub-Api-Version': '2022-11-28',
        }
        if token:
            self.headers['Authorization'] = f'Bearer {token}'
        self.ready_at = {}

    def get(self, path, **params):
        resource = 'search' if path.startswith('/search/') else 'core'
        url = API + path + ('?' + urllib.parse.urlencode(params) if params else '')
        for attempt in range(5):
            delay = self.ready_at.get(resource, 0) - time.time()
            if delay > 0:
                time.sleep(delay)
            try:
                request = urllib.request.Request(url, headers=self.headers)
                with urllib.request.urlopen(request, timeout=30) as response:
                    data = json.load(response)
                    if response.headers.get('X-RateLimit-Remaining') == '0':
                        self.ready_at[resource] = float(
                            response.headers['X-RateLimit-Reset']) + 1
                    return data
            except urllib.error.HTTPError as exc:
                message = exc.read().decode('utf-8', errors='replace').lower()
                limited = exc.code == 429 or (
                    exc.code == 403 and (
                        exc.headers.get('X-RateLimit-Remaining') == '0'
                        or exc.headers.get('Retry-After')
                        or 'rate limit' in message))
                if attempt == 4 or not (limited or exc.code in (500, 502, 503, 504)):
                    raise
                delay = 60 * (2 ** attempt) if limited else 2 ** attempt
                if exc.headers.get('Retry-After'):
                    delay = max(delay, float(exc.headers['Retry-After']))
                if exc.headers.get('X-RateLimit-Remaining') == '0':
                    delay = max(delay, float(exc.headers['X-RateLimit-Reset']) - time.time() + 1)
                # The workflow timeout bounds the total wait. No README is written yet.
                time.sleep(delay)
            except (urllib.error.URLError, TimeoutError):
                if attempt == 4:
                    raise
                time.sleep(2 ** attempt)

    def pages(self, path, max_pages=None, **params):
        page = 1
        while max_pages is None or page <= max_pages:
            batch = self.get(path, per_page=100, page=page, **params)
            yield from batch
            if len(batch) < 100:
                return
            page += 1


def merged_prs(api, username, start=None, end=None):
    """Split creation-time ranges to avoid Search's 1,000-result ceiling."""
    start = start or datetime(2008, 1, 1, tzinfo=timezone.utc)
    end = end or datetime.now(timezone.utc).replace(microsecond=0)
    stamp = lambda value: value.strftime('%Y-%m-%dT%H:%M:%SZ')
    query = (f'is:pr is:merged is:public author:{username} -user:{username} '
             f'created:{stamp(start)}..{stamp(end)}')
    first = api.get('/search/issues', q=query, per_page=100, page=1,
                    sort='created', order='asc')
    if first.get('incomplete_results'):
        raise RuntimeError('GitHub returned incomplete search results; README unchanged')
    total = first['total_count']
    if total > 1000:
        seconds = int((end - start).total_seconds())
        if seconds == 0:
            raise RuntimeError('Search exceeds 1,000 PRs in one second; README unchanged')
        middle = start + timedelta(seconds=seconds // 2)
        yield from merged_prs(api, username, start, middle)
        yield from merged_prs(api, username, middle + timedelta(seconds=1), end)
        return
    items = list(first['items'])
    for page in range(2, (total + 99) // 100 + 1):
        batch = api.get('/search/issues', q=query, per_page=100, page=page,
                        sort='created', order='asc')
        if batch.get('incomplete_results') or batch['total_count'] != total:
            raise RuntimeError('Search changed or is incomplete; retry the workflow')
        items.extend(batch['items'])
    if len({item['id'] for item in items}) != total:
        raise RuntimeError('Search returned missing or duplicate PRs; retry the workflow')
    yield from items


def project_lines(api, username):
    contributed = {}
    for pr in merged_prs(api, username):
        # Use the base repository, independent of the PR's possibly deleted head.
        repo = pr['repository_url'].removeprefix(API + '/repos/')
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo):
            raise ValueError('Invalid repository name in search results')
        entry = contributed.setdefault(repo.lower(), {'name': repo, 'prs': set(), 'forks': set()})
        entry['prs'].add(pr['id'])

    forks = {}
    for repo in api.pages(f'/users/{username}/repos', type='owner', sort='full_name'):
        if not repo['fork'] or repo.get('private'):
            continue
        detail = api.get(f"/repos/{repo['full_name']}")
        parent = detail.get('parent')
        if parent and not parent.get('private'):
            key = parent['full_name'].lower()
            name = parent['full_name']
        else:
            key = repo['full_name'].lower()
            name = repo['full_name']
        entry = contributed.get(key)
        if entry is None:
            entry = forks.setdefault(key, {'name': name, 'forks': set()})
        entry['forks'].add(repo['full_name'])

    lines = ['### Contributed projects (merged pull requests)', '']
    for entry in sorted(contributed.values(),
                        key=lambda e: (-len(e['prs']), e['name'].lower())):
        name = entry['name']
        count = len(entry['prs'])
        query = urllib.parse.urlencode({'q': f'is:pr is:merged author:{username}'})
        line = (f"- [{name}](https://github.com/{name}) — "
                f"[{count} merged {'PR' if count == 1 else 'PRs'}]"
                f"(https://github.com/{name}/pulls?{query})")
        for fork in sorted(entry['forks']):
            line += f' · [current fork](https://github.com/{fork})'
        lines.append(line)
    if not contributed:
        lines.append('No public merged upstream pull requests found.')
    lines.extend(['', '### Other current forks', '',
                  'Forks alone do not imply an upstream contribution.', ''])
    for entry in sorted(forks.values(), key=lambda e: e['name'].lower()):
        name = entry['name']
        links = ', '.join(f'[{fork}](https://github.com/{fork})'
                          for fork in sorted(entry['forks']))
        lines.append(f'- [{name}](https://github.com/{name}) — fork: {links}')
    if not forks:
        lines.append('No other public forks.')
    return lines


def replace_section(original, start, end, body):
    if original.count(start) != 1 or original.count(end) != 1:
        raise ValueError(f'Expected exactly one pair of {start} / {end} markers')
    before, rest = original.split(start)
    if end not in rest:
        raise ValueError('Section markers are out of order')
    _, after = rest.split(end)
    return before + start + '\n' + body + '\n' + end + after


def activity_lines(events, username):
    lines = []
    seen = set()
    for event in sorted(events, key=lambda e: e['created_at'], reverse=True):
        repo = event['repo']['name']
        if not event.get('public') or repo.lower() == f'{username}/{username}'.lower():
            continue
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo):
            continue
        payload = event['payload']
        kind = event['type']
        url = f'https://github.com/{repo}'
        if kind == 'PullRequestEvent':
            pr = payload['pull_request']
            action = 'merged' if pr.get('merged') else payload.get('action')
            if action not in ('opened', 'reopened', 'closed', 'merged'):
                continue
            number = pr['number']
            if not isinstance(number, int):
                continue
            text = f'{action.capitalize()} pull request [{repo}#{number}]({url}/pull/{number})'
            key = (kind, repo, number)
        elif kind == 'PushEvent':
            text = f'Pushed changes to [{repo}]({url})'
            key = (kind, repo)
        elif kind == 'ReleaseEvent' and payload.get('action') == 'published':
            text = f'Published a release in [{repo}]({url}/releases)'
            key = (kind, repo)
        else:
            continue
        if key in seen:
            continue
        seen.add(key)
        date = event['created_at'][:10]
        lines.append(f'- {date} — {text}')
        if len(lines) == 5:
            break
    return lines


def main():
    username = os.environ.get('GITHUB_REPOSITORY_OWNER', 'atontini')
    if not re.fullmatch(r'[A-Za-z0-9-]+', username):
        raise ValueError('Invalid GitHub username')
    api = GitHub(os.environ.get('GH_TOKEN'))
    events = list(api.pages(f'/users/{username}/events/public', max_pages=3))
    lines = activity_lines(events, username)
    body = '\n'.join(lines) or 'No recent public pushes, pull requests, or releases in the GitHub activity feed.'
    path = Path('README.md')
    original = path.read_text(encoding='utf-8')
    updated = replace_section(original, START, END, body)
    updated = replace_section(updated, PROJECTS_START, PROJECTS_END,
                              '\n'.join(project_lines(api, username)))
    if updated != original:
        # Replace only after every request and validation succeeds.
        temporary = path.with_suffix('.md.tmp')
        try:
            temporary.write_text(updated, encoding='utf-8')
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
