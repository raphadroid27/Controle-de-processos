"""Serviços auxiliares de dados utilizados pelo :mod:`processos_widget`."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy.exc import SQLAlchemyError

from ...utils import database as db
from ...utils.periodo_faturamento import \
    calcular_periodo_faturamento_atual_datas

__all__ = [
    "carregar_clientes_upper",
    "listar_anos_disponiveis",
    "listar_periodos_do_ano",
    "buscar_registros_filtrados",
    "obter_estatisticas_totais",
]


def carregar_clientes_upper() -> List[str]:
    """Retorna a lista de clientes conhecidos em caixa alta."""

    try:
        clientes_raw = db.buscar_clientes_unicos()
    except (SQLAlchemyError, RuntimeError, AttributeError, TypeError) as exc:
        print(f"Erro ao carregar clientes: {exc}")
        return []
    return [cliente.upper() for cliente in clientes_raw]


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
        print(f"Erro ao buscar anos únicos: {exc}")
        anos = []

    data_inicio_atual, _ = calcular_periodo_faturamento_atual_datas()
    ano_atual = str(data_inicio_atual.year)
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
        print(f"Erro ao buscar períodos de faturamento: {exc}")
        return []

    data_inicio_atual, data_fim_atual = calcular_periodo_faturamento_atual_datas()
    ano_atual = str(data_inicio_atual.year)

    if ano == ano_atual:
        inicio_atual_fmt = data_inicio_atual.strftime("%d/%m")
        fim_atual_fmt = data_fim_atual.strftime("%d/%m")
        periodo_atual_display = f"{inicio_atual_fmt} a {fim_atual_fmt}"
        periodo_atual_existe = any(
            periodo.get("display") == periodo_atual_display for periodo in periodos
        )
        if not periodo_atual_existe:
            periodos.insert(
                0,
                {
                    "display": periodo_atual_display,
                    "inicio": data_inicio_atual.strftime("%Y-%m-%d"),
                    "fim": data_fim_atual.strftime("%Y-%m-%d"),
                },
            )

    return periodos


def _ordenacao_chave(registro: Sequence[Any]) -> tuple[datetime, datetime]:
    """Chave de ordenação utilizada para ordenar registros."""

    data_processo = registro[6]
    data_lancamento = registro[9]

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
        print(f"Erro ao converter timestamp '{data_lancamento}': {exc}")
        timestamp_obj = datetime.min

    if not data_processo:
        return (datetime.min, timestamp_obj)

    try:
        data_processo_obj = datetime.strptime(str(data_processo), "%Y-%m-%d")
        return (data_processo_obj, timestamp_obj)
    except ValueError:
        return (datetime.min, timestamp_obj)


def buscar_registros_filtrados(
    *,
    usuario: Optional[str],
    cliente: Optional[str],
    processo: Optional[str],
    data_inicio: Optional[str],
    data_fim: Optional[str],
) -> List[Sequence[Any]]:
    """Busca registros no banco aplicando filtros e os devolve ordenados."""

    try:
        registros = db.buscar_lancamentos_filtros_completos(
            usuario=usuario,
            cliente=cliente,
            processo=processo,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )
    except (
        SQLAlchemyError,
        RuntimeError,
        AttributeError,
        TypeError,
        ValueError,
    ) as exc:
        print(f"Erro ao buscar registros filtrados: {exc}")
        registros = []

    return sorted(registros, key=_ordenacao_chave)


def obter_estatisticas_totais(
    filtros: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Obtém os totais agregados aplicando filtros opcionais."""

    filtros = filtros or {}

    try:
        return db.buscar_estatisticas_completas(
            usuario=filtros.get("usuario"),
            cliente=filtros.get("cliente"),
            processo=filtros.get("processo"),
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
        print(f"Erro ao buscar estatísticas: {exc}")
        return {"total_processos": 0, "total_itens": 0, "total_valor": 0.0}
