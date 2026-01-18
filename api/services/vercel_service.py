import os
import requests


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
        response = requests.get(
            f"{self.BASE_URL}/v9/projects",
            headers=self.headers
        )
        response.raise_for_status()
        data = response.json()
        return data.get('projects', [])

    def find_project_by_repo(self, repo_name: str, github_username: str = None) -> dict:
        """Find a Vercel project linked to a GitHub repository."""
        projects = self.list_projects()

        for project in projects:
            # Check if project is linked to the repo
            link = project.get('link', {})
            if link.get('type') == 'github':
                linked_repo = link.get('repo', '')
                # Match by repo name (with or without owner)
                if repo_name.lower() in linked_repo.lower():
                    return project

            # Also check project name as fallback
            if project.get('name', '').lower() == repo_name.lower():
                return project

        return None

    def get_project_url(self, repo_name: str, github_username: str = None) -> str:
        """Get the production URL for a project linked to a GitHub repo."""
        project = self.find_project_by_repo(repo_name, github_username)

        if not project:
            return None

        # Get production deployment URL
        project_id = project.get('id')
        if not project_id:
            return None

        # Try to get the latest production deployment
        response = requests.get(
            f"{self.BASE_URL}/v6/deployments",
            headers=self.headers,
            params={
                "projectId": project_id,
                "target": "production",
                "limit": 1
            }
        )

        if response.status_code == 200:
            data = response.json()
            deployments = data.get('deployments', [])
            if deployments:
                deployment = deployments[0]
                url = deployment.get('url')
                if url:
                    return f"https://{url}"

        # Fallback to project domains
        domains = project.get('targets', {}).get('production', {}).get('alias', [])
        if domains:
            return f"https://{domains[0]}"

        # Last resort: use project name
        project_name = project.get('name')
        if project_name:
            return f"https://{project_name}.vercel.app"

        return None

    def get_project_details(self, project_name: str) -> dict:
        """Get detailed information about a Vercel project."""
        response = requests.get(
            f"{self.BASE_URL}/v9/projects/{project_name}",
            headers=self.headers
        )

        if response.status_code == 200:
            project = response.json()
            return {
                'name': project.get('name'),
                'framework': project.get('framework'),
                'url': self.get_project_url(project_name),
                'created_at': project.get('createdAt'),
                'updated_at': project.get('updatedAt'),
                'github_repo': project.get('link', {}).get('repo'),
                'domains': self._get_project_domains(project)
            }

        return None

    def _get_project_domains(self, project: dict) -> list:
        """Extract all domains for a project."""
        domains = []

        # Get aliases from targets
        targets = project.get('targets', {})
        if 'production' in targets:
            domains.extend(targets['production'].get('alias', []))

        # Get custom domains
        project_domains = project.get('alias', [])
        if isinstance(project_domains, list):
            domains.extend([d.get('domain') if isinstance(d, dict) else d
                          for d in project_domains])

        return list(set(domains))

    def get_all_project_urls(self) -> dict:
        """Get URLs for all projects, indexed by linked repo name."""
        projects = self.list_projects()
        urls = {}

        for project in projects:
            link = project.get('link', {})
            project_name = project.get('name', '')

            # Use linked repo name if available, otherwise project name
            if link.get('type') == 'github':
                repo = link.get('repo', '')
                # Extract repo name from "owner/repo" format
                key = repo.split('/')[-1] if '/' in repo else repo
            else:
                key = project_name

            if key:
                url = self.get_project_url(key)
                if url:
                    urls[key.lower()] = url

        return urls
