import os
import logging
import httpx
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# استخدم موديل شغال عندك
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

SYSTEM_PROMPT = """You are OpenClaw, a smart Binance and crypto assistant.
Rules:
- Help users in Arabic or English depending on their language.
- Be short, clear, and useful.
- Never give guaranteed profit promises.
- Never give financial advice. Say DYOR when needed.
- Focus on Binance, crypto basics, security, market info, and simple explanations.
"""

user_histories = {}

# =========================
# Helpers
# =========================

def ai_available():
    return bool(GEMINI_API_KEY)

def format_price(num):
    try:
        num = float(num)
        if num >= 1:
            return f"{num:,.4f}"
        return f"{num:.8f}"
    except:
        return str(num)

async def get_binance_price(symbol: str):
    symbol = symbol.upper().replace("/", "").strip()
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(url)
        if r.status_code != 200:
            return None, f"Binance API error: {r.status_code}"
        data = r.json()
        if "price" not in data:
            return None, "Symbol not found"
        return data["price"], None

async def get_top_coins():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url)
        if r.status_code != 200:
            return None, f"Binance API error: {r.status_code}"
        data = r.json()

    usdt_pairs = []
    for item in data:
        symbol = item.get("symbol", "")
        if symbol.endswith("USDT"):
            try:
                price_change = float(item.get("priceChangePercent", 0))
                quote_volume = float(item.get("quoteVolume", 0))
                usdt_pairs.append({
                    "symbol": symbol,
                    "change": price_change,
                    "volume": quote_volume,
                    "lastPrice": item.get("lastPrice", "0")
                })
            except:
                pass

    # أكبر حجم تداول مع فلترة بسيطة
    usdt_pairs.sort(key=lambda x: x["volume"], reverse=True)
    return usdt_pairs[:10], None

async def convert_amount(amount: float, from_coin: str, to_coin: str):
    from_coin = from_coin.upper()
    to_coin = to_coin.upper()

    if from_coin == to_coin:
        return amount, None

    # نحاول نجيب من/to عبر USDT
    from_price = 1.0 if from_coin == "USDT" else None
    to_price = 1.0 if to_coin == "USDT" else None

    if from_price is None:
        p, err = await get_binance_price(from_coin + "USDT")
        if err:
            return None, f"Couldn't get {from_coin} price"
        from_price = float(p)

    if to_price is None:
        p, err = await get_binance_price(to_coin + "USDT")
        if err:
            return None, f"Couldn't get {to_coin} price"
        to_price = float(p)

    usdt_value = amount * from_price
    result = usdt_value / to_price
    return result, None

async def ask_gemini(user_id, text):
    if not GEMINI_API_KEY:
        raise Exception("AI unavailable: missing GEMINI_API_KEY")

    if user_id not in user_histories:
        user_histories[user_id] = []

    user_histories[user_id].append({
        "role": "user",
        "parts": [{"text": text}]
    })

    if len(user_histories[user_id]) > 10:
        user_histories[user_id] = user_histories[user_id][-10:]

    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "contents": user_histories[user_id]
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            GEMINI_URL,
            headers={"Content-Type": "application/json"},
            json=payload
        )

    if response.status_code != 200:
        try:
            err = response.json()
        except:
            err = response.text
        raise Exception(f"Gemini error: {response.status_code} {err}")

    data = response.json()

    try:
        reply = data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        raise Exception(f"Unexpected Gemini response: {data}")

    user_histories[user_id].append({
        "role": "model",
        "parts": [{"text": reply}]
    })

    return reply

