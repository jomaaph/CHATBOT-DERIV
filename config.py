import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Identificador do aplicativo Deriv (obrigatório para autenticação)
APP_ID = os.getenv("DERIV_APP_ID")
# Token de autenticação da Deriv (prioriza demo, senão usa real)
TOKEN = os.getenv("DERIV_TOKEN_DEMO") or os.getenv("DERIV_TOKEN")
# URL do WebSocket da Deriv, já incluindo o app_id
DERIV_WS_URL = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"

# Símbolo do ativo a ser operado (exemplo: índice sintético 100)
SYMBOL = "R_100"
# Valor de referência diário para cálculo de limites
VALOR_DIARIO = 2500.0
# Valor inicial do stake em cada operação
STAKE_INICIAL = 100
# Percentual de crescimento do stake após vitória
CRESCIMENTO = 0.05 # 5% de crescimento por operação

# Limites de risco: Stop Loss e Take Profit diários
STOP_LOSS = -VALOR_DIARIO * 0.20  # Exemplo: -20% do valor diário
TAKE_PROFIT = VALOR_DIARIO * 0.5  # Exemplo: +50% do valor diário

# Duração do contrato em minutos e unidade de tempo
DURATION = 5 # duração do contrato em minutos
DURATION_UNIT = "m"

# Granularidade dos candles em segundos (ex: 60 = 1 minuto)
GRANULARITY = int(os.getenv("GRANULARITY", 60))

# Períodos dos indicadores técnicos
RSI_PERIOD = 14
SMA_PERIOD = 10

# Configurações do Telegram para envio de notificações
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

