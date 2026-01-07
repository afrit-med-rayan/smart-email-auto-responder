import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8387861948:AAHf6istUi0iDZm98hM-4Sea5abufv90kgc")

def load_drafts():
    """Load pending drafts from JSON file"""
    try:
        with open("data/pending_drafts.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot online!\n\n"
        "Use /draft <email_id> to see a draft.\n"
        "Use /list to see all available drafts."
    )

async def list_drafts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    drafts = load_drafts()
    if not drafts:
        await update.message.reply_text("No drafts available. Run main.py first to generate drafts.")
        return
    
    draft_list = "\n".join([f"• Email ID: {email_id}" for email_id in drafts.keys()])
    await update.message.reply_text(f"📧 Available drafts:\n\n{draft_list}\n\nUse /draft <email_id> to view a draft.")

async def send_draft(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /draft <email_id>")
        return

    email_id = context.args[0]
    drafts = load_drafts()  # Reload from file
    draft_obj = drafts.get(email_id)

    if not draft_obj:
        await update.message.reply_text(f"❌ No draft found for email ID: {email_id}\n\nUse /list to see available drafts.")
        return

    # Store the current draft context for this user
    context.user_data['current_draft_id'] = email_id
    
    await update.message.reply_text(
        f"📧 Draft for Email ID {email_id}:\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{draft_obj['draft']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        "Reply with:\n"
        "• 'send' - to approve and send\n"
        "• 'modify' - to request changes\n"
        "• 'ignore' - to skip this email"
    )

async def handle_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user responses like send, modify, ignore"""
    text = update.message.text.lower().strip()
    
    # Check if user has a current draft context
    current_draft_id = context.user_data.get('current_draft_id')
    
    if text in ['send', 'approve', 'yes']:
        if current_draft_id:
            await update.message.reply_text(
                f"✅ Draft for email {current_draft_id} approved!\n\n"
                "(In production, this would send the email)"
            )
            context.user_data['current_draft_id'] = None
        else:
            await update.message.reply_text("No active draft. Use /draft <email_id> first.")
    
    elif text in ['modify', 'edit', 'change']:
        if current_draft_id:
            await update.message.reply_text(
                f"✏️ Modification requested for email {current_draft_id}\n\n"
                "(In production, this would allow editing)"
            )
            context.user_data['current_draft_id'] = None
        else:
            await update.message.reply_text("No active draft. Use /draft <email_id> first.")
    
    elif text in ['ignore', 'skip', 'no']:
        if current_draft_id:
            await update.message.reply_text(f"🚫 Draft for email {current_draft_id} ignored.")
            context.user_data['current_draft_id'] = None
        else:
            await update.message.reply_text("No active draft. Use /draft <email_id> first.")
    
    else:
        # Check if user is trying to use draft without slash
        if text.startswith('draft '):
            await update.message.reply_text(
                "💡 Tip: Use /draft <email_id> (with a slash)\n\n"
                "Example: /draft 1"
            )
        else:
            await update.message.reply_text(
                "❓ Unknown command\n\n"
                "Available commands:\n"
                "• /start - Show welcome message\n"
                "• /list - List all drafts\n"
                "• /draft <email_id> - View a specific draft\n\n"
                "Or reply with: send / modify / ignore"
            )

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_drafts))
    app.add_handler(CommandHandler("draft", send_draft))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_response))

    print("🤖 Telegram bot running…")
    app.run_polling()
