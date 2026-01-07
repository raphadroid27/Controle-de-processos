"""Componentes para o painel de totais do widget de pedidos."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QFrame, QLabel

from src.ui.flow_layout import FlowLayout


@dataclass
class TotaisControls:
    """Agrupa os widgets do painel de totais."""

    frame: QFrame
    label_pedidos: QLabel
    label_itens: QLabel
    label_media_itens_por_dia: QLabel
    label_estimativa_itens: QLabel
    label_media_dias: QLabel
    label_valor: QLabel
    label_tempo_corte_total: QLabel
    label_media_tempo_corte_dia: QLabel
    label_tempo_corte_dia: QLabel


def criar_totais(*, parent, espacamento: int) -> TotaisControls:
    """Cria o frame com os rótulos de totais."""
    frame = QFrame(parent)
    frame.setFrameStyle(QFrame.Shape.StyledPanel)

    layout = FlowLayout(
        h_spacing=espacamento,
        v_spacing=espacamento,
    )

    label_pedidos = QLabel("Pedidos período: 0")
    label_itens = QLabel("Itens período: 0")
    label_media_itens_por_dia = QLabel("Média itens/dia: --")
    label_estimativa_itens = QLabel("Estimativa itens período: --")
    label_media_dias = QLabel("Média dias processo: --")
    label_valor = QLabel("Valor total: R$ 0,00")
    label_tempo_corte_total = QLabel("Tempo corte total: --")
    label_media_tempo_corte_dia = QLabel("Média tempo corte/dia: --")
    label_tempo_corte_dia = QLabel("Tempo corte hoje: --")

    for label in (
        label_pedidos,
        label_itens,
        label_media_itens_por_dia,
        label_estimativa_itens,
        label_media_dias,
        label_valor,
        label_tempo_corte_total,
        label_media_tempo_corte_dia,
        label_tempo_corte_dia,
    ):
        label.setObjectName("label_titulo_negrito")

    layout.addWidget(label_pedidos)
    layout.addWidget(label_itens)
    layout.addWidget(label_media_itens_por_dia)
    layout.addWidget(label_estimativa_itens)
    layout.addWidget(label_media_dias)
    layout.addWidget(label_valor)
    layout.addWidget(label_tempo_corte_total)
    layout.addWidget(label_media_tempo_corte_dia)
    layout.addWidget(label_tempo_corte_dia)

    frame.setLayout(layout)

    return TotaisControls(
        frame=frame,
        label_pedidos=label_pedidos,
        label_itens=label_itens,
        label_media_itens_por_dia=label_media_itens_por_dia,
        label_estimativa_itens=label_estimativa_itens,
        label_media_dias=label_media_dias,
        label_valor=label_valor,
        label_tempo_corte_total=label_tempo_corte_total,
        label_media_tempo_corte_dia=label_media_tempo_corte_dia,
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
    tempo_corte_total: str | None,
    media_tempo_corte_dia: str | None,
    tempo_corte_dia: str | None,
) -> None:
    """Atualiza os rótulos de totais com os valores fornecidos."""
    # Usar a cor de destaque do tema atual
    palette = QApplication.palette()
    cor_destaque = palette.color(QPalette.ColorRole.Highlight).name()

    def _fmt(titulo: str, valor: Any, cor: str = cor_destaque) -> str:
        return f"{titulo}: <span style='color: {cor};'>{valor}</span>"

    # Configurar todos para RichText
    for label in (
        controles.label_pedidos,
        controles.label_itens,
        controles.label_valor,
        controles.label_media_itens_por_dia,
        controles.label_estimativa_itens,
        controles.label_tempo_corte_total,
        controles.label_media_tempo_corte_dia,
        controles.label_tempo_corte_dia,
    ):
        label.setTextFormat(Qt.TextFormat.RichText)

    controles.label_pedidos.setText(_fmt("Pedidos período", total_pedidos))
    controles.label_itens.setText(_fmt("Itens período", total_itens))
    controles.label_valor.setText(
        _fmt("Valor total", formatar_valor(total_valor)))

    if media_dias_processo is None:
        controles.label_media_dias.setTextFormat(Qt.TextFormat.RichText)
        controles.label_media_dias.setText(_fmt("Média dias processo", "--"))
    else:
        cor_media = _obter_cor_media_dias(media_dias_processo)
        controles.label_media_dias.setTextFormat(Qt.TextFormat.RichText)
        controles.label_media_dias.setText(
            f"Média dias processo: <span style='color: {cor_media}; font-weight: bold'>"
            f"{media_dias_processo:.1f}</span>"
        )

    if media_itens_por_dia is None:
        controles.label_media_itens_por_dia.setText(
            _fmt("Média itens/dia", "--"))
    else:
        controles.label_media_itens_por_dia.setText(
            _fmt("Média itens/dia", f"{media_itens_por_dia:.1f}")
        )

    if estimativa_itens_mes is None:
        controles.label_estimativa_itens.setText(
            _fmt("Estimativa itens período", "--"))
    else:
        controles.label_estimativa_itens.setText(
            _fmt("Estimativa itens período", estimativa_itens_mes)
        )

    if tempo_corte_total:
        controles.label_tempo_corte_total.setText(
            _fmt("Tempo corte total", tempo_corte_total))
    else:
        controles.label_tempo_corte_total.setText(
            _fmt("Tempo corte total", "--"))

    if media_tempo_corte_dia:
        controles.label_media_tempo_corte_dia.setText(
            _fmt("Média tempo corte/dia", media_tempo_corte_dia))
    else:
        controles.label_media_tempo_corte_dia.setText(
            _fmt("Média tempo corte/dia", "--"))

    if tempo_corte_dia:
        controles.label_tempo_corte_dia.setText(
            _fmt("Tempo corte hoje", tempo_corte_dia))
    else:
        controles.label_tempo_corte_dia.setText(
            _fmt("Tempo corte hoje", "--"))


def _obter_cor_media_dias(valor: float) -> str:
    """Retorna a cor apropriada para a média de dias de processamento."""
    if valor <= 2:
        return "#2e7d32"  # verde
    if valor <= 4:
        return "#f9a825"  # amarelo
    return "#c62828"  # vermelho
