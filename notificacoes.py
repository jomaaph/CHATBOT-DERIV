# BOT/notificacoes.py
import aiohttp
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

async def enviar_telegram(mensagem):
    """
    Envia uma mensagem para um chat do Telegram usando a API do bot.
    Requer que TELEGRAM_TOKEN e TELEGRAM_CHAT_ID estejam definidos nas configurações.
    
    Args:
        mensagem (str): Texto a ser enviado para o Telegram.
    """
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ TELEGRAM_TOKEN ou TELEGRAM_CHAT_ID não definidos.")
        return

    # Monta a URL da API do Telegram e o payload da mensagem
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem
    }

    try:
        # Cria uma sessão HTTP assíncrona para enviar a mensagem
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload) as resp:
                if resp.status != 200:
                    print("❌ Falha ao enviar para o Telegram:", await resp.text())
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem para o Telegram: {e}")
