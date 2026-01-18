# GitHub Cleaner

Analyze your GitHub repositories and generate professional READMEs using AI. Automatically finds Vercel deployment URLs and adds them to your READMEs.

## Features

- **Repository Analysis** - Scans your repos for languages, dependencies, and project structure
- **AI-Powered README Generation** - Uses Google Gemini to create comprehensive READMEs
- **Vercel Integration** - Automatically finds and includes live deployment URLs
- **Web Dashboard** - Browser-based interface for easy management
- **CLI Tool** - Command-line interface for automation and scripting
- **Batch Processing** - Update multiple repositories at once

## Tech Stack

- Python / Flask
- Google Gemini AI (free tier)
- GitHub API (PyGithub)
- Vercel API

## Setup

### 1. Clone and Install

```bash
git clone https://github.com/yourusername/github-cleaner.git
cd github-cleaner
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and add your API keys:

```bash
cp .env.example .env
```

Required keys:
- **GITHUB_TOKEN** - [Create here](https://github.com/settings/tokens) (needs `repo` scope)
- **GOOGLE_AI_API_KEY** - [Get here](https://makersuite.google.com/app/apikey)
- **VERCEL_TOKEN** (optional) - [Create here](https://vercel.com/account/tokens)

### 3. Run Locally

```bash
python api/index.py
```

Open http://localhost:5000 in your browser.

## CLI Usage

```bash
# List all repositories
python cli.py list

# Analyze a specific repo
python cli.py analyze my-repo

# Generate README for a repo
python cli.py generate my-repo

# Generate and save to file
python cli.py generate my-repo -o README.md

# Generate and commit directly
python cli.py generate my-repo --commit

# Process all repos missing READMEs
python cli.py batch --missing-only

# Dry run (see what would happen)
python cli.py batch --dry-run
```

## Deploy to Vercel

```bash
npm i -g vercel
vercel
```

Set environment variables in Vercel dashboard:
- `GITHUB_TOKEN`
- `GOOGLE_AI_API_KEY`
- `VERCEL_TOKEN`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/repos` | GET | List all repositories |
| `/api/analyze/<repo>` | GET | Analyze repository structure |
| `/api/vercel/<repo>` | GET | Get Vercel deployment URL |
| `/api/generate` | POST | Generate README with AI |
| `/api/commit` | POST | Commit README to repository |

## License

MIT
