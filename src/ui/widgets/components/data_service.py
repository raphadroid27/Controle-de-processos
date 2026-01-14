"""Serviços auxiliares de dados utilizados pelo :mod:`pedidos_widget`."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy.exc import SQLAlchemyError

from src import data as db
from src.core.formatters import normalizar_nome_cliente
from src.core.periodo_faturamento import \
    calcular_periodo_faturamento_atual_datas

__all__ = [
    "carregar_clientes_upper",
    "EstatisticasTotais",
    "listar_anos_disponiveis",
    "listar_periodos_do_ano",
    "buscar_registros_filtrados",
    "obter_estatisticas_totais",
]


logger = logging.getLogger(__name__)


@dataclass
class EstatisticasTotais:
    """Estrutura agregadora para exibir métricas no painel de totais."""

    total_pedidos: int
    total_itens: int
    total_valor: float
    media_dias_processo: float | None
    media_itens_por_dia: float | None
    estimativa_itens_mes: int | None
    tempo_corte_total: str | None
    media_tempo_corte_dia: str | None
    tempo_corte_dia: str | None


def carregar_clientes_upper() -> List[str]:
    """Retorna a lista de clientes conhecidos em caixa alta."""

    try:
        clientes_raw = db.buscar_clientes_unicos()
    except (SQLAlchemyError, RuntimeError, AttributeError, TypeError) as exc:
        logger.exception("Erro ao carregar clientes: %s", exc)
        return []
    clientes_normalizados = {
        normalizar_nome_cliente(cliente)
        for cliente in clientes_raw
        if normalizar_nome_cliente(cliente)
    }
    return sorted(clientes_normalizados)


def listar_anos_disponiveis(usuario_filtro: Optional[str]) -> List[str]:
    """Retorna a lista de anos disponíveis para filtragem."""

    try:
        anos = db.buscar_anos_unicos(usuario_filtro)
    except (
        SQLAlchemyError,
        RuntimeError,
        AttributeError,
        TypeError,
        ValueError,
    ) as exc:
        logger.exception("Erro ao buscar anos únicos: %s", exc)
        anos = []

    _, data_fim_atual = calcular_periodo_faturamento_atual_datas()
    ano_atual = str(data_fim_atual.year)
    if ano_atual not in anos:
        anos.append(ano_atual)

    anos.sort(reverse=True)
    return anos


def listar_periodos_do_ano(
    ano: str,
    usuario_filtro: Optional[str],
) -> List[Dict[str, str]]:
    """Retorna os períodos de faturamento disponíveis para um ano."""

    if ano == "Todos os anos":
        return []

    try:
        periodos = db.buscar_periodos_faturamento_por_ano(ano, usuario_filtro)
    except (
        SQLAlchemyError,
        RuntimeError,
        AttributeError,
        TypeError,
        ValueError,
    ) as exc:
        logger.exception("Erro ao buscar períodos de faturamento: %s", exc)
        return []

    _, data_fim_atual = calcular_periodo_faturamento_atual_datas()
    ano_atual = str(data_fim_atual.year)

    if ano == ano_atual:
        db.garantir_periodo_atual(periodos)

    return periodos


def _ordenacao_chave(registro: Sequence[Any]) -> tuple[datetime, datetime]:
    """Chave de ordenação utilizada para ordenar registros."""

    data_processo = registro[6]
    data_entrada = registro[5]
    data_lancamento = registro[10]

    try:
        if data_lancamento:
            if "T" in str(data_lancamento):
                timestamp_obj = datetime.fromisoformat(
                    str(data_lancamento).replace("Z", "")
                )
            else:
                timestamp_obj = datetime.strptime(
                    str(data_lancamento), "%Y-%m-%d %H:%M:%S"
                )
        else:
            timestamp_obj = datetime.min
    except (ValueError, AttributeError) as exc:
        logger.exception(
            "Erro ao converter timestamp '%s': %s",
            data_lancamento,
            exc,
        )
        timestamp_obj = datetime.min

    # Usar data_processo se existir, senão data_entrada
    data_para_ordenacao = data_processo or data_entrada

    if not data_para_ordenacao:
        return (datetime.min, timestamp_obj)

    try:
        data_obj = datetime.strptime(str(data_para_ordenacao), "%Y-%m-%d")
        return (data_obj, timestamp_obj)
    except ValueError:
        return (datetime.min, timestamp_obj)


def buscar_registros_filtrados(
    *,
    usuario: Optional[str],
    cliente: Optional[str],
    pedido: Optional[str],
    data_inicio: Optional[str],
    data_fim: Optional[str],
    limite: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[Sequence[Any]]:
    """Busca registros no banco aplicando filtros e os devolve ordenados."""

    try:
        registros = db.buscar_lancamentos_filtros_completos(
            usuario=usuario,
            cliente=cliente,
            pedido=pedido,
            data_inicio=data_inicio,
            data_fim=data_fim,
            limite=limite,
            offset=offset,
        )
    except (
        SQLAlchemyError,
        RuntimeError,
        AttributeError,
        TypeError,
        ValueError,
    ) as exc:
        logger.exception("Erro ao buscar registros filtrados: %s", exc)
        registros = []

    # Se estiver filtrando por um usuário específico, o banco já retorna ordenado
    # via ORDER BY COALESCE(data_processo, data_entrada)
    if usuario:
        return list(registros)

    return sorted(registros, key=_ordenacao_chave)


def _parse_data(valor: Any) -> date | None:
    if not valor:
        return None
    try:
        return datetime.strptime(str(valor), "%Y-%m-%d").date()
    except ValueError:
        return None


def _obter_limites_periodo(
    filtros: Dict[str, Any],
    registros: Sequence[Sequence[Any]],
) -> tuple[date | None, date | None]:
    inicio = _parse_data(filtros.get("data_inicio"))
    fim = _parse_data(filtros.get("data_fim"))

    if inicio is None:
        datas_inicio = [_parse_data(reg[5]) for reg in registros]
        datas_inicio = [data for data in datas_inicio if data is not None]
        if datas_inicio:
            inicio = min(datas_inicio)

    if fim is None:
        datas_fim = [_parse_data(reg[6]) for reg in registros]
        datas_fim = [data for data in datas_fim if data is not None]
        if datas_fim:
            fim = max(datas_fim)
        elif inicio is not None:
            fim = inicio

    return inicio, fim


def _dias_uteis_entre(inicio: date | None, fim: date | None) -> int:
    if inicio is None or fim is None or fim < inicio:
        return 0

    dias = 0
    atual = inicio
    while atual <= fim:
        if atual.weekday() < 5:
            dias += 1
        atual += timedelta(days=1)
    return dias


def _calcular_media_dias_processo(
    registros: Sequence[Sequence[Any]],
) -> float | None:
    diferencas: list[int] = []
    for registro in registros:
        data_entrada = _parse_data(registro[5])
        data_processo = _parse_data(registro[6])
        if data_entrada is None or data_processo is None:
            continue
        delta = (data_processo - data_entrada).days
        if delta >= 0:
            diferencas.append(delta)

    if not diferencas:
        return None
    return sum(diferencas) / len(diferencas)


def _calcular_media_itens_por_dia(
    total_itens: int,
    dias_uteis_decorridos: int,
) -> float | None:
    if total_itens <= 0 or dias_uteis_decorridos <= 0:
        return None
    return total_itens / dias_uteis_decorridos


def _calcular_estimativa_itens_mes(
    media_itens_por_dia: float | None,
    dias_uteis_periodo: int,
) -> int | None:
    if media_itens_por_dia is None or dias_uteis_periodo <= 0:
        return None
    return int(round(media_itens_por_dia * dias_uteis_periodo))


def _somar_tempo_processado_no_dia(
    registros: Sequence[Sequence[Any]],
    referencia: date,
) -> int:
    total_segundos = 0
    referencia_str = referencia.strftime("%Y-%m-%d")

    for registro in registros:
        data_processo = registro[6]
        tempo_corte = registro[7]

        if not data_processo or data_processo != referencia_str:
            continue
        if not tempo_corte:
            continue

        partes = tempo_corte.split(":")
        if len(partes) != 3:
            continue
        try:
            horas, minutos, segundos = (int(p) for p in partes)
        except ValueError:
            continue

        total_segundos += horas * 3600 + minutos * 60 + segundos

    return total_segundos


def _formatar_segundos_para_horas(total_segundos: int) -> str | None:
    if total_segundos <= 0:
        return None

    horas = total_segundos // 3600
    minutos = (total_segundos % 3600) // 60
    segundos = total_segundos % 60

    if segundos:
        return f"{horas:02d}h {minutos:02d}m {segundos:02d}s"
    if minutos:
        return f"{horas:02d}h {minutos:02d}m"
    return f"{horas:02d}h"


def _calcular_metricas_tempo_dashboard(
    registros: Sequence[Sequence[Any]],
) -> tuple[int, int]:
    """Calcula total de segundos e dias únicos com apontamento (lógica dashboard)."""
    total_segundos = 0
    dias_com_apontamento: set[str] = set()

    for registro in registros:
        # Indices baseados em buscar_lancamentos_filtros_completos
        data_entrada = registro[5]
        data_processo = registro[6]
        tempo_corte = registro[7]

        if not tempo_corte:
            continue

        partes = tempo_corte.split(":")
        if len(partes) != 3:
            continue
        try:
            horas, minutos, segundos = (int(p) for p in partes)
        except ValueError:
            continue

        segundos_reg = horas * 3600 + minutos * 60 + segundos

        # Só conta para a média se houver tempo apontado
        if segundos_reg > 0:
            total_segundos += segundos_reg

            # Determina o dia do apontamento (Processo ou Entrada)
            data_base = data_processo or data_entrada
            if data_base:
                dias_com_apontamento.add(str(data_base))

    return total_segundos, len(dias_com_apontamento)


def obter_estatisticas_totais(
    filtros: Optional[Dict[str, Any]] = None,
) -> EstatisticasTotais:
    """Obtém os totais agregados e métricas derivadas para o painel."""

    filtros = filtros or {}

    try:
        registros = buscar_registros_filtrados(
            usuario=filtros.get("usuario"),
            cliente=filtros.get("cliente"),
            pedido=filtros.get("pedido"),
            data_inicio=filtros.get("data_inicio"),
            data_fim=filtros.get("data_fim"),
        )

        totais = db.buscar_estatisticas_completas(
            usuario=filtros.get("usuario"),
            cliente=filtros.get("cliente"),
            pedido=filtros.get("pedido"),
            data_inicio=filtros.get("data_inicio"),
            data_fim=filtros.get("data_fim"),
        )
    except (
        SQLAlchemyError,
        RuntimeError,
        AttributeError,
        TypeError,
        ValueError,
    ) as exc:
        logger.exception("Erro ao buscar estatísticas: %s", exc)
        return EstatisticasTotais(0, 0, 0.0, None, None, None, None, None, None)

    periodo_inicio, periodo_fim = _obter_limites_periodo(filtros, registros)

    fim_para_media = date.today()
    if periodo_fim is not None:
        fim_para_media = min(periodo_fim, fim_para_media)

    dias_uteis_decorridos = _dias_uteis_entre(periodo_inicio, fim_para_media)
    dias_uteis_periodo = _dias_uteis_entre(periodo_inicio, periodo_fim)

    media_dias = _calcular_media_dias_processo(registros)
    media_por_dia = _calcular_media_itens_por_dia(
        int(totais.get("total_itens", 0)),
        dias_uteis_decorridos,
    )
    total_segundos_dia = _somar_tempo_processado_no_dia(
        registros,
        date.today(),
    )
    tempo_corte_dia = _formatar_segundos_para_horas(total_segundos_dia)

    total_segundos_total, dias_com_horas = _calcular_metricas_tempo_dashboard(
        registros)
    tempo_corte_total = _formatar_segundos_para_horas(total_segundos_total)

    media_tempo_corte_dia = None
    if dias_com_horas > 0 and total_segundos_total > 0:
        media_segundos = int(total_segundos_total / dias_com_horas)
        media_tempo_corte_dia = _formatar_segundos_para_horas(media_segundos)

    # Estimativa baseada na média do período filtrado
    # multiplicada pelos dias úteis do período filtrado
    estimativa = _calcular_estimativa_itens_mes(
        media_por_dia,
        dias_uteis_periodo,
    )

    return EstatisticasTotais(
        total_pedidos=totais.get("total_pedidos", 0),
        total_itens=totais.get("total_itens", 0),
        total_valor=totais.get("total_valor", 0.0),
        media_dias_processo=media_dias,
        media_itens_por_dia=media_por_dia,
        estimativa_itens_mes=estimativa,
        tempo_corte_total=tempo_corte_total,
        media_tempo_corte_dia=media_tempo_corte_dia,
        tempo_corte_dia=tempo_corte_dia,
    )
