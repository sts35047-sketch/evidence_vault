# EvidenceVault API Quick Reference

## Base URL
```
http://localhost:8000/api/v1
```

---

## 🔴 Real-time Endpoints

### Analyze Content
```bash
POST /realtime/analyze
Content-Type: application/json

{
  "content": "toxic message",
  "session_id": "session_123",
  "source_url": "https://twitter.com/..."
}

Response: { "scores": {...}, "is_toxic": true, "max_toxicity": 0.92 }
```

### Stream Events
```bash
GET /realtime/stream/{session_id}

Response: Server-Sent Events
data: {"type": "toxicity_detected", "score": 0.92}
```

### Screenshot Monitor
```bash
POST /realtime/screenshot-monitor
Content-Type: multipart/form-data

- screenshot: [image file]
- session_id: "session_123"
- platform: "twitter"
- url: "https://twitter.com/..."

Response: {"filename": "screenshot_12345.png"}
```

### Session Status
```bash
GET /realtime/status/{session_id}

Response: {"session_id": "...", "message_count": 45, "alerts": [...]}
```

### Highlight Toxic
```bash
POST /realtime/highlight-toxic

{ "page_content": "text content here" }

Response: {"toxic_count": 5, "highlights": [...]}
```

---

## 📊 Analytics Endpoints

### Network Graph
```bash
POST /analytics/network-graph/{user_id}

{
  "evidence_data": [
    {
      "abuser_id": "user_123",
      "abuser_name": "@attacker",
      "victim_id": "user_456",
      "platform": "twitter",
      "count": 5
    }
  ]
}

Response: {"nodes": [...], "links": [...], "stats": {...}}
```

### Heatmap Calendar
```bash
POST /analytics/heatmap-calendar/{user_id}

{
  "incidents": [
    {"date": "2024-04-25", "count": 3},
    {"date": "2024-04-26", "count": 7}
  ],
  "days_back": 365
}

Response: {"weeks": [...], "total_incidents": 150, "peak_date": "2024-04-26"}
```

### Predictive Escalation
```bash
POST /analytics/predictive-escalation/{user_id}

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

Response: {"predictions": [...], "critical_count": 2, "high_risk_count": 5}
```

### Single Risk Score
```bash
POST /analytics/single-risk-score

{
  "incident_frequency": 45,
  "severity_trend": "increasing",
  "days_since_last_incident": 1,
  "avg_message_intensity": 85
}

Response: {"risk_score": 0.87, "risk_level": "HIGH", "recommendation": "..."}
```

### Word Cloud
```bash
POST /analytics/word-cloud/{user_id}

{
  "content_items": [
    {"text": "toxic message", "toxicity_score": 0.92}
  ],
  "limit": 100
}

Response: {"word_cloud": [...], "total_words": 245}
```

### Time Pattern Analysis
```bash
POST /analytics/time-pattern-analysis/{user_id}

{
  "incidents": [
    {"timestamp": "2024-04-26T14:30:00Z", "severity": 0.8}
  ]
}

Response: {"hourly": {...}, "daily": {...}, "insights": {...}}
```

### Comprehensive Dashboard
```bash
POST /analytics/comprehensive-dashboard/{user_id}

{
  "evidence_data": [...],
  "incidents": [...],
  "abuser_profiles": [...],
  "content_items": [...]
}

Response: {"sections": {"network_graph": {...}, "heatmap": {...}, ...}}
```

### Export Analytics
```bash
POST /analytics/export/{user_id}/{format}

Formats: json, csv

Response: Exported data in requested format
```

---

## 🪝 Webhook Endpoints

### Register Webhook
```bash
POST /webhooks/register

{
  "user_id": "user_123",
  "platform": "discord",
  "webhook_url": "https://discord.com/api/webhooks/...",
  "secret_key": "optional_secret"
}

Response: {"webhook": {"id": "wh_abc...", "platform": "discord"}}
```

### Discord Webhook
```bash
POST /webhooks/discord

Discord Event Payload (automatic)

Response: {"message": "Discord webhook received"}
```

### Slack Webhook
```bash
POST /webhooks/slack

Slack Event Payload (automatic)

Response: {"message": "Slack webhook received"}
```

### Telegram Webhook
```bash
POST /webhooks/telegram

Telegram Update Payload (automatic)

Response: {"message": "Telegram webhook received"}
```

### Twitter Webhook
```bash
POST /webhooks/twitter

Twitter Event Payload (automatic)

Response: {"message": "Twitter webhook received"}
```

### Create Evidence from Webhook
```bash
POST /webhooks/create-evidence

{
  "source": "discord",
  "content": "toxic message",
  "event_type": "message_report"
}

Response: {"evidence": {"id": "ev_123"}}
```

### List Webhooks
```bash
GET /webhooks/list/{user_id}

Response: {"webhooks": [...], "total": 3}
```

### Test Webhook
```bash
POST /webhooks/{webhook_id}/test

Response: {"message": "Test webhook sent", "status_code": 200}
```

### Delete Webhook
```bash
DELETE /webhooks/{webhook_id}/delete

Response: {"message": "Webhook deleted successfully"}
```

### Event Log
```bash
GET /webhooks/events/log?limit=50

Response: {"total_events": 100, "recent_events": [...]}
```

