"""
Módulo de lógica de negócio para períodos de faturamento.

Contém funções para calcular períodos de faturamento e aplicar filtros baseados nas regras da empresa.
"""

from datetime import datetime


def calcular_periodo_faturamento_atual():
    """
    Calcula o período de faturamento atual baseado na regra da empresa:
    Do dia 26 do mês anterior até o dia 25 do mês corrente.

    Exemplos:
    - Se hoje é 06/08/2025: período = agosto/2025 (26/07 a 25/08)
    - Se hoje é 25/08/2025: período = agosto/2025 (ainda no período atual)
    - Se hoje é 26/08/2025: período = setembro/2025 (novo período iniciou)
    - Se hoje é 24/08/2025: período = agosto/2025 (ainda no período atual)

    O período de faturamento sempre corresponde ao mês onde o dia 25 está incluído.

    Retorna o mês e ano que devem ser filtrados.
    """
    hoje = datetime.now()

    if hoje.day >= 26:
        # Se hoje é 26 ou depois, o período é do próximo mês
        # Exemplo: 26/08 = período setembro (26/08 a 25/09)
        if hoje.month == 12:
            # Dezembro -> período de janeiro do próximo ano
            mes_faturamento = 1
            ano_faturamento = hoje.year + 1
        else:
            mes_faturamento = hoje.month + 1
            ano_faturamento = hoje.year
    else:
        # Se hoje é antes do dia 26, o período é do mês atual
        # Exemplo: 06/08 = período agosto (26/07 a 25/08)
        mes_faturamento = hoje.month
        ano_faturamento = hoje.year

    # Retornar mês formatado com zero à esquerda
    mes_formatado = f"{mes_faturamento:02d}"
    ano_formatado = str(ano_faturamento)

    return mes_formatado, ano_formatado


def calcular_periodo_faturamento_atual_datas():
    """
    Calcula as datas de início e fim do período de faturamento atual.
    Retorna objetos datetime para facilitar manipulação.
    """
    hoje = datetime.now()

    if hoje.day >= 26:
        # Período atual: 26/MM a 25/(MM+1)
        inicio_mes = hoje.month
        inicio_ano = hoje.year

        # Calcular mês seguinte
        if inicio_mes == 12:
            fim_mes = 1
            fim_ano = inicio_ano + 1
        else:
            fim_mes = inicio_mes + 1
            fim_ano = inicio_ano
    else:
        # Período anterior: 26/(MM-1) a 25/MM
        fim_mes = hoje.month
        fim_ano = hoje.year

        # Calcular mês anterior
        if fim_mes == 1:
            inicio_mes = 12
            inicio_ano = fim_ano - 1
        else:
            inicio_mes = fim_mes - 1
            inicio_ano = fim_ano

    data_inicio = datetime(inicio_ano, inicio_mes, 26)
    data_fim = datetime(fim_ano, fim_mes, 25)

    return data_inicio, data_fim
