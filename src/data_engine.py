import pandas as pd
from src.config import SYMBOL_1, SYMBOL_2, TIMEFRAME, VENTANA_HORAS

def _descargar_par(exchange, symbol: str, limit: int) -> pd.DataFrame:
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    prefijo = symbol.split('/')[0]
    df = df.rename(columns={'close': f'close_{prefijo}'})
    return df[['timestamp', f'close_{prefijo}']]

def obtener_estado_mercado(exchange) -> dict:
    # Pedimos 250 velas para tener margen de sobra para la media de 150 horas
    limit = VENTANA_HORAS + 100
    df1 = _descargar_par(exchange, SYMBOL_1, limit)
    df2 = _descargar_par(exchange, SYMBOL_2, limit)
    
    df = pd.merge(df1, df2, on='timestamp', how='inner')
    
    df['ratio'] = df['close_ETH'] / df['close_BTC']
    df['media'] = df['ratio'].rolling(window=VENTANA_HORAS).mean()
    df['std'] = df['ratio'].rolling(window=VENTANA_HORAS).std()
    df['zscore'] = (df['ratio'] - df['media']) / df['std']
    
    # IMPORTANTE: Usamos iloc[-2] (última vela de 1h 100% cerrada)
    ultima_cerrada = df.iloc[-2]
    
    return {
        "timestamp": ultima_cerrada['timestamp'].strftime('%Y-%m-%d %H:%M UTC'),
        "precio_eth": float(ultima_cerrada['close_ETH']),
        "precio_btc": float(ultima_cerrada['close_BTC']),
        "zscore": round(float(ultima_cerrada['zscore']), 3)
    }