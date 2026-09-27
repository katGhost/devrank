import requests
from cachetools import TTLCache
from datetime import datetime, timedelta, timezone
from app.config import Config

# 1-hour in-memory cache
weekly_score_cache = TTLCache(maxsize=100, ttl=3600)

class GithubService:
    GITHUB_API_BASE_URL = Config.GITHUB_API_BASE_URL

    def __init__(self, token: str):
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            # required by GitHub API
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }

    def get_user_repos(self):
        """Fetch ALL user repos across all pages, excluding forks."""
        repos = []
        page = 1

        while True:
            response = requests.get(
                f'{self.GITHUB_API_BASE_URL}/user/repos',
                headers=self.headers,
                params={
                    'per_page': 100,   # max allowed by GitHub
                    'page': page,
                    'type': 'owner',   # only repos the user owns, no collaborations
                    'sort': 'updated', # most recently updated first
                }
            )
            response.raise_for_status()
            page_repos = response.json()

            # no more pages
            if not page_repos:
                break

            for repo in page_repos:
                # skip forks and archived repos
                if repo.get('fork') or repo.get('archived'):
                    continue
                repos.append(repo)

            # GitHub returns less than per_page on the last page
            if len(page_repos) < 100:
                break

            page += 1

        return repos

    def get_repo_commits(self, repo_full_name, since, github_username):
        """Get commits by the authenticated user in a repo since a given date."""
        commits = []
        page = 1

        while True:
            response = requests.get(
                f'{self.GITHUB_API_BASE_URL}/repos/{repo_full_name}/commits',
                headers=self.headers,
                params={
                    'since': since.isoformat(),
                    'author': github_username,  # only this user's activity
                    'per_page': 100,
                    'page': page,
                }
            )

            # repo may be empty or inaccessible
            if response.status_code in (404, 409):
                break

            response.raise_for_status()
            page_commits = response.json()

            if not page_commits:
                break

            commits.extend(page_commits)

            if len(page_commits) < 100:
                break

            page += 1

        return commits

    def get_authenticated_user(self):
        """Fetch the authenticated user's information."""
        response = requests.get(
            f'{self.GITHUB_API_BASE_URL}/user',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_weekly_contributions(self, github_username: str):
        """Return total commits across all owned repos in the past 7 days."""
        cache_key = f"{self.token}:{github_username}"
        if cache_key in weekly_score_cache:
            return weekly_score_cache[cache_key]

        since = datetime.now(timezone.utc) - timedelta(days=7)
        repos = self.get_user_repos()
        total_commits = 0

        for repo in repos:
            commits = self.get_repo_commits(
                repo['full_name'],
                since,
                github_username
            )
            total_commits += len(commits)
            

        weekly_score_cache[cache_key] = total_commits
        return total_commits
    
    """
    get or extract user experience level from GitHub profile
    summarize user activity
    """
    def summarize_user_activity(self):
        since_last_7_days = datetime.now(timezone.utc) - timedelta(days=7)
        since_last_year = datetime.now(timezone.utc) - timedelta(days=365)

        user = self.get_authenticated_user()
        username = user['login']

        all_repos = self.get_user_repos()
        repos = all_repos[:5]

        total_commits = 0
        commits_last_7_days = 0
        languages = set()
        repo_contributions = {}
        active_repos = []

        for repo in repos:
            fullname = repo['full_name']
            repo_name = repo['name']

            all_commits = self.get_repo_commits(fullname, since_last_year, username)
            total_commits += len(all_commits)

            repo_weekly_commits = sum(
                1 for c in all_commits
                if datetime.fromisoformat(
                    c['commit']['author']['date'].replace('Z', '+00:00')
                ) >= since_last_7_days
            )
            commits_last_7_days += repo_weekly_commits
            repo_contributions[repo_name] = repo_weekly_commits

            if repo_weekly_commits > 0:
                active_repos.append(repo_name)

            if repo.get('language'):
                languages.add(repo['language'])

        if total_commits < 30 or len(all_repos) < 3:
            level = 'Beginner'
        elif total_commits < 150 and len(all_repos) >= 3:
            level = 'Intermediate'
        else:
            level = 'Advanced'

        return {
            'username': username,
            'experience_level': level,
            'commits_last_week': commits_last_7_days,
            'languages_used': list(languages),
            'repos_contributed': [r["name"] for r in all_repos],
            'repo_contributions': repo_contributions,
            'total_commits': total_commits,
            'active_repos_count': len(active_repos)
        }

    







