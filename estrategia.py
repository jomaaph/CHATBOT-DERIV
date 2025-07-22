from statistics import mean, stdev
from config import RSI_PERIOD, SMA_PERIOD
import numpy as np
import pandas as pd

# Parâmetros ajustáveis para os indicadores técnicos
RSI_OVERBOUGHT = 70  # Limite de sobrecompra para RSI
RSI_OVERSOLD = 30    # Limite de sobrevenda para RSI
SMA_TENDENCIA_PERIOD = 50  # Período da SMA para tendência principal
BOLLINGER_PERIOD = 20      # Período das Bandas de Bollinger
BOLLINGER_MULT = 2         # Multiplicador do desvio padrão para Bollinger

def calcular_rsi(fechamentos, periodo):
    """
    Calcula o RSI (Relative Strength Index) baseado nos fechamentos e período.
    Retorna 50 se não houver dados suficientes.
    """
    if len(fechamentos) < periodo + 1:
        return 50  # Valor neutro se não houver dados suficientes

    # Calcula as diferenças entre fechamentos consecutivos
    deltas = [fechamentos[i] - fechamentos[i - 1] for i in range(-periodo, 0)]
    ganhos = [d for d in deltas if d > 0]
    perdas = [abs(d) for d in deltas if d < 0]

    # Calcula médias de ganhos e perdas
    media_ganhos = mean(ganhos) if ganhos else 0.0001
    media_perdas = mean(perdas) if perdas else 0.0001

    # Calcula o RSI
    rs = media_ganhos / media_perdas if media_perdas != 0 else 0
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calcular_sma(fechamentos, periodo):
    """
    Calcula a Média Móvel Simples (SMA) dos fechamentos.
    """
    return mean(fechamentos[-periodo:])

def calcular_bollinger(fechamentos, periodo=BOLLINGER_PERIOD, mult=BOLLINGER_MULT):
    """
    Calcula as bandas superior e inferior de Bollinger.
    """
    if len(fechamentos) < periodo:
        return None, None
    sma = mean(fechamentos[-periodo:])
    std = stdev(fechamentos[-periodo:])
    upper = sma + mult * std
    lower = sma - mult * std
    return upper, lower

def filtro_tendencia(fechamentos):
    """
    Determina a tendência principal do ativo com base em duas SMAs.
    """
    if len(fechamentos) < SMA_TENDENCIA_PERIOD:
        return None  # Não há dados suficientes
    sma_curta = calcular_sma(fechamentos, SMA_PERIOD)
    sma_longa = calcular_sma(fechamentos, SMA_TENDENCIA_PERIOD)
    if sma_curta > sma_longa:
        return "alta"
    elif sma_curta < sma_longa:
        return "baixa"
    else:
        return "neutra"

def filtro_volatilidade(fechamentos):
    """
    Verifica se a volatilidade está adequada usando a largura das Bandas de Bollinger.
    """
    upper, lower = calcular_bollinger(fechamentos)
    if upper is None or lower is None:
        return False
    banda = upper - lower
    return banda > 0.001  # Ajuste conforme ativo

def candle_confirmacao(candles, direcao, sma):
    """
    Confirma o sinal verificando se o último candle fechou acima/abaixo da SMA.
    """
    if len(candles) < 2:
        return False
    ultimo = float(candles[-1]['close'])
    anterior = float(candles[-2]['close'])
    if direcao == "CALL":
        return anterior < sma and ultimo > sma
    elif direcao == "PUT":
        return anterior > sma and ultimo < sma
    return False

def sinal_entrada(candles,
                  rsi_overbought=RSI_OVERBOUGHT,
                  rsi_oversold=RSI_OVERSOLD):
    """
    Gera o sinal de entrada (CALL/PUT) com base em RSI, SMA, tendência, volatilidade e confirmação de candle.
    Retorna também os valores dos indicadores para logging.
    """
    fechamentos = [float(c['close']) for c in candles]
    preco_atual = fechamentos[-1]
    rsi = calcular_rsi(fechamentos, RSI_PERIOD)
    sma = calcular_sma(fechamentos, SMA_PERIOD)
    tendencia = filtro_tendencia(fechamentos)
    volatilidade_ok = filtro_volatilidade(fechamentos)
    upper, lower = calcular_bollinger(fechamentos)

    # Sinal base RSI + SMA
    direcao = None
    if rsi <= rsi_oversold and preco_atual > sma:
        direcao = "CALL"
    elif rsi >= rsi_overbought and preco_atual < sma:
        direcao = "PUT"

    # Filtros adicionais: tendência, volatilidade e confirmação de candle
    if not direcao:
        return None, rsi, sma, preco_atual, tendencia, upper, lower

    if (direcao == "CALL" and tendencia != "alta") or (direcao == "PUT" and tendencia != "baixa"):
        return None, rsi, sma, preco_atual, tendencia, upper, lower

    if not volatilidade_ok:
        return None, rsi, sma, preco_atual, tendencia, upper, lower

    if not candle_confirmacao(candles, direcao, sma):
        return None, rsi, sma, preco_atual, tendencia, upper, lower

    return direcao, rsi, sma, preco_atual, tendencia, upper, lower

def calcular_ema(valores, periodo):
    """
    Calcula a Média Móvel Exponencial (EMA) de uma lista de valores.
    """
    pesos = np.exp(np.linspace(-1., 0., periodo))
    pesos /= pesos.sum()
    a = np.convolve(valores, pesos, mode='valid')
    return a[-1]

def calcular_rsi_ema(fechamentos, periodo):
    """
    Calcula o RSI usando médias móveis exponenciais (EMA).
    """
    if len(fechamentos) < periodo + 1:
        return 50
    serie = pd.Series(fechamentos)
    delta = serie.diff()
    ganhos = delta.clip(lower=0)
    perdas = -delta.clip(upper=0)
    media_ganhos = ganhos.ewm(span=periodo, adjust=False).mean()
    media_perdas = perdas.ewm(span=periodo, adjust=False).mean()
    rs = media_ganhos / (media_perdas + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def calcular_atr(candles, periodo=14):
    """
    Calcula o ATR (Average True Range) para medir a volatilidade do ativo.
    """
    if len(candles) < periodo + 1:
        return None
    trs = []
    for i in range(-periodo, 0):
        high = float(candles[i]['high'])
        low = float(candles[i]['low'])
        prev_close = float(candles[i-1]['close'])
        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )
        trs.append(tr)
    return sum(trs) / len(trs)

