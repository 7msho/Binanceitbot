import os
import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)
import anthropic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are OpenClaw 🦀, an elite AI assistant built for the Binance ecosystem.
You help ALL users navigate Binance with confidence.
- Explain crypto concepts simply
- Help with Binance features
- Security best practices
- Never give financial advice
- Always say DYOR
- Respond in same language as user (Arabic or English)
- Use *bold* and bullet points for Telegram"""

user_histories = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً! أنا *OpenClaw* 🦀\nمساعدك الذكي لكل حاجة Binance!\n\nاسألني أي حاجة عن Crypto أو Binance 🚀\n\n_⚠️ للأغراض التعليمية فقط - مش نصيحة مالية_",
        parse_mode="Markdown"
    )

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_histories[update.effective_user.id] = []
    await update.message.reply_text("✅ تم مسح المحادثة!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    if user_id not in user_histories:
        user_histories[user_id] = []

    user_histories[user_id].append({"role": "user", "content": user_text})

    if len(user_histories[user_id]) > 10:
        user_histories[user_id] = user_histories[user_id][-10:]

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=user_histories[user_id]
        )
        reply = response.content[0].text
        user_histories[user_id].append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("⚠️ حدث خطأ، حاول تاني!")

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN مش موجود في Variables")
    
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("🦀 OpenClaw Bot running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
