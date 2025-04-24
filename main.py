from telethon import TelegramClient, events
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re

# --- CONFIG TELEGRAM ---
api_id = 27143574
api_hash = "62ab5efd67204a932d8d5ef92be9161a"
canal = "https://t.me/promocoesdodiacanal"

# --- CONFIG GOOGLE SHEETS ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
import json
import os

json_creds = json.loads(os.environ["GOOGLE_CREDS_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(json_creds, scope)

client_sheets = gspread.authorize(creds)
sheet = client_sheets.open("PromocoesTelegram").sheet1

# --- FUNÇÕES DE EXTRAÇÃO ---
def limpar_texto(texto):
    return re.sub(r'[^\w\s\-.,]', '', texto)

def extrair_nome_produto(mensagem):
    linhas = mensagem.split('\n')
    provaveis = []
    for linha in linhas:
        limpa = limpar_texto(linha).strip()
        if len(limpa.split()) > 2 and "http" not in limpa and "R$" not in limpa and "cupom" not in limpa.lower():
            provaveis.append(limpa)
    return max(provaveis, key=len) if provaveis else ""

def extrair_dados(mensagem):
    link = re.search(r'(https?://[^\s]+)', mensagem)
    preco = re.search(r'R?\$ ?\d+(?:[.,]\d{2})?', mensagem)
    cupom = re.search(r'[Cc]upom[:\- ]+([A-Z0-9]{4,20})', mensagem)
    produto = extrair_nome_produto(mensagem)
    return {
        'mensagem': mensagem,
        'produto': produto,
        'preco': preco.group() if preco else '',
        'link': link.group() if link else '',
        'cupom': cupom.group(1) if cupom else ''
    }

# --- TELEGRAM ---
client = TelegramClient('session_name', api_id, api_hash)

@client.on(events.NewMessage(chats=canal))
async def handler(event):
    texto = event.message.message
    dados = extrair_dados(texto)
    print("Nova mensagem recebida:", dados)
    sheet.append_row([dados['mensagem'], dados['produto'], dados['preco'], dados['link'], dados['cupom']])

# --- FLASK ---
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot está online!"

def run():
    app.run(host='0.0.0.0', port=8080)

t = Thread(target=run)
t.start()

# --- INICIA O BOT TELEGRAM ---
print("Aguardando mensagens...")
client.start()
client.run_until_disconnected()
