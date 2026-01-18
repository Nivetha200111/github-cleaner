```markdown
# github-cleaner

[![Python](https://img.shields.io/badge/python-3.7+-blue.svg?style=flat-square)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/github/actions/nivetha-projects/github-cleaner/main?style=flat-square)](https://github.com/nivetha-projects/github-cleaner/actions/workflows/main.yml)

Analyze your GitHub repositories and generate professional READMEs using AI. Automatically finds Vercel deployment URLs and adds them to your READMEs.

## ✨ Key Features

*   **AI-Powered README Generation**:  Automatically generate comprehensive and informative README files using Google Gemini AI.
*   **Repository Analysis**:  Scans your repositories to identify languages, dependencies, and project structure to understand your codebase.
*   **Vercel Integration**: Detects Vercel deployment URLs and seamlessly integrates them into the generated READMEs.
*   **Web Interface**:  Provides a user-friendly web interface for easy management and configuration.
*   **Command-Line Interface (CLI)**:  Offers a powerful command-line tool for automation and scripting tasks.
*   **Customizable Templates**: Tailor the generated READMEs to fit your specific project needs and branding.
*   **Batch Processing**: Update multiple repositories simultaneously for increased efficiency.

## 🛠️ Tech Stack

*   **Python**: Core programming language for backend logic and scripting.  [![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=yellow)](https://www.python.org/)
*   **Flask**: Micro web framework for building the API and web dashboard.  [![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
*   **Google Gemini AI**: Powers the README generation with its natural language processing capabilities.
*   **PyGithub**: Python library for interacting with the GitHub API.
*   **HTML/CSS/JavaScript**: Used for the web interface.  [![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/HTML)  [![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/CSS)  [![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)

## ⚙️ Prerequisites

Before you begin, ensure you have the following installed:

*   **Python 3.7+**:  Download from [python.org](https://www.python.org/downloads/)
*   **pip**: Python package installer (usually included with Python)
*   **GitHub Account**: A GitHub account is required to interact with your repositories.
*   **Google Gemini API Key**: Obtain an API Key from [Google AI Studio](https://makersuite.google.com/)

## 🚀 Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/nivetha-projects/github-cleaner.git
    cd github-cleaner
    ```

2.  **Create a virtual environment (recommended):**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Linux/macOS
    venv\Scripts\activate  # On Windows
    ```

3.  **Install the dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**

    Create a `.env` file in the root directory and add your GitHub token and Google Gemini API key:

    ```
    GITHUB_TOKEN=your_github_token
    GOOGLE_API_KEY=your_google_gemini_api_key
    ```

## 💻 Usage

### Running the CLI

```bash
python cli.py --help
```

This will display the available command-line options.  For example, to generate a README for a specific repository:

```bash
python cli.py --repo your_username/your_repository
```

### Running the Web Application

1.  Navigate to the `api` directory

    ```bash
    cd api
    ```

2. Run `index.py`

    ```bash
    python index.py
    ```

3.  Open your web browser and navigate to the address displayed in the console (usually `http://127.0.0.1:5000/`).

## 🌐 Live Demo

Check out the live demo here: [https://github-cleaner-g0avpp9rf-nivethas-projects-f7c0732d.vercel.app](https://github-cleaner-g0avpp9rf-nivethas-projects-f7c0732d.vercel.app)

## 🤝 Contributing

Contributions are welcome!  Please follow these guidelines:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes and commit them with clear, descriptive messages.
4.  Submit a pull request.

## 📜 License

This project is licensed under the MIT License. See the `LICENSE` file for details (Not Included).  It's highly recommended you add a LICENSE file to your repository and update this section accordingly.
```