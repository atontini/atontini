import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import urllib.error
from datetime import datetime, timezone

import update_activity as app


def result(items, total=None, incomplete=False):
    return {'items': items, 'total_count': len(items) if total is None else total,
            'incomplete_results': incomplete}


def pr(number, repo='upstream/project'):
    return {'id': number, 'repository_url': app.API + '/repos/' + repo}


class SearchTests(unittest.TestCase):
    def test_pages_and_query(self):
        api = Mock()
        api.get.side_effect = [result([pr(n) for n in range(100)], 101),
                               result([pr(100)], 101)]
        self.assertEqual(len(list(app.merged_prs(api, 'atontini'))), 101)
        self.assertEqual(api.get.call_args.kwargs['page'], 2)
        query = api.get.call_args.kwargs['q']
        for qualifier in ('is:merged', 'is:public', 'author:atontini', '-user:atontini'):
            self.assertIn(qualifier, query)

    def test_splits_over_search_cap_without_overlap(self):
        api = Mock()
        api.get.side_effect = [result([], 1001), result([pr(1)]), result([pr(2)])]
        start = datetime(2020, 1, 1, tzinfo=timezone.utc)
        end = datetime(2020, 1, 1, 0, 0, 3, tzinfo=timezone.utc)
        self.assertEqual(len(list(app.merged_prs(api, 'me', start, end))), 2)
        queries = [call.kwargs['q'] for call in api.get.call_args_list]
        self.assertIn('created:2020-01-01T00:00:00Z..2020-01-01T00:00:01Z', queries[1])
        self.assertIn('created:2020-01-01T00:00:02Z..2020-01-01T00:00:03Z', queries[2])

    def test_incomplete_missing_and_duplicate_results_fail(self):
        for response in (result([], 1), result([pr(1), pr(1)], 2),
                         result([], incomplete=True)):
            with self.subTest(response=response):
                api = Mock()
                api.get.return_value = response
                with self.assertRaises(RuntimeError):
                    list(app.merged_prs(api, 'me'))

    def test_unsplittable_range_fails(self):
        api = Mock()
        api.get.return_value = result([], 1001)
        date = datetime(2020, 1, 1, tzinfo=timezone.utc)
        with self.assertRaises(RuntimeError):
            list(app.merged_prs(api, 'me', date, date))

    def test_changed_later_page_fails(self):
        api = Mock()
        api.get.side_effect = [result([pr(n) for n in range(100)], 101), result([], 102)]
        with self.assertRaises(RuntimeError):
            list(app.merged_prs(api, 'me'))


class ProjectTests(unittest.TestCase):
    @patch.object(app, 'merged_prs')
    def test_deleted_forks_counts_and_case_insensitive_grouping(self, search):
        search.return_value = [pr(1), pr(2, 'Upstream/Project'), pr(2),
                               pr(3, 'old/deleted-fork')]
        api = Mock()
        api.pages.return_value = [
            {'full_name': 'me/project', 'fork': True},
            {'full_name': 'me/other', 'fork': True},
            {'full_name': 'me/own', 'fork': False},
            {'full_name': 'me/secret', 'fork': True, 'private': True},
        ]
        api.get.side_effect = [{'parent': {'full_name': 'UPSTREAM/project'}},
                               {'parent': {'full_name': 'another/project'}}]
        body = '\n'.join(app.project_lines(api, 'me'))
        self.assertIn('2 merged PRs', body)
        self.assertIn('old/deleted-fork', body)
        self.assertIn('[current fork](https://github.com/me/project)', body)
        contributed, forks = body.split('### Other current forks')
        self.assertNotIn('UPSTREAM/project', forks)
        self.assertIn('another/project', forks)
        self.assertNotIn('secret', body)
        self.assertEqual(api.get.call_count, 2)

    @patch.object(app, 'merged_prs', return_value=[])
    def test_empty_state(self, search):
        api = Mock()
        api.pages.return_value = []
        body = '\n'.join(app.project_lines(api, 'me'))
        self.assertIn('No public merged', body)
        self.assertIn('No other public forks', body)


