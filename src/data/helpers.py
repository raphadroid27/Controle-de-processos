"""Funções auxiliares para validação e formatação de lançamentos."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, Optional

from src.core.tempo_corte import normalizar_tempo_corte
from src.data.models import Lancamento


def parse_iso_date(value: Optional[str]) -> Optional[date]:
    """Converte string ISO (YYYY-MM-DD) ou DD/MM/YYYY para date.

    Args:
        value: String com data no formato YYYY-MM-DD ou DD/MM/YYYY

    Returns:
        Objeto date ou None se a conversão falhar ou valor for vazio

    Examples:
        >>> parse_iso_date("2025-11-06")
        date(2025, 11, 6)
        >>> parse_iso_date("06/11/2025")
        date(2025, 11, 6)
        >>> parse_iso_date("")
        None
    """
    if not value or value == "Não processado":
        return None

    # Tenta formato ISO (YYYY-MM-DD)
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        pass

    # Tenta formato brasileiro (DD/MM/YYYY)
    try:
        return datetime.strptime(value, "%d/%m/%Y").date()
    except ValueError:
        return None


def format_datetime(value: Optional[datetime]) -> Optional[str]:
    """Formata ``datetime`` para ISO sem microssegundos."""
    if value is None:
        return None
    return value.replace(microsecond=0).isoformat(sep=" ")


def validar_qtde_itens(qtde_str: str) -> str | int:
    """Valida e converte quantidade de itens.

    Args:
        qtde_str: String representando a quantidade

    Returns:
        int se válido, ou str com mensagem de erro
    """
    try:
        qtde = int(qtde_str)
        if qtde <= 0:
            return "Erro: A quantidade de itens deve ser um número positivo."
        return qtde
    except ValueError:
        return "Erro: A quantidade de itens deve ser um número válido."


def validar_e_processar_valor(valor_str: str) -> str | float:
    """Valida e processa valor do pedido.

    Args:
        valor_str: String representando o valor monetário

    Returns:
        float arredondado se válido, ou str com mensagem de erro
    """
    try:
        valor = float(valor_str)
        if valor < 0:
            return "Erro: O valor do pedido não pode ser negativo."
        return round(valor, 2)
    except ValueError:
        try:
            valor_limpo = valor_str.replace(".", "").replace(",", ".")
            valor = float(valor_limpo)
            if valor < 0:
                return "Erro: O valor do pedido não pode ser negativo."
            return round(valor, 2)
        except ValueError:
            return "Erro: O valor do pedido deve ser um número válido."


def processar_datas(
    data_entrada_str: str, data_processo_str: Optional[str] = None
) -> tuple[date | str, Optional[date]]:
    """Processa datas de entrada e processo.

    Args:
        data_entrada_str: Data de entrada no formato YYYY-MM-DD
        data_processo_str: Data de processo no formato YYYY-MM-DD (opcional)

    Returns:
        Tupla com (data_entrada, data_processo) se válido,
        ou (mensagem_erro, None) se inválido
    """
    data_entrada = parse_iso_date(data_entrada_str.strip())
    if data_entrada is None:
        return "Erro: Data de entrada inválida.", None

    data_processo = parse_iso_date(data_processo_str)
    return data_entrada, data_processo


def processar_observacoes(observacoes: Optional[str]) -> Optional[str]:
    """Processa campo de observações."""
    return observacoes.strip() if observacoes else None


def preparar_lancamento_para_insert(lanc: Lancamento) -> str | Dict[str, Any]:
    """Valida e normaliza dados para inserção.

    Args:
        lanc: Objeto Lancamento com dados a serem validados

    Returns:
        Dicionário com dados normalizados se válido,
        ou string com mensagem de erro se inválido
    """
    if not all(
        [
            (lanc.usuario or "").strip(),
            lanc.cliente.strip(),
            lanc.pedido.strip(),
            lanc.qtde_itens.strip(),
            lanc.data_entrada.strip(),
            lanc.valor_pedido.strip(),
        ]
    ):
        return (
            "Erro: Campos obrigatórios: usuário, cliente, pedido, "
            "qtd itens, data entrada, valor."
        )

    qtde_result = validar_qtde_itens(lanc.qtde_itens)
    if isinstance(qtde_result, str):
        return qtde_result
    qtde = qtde_result

    valor_result = validar_e_processar_valor(lanc.valor_pedido)
    if isinstance(valor_result, str):
        return valor_result
    valor = valor_result

    data_result = processar_datas(lanc.data_entrada.strip(), lanc.data_processo)
    if isinstance(data_result[0], str):
        return data_result[0]
    data_entrada, data_processo = data_result

    tempo_corte, erro_tempo = normalizar_tempo_corte(lanc.tempo_corte)
    if erro_tempo:
        return erro_tempo

    return {
        "usuario": (lanc.usuario or "").strip(),
        "cliente": lanc.cliente.strip(),
        "pedido": lanc.pedido.strip(),
        "qtde_itens": qtde,
        "data_entrada": data_entrada,
        "data_processo": data_processo,
        "tempo_corte": tempo_corte,
        "observacoes": processar_observacoes(lanc.observacoes),
        "valor_pedido": valor,
    }


def preparar_lancamento_para_update(lanc: Lancamento) -> str | Dict[str, Any]:
    """Valida e normaliza dados antes de atualizar um registro.

    Args:
        lanc: Objeto Lancamento com dados a serem validados

    Returns:
        Dicionário com dados normalizados se válido,
        ou string com mensagem de erro se inválido
    """
    if not lanc.cliente or not lanc.pedido:
        return "Erro: Cliente e pedido são obrigatórios."

    qtde_result = validar_qtde_itens(lanc.qtde_itens)
    if isinstance(qtde_result, str):
        return qtde_result
    qtde = qtde_result

    valor_result = validar_e_processar_valor(lanc.valor_pedido)
    if isinstance(valor_result, str):
        return valor_result
    valor = valor_result

    data_result = processar_datas(lanc.data_entrada, lanc.data_processo)
    if isinstance(data_result[0], str):
        return data_result[0]
    data_entrada, data_processo = data_result

    tempo_corte, erro_tempo = normalizar_tempo_corte(lanc.tempo_corte)
    if erro_tempo:
        return erro_tempo

    return {
        "cliente": lanc.cliente.strip(),
        "pedido": lanc.pedido.strip(),
        "qtde_itens": qtde,
        "data_entrada": data_entrada,
        "data_processo": data_processo,
        "tempo_corte": tempo_corte,
        "observacoes": processar_observacoes(lanc.observacoes),
        "valor_pedido": valor,
    }


__all__ = [
    "parse_iso_date",
    "format_datetime",
    "validar_qtde_itens",
    "validar_e_processar_valor",
    "processar_datas",
    "processar_observacoes",
    "preparar_lancamento_para_insert",
    "preparar_lancamento_para_update",
]
