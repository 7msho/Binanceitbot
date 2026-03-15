import os
import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    system_instruction="""You are OpenClaw 🦀, an elite AI assistant for the Binance ecosystem.
Help ALL users — beginners to experts — with crypto and Binance questions.
Topics you cover:
- Crypto basics (BTC, ETH, BNB, DeFi, NFT, staking, mining)
- Binance features (spot trading, futures, earn, P2P, launchpad)
- Order types (market, limit, stop-loss, OCO)
- Security (2FA, anti-phishing, withdrawal whitelist)
- Fees, spreads, funding rates
- Binance Web3 Wallet
- Trading psychology and risk management
Rules:
- Never give financial advice or tell users what to buy/sell
- Always remind users to DYOR when relevant
- Be friendly, clear, and use emojis
- Respond in the SAME language as the user (Arabic or English)
- Format nicely for Telegram"""
)

user_chats = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"👋 أهلاً {name}!\n\n"
        "🦀 أنا *OpenClaw* — مساعدك الذكي لكل حاجة Binance وCrypto!\n\n"
        "اسألني عن:\n"
        "🪙 شرح العملات والمفاهيم\n"
        "📊 كيفية التداول على Binance\n"
        "🔐 أمان حسابك\n"
        "💰 Binance Earn والـ Staking\n"
        "⚡ الـ Futures والـ Leverage\n\n"
        "اكتب /help لقائمة الأوامر\n\n"
        "⚠️ _للأغراض التعليمية فقط - مش نصيحة مالية_",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🦀 *OpenClaw - الأوامر المتاحة*\n\n"
        "/start - رسالة الترحيب\n"
        "/help - قائمة الأوامر\n"
        "/about - معلومات عن البوت\n"
        "/clear - مسح تاريخ المحادثة\n"
        "/binance - مميزات Binance الرئيسية\n"
        "/crypto - مصطلحات Crypto الأساسية\n"
        "/security - نصائح أمان الحساب\n\n"
        "💬 أو اكتب سؤالك مباشرة!",
        parse_mode="Markdown"
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🦀 *OpenClaw AI Assistant*\n\n"
        "Built for the *Binance OpenClaw AI Challenge 2026* 🏆\n\n"
        "🎯 الهدف: تسهيل تجربة Binance للجميع\n"
        "🤖 مدعوم بـ: Google Gemini AI\n"
        "⚡ السرعة: ردود فورية\n"
        "🌍 اللغات: العربية والإنجليزية\n\n"
        "⚠️ _للأغراض التعليمية فقط - ليس نصيحة مالية_",
        parse_mode="Markdown"
    )

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_chats:
        del user_chats[user_id]
    await update.message.reply_text("✅ تم مسح تاريخ المحادثة! ابدأ سؤال جديد 🦀")

async def binance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏦 *مميزات Binance الرئيسية*\n\n"
        "📈 *Spot Trading* - تداول العملات مباشرة\n"
        "⚡ *Futures* - تداول بالرافعة المالية\n"
        "💰 *Binance Earn* - استثمار وفوائد يومية\n"
        "🔄 *P2P* - بيع وشراء بالعملات المحلية\n"
        "🚀 *Launchpad* - الاشتراك في عملات جديدة\n"
        "🌐 *Web3 Wallet* - محفظة لامركزية\n"
        "💳 *Binance Card* - بطاقة دفع بالكريبتو\n\n"
        "اسألني عن أي ميزة للمزيد من التفاصيل! 🦀",
        parse_mode="Markdown"
    )

async def crypto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 *مصطلحات Crypto الأساسية*\n\n"
        "🪙 *BTC* - Bitcoin، أول عملة رقمية\n"
        "💎 *ETH* - Ethereum، منصة العقود الذكية\n"
        "🟡 *BNB* - عملة Binance الأصلية\n"
        "💵 *USDT* - عملة مستقرة مربوطة بالدولار\n"
        "🏦 *DeFi* - التمويل اللامركزي\n"
        "🖼️ *NFT* - رمز غير قابل للاستبدال\n"
        "📊 *ATH* - أعلى سعر في التاريخ\n"
        "🐂 *Bull Market* - سوق صاعد\n"
        "🐻 *Bear Market* - سوق هابط\n\n"
        "اسألني عن أي مصطلح للمزيد! 🦀",
        parse_mode="Markdown"
    )

async def security_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔐 *نصائح أمان حساب Binance*\n\n"
        "✅ فعّل *2FA* (Google Authenticator)\n"
        "✅ استخدم *Anti-Phishing Code*\n"
        "✅ فعّل *Withdrawal Whitelist*\n"
        "✅ استخدم كلمة مرور قوية وفريدة\n"
        "✅ لا تشارك الـ API Keys مع أحد\n"
        "✅ تحقق دايماً من الـ URL\n"
        "❌ لا تدخل بياناتك في مواقع مجهولة\n"
        "❌ لا تصدق عروض الـ giveaway\n\n"
        "🦀 _أمانك أهم من أي ربح!_",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    if user_id not in user_chats:
        user_chats[user_id] = model.start_chat(history=[])

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        response = user_chats[user_id].send_message(user_text)
        await update.message.reply_text(response.text)
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
