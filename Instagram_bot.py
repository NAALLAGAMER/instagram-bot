"""
Instagram Bot with Auto-Reply and Flirting Features
Dynamically configured via Telegram/Web
"""

import os
import random
import asyncio
import json
from datetime import datetime, timedelta
from collections import defaultdict
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
            'flirts_sent': 0,
            'follows_done': 0
        }
        
        # Load or create flirt messages
        self.flirt_messages = self.load_flirt_messages()
        
        logger.info(f"✅ Instagram Bot initialized for {username}")
    
    def load_flirt_messages(self):
        """Load flirt messages from file or use defaults"""
        messages_file = 'flirt_messages.json'
        
        default_messages = {
            'greeting': [
                "Hey {name}! Thanks for messaging me! 😊",
                "Hello {name}! How can I help you today? 🌟",
                "Hi there! Good to hear from you! ✨",
            ],
            'compliment': [
                "That's very kind of you to say! 😊",
                "You're too sweet! Thank you! 💕",
                "Aww, you just made my day! ✨",
            ],
            'flirty': [
                "You're quite the charmer, aren't you? 😉",
                "I like your style! 😊",
                "You know how to make someone smile! ✨",
            ],
            'romantic': [
                "You have a way with words! 💕",
                "That's so romantic! 🌹",
                "You're making me blush! 😊",
            ],
            'question': [
                "That's interesting! Tell me more! 💭",
                "Great question! What do you think? 🤔",
                "I'd love to hear your thoughts! ✨",
            ],
            'response': [
                "Thanks for your message! 😊",
                "I appreciate you reaching out! ✨",
                "Good to hear from you! 💫",
            ]
        }
        
        if os.path.exists(messages_file):
            with open(messages_file, 'r') as f:
                return json.load(f)
        else:
            with open(messages_file, 'w') as f:
                json.dump(default_messages, f, indent=2)
            return default_messages
    
    def save_flirt_messages(self):
        """Save flirt messages to file"""
        with open('flirt_messages.json', 'w') as f:
            json.dump(self.flirt_messages, f, indent=2)
    
    def add_flirt_message(self, category: str, message: str):
        """Add new flirt message"""
        if category in self.flirt_messages:
            self.flirt_messages[category].append(message)
            self.save_flirt_messages()
            logger.info(f"✅ Added new {category} message: {message}")
    
    def remove_flirt_message(self, category: str, index: int):
        """Remove flirt message"""
        if category in self.flirt_messages and 0 <= index < len(self.flirt_messages[category]):
            removed = self.flirt_messages[category].pop(index)
            self.save_flirt_messages()
            logger.info(f"✅ Removed {category} message: {removed}")
    
    def set_telegram_controller(self, telegram_bot):
        """Set Telegram controller"""
        self.telegram = telegram_bot
    
    async def login(self) -> bool:
        """Login to Instagram"""
        try:
            logger.info(f"📱 Logging into Instagram as @{self.username}...")
            
            self.client.set_user_agent(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
            )
            
            self.client.login(self.username, self.password)
            self.user_id = self.client.user_id
            
            user_info = self.client.user_info(self.user_id)
            logger.success(f"✅ Logged in as @{user_info.username}")
            
            if self.telegram:
                await self.telegram.notify_admin(
                    f"✅ *Instagram Bot Logged In*\n\n"
                    f"Account: @{user_info.username}"
                )
            
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
                        if msg.text and not self.is_auto_reply(msg.text):
                            new_messages.append({
                                'user_id': str(user.pk),
                                'username': user.username,
                                'thread_id': thread.id,
                                'text': msg.text,
                                'timestamp': msg.timestamp
                            })
                            
                            self.daily_stats['messages_received'] += 1
                            
                            # Notify Telegram
                            if self.telegram:
                                await self.telegram.notify_new_message(user.username, msg.text)
            
            return new_messages
            
        except Exception as e:
            logger.error(f"❌ Error checking messages: {e}")
            return []
    
    def is_auto_reply(self, text: str) -> bool:
        """Check if message is from auto-reply"""
        auto_reply_indicators = ["auto-reply", "automatic", "bot reply"]
        return any(indicator in text.lower() for indicator in auto_reply_indicators)
    
    def analyze_message(self, text: str) -> str:
        """Analyze message type"""
        text_lower = text.lower()
        
        # Check for keywords
        if any(word in text_lower for word in ['hi', 'hello', 'hey']):
            return 'greeting'
        elif any(word in text_lower for word in ['nice', 'beautiful', 'cute', 'pretty']):
            return 'compliment'
        elif any(word in text_lower for word in ['love', 'date', 'crush', 'like you']):
            return 'romantic'
        elif '?' in text:
            return 'question'
        elif any(word in text_lower for word in ['flirt', 'sexy', 'hot']):
            return 'flirty'
        
        return 'response'
    
    def generate_response(self, message_type: str, username: str) -> str:
        """Generate appropriate response"""
        # Get flirt level from config
        flirt_level = self.config.get('flirt_level', 'moderate')
        
        # Select appropriate category
        if message_type in self.flirt_messages:
            responses = self.flirt_messages[message_type]
        else:
            responses = self.flirt_messages['response']
        
        # Adjust based on flirt level
        if flirt_level == 'low':
            responses = [r for r in responses if '😊' in r or '👋' in r]
        elif flirt_level == 'high':
            # Include more romantic/flirty messages
            if 'romantic' in self.flirt_messages:
                responses.extend(self.flirt_messages['romantic'])
        
        if not responses:
            responses = self.flirt_messages['response']
        
        # Get random response
        response = random.choice(responses)
        response = response.replace('{name}', username)
        
        return response
    
    async def send_reply(self, thread_id: str, message: str, username: str, msg_type: str):
        """Send reply with rate limiting"""
        
        # Check rate limit
        max_replies = self.config.get('max_replies', 50)
        if self.daily_stats['messages_sent'] >= max_replies:
            logger.warning(f"⏳ Daily message limit ({max_replies}) reached")
            return False
        
        try:
            # Random delay (30-90 seconds)
            delay = random.randint(30, 90)
            logger.info(f"⏳ Waiting {delay}s before replying to @{username}...")
            await asyncio.sleep(delay)
            
            # Send message
            self.client.direct_send(message, thread_ids=[thread_id])
            
            # Update stats
            self.daily_stats['messages_sent'] += 1
            if msg_type in ['flirty', 'romantic', 'compliment']:
                self.daily_stats['flirts_sent'] += 1
            
            # Track user
            self.replied_users[username] = {
                'time': datetime.now(),
                'message': message[:50]
            }
            
            logger.success(f"✅ Replied to @{username}")
            
            # Notify Telegram
            if self.telegram:
                await self.telegram.notify_reply(username, message)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send reply: {e}")
            return False
    
    async def auto_like(self):
        """Auto-like posts (if enabled)"""
        if not self.config.get('auto_like', True):
            return
        
        try:
            followers = self.client.user_followers(self.user_id, amount=10)
            
            for follower_id in list(followers.keys())[:3]:
                try:
                    medias = self.client.user_medias(int(follower_id), amount=2)
                    
                    for media in medias[:1]:
                        if not media.has_liked:
                            await asyncio.sleep(random.randint(20, 40))
                            self.client.media_like(media.id)
                            self.daily_stats['likes_given'] += 1
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Auto-like error: {e}")
    
    async def run(self):
        """Main bot loop"""
        self.is_running = True
        logger.info(f"🚀 Instagram bot started for @{self.username}")
        
        last_like_time = datetime.now()
        check_interval = self.config.get('check_interval', 60)
        
        while self.is_running:
            try:
                # Check messages
                new_messages = await self.check_messages()
                
                for msg in new_messages:
                    # Check if recently replied
                    if msg['username'] in self.replied_users:
                        last_reply = self.replied_users[msg['username']]['time']
                        if datetime.now() - last_reply < timedelta(hours=2):
                            continue
                    
                    # Generate and send response
                    msg_type = self.analyze_message(msg['text'])
                    response = self.generate_response(msg_type, msg['username'])
                    await self.send_reply(msg['thread_id'], response, msg['username'], msg_type)
                
                # Auto-like every 2 hours
                if datetime.now() - last_like_time > timedelta(hours=2):
                    await self.auto_like()
                    last_like_time = datetime.now()
                
                # Wait before next check
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"❌ Main loop error: {e}")
                await asyncio.sleep(300)
    
    def stop(self):
        """Stop the bot"""
        self.is_running = False
        logger.info(f"🛑 Instagram bot stopped")