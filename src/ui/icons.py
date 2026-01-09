"""
Gerenciamento centralizado de ícones para a aplicação.
"""
from __future__ import annotations

import qtawesome as qta
from PySide6.QtCore import QEvent, QObject
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QPushButton, QTabWidget, QWidget

from src.ui.styles import BUTTON_COLORS
from src.ui.theme_manager import ThemeManager


class IconHoverFilter(QObject):
    """
    Filtro de eventos para lidar com eventos de mouse hover em ícones.
    Altera a cor do ícone quando o mouse entra ou sai do widget.
    """

    def __init__(self, target: QObject, name: str, color_normal: str, color_active: str):
        super().__init__(target)
        self.target = target
        self.name = name
        self.color_normal = color_normal
        self.color_active = color_active
        self._icon_normal = qta.icon(name, color=color_normal)
        self._icon_active = qta.icon(name, color=color_active)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Lida com eventos hover para alternar cores dos ícones."""
        # pylint: disable=invalid-name, unused-argument
        if event.type() == QEvent.Type.Enter:
            if hasattr(self.target, "setIcon"):
                self.target.setIcon(self._icon_active)
        elif event.type() == QEvent.Type.Leave:
            if hasattr(self.target, "setIcon"):
                self.target.setIcon(self._icon_normal)
        return False


def _get_contrast_text_color(color_name: str | None) -> str:
    """Retorna a cor do texto que deve ser usada sobre a cor de destaque fornecida."""
    color_info = BUTTON_COLORS.get(color_name, {})
    # Retorna a cor definida em 'text' ou 'white' como fallback
    return color_info.get("text", "white")


def _remove_hover_filter(target: QObject) -> None:
    """Remove e limpa o filtro de hover 'qta_hover_filter' se existir."""
    old_filter = target.property("qta_hover_filter")
    if old_filter and isinstance(old_filter, QObject):
        target.removeEventFilter(old_filter)
        target.setProperty("qta_hover_filter", None)


def _get_colors_for_theme(color_normal: str | None = None, color_active: str | None = None):
    manager = ThemeManager.instance()
    mode = manager.current_mode

    # Determina a cor ativa com base na cor de contraste do texto do destaque atual
    default_active = _get_contrast_text_color(manager.current_color)

    if mode == "dark":
        default_normal = "#e8eaed"
    else:
        default_normal = "#5f6368"

    final_normal = color_normal or default_normal
    final_active = color_active or default_active
    return final_normal, final_active


def get_icon(name: str, color_normal: str | None = None, color_active: str | None = None) -> QIcon:
    """
    Cria um ícone qtawesome.
    Nota: retorno puramente estático, não lida automaticamente com invalidação de hover
    a menos que usado com a interação set_icon.
    """
    final_normal, final_active = _get_colors_for_theme(
        color_normal, color_active)
    return qta.icon(name, color=final_normal, color_active=final_active)


def set_icon(
    target: QObject,
    name: str,
    color_normal: str | None = None,
    color_active: str | None = None
) -> None:
    """
    Define o ícone em um widget ou ação, armazena metadados e instala filtro de hover.
    """
    # Detecta se o alvo é um QPushButton (geralmente botões coloridos neste app)
    is_button = isinstance(target, QPushButton)

    if is_button:
        # Botões mantêm cores fixas de ícone e não mudam com tema/hover.
        # Tenta obter a cor definida pelo estilo (via aplicar_estilo_botao)
        # Se 'qta_style' não estiver definido ou for inválido, assume branco
        style_color = target.property("qta_style")
        default_color = _get_contrast_text_color(style_color)

        final_normal = color_normal or default_color
        final_active = color_active or final_normal

        # Força a cor de desabilitado para corresponder ao normal (branco) para
        # garantir visibilidade em fundos coloridos mesmo quando o botão está desabilitado.
        icon = qta.icon(name, color=final_normal, color_disabled=final_normal)
        if hasattr(target, "setIcon"):
            target.setIcon(icon)

        # Armazena propriedades (fixas)
        target.setProperty("qta_icon", name)
        target.setProperty("qta_color_normal", final_normal)
        target.setProperty("qta_color_active", final_active)

        # Remove qualquer filtro de hover existente
        _remove_hover_filter(target)

        return

    # Calcula cores para outros widgets/ações
    final_normal, final_active = _get_colors_for_theme(
        color_normal, color_active)

    # Ajuste específico para QAction no modo escuro:
    # Se o texto fica escuro no hover (fundo claro), o ícone deve acompanhar.
    # Força cor escura para active se o padrão calculado for branco.
    if isinstance(target, QAction):
        manager = ThemeManager.instance()
        if manager.current_mode == "dark":
            if final_active.lower() in ("white", "#ffffff", "#fff"):
                final_active = "#333333"

    # Define o ícone inicial
    icon = qta.icon(name, color=final_normal, color_active=final_active)
    if hasattr(target, "setIcon"):
        target.setIcon(icon)

    # Armazena propriedades para atualizações de tema
    target.setProperty("qta_icon", name)
    if color_normal:
        target.setProperty("qta_color_normal", color_normal)
    if color_active:
        target.setProperty("qta_color_active", color_active)

    # Instala ou atualiza filtro de hover se o alvo for um widget
    if isinstance(target, QWidget):
        _remove_hover_filter(target)

        hover_filter = IconHoverFilter(
            target, name, final_normal, final_active)
        target.installEventFilter(hover_filter)
        target.setProperty("qta_hover_filter", hover_filter)


def set_tab_icon(
    tab_widget: QTabWidget,
    index: int,
    name: str,
    color_normal: str | None = None,
    color_active: str | None = None
) -> None:
    """
    Define o ícone para uma aba específica em um QTabWidget e armazena metadados para atualizações.
    Nota: Efeito de hover em abas é mais difícil de obter via filtro de eventos em abas individuais.
    """
    icon = get_icon(name, color_normal, color_active)
    tab_widget.setTabIcon(index, icon)

    # Armazena metadados no widget da página
    widget = tab_widget.widget(index)
    if widget:
        widget.setProperty("qta_tab_icon", name)
        if color_normal:
            widget.setProperty("qta_color_normal", color_normal)
        if color_active:
            widget.setProperty("qta_color_active", color_active)


def update_icons(root: QObject) -> None:
    """
    Atualiza recursivamente ícones no objeto e seus filhos com base no tema atual.
    """
    # Verifica a própria raiz
    if root.property("qta_icon"):
        name = root.property("qta_icon")
        c_norm = root.property("qta_color_normal")
        c_act = root.property("qta_color_active")

        # Reaplica set_icon para atualizar cores e filtro
        set_icon(root, name, c_norm, c_act)

    # Tratamento especial para QTabWidget
    if isinstance(root, QTabWidget):
        for i in range(root.count()):
            widget = root.widget(i)
            if widget and widget.property("qta_tab_icon"):
                name = widget.property("qta_tab_icon")
                c_norm = widget.property("qta_color_normal")
                c_act = widget.property("qta_color_active")

                # Simplesmente atualiza o ícone, hover em abas ainda não é suportado
                # por este auxiliar
                icon = get_icon(name, c_norm, c_act)
                root.setTabIcon(i, icon)

    # Verifica filhos
    children = root.findChildren(QObject)
    for child in children:
        # Atualização recursiva para filhos
        update_icons(child)
