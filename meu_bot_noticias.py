import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Tokens
TELEGRAM_TOKEN = "8300789769:AAF0CblqLBjWXOZpzEZYSyad9NQ_cwMwW3E"
NEWSAPI_KEY = "eaefc719ba5a4cde98416470f752e578"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("5 últimas notícias", callback_data="news_5")],
        [InlineKeyboardButton("10 últimas notícias", callback_data="news_10")],
        [InlineKeyboardButton("15 últimas notícias", callback_data="news_15")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Escolha quantas notícias deseja ver:", reply_markup=reply_markup)

def split_message(text: str, max_length: int = 4096) -> list[str]:
    if len(text) <= max_length:
        return [text]
    parts = []
    while text:
        if len(text) <= max_length:
            parts.append(text)
            break
        split_at = text.rfind("\n\n", 0, max_length)
        if split_at == -1:
            split_at = max_length
        parts.append(text[:split_at])
        text = text[split_at:].lstrip()
    return parts

def get_news(limit: int):
    url = f"https://newsapi.org/v2/top-headlines?language=pt&pageSize={limit}&apiKey={NEWSAPI_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        articles = data.get("articles", [])
        if not articles:
            return "Nenhuma notícia encontrada."

        news_list = []
        for art in articles:
            title = art.get("title", "Sem título") or "Sem título"
            source = art.get("source", {}).get("name", "Desconhecido") or "Desconhecido"
            url = art.get("url", "")
            news_list.append(f"📰 *{title}*\n_{source}_\n🔗 {url}")
        return "\n\n".join(news_list)
    except Exception as e:
        return f"Erro ao buscar notícias: {e}"

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data

    if not choice.startswith("news_"):
        return

    try:
        limit = int(choice.split("_")[1])
    except:
        await query.edit_message_text("Opção inválida.")
        return

    news_message = get_news(limit)
    messages = split_message(news_message)

    await query.edit_message_text(messages[0], parse_mode=ParseMode.MARKDOWN)
    for extra in messages[1:]:
        await update.effective_chat.send_message(extra, parse_mode=ParseMode.MARKDOWN)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()

if __name__ == "__main__":
    main()