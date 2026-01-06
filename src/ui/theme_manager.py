"""Gerenciador central de tema usando paletas nativas do PySide6."""

from __future__ import annotations

import ctypes
import logging
import platform
from typing import Any, Callable, ClassVar, Dict, List, cast

from PySide6.QtCore import QEvent, QObject, QSettings
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QWidget

from src.ui.styles import get_widgets_styles

# pylint: disable=too-many-public-methods


class ThemeManager:
    """Aplica e persiste o tema visual da aplicação com suporte a destaque do sistema."""

    _INSTANCE: ClassVar["ThemeManager | None"] = None
    _VALID_MODES: ClassVar[set[str]] = {"light", "dark"}
    _SETTINGS_KEY: ClassVar[str] = "appearance/theme_mode"
    _DEFAULT_MODE: ClassVar[str] = "dark"
    _COLOR_SETTINGS_KEY: ClassVar[str] = "appearance/theme_accent"
    _DEFAULT_COLOR: ClassVar[str] = "azul"
    _STYLE_SETTINGS_KEY: ClassVar[str] = "appearance/theme_style"
    _DEFAULT_STYLE: ClassVar[str] = "Fusion"

    _COLOR_OPTIONS: ClassVar[dict[str, tuple[str, str]]] = {
        "cinza": ("Cinza", "#9E9E9E"),
        "vermelho": ("Vermelho", "#E53935"),
        "laranja": ("Laranja", "#FF5722"),
        "ambar": ("Âmbar", "#FF6F00"),
        "verde": ("Verde", "#4CAF50"),
        "teal": ("Verde-água", "#009688"),
        "ciano": ("Ciano", "#00BCD4"),
        "azul": ("Azul", "#2196F3"),
        "indigo": ("Índigo", "#3F51B5"),
        "roxo": ("Roxo", "#9C27B0"),
        "rosa": ("Rosa", "#EC407A"),
    }

    def __init__(self) -> None:
        """Inicializa o gerenciador de temas."""
        self._settings: QSettings | None = None
        self._style = self._DEFAULT_STYLE
        self._mode = self._DEFAULT_MODE
        self._color = self._DEFAULT_COLOR
        self._listeners: List[Callable[[str], None]] = []
        self._color_listeners: List[Callable[[str], None]] = []
        self._color_actions: Dict[str, Any] = {}
        self._actions: Dict[str, Any] = {}
        self._registered_windows: List[QWidget] = []
        self._logger = logging.getLogger(__name__)
        self._event_filter: QObject | None = None

    def _get_settings(self) -> QSettings:
        """Retorna a instância de QSettings, criando se necessário."""
        if self._settings is None:
            self._settings = QSettings()
        return self._settings

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
        saved_style = self._get_settings().value(
            self._STYLE_SETTINGS_KEY, self._DEFAULT_STYLE
        )
        if not isinstance(saved_style, str) or saved_style != self._DEFAULT_STYLE:
            saved_style = self._DEFAULT_STYLE
        self._style = saved_style
        self._get_settings().setValue(self._STYLE_SETTINGS_KEY, self._style)
        self._get_settings().sync()
        QApplication.setStyle(self._style)

        saved_mode = self._get_settings().value(self._SETTINGS_KEY, self._DEFAULT_MODE)
        self._mode = (
            saved_mode
            if isinstance(saved_mode, str) and saved_mode in self._VALID_MODES
            else self._DEFAULT_MODE
        )
        saved_color = self._get_settings().value(
            self._COLOR_SETTINGS_KEY, self._DEFAULT_COLOR
        )
        if not isinstance(saved_color, str) or saved_color not in self._COLOR_OPTIONS:
            saved_color = self._DEFAULT_COLOR
        self._color = saved_color

        self._apply_theme(self._mode, persist=False)
        self._install_titlebar_event_filter()

    def _log_debug(self, message: str) -> None:
        """Wrapper seguro para logs de debug, evitando acesso protegido em filtros Qt."""
        try:
            self._logger.debug(message, exc_info=True)
        except Exception:  # pylint: disable=broad-exception-caught
            pass

    def _install_titlebar_event_filter(self) -> None:
        """Instala um event filter global para aplicar dark title bar em todas as janelas."""
        app = QApplication.instance()
        if app is None:
            return
        if self._event_filter is not None:
            return

        class _TitleBarEventFilter(QObject):
            def __init__(self, manager: "ThemeManager") -> None:
                super().__init__()
                self._manager = manager

            def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # pylint: disable=invalid-name,protected-access
                """Registra janelas top-level exibidas para aplicar dark title bar."""
                if event.type() == QEvent.Type.Show and isinstance(watched, QWidget):
                    # Registrar apenas janelas/top-level para evitar registrar cada child widget
                    if getattr(watched, "isWindow", lambda: False)():
                        try:
                            self._manager.register_window(
                                cast(QWidget, watched))
                        except Exception:  # pylint: disable=broad-exception-caught
                            manager_log = getattr(
                                self._manager, "_log_debug", None)
                            if callable(manager_log):
                                manager_log(
                                    "Falha ao registrar janela no filtro")
                return False

        self._event_filter = _TitleBarEventFilter(self)
        try:
            app.installEventFilter(self._event_filter)
        except Exception:  # pylint: disable=broad-exception-caught
            self._logger.debug(
                "Falha ao instalar event filter global de title bar", exc_info=True)

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
        self._get_settings().setValue(self._COLOR_SETTINGS_KEY, color_key)
        self._get_settings().sync()
        self._apply_theme(self._mode, persist=False)
        self._notify_color_listeners()
        self._update_color_actions()

    def apply_style(self, style: str) -> None:
        """Aplica um novo estilo para a aplicação."""
        if style == self._style:
            return
        self._style = style
        self._get_settings().setValue(self._STYLE_SETTINGS_KEY, style)
        self._get_settings().sync()
        QApplication.setStyle(style)
        app = QApplication.instance()
        if app:
            try:
                app.setStyleSheet(get_widgets_styles(self._mode))
            except Exception:  # pylint: disable=broad-exception-caught
                self._logger.debug(
                    "Falha ao reaplicar stylesheet após trocar estilo", exc_info=True)
            for widget in QApplication.allWidgets():
                widget.repaint()

    def refresh_interface(self) -> None:
        """Reaplica tema e força repaint para corrigir artefatos visuais."""
        self._apply_theme(self._mode, persist=False)

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

    def register_color_actions(self, actions: Dict[str, Any]) -> None:
        """Registra actions do menu de cores para manter check sincronizado."""
        self._color_actions = dict(actions)
        self._update_color_actions()

    def unregister_color_actions(self) -> None:
        """Remove o registro de actions de cor."""
        self._color_actions = {}

    def _update_color_actions(self) -> None:
        actions = getattr(self, "_color_actions", None)
        if not actions:
            return
        for cor_key, action in actions.items():
            try:
                action.setChecked(cor_key == self._color)
            except Exception:  # pylint: disable=broad-exception-caught
                self._logger.debug(
                    "Não foi possível atualizar action de cor %s", cor_key)

    def _create_light_palette(self, accent_color: QColor) -> QPalette:
        """Cria uma paleta clara nativa com cor de destaque."""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase,
                         QColor(245, 245, 245))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Link, accent_color)
        palette.setColor(QPalette.ColorRole.Highlight, accent_color)
        palette.setColor(QPalette.ColorRole.HighlightedText,
                         QColor(255, 255, 255))
        return palette

    def _create_dark_palette(self, accent_color: QColor) -> QPalette:
        """Cria uma paleta escura nativa com cor de destaque."""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, accent_color)
        palette.setColor(QPalette.ColorRole.Highlight, accent_color)
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
        return palette

    def _apply_theme(self, mode: str, *, persist: bool) -> None:
        selected = mode if mode in self._VALID_MODES else self._DEFAULT_MODE
        resolved = selected
        app = QApplication.instance()
        if app is None:
            return
        app = cast(QApplication, app)
        accent_hex = self._get_accent_hex()
        if not accent_hex:
            accent_hex = self._COLOR_OPTIONS[self._DEFAULT_COLOR][1]
        accent_color = QColor(accent_hex)
        palette = (
            self._create_dark_palette(accent_color)
            if resolved == "dark"
            else self._create_light_palette(accent_color)
        )
        app.setPalette(palette)
        try:
            app.setStyleSheet(get_widgets_styles(resolved))
        except Exception:  # pylint: disable=broad-exception-caught
            self._logger.debug(
                "Falha ao aplicar stylesheet de widgets", exc_info=True)
        for widget in QApplication.allWidgets():
            widget.repaint()
        self._mode = selected
        if persist:
            self._get_settings().setValue(self._SETTINGS_KEY, selected)
            self._get_settings().sync()
        self._update_actions()
        self._update_all_title_bars()
        for callback in list(self._listeners):
            try:
                callback(selected)
            except Exception:  # pylint: disable=broad-exception-caught
                self._logger.debug("Listener de tema falhou", exc_info=True)

        # Atualiza cache de accent atual
        # Sem cor dinâmica de sistema; cache removido

    @classmethod
    def available_themes(cls) -> List[str]:
        """Lista de temas disponíveis."""
        return sorted(cls._VALID_MODES)

    @classmethod
    def color_options(cls) -> dict[str, tuple[str, str]]:
        """Mapa de cores disponíveis (chave -> (rótulo, hex))."""
        return dict(cls._COLOR_OPTIONS)

    def register_actions(self, actions: Dict[str, Any]) -> None:
        """Registra actions de tema para sincronizar estado checkable."""
        self._actions = dict(actions)
        self._update_actions()

    def unregister_actions(self) -> None:
        """Remove o registro de actions de tema."""
        self._actions = {}

    def _update_actions(self) -> None:
        actions = getattr(self, "_actions", None)
        if not actions:
            return
        for tema, action in actions.items():
            try:
                action.setChecked(tema == self._mode)
            except Exception:  # pylint: disable=broad-exception-caught
                self._logger.debug(
                    "Não foi possível atualizar action de tema %s", tema)

    def _get_accent_hex(self) -> str:
        rotulo_hex = self._COLOR_OPTIONS.get(
            self._color, self._COLOR_OPTIONS[self._DEFAULT_COLOR]
        )
        return rotulo_hex[1]

    def _notify_color_listeners(self) -> None:
        for callback in list(self._color_listeners):
            try:
                callback(self._color)
            except Exception:  # pylint: disable=broad-exception-caught
                self._logger.debug("Listener de cor falhou", exc_info=True)

    def register_window(self, window: QWidget) -> None:
        """Registra janela para aplicar dark title bar em modo escuro."""
        if window not in self._registered_windows:
            self._registered_windows.append(window)
        self._apply_dark_title_bar(window)

    def unregister_window(self, window: QWidget) -> None:
        """Remove janela previamente registrada."""
        if window in self._registered_windows:
            self._registered_windows.remove(window)

    def _apply_dark_title_bar(self, window: QWidget) -> None:
        if platform.system() != "Windows":
            return
        try:
            hwnd = int(window.winId())
            value = ctypes.c_int(1 if self._mode == "dark" else 0)
            set_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
            # Tenta atributo moderno (20) e fallback (19) para versões mais antigas do Windows
            for attribute in (20, 19):
                try:
                    set_attribute(hwnd, attribute, ctypes.byref(value), 4)
                except Exception:  # pylint: disable=broad-exception-caught
                    continue
        except Exception:  # pylint: disable=broad-exception-caught
            self._logger.debug(
                "Falha ao aplicar dark title bar", exc_info=True)

    def _update_all_title_bars(self) -> None:
        for window in list(self._registered_windows):
            self._apply_dark_title_bar(window)
