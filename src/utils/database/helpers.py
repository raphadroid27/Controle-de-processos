"""Funções auxiliares para validação e formatação de lançamentos."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, Optional

from ..tempo_corte import normalizar_tempo_corte
from .models import Lancamento


def parse_iso_date(value: Optional[str]) -> Optional[date]:
    """Convert ISO string (YYYY-MM-DD) to ``date`` or ``None``."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def format_datetime(value: Optional[datetime]) -> Optional[str]:
    """Formata ``datetime`` para ISO sem microssegundos."""
    if value is None:
        return None
    return value.replace(microsecond=0).isoformat(sep=" ")


def preparar_lancamento_para_insert(lanc: Lancamento) -> str | Dict[str, Any]:
    """Valida e normaliza dados para inserção."""
    if not all(
        [
            (lanc.usuario or "").strip(),
            lanc.cliente.strip(),
            lanc.processo.strip(),
            lanc.qtde_itens.strip(),
            lanc.data_entrada.strip(),
            lanc.valor_pedido.strip(),
        ]
    ):
        return (
            "Erro: Campos obrigatórios: usuário, cliente, processo, "
            "qtd itens, data entrada, valor."
        )

    try:
        qtde = int(lanc.qtde_itens)
        if qtde <= 0:
            msg = "Erro: A quantidade de itens deve ser um número positivo."
            return msg
    except ValueError:
        return "Erro: A quantidade de itens deve ser um número válido."

    try:
        # Remover pontos de milhares e trocar vírgula por ponto
        valor_limpo = lanc.valor_pedido.replace(".", "").replace(",", ".")
        valor = float(valor_limpo)
        if valor <= 0:
            return "Erro: O valor do pedido deve ser maior que zero."
    except ValueError:
        return "Erro: O valor do pedido deve ser um número válido."

    data_entrada = parse_iso_date(lanc.data_entrada.strip())
    if data_entrada is None:
        return "Erro: Data de entrada inválida."

    data_processo = parse_iso_date(lanc.data_processo)

    tempo_corte, erro_tempo = normalizar_tempo_corte(lanc.tempo_corte)
    if erro_tempo:
        return erro_tempo

    return {
        "usuario": (lanc.usuario or "").strip(),
        "cliente": lanc.cliente.strip(),
        "processo": lanc.processo.strip(),
        "qtde_itens": qtde,
        "data_entrada": data_entrada,
        "data_processo": data_processo,
        "tempo_corte": tempo_corte,
        "valor_pedido": valor,
    }


def preparar_lancamento_para_update(lanc: Lancamento) -> str | Dict[str, Any]:
    """Valida e normaliza dados antes de atualizar um registro."""
    if not lanc.cliente or not lanc.processo:
        return "Erro: Cliente e processo são obrigatórios."

    try:
        qtde = int(lanc.qtde_itens)
        if qtde <= 0:
            return "Erro: Quantidade de itens deve ser um número positivo."
    except ValueError:
        msg = "Erro: Quantidade de itens deve ser um número válido."
        return msg

    try:
        # Remover pontos de milhares e trocar vírgula por ponto
        valor_limpo = lanc.valor_pedido.replace(".", "").replace(",", ".")
        valor = float(valor_limpo)
        if valor < 0:
            return "Erro: Valor do pedido não pode ser negativo."
    except ValueError:
        return "Erro: Valor do pedido deve ser um número válido."

    data_entrada = parse_iso_date(lanc.data_entrada)
    if data_entrada is None:
        return "Erro: Data de entrada inválida."

    data_processo = parse_iso_date(lanc.data_processo)

    tempo_corte, erro_tempo = normalizar_tempo_corte(lanc.tempo_corte)
    if erro_tempo:
        return erro_tempo

    return {
        "cliente": lanc.cliente.strip(),
        "processo": lanc.processo.strip(),
        "qtde_itens": qtde,
        "data_entrada": data_entrada,
        "data_processo": data_processo,
        "tempo_corte": tempo_corte,
        "valor_pedido": valor,
    }


__all__ = [
    "parse_iso_date",
    "format_datetime",
    "preparar_lancamento_para_insert",
    "preparar_lancamento_para_update",
]
