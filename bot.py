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

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY missing")

client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """You are OpenClaw 🦀, an elite AI assistant for Binance and crypto.
Help users with Binance products, crypto education, risk explanations, market concepts, security tips, and trading tools.
Never promise profits.
Never give guaranteed financial advice.
Always remind users to do their own research (DYOR).
Respond in the same language as the user (Arabic or English).
Be friendly, clear, and useful.
Keep answers practical and short unless the user asks for more detail.
"""

user_histories = {}

def build_contents(user_id: int, user_text: str):
    history = user_histories.get(user_id, [])
    history.append(f"User: {user_text}")

    if len(history) > 12:
        history = history[-12:]

    user_histories[user_id] = history

    conversation = "\n".join(history)
    return f"{SYSTEM_PROMPT}\n\nConversation:\n{conversation}\n\nAssistant:"

async def ask_gemini(user_id: int, text: str) -> str:
    prompt = build_contents(user_id, text)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    reply = response.text if response.text else "⚠️ مفيش رد من Gemini."
    user_histories[user_id].append(f"Assistant: {reply}")
    return reply

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name or "friend"
    await update.message.reply_text(
        f"👋 أهلاً {name}!\n\n"
        f"🦀 أنا OpenClaw — مساعد Binance & Crypto\n\n"
        f"اكتب /help عشان تشوف الأوامر.\n\n"
        f"⚠️ Educational only — DYOR"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🦀 الأوامر:\n\n"
        "/start - بداية\n"
        "/help - الأوامر\n"
        "/about - عن البوت\n"
        "/clear - مسح المحادثة\n"
        "/binance - خدمات Binance\n"
        "/crypto - مصطلحات الكريبتو\n"
        "/security - نصائح الأمان\n\n"
        "💬 أو ابعت سؤالك مباشرة"
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🦀 OpenClaw AI Assistant\n\n"
        "Built for Binance OpenClaw AI Challenge 2026 🏆\n"
        "Powered by Google Gemini\n"
        "Supports Arabic & English\n\n"
        "⚠️ For educational purposes only"
    )

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_histories[update.effective_user.id] = []
    await update.message.reply_text("✅ تم مسح المحادثة.")

async def binance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏦 Binance features:\n\n"
        "📈 Spot Trading\n"
        "⚡ Futures\n"
        "💰 Earn\n"
        "🔄 P2P\n"
        "🚀 Launchpad\n"
        "🌐 Web3 Wallet\n\n"
        "اسألني عن أي واحدة منهم 🦀"
    )

async def crypto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 مصطلحات سريعة:\n\n"
        "BTC = Bitcoin\n"
        "ETH = Ethereum\n"
        "BNB = Binance Coin\n"
        "USDT = Tether\n"
        "Bull Market = سوق صاعد\n"
        "Bear Market = سوق هابط\n\n"
        "ابعتلي أي مصطلح وأنا أشرحه"
    )

async def security_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔐 نصائح الأمان:\n\n"
        "✅ فعل 2FA\n"
        "✅ فعل Anti-Phishing Code\n"
        "✅ استخدم Password قوي\n"
        "✅ راجع الروابط كويس\n"
        "❌ ما تشاركش API Keys\n"
        "❌ ما تصدقش giveaways الوهمية"
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
        logger.exception("Gemini error")
        await update.message.reply_text(f"⚠️ Gemini error: {str(e)}")

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
