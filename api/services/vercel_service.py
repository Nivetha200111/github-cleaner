import os
import requests
from .cache import cache


class VercelService:
    BASE_URL = "https://api.vercel.com"

    def __init__(self, token: str = None):
        self.token = token or os.getenv('VERCEL_TOKEN')
        if not self.token:
            raise ValueError("Vercel token is required")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def list_projects(self) -> list:
        """List all Vercel projects."""
        cache_key = "vercel:projects"
        cached = cache.get(cache_key)
        if cached:
            return cached

        response = requests.get(
            f"{self.BASE_URL}/v9/projects",
            headers=self.headers
        )
        response.raise_for_status()
        data = response.json()
        result = data.get('projects', [])
        cache.set(cache_key, result, ttl=300)  # Cache for 5 minutes
        return result

    def find_project_by_repo(self, repo_name: str, github_username: str = None) -> dict:
        """Find a Vercel project linked to a GitHub repository."""
        projects = self.list_projects()

        for project in projects:
            link = project.get('link', {})
            if link.get('type') == 'github':
                linked_repo = link.get('repo', '')
                if repo_name.lower() in linked_repo.lower():
                    return project

            if project.get('name', '').lower() == repo_name.lower():
                return project

        return None

    def get_project_url(self, repo_name: str, github_username: str = None) -> str:
        """Get the production URL for a project linked to a GitHub repo."""
        cache_key = f"vercel:url:{repo_name.lower()}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        project = self.find_project_by_repo(repo_name, github_username)

        if not project:
            return None

        project_id = project.get('id')
        if not project_id:
            return None

        response = requests.get(
            f"{self.BASE_URL}/v6/deployments",
            headers=self.headers,
            params={
                "projectId": project_id,
                "target": "production",
                "limit": 1
            }
        )

        url = None
        if response.status_code == 200:
            data = response.json()
            deployments = data.get('deployments', [])
            if deployments:
                deployment = deployments[0]
                deployment_url = deployment.get('url')
                if deployment_url:
                    url = f"https://{deployment_url}"

        if not url:
            domains = project.get('targets', {}).get('production', {}).get('alias', [])
            if domains:
                url = f"https://{domains[0]}"

        if not url:
            project_name = project.get('name')
            if project_name:
                url = f"https://{project_name}.vercel.app"

        if url:
            cache.set(cache_key, url, ttl=600)  # Cache for 10 minutes

        return url

    def get_all_project_urls(self) -> dict:
        """Get URLs for all projects, indexed by linked repo name."""
        cache_key = "vercel:all_urls"
        cached = cache.get(cache_key)
        if cached:
            return cached

        projects = self.list_projects()
        urls = {}

        for project in projects:
            link = project.get('link', {})
            project_name = project.get('name', '')

            if link.get('type') == 'github':
                repo = link.get('repo', '')
                key = repo.split('/')[-1] if '/' in repo else repo
            else:
                key = project_name

            if key:
                url = self.get_project_url(key)
                if url:
                    urls[key.lower()] = url

        cache.set(cache_key, urls, ttl=300)  # Cache for 5 minutes
        return urls
