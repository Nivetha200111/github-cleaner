#!/usr/bin/env python3
"""
GitHub Cleaner CLI - Analyze repos and generate READMEs from the command line.
"""

import argparse
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Add api directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.services.github_service import GitHubService
from api.services.ai_service import AIService
from api.services.vercel_service import VercelService


def get_services():
    """Initialize services with environment variables."""
    github_token = os.getenv('GITHUB_TOKEN')
    ai_key = os.getenv('GOOGLE_AI_API_KEY')
    vercel_token = os.getenv('VERCEL_TOKEN')

    if not github_token:
        print("Error: GITHUB_TOKEN not set in environment")
        sys.exit(1)
    if not ai_key:
        print("Error: GOOGLE_AI_API_KEY not set in environment")
        sys.exit(1)

    github = GitHubService(github_token)
    ai = AIService(ai_key)
    vercel = VercelService(vercel_token) if vercel_token else None

    return github, ai, vercel


def cmd_list(args):
    """List all repositories."""
    github, _, _ = get_services()
    repos = github.list_repos(include_forks=args.include_forks)

    print(f"\n{'Repository':<30} {'Language':<15} {'README':<10} {'Stars':<6}")
    print("-" * 65)

    for repo in repos:
        readme_status = "Yes" if repo['has_readme'] else "No"
        print(f"{repo['name']:<30} {repo['language'] or 'N/A':<15} {readme_status:<10} {repo['stars']:<6}")

    print(f"\nTotal: {len(repos)} repositories")


def cmd_analyze(args):
    """Analyze a repository."""
    github, _, vercel = get_services()

    print(f"\nAnalyzing {args.repo}...")
    analysis = github.analyze_repo(args.repo)

    print(f"\n{'='*50}")
    print(f"Repository: {analysis['name']}")
    print(f"Description: {analysis['description'] or 'None'}")
    print(f"Primary Language: {analysis['language'] or 'Unknown'}")
    print(f"{'='*50}")

    print("\nLanguages:")
    for lang, pct in analysis['languages'].items():
        print(f"  - {lang}: {pct}%")

    print("\nKey Files:")
    for f in analysis['key_files']:
        print(f"  - {f}")

    print("\nDependencies:")
    for file, deps in analysis['dependencies'].items():
        print(f"  {file}:")
        if isinstance(deps, list):
            for d in deps[:10]:
                print(f"    - {d}")
        elif isinstance(deps, dict):
            for key, items in deps.items():
                if isinstance(items, list) and items:
                    print(f"    {key}: {', '.join(items[:5])}")

    # Check Vercel
    if vercel:
        vercel_url = vercel.get_project_url(args.repo)
        if vercel_url:
            print(f"\nVercel URL: {vercel_url}")
        else:
            print("\nVercel: Not deployed")


def cmd_generate(args):
    """Generate README for a repository."""
    github, ai, vercel = get_services()

    print(f"\nAnalyzing {args.repo}...")
    analysis = github.analyze_repo(args.repo)

    # Get Vercel URL if available
    vercel_url = None
    if vercel:
        vercel_url = vercel.get_project_url(args.repo)
        if vercel_url:
            print(f"Found Vercel deployment: {vercel_url}")

    print("Generating README with AI...")
    readme = ai.generate_readme(analysis, vercel_url)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(readme)
        print(f"\nREADME saved to {args.output}")
    else:
        print("\n" + "="*50)
        print("GENERATED README:")
        print("="*50)
        print(readme)

    if args.commit:
        confirm = input("\nCommit this README to the repository? (y/n): ")
        if confirm.lower() == 'y':
            github.commit_readme(args.repo, readme)
            print("README committed successfully!")


def cmd_batch(args):
    """Process multiple repositories."""
    github, ai, vercel = get_services()

    repos = github.list_repos()

    # Filter repos without README if specified
    if args.missing_only:
        repos = [r for r in repos if not r['has_readme']]

    print(f"\nProcessing {len(repos)} repositories...")

    for i, repo in enumerate(repos, 1):
        print(f"\n[{i}/{len(repos)}] {repo['name']}")

        try:
            analysis = github.analyze_repo(repo['name'])

            vercel_url = None
            if vercel:
                vercel_url = vercel.get_project_url(repo['name'])

            readme = ai.generate_readme(analysis, vercel_url)

            if args.dry_run:
                print(f"  Would generate README ({len(readme)} chars)")
            else:
                github.commit_readme(repo['name'], readme)
                print(f"  README committed ({len(readme)} chars)")

        except Exception as e:
            print(f"  Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="GitHub Cleaner - Analyze repos and generate READMEs"
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # List command
    list_parser = subparsers.add_parser('list', help='List all repositories')
    list_parser.add_argument('--include-forks', action='store_true',
                            help='Include forked repositories')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze a repository')
    analyze_parser.add_argument('repo', help='Repository name')

    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate README for a repo')
    gen_parser.add_argument('repo', help='Repository name')
    gen_parser.add_argument('-o', '--output', help='Output file path')
    gen_parser.add_argument('--commit', action='store_true',
                           help='Commit the README to the repository')

    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Process multiple repositories')
    batch_parser.add_argument('--missing-only', action='store_true',
                             help='Only process repos without README')
    batch_parser.add_argument('--dry-run', action='store_true',
                             help='Show what would be done without committing')

    args = parser.parse_args()

    if args.command == 'list':
        cmd_list(args)
    elif args.command == 'analyze':
        cmd_analyze(args)
    elif args.command == 'generate':
        cmd_generate(args)
    elif args.command == 'batch':
        cmd_batch(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