class ApiTests(unittest.TestCase):
    def test_repository_pagination(self):
        api = app.GitHub()
        api.get = Mock(side_effect=[list(range(100)), [100]])
        self.assertEqual(len(list(api.pages('/users/me/repos'))), 101)
        self.assertEqual(api.get.call_args.kwargs['page'], 2)

    @patch.object(app.time, 'sleep')
    @patch.object(app.urllib.request, 'urlopen')
    def test_primary_secondary_and_server_retries(self, open_url, sleep):
        for code, headers in ((403, {'X-RateLimit-Remaining': '0',
                                     'X-RateLimit-Reset': '1010'}),
                              (429, {'Retry-After': '90'}),
                              (403, {}), (503, {})):
            with self.subTest(code=code, headers=headers):
                response = Mock()
                response.__enter__ = Mock(return_value=response)
                response.__exit__ = Mock(return_value=False)
                response.read.return_value = b'[]'
                response.headers = {}
                error = urllib.error.HTTPError('url', code, 'error', headers,
                                               io.BytesIO(b'secondary rate limit'))
                open_url.side_effect = [error, response]
                with patch.object(app.time, 'time', return_value=1000):
                    self.assertEqual(app.GitHub().get('/users/me/repos'), [])
                self.assertGreater(sleep.call_args.args[0], 0)

    @patch.object(app.time, 'sleep')
    @patch.object(app.urllib.request, 'urlopen')
    def test_retry_budget_and_permission_failure(self, open_url, sleep):
        open_url.side_effect = urllib.error.HTTPError('url', 503, 'error', {}, None)
        with self.assertRaises(urllib.error.HTTPError):
            app.GitHub().get('/search/issues')
        self.assertEqual(open_url.call_count, 5)
        open_url.reset_mock()
        open_url.side_effect = urllib.error.HTTPError('url', 403, 'forbidden', {}, None)
        with self.assertRaises(urllib.error.HTTPError):
            app.GitHub().get('/search/issues')
        self.assertEqual(open_url.call_count, 1)

    @patch.object(app.time, 'sleep')
    @patch.object(app.time, 'time', return_value=1000)
    @patch.object(app.urllib.request, 'urlopen')
    def test_successful_response_with_exhausted_budget_waits(self, open_url, now, sleep):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = b'[]'
        response.headers = {'X-RateLimit-Remaining': '0', 'X-RateLimit-Reset': '1010'}
        open_url.return_value = response
        api = app.GitHub()
        api.get('/search/issues')
        api.get('/search/issues')
        sleep.assert_called_once_with(11)


class ReadmeTests(unittest.TestCase):
    def test_marker_validation_and_preservation(self):
        original = 'before\n' + app.START + '\nold\n' + app.END + '\nafter'
        updated = app.replace_section(original, app.START, app.END, 'new')
        self.assertEqual(updated, original.replace('\nold\n', '\nnew\n'))
        for invalid in ('none', app.END + app.START, original + app.START):
            with self.assertRaises(ValueError):
                app.replace_section(invalid, app.START, app.END, 'new')

    @patch.object(app, 'project_lines', side_effect=RuntimeError('incomplete search'))
    @patch.object(app, 'GitHub')
    def test_api_failure_preserves_existing_readme(self, github, projects):
        github.return_value.pages.return_value = []
        original = f'Andrea —\n{app.START}\nold\n{app.END}\n{app.PROJECTS_START}\nold\n{app.PROJECTS_END}'
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as folder:
            try:
                os.chdir(folder)
                Path('README.md').write_text(original, encoding='utf-8')
                with self.assertRaises(RuntimeError):
                    app.main()
                self.assertEqual(Path('README.md').read_text(encoding='utf-8'), original)
            finally:
                os.chdir(previous)

    @patch.object(app, 'project_lines', return_value=['- project'])
    @patch.object(app, 'GitHub')
    def test_successful_update_is_utf8_and_idempotent(self, github, projects):
        github.return_value.pages.return_value = []
        original = f'Andrea —\n{app.START}\nold\n{app.END}\n{app.PROJECTS_START}\nold\n{app.PROJECTS_END}'
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as folder:
            try:
                os.chdir(folder)
                path = Path('README.md')
                path.write_text(original, encoding='utf-8')
                app.main()
                first = path.read_bytes()
                app.main()
                self.assertEqual(path.read_bytes(), first)
                self.assertIn('Andrea —', path.read_text(encoding='utf-8'))
                self.assertFalse(Path('README.md.tmp').exists())
            finally:
                os.chdir(previous)

    def test_recent_activity_still_deduplicates(self):
        event = {'created_at': '2026-01-01T12:00:00Z', 'public': True,
                 'repo': {'name': 'upstream/project'}, 'type': 'PullRequestEvent',
                 'payload': {'action': 'closed', 'pull_request': {'number': 3, 'merged': True}}}
        lines = app.activity_lines([event, event], 'me')
        self.assertEqual(len(lines), 1)
        self.assertIn('Merged pull request', lines[0])


if __name__ == '__main__':
    unittest.main()
