"""Utilitários de layout compartilhados entre componentes de processos."""

from __future__ import annotations

from typing import Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout

__all__ = ["criar_coluna_rotulo", "criar_layout_botao_padrao"]


def criar_coluna_rotulo(label_texto: str, widget, peso: int) -> Tuple[QVBoxLayout, int]:
    """Cria um layout vertical com rótulo associado a um widget."""
    layout = QVBoxLayout()
    layout.setSpacing(3)
    layout.setContentsMargins(0, 0, 0, 0)

    label = QLabel(label_texto)
    label.setObjectName("label_titulo")
    label.setAlignment(Qt.AlignmentFlag.AlignLeft |
                       Qt.AlignmentFlag.AlignBottom)
    label.setMinimumHeight(16)
    label.setMaximumHeight(18)

    layout.addWidget(label)
    layout.addWidget(widget)

    return layout, peso


def criar_layout_botao_padrao(botao: QPushButton) -> QVBoxLayout:
    """Cria um layout vertical padrão para botões alinhados a campos."""
    layout = QVBoxLayout()
    layout.setSpacing(3)
    layout.setContentsMargins(0, 0, 0, 0)

    spacer = QLabel(" ")
    spacer.setObjectName("label_titulo")
    spacer.setAlignment(Qt.AlignmentFlag.AlignLeft |
                        Qt.AlignmentFlag.AlignBottom)
    spacer.setMinimumHeight(16)
    spacer.setMaximumHeight(18)
    layout.addWidget(spacer)
    layout.addWidget(botao)
    return layout
