from src.config import UMBRAL_ENTRADA, UMBRAL_SALIDA, UMBRAL_STOP_LOSS, USE_TESTNET
from src.broker import conectar_exchange, consultar_posiciones_abiertas, abrir_arbitraje, cerrar_arbitraje, obtener_saldo_usdt
from src.data_engine import obtener_estado_mercado
from src.notifier import enviar_telegram

def ejecutar_ciclo():
    modo_txt = "🧪 TESTNET" if USE_TESTNET else "🔥 REAL"
    print(f"--- Iniciando ronda de vigilancia ({modo_txt}) ---")
    
    try:
        exchange = conectar_exchange()
        mercado = obtener_estado_mercado(exchange)
        pos = consultar_posiciones_abiertas(exchange)
        
        z = mercado["zscore"]
        estado = pos["estado"]
        
        print(f"[{mercado['timestamp']}] ETH: ${mercado['precio_eth']} | BTC: ${mercado['precio_btc']} | Z-Score: {z} | Estado Posición: {estado}")

        # ==========================================
        # CASO 1: ESTAMOS ADENTRO -> BUSCAR SALIDA
        # ==========================================
        if estado != 0:
            salir_ganancia = (estado == 1 and z >= UMBRAL_SALIDA) or (estado == -1 and z <= UMBRAL_SALIDA)
            salir_emergencia = abs(z) >= UMBRAL_STOP_LOSS

            if salir_ganancia or salir_emergencia:
                motivo = "✅ VUELTA A LA MEDIA (Take Profit)" if salir_ganancia else "🛑 STOP DE EMERGENCIA (Z-Score extremo)"
                pnl_estimado = pos["pnl_flotante"]
                
                cerrar_arbitraje(exchange, pos)
                nuevo_saldo = obtener_saldo_usdt(exchange)
                
                msg = (
                    f"<b>🔔 CIERRE DE ARBITRAJE ({modo_txt})</b>\n"
                    f"<b>Motivo:</b> {motivo}\n"
                    f"<b>Z-Score al cierre:</b> {z}\n"
                    f"<b>PnL Flotante previo:</b> ${pnl_estimado} USD\n"
                    f"<b>Saldo Disponible:</b> ${nuevo_saldo:.2f} USDT"
                )
                enviar_telegram(msg)
            else:
                print(f"⏳ Posición abierta mantenida. PnL actual: ${pos['pnl_flotante']} USD. Esperando que Z={z} vuelva a 0.0")

        # ==========================================
        # CASO 2: ESTAMOS AFUERA -> BUSCAR ENTRADA
        # ==========================================
        else:
            if z <= -UMBRAL_ENTRADA:
                # ETH barato frente a BTC -> Long ETH / Short BTC
                res = abrir_arbitraje(exchange, direccion=1, precio_eth=mercado["precio_eth"], precio_btc=mercado["precio_btc"])
                enviar_telegram(
                    f"<b>🚀 NUEVO DISPARO DE ARBITRAJE ({modo_txt})</b>\n"
                    f"<b>Jugada:</b> {res['jugada']}\n"
                    f"<b>Z-Score detectado:</b> {z}\n"
                    f"<b>Tamaño por pierna:</b> ${res['usd_por_pierna']} USD"
                )
            elif z >= UMBRAL_ENTRADA:
                # ETH caro frente a BTC -> Short ETH / Long BTC
                res = abrir_arbitraje(exchange, direccion=-1, precio_eth=mercado["precio_eth"], precio_btc=mercado["precio_btc"])
                enviar_telegram(
                    f"<b>🚀 NUEVO DISPARO DE ARBITRAJE ({modo_txt})</b>\n"
                    f"<b>Jugada:</b> {res['jugada']}\n"
                    f"<b>Z-Score detectado:</b> {z}\n"
                    f"<b>Tamaño por pierna:</b> ${res['usd_por_pierna']} USD"
                )
            else:
                print(f"😴 Mercado en calma (Z-Score: {z}). Sin señales por encima de ±{UMBRAL_ENTRADA}.")

    except Exception as e:
        enviar_telegram(f"⚠️ <b>ERROR EN BOT DE ARBITRAJE:</b>\n<code>{str(e)}</code>")

if __name__ == "__main__":
    ejecutar_ciclo()