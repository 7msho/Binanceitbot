import os
import logging
import httpx
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL","openai/gpt-4o-mini")

SYSTEM_PROMPT = """
You are OpenClaw, a smart Binance and crypto assistant.

Rules:
Reply in the same language as the user.
Never promise profit.
Never give guaranteed financial advice.
Encourage DYOR.
Focus on crypto education and Binance ecosystem.
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


# =========================
# Binance APIs
# =========================

async def get_binance_price(symbol):

    symbol = symbol.upper().replace("/","")

    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"

    async with httpx.AsyncClient() as client:
        r = await client.get(url)

    if r.status_code != 200:
        return None,"API error"

    data = r.json()

    return data["price"],None


async def get_top_coins():

    url="https://api.binance.com/api/v3/ticker/24hr"

    async with httpx.AsyncClient() as client:
        r=await client.get(url)

    data=r.json()

    pairs=[]

    for item in data:

        if item["symbol"].endswith("USDT"):

            pairs.append({

                "symbol":item["symbol"],
                "change":float(item["priceChangePercent"]),
                "volume":float(item["quoteVolume"]),
                "price":item["lastPrice"]

            })

    pairs.sort(key=lambda x:x["volume"],reverse=True)

    return pairs[:10],None


# =========================
# CoinGecko APIs
# =========================

async def get_contract(symbol):

    url="https://api.coingecko.com/api/v3/coins/list"

    async with httpx.AsyncClient() as client:
        r=await client.get(url)

    coins=r.json()

    for c in coins:

        if c["symbol"].upper()==symbol.upper():

            coin_id=c["id"]

            detail_url=f"https://api.coingecko.com/api/v3/coins/{coin_id}"

            async with httpx.AsyncClient() as client:
                rr=await client.get(detail_url)

            data=rr.json()

            platforms=data.get("platforms",{})

            return platforms

    return None


async def get_new_tokens():

    url="https://api.coingecko.com/api/v3/coins/markets"

    params={

        "vs_currency":"usd",
        "order":"market_cap_desc",
        "per_page":10,
        "page":1

    }

    async with httpx.AsyncClient() as client:

        r=await client.get(url,params=params)

    return r.json()


async def get_global_market():

    url="https://api.coingecko.com/api/v3/global"

    async with httpx.AsyncClient() as client:
        r=await client.get(url)

    return r.json()


async def get_fear():

    url="https://api.alternative.me/fng/"

    async with httpx.AsyncClient() as client:
        r=await client.get(url)

    return r.json()


async def get_gas():

    url="https://ethgasstation.info/json/ethgasAPI.json"

    async with httpx.AsyncClient() as client:
        r=await client.get(url)

    return r.json()


# =========================
# Commands
# =========================

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🦀 OpenClaw Crypto Assistant\n\n"
        "/price BTC\n"
        "/top\n"
        "/contract ETH\n"
        "/newtokens\n"
        "/global\n"
        "/fear\n"
        "/gas\n"
    )


async def price_command(update:Update,context:ContextTypes.DEFAULT_TYPE):

    coin=context.args[0]

    symbol=coin+"USDT"

    price,_=await get_binance_price(symbol)

    await update.message.reply_text(f"{coin} price: {price} USDT")


async def top_command(update:Update,context:ContextTypes.DEFAULT_TYPE):

    coins,_=await get_top_coins()

    msg="🔥 Top pairs\n\n"

    for c in coins:

        msg+=f"{c['symbol']} | {c['price']} | {c['change']}%\n"

    await update.message.reply_text(msg)


# =========================
# NEW FEATURES
# =========================

async def contract_command(update:Update,context:ContextTypes.DEFAULT_TYPE):

    coin=context.args[0]

    data=await get_contract(coin)

    if not data:
        await update.message.reply_text("No contract found")

        return

    msg=f"📄 Contracts for {coin}\n\n"

    for net,addr in data.items():

        if addr:

            msg+=f"{net}\n{addr}\n\n"

    await update.message.reply_text(msg)


async def newtokens_command(update:Update,context:ContextTypes.DEFAULT_TYPE):

    tokens=await get_new_tokens()

    msg="🆕 Market tokens\n\n"

    for t in tokens[:10]:

        msg+=f"{t['symbol'].upper()} | ${t['current_price']} | MC ${t['market_cap']}\n"

    await update.message.reply_text(msg)


async def global_command(update:Update,context:ContextTypes.DEFAULT_TYPE):

    data=await get_global_market()

    market=data["data"]

    msg=(
        "🌍 Crypto Market\n\n"
        f"Market Cap: ${market['total_market_cap']['usd']}\n"
        f"24h Volume: ${market['total_volume']['usd']}\n"
        f"BTC Dominance: {market['market_cap_percentage']['btc']}%\n"
    )

    await update.message.reply_text(msg)


async def fear_command(update:Update,context:ContextTypes.DEFAULT_TYPE):

    data=await get_fear()

    index=data["data"][0]

    msg=(
        "😱 Fear & Greed Index\n\n"
        f"Value: {index['value']}\n"
        f"Status: {index['value_classification']}"
    )

    await update.message.reply_text(msg)


async def gas_command(update:Update,context:ContextTypes.DEFAULT_TYPE):

    data=await get_gas()

    fast=data["fast"]/10
    avg=data["average"]/10
    slow=data["safeLow"]/10

    msg=(
        "⛽ Ethereum Gas\n\n"
        f"Fast: {fast} gwei\n"
        f"Average: {avg} gwei\n"
        f"Slow: {slow} gwei"
    )

    await update.message.reply_text(msg)


# =========================
# AI chat
# =========================

async def handle_message(update:Update,context:ContextTypes.DEFAULT_TYPE):

    if not ai_available():

        await update.message.reply_text("AI unavailable")

        return


# =========================
# Main
# =========================

def main():

    app=Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("price",price_command))
    app.add_handler(CommandHandler("top",top_command))

    app.add_handler(CommandHandler("contract",contract_command))
    app.add_handler(CommandHandler("newtokens",newtokens_command))
    app.add_handler(CommandHandler("global",global_command))
    app.add_handler(CommandHandler("fear",fear_command))
    app.add_handler(CommandHandler("gas",gas_command))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handle_message))

    logger.info("Bot running...")

    app.run_polling()


if __name__=="__main__":

    main()
