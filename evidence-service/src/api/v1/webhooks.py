"""
Webhook receiver for integrating external platforms (Discord, Slack, Twitter, Telegram)
"""
from flask import Blueprint, request, jsonify
from flask_cors import CORS
from datetime import datetime
import json
import hashlib
import hmac
import requests
from typing import Dict

bp = Blueprint('webhooks', __name__)
CORS(bp)

# ── Webhook Handlers ───────────────────────────────────────────────────────────

class WebhookManager:
    """Manages webhook configurations and incoming webhook events"""
    
    def __init__(self):
        self.webhook_configs = {}  # In production, load from database
        self.event_log = []
    
    def register_webhook(self, user_id: str, platform: str, webhook_url: str, 
                        secret_key: str = None) -> Dict:
        """Register a new webhook endpoint"""
        webhook_id = hashlib.md5(f"{user_id}_{platform}_{datetime.now().isoformat()}".encode()).hexdigest()
        
        config = {
            'id': webhook_id,
            'user_id': user_id,
            'platform': platform,
            'webhook_url': webhook_url,
            'secret_key': secret_key,
            'is_active': True,
            'created_at': datetime.now().isoformat(),
            'last_ping': None,
            'event_count': 0
        }
        
        self.webhook_configs[webhook_id] = config
        return config
    
    def verify_webhook_signature(self, platform: str, payload: bytes, 
                                signature: str, secret: str) -> bool:
        """Verify webhook signature based on platform"""
        if platform == 'discord':
            # Discord uses plain HMAC-SHA256
            expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected, signature)
        elif platform == 'slack':
            # Slack uses HMAC-SHA256 with version prefix
            expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
            return signature.endswith(expected)
        elif platform == 'telegram':
            # Telegram uses HMAC-SHA256
            expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected, signature)
        return False
    
    def process_discord_webhook(self, payload: Dict) -> Dict:
        """Process Discord webhook event"""
        return {
            'source': 'discord',
            'event_type': 'message_report',
            'content': payload.get('content', ''),
            'author': payload.get('author', {}).get('username', 'unknown'),
            'channel_id': payload.get('channel_id'),
            'message_id': payload.get('id'),
            'timestamp': payload.get('timestamp'),
            'attachments': payload.get('attachments', [])
        }
    
    def process_slack_webhook(self, payload: Dict) -> Dict:
        """Process Slack webhook event"""
        return {
            'source': 'slack',
            'event_type': 'message_report',
            'content': payload.get('event', {}).get('text', ''),
            'user_id': payload.get('event', {}).get('user'),
            'channel': payload.get('event', {}).get('channel'),
            'timestamp': payload.get('event', {}).get('ts'),
            'thread_ts': payload.get('event', {}).get('thread_ts')
        }
    
    def process_telegram_webhook(self, payload: Dict) -> Dict:
        """Process Telegram webhook event"""
        message = payload.get('message', {})
        return {
            'source': 'telegram',
            'event_type': 'message_report',
            'content': message.get('text', ''),
            'user_id': message.get('from', {}).get('id'),
            'user_name': message.get('from', {}).get('username'),
            'chat_id': message.get('chat', {}).get('id'),
            'message_id': message.get('message_id'),
            'timestamp': message.get('date'),
            'media': message.get('photo') or message.get('video') or message.get('document')
        }
    
    def process_twitter_webhook(self, payload: Dict) -> Dict:
        """Process Twitter webhook event"""
        data = payload.get('data', {})
        return {
            'source': 'twitter',
            'event_type': 'report_event',
            'content': data.get('text', ''),
            'tweet_id': data.get('id'),
            'author_id': data.get('author_id'),
            'created_at': data.get('created_at'),
            'public_metrics': data.get('public_metrics', {})
        }
    
    def forward_to_vault(self, webhook_event: Dict, vault_api_url: str, 
                        api_key: str) -> bool:
        """Forward processed webhook event to evidence vault"""
        try:
            headers = {'Authorization': f'Bearer {api_key}'}
            response = requests.post(
                f"{vault_api_url}/api/v1/webhooks/create-evidence",
                json=webhook_event,
                headers=headers,
                timeout=10
            )
            return response.status_code in [200, 201]
        except Exception as e:
            print(f"Error forwarding to vault: {e}")
            return False

manager = WebhookManager()

# ── Webhook API Endpoints ──────────────────────────────────────────────────────

