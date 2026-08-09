const API_URL = 'http://localhost:8000';

// DOM Elements
const statusIndicator = document.getElementById('status-indicator');
const statusMessage = document.getElementById('status-message');
const refreshBtn = document.getElementById('refresh-btn');

const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const uploadBtn = document.getElementById('upload-btn');
const uploadStatus = document.getElementById('upload-status');
const uploadProgress = document.getElementById('upload-progress');
const uploadError = document.getElementById('upload-error');
const uploadMessage = document.getElementById('upload-message');

const resultsSection = document.getElementById('results-section');
const resultSummary = document.getElementById('result-summary');
const resultSentiment = document.getElementById('result-sentiment');
const resultTopics = document.getElementById('result-topics');
const resultInsights = document.getElementById('result-insights');
const resultRecommendations = document.getElementById('result-recommendations');

// --- Helper: Connectivity Check ---
async function checkStatus() {
    statusMessage.textContent = 'Checking connectivity...';
    try {
        const response = await fetch(`${API_URL}/health`);
        if (response.ok) {
            const data = await response.json();
            statusMessage.textContent = `Backend is online (v${data.version})`;
            statusIndicator.className = 'indicator online';
        } else {
            throw new Error();
        }
    } catch (error) {
        statusMessage.textContent = 'Cannot reach backend. Make sure the server is running.';
        statusIndicator.className = 'indicator offline';
    }
}

// --- Interaction Logic ---

// Trigger file input
dropZone.addEventListener('click', () => fileInput.click());

// Handle drag events
['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    }, false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
    }, false);
});

dropZone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length) {
        fileInput.files = files;
        handleFileSelection();
    }
});

fileInput.addEventListener('change', handleFileSelection);

function handleFileSelection() {
    const file = fileInput.files[0];
    if (file) {
        uploadBtn.disabled = false;
        uploadError.style.display = 'none';
        
        // Show file feedback
        const dropZoneText = dropZone.querySelector('p');
        dropZoneText.innerHTML = `Selected: <strong>${file.name}</strong>`;
    }
}

uploadBtn.addEventListener('click', async () => {
    const file = fileInput.files[0];
    if (!file) return;

    // Reset UI
    uploadBtn.disabled = true;
    uploadStatus.classList.remove('hidden');
    uploadProgress.style.width = '0%';
    uploadError.style.display = 'none';
    resultsSection.classList.add('hidden');
    uploadMessage.textContent = 'Uploading and analyzing... This may take a moment.';

    const formData = new FormData();
    formData.append('file', file);

    try {
        // Fake progress for short uploads
        let progress = 0;
        const interval = setInterval(() => {
            progress += 5;
            if (progress <= 90) uploadProgress.style.width = `${progress}%`;
        }, 200);

        const response = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        clearInterval(interval);
        uploadProgress.style.width = '100%';

        if (!response.ok) {
            const errorBody = await response.json();
            throw new Error(errorBody.detail || 'Upload failed');
        }

        const result = await response.json();
        renderResults(result);
        
    } catch (error) {
        showError(error.message || 'A network error occurred. Please try again.');
    } finally {
        uploadBtn.disabled = false;
        setTimeout(() => {
            uploadStatus.classList.add('hidden');
        }, 1000);
    }
});

function showError(message) {
    uploadError.textContent = message;
    uploadError.style.display = 'block';
    uploadStatus.classList.add('hidden');
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// --- Render Dynamics ---

function renderResults(data) {
    resultsSection.classList.remove('hidden');
    
    // 1. Summary
    // We'll extract the Executive Summary from the markdown report
    const report = data.report_markdown;
    const summaryMatch = report.match(/\*\*Executive Summary\*\*:(.*?)(?=\n\d\.|\n\*\*|$)/s);
    resultSummary.textContent = summaryMatch ? summaryMatch[1].trim() : 'Data processed successfully with significant findings.';

    // 2. Sentiment (JSON Data)
    resultSentiment.innerHTML = '';
    const sentimentDist = data.analysis.sentiment_distribution;
    Object.entries(sentimentDist).forEach(([type, value]) => {
        const bar = document.createElement('div');
        bar.className = 'mb-4';
        const colorClass = type === 'positive' ? 'bg-success' : (type === 'negative' ? 'bg-error' : 'bg-secondary');
        bar.innerHTML = `
            <div class="flex justify-between text-sm mb-1">
                <span class="capitalize">${type}</span>
                <span>${value}%</span>
            </div>
            <div class="progress-container" style="margin: 0;">
                <div class="progress-bar ${colorClass}" style="width: ${value}%"></div>
            </div>
        `;
        resultSentiment.appendChild(bar);
    });

    // 3. Topics (JSON Data)
    resultTopics.innerHTML = '';
    const topics = data.analysis.common_topics;
    topics.forEach(t => {
        const tag = document.createElement('span');
        tag.className = 'result-tag tag-topic';
        tag.textContent = `${t.topic} (${t.count})`;
        resultTopics.appendChild(tag);
    });

    // 4. Insights & Recommendations (Markdown Parsing)
    // Extracting sections from markdown
    const risksMatch = report.match(/\*\*Key Risks\*\*:(.*?)(?=\n\d\.|\n\*\*|$)/s);
    const oppsMatch = report.match(/\*\*Opportunities\*\*:(.*?)(?=\n\d\.|\n\*\*|$)/s);
    const insightsMatch = report.match(/\*\*Actionable Insights\*\*:(.*?)(?=\n\d\.|\n\*\*|$)/s);

    resultInsights.innerHTML = `
        <div class="mb-4">
            <h4 class="text-sm font-bold text-error mb-1">Key Risks</h4>
            <p>${risksMatch ? formatMarkdownList(risksMatch[1]) : 'No critical risks identified.'}</p>
        </div>
        <div>
            <h4 class="text-sm font-bold text-success mb-1">Opportunities</h4>
            <p>${oppsMatch ? formatMarkdownList(oppsMatch[1]) : 'New market entries and growth potential.'}</p>
        </div>
    `;

    resultRecommendations.innerHTML = insightsMatch 
        ? formatMarkdownList(insightsMatch[1]) 
        : 'Optimize engagement timing and content strategy for better reach.';

    // Smooth scroll to results
    setTimeout(() => {
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }, 100);
}

function formatMarkdownList(text) {
    // Simple conversion of bullet points and bolding for native rendering
    return text.trim()
        .replace(/\n\s*-\s*/g, '<br>• ')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
}

// Initialize
checkStatus();
refreshBtn.addEventListener('click', checkStatus);
