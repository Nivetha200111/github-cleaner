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

    const chars = 'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ';
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

        ctx.fillStyle = '#0f0';
        ctx.font = fontSize + 'px monospace';

        for (let i = 0; i < drops.length; i++) {
            const text = charArray[Math.floor(Math.random() * charArray.length)];
            ctx.fillStyle = `rgba(0, ${150 + Math.random() * 105}, 0, ${0.5 + Math.random() * 0.5})`;
            ctx.fillText(text, i * fontSize, drops[i] * fontSize);

            if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
                drops[i] = 0;
            }
            drops[i]++;
        }
    }

    setInterval(draw, 50);

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

// Load Repositories
async function loadRepos() {
    showLoading('ACCESSING GITHUB...');

    try {
        const response = await fetch('/api/repos');
        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        renderRepos(data.repos);
    } catch (error) {
        document.getElementById('repos-list').innerHTML =
            `<p class="loading" style="color: #ff0000;">ERROR: ${error.message}</p>`;
    } finally {
        hideLoading();
    }
}

function renderRepos(repos) {
    const container = document.getElementById('repos-list');

    if (!repos.length) {
        container.innerHTML = '<p class="loading">NO REPOSITORIES FOUND</p>';
        return;
    }

    container.innerHTML = repos.map(repo => `
        <div class="repo-card" onclick="selectRepo('${repo.name}')" data-repo="${repo.name}">
            <h4>
                <span class="language-dot lang-${(repo.language || 'default').toLowerCase()}"></span>
                ${repo.name}
                ${repo.private ? '[PRIVATE]' : ''}
            </h4>
            <p>${repo.description || 'No description available'}</p>
            <div class="repo-meta">
                <span>${repo.language || 'Unknown'}</span>
                <span>* ${repo.stars}</span>
                <span class="readme-status ${repo.has_readme ? 'has-readme' : 'no-readme'}">
                    ${repo.has_readme ? 'README' : 'NO README'}
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

    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelector('[data-tab="overview"]').classList.add('active');
    document.getElementById('overview-tab').style.display = 'block';
    document.getElementById('readme-tab').style.display = 'none';

    showLoading('SCANNING REPOSITORY...');

    try {
        const [analysisRes, vercelRes] = await Promise.all([
            fetch(`/api/analyze/${repoName}`),
            fetch(`/api/vercel/${repoName}`)
        ]);

        const analysisData = await analysisRes.json();
        const vercelData = await vercelRes.json();

        if (analysisData.error) throw new Error(analysisData.error);

        currentAnalysis = analysisData.analysis;
        renderAnalysis(currentAnalysis, vercelData.url);
    } catch (error) {
        alert('ERROR: ' + error.message);
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
        depsEl.innerHTML = '<span class="dep-tag">NO DEPS FOUND</span>';
    }

    // Structure
    const structureEl = document.getElementById('structure-list');
    structureEl.innerHTML = `<div class="file-tree">${renderStructure(analysis.structure.slice(0, 15))}</div>`;

    // Vercel
    const vercelEl = document.getElementById('vercel-info');
    if (vercelUrl) {
        vercelEl.innerHTML = `<a href="${vercelUrl}" target="_blank" style="color: var(--accent);">${vercelUrl}</a>`;
    } else {
        vercelEl.innerHTML = '<span style="color: var(--text-dim);">NOT DEPLOYED</span>';
    }
}

function renderStructure(items, indent = 0) {
    return items.map(item => {
        const prefix = '  '.repeat(indent);
        const icon = item.type === 'dir' ? '[D]' : '[F]';
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
        alert('SELECT A REPOSITORY FIRST');
        return;
    }

    showLoading('GENERATING README...');

    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ repo_name: currentRepo })
        });

        const data = await response.json();

        if (data.error) throw new Error(data.error);

        generatedReadme = data.readme;

        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelector('[data-tab="readme"]').classList.add('active');
        document.getElementById('overview-tab').style.display = 'none';
        document.getElementById('readme-tab').style.display = 'block';

        const readmeEl = document.getElementById('readme-content');
        readmeEl.innerHTML = marked.parse(generatedReadme);
        hljs.highlightAll();

    } catch (error) {
        alert('ERROR: ' + error.message);
    } finally {
        hideLoading();
    }
}

// Copy README
function copyReadme() {
    if (!generatedReadme) {
        alert('NO README GENERATED');
        return;
    }

    navigator.clipboard.writeText(generatedReadme).then(() => {
        alert('README COPIED TO CLIPBOARD');
    }).catch(err => {
        console.error('Copy failed:', err);
    });
}

// Commit README
async function commitReadme() {
    if (!currentRepo || !generatedReadme) {
        alert('NO README TO COMMIT');
        return;
    }

    if (!confirm(`COMMIT README TO ${currentRepo}?`)) {
        return;
    }

    showLoading('COMMITTING...');

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

        alert('README COMMITTED SUCCESSFULLY');
        loadRepos();

    } catch (error) {
        alert('ERROR: ' + error.message);
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
