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
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini")

SYSTEM_PROMPT = """You are OpenClaw, a smart Binance and crypto assistant.
Rules:
- Reply in the same language as the user (Arabic or English).
- Be clear, concise, and helpful.
- Never promise profit.
- Never give guaranteed financial advice.
- Encourage users to do their own research (DYOR).
- Focus on Binance, crypto basics, market tools, risk awareness, and security.
- Keep replies practical and friendly.
"""

user_histories = {}

# =========================
# Helpers
# =========================

def ai_available():
    return bool(OPENROUTER_API_KEY)

def format_price(num):
    try:
        num = float(num)
        if num >= 1000:
            return f"{num:,.2f}"
        elif num >= 1:
            return f"{num:,.4f}"
        else:
            return f"{num:.8f}"
    except:
        return str(num)

async def get_binance_price(symbol: str):
    symbol = symbol.upper().replace("/", "").strip()
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(url)

    if r.status_code != 200:
        try:
            data = r.json()
        except:
            data = r.text
        return None, f"Binance API error: {r.status_code} | {data}"

    data = r.json()
    if "price" not in data:
        return None, "Symbol not found"

    return data["price"], None

async def get_24hr_ticker(symbol: str):
    symbol = symbol.upper().replace("/", "").strip()
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(url)

    if r.status_code != 200:
        return None, f"Binance API error: {r.status_code}"

    data = r.json()
    if "symbol" not in data:
        return None, "Symbol not found"

    return data, None

async def get_top_coins():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url)

    if r.status_code != 200:
        return None, f"Binance API error: {r.status_code}"

    data = r.json()

    pairs = []
    for item in data:
        symbol = item.get("symbol", "")
        if symbol.endswith("USDT"):
            try:
                pairs.append({
                    "symbol": symbol,
                    "change": float(item.get("priceChangePercent", 0)),
                    "volume": float(item.get("quoteVolume", 0)),
                    "lastPrice": item.get("lastPrice", "0")
                })
            except:
                pass

    pairs.sort(key=lambda x: x["volume"], reverse=True)
    return pairs[:10], None

async def convert_amount(amount: float, from_coin: str, to_coin: str):
    from_coin = from_coin.upper()
    to_coin = to_coin.upper()

    if from_coin == to_coin:
        return amount, None

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

async def ask_openrouter(user_id, text):
    if not OPENROUTER_API_KEY:
        raise Exception("OPENROUTER_API_KEY missing")

    if user_id not in user_histories:
        user_histories[user_id] = []

    user_histories[user_id].append({
        "role": "user",
        "content": text
    })

    if len(user_histories[user_id]) > 12:
        user_histories[user_id] = user_histories[user_id][-12:]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + user_histories[user_id]

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/",
        "X-Title": "OpenClaw Bot"
    }

    async with httpx.AsyncClient(timeout=40) as client:
        response = await client.post(OPENROUTER_URL, headers=headers, json=payload)

    if response.status_code != 200:
        try:
            err = response.json()
        except:
            err = response.text
        raise Exception(f"OpenRouter error: {response.status_code} | {err}")

    data = response.json()

    try:
        reply = data["choices"][0]["message"]["content"]
    except Exception:
        raise Exception(f"Unexpected OpenRouter response: {data}")

    user_histories[user_id].append({
        "role": "assistant",
        "content": reply
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
        f"مساعد ذكي للـ Binance وCrypto.\n\n"
        f"الأوامر:\n"
        f"/help - كل الأوامر\n"
        f"/price BTC - سعر عملة\n"
        f"/convert 100 USDT BNB - تحويل\n"
        f"/top - العملات النشطة\n"
        f"/roadmap - تتعلم تبدأ منين\n"
        f"/opportunity BTC - لمحة سريعة عن العملة\n"
        f"/risk - قواعد إدارة المخاطر\n\n"
        f"💬 أو ابعت أي سؤال مباشر.\n"
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
        "/price BTC\n"
        "/convert 100 USDT BNB\n"
        "/top\n"
        "/opportunity BTC\n\n"
        "📚 تعلم:\n"
        "/roadmap\n"
        "/crypto\n"
        "/binance\n"
        "/security\n"
        "/risk\n\n"
        "🤖 AI:\n"
        "ابعت سؤالك مباشرة."
    )
    await update.message.reply_text(msg)

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🦀 OpenClaw v2\n\n"
        "بوت يساعد في:\n"
        "• أسعار العملات\n"
        "• التحويل بين العملات\n"
        "• شرح Binance\n"
        "• أساسيات الكريبتو\n"
        "• الأمن وإدارة المخاطر\n"
        "• أسئلة عامة بالذكاء الاصطناعي عبر OpenRouter\n\n"
        "⚠️ Educational only — DYOR"
    )
    await update.message.reply_text(msg)

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_histories[update.effective_user.id] = []
    await update.message.reply_text("✅ تم مسح المحادثة.")

async def binance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
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

