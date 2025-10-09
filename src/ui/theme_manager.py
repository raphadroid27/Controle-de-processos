"""Gerenciador central de tema usando paletas nativas do PySide6."""

from __future__ import annotations

from typing import Callable, ClassVar, List

from PySide6.QtCore import QSettings
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication


class ThemeManager:
    """Aplica e persiste o tema visual da aplicação (simplificado)."""

    _INSTANCE: ClassVar["ThemeManager | None"] = None
    _VALID_MODES: ClassVar[set[str]] = {"light", "dark"}
    _SETTINGS_KEY: ClassVar[str] = "appearance/theme_mode"
    _DEFAULT_MODE: ClassVar[str] = "light"
    _COLOR_SETTINGS_KEY: ClassVar[str] = "appearance/theme_accent"
    _DEFAULT_COLOR: ClassVar[str] = "verde"
    _STYLE_SETTINGS_KEY: ClassVar[str] = "appearance/theme_style"
    _DEFAULT_STYLE: ClassVar[str] = "Fusion"
    _COLOR_OPTIONS: ClassVar[dict[str, tuple[str, str]]] = {
        "verde": ("Verde", "#4CAF50"),
        "azul": ("Azul", "#2196F3"),
        "amarelo": ("Amarelo", "#FFC107"),
        "vermelho": ("Vermelho", "#E53935"),
        "laranja": ("Laranja", "#FF5722"),
        "cinza": ("Cinza", "#9E9E9E"),
        "roxo": ("Roxo", "#9C27B0"),
        "magenta": ("Magenta", "#E91E63"),
        "ciano": ("Ciano", "#00BCD4"),
    }

    def __init__(self) -> None:
        self._settings = QSettings()
        # Define o estilo Fusion para melhor suporte a paletas
        saved_style = self._settings.value(
            self._STYLE_SETTINGS_KEY, self._DEFAULT_STYLE
        )
        if not isinstance(saved_style, str):
            saved_style = self._DEFAULT_STYLE
        self._style = saved_style
        # Garante que seja salvo
        self._settings.setValue(self._STYLE_SETTINGS_KEY, self._style)
        QApplication.setStyle(self._style)
        saved_mode = self._settings.value(
            self._SETTINGS_KEY, self._DEFAULT_MODE)
        self._mode = (
            saved_mode if saved_mode in self._VALID_MODES else self._DEFAULT_MODE
        )
        saved_color = self._settings.value(
            self._COLOR_SETTINGS_KEY, self._DEFAULT_COLOR
        )
        if not isinstance(saved_color, str) or saved_color not in self._COLOR_OPTIONS:
            saved_color = self._DEFAULT_COLOR
        self._color = saved_color
        self._listeners: List[Callable[[str], None]] = []
        self._color_listeners: List[Callable[[str], None]] = []

    @classmethod
    def instance(cls) -> "ThemeManager":
        """Retorna a instância única do gerenciador de temas."""
        if cls._INSTANCE is None:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    @property
    def current_mode(self) -> str:
        """Devolve o modo de tema atualmente aplicado."""
        return self._mode

    @property
    def current_color(self) -> str:
        """Retorna a cor de destaque atualmente aplicada."""
        return self._color

    @property
    def current_style(self) -> str:
        """Retorna o estilo atualmente aplicado."""
        return self._style

    def initialize(self) -> None:
        """Aplica o tema salvo sem sobrescrever a preferência."""
        self._apply_theme(self._mode, persist=False)

    def apply_theme(self, mode: str) -> None:
        """Aplica o tema desejado e salva a escolha do usuário."""
        self._apply_theme(mode, persist=True)

    def apply_color(self, color_key: str) -> None:
        """Aplica uma nova cor de destaque para o tema."""
        if color_key not in self._COLOR_OPTIONS:
            return
        if color_key == self._color:
            return
        self._color = color_key
        self._settings.setValue(self._COLOR_SETTINGS_KEY, color_key)
        self._apply_theme(self._mode, persist=False)
        self._notify_color_listeners()

    def apply_style(self, style: str) -> None:
        """Aplica um novo estilo para a aplicação."""
        if style == self._style:
            return
        self._style = style
        self._settings.setValue(self._STYLE_SETTINGS_KEY, style)
        QApplication.setStyle(style)
        # Força atualização de todos os widgets para aplicar o novo estilo
        for widget in QApplication.allWidgets():
            widget.repaint()

    def register_listener(self, callback: Callable[[str], None]) -> None:
        """Registra um callback para ser notificado quando o tema mudar."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unregister_listener(self, callback: Callable[[str], None]) -> None:
        """Remove um callback previamente registrado."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def register_color_listener(self, callback: Callable[[str], None]) -> None:
        """Registra um callback para notificações de mudança de cor de destaque."""
        if callback not in self._color_listeners:
            self._color_listeners.append(callback)

    def unregister_color_listener(self, callback: Callable[[str], None]) -> None:
        """Remove um callback previamente registrado para mudanças de cor."""
        if callback in self._color_listeners:
            self._color_listeners.remove(callback)

    def _create_light_palette(self, accent_color: QColor) -> QPalette:
        """Cria uma paleta clara nativa com cor de destaque."""
        palette = QPalette()
        # Cores para tema claro
        palette.setColor(QPalette.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
        palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.Text, QColor(0, 0, 0))
        palette.setColor(QPalette.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
        palette.setColor(QPalette.BrightText, QColor(255, 255, 255))
        palette.setColor(QPalette.Link, accent_color)
        palette.setColor(QPalette.Highlight, accent_color)
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        return palette

    def _create_dark_palette(self, accent_color: QColor) -> QPalette:
        """Cria uma paleta escura nativa com cor de destaque."""
        palette = QPalette()
        # Cores para tema escuro
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Link, accent_color)
        palette.setColor(QPalette.Highlight, accent_color)
        palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
        return palette

    def _apply_theme(self, mode: str, *, persist: bool) -> None:
        selected = mode if mode in self._VALID_MODES else self._DEFAULT_MODE
        resolved = self._resolve_visual_mode(selected)
        app = QApplication.instance()
        accent_color = QColor(self._get_accent_hex())
        if resolved == "dark":
            palette = self._create_dark_palette(accent_color)
        else:
            palette = self._create_light_palette(accent_color)
        app.setPalette(palette)
        # Força atualização de todos os widgets para aplicar a nova paleta
        for widget in app.allWidgets():
            widget.repaint()
        self._mode = selected
        if persist:
            self._settings.setValue(self._SETTINGS_KEY, selected)
        for callback in list(self._listeners):
            callback(selected)

    def _resolve_visual_mode(self, mode: str) -> str:
        return mode

    @classmethod
    def color_options(cls) -> dict[str, tuple[str, str]]:
        """Retorna mapa de cores disponíveis (chave -> (rótulo, hex))."""
        return dict(cls._COLOR_OPTIONS)

    def _get_accent_hex(self) -> str:
        rotulo_hex = self._COLOR_OPTIONS.get(
            self._color, self._COLOR_OPTIONS[self._DEFAULT_COLOR]
        )
        return rotulo_hex[1]

    def _notify_color_listeners(self) -> None:
        for callback in list(self._color_listeners):
            callback(self._color)
