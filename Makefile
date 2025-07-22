# ==========================
# CHATBOT DERIV - Makefile
# ==========================
# Este projeto requer os seguintes tokens e IDs:
# - DERIV_APP_ID: ID do aplicativo Deriv (obrigatório)
# - DERIV_TOKEN_DEMO: Token de autenticação Deriv para conta demo (opcional)
# - DERIV_TOKEN: Token de autenticação Deriv para conta real (opcional)
# - TELEGRAM_TOKEN: Token do bot do Telegram (opcional, para notificações)
# - TELEGRAM_CHAT_ID: ID do chat do Telegram (opcional, para notificações)
#
# Como definir:
# Crie um arquivo .env na raiz do projeto com o seguinte conteúdo:
#
# DERIV_APP_ID=seu_app_id
# DERIV_TOKEN_DEMO=seu_token_demo
# DERIV_TOKEN=seu_token_real
# TELEGRAM_TOKEN=seu_token_telegram
# TELEGRAM_CHAT_ID=seu_chat_id_telegram
#
# ==========================
# Comandos principais
# ==========================

install:
	pip install -r requirements.txt

run:
	python main.py

clean:
	rm -f resultados.csv
	rm -rf __pycache__/
