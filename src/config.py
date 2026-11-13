import os
from dotenv import load_dotenv

load_dotenv()

# Credenciales y Entorno
API_KEY = os.getenv("BINANCE_API_KEY", "")
API_SECRET = os.getenv("BINANCE_API_SECRET", "")
USE_TESTNET = os.getenv("USE_TESTNET", "True").lower() == "true"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Parámetros del Modelo Matemático (V5.0 Optimizado)
SYMBOL_1 = "ETH/USDT"
SYMBOL_2 = "BTC/USDT"
TIMEFRAME = "1h"
VENTANA_HORAS = 150
UMBRAL_ENTRADA = 0.01    # Podés cambiarlo a 3.5 si querés modo francotirador extremo
UMBRAL_SALIDA = 0.0     # Vuelta a la media (banda relajada)
UMBRAL_STOP_LOSS = 4.5  # Freno de emergencia si el Z-Score se descontrola

# Gestión de Capital
APALANCAMIENTO = 5      # 5x validado en simulación
PORCENTAJE_BANCA = 0.90 # Usa el 90% del saldo disponible (deja 10% de margen libre para comisiones)