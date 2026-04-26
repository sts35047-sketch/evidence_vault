# EvidenceVault Advanced Features - Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
cd evidence-service
pip install -r requirements.txt
```

### 2. Database Migration

```bash
python -c "from src.db.models import *; print('Models imported successfully')"
```

### 3. Configure Environment

Create `.env` file in project root:

```bash
# API Configuration
VAULT_API_URL=http://localhost:8000
API_KEY=evault-demo-key-2026

# Database
DATABASE_URL=sqlite:///evidence.db

# Real-time Features
REDIS_URL=redis://localhost:6379

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_WEBHOOK_URL=https://your-domain.com/api/v1/bots/telegram/webhook

# WhatsApp (Twilio)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
WHATSAPP_BOT_TOKEN=your_whatsapp_number

# Encryption
ENCRYPTION_KEY=your-base64-key

# Gemini API
GEMINI_API_KEY=your_gemini_key
```

### 4. Browser Extension Setup

1. Extract `extension/` folder
2. Open `chrome://extensions`
3. Enable "Developer mode" (top-right)
4. Click "Load unpacked"
5. Select the `extension/` folder
6. Configure API endpoint in extension options

### 5. Start Application

```bash
# Main app
python app.py

# Or FastAPI server
cd evidence-service
uvicorn src.app:app --reload --port 8000
```

---

## Feature-by-Feature Setup

### Real-time Monitoring

**Start monitoring session:**

```bash
curl -X GET "http://localhost:8000/api/v1/realtime/stream/session_123"
```

**Analyze content:**

```bash
curl -X POST "http://localhost:8000/api/v1/realtime/analyze" \
  -H "Content-Type: application/json" \
  -d '{"content":"toxic message","session_id":"session_123"}'
```

### Telegram Bot

**1. Get Token from @BotFather**

```
Message to @BotFather:
/start
/newbot
Name: EvidenceVault
Username: evidencevault_bot
(copy token)
```

**2. Set Webhook**

```bash
export TELEGRAM_BOT_TOKEN="your_token"
export WEBHOOK_URL="https://your-domain.com/api/v1/bots/telegram/webhook"

curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  -d "url=${WEBHOOK_URL}"
```

**3. Test Bot**

```bash
# Search for @evidencevault_bot and send:
/start
/submit
[paste toxic message]
```

### WhatsApp Bot (Twilio)

**1. Create Twilio Account**
- Visit twilio.com
- Create account and get credentials
- Get WhatsApp sandbox number

**2. Configure in Code**

```python
# In app.py or environment
TWILIO_ACCOUNT_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_AUTH_TOKEN = "your_auth_token"
WHATSAPP_NUMBER = "+14155552671"  # Sandbox number
```

**3. Send Test Message**

```bash
curl -X POST "http://localhost:8000/api/v1/bots/whatsapp/send" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "15551234567",
    "message": "Hello from EvidenceVault"
  }'
```

### Webhook Integration

**Discord Setup:**

```bash
# Create Discord webhook in channel settings
# Copy webhook URL

curl -X POST "http://localhost:8000/api/v1/webhooks/register" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "platform": "discord",
    "webhook_url": "https://discord.com/api/webhooks/...",
    "secret_key": "optional_secret"
  }'
```

**Slack Setup:**

```bash
# Create Slack bot in workspace
# Get bot token and configure

curl -X POST "http://localhost:8000/api/v1/webhooks/register" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "platform": "slack",
    "webhook_url": "https://hooks.slack.com/services/...",
    "secret_key": "bot_token"
  }'
```

### Analytics Dashboard

**Get Comprehensive Analytics:**

```bash
curl -X POST "http://localhost:8000/api/v1/analytics/comprehensive-dashboard/user_123" \
  -H "Content-Type: application/json" \
  -d '{
    "evidence_data": [...],
    "incidents": [...],
    "abuser_profiles": [...],
    "content_items": [...]
  }'
```

### Mobile App

**React Native:**

```bash
npx react-native init EvidenceVault
cd EvidenceVault
npm install axios react-native-camera react-native-file-picker

# Configure API endpoint in src/api/client.js
# Run on iOS or Android
npx react-native run-ios
# or
npx react-native run-android
```

**Flutter:**

```bash
flutter create evidence_vault
cd evidence_vault
flutter pub add dio camera image_picker

# Configure API endpoint
flutter run
```

---

## API Testing

### Using Postman

1. Import API collection:
   - File → Import
   - Paste JSON below

