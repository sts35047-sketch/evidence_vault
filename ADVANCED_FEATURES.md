# EvidenceVault - Advanced Features Documentation

## Table of Contents
1. [Real-time Monitoring](#real-time-monitoring)
2. [Browser Extension](#browser-extension)
3. [Bot Integration](#bot-integration)
4. [Webhook System](#webhook-system)
5. [Advanced Analytics](#advanced-analytics)
6. [Mobile App](#mobile-app)

---

## Real-time Monitoring

### Overview
Real-time toxicity detection and content analysis as users browse social media platforms.

### API Endpoints

#### Analyze Content Real-time
```http
POST /api/v1/realtime/analyze

{
  "content": "toxic message here",
  "session_id": "session_123456",
  "source_url": "https://twitter.com/user/status/123"
}

Response:
{
  "text": "toxic message here",
  "timestamp": "2024-04-26T10:30:00Z",
  "scores": {
    "toxic": 0.92,
    "severe_toxic": 0.45,
    "obscene": 0.23,
    "threat": 0.12,
    "insult": 0.88,
    "identity_hate": 0.34
  },
  "is_toxic": true,
  "max_toxicity": 0.92
}
```

#### Server-Sent Events Stream
```http
GET /api/v1/realtime/stream/{session_id}

Continuously receives alerts:
data: {"type": "toxicity_detected", "score": 0.92, ...}
data: {"type": "screenshot_captured", ...}
data: {"type": "heartbeat", "timestamp": "..."}
```

#### Screenshot Processing
```http
POST /api/v1/realtime/screenshot-monitor

FormData:
- screenshot: [image file]
- session_id: "session_123456"
- platform: "twitter"
- url: "https://twitter.com/..."

Response:
{
  "message": "Screenshot processed",
  "filename": "screenshot_1714121400.png",
  "alert": {...}
}
```

#### Get Session Status
```http
GET /api/v1/realtime/status/{session_id}

Response:
{
  "session_id": "session_123456",
  "created_at": "2024-04-26T10:00:00Z",
  "message_count": 45,
  "recent_alerts": [...],
  "is_active": true
}
```

### Usage Example

```python
import requests
import sseclient

# Start real-time monitoring session
session_id = "session_" + str(int(time.time()))

# Stream events
response = requests.get(
    "http://localhost:8000/api/v1/realtime/stream/" + session_id,
    stream=True
)

client = sseclient.SSEClient(response)
for event in client:
    print(event.data)
    # React to toxic content detected
```

---

## Browser Extension

### Installation

1. **Chrome/Firefox**
   - Navigate to `chrome://extensions` or `about:addons`
   - Enable Developer Mode
   - Click "Load unpacked" and select the `extension/` folder

2. **Configuration**
   - Set API endpoint in options page
   - Configure monitoring preferences

### Features

#### 1. Context Menu Integration
- Right-click on text → "Secure in EvidenceVault"
- Auto-submits selected text with context

#### 2. Real-time Highlighting
- Toxic content automatically highlighted
- Color-coded severity levels:
  - 🔴 Red: CRITICAL (>80% toxicity)
  - 🟠 Orange: HIGH (60-80% toxicity)
  - 🟡 Yellow: MEDIUM (40-60% toxicity)
  - 🟢 Green: LOW (<40% toxicity)

#### 3. Screenshot Capture
- Right-click page → "Screenshot as Evidence"
- Captures full page and submits

#### 4. Keyboard Shortcuts
- `Ctrl+Shift+E` - Capture current page
- `Ctrl+Shift+M` - Toggle monitoring

### Configuration (manifest.json)

Update supported platforms:

```json
{
  "host_permissions": [
    "https://twitter.com/*",
    "https://facebook.com/*",
    "https://instagram.com/*",
    "https://reddit.com/*",
    "https://youtube.com/*",
    "https://tiktok.com/*"
  ]
}
```

### JavaScript API for Developers

```javascript
// In content script
chrome.runtime.sendMessage({
  action: 'analyzeToxicity',
  content: 'text to analyze'
}, (response) => {
  console.log('Toxicity score:', response.max_toxicity);
});

// In background script
chrome.tabs.sendMessage(tabId, {
  action: 'toggleMonitoring',
  enabled: true,
  sessionId: sessionId
});
```

---

## Bot Integration

### Telegram Bot

#### Setup

```bash
# Get Telegram Bot Token from @BotFather
export TELEGRAM_BOT_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
export TELEGRAM_WEBHOOK_URL="https://your-domain.com/api/v1/bots/telegram/webhook"

# Set webhook
curl -X POST "https://api.telegram.org/bot{TOKEN}/setWebhook" \
  -d "url={WEBHOOK_URL}"
```

#### Commands

```
/start - Welcome message
/submit - Submit text evidence
/photo - Submit screenshot evidence
/help - Get help
/history - View submission history
```

#### Example Conversation

```
User: /submit
Bot: 📝 Please send the text evidence you want to submit:

User: "You're so ugly, nobody likes you"
Bot: ✅ Evidence received!
     ID: ev_12345
     Toxicity: HIGH (0.88)
```

#### API Usage

```python
# Send message
requests.post(
    "http://localhost:8000/api/v1/bots/telegram/send",
    json={
        "user_id": "123456",
        "message": "Evidence received successfully!"
    }
)

# Get submission history
response = requests.get(
    "http://localhost:8000/api/v1/bots/telegram/submissions/123456"
)
```

### WhatsApp Bot (Twilio)

#### Setup

```bash
# Install Twilio
pip install twilio

# Set environment variables
export TWILIO_ACCOUNT_SID="AC..."
export TWILIO_AUTH_TOKEN="..."
export WHATSAPP_BOT_TOKEN="+1234567890"
```

#### Webhook Configuration

```python
# In your Flask app
@app.route('/api/v1/bots/whatsapp/webhook', methods=['POST'])
def whatsapp_webhook():
    # Processes WhatsApp messages
    # Supports text, images, documents
    pass
```

#### Message Flow

```
WhatsApp User: [sends message with screenshot]
Bot: ✅ Media received and secured!
     Evidence ID: ev_67890
     Secure Status: ENCRYPTED
```

---

## Webhook System

### Register Webhook

```http
POST /api/v1/webhooks/register

{
  "user_id": "user_123",
  "platform": "discord",
  "webhook_url": "https://discord.com/api/webhooks/123/abc",
  "secret_key": "optional_secret"
}

Response:
{
  "webhook": {
    "id": "wh_abc123...",
    "platform": "discord",
    "is_active": true,
    "created_at": "2024-04-26T10:00:00Z"
  }
}
```

### Supported Platforms

1. **Discord**
   - Receives channel messages
   - Posts reports to configured channel

2. **Slack**
   - Event API integration
   - Slash commands for reporting

3. **Twitter/X**
   - Monitors mentions and reports
   - Posts to timeline

4. **Telegram**
   - Forwards bot messages
   - Receives channel posts

### Event Types

```python
{
  'source': 'discord',
  'event_type': 'message_report',
  'content': 'toxic message',
  'author': 'username',
  'channel_id': '123456',
  'timestamp': '2024-04-26T10:00:00Z',
  'attachments': [...]
}
```

### Test Webhook

```http
POST /api/v1/webhooks/{webhook_id}/test

Response:
{
  "message": "Test webhook sent",
  "status_code": 200
}
```

---

## Advanced Analytics

### 1. Network Graph Visualization

```http
POST /api/v1/analytics/network-graph/{user_id}

{
  "evidence_data": [
    {
      "abuser_id": "user_123",
      "abuser_name": "@attacker",
      "victim_id": "user_456",
      "victim_name": "@victim",
      "platform": "twitter",
      "count": 5
    }
  ]
}

Response:
{
  "network_graph": {
    "nodes": [
      {
        "id": "user_123",
        "type": "abuser",
        "label": "@attacker",
        "metadata": {"incidents": 5}
      },
      ...
    ],
    "links": [
      {
        "source": 0,
        "target": 2,
        "type": "targets",
        "weight": 5
      }
    ],
    "stats": {
      "node_count": 10,
      "abuser_count": 3,
      "victim_count": 2,
      "platform_count": 5
    }
  }
}
```

**Visualization with D3.js:**

```html
<script src="https://d3js.org/d3.v7.min.js"></script>
<div id="network-graph"></div>

<script>
const data = response.network_graph;

// Create simulation
const simulation = d3.forceSimulation(data.nodes)
  .force("link", d3.forceLink(data.links).id(d => d.id).distance(100))
  .force("charge", d3.forceManyBody().strength(-500))
  .force("center", d3.forceCenter(400, 300));

// Render nodes and links
const svg = d3.select("#network-graph").append("svg");
// ... D3 visualization code
</script>
```

### 2. Heatmap Calendar

```http
POST /api/v1/analytics/heatmap-calendar/{user_id}

{
  "incidents": [
    {"date": "2024-04-25", "count": 3},
    {"date": "2024-04-26", "count": 7},
    {"date": "2024-04-27", "count": 2}
  ],
  "days_back": 365
}

Response:
{
  "heatmap_calendar": {
    "weeks": [
      [
        {"date": "2024-04-25", "count": 3, "intensity": "medium"},
        ...
      ]
    ],
    "total_incidents": 150,
    "peak_date": "2024-04-26",
    "peak_count": 12,
    "average_per_day": 0.41
  }
}
```

### 3. Predictive Escalation Model

```http
POST /api/v1/analytics/predictive-escalation/{user_id}

{
  "abuser_profiles": [
    {
      "abuser_id": "user_123",
      "incident_frequency": 45,
      "severity_trend": "increasing",
      "days_since_last_incident": 1,
      "avg_message_intensity": 85
    }
  ]
}

Response:
{
  "predictions": [
    {
      "abuser_id": "user_123",
      "risk_score": 0.87,
      "risk_level": "HIGH",
      "recommendation": "Prepare documentation for escalation",
      "factors": {
        "frequency": 45,
        "trend": "increasing",
        "recency": 1
      }
    }
  ],
  "critical_count": 2,
  "high_risk_count": 5
}
```

**Risk Levels:**
- CRITICAL (0.8-1.0): Immediate legal escalation
- HIGH (0.6-0.8): Prepare documentation
- MEDIUM (0.3-0.6): Increase monitoring
- LOW (0.0-0.3): Monitor but no action needed

### 4. Word Cloud Analysis

```http
POST /api/v1/analytics/word-cloud/{user_id}

{
  "content_items": [
    {"text": "toxic message content", "toxicity_score": 0.92},
    {"text": "hateful comment here", "toxicity_score": 0.87}
  ],
  "limit": 100
}

Response:
{
  "word_cloud": [
    {
      "word": "toxic",
      "frequency": 42,
      "toxicity_ratio": 0.95,
      "size": "xl"
    },
    {
      "word": "hate",
      "frequency": 28,
      "toxicity_ratio": 0.89,
      "size": "lg"
    }
  ],
  "total_words": 245,
  "toxic_words": 89
}
```

### 5. Time-of-Day Analysis

```http
POST /api/v1/analytics/time-pattern-analysis/{user_id}

{
  "incidents": [
    {"timestamp": "2024-04-26T14:30:00Z", "severity": 0.8},
    {"timestamp": "2024-04-26T22:15:00Z", "severity": 0.92},
    {"timestamp": "2024-04-27T02:45:00Z", "severity": 0.75}
  ]
}

Response:
{
  "analysis": {
    "hourly": {
      "hourly_pattern": {"00": 5, "01": 3, ..., "23": 8},
      "peak_hours": [[22, 12], [23, 10], [14, 9]],
      "average_per_hour": 0.58
    },
    "daily": {
      "daily_pattern": {
        "Monday": 15,
        "Tuesday": 18,
        "Wednesday": 12,
        "Thursday": 22,
        "Friday": 28,
        "Saturday": 8,
        "Sunday": 5
      },
      "peak_days": [["Friday", 28], ["Thursday", 22]],
      "weekend_incidents": 13,
      "weekday_incidents": 95
    }
  },
  "insights": {
    "peak_hour_range": "22:00-22:59",
    "peak_day": "Friday",
    "pattern": "Abuse spikes on Friday evenings"
  }
}
```

### 6. Comprehensive Dashboard

```http
POST /api/v1/analytics/comprehensive-dashboard/{user_id}

Body: { evidence_data, incidents, abuser_profiles, content_items }

Response:
{
  "sections": {
    "network_graph": {...},
    "heatmap": {...},
    "escalation_predictions": {...},
    "word_cloud": {...},
    "time_analysis": {...}
  }
}
```

---

## Mobile App

See [MOBILE_APP_GUIDE.md](./MOBILE_APP_GUIDE.md) for detailed React Native and Flutter implementation.

### Quick Links
- React Native Components
- Flutter Widgets
- API Integration
- Offline Support
- Push Notifications

---

## Deployment

### Environment Variables

```bash
# API Configuration
VAULT_API_URL=http://localhost:8000
API_KEY=your-secret-key

# Real-time & WebSocket
REDIS_URL=redis://localhost:6379

# Database
DATABASE_URL=sqlite:///evidence.db
SQLALCHEMY_TRACK_MODIFICATIONS=false

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_WEBHOOK_URL=https://your-domain.com/api/v1/bots/telegram/webhook

# WhatsApp (Twilio)
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
WHATSAPP_BOT_TOKEN=+1234567890

# Discord Webhook
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Encryption
ENCRYPTION_KEY=your-base64-encoded-key

# Analytics
ANALYTICS_ENABLED=true
ML_MODEL_VERSION=v1
```

### Docker Setup

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV FLASK_APP=app.py
ENV VAULT_API_URL=http://localhost:8000

CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "app:app"]
```

---

## Support

For issues or questions:
1. Check documentation
2. Search existing issues
3. Create new issue with detailed description
4. Contact support at support@evidencevault.io
