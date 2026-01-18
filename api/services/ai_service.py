import os
import google.generativeai as genai


class AIService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GOOGLE_AI_API_KEY')
        if not self.api_key:
            raise ValueError("Google AI API key is required")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def generate_readme(self, analysis: dict, vercel_url: str = None) -> str:
        """Generate a README based on repository analysis."""
        prompt = self._build_readme_prompt(analysis, vercel_url)

        response = self.model.generate_content(prompt)
        return response.text

    def _build_readme_prompt(self, analysis: dict, vercel_url: str = None) -> str:
        """Build the prompt for README generation."""
        deps_summary = self._format_dependencies(analysis.get('dependencies', {}))
        structure_summary = self._format_structure(analysis.get('structure', []))

        prompt = f"""Generate a professional README.md for a GitHub repository with the following details:

## Repository Information
- **Name**: {analysis.get('name', 'Unknown')}
- **Description**: {analysis.get('description', 'No description provided')}
- **Primary Language**: {analysis.get('language', 'Unknown')}
- **Languages Used**: {', '.join(f"{lang} ({pct}%)" for lang, pct in analysis.get('languages', {}).items())}
- **Topics/Tags**: {', '.join(analysis.get('topics', [])) or 'None'}
- **License**: {analysis.get('license', 'Not specified')}

## Project Structure
{structure_summary}

## Dependencies
{deps_summary}

## Key Files Detected
{', '.join(analysis.get('key_files', [])) or 'None'}

## Existing README Content (for reference, improve upon it)
{analysis.get('existing_readme', 'No existing README')[:2000] if analysis.get('existing_readme') else 'No existing README'}

{f"## Live Demo URL: {vercel_url}" if vercel_url else ""}

---

Generate a comprehensive README.md that includes:
1. A clear project title with appropriate badges (build status, license, language)
2. A concise but informative description
3. Key features (infer from the code structure and dependencies)
4. Tech stack section with icons/badges
5. Prerequisites and installation instructions
6. Usage examples with code snippets
7. {f"Live demo section with the URL: {vercel_url}" if vercel_url else "Placeholder for demo link"}
8. Contributing guidelines (brief)
9. License information

Use proper markdown formatting. Make it visually appealing with appropriate headers, code blocks, and badges.
Keep it professional and developer-friendly.
Do NOT include any explanatory text before or after the README - output ONLY the README content.
"""
        return prompt

    def _format_dependencies(self, deps: dict) -> str:
        """Format dependencies for the prompt."""
        if not deps:
            return "No dependencies detected"

        lines = []
        for file, packages in deps.items():
            if isinstance(packages, list):
                lines.append(f"**{file}**: {', '.join(packages[:15])}")
            elif isinstance(packages, dict):
                for key, pkgs in packages.items():
                    if isinstance(pkgs, list) and pkgs:
                        lines.append(f"**{file} ({key})**: {', '.join(pkgs[:10])}")

        return '\n'.join(lines) if lines else "No dependencies detected"

    def _format_structure(self, structure: list, indent: int = 0) -> str:
        """Format file structure for the prompt."""
        if not structure:
            return "Unable to fetch structure"

        lines = []
        for item in structure[:30]:  # Limit to avoid token overflow
            prefix = "  " * indent
            icon = "📁" if item.get('type') == 'dir' else "📄"
            lines.append(f"{prefix}{icon} {item.get('name', 'unknown')}")
            if 'children' in item:
                lines.append(self._format_structure(item['children'], indent + 1))

        return '\n'.join(lines)

    def analyze_code_quality(self, analysis: dict) -> dict:
        """Analyze code quality and provide suggestions."""
        prompt = f"""Analyze this repository and provide brief suggestions:

Repository: {analysis.get('name')}
Language: {analysis.get('language')}
Has README: {analysis.get('has_readme')}
Key files: {analysis.get('key_files')}
Dependencies: {list(analysis.get('dependencies', {}).keys())}

Provide a JSON response with:
1. "score": overall score 1-10
2. "suggestions": list of 3-5 improvement suggestions
3. "missing": list of commonly expected files that are missing
4. "strengths": list of 2-3 things done well

Output ONLY valid JSON, no markdown or explanation."""

        response = self.model.generate_content(prompt)
        text = response.text.strip()

        # Try to parse as JSON
        import json
        try:
            # Remove markdown code blocks if present
            if text.startswith('```'):
                text = text.split('\n', 1)[1].rsplit('\n', 1)[0]
            return json.loads(text)
        except json.JSONDecodeError:
            return {
                "score": 5,
                "suggestions": ["Unable to analyze"],
                "missing": [],
                "strengths": []
            }

    def suggest_improvements(self, readme_content: str) -> str:
        """Suggest improvements for existing README."""
        prompt = f"""Review this README and suggest specific improvements:

{readme_content[:3000]}

Provide 3-5 specific, actionable suggestions to improve this README.
Focus on clarity, completeness, and professionalism.
Keep suggestions brief and practical."""

        response = self.model.generate_content(prompt)
        return response.text
