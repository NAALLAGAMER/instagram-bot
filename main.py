#!/usr/bin/env python3
"""
Instagram-Telegram Flirt Bot - Main Entry Point with Web Configuration
"""

import os
import sys
import asyncio
import threading
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from loguru import logger
import secrets

# Import bot modules
from instagram_bot import InstagramBot
from telegram_bot import TelegramBot
from database import init_db
from config_manager import ConfigManager

# Initialize Flask app
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Initialize config manager
config_manager = ConfigManager()

# Global bot manager instance
class BotManager:
    def __init__(self):
        self.instagram_bot = None
        self.telegram_bot = None
        self.is_running = False
        self.start_time = None
        self.bot_thread = None
        
    def initialize_from_config(self, config):
        """Initialize bots from config dictionary"""
        try:
            # Get credentials from config
            instagram_username = config.get('instagram_username')
            instagram_password = config.get('instagram_password')
            telegram_token = config.get('telegram_token')
            admin_ids = [int(config.get('admin_user_id'))] if config.get('admin_user_id') else []
            
            if not all([instagram_username, instagram_password, telegram_token, admin_ids]):
                logger.error("❌ Missing required configuration!")
                return False
            
            # Initialize database
            init_db()
            
            # Create bot instances
            self.instagram_bot = InstagramBot(instagram_username, instagram_password, config)
            self.telegram_bot = TelegramBot(telegram_token, admin_ids, self.instagram_bot)
            
            # Connect bots
            self.instagram_bot.set_telegram_controller(self.telegram_bot)
            
            logger.info(f"✅ Bot initialized for Instagram user: @{instagram_username}")
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
    
    def start_bot(self):
        """Start the bot in background thread"""
        if self.bot_thread and self.bot_thread.is_alive():
            logger.warning("Bot already running")
            return False
        
        self.bot_thread = threading.Thread(target=self._run_bot, daemon=True)
        self.bot_thread.start()
        self.is_running = True
        self.start_time = datetime.now()
        return True
    
    def _run_bot(self):
        """Internal method to run bot"""
        try:
            self.run_instagram()
        except Exception as e:
            logger.error(f"Bot error: {e}")
    
    def stop_bot(self):
        """Stop the bot"""
        if self.instagram_bot:
            self.instagram_bot.is_running = False
        self.is_running = False
        logger.info("Bot stopped")

# Global bot manager
bot_manager = BotManager()

# Flask Routes
@app.route('/')
def index():
    """Main configuration page"""
    config = config_manager.get_config()
    return render_template('index.html', config=config, bot_status=bot_manager.is_running)

@app.route('/save-config', methods=['POST'])
def save_config():
    """Save configuration from web form"""
    try:
        # Get form data
        config = {
            'instagram_username': request.form.get('instagram_username'),
            'instagram_password': request.form.get('instagram_password'),
            'telegram_token': request.form.get('telegram_token'),
            'telegram_bot_username': request.form.get('telegram_bot_username'),
            'admin_user_id': request.form.get('admin_user_id'),
            'check_interval': int(request.form.get('check_interval', 60)),
            'max_replies_per_hour': int(request.form.get('max_replies_per_hour', 50)),
            'flirt_level': request.form.get('flirt_level', 'moderate'),
            'auto_like': request.form.get('auto_like') == 'on'
        }
        
        # Validate required fields
        if not all([config['instagram_username'], config['instagram_password'], 
                   config['telegram_token'], config['admin_user_id']]):
            flash('Please fill in all required fields!', 'error')
            return redirect(url_for('index'))
        
        # Save config
        config_manager.save_config(config)
        
        # Initialize bot with new config
        if bot_manager.initialize_from_config(config):
            flash('Configuration saved successfully!', 'success')
        else:
            flash('Failed to initialize bot with configuration', 'error')
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/start-bot', methods=['POST'])
def start_bot():
    """Start the bot"""
    if bot_manager.start_bot():
        flash('Bot started successfully!', 'success')
    else:
        flash('Bot is already running or failed to start', 'error')
    return redirect(url_for('index'))

@app.route('/stop-bot', methods=['POST'])
def stop_bot():
    """Stop the bot"""
    bot_manager.stop_bot()
    flash('Bot stopped', 'info')
    return redirect(url_for('index'))

@app.route('/status')
def status():
    """Get bot status as JSON"""
    if bot_manager.instagram_bot:
        return {
            'running': bot_manager.is_running,
            'instagram_user': bot_manager.instagram_bot.username,
            'stats': bot_manager.instagram_bot.daily_stats,
            'users_count': len(bot_manager.instagram_bot.replied_users),
            'start_time': bot_manager.start_time.isoformat() if bot_manager.start_time else None
        }
    return {'running': False}

def run_flask():
    """Run Flask app"""
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
    logger.info(f"✅ Web interface available at http://localhost:{os.environ.get('PORT', 5000)}")
    
    # Try to load existing config
    config = config_manager.get_config()
    if config.get('instagram_username'):
        logger.info("📋 Found existing configuration")
        if bot_manager.initialize_from_config(config):
            logger.info("✅ Bot initialized with existing config")
    
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