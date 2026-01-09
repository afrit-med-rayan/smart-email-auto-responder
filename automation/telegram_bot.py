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

def save_drafts(drafts):
    """Save drafts dictionary to JSON file"""
    with open("data/pending_drafts.json", "w", encoding="utf-8") as f:
        json.dump(drafts, f, indent=2, ensure_ascii=False)

def remove_draft(email_id):
    """Remove a specific draft from the JSON file"""
    drafts = load_drafts()
    if email_id in drafts:
        del drafts[email_id]
        save_drafts(drafts)
        return True
    return False

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
    text = update.message.text.strip()
    text_lower = text.lower()
    
    # Check if user is awaiting modification input
    if context.user_data.get('awaiting_modification'):
        email_id = context.user_data.get('current_draft_id')
        if email_id:
            # Load drafts and update the specific draft
            drafts = load_drafts()
            if email_id in drafts:
                drafts[email_id]['draft'] = text
                save_drafts(drafts)
                
                # Clear modification state
                context.user_data['awaiting_modification'] = False
                
                # Show updated draft for re-approval
                await update.message.reply_text(
                    f"✅ Draft updated for Email ID {email_id}:\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"{text}\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n\n"
                    "Reply with:\n"
                    "• 'send' - to approve and send\n"
                    "• 'modify' - to request changes\n"
                    "• 'ignore' - to skip this email"
                )
            else:
                await update.message.reply_text(f"❌ Draft {email_id} no longer exists.")
                context.user_data['awaiting_modification'] = False
                context.user_data['current_draft_id'] = None
        return
    
    # Check if user has a current draft context
    current_draft_id = context.user_data.get('current_draft_id')
    
    if text_lower in ['send', 'approve', 'yes']:
        if current_draft_id:
            # Remove draft from pending queue
            if remove_draft(current_draft_id):
                await update.message.reply_text(
                    f"✅ Email sent!\n\n"
                    f"Draft for email {current_draft_id} has been approved and sent.\n"
                    "(Simulated mode - in production, this would send via Gmail)"
                )
            else:
                await update.message.reply_text(f"❌ Draft {current_draft_id} not found.")
            
            context.user_data['current_draft_id'] = None
        else:
            await update.message.reply_text("No active draft. Use /draft <email_id> first.")
    
    elif text_lower in ['modify', 'edit', 'change']:
        if current_draft_id:
            # Set state to await modification
            context.user_data['awaiting_modification'] = True
            await update.message.reply_text(
                f"✏️ Okay, send your modified draft:\n\n"
                "Type your new draft text and send it."
            )
        else:
            await update.message.reply_text("No active draft. Use /draft <email_id> first.")
    
    elif text_lower in ['ignore', 'skip', 'no']:
        if current_draft_id:
            # Remove draft from pending queue
            if remove_draft(current_draft_id):
                await update.message.reply_text(
                    f"🚫 Draft for email {current_draft_id} ignored and removed from queue."
                )
            else:
                await update.message.reply_text(f"❌ Draft {current_draft_id} not found.")
            
            context.user_data['current_draft_id'] = None
        else:
            await update.message.reply_text("No active draft. Use /draft <email_id> first.")
    
    else:
        # Check if user is trying to use draft without slash
        if text_lower.startswith('draft '):
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