---

## 🤖 Bot Endpoints

### Telegram Webhook
```bash
POST /bots/telegram/webhook

Telegram Update (automatic)

Response: {"status": "success", "result": {...}}
```

### Telegram Send
```bash
POST /bots/telegram/send

{
  "user_id": "123456",
  "message": "Evidence submitted!"
}

Response: Telegram API response
```

### Telegram Submissions
```bash
GET /bots/telegram/submissions/{user_id}

Response: {"submissions": [...], "total": 5}
```

### Set Telegram Webhook
```bash
POST /bots/telegram/set-webhook

{
  "webhook_url": "https://your-domain.com/api/v1/bots/telegram/webhook"
}

Response: Telegram webhook confirmation
```

### WhatsApp Webhook
```bash
POST /bots/whatsapp/webhook

Twilio Message (automatic)

Response: {"status": "success"}
```

### WhatsApp Send
```bash
POST /bots/whatsapp/send

{
  "phone_number": "15551234567",
  "message": "Evidence received!"
}

Response: Twilio API response
```

### Bot Status
```bash
GET /bots/status

Response: {
  "telegram": {"enabled": true, "submissions": 45},
  "whatsapp": {"enabled": true, "submissions": 23}
}
```

### All Submissions
```bash
GET /bots/submissions

Response: {"total": 68, "by_platform": {...}, "submissions": [...]}
```

### User Submissions by Bot
```bash
GET /bots/submissions/{bot_type}/{user_id}

Response: {"submissions": [...], "total": 12}
```

---

## Response Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not found |
| 500 | Server error |
| 503 | Service unavailable |

---

## Common Parameters

```javascript
// In headers
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

// Common query params
?limit=50           // Pagination
?offset=0           // Offset
?sort=date          // Sorting
?filter=HIGH        // Filtering
```

---

## Rate Limits (Recommended)

- Real-time analyze: 100 req/min
- Analytics: 50 req/min
- Webhooks: 1000 req/min
- Bots: 100 req/min

---

## Example cURL Commands

```bash
# Analyze toxicity
curl -X POST http://localhost:8000/api/v1/realtime/analyze \
  -H "Content-Type: application/json" \
  -d '{"content":"toxic message","session_id":"session_123"}'

# Get network graph
curl -X POST http://localhost:8000/api/v1/analytics/network-graph/user_123 \
  -H "Content-Type: application/json" \
  -d '{"evidence_data":[]}'

# Register webhook
curl -X POST http://localhost:8000/api/v1/webhooks/register \
  -H "Content-Type: application/json" \
  -d '{
    "user_id":"user_123",
    "platform":"discord",
    "webhook_url":"https://discord.com/api/webhooks/..."
  }'

# Send Telegram message
curl -X POST http://localhost:8000/api/v1/bots/telegram/send \
  -H "Content-Type: application/json" \
  -d '{"user_id":"123456","message":"Evidence received!"}'

# Get predictions
curl -X POST http://localhost:8000/api/v1/analytics/predictive-escalation/user_123 \
  -H "Content-Type: application/json" \
  -d '{
    "abuser_profiles":[{
      "abuser_id":"user_456",
      "incident_frequency":45,
      "severity_trend":"increasing",
      "days_since_last_incident":1,
      "avg_message_intensity":85
    }]
  }'
```

---

## Python SDK Example

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "your-api-key"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Analyze content
response = requests.post(
    f"{BASE_URL}/realtime/analyze",
    json={"content": "toxic message", "session_id": "session_123"},
    headers=headers
)
print(response.json())

# Get analytics
response = requests.post(
    f"{BASE_URL}/analytics/comprehensive-dashboard/user_123",
    json={
        "evidence_data": [],
        "incidents": [],
        "abuser_profiles": [],
        "content_items": []
    },
    headers=headers
)
print(json.dumps(response.json(), indent=2))
```

---

## JavaScript SDK Example

```javascript
const BASE_URL = "http://localhost:8000/api/v1";
const API_KEY = "your-api-key";

async function analyzeContent(content, sessionId) {
  const response = await fetch(`${BASE_URL}/realtime/analyze`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${API_KEY}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      content: content,
      session_id: sessionId
    })
  });
  
  return response.json();
}

async function getAnalytics(userId) {
  const response = await fetch(
    `${BASE_URL}/analytics/comprehensive-dashboard/${userId}`,
    {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${API_KEY}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        evidence_data: [],
        incidents: [],
        abuser_profiles: [],
        content_items: []
      })
    }
  );
  
  return response.json();
}
```

---

## Troubleshooting

### 401 Unauthorized
- Check API key is correct
- Verify Authorization header format

### 404 Not Found
- Check endpoint URL spelling
- Verify path parameters (user_id, session_id, etc.)

### 500 Server Error
- Check server logs
- Verify request body format
- Check database connectivity

### Timeout
- Check network connectivity
- Verify API server is running
- Check for large data requests

---

## Resources

- Full Docs: `ADVANCED_FEATURES.md`
- Setup: `SETUP_GUIDE.md`
- Mobile: `MOBILE_APP_GUIDE.md`
- Examples: See `.md` files in project

---

Last Updated: April 26, 2024
