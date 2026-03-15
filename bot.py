import os
import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)
import anthropic
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

ANTHROPIC_CLIENT = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are OpenClaw 🦀, an elite AI assistant built for the Binance ecosystem.
You help ALL users — from complete beginners to seasoned traders — navigate Binance with confidence.

You can help with:
- Explaining crypto concepts (BTC, ETH, BNB, DeFi, staking, futures, etc.)
- Walking users through Binance features (buy, sell, transfer, stake, Binance Earn)
- Explaining order types (market, limit, stop-loss, OCO)
- Risk management and trading psychology
- Binance security best practices (2FA, anti-phishing, withdrawal whitelist)
- Understanding fees, spreads, and funding rates
- Binance Web3 Wallet and dApp usage

Rules:
- Always be friendly, clear, and encouraging
- Never give financial advice or tell users what to buy/sell
- Always remind users to DYOR when relevant
- Keep answers concise but complete
- Use emojis to make it friendly
- Respond in the SAME language the user writes in (Arabic or English)
- Format nicely for Telegram (use *bold* and bullet points)"""

# Store conversation history per user
user_histories = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    welcome = f"""👋 أهلاً {user_name}!

🦀 أنا *OpenClaw* — مساعدك الذكي لكل حاجة Binance وCrypto!

اسألني عن أي حاجة:
• 🪙 شرح العملات والمفاهيم
• 📊 كيفية التداول على Binance
• 🔐 أمان حسابك
• 💰 Binance Earn والـ Staking
• ⚡ الـ Futures والـ Leverage

اكتب سؤالك وأنا هجاوبك! 🚀

_⚠️ تنبيه: أنا بدي معلومات تعليمية بس، مش نصيحة مالية. اعمل بحثك دايماً (DYOR)_"""
    
    await update.message.reply_text(welcome, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """🦀 *OpenClaw - أوامر البوت*

/start - ابدأ من هنا
/help - قائمة الأوامر
/clear - امسح تاريخ المحادثة
/about - معلومات عن OpenClaw

💬 أو اكتب سؤالك مباشرة!"""
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_histories[user_id] = []
    await update.message.reply_text("✅ تم مسح تاريخ المحادثة! ابدأ سؤال جديد 🦀")

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_text = """🦀 *OpenClaw AI Assistant*

Built for the *Binance OpenClaw AI Challenge 2026* 🏆

🎯 الهدف: تسهيل تجربة Binance للجميع
🤖 مدعوم بـ: Claude AI (Anthropic)
👨‍💻 التقنيات: Python, Telegram Bot API, Railway

_⚠️ للأغراض التعليمية فقط - ليس نصيحة مالية_"""
    await update.message.reply_text(about_text, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    # Initialize history for new users
    if user_id not in user_histories:
        user_histories[user_id] = []

    # Add user message to history
    user_histories[user_id].append({
        "role": "user",
        "content": user_text
    })

    # Keep last 10 messages only (5 exchanges)
    if len(user_histories[user_id]) > 10:
        user_histories[user_id] = user_histories[user_id][-10:]

    # Show typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    try:
        response = ANTHROPIC_CLIENT.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=user_histories[user_id]
        )
        
        reply = response.content[0].text

        # Add assistant response to history
        user_histories[user_id].append({
            "role": "assistant",
            "content": reply
        })

        await update.message.reply_text(reply, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(
            "⚠️ حدث خطأ. حاول تاني بعد شوية!\n_If this persists, try /clear_",
            parse_mode="Markdown"
        )

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN غير موجود في .env")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🦀 OpenClaw Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
