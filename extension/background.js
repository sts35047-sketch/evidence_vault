// EvidenceVault Chrome Extension Background Service Worker
const API_URL = "http://localhost:5000/api/v1";
const API_KEY = "evault-demo-key-2026";
const SESSION_ID = generateSessionId();

function generateSessionId() {
  return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// ── Real-time Monitoring ──────────────────────────────────────────────────────
let realtimeSession = null;
let monitoringActive = false;

// Create context menu items
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "secure-evidence",
    title: "📸 Secure in EvidenceVault",
    contexts: ["selection"]
  });
  
  chrome.contextMenus.create({
    id: "screenshot-evidence",
    title: "📷 Screenshot as Evidence",
    contexts: ["page"]
  });
  
  chrome.contextMenus.create({
    id: "enable-realtime",
    title: "🔴 Start Real-time Monitoring",
    contexts: ["page"]
  });
});

// ── Context Menu Handlers ──────────────────────────────────────────────────────

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "secure-evidence") {
    captureSelectedText(info.selectionText, tab);
  } else if (info.menuItemId === "screenshot-evidence") {
    captureScreenshot(tab);
  } else if (info.menuItemId === "enable-realtime") {
    toggleRealtimeMonitoring(tab);
  }
});

function captureSelectedText(selectedText, tab) {
  const contextualText = `[Captured from: ${tab.url}]\n\n${selectedText}`;

  fetch(`${API_URL}/realtime/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      api_key: API_KEY,
      content: contextualText,
      session_id: SESSION_ID,
      source_url: tab.url
    })
  })
  .then(response => response.json())
  .then(data => {
    const toxicityScore = Math.max(...Object.values(data.scores || {})) || 0;
    const riskLevel = getRiskLevel(toxicityScore);
    
    chrome.notifications.create({
      type: "basic",
      iconUrl: "images/icon48.png",
      title: `Evidence Secured - Risk: ${riskLevel}`,
      message: `Toxicity: ${(toxicityScore * 100).toFixed(1)}%`
    });
  })
  .catch(error => {
    chrome.notifications.create({
      type: "basic",
      iconUrl: "images/icon48.png",
      title: "Connection Error",
      message: "Could not connect to EvidenceVault"
    });
  });
}

function captureScreenshot(tab) {
  chrome.tabs.captureVisibleTab(tab.windowId, { format: "png" }, (screenshotUrl) => {
    if (!screenshotUrl) return;
    
    // Convert data URL to blob
    fetch(screenshotUrl)
      .then(res => res.blob())
      .then(blob => {
        const formData = new FormData();
        formData.append('screenshot', blob);
        formData.append('session_id', SESSION_ID);
        formData.append('platform', getPagePlatform(tab.url));
        formData.append('url', tab.url);
        
        return fetch(`${API_URL}/realtime/screenshot-monitor`, {
          method: "POST",
          body: formData
        });
      })
      .then(response => response.json())
      .then(data => {
        chrome.notifications.create({
          type: "basic",
          iconUrl: "images/icon48.png",
          title: "Screenshot Captured",
          message: `Saved as: ${data.filename}`
        });
      })
      .catch(error => {
        console.error('Screenshot error:', error);
      });
  });
}

function toggleRealtimeMonitoring(tab) {
  monitoringActive = !monitoringActive;
  const status = monitoringActive ? "Active" : "Stopped";
  
  chrome.tabs.sendMessage(tab.id, {
    action: "toggleMonitoring",
    enabled: monitoringActive,
    sessionId: SESSION_ID
  }).catch(err => console.log('Content script not ready'));
  
  chrome.notifications.create({
    type: "basic",
    iconUrl: "images/icon48.png",
    title: `Real-time Monitoring ${status}`,
    message: `Now ${monitoringActive ? 'detecting toxic content live' : 'idle'}`
  });
}

// ── Helper Functions ──────────────────────────────────────────────────────────

function getRiskLevel(score) {
  if (score < 0.3) return 'LOW';
  if (score < 0.6) return 'MEDIUM';
  if (score < 0.8) return 'HIGH';
  return 'CRITICAL';
}

function getPagePlatform(url) {
  if (url.includes('twitter.com') || url.includes('x.com')) return 'twitter';
  if (url.includes('facebook.com')) return 'facebook';
  if (url.includes('instagram.com')) return 'instagram';
  if (url.includes('tiktok.com')) return 'tiktok';
  if (url.includes('reddit.com')) return 'reddit';
  if (url.includes('youtube.com')) return 'youtube';
  if (url.includes('discord.com')) return 'discord';
  return 'unknown';
}

// ── Listen for messages from content scripts ──────────────────────────────────

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'analyzeToxicity') {
    fetch(`${API_URL}/realtime/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        api_key: API_KEY,
        content: request.content,
        session_id: SESSION_ID,
        source_url: sender.url
      })
    })
    .then(response => response.json())
    .then(data => sendResponse(data))
    .catch(error => sendResponse({ error: error.message }));
    
    return true; // Keep the message channel open
  }
});