@bp.route('/webhooks/register', methods=['POST'])
def register_webhook():
    """
    Register a new webhook integration
    POST /api/v1/webhooks/register
    Body: { user_id, platform, webhook_url, secret_key }
    """
    data = request.get_json()
    user_id = data.get('user_id')
    platform = data.get('platform')  # discord, slack, telegram, twitter
    webhook_url = data.get('webhook_url')
    secret_key = data.get('secret_key')
    
    if not all([user_id, platform, webhook_url]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if platform not in ['discord', 'slack', 'telegram', 'twitter']:
        return jsonify({'error': 'Unsupported platform'}), 400
    
    config = manager.register_webhook(user_id, platform, webhook_url, secret_key)
    return jsonify({
        'message': 'Webhook registered successfully',
        'webhook': config
    }), 201

@bp.route('/webhooks/discord', methods=['POST'])
def receive_discord_webhook():
    """
    Receive webhook from Discord
    POST /api/v1/webhooks/discord
    """
    try:
        payload = request.get_json()
        
        # Process Discord event
        event = manager.process_discord_webhook(payload)
        
        manager.event_log.append({
            'platform': 'discord',
            'event': event,
            'received_at': datetime.now().isoformat()
        })
        
        return jsonify({
            'message': 'Discord webhook received',
            'event_type': event['event_type']
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/webhooks/slack', methods=['POST'])
def receive_slack_webhook():
    """
    Receive webhook from Slack
    POST /api/v1/webhooks/slack
    """
    try:
        # Handle Slack URL verification
        data = request.get_json()
        if data.get('type') == 'url_verification':
            return jsonify({'challenge': data.get('challenge')}), 200
        
        # Process Slack event
        event = manager.process_slack_webhook(data)
        
        manager.event_log.append({
            'platform': 'slack',
            'event': event,
            'received_at': datetime.now().isoformat()
        })
        
        return jsonify({
            'message': 'Slack webhook received',
            'event_type': event['event_type']
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/webhooks/telegram', methods=['POST'])
def receive_telegram_webhook():
    """
    Receive webhook from Telegram
    POST /api/v1/webhooks/telegram
    """
    try:
        payload = request.get_json()
        
        if 'message' in payload:
            event = manager.process_telegram_webhook(payload)
            
            manager.event_log.append({
                'platform': 'telegram',
                'event': event,
                'received_at': datetime.now().isoformat()
            })
            
            return jsonify({
                'message': 'Telegram webhook received',
                'event_type': event['event_type']
            }), 200
        
        return jsonify({'message': 'Webhook acknowledged'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/webhooks/twitter', methods=['POST'])
def receive_twitter_webhook():
    """
    Receive webhook from Twitter/X API
    POST /api/v1/webhooks/twitter
    """
    try:
        payload = request.get_json()
        
        # Process Twitter event
        event = manager.process_twitter_webhook(payload)
        
        manager.event_log.append({
            'platform': 'twitter',
            'event': event,
            'received_at': datetime.now().isoformat()
        })
        
        return jsonify({
            'message': 'Twitter webhook received',
            'event_type': event['event_type']
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/webhooks/create-evidence', methods=['POST'])
def create_evidence_from_webhook():
    """
    Create evidence entry from webhook event
    POST /api/v1/webhooks/create-evidence
    """
    data = request.get_json()
    
    evidence = {
        'title': f"Evidence from {data.get('source', 'unknown')}",
        'description': data.get('content', ''),
        'source': data.get('source'),
        'event_type': data.get('event_type'),
        'original_payload': data,
        'created_at': datetime.now().isoformat()
    }
    
    # TODO: Save to database
    
    return jsonify({
        'message': 'Evidence created from webhook',
        'evidence': evidence
    }), 201

@bp.route('/webhooks/list/<user_id>', methods=['GET'])
def list_webhooks(user_id):
    """Get all registered webhooks for a user"""
    user_webhooks = [w for w in manager.webhook_configs.values() 
                     if w['user_id'] == user_id]
    return jsonify({
        'user_id': user_id,
        'webhooks': user_webhooks,
        'total': len(user_webhooks)
    }), 200

@bp.route('/webhooks/<webhook_id>/test', methods=['POST'])
def test_webhook(webhook_id):
    """Send a test event to the webhook"""
    if webhook_id not in manager.webhook_configs:
        return jsonify({'error': 'Webhook not found'}), 404
    
    config = manager.webhook_configs[webhook_id]
    test_payload = {
        'type': 'test_event',
        'timestamp': datetime.now().isoformat(),
        'message': 'This is a test webhook event from EvidenceVault'
    }
    
    try:
        response = requests.post(
            config['webhook_url'],
            json=test_payload,
            timeout=10
        )
        return jsonify({
            'message': 'Test webhook sent',
            'status_code': response.status_code
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/webhooks/<webhook_id>/delete', methods=['DELETE'])
def delete_webhook(webhook_id):
    """Delete a webhook configuration"""
    if webhook_id not in manager.webhook_configs:
        return jsonify({'error': 'Webhook not found'}), 404
    
    del manager.webhook_configs[webhook_id]
    return jsonify({'message': 'Webhook deleted successfully'}), 200

@bp.route('/webhooks/events/log', methods=['GET'])
def get_webhook_event_log():
    """Get recent webhook events"""
    limit = request.args.get('limit', 50, type=int)
    return jsonify({
        'total_events': len(manager.event_log),
        'recent_events': manager.event_log[-limit:],
        'timestamp': datetime.now().isoformat()
    }), 200
