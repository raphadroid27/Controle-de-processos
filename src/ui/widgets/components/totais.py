"""Componentes para o painel de totais do widget de pedidos."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QLabel

from src.ui.flow_layout import FlowLayout


@dataclass
class TotaisControls:
    """Agrupa os widgets do painel de totais."""

    frame: QFrame
    label_pedidos: QLabel
    label_itens: QLabel
    label_valor: QLabel
    label_media_dias: QLabel
    label_media_itens_por_dia: QLabel
    label_estimativa_itens: QLabel
    label_tempo_corte_dia: QLabel


def criar_totais(*, parent, espacamento: int) -> TotaisControls:
    """Cria o frame com os rótulos de totais."""
    frame = QFrame(parent)
    frame.setFrameStyle(QFrame.Shape.StyledPanel)

    layout = FlowLayout(
        h_spacing=espacamento,
        v_spacing=espacamento,
    )

    font = QFont()
    font.setBold(True)

    label_pedidos = QLabel("Total Pedidos: 0")
    label_itens = QLabel("Total Itens: 0")
    label_valor = QLabel("Total Valor: R$ 0,00")
    label_media_dias = QLabel("Média dias processo: --")
    label_media_itens_por_dia = QLabel("Itens/dia: --")
    label_estimativa_itens = QLabel("Estimativa itens mês: --")
    label_tempo_corte_dia = QLabel("Tempo corte hoje: --")

    for label in (
        label_pedidos,
        label_itens,
        label_valor,
        label_media_dias,
        label_media_itens_por_dia,
        label_estimativa_itens,
        label_tempo_corte_dia,
    ):
        label.setFont(font)

    layout.addWidget(label_pedidos)
    layout.addWidget(label_itens)
    layout.addWidget(label_valor)
    layout.addWidget(label_media_dias)
    layout.addWidget(label_media_itens_por_dia)
    layout.addWidget(label_estimativa_itens)
    layout.addWidget(label_tempo_corte_dia)

    frame.setLayout(layout)

    return TotaisControls(
        frame=frame,
        label_pedidos=label_pedidos,
        label_itens=label_itens,
        label_valor=label_valor,
        label_media_dias=label_media_dias,
        label_media_itens_por_dia=label_media_itens_por_dia,
        label_estimativa_itens=label_estimativa_itens,
        label_tempo_corte_dia=label_tempo_corte_dia,
    )


def atualizar_totais(
    controles: TotaisControls,
    *,
    total_pedidos: int,
    total_itens: int,
    total_valor: float,
    formatar_valor: Callable[[float], str],
    media_dias_processo: float | None,
    media_itens_por_dia: float | None,
    estimativa_itens_mes: int | None,
    tempo_corte_dia: str | None,
) -> None:
    """Atualiza os rótulos de totais com os valores fornecidos."""
    controles.label_pedidos.setText(f"Total Pedidos: {total_pedidos}")
    controles.label_itens.setText(f"Total Itens: {total_itens}")
    controles.label_valor.setText(
        f"Total Valor: {formatar_valor(total_valor)}")

    if media_dias_processo is None:
        controles.label_media_dias.setTextFormat(Qt.TextFormat.PlainText)
        controles.label_media_dias.setText("Média dias processo: --")
    else:
        cor = _obter_cor_media_dias(media_dias_processo)
        controles.label_media_dias.setTextFormat(Qt.TextFormat.RichText)
        controles.label_media_dias.setText(
            f"Média dias processo: <span style='color: {cor}; font-weight: bold'>"
            f"{media_dias_processo:.1f}</span>"
        )

    if media_itens_por_dia is None:
        controles.label_media_itens_por_dia.setText("Itens/dia: --")
    else:
        controles.label_media_itens_por_dia.setText(
            f"Itens/dia: {media_itens_por_dia:.1f}"
        )

    if estimativa_itens_mes is None:
        controles.label_estimativa_itens.setText("Estimativa itens: --")
    else:
        controles.label_estimativa_itens.setText(
            f"Estimativa itens: {estimativa_itens_mes}"
        )

    if tempo_corte_dia:
        controles.label_tempo_corte_dia.setText(
            f"Tempo corte hoje: {tempo_corte_dia}")
    else:
        controles.label_tempo_corte_dia.setText("Tempo corte hoje: --")


def _obter_cor_media_dias(valor: float) -> str:
    """Retorna a cor apropriada para a média de dias de processamento."""
    if valor <= 2:
        return "#2e7d32"  # verde
    if valor <= 4:
        return "#f9a825"  # amarelo
    return "#c62828"  # vermelho
