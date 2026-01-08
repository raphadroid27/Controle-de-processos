"""Camada de lógica de negócio central."""

from src.core.formatters import (formatar_data_para_exibicao,
                                 formatar_valor_monetario,
                                 normalizar_nome_cliente,
                                 normalizar_valor_padrao_brasileiro,
                                 segundos_para_horas)
from src.core.periodo_faturamento import (
    calcular_periodo_faturamento_atual_datas,
    calcular_periodo_faturamento_para_data,
    calcular_periodo_faturamento_para_data_datas)
from src.core.tempo_corte import (normalizar_tempo_corte,
                                  tempo_corte_para_segundos)

__all__ = [
    # Formatters
    "formatar_data_para_exibicao",
    "formatar_valor_monetario",
    "normalizar_nome_cliente",
    "normalizar_valor_padrao_brasileiro",
    "segundos_para_horas",
    # Período de faturamento
    "calcular_periodo_faturamento_atual_datas",
    "calcular_periodo_faturamento_para_data",
    "calcular_periodo_faturamento_para_data_datas",
    # Tempo de corte
    "normalizar_tempo_corte",
    "tempo_corte_para_segundos",
]