async def crypto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 مصطلحات Crypto:\n\n"
        "BTC = Bitcoin\n"
        "ETH = Ethereum\n"
        "BNB = Binance Coin\n"
        "USDT = Stablecoin\n"
        "DeFi = تمويل لامركزي\n"
        "Bull Market = سوق صاعد\n"
        "Bear Market = سوق هابط\n"
        "Liquidity = السيولة\n"
        "Volatility = التذبذب\n\n"
        "ابعت أي مصطلح وأنا أبسطه."
    )

async def security_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔐 نصائح الأمان:\n\n"
        "✅ فعّل 2FA\n"
        "✅ استخدم Anti-Phishing Code\n"
        "✅ فعل Withdrawal Whitelist\n"
        "✅ راجع اللينكات كويس\n"
        "✅ استخدم كلمة مرور قوية\n"
        "❌ ما تشاركش API Keys\n"
        "❌ ما تصدقش أي giveaway بسهولة\n"
        "❌ ما تدخلش seed phrase في أي موقع\n\n"
        "أمانك أهم من أي صفقة."
    )

async def risk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚠️ قواعد إدارة المخاطر:\n\n"
        "1) ما تدخلش بكل رأس المال في صفقة واحدة\n"
        "2) حدد وقف خسارة قبل الدخول\n"
        "3) ما تستخدمش رافعة عالية من غير خبرة\n"
        "4) افصل بين الاستثمار والتداول\n"
        "5) ما تطاردش الشموع\n"
        "6) DYOR دايمًا\n\n"
        "الهدف الأول: البقاء في السوق."
    )

async def roadmap_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛣️ Roadmap للمبتدئ:\n\n"
        "1) افهم BTC / ETH / BNB / USDT\n"
        "2) اتعلم Spot الأول\n"
        "3) افهم الفرق بين Wallet و Exchange\n"
        "4) فعّل كل إعدادات الأمان\n"
        "5) جرّب مبالغ صغيرة\n"
        "6) بعدين فقط افهم Futures والمخاطر\n"
        "7) تابع الأخبار والمشاريع بعقل، مش بعاطفة\n\n"
        "ابدأ بسيط وامشِ خطوة خطوة."
    )

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("استخدمها كده:\n/price BTC\nأو\n/price BTCUSDT")
        return

    coin = context.args[0].upper().replace("/", "").strip()
    symbol = coin if coin.endswith("USDT") else coin + "USDT"

    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

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

    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

    result, err = await convert_amount(amount, from_coin, to_coin)
    if err:
        await update.message.reply_text(f"⚠️ {err}")
        return

    await update.message.reply_text(
        f"🔄 التحويل:\n\n"
        f"{amount} {from_coin} ≈ {format_price(result)} {to_coin}"
    )

async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

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

async def opportunity_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("استخدمها كده:\n/opportunity BTC")
        return

    coin = context.args[0].upper().replace("/", "").strip()
    symbol = coin if coin.endswith("USDT") else coin + "USDT"

    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

    data, err = await get_24hr_ticker(symbol)
    if err:
        await update.message.reply_text(f"⚠️ ماقدرتش أجيب بيانات {symbol}\n{err}")
        return

    try:
        change = float(data.get("priceChangePercent", 0))
        high = data.get("highPrice")
        low = data.get("lowPrice")
        last = data.get("lastPrice")
        volume = float(data.get("quoteVolume", 0))
    except:
        await update.message.reply_text("⚠️ حصل خطأ في قراءة البيانات.")
        return

    mood = "🔥 Momentum قوي" if change > 5 else "🙂 حركة إيجابية" if change > 0 else "⚠️ ضغط أو ضعف" if change < 0 else "😐 حركة محايدة"

    msg = (
        f"📌 Snapshot: {symbol}\n\n"
        f"السعر: {format_price(last)} USDT\n"
        f"24h Change: {change:.2f}%\n"
        f"24h High: {format_price(high)}\n"
        f"24h Low: {format_price(low)}\n"
        f"Quote Volume: {format_price(volume)}\n\n"
        f"الحالة: {mood}\n"
        f"دي مجرد لمحة سريعة وليست إشارة دخول. DYOR."
    )
    await update.message.reply_text(msg)

# =========================
# AI chat
# =========================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

    if not ai_available():
        await update.message.reply_text(
            "⚠️ AI is temporarily unavailable.\n\n"
            "Use:\n"
            "/price BTC\n"
            "/convert 100 USDT BNB\n"
            "/top\n"
            "/opportunity BTC\n"
            "/help"
        )
        return

    try:
        reply = await ask_openrouter(user_id, user_text)
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"AI Error: {e}")
        await update.message.reply_text(
            "⚠️ AI is temporarily unavailable right now.\n\n"
            "You can still use:\n"
            "/price BTC\n"
            "/convert 100 USDT BNB\n"
            "/top\n"
            "/opportunity BTC\n"
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
    app.add_handler(CommandHandler("risk", risk_command))
    app.add_handler(CommandHandler("roadmap", roadmap_command))
    app.add_handler(CommandHandler("price", price_command))
    app.add_handler(CommandHandler("convert", convert_command))
    app.add_handler(CommandHandler("top", top_command))
    app.add_handler(CommandHandler("opportunity", opportunity_command))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🦀 OpenClaw v2 is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
