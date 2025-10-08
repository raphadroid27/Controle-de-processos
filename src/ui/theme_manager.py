"""Gerenciador central de tema usando PyQtDarkTheme."""

from __future__ import annotations

from typing import Callable, ClassVar, List

import qdarktheme
from PySide6.QtCore import QSettings


class ThemeManager:
    """Aplica e persiste o tema visual da aplicação."""

    _INSTANCE: ClassVar["ThemeManager | None"] = None
    _VALID_MODES: ClassVar[set[str]] = {"auto", "light", "dark"}
    _SETTINGS_KEY: ClassVar[str] = "appearance/theme_mode"
    _DEFAULT_MODE: ClassVar[str] = "auto"
    _CUSTOM_COLORS: ClassVar[dict[str, str]] = {"primary": "#4CAF50"}

    def __init__(self) -> None:
        qdarktheme.enable_hi_dpi()
        self._settings = QSettings()
        saved_mode = self._settings.value(
            self._SETTINGS_KEY, self._DEFAULT_MODE)
        self._mode = saved_mode if saved_mode in self._VALID_MODES else self._DEFAULT_MODE
        self._listeners: List[Callable[[str], None]] = []

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

    def initialize(self) -> None:
        """Aplica o tema salvo sem sobrescrever a preferência."""
        self._apply_theme(self._mode, persist=False)

    def apply_theme(self, mode: str) -> None:
        """Aplica o tema desejado e salva a escolha do usuário."""
        self._apply_theme(mode, persist=True)

    def register_listener(self, callback: Callable[[str], None]) -> None:
        """Registra um callback para ser notificado quando o tema mudar."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unregister_listener(self, callback: Callable[[str], None]) -> None:
        """Remove um callback previamente registrado."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _apply_theme(self, mode: str, *, persist: bool) -> None:
        selected = mode if mode in self._VALID_MODES else self._DEFAULT_MODE
        qdarktheme.setup_theme(
            theme=selected, custom_colors=self._CUSTOM_COLORS)
        self._mode = selected
        if persist:
            self._settings.setValue(self._SETTINGS_KEY, selected)
        for callback in list(self._listeners):
            callback(selected)
