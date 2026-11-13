import ccxt
import pandas as pd
import numpy as np

# ==========================================
# 1. CONFIGURACIÓN GANADORA (EL SANTO GRIAL)
# ==========================================
SYMBOL_1 = 'ETH/USDT'
SYMBOL_2 = 'BTC/USDT'
TIMEFRAME = '1h'
VELAS_HISTORICAS = 2000
CAPITAL_INICIAL = 50.0
COMISION_BINANCE = 0.0005

# Parámetros optimizados descubiertos en la V5.0
VENTANA_HORAS = 150
UMBRAL_ZSCORE = 2.0  # Cambiá a 2.0 para tener ~5 tiros al mes en lugar de 3
APALANCAMIENTO = 100.0

def descargar_datos(symbol, timeframe, limit):
    exchange = ccxt.binance({'enableRateLimit': True, 'options': {'defaultType': 'future'}})
    ohlcv = []
    since = None
    while len(ohlcv) < limit:
        batch = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=1000)
        if not batch: break
        ohlcv.extend(batch)
        since = batch[-1][0] + 1
        if len(batch) < 1000: break
    df = pd.DataFrame(ohlcv[:limit], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df.rename(columns={'close': f'close_{symbol[:3]}', 'open': f'open_{symbol[:3]}'})
    return df[['timestamp', f'close_{symbol[:3]}', f'open_{symbol[:3]}']]

# ==========================================
# 2. LÓGICA DE TENSIÓN (LA BANDA ELÁSTICA)
# ==========================================
def calcular_zscore(df_sync, window, sym1, sym2):
    df = df_sync.copy()
    col_c1, col_c2 = f'close_{sym1[:3]}', f'close_{sym2[:3]}'
    # Relación entre ETH y BTC
    df['ratio'] = df[col_c1] / df[col_c2]
    # Promedio de la relación en las últimas 150 horas
    df['media_ratio'] = df['ratio'].rolling(window=window).mean()
    # Qué tan volátil fue esa relación
    df['std_ratio'] = df['ratio'].rolling(window=window).std()
    # Z-Score: a cuántas desviaciones estándar estamos del promedio
    df['zscore'] = (df['ratio'] - df['media_ratio']) / df['std_ratio']
    return df.dropna().reset_index(drop=True)

# ==========================================
# 3. SIMULADOR DEL FRANCOTIRADOR
# ==========================================
def simular_arbitraje_final(df):
    capital = CAPITAL_INICIAL
    en_posicion = False
    tipo_posicion = 0 
    precio_entrada_1 = 0.0; precio_entrada_2 = 0.0; tamano_pierna = 0.0
    historial_trades = []

    col_c1, col_c2 = 'close_ETH', 'close_BTC'

    for i, row in df.iterrows():
        z = row['zscore']
        
        # -- LÓGICA DE SALIDA --
        if en_posicion:
            salio = False
            # Si la banda elástica se relajó (volvió al centro 0)
            if tipo_posicion == 1 and z >= 0.0: salio = True
            elif tipo_posicion == -1 and z <= 0.0: salio = True
            # Freno de emergencia por si el mercado enloquece
            if abs(z) >= 4.5: salio = True 

            if salio:
                cambio_1 = (row[col_c1] - precio_entrada_1) / precio_entrada_1
                cambio_2 = (row[col_c2] - precio_entrada_2) / precio_entrada_2
                
                # Calculamos si ganamos con el Short o con el Long
                if tipo_posicion == 1:
                    pnl_bruto = (tamano_pierna * cambio_1) - (tamano_pierna * cambio_2)
                    accion = "LONG ETH / SHORT BTC"
                else:
                    pnl_bruto = (tamano_pierna * cambio_2) - (tamano_pierna * cambio_1)
                    accion = "SHORT ETH / LONG BTC"
                
                # Descontamos TODAS las comisiones (abrir y cerrar 2 monedas = 4 operaciones)
                friccion_total = (tamano_pierna * 2) * (COMISION_BINANCE * 2)
                pnl_neto = pnl_bruto - friccion_total
                capital += pnl_neto
                
                historial_trades.append({
                    'Cierre': row['timestamp'].strftime('%Y-%m-%d %H:00'),
                    'Jugada': accion,
                    'Z-Entrada': round(z_entrada, 2),
                    'PnL Neto ($)': round(pnl_neto, 2),
                    'Capital ($)': round(capital, 2)
                })
                en_posicion = False

        # -- LÓGICA DE ENTRADA --
        if not en_posicion:
            if z <= -UMBRAL_ZSCORE:
                # ETH está extremadamente barato frente a BTC (Z-Score negativo extremo)
                tamano_pierna = (capital * APALANCAMIENTO) / 2.0
                precio_entrada_1, precio_entrada_2 = row[col_c1], row[col_c2]
                z_entrada = z
                tipo_posicion = 1
                en_posicion = True
                
            elif z >= UMBRAL_ZSCORE:
                # ETH está extremadamente caro frente a BTC (Z-Score positivo extremo)
                tamano_pierna = (capital * APALANCAMIENTO) / 2.0
                precio_entrada_1, precio_entrada_2 = row[col_c1], row[col_c2]
                z_entrada = z
                tipo_posicion = -1
                en_posicion = True

    return pd.DataFrame(historial_trades)

# ==========================================
# 4. EJECUCIÓN
# ==========================================
if __name__ == "__main__":
    print(f" Descargando datos de Binance...")
    df1 = descargar_datos(SYMBOL_1, TIMEFRAME, VELAS_HISTORICAS)
    df2 = descargar_datos(SYMBOL_2, TIMEFRAME, VELAS_HISTORICAS)
    
    print(f" Sincronizando e inyectando lógica (Ventana: {VENTANA_HORAS}h, Umbral: {UMBRAL_ZSCORE})...")
    df_sync = pd.merge(df1, df2, on='timestamp', how='inner')
    df_listo = calcular_zscore(df_sync, VENTANA_HORAS, SYMBOL_1, SYMBOL_2)
    
    trades = simular_arbitraje_final(df_listo)
    
    print("\n" + "="*80)
    print(f" AUDITORÍA DE OPERACIONES: ARBITRAJE {SYMBOL_1} vs {SYMBOL_2}")
    print("="*80)
    if trades.empty:
        print("El mercado no estuvo lo suficientemente tenso como para disparar operaciones.")
    else:
        print(trades.to_string(index=False))
        ganancia_total = trades.iloc[-1]['Capital ($)'] - CAPITAL_INICIAL
        print("-" * 80)
        print(f" CAPITAL INICIAL: ${CAPITAL_INICIAL} USD")
        print(f" CAPITAL FINAL:   ${trades.iloc[-1]['Capital ($)']} USD")
        print(f" GANANCIA NETA:   ${round(ganancia_total, 2)} USD (+{round((ganancia_total/CAPITAL_INICIAL)*100, 2)}%)")