// State
let currentRepo = null;
let currentAnalysis = null;
let generatedReadme = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadStoredSettings();
    setupTabs();
});

// Settings Management
function loadStoredSettings() {
    const githubToken = localStorage.getItem('github_token');
    const aiKey = localStorage.getItem('ai_key');
    const vercelToken = localStorage.getItem('vercel_token');

    if (githubToken) document.getElementById('github-token').value = githubToken;
    if (aiKey) document.getElementById('ai-key').value = aiKey;
    if (vercelToken) document.getElementById('vercel-token').value = vercelToken;

    if (githubToken && aiKey) {
        loadRepos();
    }
}

function saveSettings() {
    const githubToken = document.getElementById('github-token').value.trim();
    const aiKey = document.getElementById('ai-key').value.trim();
    const vercelToken = document.getElementById('vercel-token').value.trim();

    if (!githubToken || !aiKey) {
        alert('GitHub Token and AI API Key are required');
        return;
    }

    localStorage.setItem('github_token', githubToken);
    localStorage.setItem('ai_key', aiKey);
    if (vercelToken) localStorage.setItem('vercel_token', vercelToken);

    loadRepos();
}

function getHeaders() {
    return {
        'Content-Type': 'application/json',
        'X-GitHub-Token': localStorage.getItem('github_token') || '',
        'X-AI-Key': localStorage.getItem('ai_key') || '',
        'X-Vercel-Token': localStorage.getItem('vercel_token') || ''
    };
}

// Tabs
function setupTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            const tabName = tab.dataset.tab;
            document.querySelectorAll('.tab-content').forEach(content => {
                content.style.display = 'none';
            });
            document.getElementById(`${tabName}-tab`).style.display = 'block';
        });
    });
}

// Load Repositories
async function loadRepos() {
    showLoading('Loading repositories...');

    try {
        const response = await fetch('/api/repos', {
            headers: getHeaders()
        });
        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        renderRepos(data.repos);
        document.getElementById('main-content').style.display = 'grid';
    } catch (error) {
        alert('Error loading repos: ' + error.message);
    } finally {
        hideLoading();
    }
}

function renderRepos(repos) {
    const container = document.getElementById('repos-list');

    if (!repos.length) {
        container.innerHTML = '<p class="loading">No repositories found</p>';
        return;
    }

    container.innerHTML = repos.map(repo => `
        <div class="repo-card" onclick="selectRepo('${repo.name}')" data-repo="${repo.name}">
            <h4>
                <span class="language-dot lang-${(repo.language || 'default').toLowerCase()}"></span>
                ${repo.name}
                ${repo.private ? '🔒' : ''}
            </h4>
            <p>${repo.description || 'No description'}</p>
            <div class="repo-meta">
                <span>${repo.language || 'Unknown'}</span>
                <span>⭐ ${repo.stars}</span>
                <span class="readme-status ${repo.has_readme ? 'has-readme' : 'no-readme'}">
                    ${repo.has_readme ? 'Has README' : 'No README'}
                </span>
            </div>
        </div>
    `).join('');
}

// Select Repository
async function selectRepo(repoName) {
    // Update UI
    document.querySelectorAll('.repo-card').forEach(card => {
        card.classList.toggle('selected', card.dataset.repo === repoName);
    });

    currentRepo = repoName;
    document.getElementById('selected-repo').textContent = repoName;
    document.getElementById('analysis-section').style.display = 'block';

    // Switch to overview tab
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelector('[data-tab="overview"]').classList.add('active');
    document.getElementById('overview-tab').style.display = 'block';
    document.getElementById('readme-tab').style.display = 'none';

    showLoading('Analyzing repository...');

    try {
        // Fetch analysis and Vercel URL in parallel
        const [analysisRes, vercelRes] = await Promise.all([
            fetch(`/api/analyze/${repoName}`, { headers: getHeaders() }),
            fetch(`/api/vercel/${repoName}`, { headers: getHeaders() })
        ]);

        const analysisData = await analysisRes.json();
        const vercelData = await vercelRes.json();

        if (analysisData.error) throw new Error(analysisData.error);

        currentAnalysis = analysisData.analysis;
        renderAnalysis(currentAnalysis, vercelData.url);
    } catch (error) {
        alert('Error analyzing repo: ' + error.message);
    } finally {
        hideLoading();
    }
}

