import os
import base64
from github import Github, GithubException


class GitHubService:
    def __init__(self, token: str = None):
        self.token = token or os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GitHub token is required")
        self.github = Github(self.token)
        self.user = self.github.get_user()

    def list_repos(self, include_forks: bool = False):
        """List all repositories for the authenticated user."""
        repos = []
        for repo in self.user.get_repos():
            if not include_forks and repo.fork:
                continue
            repos.append({
                'name': repo.name,
                'full_name': repo.full_name,
                'description': repo.description or '',
                'language': repo.language,
                'stars': repo.stargazers_count,
                'url': repo.html_url,
                'has_readme': self._has_readme(repo),
                'updated_at': repo.updated_at.isoformat() if repo.updated_at else None,
                'private': repo.private
            })
        return sorted(repos, key=lambda x: x['updated_at'] or '', reverse=True)

    def _has_readme(self, repo) -> bool:
        """Check if repository has a README file."""
        try:
            repo.get_readme()
            return True
        except GithubException:
            return False

    def analyze_repo(self, repo_name: str) -> dict:
        """Analyze a repository's structure and content."""
        repo = self.github.get_repo(f"{self.user.login}/{repo_name}")

        analysis = {
            'name': repo.name,
            'description': repo.description or '',
            'language': repo.language,
            'languages': self._get_languages(repo),
            'topics': repo.get_topics(),
            'license': repo.license.name if repo.license else None,
            'structure': self._get_structure(repo),
            'dependencies': self._get_dependencies(repo),
            'has_readme': self._has_readme(repo),
            'existing_readme': self._get_readme_content(repo),
            'key_files': self._identify_key_files(repo)
        }
        return analysis

    def _get_languages(self, repo) -> dict:
        """Get language breakdown for repository."""
        try:
            languages = repo.get_languages()
            total = sum(languages.values())
            if total == 0:
                return {}
            return {lang: round(bytes_count / total * 100, 1)
                    for lang, bytes_count in languages.items()}
        except GithubException:
            return {}

    def _get_structure(self, repo, path: str = "", depth: int = 0, max_depth: int = 2) -> list:
        """Get repository file structure."""
        if depth > max_depth:
            return []

        structure = []
        try:
            contents = repo.get_contents(path)
            for content in contents:
                item = {
                    'name': content.name,
                    'type': content.type,
                    'path': content.path
                }
                if content.type == 'dir' and depth < max_depth:
                    item['children'] = self._get_structure(repo, content.path, depth + 1, max_depth)
                structure.append(item)
        except GithubException:
            pass
        return structure

    def _get_dependencies(self, repo) -> dict:
        """Extract dependencies from common package files."""
        deps = {}

        # Package file mappings
        package_files = {
            'package.json': self._parse_package_json,
            'requirements.txt': self._parse_requirements_txt,
            'Pipfile': self._parse_pipfile,
            'pyproject.toml': self._parse_pyproject,
            'Cargo.toml': self._parse_cargo_toml,
            'go.mod': self._parse_go_mod,
            'Gemfile': self._parse_gemfile,
            'pom.xml': self._parse_pom_xml,
            'composer.json': self._parse_composer_json
        }

        for filename, parser in package_files.items():
            try:
                content = repo.get_contents(filename)
                decoded = base64.b64decode(content.content).decode('utf-8')
                parsed = parser(decoded)
                if parsed:
                    deps[filename] = parsed
            except GithubException:
                continue

        return deps

    def _parse_package_json(self, content: str) -> dict:
        """Parse package.json for dependencies."""
        import json
        try:
            data = json.loads(content)
            return {
                'dependencies': list(data.get('dependencies', {}).keys()),
                'devDependencies': list(data.get('devDependencies', {}).keys()),
                'scripts': list(data.get('scripts', {}).keys())
            }
        except json.JSONDecodeError:
            return {}

    def _parse_requirements_txt(self, content: str) -> list:
        """Parse requirements.txt for dependencies."""
        deps = []
        for line in content.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # Remove version specifiers
                pkg = line.split('==')[0].split('>=')[0].split('<=')[0].split('[')[0]
                deps.append(pkg.strip())
        return deps

    def _parse_pipfile(self, content: str) -> dict:
        """Parse Pipfile for dependencies."""
        packages = []
        in_packages = False
        for line in content.split('\n'):
            if '[packages]' in line:
                in_packages = True
                continue
            if in_packages and line.startswith('['):
                break
            if in_packages and '=' in line:
                pkg = line.split('=')[0].strip().strip('"')
                if pkg:
                    packages.append(pkg)
        return packages

    def _parse_pyproject(self, content: str) -> list:
        """Parse pyproject.toml for dependencies."""
        deps = []
        in_deps = False
        for line in content.split('\n'):
            if 'dependencies' in line and '=' in line:
                in_deps = True
                continue
            if in_deps:
                if line.strip().startswith(']'):
                    break
                if '"' in line:
                    pkg = line.split('"')[1].split('>=')[0].split('==')[0]
                    deps.append(pkg)
        return deps

    def _parse_cargo_toml(self, content: str) -> list:
        """Parse Cargo.toml for dependencies."""
        deps = []
        in_deps = False
        for line in content.split('\n'):
            if '[dependencies]' in line:
                in_deps = True
                continue
            if in_deps and line.startswith('['):
                break
            if in_deps and '=' in line:
                pkg = line.split('=')[0].strip()
                if pkg:
                    deps.append(pkg)
        return deps

    def _parse_go_mod(self, content: str) -> list:
        """Parse go.mod for dependencies."""
        deps = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('require') or '\t' in line:
                parts = line.replace('require', '').strip().split()
                if parts and '/' in parts[0]:
                    deps.append(parts[0])
        return deps

    def _parse_gemfile(self, content: str) -> list:
        """Parse Gemfile for dependencies."""
        deps = []
        for line in content.split('\n'):
            if line.strip().startswith('gem '):
                parts = line.split("'")
                if len(parts) >= 2:
                    deps.append(parts[1])
        return deps

    def _parse_pom_xml(self, content: str) -> list:
        """Parse pom.xml for dependencies (simplified)."""
        import re
        artifacts = re.findall(r'<artifactId>([^<]+)</artifactId>', content)
        return artifacts[:20]  # Limit to avoid noise

    def _parse_composer_json(self, content: str) -> dict:
        """Parse composer.json for dependencies."""
        import json
        try:
            data = json.loads(content)
            return {
                'require': list(data.get('require', {}).keys()),
                'require-dev': list(data.get('require-dev', {}).keys())
            }
        except json.JSONDecodeError:
            return {}

    def _get_readme_content(self, repo) -> str:
        """Get existing README content if available."""
        try:
            readme = repo.get_readme()
            return base64.b64decode(readme.content).decode('utf-8')
        except GithubException:
            return None

    def _identify_key_files(self, repo) -> list:
        """Identify key files that indicate project type."""
        key_files = []
        important_files = [
            'package.json', 'requirements.txt', 'Cargo.toml', 'go.mod',
            'Dockerfile', 'docker-compose.yml', '.github/workflows',
            'Makefile', 'setup.py', 'setup.cfg', 'next.config.js',
            'vite.config.js', 'webpack.config.js', 'tsconfig.json',
            'tailwind.config.js', '.eslintrc', 'jest.config.js'
        ]

        try:
            contents = repo.get_contents("")
            for content in contents:
                if content.name in important_files:
                    key_files.append(content.name)
                if content.type == 'dir' and content.name == '.github':
                    try:
                        github_contents = repo.get_contents('.github')
                        for gc in github_contents:
                            if gc.name == 'workflows':
                                key_files.append('.github/workflows')
                    except GithubException:
                        pass
        except GithubException:
            pass

        return key_files

    def commit_readme(self, repo_name: str, content: str, message: str = "Update README.md") -> bool:
        """Commit a new README to the repository."""
        repo = self.github.get_repo(f"{self.user.login}/{repo_name}")

        try:
            # Try to update existing README
            readme = repo.get_readme()
            repo.update_file(
                path="README.md",
                message=message,
                content=content,
                sha=readme.sha
            )
        except GithubException:
            # Create new README
            repo.create_file(
                path="README.md",
                message=message,
                content=content
            )

        return True

    def get_file_content(self, repo_name: str, file_path: str) -> str:
        """Get content of a specific file."""
        repo = self.github.get_repo(f"{self.user.login}/{repo_name}")
        try:
            content = repo.get_contents(file_path)
            return base64.b64decode(content.content).decode('utf-8')
        except GithubException:
            return None
