"""
Widgets personalizados com navegação por teclado.

Contém widgets customizados que permitem navegação entre campos
usando as setas do teclado.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QDateEdit, QLineEdit


class NavigableLineEdit(QLineEdit):
    """QLineEdit personalizado que permite navegação entre campos com setas."""

    def __init__(self, campos_navegacao=None, parent=None):
        super().__init__(parent)
        self.campos_navegacao = campos_navegacao or []

    def set_campos_navegacao(self, campos):
        """Define a lista de campos para navegação."""
        self.campos_navegacao = campos

    def keyPressEvent(self, event):  # pylint: disable=invalid-name
        """Intercepta eventos de teclado para navegação."""
        if event.key() == Qt.Key.Key_Left:
            # Navegar para campo anterior se cursor estiver no início
            if self.cursorPosition() == 0 and self.campos_navegacao:
                try:
                    indice_atual = self.campos_navegacao.index(self)
                    indice_anterior = (indice_atual - 1) % len(self.campos_navegacao)
                    self.campos_navegacao[indice_anterior].setFocus()
                    # Posicionar cursor no final do campo anterior
                    if isinstance(self.campos_navegacao[indice_anterior], QLineEdit):
                        self.campos_navegacao[indice_anterior].setCursorPosition(
                            len(self.campos_navegacao[indice_anterior].text())
                        )
                    return
                except ValueError:
                    pass

        elif event.key() == Qt.Key.Key_Right:
            # Navegar para próximo campo se cursor estiver no final
            if self.cursorPosition() == len(self.text()) and self.campos_navegacao:
                try:
                    indice_atual = self.campos_navegacao.index(self)
                    proximo_indice = (indice_atual + 1) % len(self.campos_navegacao)
                    self.campos_navegacao[proximo_indice].setFocus()
                    # Posicionar cursor no início do próximo campo
                    if isinstance(self.campos_navegacao[proximo_indice], QLineEdit):
                        self.campos_navegacao[proximo_indice].setCursorPosition(0)
                    return
                except ValueError:
                    pass

        # Passar o evento para o comportamento padrão
        super().keyPressEvent(event)


class NavigableDateEdit(QDateEdit):
    """QDateEdit personalizado que permite navegação entre campos com setas."""

    def __init__(self, campos_navegacao=None, parent=None):
        super().__init__(parent)
        self.campos_navegacao = campos_navegacao or []

    def set_campos_navegacao(self, campos):
        """Define a lista de campos para navegação."""
        self.campos_navegacao = campos

    def keyPressEvent(self, event):  # pylint: disable=invalid-name
        """Intercepta eventos de teclado para navegação."""
        if event.key() == Qt.Key.Key_Left and self.campos_navegacao:
            try:
                indice_atual = self.campos_navegacao.index(self)
                indice_anterior = (indice_atual - 1) % len(self.campos_navegacao)
                self.campos_navegacao[indice_anterior].setFocus()
                # Posicionar cursor no final do campo anterior
                if isinstance(self.campos_navegacao[indice_anterior], QLineEdit):
                    self.campos_navegacao[indice_anterior].setCursorPosition(
                        len(self.campos_navegacao[indice_anterior].text())
                    )
                return
            except ValueError:
                pass

        elif event.key() == Qt.Key.Key_Right and self.campos_navegacao:
            try:
                indice_atual = self.campos_navegacao.index(self)
                proximo_indice = (indice_atual + 1) % len(self.campos_navegacao)
                self.campos_navegacao[proximo_indice].setFocus()
                # Posicionar cursor no início do próximo campo
                if isinstance(self.campos_navegacao[proximo_indice], QLineEdit):
                    self.campos_navegacao[proximo_indice].setCursorPosition(0)
                return
            except ValueError:
                pass

        # Passar o evento para o comportamento padrão
        super().keyPressEvent(event)


class NavigableComboBox(QComboBox):
    """QComboBox com navegação lateral entre campos."""

    def __init__(self, campos_navegacao=None, parent=None):
        super().__init__(parent)
        self.campos_navegacao = campos_navegacao or []

    def set_campos_navegacao(self, campos):
        """Define a sequência de widgets navegáveis a partir deste combo box."""
        self.campos_navegacao = campos

    def keyPressEvent(self, event):  # pylint: disable=invalid-name
        """Permite alternar entre campos usando as setas esquerda/direita."""
        if event.key() == Qt.Key.Key_Left and self.campos_navegacao:
            try:
                indice_atual = self.campos_navegacao.index(self)
                indice_anterior = (indice_atual - 1) % len(self.campos_navegacao)
                alvo = self.campos_navegacao[indice_anterior]
                alvo.setFocus()
                if isinstance(alvo, QLineEdit):
                    alvo.setCursorPosition(len(alvo.text()))
                return
            except ValueError:
                pass

        if event.key() == Qt.Key.Key_Right and self.campos_navegacao:
            try:
                indice_atual = self.campos_navegacao.index(self)
                proximo_indice = (indice_atual + 1) % len(self.campos_navegacao)
                alvo = self.campos_navegacao[proximo_indice]
                alvo.setFocus()
                if isinstance(alvo, QLineEdit):
                    alvo.setCursorPosition(0)
                return
            except ValueError:
                pass

        super().keyPressEvent(event)