# =========================
# Commands
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name or "friend"
    msg = (
        f"👋 أهلاً {name}!\n\n"
        f"أنا OpenClaw 🦀\n"
        f"مساعد Binance و Crypto.\n\n"
        f"الأوامر الأساسية:\n"
        f"/help - كل الأوامر\n"
        f"/price BTC - سعر عملة\n"
        f"/convert 100 USDT BNB - تحويل\n"
        f"/top - العملات النشطة\n"
        f"/fear - مؤشر الخوف والطمع\n"
        f"/learn - تعلم سريع\n"
        f"/security - الأمان\n"
        f"/clear - مسح المحادثة\n\n"
        f"💬 ابعتلي أي سؤال مباشر.\n"
        f"⚠️ للأغراض التعليمية فقط"
    )
    await update.message.reply_text(msg)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🦀 الأوامر المتاحة:\n\n"
        "/start - تشغيل البوت\n"
        "/help - قائمة الأوامر\n"
        "/about - عن البوت\n"
        "/clear - مسح المحادثة\n\n"
        "📊 السوق:\n"
        "/price BTC - سعر BTCUSDT\n"
        "/price ETH - سعر ETHUSDT\n"
        "/convert 100 USDT BNB - تحويل عملات\n"
        "/top - أشهر العملات على Binance\n\n"
        "📚 تعليم:\n"
        "/learn - أساسيات سريعة\n"
        "/crypto - مصطلحات كريبتو\n"
        "/binance - خدمات Binance\n"
        "/security - نصائح الأمان\n\n"
        "🤖 الذكاء الاصطناعي:\n"
        "ابعت سؤالك مباشرة، ولو الـ AI غير متاح استخدم الأوامر الأساسية."
    )
    await update.message.reply_text(msg)

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🦀 OpenClaw AI Assistant\n\n"
        "بوت لمساعدة المستخدمين في:\n"
        "• أسعار العملات\n"
        "• التحويل بين العملات\n"
        "• أساسيات Binance\n"
        "• مصطلحات الكريبتو\n"
        "• الأمان\n"
        "• أسئلة عامة بالذكاء الاصطناعي\n\n"
        "🏆 Built for a Binance bot challenge\n"
        "⚠️ Educational only — DYOR"
    )
    await update.message.reply_text(msg)

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_histories[update.effective_user.id] = []
    await update.message.reply_text("✅ تم مسح المحادثة.")

async def binance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🏦 خدمات Binance:\n\n"
        "• Spot Trading\n"
        "• Futures\n"
        "• Binance Earn\n"
        "• P2P\n"
        "• Convert\n"
        "• Launchpad / Launchpool\n"
        "• Web3 Wallet\n"
        "• Copy Trading\n\n"
        "ابعت اسم أي خدمة وأنا أشرحها."
    )
    await update.message.reply_text(msg)

async def crypto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📚 مصطلحات مهمة:\n\n"
        "BTC = Bitcoin\n"
        "ETH = Ethereum\n"
        "BNB = Binance Coin\n"
        "USDT = Stablecoin\n"
        "DeFi = تمويل لامركزي\n"
        "Bull Market = سوق صاعد\n"
        "Bear Market = سوق هابط\n"
        "Market Cap = القيمة السوقية\n"
        "Liquidity = السيولة\n\n"
        "ابعتلي أي مصطلح وأنا أبسطهولك."
    )
    await update.message.reply_text(msg)

async def security_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🔐 أهم نصائح الأمان:\n\n"
        "✅ فعّل 2FA\n"
        "✅ استخدم Anti-Phishing Code\n"
        "✅ فعل Withdrawal Whitelist\n"
        "✅ خلي الباسورد قوي ومختلف\n"
        "✅ راجع اللينكات كويس\n"
        "❌ ما تشاركش API Keys\n"
        "❌ ما تدخلش على مواقع مجهولة\n"
        "❌ ما تصدقش أي Giveaway بسهولة\n\n"
        "أمانك قبل الربح."
    )
    await update.message.reply_text(msg)

async def learn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🎓 تعلم سريع:\n\n"
        "1) Spot = شراء وبيع مباشر\n"
        "2) Futures = عقود برافعة ومخاطرة أعلى\n"
        "3) Wallet = محفظة لحفظ الأصول\n"
        "4) Seed Phrase = مفتاح المحفظة، ما يتشاركش أبداً\n"
        "5) Stablecoin = عملة مستقرة زي USDT\n"
        "6) DYOR = اعمل بحثك بنفسك\n\n"
        "ابدأ بـ Spot والأمان الأول."
    )
    await update.message.reply_text(msg)

