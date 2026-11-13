import requests
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

url = f"https://api.telegram.org/bot{token}/sendMessage"
body = {
    "chat_id": chat_id,
    "text": "🚨 <b>PRUEBA DE FUEGO:</b> ¡El sistema de alertas funciona perfectamente!",
    "parse_mode": "HTML"
}

res = requests.post(url, json=body)
print("Respuesta de Telegram:", res.status_code, res.text)