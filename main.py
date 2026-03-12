#!/usr/bin/env python3
"""
Instagram-Telegram Flirt Bot
Main entry point with dynamic configuration
"""

import os
import sys
import asyncio
import threading
import json
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger
from flask import Flask, render_template_string, request, redirect, session
import secrets

# Load environment variables
load_dotenv()

# Import bot modules
from instagram_bot import InstagramBot
from telegram_bot import TelegramBot
from database import init_db, get_session, BotConfig

# Setup logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/bot.log",
    rotation="10 MB",
    retention="30 days",
    format="{time} | {level} | {message}"
)

# Flask app for web interface
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# HTML Template for Configuration
CONFIG_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Instagram Bot Configuration</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            border-radius: 20px 20px 0 0;
            padding: 30px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .header h1 {
            color: #333;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #666;
        }
        
        .config-form {
            background: white;
            padding: 30px;
            border-radius: 0 0 20px 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 600;
        }
        
        input, select, textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: all 0.3s;
        }
        
        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .help-text {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        
        .section-title {
            font-size: 18px;
            color: #667eea;
            margin: 30px 0 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            width: 100%;
            transition: transform 0.3s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .btn-secondary {
            background: #f0f0f0;
            color: #333;
            margin-top: 10px;
        }
        
        .status-box {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
        }
        
        .status-item {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .status-item:last-child {
            border-bottom: none;
        }
        
        .badge {
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
        }
        
        .badge-success {
            background: #d4edda;
            color: #155724;
        }
        
        .badge-warning {
            background: #fff3cd;
            color: #856404;
        }
        
        .flirt-message-item {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
        }
        
        .flirt-category {
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .add-message {
            margin-top: 20px;
            padding: 20px;
            background: #f0f4f8;
            border-radius: 8px;
        }
        
        @media (max-width: 768px) {
            .row {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Instagram Bot Configuration</h1>
            <p>Configure your Instagram auto-reply bot settings</p>
        </div>
        
        <div class="config-form">
            {% if message %}
            <div style="background: #d4edda; color: #155724; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                {{ message }}
            </div>
            {% endif %}
            
            {% if error %}
            <div style="background: #f8d7da; color: #721c24; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                {{ error }}
            </div>
            {% endif %}
            
            <form method="POST" action="/save-config">
                <h3 class="section-title">📱 Instagram Account</h3>
                
                <div class="row">
                    <div class="form-group">
                        <label>Instagram Username *</label>
                        <input type="text" name="instagram_username" value="{{ config.instagram_username }}" required placeholder="your_instagram">
                        <div class="help-text">Your Instagram username (without @)</div>
                    </div>
                    
                    <div class="form-group">
                        <label>Instagram Password *</label>
                        <input type="password" name="instagram_password" value="{{ config.instagram_password }}" required placeholder="••••••••">
                        <div class="help-text">Your Instagram password</div>
                    </div>
                </div>
                
                <h3 class="section-title">📱 Telegram Bot</h3>
                
                <div class="row">
                    <div class="form-group">
                        <label>Telegram Bot Token *</label>
                        <input type="text" name="telegram_token" value="{{ config.telegram_token }}" required placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz">
                        <div class="help-text">Get from @BotFather on Telegram</div>
                    </div>
                    
                    <div class="form-group">
                        <label>Telegram Bot Username</label>
                        <input type="text" name="telegram_username" value="{{ config.telegram_username }}" placeholder="myflirtbot">
                        <div class="help-text">Your bot's username (without @)</div>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>Your Telegram User ID *</label>
                    <input type="text" name="admin_user_id" value="{{ config.admin_user_id }}" required placeholder="123456789">
                    <div class="help-text">Get from @userinfobot on Telegram (only you can control the bot)</div>
                </div>
                
                <h3 class="section-title">⚙️ Bot Settings</h3>
                
                <div class="row">
                    <div class="form-group">
                        <label>Check Interval (seconds)</label>
                        <input type="number" name="check_interval" value="{{ config.check_interval or 60 }}" min="30" max="300">
                        <div class="help-text">How often to check for new messages (30-300s)</div>
                    </div>
                    
                    <div class="form-group">
                        <label>Max Messages Per Hour</label>
                        <input type="number" name="max_replies" value="{{ config.max_replies or 50 }}" min="10" max="100">
                        <div class="help-text">Safety limit to avoid Instagram ban</div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="form-group">
                        <label>Flirt Level</label>
                        <select name="flirt_level">
                            <option value="low" {% if config.flirt_level == 'low' %}selected{% endif %}>😊 Low - Friendly only</option>
                            <option value="moderate" {% if config.flirt_level == 'moderate' %}selected{% endif %}>💕 Moderate - Some flirting</option>
                            <option value="high" {% if config.flirt_level == 'high' %}selected{% endif %}>🔥 High - Very flirty</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>Auto Like Posts</label>
                        <select name="auto_like">
                            <option value="true" {% if config.auto_like %}selected{% endif %}>✅ Yes</option>
                            <option value="false" {% if not config.auto_like %}selected{% endif %}>❌ No</option>
                        </select>
                    </div>
                </div>
                
                <h3 class="section-title">💋 Flirt Messages</h3>
                
                <div class="status-box">
                    {% for category, messages in flirt_messages.items() %}
                    <div class="flirt-message-item">
                        <div class="flirt-category">{{ category|upper }}</div>
                        {% for msg in messages %}
                        <div style="padding: 5px 0; border-bottom: 1px dashed #e0e0e0;">
                            {{ msg }}
                        </div>
                        {% endfor %}
                    </div>
                    {% endfor %}
                </div>
                
                <div class="add-message">
                    <h4 style="margin-bottom: 15px;">Add New Flirt Message</h4>
                    <div class="row">
                        <div class="form-group">
                            <select name="new_message_category">
                                <option value="greeting">Greeting</option>
                                <option value="compliment">Compliment</option>
                                <option value="flirty">Flirty</option>
                                <option value="romantic">Romantic</option>
                                <option value="question">Question</option>
                                <option value="response">Response</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <input type="text" name="new_message" placeholder="Enter new flirt message...">
                        </div>
                    </div>
                </div>
                
                <button type="submit" name="action" value="save" class="btn">💾 Save Configuration</button>
                <button type="submit" name="action" value="save_and_start" class="btn btn-secondary">🚀 Save & Start Bot</button>
            </form>
            
            <div style="margin-top: 30px; text-align: center;">
                <a href="/status" style="color: #667eea; text-decoration: none;">View Bot Status →</a>
            </div>
        </div>
    </div>
</body>
</html>
"""

STATUS_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Bot Status - {{ username }}</title>
    <style>
        body { font-family: Arial; background: #f5f5f5; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; }
        .card { background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .status-online { color: green; font-weight: bold; }
        .status-offline { color: red; font-weight: bold; }
        .stat { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>🤖 Bot Status - @{{ username }}</h1>
            <div class="stat">
                <span>Status:</span>
                <span class="{% if is_running %}status-online{% else %}status-offline{% endif %}">
                    {% if is_running %}✅ ONLINE{% else %}❌ OFFLINE{% endif %}
                </span>
            </div>
            <div class="stat"><span>Started:</span> <span>{{ start_time }}</span></div>
            <div class="stat"><span>Uptime:</span> <span>{{ uptime }}</span></div>
        </div>
        
        <div class="card">
            <h2>📊 Today's Stats</h2>
            <div class="stat"><span>Messages Sent:</span> <span>{{ stats.messages_sent }}</span></div>
            <div class="stat"><span>Messages Received:</span> <span>{{ stats.messages_received }}</span></div>
            <div class="stat"><span>Flirts Sent:</span> <span>{{ stats.flirts_sent }}</span></div>
            <div class="stat"><span>Likes Given:</span> <span>{{ stats.likes_given }}</span></div>
            <div class="stat"><span>Users Interacted:</span> <span>{{ total_users }}</span></div>
        </div>
        
        <div class="card">
            <h2>⚙️ Configuration</h2>
            <div class="stat"><span>Check Interval:</span> <span>{{ config.check_interval }}s</span></div>
            <div class="stat"><span>Max Replies/Hour:</span> <span>{{ config.max_replies }}</span></div>
            <div class="stat"><span>Flirt Level:</span> <span>{{ config.flirt_level }}</span></div>
            <div class="stat"><span>Auto Like:</span> <span>{% if config.auto_like %}✅{% else %}❌{% endif %}</span></div>
        </div>
        
        <div style="text-align: center;">
            <a href="/" style="background: #667eea; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">⚙️ Configure</a>
        </div>
    </div>
</body>
</html>
"""

class BotManager:
    def __init__(self):
        self.instagram_bot = None
        self.telegram_bot = None
        self.is_running = False
        self.start_time = None
        self.config = {}
        self.load_config()
        
    def load_config(self):
        """Load configuration from database or file"""
        config_file = 'bot_config.json'
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                self.config = json.load(f)
        else:
            # Default config
            self.config = {
                'instagram_username': '',
                'instagram_password': '',
                'telegram_token': '',
                'telegram_username': '',
                'admin_user_id': '',
                'check_interval': 60,
                'max_replies': 50,
                'flirt_level': 'moderate',
                'auto_like': True
            }
    
    def save_config(self, new_config):
        """Save configuration to file"""
        self.config.update(new_config)
        with open('bot_config.json', 'w') as f:
            json.dump(self.config, f, indent=2)
        logger.info("✅ Configuration saved")
        
    def initialize(self):
        """Initialize both bots with current config"""
        try:
            if not all([self.config['instagram_username'], 
                       self.config['instagram_password'],
                       self.config['telegram_token'],
                       self.config['admin_user_id']]):
                logger.error("Missing required configuration!")
                return False
            
            # Initialize database
            init_db()
            
            # Convert admin user ID to list
            admin_ids = [int(self.config['admin_user_id'])]
            
            # Create bot instances
            self.instagram_bot = InstagramBot(
                self.config['instagram_username'], 
                self.config['instagram_password'],
                self.config
            )
            
            self.telegram_bot = TelegramBot(
                self.config['telegram_token'], 
                admin_ids, 
                self.instagram_bot,
                self.config.get('telegram_username', 'YourBot')
            )
            
            # Connect bots
            self.instagram_bot.set_telegram_controller(self.telegram_bot)
            
            logger.info(f"✅ Bot initialized for user: {self.config['instagram_username']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize: {e}")
            return False
    
    def run_instagram(self):
        """Run Instagram bot in async loop"""
        async def run():
            try:
                if await self.instagram_bot.login():
                    logger.info("✅ Instagram bot logged in")
                    await self.instagram_bot.run()
                else:
                    logger.error("❌ Instagram login failed")
            except Exception as e:
                logger.error(f"❌ Instagram bot error: {e}")
        
        asyncio.run(run())
    
    def run_telegram(self):
        """Run Telegram bot"""
        try:
            logger.info("✅ Starting Telegram bot")
            self.telegram_bot.run()
        except Exception as e:
            logger.error(f"❌ Telegram bot error: {e}")
    
    def start(self):
        """Start all bots"""
        if not self.initialize():
            logger.error("Failed to initialize bots")
            return
        
        self.start_time = datetime.now()
        self.is_running = True
        
        # Start Instagram bot in background
        instagram_thread = threading.Thread(target=self.run_instagram, daemon=True)
        instagram_thread.start()
        
        # Run Telegram bot in main thread
        try:
            self.run_telegram()
        except KeyboardInterrupt:
            logger.info("🛑 Bot stopped by user")
            self.is_running = False
            sys.exit(0)
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            self.is_running = False
            sys.exit(1)

# Global instance
bot_manager = BotManager()

@app.route('/')
def index():
    """Configuration page"""
    return render_template_string(
        CONFIG_HTML,
        config=bot_manager.config,
        flirt_messages=bot_manager.instagram_bot.flirt_messages if bot_manager.instagram_bot else {},
        message=request.args.get('message'),
        error=request.args.get('error')
    )

@app.route('/save-config', methods=['POST'])
def save_config():
    """Save configuration"""
    try:
        # Get form data
        new_config = {
            'instagram_username': request.form.get('instagram_username'),
            'instagram_password': request.form.get('instagram_password'),
            'telegram_token': request.form.get('telegram_token'),
            'telegram_username': request.form.get('telegram_username'),
            'admin_user_id': request.form.get('admin_user_id'),
            'check_interval': int(request.form.get('check_interval', 60)),
            'max_replies': int(request.form.get('max_replies', 50)),
            'flirt_level': request.form.get('flirt_level', 'moderate'),
            'auto_like': request.form.get('auto_like') == 'true'
        }
        
        # Add new flirt message if provided
        new_message = request.form.get('new_message')
        new_category = request.form.get('new_message_category')
        
        if new_message and new_category and bot_manager.instagram_bot:
            bot_manager.instagram_bot.add_flirt_message(new_category, new_message)
        
        # Save config
        bot_manager.save_config(new_config)
        
        action = request.form.get('action')
        if action == 'save_and_start':
            # Start bot in background
            threading.Thread(target=bot_manager.start, daemon=True).start()
            return redirect('/?message=Configuration saved and bot started!')
        
        return redirect('/?message=Configuration saved successfully!')
        
    except Exception as e:
        return redirect(f'/?error={str(e)}')

@app.route('/status')
def status():
    """Bot status page"""
    if not bot_manager.instagram_bot:
        return redirect('/?error=Bot not initialized')
    
    stats = bot_manager.instagram_bot.daily_stats
    total_users = len(bot_manager.instagram_bot.replied_users)
    
    # Calculate uptime
    if bot_manager.start_time:
        uptime_delta = datetime.now() - bot_manager.start_time
        hours = uptime_delta.seconds // 3600
        minutes = (uptime_delta.seconds % 3600) // 60
        uptime = f"{uptime_delta.days}d {hours}h {minutes}m"
    else:
        uptime = "Not started"
    
    return render_template_string(
        STATUS_HTML,
        username=bot_manager.config.get('instagram_username', 'Not set'),
        is_running=bot_manager.is_running,
        start_time=bot_manager.start_time.strftime('%Y-%m-%d %H:%M:%S') if bot_manager.start_time else 'Not started',
        uptime=uptime,
        stats=stats,
        total_users=total_users,
        config=bot_manager.config
    )

@app.route('/health')
def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "bot_running": bot_manager.is_running,
        "instagram_user": bot_manager.config.get('instagram_username'),
        "timestamp": datetime.now().isoformat()
    }

def run_flask():
    """Run Flask server"""
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def main():
    """Main function"""
    logger.info("=" * 50)
    logger.info("🚀 Starting Instagram-Telegram Flirt Bot")
    logger.info("=" * 50)
    
    # Start Flask in background
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info(f"✅ Web interface available at http://localhost:{os.getenv('PORT', 5000)}")
    
    # Check if config exists and auto-start if configured
    if os.path.exists('bot_config.json') and os.getenv('AUTO_START', 'false').lower() == 'true':
        logger.info("🔄 Auto-starting bot with saved configuration...")
        threading.Thread(target=bot_manager.start, daemon=True).start()
    
    # Keep main thread alive
    try:
        while True:
            import time
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    main()