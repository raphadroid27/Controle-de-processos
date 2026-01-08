# pylint: disable=cyclic-import
"""Widgets com suporte automático a dark title bar.

Este módulo expõe classes base que registram janelas no ThemeManager para
aplicar dark title bar automaticamente quando o tema estiver em modo escuro.
"""

from PySide6.QtWidgets import QDialog, QMainWindow, QMessageBox, QWidget

from src.ui.theme_manager import ThemeManager

THEME_MANAGER = ThemeManager.instance()


class _ThemedWidgetMixin:
    """Mixin para registrar janelas no gerenciador de temas."""

    def showEvent(self, event):  # pylint: disable=invalid-name
        """Registra a janela ao ser exibida para aplicar dark title bar."""
        super().showEvent(event)
        THEME_MANAGER.register_window(self)


class ThemedDialog(_ThemedWidgetMixin, QDialog):
    """QDialog que aplica automaticamente dark title bar quando exibido."""


class ThemedMainWindow(_ThemedWidgetMixin, QMainWindow):
    """QMainWindow que aplica automaticamente dark title bar quando exibido."""


class ThemedMessageBox(_ThemedWidgetMixin, QMessageBox):
    """QMessageBox que aplica automaticamente dark title bar quando exibido."""


def create_themed_dialog(parent: QWidget | None = None) -> ThemedDialog:
    """Cria um QDialog com dark title bar automático."""

    return ThemedDialog(parent)


def apply_dark_titlebar(widget: QWidget) -> None:
    """Aplica dark title bar manualmente a um widget existente."""

    THEME_MANAGER.register_window(widget)
