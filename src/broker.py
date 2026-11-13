import ccxt
from src.config import API_KEY, API_SECRET, USE_TESTNET, SYMBOL_1, SYMBOL_2, APALANCAMIENTO, PORCENTAJE_BANCA

def conectar_exchange():
    exchange = ccxt.binance({
        'apiKey': API_KEY,
        'secret': API_SECRET,
        'enableRateLimit': True,
        'options': {'defaultType': 'future'}
    })
    if USE_TESTNET:
        exchange.enable_demo_trading(True)
    exchange.load_markets()
    return exchange

def obtener_saldo_usdt(exchange) -> float:
    balance = exchange.fetch_balance()
    return float(balance['USDT']['free'])

def consultar_posiciones_abiertas(exchange) -> dict:
    """
    Revisa directamente en Binance si ya estamos adentro del mercado.
    Devuelve:
      0  -> Sin posición (Afuera)
      1  -> Long ETH / Short BTC activo
     -1  -> Short ETH / Long BTC activo
    """
    positions = exchange.fetch_positions([SYMBOL_1, SYMBOL_2])
    eth_amt = 0.0
    btc_amt = 0.0
    pnl_no_realizado = 0.0

    for p in positions:
        amt = float(p['info'].get('positionAmt', 0))
        un_pnl = float(p['info'].get('unRealizedProfit', 0))
        if p['symbol'].startswith('ETH/USDT') and amt != 0:
            eth_amt = amt
            pnl_no_realizado += un_pnl
        elif p['symbol'].startswith('BTC/USDT') and amt != 0:
            btc_amt = amt
            pnl_no_realizado += un_pnl

    if eth_amt > 0 and btc_amt < 0:
        estado = 1
    elif eth_amt < 0 and btc_amt > 0:
        estado = -1
    else:
        estado = 0

    return {
        "estado": estado,
        "eth_amt": eth_amt,
        "btc_amt": btc_amt,
        "pnl_flotante": round(pnl_no_realizado, 2)
    }

def abrir_arbitraje(exchange, direccion: int, precio_eth: float, precio_btc: float) -> dict:
    # Configurar apalancamiento en ambos pares
    exchange.set_leverage(APALANCAMIENTO, SYMBOL_1)
    exchange.set_leverage(APALANCAMIENTO, SYMBOL_2)

    saldo_libre = obtener_saldo_usdt(exchange)
    capital_usable = saldo_libre * PORCENTAJE_BANCA
    tamano_pierna_usd = (capital_usable * APALANCAMIENTO) / 2.0

    if tamano_pierna_usd < 10.0:
        raise ValueError(f"Tamaño por pierna (${tamano_pierna_usd:.2f}) menor al mínimo permitido por Binance ($10 USD).")

    # Convertir dólares a cantidad de monedas respetando los decimales de Binance
    cant_eth = float(exchange.amount_to_precision(SYMBOL_1, tamano_pierna_usd / precio_eth))
    cant_btc = float(exchange.amount_to_precision(SYMBOL_2, tamano_pierna_usd / precio_btc))

    if direccion == 1:
        # LONG ETH / SHORT BTC
        exchange.create_market_buy_order(SYMBOL_1, cant_eth)
        exchange.create_market_sell_order(SYMBOL_2, cant_btc)
        jugada = "LONG ETH 🟢 / SHORT BTC 🔴"
    else:
        # SHORT ETH / LONG BTC
        exchange.create_market_sell_order(SYMBOL_1, cant_eth)
        exchange.create_market_buy_order(SYMBOL_2, cant_btc)
        jugada = "SHORT ETH 🔴 / LONG BTC 🟢"

    return {
        "jugada": jugada,
        "usd_por_pierna": round(tamano_pierna_usd, 2),
        "cant_eth": cant_eth,
        "cant_btc": cant_btc
    }

def cerrar_arbitraje(exchange, pos_info: dict):
    eth_amt = pos_info["eth_amt"]
    btc_amt = pos_info["btc_amt"]

    # Cerrar ETH con orden inversa + reduceOnly
    if eth_amt > 0:
        exchange.create_market_sell_order(SYMBOL_1, abs(eth_amt), params={'reduceOnly': True})
    elif eth_amt < 0:
        exchange.create_market_buy_order(SYMBOL_1, abs(eth_amt), params={'reduceOnly': True})

    # Cerrar BTC con orden inversa + reduceOnly
    if btc_amt > 0:
        exchange.create_market_sell_order(SYMBOL_2, abs(btc_amt), params={'reduceOnly': True})
    elif btc_amt < 0:
        exchange.create_market_buy_order(SYMBOL_2, abs(btc_amt), params={'reduceOnly': True})