"""Componentes para o painel de totais do widget de processos."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel


@dataclass
class TotaisControls:
    """Agrupa os widgets do painel de totais."""

    frame: QFrame
    label_processos: QLabel
    label_itens: QLabel
    label_valor: QLabel
    label_media_dias: QLabel
    label_media_itens_por_dia: QLabel
    label_estimativa_itens: QLabel


def criar_totais(*, parent, espacamento: int) -> TotaisControls:
    """Cria o frame com os rótulos de totais."""

    frame = QFrame(parent)
    frame.setFrameStyle(QFrame.StyledPanel)

    layout = QHBoxLayout()
    layout.setSpacing(espacamento)

    font = QFont()
    font.setBold(True)

    label_processos = QLabel("Total Processos: 0")
    label_itens = QLabel("Total Itens: 0")
    label_valor = QLabel("Total Valor: R$ 0,00")
    label_media_dias = QLabel("Média dias processamento: --")
    label_media_itens_por_dia = QLabel("Itens/dia: --")
    label_estimativa_itens = QLabel("Estimativa itens mês: --")

    for label in (
        label_processos,
        label_itens,
        label_valor,
        label_media_dias,
        label_media_itens_por_dia,
        label_estimativa_itens,
    ):
        label.setFont(font)

    layout.addWidget(label_processos)
    layout.addWidget(label_itens)
    layout.addWidget(label_valor)
    layout.addWidget(label_media_dias)
    layout.addWidget(label_media_itens_por_dia)
    layout.addWidget(label_estimativa_itens)
    layout.addStretch()

    frame.setLayout(layout)

    return TotaisControls(
        frame=frame,
        label_processos=label_processos,
        label_itens=label_itens,
        label_valor=label_valor,
        label_media_dias=label_media_dias,
        label_media_itens_por_dia=label_media_itens_por_dia,
        label_estimativa_itens=label_estimativa_itens,
    )


def atualizar_totais(
    controles: TotaisControls,
    *,
    total_processos: int,
    total_itens: int,
    total_valor: float,
    formatar_valor: Callable[[float], str],
    media_dias_processamento: float | None,
    media_itens_por_dia: float | None,
    estimativa_itens_mes: int | None,
) -> None:
    """Atualiza os rótulos de totais com os valores fornecidos."""

    controles.label_processos.setText(f"Total Processos: {total_processos}")
    controles.label_itens.setText(f"Total Itens: {total_itens}")
    controles.label_valor.setText(f"Total Valor: {formatar_valor(total_valor)}")

    if media_dias_processamento is None:
        controles.label_media_dias.setText("Média dias processamento: --")
    else:
        controles.label_media_dias.setText(
            f"Média dias processamento: {media_dias_processamento:.1f}"
        )

    if media_itens_por_dia is None:
        controles.label_media_itens_por_dia.setText("Itens/dia: --")
    else:
        controles.label_media_itens_por_dia.setText(
            f"Itens/dia: {media_itens_por_dia:.1f}"
        )

    if estimativa_itens_mes is None:
        controles.label_estimativa_itens.setText("Estimativa itens mês: --")
    else:
        controles.label_estimativa_itens.setText(
            f"Estimativa itens mês: {estimativa_itens_mes}"
        )
