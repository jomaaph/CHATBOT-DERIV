import json
import asyncio
import websockets
from config import DERIV_WS_URL, TOKEN, SYMBOL, DURATION, DURATION_UNIT
from contextlib import asynccontextmanager

async def limpar_fila(ws):
    """
    Esvazia a fila de mensagens do WebSocket antes de cada operação.
    Útil para evitar mensagens antigas interferindo nas operações atuais.
    """
    try:
        while True:
            await asyncio.wait_for(ws.recv(), timeout=0.2)
    except (asyncio.TimeoutError, websockets.ConnectionClosed):
        pass

@asynccontextmanager
async def conectar_deriv():
    """
    Gerencia a conexão WebSocket com a Deriv.
    Uso:
        async with conectar_deriv() as ws:
            # use ws
    """
    ws = await websockets.connect(DERIV_WS_URL)
    try:
        yield ws
    except Exception as e:
        print(f"Erro ao conectar WebSocket: {e}")
        raise
    finally:
        await ws.close()

async def autorizar(ws, max_retries=3):
    """
    Autoriza o token na API Deriv.
    Args:
        ws: conexão websocket ativa.
        max_retries: número máximo de tentativas em caso de timeout.
    Returns:
        dict com resposta da autorização ou vazio em falha.
    """
    for tentativa in range(max_retries):
        await ws.send(json.dumps({"authorize": TOKEN}))
        try:
            response = await asyncio.wait_for(ws.recv(), timeout=10)
            return json.loads(response)
        except asyncio.TimeoutError:
            print(f"Timeout na autorização. Tentativa {tentativa+1}/{max_retries}")
    print("Falha ao autorizar após múltiplas tentativas.")
    return {}

async def obter_candles(ws, count=30, granularity=60, max_retries=3):
    """
    Obtém candles do ativo configurado.
    Args:
        ws: conexão websocket ativa.
        count: quantidade de candles.
        granularity: granularidade em segundos.
        max_retries: número máximo de tentativas em caso de timeout.
    Returns:
        Lista de candles ou vazia em falha.
    """
    for tentativa in range(max_retries):
        await ws.send(json.dumps({
            "ticks_history": SYMBOL,
            "style": "candles",
            "granularity": granularity,
            "count": count,
            "end": "latest"
        }))
        try:
            response = await asyncio.wait_for(ws.recv(), timeout=10)
            data = json.loads(response)
            return data.get("candles", [])
        except asyncio.TimeoutError:
            print(f"Timeout ao obter candles. Tentativa {tentativa+1}/{max_retries}")
    print("Falha ao obter candles após múltiplas tentativas.")
    return []

async def comprar_contrato(ws, direcao, stake):
    """
    Envia ordem de compra de contrato para a Deriv.
    Args:
        ws: conexão websocket ativa.
        direcao: tipo de contrato (ex: 'CALL', 'PUT').
        stake: valor da aposta.
    Returns:
        dict com resposta da compra.
    """
    stake = round(stake, 2)
    await ws.send(json.dumps({
        "buy": 1,
        "price": stake,
        "parameters": {
            "amount": stake,
            "basis": "stake",
            "contract_type": direcao,
            "currency": "USD",
            "duration": DURATION,
            "duration_unit": DURATION_UNIT,
            "symbol": SYMBOL
        }
    }))
    return json.loads(await ws.recv())

