import requests
from src.config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

def enviar_telegram(mensaje: str):
    print(mensaje)
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram no configurado. Saltando alerta móvil.")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # CORRECCIÓN: Cambiamos 'payload' por 'json' que es el argumento correcto de requests.post
    body = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "HTML"
    }
    
    try:
        requests.post(url, json=body, timeout=10)
    except Exception as e:
        print(f"❌ Error enviando mensaje a Telegram: {e}")