/robo_deriv
│
├── main.py                   # Ponto de entrada
├── config.py                 # Configurações e variáveis globais
├── deriv_ws.py               # Conexão e funções WebSocket da Deriv
├── estrategia.py             # Cálculo de RSI, SMA, Bollinger e lógica de entrada
├── operacoes.py              # Compra, venda, gestão de lucro/stake
├── notificacoes.py           # Integração com Telegram
├── utils.py                  # Funções auxiliares (tempo, formatação, gravação CSV)
├── .env                      # Tokens e configuração sensível
└── resultados.csv            # Log das operações