async def monitorar_resultado(
    ws, contract_id, stake,
    stop_loss_pct=0.20, take_profit_pct=0.25, max_sell_retries=3
):
    """
    Monitora o resultado do contrato, tentando venda antecipada se atingir stop loss/take profit.
    Args:
        ws: conexão websocket ativa.
        contract_id: id do contrato.
        stake: valor da aposta.
        stop_loss_pct: percentual negativo para stop loss (ex: 0.20 para 20%).
        take_profit_pct: percentual positivo para take profit (ex: 0.25 para 25%).
        max_sell_retries: tentativas de venda antecipada em caso de rejeição.
    Returns:
        Lucro/prejuízo final do contrato.
    """
    # Solicita atualização em tempo real do contrato
    await ws.send(json.dumps({
        "proposal_open_contract": 1,
        "contract_id": contract_id,
        "subscribe": 1
    }))

    contrato_foi_vendido = False
    stop_loss_operacao = -abs(stake) * stop_loss_pct
    take_profit_operacao = abs(stake) * take_profit_pct
    sell_retries = 0
    missing_profit_retries = 0
    MAX_MISSING_PROFIT_RETRIES = 5

    while True:
        msg = json.loads(await ws.recv())

        # Trata mensagens de atualização do contrato
        if msg.get("msg_type") == "proposal_open_contract":
            poc = msg.get("proposal_open_contract", {})
            if poc.get("contract_id") != contract_id:
                continue

            profit = poc.get("profit", 0.0)
            bid_price = poc.get("bid_price", 0.0)

            # Venda antecipada se atingir o stop loss da operação
            if not contrato_foi_vendido and profit <= stop_loss_operacao:
                print("🛑 Stop loss da operação atingido! Vendendo contrato...")
                await ws.send(json.dumps({
                    "sell": contract_id,
                    "price": bid_price
                }))
                contrato_foi_vendido = True

            # Venda antecipada se atingir o take profit da operação
            if not contrato_foi_vendido and profit >= take_profit_operacao:
                print("🎯 Take profit da operação atingido! Vendendo contrato...")
                await ws.send(json.dumps({
                    "sell": contract_id,
                    "price": bid_price
                }))
                contrato_foi_vendido = True

            # Se o contrato foi vendido, retorna o lucro/prejuízo
            if poc.get("is_sold"):
                return poc.get("profit", 0.0)

        # Trata resposta de venda antecipada
        elif msg.get("msg_type") == "sell":
            sell_data = msg.get("sell", {})
            profit = sell_data.get("profit")
            bid_price = sell_data.get("bid_price")
            if sell_data.get("contract_id") == contract_id:
                if profit is not None:
                    print(f"✅ Contrato vendido com lucro: {profit:.2f}")
                    return profit
                elif bid_price is not None:
                    # Calcula lucro manualmente se não informado
                    lucro_manual = bid_price - stake
                    print(f"✅ Contrato vendido, lucro calculado manualmente: {lucro_manual:.2f}")
                    return lucro_manual
                else:
                    # Tentar buscar novamente o status do contrato algumas vezes antes de desistir
                    if missing_profit_retries < MAX_MISSING_PROFIT_RETRIES:
                        print("✅ Contrato vendido, mas lucro não informado e bid_price ausente. Tentando buscar novamente...")
                        await asyncio.sleep(1)
                        await ws.send(json.dumps({
                            "proposal_open_contract": 1,
                            "contract_id": contract_id
                        }))
                        missing_profit_retries += 1
                        continue
                    else:
                        print("✅ Contrato vendido, mas lucro não informado e bid_price ausente após múltiplas tentativas.")
                        return 0.0

        # Trata erros de venda antecipada
        elif msg.get("msg_type") == "error":
            error_info = msg.get("error", {})
            if error_info.get("code") == "InvalidSellProposal":
                print("⚠️ Venda antecipada rejeitada. Tentando novamente...")
                if contrato_foi_vendido and sell_retries < max_sell_retries:
                    # Tenta vender novamente após pequeno delay
                    await asyncio.sleep(1)
                    await ws.send(json.dumps({
                        "sell": contract_id,
                        "price": 0  # preço 0 para aceitar qualquer preço de mercado
                    }))
                    sell_retries += 1
                elif sell_retries >= max_sell_retries:
                    print("❌ Limite de tentativas de venda antecipada atingido. Aguardando encerramento natural do contrato.")
            else:
                print(f"⚠️ Erro inesperado: {error_info}")

        # Mensagens não tratadas
        else:
            print(f"🔎 Mensagem não tratada recebida: {msg}")
