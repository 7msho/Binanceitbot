import os
import logging
from google import genai
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

SYSTEM_PROMPT = """You are OpenClaw 🦀, an elite AI assistant for Binance and crypto.
Help users with Binance features, crypto education, security basics, and product discovery.
Do not provide personalized financial advice or guaranteed profit claims.
Always encourage users to do their own research.
Respond in the same language as the user (Arabic or English).
Be friendly, helpful, and concise.
"""

user_histories = {}

client = genai.Client(api_key=GEMINI_API_KEY)

async def ask_gemini(user_id: int, text: str) -> str:
    if not GEMINI_API_KEY:
        return "⚠️ GEMINI_API_KEY missing"

    if user_id not in user_histories:
        user_histories[user_id] = []

    user_histories[user_id].append(f"User: {text}")

    if len(user_histories[user_id]) > 10:
        user_histories[user_id] = user_histories[user_id][-10:]

    history_text = "\n".join(user_histories[user_id])

    full_prompt = f"""{SYSTEM_PROMPT}

Conversation history:
{history_text}

Current user message:
{text}
"""

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=full_prompt
        )

        reply = response.text if response.text else "⚠️ مفيش رد واضح من Gemini."

        user_histories[user_id].append(f"Assistant: {reply}")
        return reply

    except Exception as e:
        logger.exception("Gemini SDK error")
        return f"⚠️ Gemini error: {e}"

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
        "🤖 Powered by Google GenAI SDK\n"
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
        "❌ لا تصدق الرسائل أو الروابط المزيفة"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    reply = await ask_gemini(user_id, user_text)
    await update.message.reply_text(reply)

def main():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN missing")

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY missing")

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
