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
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

SYSTEM_PROMPT = """You are OpenClaw 🦀, an elite AI assistant for Binance and crypto.
Help users with Binance features, crypto education, security basics, and product discovery.
Do not provide personalized financial advice or guaranteed profit claims.
Always encourage users to do their own research.
Respond in the same language as the user (Arabic or English).
Be friendly and helpful and concise.
"""

user_histories = {}

async def ask_gemini(user_id: int, text: str) -> str:
    if not GEMINI_API_KEY:
        return "⚠️ GEMINI_API_KEY مش مضاف في Variables."

    if user_id not in user_histories:
        user_histories[user_id] = []

    user_histories[user_id].append({
        "role": "user",
        "parts": [{"text": text}]
    })

    if len(user_histories[user_id]) > 10:
        user_histories[user_id] = user_histories[user_id][-10:]

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "contents": user_histories[user_id]
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, json=payload)

    logger.info(f"Gemini status: {response.status_code}")
    logger.info(f"Gemini raw response: {response.text}")

    if response.status_code != 200:
        return f"⚠️ Gemini API error: {response.status_code}"

    data = response.json()

    try:
        reply = data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        logger.error(f"Gemini parse error: {e}")
        return "⚠️ Gemini رجّع response غير متوقع. شوف الـ logs."

    user_histories[user_id].append({
        "role": "model",
        "parts": [{"text": reply}]
    })

    return reply

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"👋 أهلاً {name}!\n\n"
        "🦀 أنا OpenClaw — مساعد Binance و Crypto.\n\n"
        "اكتب /help للأوامر\n\n"
        "⚠️ للأغراض التعليمية فقط"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🦀 الأوامر:\n\n"
        "/start - الترحيب\n"
        "/help - الأوامر\n"
        "/about - عن البوت\n"
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
        "🤖 Powered by Gemini AI\n"
        "🌍 عربي وإنجليزي\n\n"
        "⚠️ للأغراض التعليمية فقط"
    )

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_histories[update.effective_user.id] = []
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
        "اسألني عن أي ميزة."
    )

async def crypto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 مصطلحات Crypto:\n\n"
        "🪙 BTC - Bitcoin\n"
        "💎 ETH - Ethereum\n"
        "🟡 BNB - Binance Coin\n"
        "💵 USDT - Tether\n"
        "🏦 DeFi - Decentralized Finance\n"
        "🐂 Bull Market - سوق صاعد\n"
        "🐻 Bear Market - سوق هابط"
    )

async def security_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔐 نصائح الأمان:\n\n"
        "✅ فعّل 2FA\n"
        "✅ فعّل Anti-Phishing Code\n"
        "✅ استخدم Withdrawal Whitelist\n"
        "✅ استخدم كلمة مرور قوية\n"
        "❌ لا تشارك API Keys\n"
        "❌ لا تصدق giveways أو الرسائل المزيفة"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    try:
        reply = await ask_gemini(user_id, user_text)
        await update.message.reply_text(reply)
    except Exception as e:
        logger.exception("handle_message failed")
        await update.message.reply_text(f"⚠️ حصل خطأ: {e}")

def main():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN missing")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

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
