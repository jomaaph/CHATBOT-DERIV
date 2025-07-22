# Importa funções de módulos locais para lidar com WebSocket da Deriv, estratégias, operações, notificações e configurações
from deriv_ws import conectar_deriv, obter_candles, autorizar, comprar_contrato, monitorar_resultado, limpar_fila
from estrategia import sinal_entrada, calcular_atr
from operacoes import atualizar_stake, gravar_resultado
from notificacoes import enviar_telegram
from config import (
    STAKE_INICIAL, CRESCIMENTO, TAKE_PROFIT, STOP_LOSS,
    RSI_PERIOD, SMA_PERIOD, GRANULARITY
)

import asyncio
from datetime import datetime

# Variáveis globais para controle do lucro total e stake atual
lucro_total = 0
stake_atual = STAKE_INICIAL

# Limite de operações por dia para evitar excesso de trades
LIMITE_OPERACOES = 20
operacoes_realizadas = 0

# Função principal assíncrona que executa o robô
async def run_bot():
    global lucro_total, stake_atual, operacoes_realizadas
    # Conecta ao WebSocket da Deriv
    async with conectar_deriv() as ws:
        # Autoriza a conta e envia notificação de início
        auth = await autorizar(ws)
        print("✅ Login autorizado:", auth["authorize"]["loginid"])
        await enviar_telegram(f"🤖 Robô iniciado: conta {auth['authorize']['loginid']}")

        # Loop principal: executa enquanto não atinge o take profit ou stop loss
        while lucro_total < TAKE_PROFIT and lucro_total > STOP_LOSS:
            # Checagem extra para garantir parada imediata em caso de stop loss
            if lucro_total <= STOP_LOSS:
                print("\n💸 STOP LOSS diário ultrapassado! Encerrando operações.")
                await enviar_telegram("💸 STOP LOSS diário ultrapassado! Robô encerrado.")
                break

            # Verifica se atingiu o limite diário de operações
            if operacoes_realizadas >= LIMITE_OPERACOES:
                print("🔒 Limite diário de operações atingido.")
                await enviar_telegram("🔒 Limite diário de operações atingido. Robô pausado.")
                break

            # Define o período máximo necessário para os indicadores
            max_period = max(50, 20, RSI_PERIOD, SMA_PERIOD) + 2  # 50 = SMA_TENDENCIA_PERIOD, 20 = BOLLINGER_PERIOD
            # Obtém candles históricos para análise
            candles = await obter_candles(ws, max_period, granularity=GRANULARITY)
            if not candles:
                continue

            # Calcula os sinais de entrada e indicadores técnicos
            direcao, rsi, sma, preco, tendencia, boll_upper, boll_lower = sinal_entrada(candles)
            boll_upper_str = f"{boll_upper:.5f}" if boll_upper is not None else "N/A"
            boll_lower_str = f"{boll_lower:.5f}" if boll_lower is not None else "N/A"
            print(f"📈 RSI: {rsi:.2f} | SMA: {sma:.5f} | Preço: {preco:.5f} | Tendência: {tendencia} | Bollinger: [{boll_lower_str}, {boll_upper_str}]")

            # Se não houver sinal claro, aguarda e repete o loop
            if not direcao:
                print("🔸 Sem sinal claro ou filtros não aprovados. Aguardando...")
                await asyncio.sleep(5)
                continue

            # --- ATR para SL/TP dinâmicos ---
            # Calcula o ATR para definir stop loss e take profit dinâmicos
            atr = calcular_atr(candles, periodo=14)
            if atr is not None and preco > 0:
                sl_atr = atr * 1.5  # Ajuste conforme seu perfil de risco
                tp_atr = atr * 2.0
                stop_loss_pct = sl_atr / preco
                take_profit_pct = tp_atr / preco
            else:
                print("❌ Não foi possível calcular o ATR. Pulando operação.")
                await asyncio.sleep(3)
                continue

            print(f"ATR: {atr:.5f}")
            print(f"SL%: {stop_loss_pct:.4f} | TP%: {take_profit_pct:.4f}")

            # Envia notificação de sinal de compra
            print(f"🟢 SINAL DE COMPRA — {direcao} com stake: {stake_atual:.2f}")
            await enviar_telegram(
                f"🟢 SINAL DE COMPRA — {direcao} | Stake: {stake_atual:.2f}\n"
                f"RSI: {rsi:.2f} | SMA: {sma:.5f} | Tendência: {tendencia}\n"
                f"Bollinger: [{boll_lower_str}, {boll_upper_str}]"
            )

            # Limpa a fila de operações pendentes antes de comprar
            await limpar_fila(ws)

            # Realiza a compra do contrato
            compra = await comprar_contrato(ws, direcao, stake_atual)
            if "error" in compra:
                print("❌ Erro na compra:", compra["error"]["message"])
                await enviar_telegram(f"❌ Erro na compra: {compra['error']['message']}")
                await asyncio.sleep(3)
                continue

            # Verifica se a resposta da compra é válida
            if "buy" not in compra or "contract_id" not in compra["buy"]:
                print("❌ Erro: resposta inesperada ao comprar contrato:", compra)
                await enviar_telegram(f"❌ Erro: resposta inesperada ao comprar contrato: {compra}")
                await asyncio.sleep(3)
                continue

            # Obtém o ID do contrato comprado
            contract_id = compra["buy"]["contract_id"]
            # Monitora o resultado do contrato até o fim ou atingir SL/TP
            lucro = await monitorar_resultado(
                ws, contract_id, stake_atual,
                stop_loss_pct=stop_loss_pct,
                take_profit_pct=take_profit_pct
            )
            # Atualiza o lucro total
            lucro_total += lucro

            # Define o resultado da operação e registra
            resultado = "✅ GANHO" if lucro > 0 else "❌ PERDA"
            data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"{resultado} | Lucro: {lucro:.2f} | Total acumulado: {lucro_total:.2f}")
            await enviar_telegram(f"{resultado} | Lucro: {lucro:.2f} | Total: {lucro_total:.2f}")

            # Grava o resultado da operação em arquivo ou banco de dados
            gravar_resultado(
                data_hora, stake_atual, lucro, lucro_total, resultado
                # Adicione mais campos se desejar, ex: rsi, sma, tendencia, etc.
            )
            # Atualiza o valor do stake para próxima operação
            stake_atual = atualizar_stake(stake_atual, lucro)
            # Incrementa o contador de operações realizadas
            operacoes_realizadas += 1
            # Aguarda um tempo antes da próxima operação
            await asyncio.sleep(2)

        # Mensagem final ao encerrar o robô
        print("\n🏁 Robô finalizado!")
        msg_final = "🎯 TAKE PROFIT diário atingido!" if lucro_total >= TAKE_PROFIT else "💸 STOP LOSS diário atingido!"
        print(msg_final)
        await enviar_telegram("🏁 Robô finalizado! " + msg_final)

# Executa o robô se o script for chamado diretamente
if __name__ == "__main__":
    asyncio.run(run_bot())
