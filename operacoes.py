import csv
import os
from config import STAKE_INICIAL, CRESCIMENTO

def atualizar_stake(stake_atual, lucro):
    """
    Atualiza o valor do stake para a próxima operação.
    Se houver prejuízo, retorna ao valor inicial.
    Se houver lucro, aumenta o stake conforme o percentual de crescimento.
    """
    if lucro <= 0:
        return STAKE_INICIAL
    else:
        novo_stake = stake_atual * (1 + CRESCIMENTO)
        return round(novo_stake, 2)

def gravar_resultado(data_hora, stake, lucro, lucro_total, resultado):
    """
    Registra o resultado da operação em um arquivo CSV.
    Cria o cabeçalho se o arquivo ainda não existir.
    """
    file_exists = os.path.isfile("resultados.csv")
    with open("resultados.csv", mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Data/Hora", "Stake", "Lucro", "Lucro Total", "Resultado"])
        writer.writerow([data_hora, f"{stake:.2f}", f"{lucro:.2f}", f"{lucro_total:.2f}", resultado])
