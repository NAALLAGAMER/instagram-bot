"""
Telegram Bot Module - Controls Instagram bot
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from loguru import logger

class TelegramBot:
    def __init__(self, token: str, admin_ids: list, instagram_bot):
        self.token = token
        self.admin_ids = admin_ids
        self.instagram_bot = instagram_bot
        self.app = None
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command"""
        user = update.effective_user
        
        if user.id not in self.admin_ids:
            await update.message.reply_text("⛔ Unauthorized!")
            return
        
        status = "✅ Running" if self.instagram_bot.is_running else "❌ Stopped"
        
        keyboard = [
            [InlineKeyboardButton("📊 Stats", callback_data="stats")],
            [InlineKeyboardButton("▶️ Start", callback_data="start")],
            [InlineKeyboardButton("⏸️ Stop", callback_data="stop")],
        ]
        
        await update.message.reply_text(
            f"🤖 *Bot Controller*\n\n"
            f"Status: {status}\n"
            f"Instagram: @{self.instagram_bot.username}",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle buttons"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "stats":
            stats = self.instagram_bot.daily_stats
            text = f"📊 Stats:\nSent: {stats['messages_sent']}\nReceived: {stats['messages_received']}"
            await query.edit_message_text(text)
        elif query.data == "start":
            self.instagram_bot.is_running = True
            await query.edit_message_text("✅ Bot started")
        elif query.data == "stop":
            self.instagram_bot.is_running = False
            await query.edit_message_text("⏸️ Bot stopped")
    
    async def notify_admin(self, message: str):
        """Notify admin"""
        for admin_id in self.admin_ids:
            try:
                await self.app.bot.send_message(admin_id, message, parse_mode='Markdown')
            except:
                pass
    
    async def notify_new_message(self, username: str, msg: str):
        """Notify new message"""
        await self.notify_admin(f"📥 New from @{username}: {msg[:50]}...")
    
    async def notify_reply(self, username: str, reply: str):
        """Notify reply sent"""
        await self.notify_admin(f"📤 Reply to @{username}: {reply[:50]}...")
    
    def run(self):
        """Run bot"""
        self.app = Application.builder().token(self.token).build()
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CallbackQueryHandler(self.button_handler))
        logger.info("✅ Telegram bot started")
        self.app.run_polling()