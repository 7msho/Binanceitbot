import os
import logging
import httpx
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

SYSTEM_PROMPT = """You are OpenClaw, an AI assistant for Binance and crypto.
Help users with crypto and Binance questions.
Never give financial advice. Always say DYOR.
Respond in same language as user (Arabic or English)."""

user_histories = {}

async def ask_gemini(user_id, text):
    if user_id not in user_histories:
        user_histories[user_id] = []
    
    user_histories[user_id].append({"role": "user", "parts": [{"text": text}]})
    
    if len(user_histories[user_id]) > 10:
        user_histories[user_id] = user_histories[user_id][-10:]
    
    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": user_histories[user_id]
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(GEMINI_URL, json=payload)
        data = response.json()
    
    reply = data["candidates"][0]["content"]["parts"][0]["text"]
    user_histories[user_id].append({"role": "model", "parts": [{"text": reply}]})
    return reply

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"👋 أهلاً {name}!\n\n"
        "🦀 أنا OpenClaw — مساعدك لكل حاجة Binance وCrypto!\n\n"
        "اسألني أي حاجة أو اكتب /help 🚀\n\n"
        "⚠️ للأغراض التعليمية فقط"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🦀 الأوامر المتاحة:\n\n"
        "/start - رسالة الترحيب\n"
        "/help - قائمة الأوامر\n"
        "/about - معلومات عن البوت\n"
        "/clear - مسح المحادثة\n"
        "/binance - مميزات Binance\n"
        "/crypto - مصطلحات Crypto\n"
        "/security - نصائح الأمان\n\n"
        "💬 أو اكتب سؤالك مباشرة!"
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🦀 OpenClaw AI Assistant\n\n"
        "Built for Binance OpenClaw AI Challenge 2026 🏆\n\n"
        "🤖 مدعوم بـ Google Gemini AI\n"
        "🌍 يرد بالعربي والإنجليزي\n\n"
        "⚠️ للأغراض التعليمية فقط"
    )

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_histories[user_id] = []
    await update.message.reply_text("✅ تم مسح المحادثة!")

async def binance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏦 مميزات Binance:\n\n"
        "📈 Spot Trading\n"
        "⚡ Futures\n"
        "💰 Binance Earn\n"
        "🔄 P2P\n"
        "🚀 Launchpad\n"
        "🌐 Web3 Wallet\n\n"
        "اسألني عن أي ميزة! 🦀"
    )

async def crypto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 مصطلحات أساسية:\n\n"
        "🪙 BTC - Bitcoin\n"
        "💎 ETH - Ethereum\n"
        "🟡 BNB - Binance Coin\n"
        "💵 USDT - Tether\n"
        "🏦 DeFi - تمويل لامركزي\n"
        "🐂 Bull Market - سوق صاعد\n"
        "🐻 Bear Market - سوق هابط\n\n"
        "اسألني عن أي مصطلح! 🦀"
    )

async def security_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔐 نصائح الأمان:\n\n"
        "✅ فعّل 2FA\n"
        "✅ استخدم Anti-Phishing Code\n"
        "✅ فعّل Withdrawal Whitelist\n"
        "✅ كلمة مرور قوية\n"
        "❌ لا تشارك API Keys\n"
        "❌ لا تصدق Giveaways\n\n"
        "🦀 أمانك أهم من أي ربح!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        reply = await ask_gemini(user_id, user_text)
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("⚠️ حدث خطأ، حاول تاني!")

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN missing")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CommandHandler("binance", binance_command))
    app.add_handler(CommandHandler("crypto", crypto_command))
    app.add_handler(CommandHandler("security", security_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🦀 OpenClaw Bot running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
