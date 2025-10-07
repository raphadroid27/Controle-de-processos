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


def criar_totais(*, parent, espacamento: int) -> TotaisControls:
    """Cria o frame com os rótulos de totais."""

    frame = QFrame(parent)
    frame.setFrameStyle(QFrame.StyledPanel)

    layout = QHBoxLayout()
    layout.setSpacing(espacamento)

    label_processos = QLabel("Total Processos: 0")
    label_itens = QLabel("Total Itens: 0")
    label_valor = QLabel("Total Valor: R$ 0,00")

    font = QFont()
    font.setBold(True)
    for label in (label_processos, label_itens, label_valor):
        label.setFont(font)

    layout.addWidget(label_processos)
    layout.addWidget(label_itens)
    layout.addWidget(label_valor)
    layout.addStretch()

    frame.setLayout(layout)

    return TotaisControls(
        frame=frame,
        label_processos=label_processos,
        label_itens=label_itens,
        label_valor=label_valor,
    )


def atualizar_totais(
    controles: TotaisControls,
    *,
    total_processos: int,
    total_itens: int,
    total_valor: float,
    formatar_valor: Callable[[float], str],
) -> None:
    """Atualiza os rótulos de totais com os valores fornecidos."""

    controles.label_processos.setText(f"Total Processos: {total_processos}")
    controles.label_itens.setText(f"Total Itens: {total_itens}")
    controles.label_valor.setText(f"Total Valor: {formatar_valor(total_valor)}")
