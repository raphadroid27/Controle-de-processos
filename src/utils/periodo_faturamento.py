"""
Módulo de lógica de negócio para períodos de faturamento.

Contém funções para calcular períodos de faturamento e aplicar
filtros baseados nas regras da empresa.
"""

from datetime import datetime


def _calcular_periodo_faturamento_base(data: datetime):
    """
    Função auxiliar que calcula o período de faturamento para qualquer data.
    """
    if data.day >= 26:
        # Se o dia é 26 ou depois, o período é do próximo mês
        if data.month == 12:
            mes_faturamento = 1
            ano_faturamento = data.year + 1
        else:
            mes_faturamento = data.month + 1
            ano_faturamento = data.year
    else:
        # Se o dia é antes do 26, o período é do mês atual
        mes_faturamento = data.month
        ano_faturamento = data.year

    return mes_faturamento, ano_faturamento


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
    mes_faturamento, ano_faturamento = _calcular_periodo_faturamento_base(hoje)

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
    mes_faturamento, ano_faturamento = _calcular_periodo_faturamento_base(hoje)

    # Calcular datas baseado no período
    if hoje.day >= 26:
        # Período atual: 26/MM a 25/(MM+1)
        inicio_mes = hoje.month
        inicio_ano = hoje.year
        fim_mes = mes_faturamento
        fim_ano = ano_faturamento
    else:
        # Período anterior: 26/(MM-1) a 25/MM
        fim_mes = hoje.month
        fim_ano = hoje.year
        if mes_faturamento == 1:
            inicio_mes = 12
            inicio_ano = ano_faturamento - 1
        else:
            inicio_mes = mes_faturamento - 1
            inicio_ano = ano_faturamento

    data_inicio = datetime(inicio_ano, inicio_mes, 26)
    data_fim = datetime(fim_ano, fim_mes, 25)

    return data_inicio, data_fim


def calcular_periodo_faturamento_para_data(data: datetime):
    """
    Calcula o período de faturamento para uma data específica.

    Aplica a mesma regra: do dia 26 do mês anterior até o dia 25 do mês corrente.
    """
    mes_faturamento, ano_faturamento = _calcular_periodo_faturamento_base(data)

    # Retornar mês formatado com zero à esquerda
    mes_formatado = f"{mes_faturamento:02d}"
    ano_formatado = str(ano_faturamento)

    return mes_formatado, ano_formatado


def calcular_periodo_faturamento_para_data_datas(data: datetime):
    """
    Calcula as datas de início e fim do período de faturamento para uma data específica.
    Retorna objetos datetime para facilitar manipulação.
    """
    mes_faturamento, ano_faturamento = _calcular_periodo_faturamento_base(data)

    # Calcular datas baseado no período
    if data.day >= 26:
        # Período: 26/MM a 25/(MM+1)
        inicio_mes = data.month
        inicio_ano = data.year
        fim_mes = mes_faturamento
        fim_ano = ano_faturamento
    else:
        # Período: 26/(MM-1) a 25/MM
        fim_mes = data.month
        fim_ano = data.year
        if mes_faturamento == 1:
            inicio_mes = 12
            inicio_ano = ano_faturamento - 1
        else:
            inicio_mes = mes_faturamento - 1
            inicio_ano = ano_faturamento

    data_inicio = datetime(inicio_ano, inicio_mes, 26)
    data_fim = datetime(fim_ano, fim_mes, 25)

    return data_inicio, data_fim
