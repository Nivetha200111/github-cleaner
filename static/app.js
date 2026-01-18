// State
let currentRepo = null;
let currentAnalysis = null;
let generatedReadme = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initMatrix();
    setupTabs();
    loadRepos();
});

// Matrix Rain Effect
function initMatrix() {
    const canvas = document.getElementById('matrix-canvas');
    const ctx = canvas.getContext('2d');

    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const chars = 'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ<>{}[]=/\\';
    const charArray = chars.split('');

    const fontSize = 14;
    const columns = canvas.width / fontSize;

    const drops = [];
    for (let i = 0; i < columns; i++) {
        drops[i] = Math.random() * -100;
    }

    function draw() {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        for (let i = 0; i < drops.length; i++) {
            const text = charArray[Math.floor(Math.random() * charArray.length)];

            // Vary the green intensity
            const intensity = 100 + Math.floor(Math.random() * 155);
            ctx.fillStyle = `rgba(0, ${intensity}, 0, ${0.6 + Math.random() * 0.4})`;
            ctx.font = fontSize + 'px monospace';
            ctx.fillText(text, i * fontSize, drops[i] * fontSize);

            if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
                drops[i] = 0;
            }
            drops[i]++;
        }
    }

    setInterval(draw, 45);

    window.addEventListener('resize', () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    });
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

// Toast Notifications
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 4000);
}

// Load Repositories
async function loadRepos() {
    showLoading('ACCESSING GITHUB SERVERS...');

    try {
        const response = await fetch('/api/repos');
        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        renderRepos(data.repos);
        showToast(`LOADED ${data.repos.length} REPOSITORIES`);
    } catch (error) {
        document.getElementById('repos-list').innerHTML =
            `<p class="loading" style="color: var(--danger);">CONNECTION FAILED: ${error.message}</p>`;
        showToast(error.message, 'error');
    } finally {
        hideLoading();
    }
}

function renderRepos(repos) {
    const container = document.getElementById('repos-list');

    if (!repos.length) {
        container.innerHTML = '<p class="loading">NO REPOSITORIES DETECTED</p>';
        return;
    }

    container.innerHTML = repos.map(repo => `
        <div class="repo-card" onclick="selectRepo('${repo.name}')" data-repo="${repo.name}">
            <h4>
                ${repo.name}
                ${repo.private ? '<span style="color: var(--warning); font-size: 10px;">[PRIVATE]</span>' : ''}
            </h4>
            <p>${repo.description || 'No description available'}</p>
            <div class="repo-meta">
                <span>${repo.language || 'Unknown'}</span>
                <span>★ ${repo.stars}</span>
                <span class="readme-status ${repo.has_readme ? 'has-readme' : 'no-readme'}">
                    ${repo.has_readme ? 'HAS README' : 'NO README'}
                </span>
            </div>
        </div>
    `).join('');
}

