```markdown
# github-cleaner

[![Python](https://img.shields.io/badge/python-3.7+-blue.svg?style=flat-square)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) <!-- Replace with actual license badge if applicable -->
<!-- Add build status badge here - e.g., [![Build Status](https://travis-ci.org/yourusername/github-cleaner.svg?branch=main)](https://travis-ci.org/yourusername/github-cleaner) -->

Analyze your GitHub repositories and generate professional READMEs using AI. Automatically finds Vercel deployment URLs and adds them to your READMEs.

## ✨ Key Features

*   **Repository Analysis**: Scans your repositories for languages, dependencies, and project structure to understand your codebase.
*   **AI-Powered README Generation**: Leverages Google Gemini to automatically generate comprehensive and informative README files.
*   **Vercel Integration**: Detects Vercel deployment URLs and seamlessly integrates them into the generated READMEs.
*   **Web Dashboard**: Provides a browser-based interface for easy management and control.
*   **Command-Line Interface (CLI)**: Offers a powerful command-line tool for automation and scripting tasks.
*   **Batch Processing**: Enables updating multiple repositories simultaneously for increased efficiency.

## 🛠️ Tech Stack

*   **Python**: Core programming language for backend logic and scripting. [![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=yellow)](https://www.python.org/)
*   **Flask**: Micro web framework for building the API and web dashboard.  [![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
*   **Google Gemini AI**: Powers the README generation process with its natural language processing capabilities.
*   **PyGithub**: Python library for interacting with the GitHub API.
*   **JavaScript**: Used for front-end interactivity in the web dashboard. [![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://www.javascript.com/)
*   **CSS**: Stylesheet language for web dashboard. [![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)](https://www.w3schools.com/css/)
*   **HTML**: Markup language for web dashboard.  [![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)](https://www.w3schools.com/html/)
*   **Vercel**:  Platform for deployment and hosting, with automatic URL detection.  [![Vercel](https://img.shields.io/badge/vercel-%23000000.svg?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com/)

## ⚙️ Prerequisites

Before you begin, ensure you have met the following requirements:

*   Python 3.7+
*   `pip` package installer
*   A GitHub account
*   A Google AI Studio account

## 📦 Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/yourusername/github-cleaner.git
    cd github-cleaner
    ```

2.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure environment variables:**

    Copy the `.env.example` file to `.env` and populate the required API keys:

    ```bash
    cp .env.example .env
    ```

    Edit the `.env` file and add the following:

    *   `GITHUB_TOKEN`:  Your GitHub personal access token with `repo` scope.  [Create here](https://github.com/settings/tokens)
    *   `GOOGLE_AI_API_KEY`: Your Google AI API key. [Get here](https://makersuite.google.com/app/apikey)
    *   `VERCEL_TOKEN` (optional): Your Vercel API token. [Create here](https://vercel.com/account/tokens)

## 🚀 Usage

### Running the API and Web Dashboard Locally

```bash
python api/index.py
```

Then, open your browser and navigate to `http://localhost:5000` to access the web dashboard.

### CLI Usage

The `cli.py` provides several commands for interacting with your repositories:

*   **List repositories:**

    ```bash
    python cli.py list
    ```

*   **Analyze a specific repository:**

    ```bash
    python cli.py analyze my-repo
    ```

*   **Generate README for a repository:**

    ```bash
    python cli.py generate my-repo
    ```

*   **Generate and save to a file:**

    ```bash
    python cli.py generate my-repo -o README.md
    ```

*   **Generate and commit directly (requires proper git configuration):**

    ```bash
    python cli.py generate my-repo --commit
    ```

*   **Batch process repositories missing READMEs:**

    ```bash
    python cli.py batch --missing-only
    ```

*   **Dry run (preview changes without executing):**

    ```bash
    python cli.py batch --dry-run
    ```

### Deploying to Vercel

1.  Install the Vercel CLI:

    ```bash
    npm i -g vercel
    ```

2.  Deploy your project:

    ```bash
    vercel
    ```

3.  Set the environment variables in the Vercel dashboard:

    *   `GITHUB_TOKEN`
    *   `GOOGLE_AI_API_KEY`
    *   `VERCEL_TOKEN` (optional)

## 🌐 Live Demo

Check out the live demo: [https://github-cleaner-jxvkhmy1o-nivethas-projects-f7c0732d.vercel.app](https://github-cleaner-jxvkhmy1o-nivethas-projects-f7c0732d.vercel.app)

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes and commit them with clear and concise messages.
4.  Push your changes to your fork.
5.  Submit a pull request.

## 📜 License

This project is licensed under the MIT License.  See the `LICENSE` file for details.  (Add this file to the repository root).
```