```json
{
  "info": {"name": "EvidenceVault API", "version": "2.0"},
  "item": [
    {
      "name": "Real-time",
      "item": [
        {
          "name": "Analyze",
          "request": {
            "method": "POST",
            "url": "{{base_url}}/realtime/analyze",
            "body": {"content": "toxic message", "session_id": "session_123"}
          }
        }
      ]
    },
    {
      "name": "Analytics",
      "item": [
        {
          "name": "Network Graph",
          "request": {
            "method": "POST",
            "url": "{{base_url}}/analytics/network-graph/user_123",
            "body": {"evidence_data": []}
          }
        }
      ]
    }
  ]
}
```

### Using cURL

All examples provided in feature sections above.

### Using Python

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Analyze text
response = requests.post(
    f"{BASE_URL}/realtime/analyze",
    json={"content": "toxic message", "session_id": "session_123"}
)
print(response.json())

# Get network graph
response = requests.post(
    f"{BASE_URL}/analytics/network-graph/user_123",
    json={"evidence_data": []}
)
print(response.json())

# Get dashboard
response = requests.post(
    f"{BASE_URL}/analytics/comprehensive-dashboard/user_123",
    json={...}
)
print(response.json())
```

---

## Troubleshooting

### Real-time Not Working

```bash
# Check Redis connection
redis-cli ping
# Should return PONG

# Verify Detoxify is installed
python -c "from detoxify import Detoxify; print('OK')"

# Check API logs
tail -f app.log
```

### Bot Not Receiving Messages

```bash
# Verify webhook is set
curl https://api.telegram.org/bot{TOKEN}/getWebhookInfo

# Test webhook
curl -X POST https://your-domain.com/api/v1/bots/telegram/webhook \
  -H "Content-Type: application/json" \
  -d '{"message":{"text":"test"}}'

# Check firewall/SSL
# Ensure webhook URL is accessible from internet
```

### Analytics Not Loading

```bash
# Check database
sqlite3 evidence.db ".tables"

# Verify data format
python -c "
import json
data = {
    'evidence_data': [...],
    'incidents': [...]
}
print(json.dumps(data))
"
```

### Browser Extension Issues

```bash
# Check console
Right-click → Inspect → Console tab

# Verify API endpoint
# Extension Options → Check URL and API Key

# Check permissions in manifest.json
# Ensure platform URLs match
```

---

## Performance Optimization

### For Real-time Monitoring

```python
# Use Redis for caching
from redis import Redis
cache = Redis(host='localhost', port=6379)

# Batch analyze instead of one-by-one
# Limit monitoring to N characters
MAX_ANALYZE_CHARS = 5000

# Use async processing
from celery import Celery
app = Celery('tasks')

@app.task
def analyze_async(content):
    # Async analysis
    pass
```

### For Analytics

```python
# Cache heatmap calculations
# Limit historical data to relevant period
# Use aggregated queries

# Example aggregation
db.session.query(
    IncidentMetric.date,
    func.sum(IncidentMetric.incident_count)
).group_by(IncidentMetric.date)
```

### For Bot Processing

```python
# Queue bot messages
# Use rate limiting
# Batch evidence submission
```

---

## Security Best Practices

1. **API Keys**
   - Store in environment variables
   - Rotate regularly
   - Never commit to git

2. **Webhooks**
   - Verify signatures
   - Use HTTPS only
   - IP whitelist where possible

3. **Database**
   - Enable encryption at rest
   - Use strong passwords
   - Regular backups

4. **Browser Extension**
   - Validate URLs before sending data
   - Store session keys securely
   - Clear cache on logout

5. **Bots**
   - Validate user input
   - Rate limit submissions
   - Log all activities

---

## Next Steps

1. ✅ Set up database and models
2. ✅ Configure bot integrations
3. ✅ Deploy webhook receivers
4. ✅ Build analytics dashboard UI
5. ✅ Test browser extension
6. ✅ Deploy mobile apps
7. Monitor and optimize performance
8. Gather user feedback
9. Iterate on features

---

## Additional Resources

- [Advanced Features Documentation](./ADVANCED_FEATURES.md)
- [Mobile App Guide](./MOBILE_APP_GUIDE.md)
- [API Reference](./API_REFERENCE.md)
- [Contributing Guidelines](./CONTRIBUTING.md)

---

## Support

- Documentation: See `*.md` files
- Issues: GitHub Issues
- Email: support@evidencevault.io
- Discord: [Join Community](https://discord.gg/evidencevault)
