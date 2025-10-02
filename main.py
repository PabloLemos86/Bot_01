import telebot
import json
import os
import requests

TOKEN = "8300789769:AAF0CblqLBjWXOZpzEZYSyad9NQ_cwMwW3E"
bot = telebot.TeleBot(TOKEN)

STORE_FILE = "store.json"

# Carrega dados
def load_store():
    if os.path.exists(STORE_FILE):
        with open(STORE_FILE, "r") as f:
            return json.load(f)
    return {"users": {}}

# Salva dados
def save_store(data):
    with open(STORE_FILE, "w") as f:
        json.dump(data, f, indent=2)

# /start comando
@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(msg, "🤖 Bot ativo! Use /setapi, /addendpoint e /call")

# /setapi nome token base_url
@bot.message_handler(commands=['setapi'])
def setapi(msg):
    try:
        _, name, token, base_url = msg.text.split(maxsplit=3)
    except:
        bot.reply_to(msg, "Uso: /setapi nome_api token base_url")
        return

    data = load_store()
    user_id = str(msg.from_user.id)
    if user_id not in data["users"]:
        data["users"][user_id] = {"apis": {}}
    data["users"][user_id]["apis"][name] = {
        "token": token,
        "base_url": base_url,
        "endpoints": {}
    }
    save_store(data)
    bot.reply_to(msg, f"API '{name}' configurada!")

# /addendpoint api nome_endpoint method path params
@bot.message_handler(commands=['addendpoint'])
def addendpoint(msg):
    try:
        _, api, endpoint, method, path, params = msg.text.split(maxsplit=5)
    except:
        bot.reply_to(msg, "Uso: /addendpoint nome_api nome_endpoint method path params")
        return

    data = load_store()
    user_id = str(msg.from_user.id)
    if user_id not in data["users"] or api not in data["users"][user_id]["apis"]:
        bot.reply_to(msg, "API não encontrada. Configure com /setapi primeiro.")
        return

    data["users"][user_id]["apis"][api]["endpoints"][endpoint] = {
        "method": method,
        "path": path,
        "params": params.split(",") if params else []
    }
    save_store(data)
    bot.reply_to(msg, f"Endpoint '{endpoint}' adicionado na API '{api}'")

# /call api endpoint {json}
@bot.message_handler(commands=['call'])
def call(msg):
    try:
        parts = msg.text.split(maxsplit=3)
        _, api, endpoint, json_params = parts
    except:
        bot.reply_to(msg, "Uso: /call nome_api nome_endpoint {json_params}")
        return

    import json as js
    try:
        params = js.loads(json_params)
    except Exception as e:
        bot.reply_to(msg, f"Erro no JSON: {e}")
        return

    data = load_store()
    user_id = str(msg.from_user.id)
    if user_id not in data["users"] or api not in data["users"][user_id]["apis"]:
        bot.reply_to(msg, "API não configurada.")
        return
    api_data = data["users"][user_id]["apis"][api]
    if endpoint not in api_data["endpoints"]:
        bot.reply_to(msg, "Endpoint não encontrado.")
        return
    ep = api_data["endpoints"][endpoint]
    url = api_data["base_url"] + ep["path"]
    headers = {}
    if api_data["token"] and api_data["token"] != "none":
        headers["Authorization"] = f"Bearer {api_data['token']}"

    try:
        if ep["method"].upper() == "GET":
            r = requests.get(url, headers=headers, params=params)
        else:
            r = requests.post(url, headers=headers, json=params)
        bot.reply_to(msg, f"Resposta ({r.status_code}):\n{r.text[:1000]}")
    except Exception as e:
        bot.reply_to(msg, f"Erro na requisição: {e}")

print("🤖 Bot rodando...")
bot.polling()