function renderAnalysis(analysis, vercelUrl) {
    // Languages
    const languagesEl = document.getElementById('languages-list');
    if (Object.keys(analysis.languages).length) {
        const langBar = Object.entries(analysis.languages)
            .map(([lang, pct]) => `<div class="lang-${lang.toLowerCase()}" style="width: ${pct}%" title="${lang}: ${pct}%"></div>`)
            .join('');

        const langList = Object.entries(analysis.languages)
            .map(([lang, pct]) => `<span class="dep-tag">${lang} ${pct}%</span>`)
            .join('');

        languagesEl.innerHTML = `<div class="language-bar">${langBar}</div>${langList}`;
    } else {
        languagesEl.innerHTML = '<span class="dep-tag">Unknown</span>';
    }

    // Dependencies
    const depsEl = document.getElementById('deps-list');
    const deps = [];
    Object.values(analysis.dependencies).forEach(pkgDeps => {
        if (Array.isArray(pkgDeps)) {
            deps.push(...pkgDeps.slice(0, 10));
        } else if (typeof pkgDeps === 'object') {
            Object.values(pkgDeps).forEach(d => {
                if (Array.isArray(d)) deps.push(...d.slice(0, 5));
            });
        }
    });

    if (deps.length) {
        depsEl.innerHTML = deps.slice(0, 15).map(d => `<span class="dep-tag">${d}</span>`).join('');
    } else {
        depsEl.innerHTML = '<span class="dep-tag">No dependencies found</span>';
    }

    // Structure
    const structureEl = document.getElementById('structure-list');
    structureEl.innerHTML = `<div class="file-tree">${renderStructure(analysis.structure.slice(0, 15))}</div>`;

    // Vercel
    const vercelEl = document.getElementById('vercel-info');
    if (vercelUrl) {
        vercelEl.innerHTML = `<a href="${vercelUrl}" target="_blank" style="color: var(--accent);">${vercelUrl}</a>`;
    } else {
        vercelEl.innerHTML = '<span style="color: var(--text-secondary);">Not deployed on Vercel</span>';
    }
}

function renderStructure(items, indent = 0) {
    return items.map(item => {
        const prefix = '  '.repeat(indent);
        const icon = item.type === 'dir' ? '📁' : '📄';
        let html = `<div>${prefix}${icon} <span class="${item.type === 'dir' ? 'dir' : ''}">${item.name}</span></div>`;
        if (item.children) {
            html += renderStructure(item.children, indent + 1);
        }
        return html;
    }).join('');
}

// Generate README
async function generateReadme() {
    if (!currentRepo) {
        alert('Please select a repository first');
        return;
    }

    showLoading('Generating README with AI...');

    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ repo_name: currentRepo })
        });

        const data = await response.json();

        if (data.error) throw new Error(data.error);

        generatedReadme = data.readme;

        // Switch to README tab
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelector('[data-tab="readme"]').classList.add('active');
        document.getElementById('overview-tab').style.display = 'none';
        document.getElementById('readme-tab').style.display = 'block';

        // Render markdown
        const readmeEl = document.getElementById('readme-content');
        readmeEl.innerHTML = marked.parse(generatedReadme);
        hljs.highlightAll();

    } catch (error) {
        alert('Error generating README: ' + error.message);
    } finally {
        hideLoading();
    }
}

// Copy README
function copyReadme() {
    if (!generatedReadme) {
        alert('No README generated yet');
        return;
    }

    navigator.clipboard.writeText(generatedReadme).then(() => {
        alert('README copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

// Commit README
async function commitReadme() {
    if (!currentRepo || !generatedReadme) {
        alert('No README to commit');
        return;
    }

    if (!confirm(`Commit this README to ${currentRepo}?`)) {
        return;
    }

    showLoading('Committing README...');

    try {
        const response = await fetch('/api/commit', {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({
                repo_name: currentRepo,
                readme: generatedReadme
            })
        });

        const data = await response.json();

        if (data.error) throw new Error(data.error);

        alert('README committed successfully!');

        // Refresh repo list to update README status
        loadRepos();

    } catch (error) {
        alert('Error committing README: ' + error.message);
    } finally {
        hideLoading();
    }
}

// Loading helpers
function showLoading(text = 'Processing...') {
    document.getElementById('loading-text').textContent = text;
    document.getElementById('loading-overlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loading-overlay').style.display = 'none';
}
