"""
Telegram & WhatsApp Bot Service for EvidenceVault
Allows users to submit evidence directly from chat apps
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
import requests
from abc import ABC, abstractmethod

# ── Base Bot Class ─────────────────────────────────────────────────────────────

class ChatBotBase(ABC):
    """Base class for chat platform bots"""
    
    def __init__(self, api_token: str, vault_api_url: str, api_key: str):
        self.api_token = api_token
        self.vault_api_url = vault_api_url
        self.api_key = api_key
        self.users = {}
        self.submissions = []
    
    @abstractmethod
    def send_message(self, user_id: str, message: str):
        """Send message to user"""
        pass
    
    @abstractmethod
    def receive_webhook(self, payload: Dict) -> Dict:
        """Process incoming webhook"""
        pass
    
    def create_evidence(self, user_id: str, content: str, 
                       platform: str, metadata: Dict = None) -> Dict:
        """Create evidence in vault"""
        evidence = {
            'bot_type': self.__class__.__name__,
            'user_id': user_id,
            'content': content,
            'platform': platform,
            'metadata': metadata or {},
            'submitted_at': datetime.now().isoformat()
        }
        
        try:
            headers = {'Authorization': f'Bearer {self.api_key}'}
            response = requests.post(
                f"{self.vault_api_url}/api/v1/webhooks/create-evidence",
                json=evidence,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                self.submissions.append({**evidence, 'status': 'submitted'})
                return result
        except Exception as e:
            print(f"Error creating evidence: {e}")
        
        return {'error': 'Failed to create evidence'}

# ── Telegram Bot ───────────────────────────────────────────────────────────────

class TelegramBot(ChatBotBase):
    """Telegram bot for evidence submission"""
    
    BASE_URL = "https://api.telegram.org/bot"
    
    def __init__(self, api_token: str, vault_api_url: str, api_key: str):
        super().__init__(api_token, vault_api_url, api_key)
        self.webhook_url = None
        self.users_context = {}
    
    def send_message(self, user_id: str, message: str, reply_markup=None):
        """Send message to Telegram user"""
        url = f"{self.BASE_URL}{self.api_token}/sendMessage"
        
        payload = {
            'chat_id': user_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        if reply_markup:
            payload['reply_markup'] = reply_markup
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.json()
        except Exception as e:
            print(f"Telegram send error: {e}")
            return {'ok': False}
    
    def set_webhook(self, webhook_url: str):
        """Set webhook URL for incoming updates"""
        url = f"{self.BASE_URL}{self.api_token}/setWebhook"
        payload = {'url': webhook_url}
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            self.webhook_url = webhook_url
            return response.json()
        except Exception as e:
            print(f"Webhook set error: {e}")
            return {'ok': False}
    
    def receive_webhook(self, payload: Dict) -> Dict:
        """Process incoming Telegram webhook"""
        
        if 'message' in payload:
            message = payload['message']
            user_id = message['from']['id']
            user_name = message['from'].get('username', 'anonymous')
            chat_id = message['chat']['id']
            
            # Handle text message
            if 'text' in message:
                text = message['text']
                return self._handle_text_message(user_id, user_name, chat_id, text)
            
            # Handle photo
            elif 'photo' in message:
                photo = message['photo'][-1]  # Get highest quality
                return self._handle_media(user_id, user_name, chat_id, 'photo', photo)
            
            # Handle document
            elif 'document' in message:
                document = message['document']
                return self._handle_media(user_id, user_name, chat_id, 'document', document)
        
        return {'status': 'ignored'}
    
    def _handle_text_message(self, user_id: str, user_name: str, 
                            chat_id: str, text: str) -> Dict:
        """Handle text message from Telegram"""
        
        if text.startswith('/start'):
            welcome_message = (
                "🛡️ <b>Welcome to EvidenceVault!</b>\n\n"
                "I can help you collect and secure evidence of cyberbullying.\n\n"
                "Commands:\n"
                "/submit - Submit text evidence\n"
                "/photo - Submit a screenshot\n"
                "/help - Get help\n"
            )
            self.send_message(chat_id, welcome_message)
            return {'status': 'welcome_sent'}
        
        elif text.startswith('/submit'):
            self.users_context[user_id] = {'mode': 'submit_text'}
            self.send_message(chat_id, "📝 Please send the text evidence you want to submit:")
            return {'status': 'waiting_for_text'}
        
        elif text.startswith('/help'):
            help_text = (
                "📚 <b>How to use EvidenceVault Bot:</b>\n\n"
                "1. <b>Text Evidence</b>: Use /submit and paste toxic messages\n"
                "2. <b>Screenshots</b>: Use /photo to send images\n"
                "3. <b>Context</b>: Include platform and date if possible\n\n"
                "All evidence is encrypted and securely stored."
            )
            self.send_message(chat_id, help_text)
            return {'status': 'help_sent'}
        
        else:
            # Check if user is in submission mode
            if user_id in self.users_context and self.users_context[user_id].get('mode') == 'submit_text':
                result = self.create_evidence(
                    user_id=str(user_id),
                    content=text,
                    platform='telegram',
                    metadata={'username': user_name, 'raw_message': text}
                )
                
                if 'error' not in result:
                    self.send_message(chat_id, 
                        f"✅ Evidence submitted successfully!\n"
                        f"Evidence ID: <code>{result.get('evidence_id', 'N/A')}</code>")
                else:
                    self.send_message(chat_id, "❌ Failed to submit evidence. Try again.")
                
                del self.users_context[user_id]
                return {'status': 'evidence_created', 'result': result}
            
            else:
                # Default response
                self.send_message(chat_id, 
                    "👋 Send me text evidence, photos, or use /help for commands.")
                return {'status': 'default_response'}
    
    def _handle_media(self, user_id: str, user_name: str, chat_id: str,
                      media_type: str, media_data: Dict) -> Dict:
        """Handle media (photo, document) from Telegram"""
        
        result = self.create_evidence(
            user_id=str(user_id),
            content=f"{media_type.upper()} Evidence",
            platform='telegram',
            metadata={
                'username': user_name,
                'media_type': media_type,
                'file_id': media_data.get('file_id'),
                'file_size': media_data.get('file_size')
            }
        )
        
        if 'error' not in result:
            self.send_message(chat_id,
                f"✅ {media_type.capitalize()} evidence received!\n"
                f"Evidence ID: <code>{result.get('evidence_id', 'N/A')}</code>")
        else:
            self.send_message(chat_id, "❌ Failed to process media.")
        
        return {'status': 'media_processed', 'result': result}
    
    def get_user_submissions(self, user_id: str) -> List[Dict]:
        """Get submission history for user"""
        return [s for s in self.submissions if s.get('user_id') == str(user_id)]

# ── WhatsApp Bot ───────────────────────────────────────────────────────────────

class WhatsAppBot(ChatBotBase):
    """WhatsApp bot using Twilio or official WhatsApp API"""
    
    def __init__(self, api_token: str, vault_api_url: str, api_key: str, 
                 account_sid: str = None, auth_token: str = None):
        super().__init__(api_token, vault_api_url, api_key)
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}"
    
    def send_message(self, phone_number: str, message: str):
        """Send WhatsApp message via Twilio"""
        url = f"{self.base_url}/Messages.json"
        
        payload = {
            'From': f'whatsapp:+{self.api_token}',
            'To': f'whatsapp:+{phone_number}',
            'Body': message
        }
        
        try:
            response = requests.post(
                url,
                auth=(self.account_sid, self.auth_token),
                data=payload,
                timeout=10
            )
            return response.json()
        except Exception as e:
            print(f"WhatsApp send error: {e}")
            return {'error': str(e)}
    
    def receive_webhook(self, payload: Dict) -> Dict:
        """Process incoming WhatsApp webhook from Twilio"""
        
        phone_number = payload.get('From', '').replace('whatsapp:+', '')
        message_body = payload.get('Body', '')
        message_sid = payload.get('MessageSid')
        
        # Handle media
        if 'MediaUrl0' in payload:
            media_urls = [v for k, v in payload.items() if k.startswith('MediaUrl')]
            media_types = [payload.get(k) for k in payload if k.startswith('MediaContentType')]
            
            for media_url, media_type in zip(media_urls, media_types):
                result = self.create_evidence(
                    user_id=phone_number,
                    content=f"Media: {media_type}",
                    platform='whatsapp',
                    metadata={'media_url': media_url, 'media_type': media_type}
                )
                
                self.send_message(phone_number, "✅ Media received and secured!")
                return {'status': 'media_processed', 'result': result}
        
        # Handle text
        if message_body:
            result = self.create_evidence(
                user_id=phone_number,
                content=message_body,
                platform='whatsapp',
                metadata={'phone_number': phone_number}
            )
            
            self.send_message(phone_number, f"✅ Evidence received!\nID: {result.get('evidence_id', 'N/A')}")
            return {'status': 'text_processed', 'result': result}
        
        return {'status': 'ignored'}

# ── Bot Manager ────────────────────────────────────────────────────────────────

class BotManager:
    """Manages multiple bot instances"""
    
    def __init__(self, vault_api_url: str, api_key: str):
        self.vault_api_url = vault_api_url
        self.api_key = api_key
        self.bots = {}
    
    def create_telegram_bot(self, token: str, name: str = 'telegram') -> TelegramBot:
        """Create and register Telegram bot"""
        bot = TelegramBot(token, self.vault_api_url, self.api_key)
        self.bots[name] = bot
        return bot
    
    def create_whatsapp_bot(self, twilio_token: str, account_sid: str, 
                           auth_token: str, name: str = 'whatsapp') -> WhatsAppBot:
        """Create and register WhatsApp bot"""
        bot = WhatsAppBot(twilio_token, self.vault_api_url, self.api_key,
                         account_sid, auth_token)
        self.bots[name] = bot
        return bot
    
    def get_bot(self, name: str) -> Optional[ChatBotBase]:
        """Get bot by name"""
        return self.bots.get(name)
    
    def get_all_submissions(self) -> List[Dict]:
        """Get all submissions from all bots"""
        all_submissions = []
        for bot in self.bots.values():
            all_submissions.extend(bot.submissions)
        return all_submissions