// Select Repository
async function selectRepo(repoName) {
    document.querySelectorAll('.repo-card').forEach(card => {
        card.classList.toggle('selected', card.dataset.repo === repoName);
    });

    currentRepo = repoName;
    document.getElementById('selected-repo').textContent = repoName;
    document.getElementById('analysis-section').style.display = 'block';

    // Reset tabs
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelector('[data-tab="overview"]').classList.add('active');
    document.getElementById('overview-tab').style.display = 'block';
    document.getElementById('readme-tab').style.display = 'none';
    document.getElementById('tools-tab').style.display = 'none';

    // Hide previous alerts
    document.getElementById('security-alert').style.display = 'none';

    showLoading('SCANNING REPOSITORY...');

    try {
        // Fetch analysis, Vercel URL, and health score in parallel
        const [analysisRes, vercelRes, healthRes] = await Promise.all([
            fetch(`/api/analyze/${repoName}`),
            fetch(`/api/vercel/${repoName}`),
            fetch(`/api/health-score/${repoName}`)
        ]);

        const analysisData = await analysisRes.json();
        const vercelData = await vercelRes.json();
        const healthData = await healthRes.json();

        if (analysisData.error) throw new Error(analysisData.error);

        currentAnalysis = analysisData.analysis;
        renderAnalysis(currentAnalysis, vercelData.url);
        renderHealthScore(healthData);

        // Check for security issues
        if (healthData.security && healthData.security.has_critical) {
            renderSecurityAlert(healthData.security);
        }

    } catch (error) {
        showToast('ANALYSIS FAILED: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

function renderHealthScore(health) {
    const banner = document.getElementById('health-banner');
    const circle = document.getElementById('score-circle');
    const value = document.getElementById('score-value');
    const grade = document.getElementById('score-grade');
    const checks = document.getElementById('health-checks');

    banner.style.display = 'flex';

    // Update score
    value.textContent = health.score;
    grade.textContent = `GRADE ${health.grade}`;

    // Update circle color based on grade
    circle.className = 'score-circle grade-' + health.grade.toLowerCase();

    // Render checks
    checks.innerHTML = health.checks.map(check => `
        <span class="health-check ${check.passed ? 'passed' : 'failed'}">
            ${check.passed ? '✓' : '✗'} ${check.name}
        </span>
    `).join('');
}

function renderSecurityAlert(security) {
    const alert = document.getElementById('security-alert');
    const content = document.getElementById('security-content');

    const allIssues = [...security.issues, ...security.warnings];

    if (allIssues.length === 0) {
        alert.style.display = 'none';
        return;
    }

    alert.style.display = 'block';

    content.innerHTML = allIssues.map(issue => `
        <div class="security-issue">
            <span class="issue-type ${issue.type.toLowerCase()}">${issue.type}</span>
            <div class="issue-details">
                <div class="issue-file">${issue.file}</div>
                <div class="issue-message">${issue.message}</div>
            </div>
        </div>
    `).join('');
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
        languagesEl.innerHTML = '<span class="dep-tag">UNKNOWN</span>';
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
        depsEl.innerHTML = '<span class="dep-tag">NO DEPS DETECTED</span>';
    }

    // Structure
    const structureEl = document.getElementById('structure-list');
    structureEl.innerHTML = `<div class="file-tree">${renderStructure(analysis.structure.slice(0, 12))}</div>`;

    // Vercel
    const vercelEl = document.getElementById('vercel-info');
    if (vercelUrl) {
        vercelEl.innerHTML = `<a href="${vercelUrl}" target="_blank" style="color: var(--accent); word-break: break-all;">${vercelUrl}</a>`;
    } else {
        vercelEl.innerHTML = '<span style="color: var(--text-dim);">NOT DEPLOYED ON VERCEL</span>';
    }
}

function renderStructure(items, indent = 0) {
    return items.map(item => {
        const prefix = '│ '.repeat(indent);
        const icon = item.type === 'dir' ? '📁' : '📄';
        let html = `<div>${prefix}${icon} <span class="${item.type === 'dir' ? 'dir' : ''}">${item.name}</span></div>`;
        if (item.children && item.children.length) {
            html += renderStructure(item.children.slice(0, 5), indent + 1);
        }
        return html;
    }).join('');
}

// Generate README
async function generateReadme() {
    if (!currentRepo) {
        showToast('SELECT A REPOSITORY FIRST', 'error');
        return;
    }

    showLoading('GENERATING README WITH AI...');

    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ repo_name: currentRepo })
        });

        const data = await response.json();

        if (data.error) throw new Error(data.error);

        generatedReadme = data.readme;

        // Switch to README tab
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelector('[data-tab="readme"]').classList.add('active');
        document.getElementById('overview-tab').style.display = 'none';
        document.getElementById('tools-tab').style.display = 'none';
        document.getElementById('readme-tab').style.display = 'block';

        const readmeEl = document.getElementById('readme-content');
        readmeEl.innerHTML = marked.parse(generatedReadme);
        hljs.highlightAll();

        showToast('README GENERATED SUCCESSFULLY');

    } catch (error) {
        showToast('GENERATION FAILED: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// Copy README
function copyReadme() {
    if (!generatedReadme) {
        showToast('NO README GENERATED', 'error');
        return;
    }

    navigator.clipboard.writeText(generatedReadme).then(() => {
        showToast('README COPIED TO CLIPBOARD');
    }).catch(err => {
        showToast('COPY FAILED', 'error');
    });
}

// Commit README
async function commitReadme() {
    if (!currentRepo || !generatedReadme) {
        showToast('NO README TO COMMIT', 'error');
        return;
    }

    if (!confirm(`COMMIT README TO ${currentRepo}?`)) {
        return;
    }

    showLoading('COMMITTING TO GITHUB...');

    try {
        const response = await fetch('/api/commit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                repo_name: currentRepo,
                readme: generatedReadme
            })
        });

        const data = await response.json();

        if (data.error) throw new Error(data.error);

        showToast('README COMMITTED SUCCESSFULLY');
        loadRepos();

    } catch (error) {
        showToast('COMMIT FAILED: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// Add .gitignore
async function addGitignore() {
    if (!currentRepo) {
        showToast('SELECT A REPOSITORY FIRST', 'error');
        return;
    }

    if (!confirm(`ADD .GITIGNORE TO ${currentRepo}?`)) {
        return;
    }

    showLoading('GENERATING .GITIGNORE...');

    try {
        const response = await fetch(`/api/gitignore/${currentRepo}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        if (data.error) throw new Error(data.error);

        showToast('.GITIGNORE ADDED SUCCESSFULLY');
        selectRepo(currentRepo); // Refresh analysis

    } catch (error) {
        showToast('FAILED: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// Add License
async function addLicense(type) {
    if (!currentRepo) {
        showToast('SELECT A REPOSITORY FIRST', 'error');
        return;
    }

    if (!confirm(`ADD ${type} LICENSE TO ${currentRepo}?`)) {
        return;
    }

    showLoading('ADDING LICENSE...');

    try {
        const response = await fetch(`/api/license/${currentRepo}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type })
        });

        const data = await response.json();

        if (data.error) throw new Error(data.error);

        showToast(`${type} LICENSE ADDED SUCCESSFULLY`);
        selectRepo(currentRepo); // Refresh analysis

    } catch (error) {
        showToast('FAILED: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// Security Scan
async function runSecurityScan() {
    if (!currentRepo) {
        showToast('SELECT A REPOSITORY FIRST', 'error');
        return;
    }

    showLoading('RUNNING SECURITY SCAN...');

    try {
        const response = await fetch(`/api/security/${currentRepo}`);
        const data = await response.json();

        if (data.error) throw new Error(data.error);

        renderSecurityAlert(data);

        if (data.has_critical) {
            showToast(`CRITICAL: ${data.issues.length} SECURITY ISSUES FOUND`, 'error');
        } else if (data.warnings.length > 0) {
            showToast(`${data.warnings.length} WARNINGS FOUND`, 'error');
        } else {
            showToast('NO SECURITY ISSUES DETECTED');
            document.getElementById('security-alert').style.display = 'none';
        }

        // Switch to overview to show alert
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelector('[data-tab="overview"]').classList.add('active');
        document.getElementById('overview-tab').style.display = 'block';
        document.getElementById('readme-tab').style.display = 'none';
        document.getElementById('tools-tab').style.display = 'none';

    } catch (error) {
        showToast('SCAN FAILED: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// Loading helpers
function showLoading(text = 'PROCESSING...') {
    document.getElementById('loading-text').textContent = text;
    document.getElementById('loading-overlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loading-overlay').style.display = 'none';
}
