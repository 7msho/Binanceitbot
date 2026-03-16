import os
import logging
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# =========================
# Helpers
# =========================

def format_price(p):
    p = float(p)
    if p >= 1:
        return f"{p:,.4f}"
    return f"{p:.8f}"

async def get_market():

    url = "https://api.binance.com/api/v3/ticker/24hr"

    async with httpx.AsyncClient() as client:
        r = await client.get(url)

    return r.json()

async def get_price(symbol):

    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"

    async with httpx.AsyncClient() as client:
        r = await client.get(url)

    if r.status_code != 200:
        return None

    return r.json()["price"]

# =========================
# Commands
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = (
        "🤖 Binance iT V6\n\n"
        "Your Crypto Intelligence Bot\n\n"
        "Commands:\n"
        "/price BTC\n"
        "/convert 100 USDT BNB\n"
        "/top\n"
        "/gainers\n"
        "/losers\n"
        "/scan\n"
        "/pump\n"
        "/analyze BTC\n"
        "/entry BTC\n"
        "/market\n"
        "/fear\n"
        "/news\n"
        "/launchpool\n\n"
        "⚠️ DYOR"
    )

    await update.message.reply_text(msg)

# =========================
# Price
# =========================

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("/price BTC")
        return

    coin = context.args[0].upper()
    symbol = coin if coin.endswith("USDT") else coin + "USDT"

    price = await get_price(symbol)

    if not price:
        await update.message.reply_text("Coin not found")
        return

    await update.message.reply_text(
        f"{symbol}\n{format_price(price)} USDT"
    )

# =========================
# Convert
# =========================

async def convert(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) != 3:
        await update.message.reply_text("/convert 100 USDT BNB")
        return

    amount = float(context.args[0])
    f = context.args[1].upper()
    t = context.args[2].upper()

    fp = 1 if f=="USDT" else float(await get_price(f+"USDT"))
    tp = 1 if t=="USDT" else float(await get_price(t+"USDT"))

    result = (amount*fp)/tp

    await update.message.reply_text(
        f"{amount} {f} ≈ {format_price(result)} {t}"
    )

# =========================
# Top
# =========================

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = await get_market()

    coins = []

    for d in data:
        if d["symbol"].endswith("USDT"):
            coins.append({
                "symbol": d["symbol"],
                "volume": float(d["quoteVolume"]),
                "change": float(d["priceChangePercent"]),
                "price": d["lastPrice"]
            })

    coins.sort(key=lambda x: x["volume"], reverse=True)

    text="🔥 Top Active\n\n"

    for c in coins[:10]:
        text+=f"{c['symbol']} {c['change']:.2f}% {format_price(c['price'])}\n"

    await update.message.reply_text(text)

# =========================
# Pump detector
# =========================

async def pump(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = await get_market()

    pumps=[]

    for d in data:

        if d["symbol"].endswith("USDT"):

            change=float(d["priceChangePercent"])
            volume=float(d["quoteVolume"])

            if change>6 and volume>15000000:

                pumps.append((d["symbol"],change))

    pumps.sort(key=lambda x:x[1],reverse=True)

    if not pumps:

        await update.message.reply_text("No pumps detected.")
        return

    text="🚨 Pump Detector\n\n"

    for p in pumps[:5]:
        text+=f"{p[0]} {p[1]:.2f}%\n"

    await update.message.reply_text(text)

# =========================
# News
# =========================

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg=(
        "📰 Crypto News\n\n"
        "BTC adoption rising\n"
        "ETF flows affecting market\n"
        "BNB ecosystem expanding\n\n"
        "Watch market volatility."
    )

    await update.message.reply_text(msg)

# =========================
# Launchpool
# =========================

async def launchpool(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg=(
        "🪂 Binance Opportunities\n\n"
        "Launchpool\n"
        "Launchpad\n"
        "Megadrop\n"
        "Airdrops\n\n"
        "Stake BNB to earn rewards."
    )

    await update.message.reply_text(msg)

# =========================
# Fear
# =========================

async def fear(update: Update, context: ContextTypes.DEFAULT_TYPE):

    async with httpx.AsyncClient() as client:
        r=await client.get("https://api.alternative.me/fng/")

    data=r.json()

    v=data["data"][0]["value"]
    s=data["data"][0]["value_classification"]

    await update.message.reply_text(
        f"Fear & Greed\n\nValue: {v}\nState: {s}"
    )

# =========================
# AI chat
# =========================

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "AI assistant coming soon."
    )

# =========================
# Main
# =========================

def main():

    app=Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("price",price))
    app.add_handler(CommandHandler("convert",convert))
    app.add_handler(CommandHandler("top",top))
    app.add_handler(CommandHandler("pump",pump))
    app.add_handler(CommandHandler("news",news))
    app.add_handler(CommandHandler("launchpool",launchpool))
    app.add_handler(CommandHandler("fear",fear))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,chat))

    logger.info("Binance iT V6 running")

    app.run_polling()

if __name__=="__main__":
    main()
