import threading
import time
import json
import requests
from telebot import TeleBot, types

# Substitua pelo seu token real
TOKEN = "8300789769:AAF0CblqLBjWXOZpzEZYSyad9NQ_cwMwW3E"
bot = TeleBot(TOKEN)

STORE_FILE = "store.json"

# ------------------- Funções de armazenamento -------------------
def load_store():
    try:
        with open(STORE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_store(store):
    with open(STORE_FILE, "w") as f:
        json.dump(store, f, indent=4)

# ------------------- Função de coleta automática -------------------
def fetch_and_send():
    while True:
        store = load_store()
        for user_id, data in store.get("users", {}).items():
            for api_name, api_data in data.get("apis", {}).items():
                token = api_data.get("token")
                keywords = api_data.get("keywords", [])
                last_count = api_data.get("last_count", 10)
                endpoint_url = api_data.get("endpoint_url", "URL_DO_ENDPOINT")

                params = {"q": " OR ".join([k.replace("#","") for k in keywords])}

                if api_name == "newsdata":
                    params["apikey"] = token
                    try:
                        r = requests.get(endpoint_url, params=params)
                        results = r.json().get("results", [])[:last_count]
                        filtered = [n for n in results if any(k[1:] in n.get("title","") for k in keywords)]
                        message = "\n\n".join([f"{n.get('title')}\n{n.get('link')}" for n in filtered])
                        if message:
                            bot.send_message(user_id, f"📰 {api_name}:\n\n{message}")
                    except:
                        pass
        time.sleep(600)

threading.Thread(target=fetch_and_send, daemon=True).start()

# ------------------- Menu principal -------------------
@bot.message_handler(commands=['start'])
def start(msg):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row('New API', 'Minhas APIs', 'Configuração')
    bot.send_message(msg.chat.id, "Bem-vindo! Escolha uma opção:", reply_markup=kb)

# ------------------- Funções New API -------------------
@bot.message_handler(func=lambda m: m.text=="New API")
def new_api(msg):
    chat_id = str(msg.chat.id)
    store = load_store()
    if "users" not in store:
        store["users"] = {}
    if chat_id not in store["users"]:
        store["users"][chat_id] = {"apis": {}}

    bot.send_message(msg.chat.id, "Digite o nome da API:")
    bot.register_next_step_handler(msg, receive_api_name)

def receive_api_name(msg):
    chat_id = str(msg.chat.id)
    api_name = msg.text.lower()
    store = load_store()
    store["users"][chat_id]["current_api"] = api_name
    save_store(store)
    bot.send_message(msg.chat.id, f"Informe o token da API {api_name}:")
    bot.register_next_step_handler(msg, receive_api_token)

def receive_api_token(msg):
    chat_id = str(msg.chat.id)
    token = msg.text
    store = load_store()
    api_name = store["users"][chat_id]["current_api"]
    store["users"][chat_id]["apis"][api_name] = {
        "token": token,
        "keywords": [],
        "last_count": 10,
        "endpoint_url": "URL_DO_ENDPOINT"
    }
    save_store(store)
    bot.send_message(msg.chat.id, "Agora digite até 20 palavras-chave separadas por espaço, cada uma com #")
    bot.register_next_step_handler(msg, receive_keywords)

def receive_keywords(msg):
    chat_id = str(msg.chat.id)
    words = msg.text.split()
    if len(words) > 20:
        bot.send_message(msg.chat.id, "Você digitou mais de 20 palavras. Tente novamente.")
        bot.register_next_step_handler(msg, receive_keywords)
        return
    if not all(w.startswith("#") for w in words):
        bot.send_message(msg.chat.id, "Todas as palavras devem começar com #. Tente novamente.")
        bot.register_next_step_handler(msg, receive_keywords)
        return
    store = load_store()
    api_name = store["users"][chat_id]["current_api"]
    store["users"][chat_id]["apis"][api_name]["keywords"] = words
    save_store(store)

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("10 últimas", "20 últimas", "30 últimas")
    bot.send_message(msg.chat.id, "Escolha a quantidade de últimas informações:", reply_markup=kb)
    bot.register_next_step_handler(msg, receive_last_count)

def receive_last_count(msg):
    chat_id = str(msg.chat.id)
    count_map = {"10 últimas":10, "20 últimas":20, "30 últimas":30}
    if msg.text not in count_map:
        bot.send_message(msg.chat.id, "Escolha uma opção válida.")
        return
    count = count_map[msg.text]
    store = load_store()
    api_name = store["users"][chat_id]["current_api"]
    store["users"][chat_id]["apis"][api_name]["last_count"] = count
    save_store(store)
    bot.send_message(msg.chat.id, f"API {api_name} configurada com sucesso!")

# ------------------- Minhas APIs -------------------
@bot.message_handler(func=lambda m: m.text=="Minhas APIs")
def minhas_apis(msg):
    chat_id = str(msg.chat.id)
    store = load_store()
    user = store["users"].get(chat_id, {})
    apis = user.get("apis", {})
    if not apis:
        bot.send_message(msg.chat.id, "Nenhuma API cadastrada.")
        return
    for api_name, data in apis.items():
        bot.send_message(msg.chat.id, f"API: {api_name}\nToken: {data['token']}\nPalavras-chave: {' '.join(data['keywords'])}\nÚltimas informações: {data['last_count']}")

# ------------------- Configuração -------------------
@bot.message_handler(func=lambda m: m.text=="Configuração")
def configuracao(msg):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("Alterar API", "Apagar API", "Voltar")
    bot.send_message(msg.chat.id, "Escolha uma opção:", reply_markup=kb)

# Alterar API
@bot.message_handler(func=lambda m: m.text=="Alterar API")
def alterar_api(msg):
    chat_id = str(msg.chat.id)
    store = load_store()
    apis = list(store["users"].get(chat_id, {}).get("apis", {}).keys())
    if not apis:
        bot.send_message(msg.chat.id, "Nenhuma API para alterar.")
        return
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for api_name in apis:
        kb.row(api_name)
    bot.send_message(msg.chat.id, "Escolha a API que deseja alterar:", reply_markup=kb)
    bot.register_next_step_handler(msg, reset_api)

def reset_api(msg):
    chat_id = str(msg.chat.id)
    api_name = msg.text
    store = load_store()
    if api_name not in store["users"][chat_id]["apis"]:
        bot.send_message(msg.chat.id, "API inválida.")
        return
    # Reseta palavras-chave e last_count mantendo token
    store["users"][chat_id]["apis"][api_name]["keywords"] = []
    store["users"][chat_id]["apis"][api_name]["last_count"] = 10
    save_store(store)
    bot.send_message(msg.chat.id, f"API {api_name} reiniciada. Configure novamente palavras-chave e últimas notícias usando New API.")

# Apagar API
@bot.message_handler(func=lambda m: m.text=="Apagar API")
def apagar_api(msg):
    chat_id = str(msg.chat.id)
    store = load_store()
    apis = list(store["users"].get(chat_id, {}).get("apis", {}).keys())
    if not apis:
        bot.send_message(msg.chat.id, "Nenhuma API para apagar.")
        return
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for api_name in apis:
        kb.row(api_name)
    bot.send_message(msg.chat.id, "Escolha a API que deseja apagar:", reply_markup=kb)
    bot.register_next_step_handler(msg, confirm_delete)

def confirm_delete(msg):
    chat_id = str(msg.chat.id)
    api_name = msg.text
    store = load_store()
    if api_name not in store["users"][chat_id]["apis"]:
        bot.send_message(msg.chat.id, "API inválida.")
        return
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("Sim", "Não")
    store["users"][chat_id]["delete_api"] = api_name
    save_store(store)
    bot.send_message(msg.chat.id, f"Você tem certeza que deseja apagar a API {api_name}?", reply_markup=kb)
    bot.register_next_step_handler(msg, delete_api)

def delete_api(msg):
    chat_id = str(msg.chat.id)
    if msg.text != "Sim":
        bot.send_message(msg.chat.id, "Operação cancelada.")
        return
    store = load_store()
    api_name = store["users"][chat_id].get("delete_api")
    if api_name:
        del store["users"][chat_id]["apis"][api_name]
        del store["users"][chat_id]["delete_api"]
        save_store(store)
        bot.send_message(msg.chat.id, f"API {api_name} apagada com sucesso!")
    else:
        bot.send_message(msg.chat.id, "Nenhuma API encontrada para apagar.")

# ------------------- Polling -------------------
bot.polling()