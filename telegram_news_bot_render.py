import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import requests

# Configurações de logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Chaves e tokens do ambiente
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
NEWSDATA_KEY = os.getenv("NEWSDATA_KEY")

# Função para buscar notícias na NewsAPI
def fetch_news_from_newsapi(limit=5):
    url = f"https://newsapi.org/v2/top-headlines?country=br&pageSize={limit}&apiKey={NEWSAPI_KEY}"
    response = requests.get(url)
    data = response.json()
    articles = data.get("articles", [])
    return [f"📰 {a['title']}\n{a['url']}" for a in articles]

# Função para buscar notícias no NewsData.io
def fetch_news_from_newsdata(limit=5):
    url = f"https://newsdata.io/api/1/news?apikey={NEWSDATA_KEY}&country=br&language=pt&size={limit}"
    response = requests.get(url)
    data = response.json()
    articles = data.get("results", [])
    return [f"📰 {a['title']}\n{a['link']}" for a in articles]

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("5 últimas notícias", callback_data="5"),
            InlineKeyboardButton("10 últimas notícias", callback_data="10"),
            InlineKeyboardButton("15 últimas notícias", callback_data="15"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Escolha quantas notícias deseja ver:", reply_markup=reply_markup)

# Handler dos botões
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    limit = int(query.data)

    news_newsapi = fetch_news_from_newsapi(limit)
    news_newsdata = fetch_news_from_newsdata(limit)

    all_news = news_newsapi + news_newsdata
    if not all_news:
        await query.edit_message_text("⚠️ Não encontrei notícias no momento.")
        return

    # Envia as notícias em blocos
    chunk = 0
    for item in all_news:
        await query.message.reply_text(item)
        chunk += 1
        if chunk >= limit:
            break

async def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
