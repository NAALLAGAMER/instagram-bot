"""
Instagram Bot Module - Updated to use config
"""

import os
import random
import asyncio
from datetime import datetime, timedelta
from loguru import logger
from instagrapi import Client

class InstagramBot:
    def __init__(self, username: str, password: str, config: dict = None):
        self.username = username
        self.password = password
        self.config = config or {}
        self.client = Client()
        self.telegram = None
        self.is_running = False
        self.user_id = None
        self.replied_users = {}
        
        # Statistics
        self.daily_stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'likes_given': 0,
            'flirts_sent': 0
        }
        
        # Flirt messages based on level
        self.flirt_messages = self.get_flirt_messages()
        
        logger.info(f"✅ Instagram Bot initialized for {username}")
    
    def get_flirt_messages(self):
        """Get flirt messages based on configured level"""
        level = self.config.get('flirt_level', 'moderate')
        
        base_messages = {
            'greeting': [
                "Hey {name}! Thanks for messaging me! 😊",
                "Hello {name}! How's your day going? 🌟",
            ],
            'compliment': [
                "That's very kind! 😊",
                "You're too sweet! 💕",
            ],
            'response': [
                "Thanks for your message! 😊",
                "Good to hear from you! 💫",
            ]
        }
        
        if level == 'high':
            base_messages['flirty'] = [
                "You're quite the charmer! 😉",
                "I like your style! 😊",
                "You know how to make someone smile! ✨",
            ]
            base_messages['romantic'] = [
                "You have a way with words! 💕",
                "That's so romantic! 🌹",
            ]
        
        return base_messages
    
    def set_telegram_controller(self, telegram_bot):
        """Set Telegram controller"""
        self.telegram = telegram_bot
    
    async def login(self) -> bool:
        """Login to Instagram"""
        try:
            logger.info(f"📱 Logging into Instagram as @{self.username}...")
            self.client.login(self.username, self.password)
            self.user_id = self.client.user_id
            logger.success(f"✅ Logged in as @{self.username}")
            return True
        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            return False
    
    async def check_messages(self):
        """Check for new Instagram messages"""
        try:
            threads = self.client.direct_threads(amount=20)
            new_messages = []
            
            for thread in threads:
                if thread.unread_count > 0:
                    user = thread.users[0]
                    messages = self.client.direct_messages(thread.id, amount=thread.unread_count)
                    
                    for msg in messages:
                        if msg.text:
                            new_messages.append({
                                'user_id': str(user.pk),
                                'username': user.username,
                                'thread_id': thread.id,
                                'text': msg.text,
                                'timestamp': msg.timestamp
                            })
                            
                            self.daily_stats['messages_received'] += 1
                            
                            if self.telegram:
                                await self.telegram.notify_new_message(user.username, msg.text)
            
            return new_messages
        except Exception as e:
            logger.error(f"❌ Error checking messages: {e}")
            return []
    
    def analyze_message(self, text: str) -> str:
        """Analyze message type"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['hi', 'hello', 'hey']):
            return 'greeting'
        elif any(word in text_lower for word in ['nice', 'beautiful', 'cute']):
            return 'compliment'
        elif '?' in text:
            return 'question'
        elif any(word in text_lower for word in ['love', 'date', 'crush']):
            return 'flirty'
        
        return 'response'
    
    def generate_response(self, message_type: str, username: str) -> str:
        """Generate appropriate response"""
        if message_type in self.flirt_messages:
            responses = self.flirt_messages[message_type]
        else:
            responses = self.flirt_messages.get('response', ["Thanks! 😊"])
        
        response = random.choice(responses)
        return response.replace('{name}', username)
    
    async def send_reply(self, thread_id: str, message: str, username: str):
        """Send reply"""
        max_replies = self.config.get('max_replies_per_hour', 50)
        
        if self.daily_stats['messages_sent'] >= max_replies:
            logger.warning(f"⏳ Daily limit ({max_replies}) reached")
            return False
        
        try:
            delay = random.randint(30, 90)
            logger.info(f"⏳ Waiting {delay}s before replying...")
            await asyncio.sleep(delay)
            
            self.client.direct_send(message, thread_ids=[thread_id])
            self.daily_stats['messages_sent'] += 1
            
            self.replied_users[username] = {
                'time': datetime.now(),
                'message': message[:50]
            }
            
            logger.success(f"✅ Replied to @{username}")
            
            if self.telegram:
                await self.telegram.notify_reply(username, message)
            
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send reply: {e}")
            return False
    
    async def run(self):
        """Main bot loop"""
        self.is_running = True
        logger.info(f"🚀 Instagram bot started")
        
        check_interval = self.config.get('check_interval', 60)
        
        while self.is_running:
            try:
                new_messages = await self.check_messages()
                
                for msg in new_messages:
                    if msg['username'] in self.replied_users:
                        last_reply = self.replied_users[msg['username']]['time']
                        if datetime.now() - last_reply < timedelta(hours=2):
                            continue
                    
                    msg_type = self.analyze_message(msg['text'])
                    response = self.generate_response(msg_type, msg['username'])
                    await self.send_reply(msg['thread_id'], response, msg['username'])
                
                await asyncio.sleep(check_interval)
            except Exception as e:
                logger.error(f"❌ Error: {e}")
                await asyncio.sleep(300)