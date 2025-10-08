"""Gerenciador central de tema usando PyQtDarkTheme."""

from __future__ import annotations

from typing import Callable, ClassVar, List

import qdarktheme
from PySide6.QtCore import QSettings

from ..utils.ui_config import obter_css_tooltip

try:
    from darkdetect import isDark as _is_dark_system_theme
except ImportError:  # pragma: no cover - dependência opcional
    _is_dark_system_theme = None


class ThemeManager:
    """Aplica e persiste o tema visual da aplicação."""

    _INSTANCE: ClassVar["ThemeManager | None"] = None
    _VALID_MODES: ClassVar[set[str]] = {"auto", "light", "dark"}
    _SETTINGS_KEY: ClassVar[str] = "appearance/theme_mode"
    _DEFAULT_MODE: ClassVar[str] = "auto"
    _COLOR_SETTINGS_KEY: ClassVar[str] = "appearance/theme_accent"
    _DEFAULT_COLOR: ClassVar[str] = "verde"
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
        qdarktheme.enable_hi_dpi()
        self._settings = QSettings()
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

    def _apply_theme(self, mode: str, *, persist: bool) -> None:
        selected = mode if mode in self._VALID_MODES else self._DEFAULT_MODE
        resolved = self._resolve_visual_mode(selected)
        accent = self._get_accent_hex()
        qdarktheme.setup_theme(
            theme=selected,
            custom_colors={"primary": accent},
            additional_qss=obter_css_tooltip(resolved, accent),
        )
        self._mode = selected
        if persist:
            self._settings.setValue(self._SETTINGS_KEY, selected)
        for callback in list(self._listeners):
            callback(selected)

    def _resolve_visual_mode(self, mode: str) -> str:
        if mode == "auto" and _is_dark_system_theme is not None:
            return "dark" if _is_dark_system_theme() else "light"
        if mode == "auto":
            return "dark"
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
