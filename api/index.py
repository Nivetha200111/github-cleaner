import os
import sys
from flask import Flask, request, jsonify, render_template, send_from_directory
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

app = Flask(__name__,
            template_folder='../templates',
            static_folder='../static')


def get_github_service(token=None):
    from api.services.github_service import GitHubService
    return GitHubService(token)


def get_ai_service(api_key=None):
    from api.services.ai_service import AIService
    return AIService(api_key)


def get_vercel_service(token=None):
    from api.services.vercel_service import VercelService
    return VercelService(token)


# --- Web Interface ---

@app.route('/')
def index():
    """Serve the main dashboard."""
    return render_template('index.html')


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    return send_from_directory(app.static_folder, filename)


# --- API Endpoints ---

@app.route('/api/repos', methods=['GET'])
def list_repos():
    """List all GitHub repositories."""
    try:
        github_token = request.headers.get('X-GitHub-Token') or os.getenv('GITHUB_TOKEN')
        if not github_token:
            return jsonify({'error': 'GitHub token required'}), 401

        github = get_github_service(github_token)
        repos = github.list_repos(include_forks=request.args.get('include_forks', 'false') == 'true')
        return jsonify({'repos': repos})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze/<repo_name>', methods=['GET'])
def analyze_repo(repo_name):
    """Analyze a specific repository."""
    try:
        github_token = request.headers.get('X-GitHub-Token') or os.getenv('GITHUB_TOKEN')
        if not github_token:
            return jsonify({'error': 'GitHub token required'}), 401

        github = get_github_service(github_token)
        analysis = github.analyze_repo(repo_name)
        return jsonify({'analysis': analysis})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/vercel/<repo_name>', methods=['GET'])
def get_vercel_url(repo_name):
    """Get Vercel deployment URL for a repository."""
    try:
        vercel_token = request.headers.get('X-Vercel-Token') or os.getenv('VERCEL_TOKEN')
        if not vercel_token:
            return jsonify({'url': None, 'message': 'Vercel token not provided'})

        vercel = get_vercel_service(vercel_token)
        url = vercel.get_project_url(repo_name)
        return jsonify({'url': url, 'repo': repo_name})
    except Exception as e:
        return jsonify({'url': None, 'error': str(e)})


@app.route('/api/vercel/all', methods=['GET'])
def get_all_vercel_urls():
    """Get all Vercel project URLs."""
    try:
        vercel_token = request.headers.get('X-Vercel-Token') or os.getenv('VERCEL_TOKEN')
        if not vercel_token:
            return jsonify({'urls': {}, 'message': 'Vercel token not provided'})

        vercel = get_vercel_service(vercel_token)
        urls = vercel.get_all_project_urls()
        return jsonify({'urls': urls})
    except Exception as e:
        return jsonify({'urls': {}, 'error': str(e)})


@app.route('/api/generate', methods=['POST'])
def generate_readme():
    """Generate README for a repository using AI."""
    try:
        data = request.get_json()
        repo_name = data.get('repo_name')

        if not repo_name:
            return jsonify({'error': 'repo_name is required'}), 400

        github_token = request.headers.get('X-GitHub-Token') or os.getenv('GITHUB_TOKEN')
        ai_key = request.headers.get('X-AI-Key') or os.getenv('GOOGLE_AI_API_KEY')
        vercel_token = request.headers.get('X-Vercel-Token') or os.getenv('VERCEL_TOKEN')

        if not github_token:
            return jsonify({'error': 'GitHub token required'}), 401
        if not ai_key:
            return jsonify({'error': 'AI API key required'}), 401

        # Analyze repository
        github = get_github_service(github_token)
        analysis = github.analyze_repo(repo_name)

        # Get Vercel URL if token provided
        vercel_url = None
        if vercel_token:
            try:
                vercel = get_vercel_service(vercel_token)
                vercel_url = vercel.get_project_url(repo_name)
            except Exception:
                pass

        # Generate README
        ai = get_ai_service(ai_key)
        readme = ai.generate_readme(analysis, vercel_url)

        return jsonify({
            'readme': readme,
            'analysis': analysis,
            'vercel_url': vercel_url
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/commit', methods=['POST'])
def commit_readme():
    """Commit generated README to repository."""
    try:
        data = request.get_json()
        repo_name = data.get('repo_name')
        readme_content = data.get('readme')
        commit_message = data.get('message', 'Update README.md via GitHub Cleaner')

        if not repo_name or not readme_content:
            return jsonify({'error': 'repo_name and readme are required'}), 400

        github_token = request.headers.get('X-GitHub-Token') or os.getenv('GITHUB_TOKEN')
        if not github_token:
            return jsonify({'error': 'GitHub token required'}), 401

        github = get_github_service(github_token)
        success = github.commit_readme(repo_name, readme_content, commit_message)

        return jsonify({'success': success, 'repo': repo_name})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/quality/<repo_name>', methods=['GET'])
def analyze_quality(repo_name):
    """Analyze repository quality and get suggestions."""
    try:
        github_token = request.headers.get('X-GitHub-Token') or os.getenv('GITHUB_TOKEN')
        ai_key = request.headers.get('X-AI-Key') or os.getenv('GOOGLE_AI_API_KEY')

        if not github_token or not ai_key:
            return jsonify({'error': 'GitHub and AI tokens required'}), 401

        github = get_github_service(github_token)
        analysis = github.analyze_repo(repo_name)

        ai = get_ai_service(ai_key)
        quality = ai.analyze_code_quality(analysis)

        return jsonify({'quality': quality, 'repo': repo_name})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'service': 'github-cleaner'})


# Run locally
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