async def fear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get("https://api.alternative.me/fng/")
            data = r.json()
        
        value = int(data["data"][0]["value"])
        label = data["data"][0]["value_classification"]
        updated = data["data"][0]["time_until_update"]
        
        if value <= 25:
            emoji = "😱"
        elif value <= 45:
            emoji = "😰"
        elif value <= 55:
            emoji = "😐"
        elif value <= 75:
            emoji = "😊"
        else:
            emoji = "🤑"
        
        bar_filled = int(value / 10)
        bar = "🟡" * bar_filled + "⬛" * (10 - bar_filled)
        
        msg = (
            f"😶‍🌫️ Fear & Greed Index\n\n"
            f"{emoji} {label}\n"
            f"القيمة: {value}/100\n\n"
            f"{bar}\n\n"
            f"0 = Extreme Fear 😱\n"
            f"100 = Extreme Greed 🤑\n\n"
            f"⏱ يتحدث كل 24 ساعة"
        )
        await update.message.reply_text(msg)
    except Exception as e:
        logger.error(f"Fear & Greed error: {e}")
        await update.message.reply_text("⚠️ ماقدرتش أجيب البيانات، حاول تاني!")


async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("استخدمها كده:\n/price BTC\nأو\n/price BTCUSDT")
        return

    coin = context.args[0].upper().replace("/", "").strip()
    symbol = coin if coin.endswith("USDT") else coin + "USDT"

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    price, err = await get_binance_price(symbol)
    if err:
        await update.message.reply_text(f"⚠️ ماقدرتش أجيب السعر لـ {symbol}\n{err}")
        return

    base = symbol.replace("USDT", "")
    await update.message.reply_text(
        f"💰 سعر {base}\n\n"
        f"{symbol}: {format_price(price)} USDT"
    )

async def convert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 3:
        await update.message.reply_text("استخدمها كده:\n/convert 100 USDT BNB")
        return

    try:
        amount = float(context.args[0])
    except:
        await update.message.reply_text("⚠️ المبلغ لازم يكون رقم.")
        return

    from_coin = context.args[1].upper()
    to_coin = context.args[2].upper()

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    result, err = await convert_amount(amount, from_coin, to_coin)
    if err:
        await update.message.reply_text(f"⚠️ {err}")
        return

    await update.message.reply_text(
        f"🔄 التحويل:\n\n"
        f"{amount} {from_coin} ≈ {format_price(result)} {to_coin}"
    )

async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    coins, err = await get_top_coins()
    if err:
        await update.message.reply_text(f"⚠️ ماقدرتش أجيب البيانات.\n{err}")
        return

    lines = ["🔥 Top active USDT pairs on Binance:\n"]
    for i, c in enumerate(coins[:10], start=1):
        lines.append(
            f"{i}. {c['symbol']} | Price: {format_price(c['lastPrice'])} | 24h: {c['change']:.2f}%"
        )

    await update.message.reply_text("\n".join(lines))

# =========================
# AI chat
# =========================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    if not ai_available():
        await update.message.reply_text(
            "⚠️ AI is temporarily unavailable.\n\n"
            "You can still use:\n"
            "/price BTC\n"
            "/convert 100 USDT BNB\n"
            "/top\n"
            "/help"
        )
        return

    try:
        reply = await ask_gemini(user_id, user_text)
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"AI Error: {e}")
        await update.message.reply_text(
            "⚠️ AI is temporarily unavailable.\n\n"
            "You can still use:\n"
            "/price BTC\n"
            "/convert 100 USDT BNB\n"
            "/top\n"
            "/help"
        )

# =========================
# Main
# =========================

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
    app.add_handler(CommandHandler("learn", learn_command))
    app.add_handler(CommandHandler("fear", fear_command))
    app.add_handler(CommandHandler("price", price_command))
    app.add_handler(CommandHandler("convert", convert_command))
    app.add_handler(CommandHandler("top", top_command))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🦀 OpenClaw Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
