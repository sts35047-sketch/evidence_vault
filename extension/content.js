// EvidenceVault Content Script - Real-time Toxic Content Detection

const API_URL = "http://localhost:5000/api/v1";
let monitoringActive = false;
let sessionId = null;

// Initialize monitoring
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "toggleMonitoring") {
    monitoringActive = request.enabled;
    sessionId = request.sessionId;
    
    if (monitoringActive) {
      startMonitoring();
    } else {
      stopMonitoring();
    }
  }
});

function startMonitoring() {
  console.log("🔴 EvidenceVault real-time monitoring started");
  
  // Monitor all text nodes on the page
  monitorPageContent();
  
  // Watch for new content (dynamic loading)
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.addedNodes.length) {
        monitorPageContent();
      }
    });
  });
  
  observer.observe(document.body, {
    childList: true,
    subtree: true,
    characterData: true
  });
  
  // Set up keyboard listener for quick capture
  document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.shiftKey && e.key === 'E') {
      capturePageContent();
    }
  });
}

function stopMonitoring() {
  console.log("⏹ EvidenceVault monitoring stopped");
  removeHighlights();
}

function monitorPageContent() {
  const textNodes = getAllTextNodes(document.body);
  
  textNodes.forEach((node) => {
    const text = node.textContent.trim();
    
    // Analyze text for toxicity
    if (text.length > 20) {
      chrome.runtime.sendMessage({
        action: 'analyzeToxicity',
        content: text
      }, (response) => {
        if (response && response.is_toxic) {
          highlightToxicContent(node, response.max_toxicity);
        }
      });
    }
  });
}

function getAllTextNodes(element) {
  const textNodes = [];
  const walker = document.createTreeWalker(
    element,
    NodeFilter.SHOW_TEXT,
    null,
    false
  );
  
  let node;
  while (node = walker.nextNode()) {
    if (node.textContent.trim().length > 0) {
      textNodes.push(node);
    }
  }
  
  return textNodes;
}

function highlightToxicContent(node, toxicityScore) {
  // Create span with highlight class
  const span = document.createElement('span');
  span.className = 'evault-toxic-highlight';
  span.setAttribute('data-toxicity', toxicityScore.toFixed(2));
  span.setAttribute('title', `Toxic Content Detected\nToxicity: ${(toxicityScore * 100).toFixed(1)}%`);
  
  // Set color intensity based on score
  if (toxicityScore > 0.8) {
    span.classList.add('toxicity-critical');
  } else if (toxicityScore > 0.6) {
    span.classList.add('toxicity-high');
  } else if (toxicityScore > 0.4) {
    span.classList.add('toxicity-medium');
  } else {
    span.classList.add('toxicity-low');
  }
  
  span.appendChild(node.cloneNode(true));
  node.parentNode.replaceChild(span, node);
}

function removeHighlights() {
  document.querySelectorAll('.evault-toxic-highlight').forEach((el) => {
    while (el.firstChild) {
      el.parentNode.insertBefore(el.firstChild, el);
    }
    el.parentNode.removeChild(el);
  });
}

function capturePageContent() {
  const pageContent = document.body.innerText;
  
  fetch(`${API_URL}/realtime/highlight-toxic`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      page_content: pageContent,
      session_id: sessionId
    })
  })
  .then(response => response.json())
  .then(data => {
    console.log(`Found ${data.toxic_count} toxic items out of ${data.total_sentences} sentences`);
  });
}

// Auto-start if page is already loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    // Check if monitoring should be enabled
    chrome.storage.local.get(['monitoringEnabled'], (result) => {
      if (result.monitoringEnabled) {
        monitoringActive = true;
        startMonitoring();
      }
    });
  });
} else {
  chrome.storage.local.get(['monitoringEnabled'], (result) => {
    if (result.monitoringEnabled) {
      monitoringActive = true;
      startMonitoring();
    }
  });
}
