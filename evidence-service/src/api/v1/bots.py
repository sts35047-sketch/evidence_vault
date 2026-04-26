"""
Bot Integration API Routes
Handles Telegram and WhatsApp bot webhooks
"""

from flask import Blueprint, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os

# Import bot services
from src.services.bots import BotManager

bp = Blueprint('bots', __name__)
CORS(bp)

# Initialize bot manager
VAULT_API_URL = os.environ.get('VAULT_API_URL', 'http://localhost:8000')
API_KEY = os.environ.get('API_KEY', 'evault-demo-key-2026')
bot_manager = BotManager(VAULT_API_URL, API_KEY)

# Create bot instances
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
telegram_bot = None
if TELEGRAM_TOKEN:
    telegram_bot = bot_manager.create_telegram_bot(TELEGRAM_TOKEN)

WHATSAPP_TOKEN = os.environ.get('WHATSAPP_BOT_TOKEN', '')
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
whatsapp_bot = None
if WHATSAPP_TOKEN and TWILIO_ACCOUNT_SID:
    whatsapp_bot = bot_manager.create_whatsapp_bot(
        WHATSAPP_TOKEN, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
    )

# ── Telegram Bot Routes ────────────────────────────────────────────────────────

@bp.route('/telegram/webhook', methods=['POST'])
def telegram_webhook():
    """
    Handle Telegram webhook updates
    POST /api/v1/bots/telegram/webhook
    """
    if not telegram_bot:
        return jsonify({'error': 'Telegram bot not configured'}), 503
    
    try:
        payload = request.get_json()
        result = telegram_bot.receive_webhook(payload)
        
        return jsonify({
            'status': 'success',
            'result': result,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/telegram/send', methods=['POST'])
def telegram_send():
    """
    Send message via Telegram bot
    POST /api/v1/bots/telegram/send
    """
    if not telegram_bot:
        return jsonify({'error': 'Telegram bot not configured'}), 503
    
    data = request.get_json()
    user_id = data.get('user_id')
    message = data.get('message')
    
    if not user_id or not message:
        return jsonify({'error': 'user_id and message required'}), 400
    
    result = telegram_bot.send_message(user_id, message)
    return jsonify(result), 200

@bp.route('/telegram/submissions/<user_id>', methods=['GET'])
def telegram_submissions(user_id):
    """Get Telegram submission history for user"""
    if not telegram_bot:
        return jsonify({'error': 'Telegram bot not configured'}), 503
    
    submissions = telegram_bot.get_user_submissions(user_id)
    return jsonify({
        'user_id': user_id,
        'submissions': submissions,
        'total': len(submissions)
    }), 200

@bp.route('/telegram/set-webhook', methods=['POST'])
def telegram_set_webhook():
    """Set webhook URL for Telegram bot"""
    if not telegram_bot:
        return jsonify({'error': 'Telegram bot not configured'}), 503
    
    data = request.get_json()
    webhook_url = data.get('webhook_url')
    
    if not webhook_url:
        return jsonify({'error': 'webhook_url required'}), 400
    
    result = telegram_bot.set_webhook(webhook_url)
    return jsonify(result), 200

# ── WhatsApp Bot Routes ────────────────────────────────────────────────────────

@bp.route('/whatsapp/webhook', methods=['POST'])
def whatsapp_webhook():
    """
    Handle WhatsApp webhook updates (Twilio)
    POST /api/v1/bots/whatsapp/webhook
    """
    if not whatsapp_bot:
        return jsonify({'error': 'WhatsApp bot not configured'}), 503
    
    try:
        payload = request.form.to_dict()
        result = whatsapp_bot.receive_webhook(payload)
        
        return jsonify({
            'status': 'success',
            'result': result,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/whatsapp/send', methods=['POST'])
def whatsapp_send():
    """
    Send message via WhatsApp
    POST /api/v1/bots/whatsapp/send
    """
    if not whatsapp_bot:
        return jsonify({'error': 'WhatsApp bot not configured'}), 503
    
    data = request.get_json()
    phone_number = data.get('phone_number')
    message = data.get('message')
    
    if not phone_number or not message:
        return jsonify({'error': 'phone_number and message required'}), 400
    
    result = whatsapp_bot.send_message(phone_number, message)
    return jsonify(result), 200

# ── General Bot Routes ─────────────────────────────────────────────────────────

@bp.route('/bots/status', methods=['GET'])
def bots_status():
    """Get status of all configured bots"""
    status = {
        'telegram': {
            'enabled': telegram_bot is not None,
            'submissions': len(telegram_bot.submissions) if telegram_bot else 0
        },
        'whatsapp': {
            'enabled': whatsapp_bot is not None,
            'submissions': len(whatsapp_bot.submissions) if whatsapp_bot else 0
        },
        'total_submissions': len(bot_manager.get_all_submissions()),
        'timestamp': datetime.now().isoformat()
    }
    return jsonify(status), 200

@bp.route('/bots/submissions', methods=['GET'])
def bots_submissions():
    """Get all submissions from all bots"""
    submissions = bot_manager.get_all_submissions()
    
    # Group by bot type
    grouped = {}
    for submission in submissions:
        bot_type = submission.get('bot_type', 'unknown')
        if bot_type not in grouped:
            grouped[bot_type] = []
        grouped[bot_type].append(submission)
    
    return jsonify({
        'total': len(submissions),
        'by_platform': {k: len(v) for k, v in grouped.items()},
        'submissions': submissions,
        'timestamp': datetime.now().isoformat()
    }), 200

@bp.route('/bots/submissions/<bot_type>/<user_id>', methods=['GET'])
def bot_user_submissions(bot_type, user_id):
    """Get submissions for specific user from specific bot"""
    bot = bot_manager.get_bot(bot_type)
    
    if not bot:
        return jsonify({'error': 'Bot not found'}), 404
    
    submissions = bot.get_user_submissions(user_id) if hasattr(bot, 'get_user_submissions') else []
    
    return jsonify({
        'bot_type': bot_type,
        'user_id': user_id,
        'submissions': submissions,
        'total': len(submissions)
    }), 200
