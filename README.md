# Chatbot Deriv - Robô de Operações Automáticas

Este projeto é um robô automatizado para operar na plataforma Deriv, utilizando estratégias baseadas em indicadores técnicos como RSI, SMA, Bollinger Bands e ATR. O bot executa operações de compra e venda de contratos, gerencia o risco com stop loss/take profit dinâmicos e envia notificações via Telegram.

## Funcionalidades

- Conexão automática com a API WebSocket da Deriv.
- Análise de sinais com indicadores técnicos.
- Controle de stake, lucro acumulado, take profit e stop loss diário.
- Limite de operações por dia.
- Notificações automáticas via Telegram.
- Registro dos resultados das operações.

## Estrutura dos Arquivos

- `main.py`: Código principal do robô, responsável pelo loop de operações.
- `deriv_ws.py`: Funções para conexão e comunicação com a API da Deriv.
- `estrategia.py`: Implementação dos indicadores e lógica de sinais.
- `operacoes.py`: Controle de stake e registro de resultados.
- `notificacoes.py`: Envio de mensagens para o Telegram.
- `config.py`: Parâmetros de configuração do robô.

## Como Usar

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/seuusuario/seurepositorio.git
   cd seurepositorio/BOT
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure os parâmetros em `config.py`:**
   - Token da Deriv
   - Token do Telegram
   - Stake inicial, limites de lucro/perda, etc.

4. **Execute o robô:**
   ```bash
   python main.py
   ```

## Observações

- O código é modular e pode ser adaptado para diferentes estratégias.
- Use em conta demo antes de operar com dinheiro real.
- Certifique-se de respeitar os limites e políticas da Deriv.

## Licença

Este projeto é distribuído sob a licença MIT.

---

**Desenvolvido para fins educacionais. Use com responsabilidade!**
