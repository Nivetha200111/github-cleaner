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

    def scan_security(self, repo_name: str) -> dict:
        """Scan repository for security issues like exposed secrets."""
        repo = self.github.get_repo(f"{self.user.login}/{repo_name}")

        issues = []
        warnings = []

        # Dangerous files that should never be committed
        dangerous_files = [
            '.env', '.env.local', '.env.production', '.env.development',
            'credentials.json', 'service-account.json', 'secrets.json',
            'config.json', '.npmrc', '.pypirc', 'id_rsa', 'id_ed25519',
            '.htpasswd', 'wp-config.php', 'database.yml'
        ]

        # Patterns that indicate secrets in file content
        secret_patterns = [
            ('API_KEY', 'API Key exposed'),
            ('SECRET_KEY', 'Secret Key exposed'),
            ('PRIVATE_KEY', 'Private Key exposed'),
            ('ghp_', 'GitHub Token exposed'),
            ('sk-', 'OpenAI/Stripe Key exposed'),
            ('AIzaSy', 'Google API Key exposed'),
            ('AKIA', 'AWS Access Key exposed'),
            ('password', 'Password found'),
            ('Bearer ', 'Bearer token exposed'),
        ]

        try:
            contents = repo.get_contents("")
            all_files = self._get_all_files(repo, contents)

            for file_path in all_files:
                filename = file_path.split('/')[-1]

                # Check for dangerous files
                if filename in dangerous_files:
                    issues.append({
                        'type': 'CRITICAL',
                        'file': file_path,
                        'message': f'Sensitive file "{filename}" is committed to repo!'
                    })

                # Check for env files with secrets
                if filename.endswith('.env') or 'config' in filename.lower():
                    try:
                        content = repo.get_contents(file_path)
                        decoded = base64.b64decode(content.content).decode('utf-8')

                        for pattern, msg in secret_patterns:
                            if pattern.lower() in decoded.lower():
                                # Check if it's not just a placeholder
                                lines = decoded.split('\n')
                                for line in lines:
                                    if pattern.lower() in line.lower() and '=' in line:
                                        value = line.split('=', 1)[1].strip().strip('"').strip("'")
                                        if value and value not in ['', 'your_key_here', 'xxx', 'YOUR_API_KEY']:
                                            issues.append({
                                                'type': 'CRITICAL',
                                                'file': file_path,
                                                'message': msg
                                            })
                                            break
                    except:
                        pass

            # Check if .gitignore exists and has proper entries
            has_gitignore = False
            gitignore_missing = []

            try:
                gitignore = repo.get_contents('.gitignore')
                has_gitignore = True
                gitignore_content = base64.b64decode(gitignore.content).decode('utf-8').lower()

                should_ignore = ['.env', 'node_modules', '__pycache__', '.venv', 'venv', '*.pyc']
                for item in should_ignore:
                    if item not in gitignore_content:
                        gitignore_missing.append(item)

                if gitignore_missing:
                    warnings.append({
                        'type': 'WARNING',
                        'file': '.gitignore',
                        'message': f'Missing entries: {", ".join(gitignore_missing)}'
                    })
            except:
                warnings.append({
                    'type': 'WARNING',
                    'file': '.gitignore',
                    'message': 'No .gitignore file found!'
                })

        except GithubException as e:
            pass

        return {
            'issues': issues,
            'warnings': warnings,
            'score': max(0, 100 - (len(issues) * 25) - (len(warnings) * 10)),
            'has_critical': len(issues) > 0
        }

    def _get_all_files(self, repo, contents, path="") -> list:
        """Recursively get all files in repo."""
        files = []
        for content in contents:
            if content.type == 'file':
                files.append(content.path)
            elif content.type == 'dir' and content.name not in ['node_modules', '.git', 'vendor', '__pycache__']:
                try:
                    dir_contents = repo.get_contents(content.path)
                    files.extend(self._get_all_files(repo, dir_contents, content.path))
                except:
                    pass
        return files[:100]  # Limit to prevent API rate limits

    def generate_gitignore(self, repo_name: str, language: str = None) -> str:
        """Generate appropriate .gitignore based on project type."""
        repo = self.github.get_repo(f"{self.user.login}/{repo_name}")

        if not language:
            language = repo.language or 'Node'

        templates = {
            'JavaScript': '''# Dependencies
node_modules/
.pnp/
.pnp.js

# Build
dist/
build/
.next/
out/

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Logs
*.log
npm-debug.log*
''',
            'TypeScript': '''# Dependencies
node_modules/
.pnp/
.pnp.js

# Build
dist/
build/
.next/
out/
*.tsbuildinfo

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
''',
            'Python': '''# Byte-compiled
__pycache__/
*.py[cod]
*$py.class
*.so

# Virtual environments
.venv/
venv/
env/
ENV/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# Distribution
dist/
build/
*.egg-info/

# OS
.DS_Store
''',
            'Go': '''# Binaries
*.exe
*.exe~
*.dll
*.so
*.dylib

# Build
/bin/
/pkg/

# Environment
.env

# IDE
.vscode/
.idea/

# OS
.DS_Store
''',
            'Rust': '''# Build
/target/
Cargo.lock

# Environment
.env

# IDE
.vscode/
.idea/

# OS
.DS_Store
'''
        }

        return templates.get(language, templates['JavaScript'])

    def commit_gitignore(self, repo_name: str, content: str) -> bool:
        """Commit .gitignore to repository."""
        repo = self.github.get_repo(f"{self.user.login}/{repo_name}")

        try:
            existing = repo.get_contents('.gitignore')
            repo.update_file(
                path='.gitignore',
                message='Update .gitignore via GitHub Cleaner',
                content=content,
                sha=existing.sha
            )
        except GithubException:
            repo.create_file(
                path='.gitignore',
                message='Add .gitignore via GitHub Cleaner',
                content=content
            )
        return True

    def generate_license(self, license_type: str = 'MIT') -> str:
        """Generate license content."""
        import datetime
        year = datetime.datetime.now().year

        licenses = {
            'MIT': f'''MIT License

Copyright (c) {year}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
''',
            'Apache-2.0': f'''Apache License
Version 2.0, January 2004
http://www.apache.org/licenses/

Copyright {year}

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''
        }
        return licenses.get(license_type, licenses['MIT'])

    def commit_license(self, repo_name: str, content: str) -> bool:
        """Commit LICENSE to repository."""
        repo = self.github.get_repo(f"{self.user.login}/{repo_name}")

        try:
            existing = repo.get_contents('LICENSE')
            repo.update_file(
                path='LICENSE',
                message='Update LICENSE via GitHub Cleaner',
                content=content,
                sha=existing.sha
            )
        except GithubException:
            repo.create_file(
                path='LICENSE',
                message='Add LICENSE via GitHub Cleaner',
                content=content
            )
        return True

    def get_repo_health(self, repo_name: str) -> dict:
        """Calculate overall repository health score."""
        repo = self.github.get_repo(f"{self.user.login}/{repo_name}")

        score = 0
        checks = []

        # Has README
        has_readme = self._has_readme(repo)
        checks.append({'name': 'README', 'passed': has_readme, 'weight': 20})
        if has_readme:
            score += 20

        # Has License
        has_license = repo.license is not None
        checks.append({'name': 'LICENSE', 'passed': has_license, 'weight': 15})
        if has_license:
            score += 15

        # Has .gitignore
        has_gitignore = False
        try:
            repo.get_contents('.gitignore')
            has_gitignore = True
            score += 15
        except:
            pass
        checks.append({'name': '.gitignore', 'passed': has_gitignore, 'weight': 15})

        # Has description
        has_desc = bool(repo.description)
        checks.append({'name': 'Description', 'passed': has_desc, 'weight': 10})
        if has_desc:
            score += 10

        # Has topics
        topics = repo.get_topics()
        has_topics = len(topics) > 0
        checks.append({'name': 'Topics', 'passed': has_topics, 'weight': 10})
        if has_topics:
            score += 10

        # Recent activity (within 6 months)
        from datetime import datetime, timezone
        if repo.pushed_at:
            days_since_push = (datetime.now(timezone.utc) - repo.pushed_at).days
            is_active = days_since_push < 180
            checks.append({'name': 'Active', 'passed': is_active, 'weight': 15})
            if is_active:
                score += 15

        # Security scan
        security = self.scan_security(repo_name)
        is_secure = not security['has_critical']
        checks.append({'name': 'No Secrets Exposed', 'passed': is_secure, 'weight': 15})
        if is_secure:
            score += 15

        return {
            'score': score,
            'grade': 'A' if score >= 90 else 'B' if score >= 75 else 'C' if score >= 60 else 'D' if score >= 40 else 'F',
            'checks': checks,
            'security': security
        }
