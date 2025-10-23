"""Formulário "Sobre".

Este módulo implementa a janela "Sobre" do aplicativo.
"""

import sys
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QDialog, QLabel, QVBoxLayout, QWidget

from src import __version__  # pylint: disable=import-error


def main(root: Optional[QWidget]) -> None:
    """Create and display the About dialog."""
    sobre_form = QDialog(root)
    sobre_form.setWindowTitle("Sobre")
    sobre_form.setFixedSize(300, 210)
    sobre_form.setModal(True)

    # Layout principal vertical
    layout = QVBoxLayout(sobre_form)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(10)

    # Widget de conteúdo principal
    conteudo = QWidget()
    conteudo_layout = QVBoxLayout(conteudo)
    conteudo_layout.setSpacing(5)

    # Título
    label_titulo = QLabel("Controle de Processos")
    font_titulo = QFont("Arial", 16)
    font_titulo.setBold(True)
    label_titulo.setFont(font_titulo)
    label_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
    conteudo_layout.addWidget(label_titulo)

    # Versão
    label_versao = QLabel(f"Versão: {__version__}")
    font_normal = QFont("Arial", 12)
    label_versao.setFont(font_normal)
    label_versao.setAlignment(Qt.AlignmentFlag.AlignCenter)
    conteudo_layout.addWidget(label_versao)

    # Autor
    label_autor = QLabel("Autor: raphadroid27")
    label_autor.setFont(font_normal)
    label_autor.setAlignment(Qt.AlignmentFlag.AlignCenter)
    conteudo_layout.addWidget(label_autor)

    # Descrição
    label_desc = QLabel("Sistema de gestão de processos.")
    label_desc.setFont(font_normal)
    label_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
    conteudo_layout.addWidget(label_desc)

    # Link para o GitHub
    label_link = QLabel(
        '<a href="https://github.com/raphadroid27/Controle-de-processos">Repositório no GitHub</a>'
    )
    label_link.setFont(font_normal)
    label_link.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label_link.setOpenExternalLinks(True)
    conteudo_layout.addWidget(label_link)

    conteudo.setLayout(conteudo_layout)
    layout.addWidget(conteudo)

    sobre_form.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main(None)
    sys.exit(app.exec())
