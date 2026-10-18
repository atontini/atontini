"""Refresh the marked README section from GitHub's public events feed."""
import json
import os
from pathlib import Path
import re
import urllib.request

START = '<!-- ACTIVITY:START -->'
END = '<!-- ACTIVITY:END -->'


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
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'profile-activity'}
    if os.environ.get('GH_TOKEN'):
        headers['Authorization'] = f"Bearer {os.environ['GH_TOKEN']}"
    events = []
    for page in range(1, 4):
        url = f'https://api.github.com/users/{username}/events/public?per_page=100&page={page}'
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
            batch = json.load(response)
        events.extend(batch)
        if len(batch) < 100:
            break
    lines = activity_lines(events, username)
    body = '\n'.join(lines) or 'No recent public pushes, pull requests, or releases in the GitHub activity feed.'
    path = Path('README.md')
    original = path.read_text()
    if original.count(START) != 1 or original.count(END) != 1:
        raise ValueError('Expected exactly one pair of activity markers')
    before, rest = original.split(START)
    _, after = rest.split(END)
    updated = before + START + '\n' + body + '\n' + END + after
    if updated != original:
        path.write_text(updated)


if __name__ == '__main__':
    main()
