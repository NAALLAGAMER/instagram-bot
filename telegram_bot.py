"""
Telegram Controller for Instagram Bot
Dynamic configuration via Telegram
"""

import os
import asyncio
from datetime import datetime
from typing import List
from loguru import logger
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler

# States
MAIN_MENU, STATS, USERS, SETTINGS, ADD_FLIRT, REMOVE_FLIRT = range(6)

class TelegramBot:
    def __init__(self, token: str, admin_ids: List[int], instagram_bot, bot_username: str):
        self.token = token
        self.admin_ids = admin_ids
        self.instagram_bot = instagram_bot
        self.bot_username = bot_username
        self.app = None
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command - only for owner"""
        user = update.effective_user
        
        if user.id not in self.admin_ids:
            await update.message.reply_text("⛔ Unauthorized access!")
            return ConversationHandler.END
        
        # Get Instagram username from config
        instagram_user = self.instagram_bot.username if self.instagram_bot else "Not set"
        
        keyboard = [
            [InlineKeyboardButton("📊 Statistics", callback_data="stats")],
            [InlineKeyboardButton("👥 Recent Users", callback_data="users")],
            [InlineKeyboardButton("💋 Flirt Messages", callback_data="flirt_messages")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
            [InlineKeyboardButton("▶️ Start Bot", callback_data="start_bot")],
            [InlineKeyboardButton("⏸️ Stop Bot", callback_data="stop_bot")],
            [InlineKeyboardButton("📈 Daily Report", callback_data="daily")],
            [InlineKeyboardButton("🔄 Update Config", callback_data="update_config")]
        ]
        
        status = "✅ Running" if self.instagram_bot.is_running else "❌ Stopped"
        
        await update.message.reply_text(
            f"🤖 *Instagram Bot Controller*\n\n"
            f"👤 *Owner:* {user.first_name}\n"
            f"📱 *Instagram:* @{instagram_user}\n"
            f"🤖 *Bot Status:* {status}\n\n"
            f"*Choose an option:*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return MAIN_MENU
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button presses"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "stats":
            await self.show_stats(query)
        elif query.data == "users":
            await self.show_users(query)
        elif query.data == "flirt_messages":
            await self.show_flirt_messages(query, context)
        elif query.data == "settings":
            await self.show_settings(query)
        elif query.data == "start_bot":
            await self.start_bot(query)
        elif query.data == "stop_bot":
            await self.stop_bot(query)
        elif query.data == "daily":
            await self.daily_report(query)
        elif query.data == "update_config":
            await self.update_config_prompt(query)
        elif query.data.startswith("add_flirt_"):
            await self.prompt_add_flirt(query, query.data.replace("add_flirt_", ""))
        elif query.data.startswith("remove_flirt_"):
            await self.show_flirt_to_remove(query, query.data.replace("remove_flirt_", ""))
        elif query.data == "back":
            await self.back_to_main(query)
    
    async def show_stats(self, query):
        """Show bot statistics"""
        stats = self.instagram_bot.daily_stats
        
        text = (
            f"📊 *Bot Statistics*\n\n"
            f"*Today's Activity:*\n"
            f"📨 Messages Sent: {stats['messages_sent']}\n"
            f"📥 Messages Received: {stats['messages_received']}\n"
            f"❤️ Likes Given: {stats['likes_given']}\n"
            f"💋 Flirts Sent: {stats['flirts_sent']}\n\n"
            f"*Total Users:* {len(self.instagram_bot.replied_users)}\n"
            f"*Bot Status:* {'✅ Running' if self.instagram_bot.is_running else '❌ Stopped'}"
        )
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back")]]
        await query.edit_message_text(text, parse_mode='Markdown', 
                                     reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def show_users(self, query):
        """Show recent users"""
        recent_users = list(self.instagram_bot.replied_users.items())[-10:]
        
        text = f"👥 *Recent Users*\n\n"
        
        if recent_users:
            for username, data in reversed(recent_users):
                time_str = data['time'].strftime('%H:%M %d/%m')
                text += f"• @{username}\n  🕐 {time_str}\n  💬 {data['message']}\n\n"
        else:
            text += "No users yet"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back")]]
        await query.edit_message_text(text, parse_mode='Markdown',
                                     reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def show_flirt_messages(self, query, context):
        """Show flirt messages by category"""
        keyboard = []
        
        for category in self.instagram_bot.flirt_messages.keys():
            count = len(self.instagram_bot.flirt_messages[category])
            keyboard.append([
                InlineKeyboardButton(
                    f"{category.upper()} ({count})", 
                    callback_data=f"view_flirt_{category}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("➕ Add New", callback_data="add_flirt_prompt"),
            InlineKeyboardButton("➖ Remove", callback_data="remove_flirt_prompt")
        ])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
        
        await query.edit_message_text(
            "💋 *Flirt Messages*\n\nSelect a category to view:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # Store in context for next steps
        context.user_data['flirt_action'] = 'view'
    
    async def prompt_add_flirt(self, query, category):
        """Prompt to add new flirt message"""
        await query.edit_message_text(
            f"✏️ *Add New {category.upper()} Message*\n\n"
            f"Send me the new message you want to add.\n"
            f"Use {{name}} for username placeholder.\n\n"
            f"Example: Hey {{name}}! You're awesome! ✨",
            parse_mode='Markdown'
        )
        
        # Store category in context
        query.get_bot().user_data[query.from_user.id] = {'adding_flirt': category}
    
    async def show_flirt_to_remove(self, query, category):
        """Show messages to remove"""
        messages = self.instagram_bot.flirt_messages.get(category, [])
        
        text = f"🗑️ *Remove {category.upper()} Messages*\n\n"
        
        keyboard = []
        for i, msg in enumerate(messages[:10]):  # Show first 10
            short_msg = msg[:30] + "..." if len(msg) > 30 else msg
            keyboard.append([
                InlineKeyboardButton(
                    f"{i+1}. {short_msg}", 
                    callback_data=f"delete_flirt_{category}_{i}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="flirt_messages")])
        
        await query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_settings(self, query):
        """Show current settings"""
        config = self.instagram_bot.config
        
        text = (
            f"⚙️ *Current Settings*\n\n"
            f"📱 Instagram: @{config.get('instagram_username', 'Not set')}\n"
            f"⏱️ Check Interval: {config.get('check_interval', 60)}s\n"
            f"📨 Max Replies/Hour: {config.get('max_replies', 50)}\n"
            f"💋 Flirt Level: {config.get('flirt_level', 'moderate')}\n"
            f"❤️ Auto Like: {'✅' if config.get('auto_like', True) else '❌'}\n\n"
            f"*To change settings, use the web interface at:*\n"
            f"http://localhost:{os.getenv('PORT', 5000)}"
        )
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back")]]
        await query.edit_message_text(text, parse_mode='Markdown',
                                     reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def update_config_prompt(self, query):
        """Prompt to update config via web"""
        text = (
            f"🔄 *Update Configuration*\n\n"
            f"To update your bot configuration:\n\n"
            f"1. Open this URL in your browser:\n"
            f"`http://localhost:{os.getenv('PORT', 5000)}`\n\n"
            f"2. Update your Instagram username, password, and settings\n"
            f"3. Click 'Save & Start Bot'\n\n"
            f"After saving, the bot will restart with new settings."
        )
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back")]]
        await query.edit_message_text(text, parse_mode='Markdown',
                                     reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def start_bot(self, query):
        """Start Instagram bot"""
        if not self.instagram_bot.is_running:
            self.instagram_bot.is_running = True
            text = f"✅ *Bot started for @{self.instagram_bot.username}!*"
        else:
            text = "⚠️ *Bot is already running*"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back")]]
        await query.edit_message_text(text, parse_mode='Markdown',
                                     reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def stop_bot(self, query):
        """Stop Instagram bot"""
        if self.instagram_bot.is_running:
            self.instagram_bot.is_running = False
            text = "⏸️ *Bot stopped*"
        else:
            text = "⚠️ *Bot is already stopped*"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back")]]
        await query.edit_message_text(text, parse_mode='Markdown',
                                     reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def daily_report(self, query):
        """Show daily report"""
        stats = self.instagram_bot.daily_stats
        
        text = (
            f"📈 *Daily Report - {datetime.now().strftime('%d/%m/%Y')}*\n\n"
            f"📨 Messages Sent: {stats['messages_sent']}\n"
            f"📥 Messages Received: {stats['messages_received']}\n"
            f"💋 Flirts Sent: {stats['flirts_sent']}\n"
            f"❤️ Likes Given: {stats['likes_given']}\n"
            f"👥 Users Today: {stats['messages_received']}\n\n"
            f"*Total All Time:* {len(self.instagram_bot.replied_users)} users"
        )
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back")]]
        await query.edit_message_text(text, parse_mode='Markdown',
                                     reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def back_to_main(self, query):
        """Return to main menu"""
        instagram_user = self.instagram_bot.username if self.instagram_bot else "Not set"
        status = "✅ Running" if self.instagram_bot.is_running else "❌ Stopped"
        
        keyboard = [
            [InlineKeyboardButton("📊 Statistics", callback_data="stats")],
            [InlineKeyboardButton("👥 Recent Users", callback_data="users")],
            [InlineKeyboardButton("💋 Flirt Messages", callback_data="flirt_messages")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
            [InlineKeyboardButton("▶️ Start Bot", callback_data="start_bot")],
            [InlineKeyboardButton("⏸️ Stop Bot", callback_data="stop_bot")],
            [InlineKeyboardButton("📈 Daily Report", callback_data="daily")],
            [InlineKeyboardButton("🔄 Update Config", callback_data="update_config")]
        ]
        
        await query.edit_message_text(
            f"🤖 *Instagram Bot Controller*\n\n"
            f"📱 *Instagram:* @{instagram_user}\n"
            f"🤖 *Status:* {status}\n\n"
            f"*Choose an option:*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages (for adding flirt messages)"""
        user = update.effective_user
        
        if user.id not in self.admin_ids:
            return
        
        # Check if adding flirt message
        user_data = context.bot.user_data.get(user.id, {})
        if 'adding_flirt' in user_data:
            category = user_data['adding_flirt']
            message = update.message.text
            
            # Add message
            self.instagram_bot.add_flirt_message(category, message)
            
            await update.message.reply_text(
                f"✅ Added new {category} message!\n\n"
                f"Message: {message}\n\n"
                f"Use /start to return to menu."
            )
            
            # Clear context
            del context.bot.user_data[user.id]['adding_flirt']
    
    async def notify_admin(self, message: str):
        """Send notification to admin"""
        for admin_id in self.admin_ids:
            try:
                await self.app.bot.send_message(chat_id=admin_id, text=message, parse_mode='Markdown')
            except:
                pass
    
    async def notify_new_message(self, username: str, message: str):
        """Notify admin of new message"""
        for admin_id in self.admin_ids:
            try:
                await self.app.bot.send_message(
                    chat_id=admin_id,
                    text=f"📥 *New Message*\n\nFrom: @{username}\nMessage: {message[:100]}...",
                    parse_mode='Markdown'
                )
            except:
                pass
    
    async def notify_reply(self, username: str, reply: str):
        """Notify admin of reply sent"""
        for admin_id in self.admin_ids:
            try:
                await self.app.bot.send_message(
                    chat_id=admin_id,
                    text=f"📤 *Auto-Reply Sent*\n\nTo: @{username}\nReply: {reply[:100]}...",
                    parse_mode='Markdown'
                )
            except:
                pass
    
    def run(self):
        """Run the Telegram bot"""
        self.app = Application.builder().token(self.token).build()
        
        # Add handlers
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CallbackQueryHandler(self.button_handler))
        self.app.add_handler(CommandHandler("flirt", self.start))  # Alias for start
        self.app.add_handler(CommandHandler("menu", self.start))   # Alias for start
        
        # Handle text messages
        self.app.add_handler(CommandHandler("help", self.start))
        
        # Start bot
        logger.info("✅ Telegram bot started")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)