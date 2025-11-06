"""Formulário de manual/contextual help da aplicação."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from src.forms.common.context_help import (
    get_help_entry,
    iter_help_entries,
    register_manual_launcher,
)


@dataclass(frozen=True)
class ManualSection:
    """Representa uma seção do manual do sistema."""
    key: str
    label: str


_DEFAULT_SECTIONS: tuple[ManualSection, ...] = (
    ManualSection("manual", "Manual do Sistema"),
    ManualSection("autenticacao", "Autenticação"),
    ManualSection("visao_geral", "Visão Geral"),
    ManualSection("filtros", "Filtros e Pesquisa"),
    ManualSection("totais", "Painel de Totais"),
    ManualSection("dashboard", "Dashboard"),
    ManualSection("admin", "Ferramentas Administrativas"),
    ManualSection("sobre", "Sobre a Aplicação"),
)


class ManualDialog(QDialog):
    """Janela do manual do sistema."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Manual do Sistema")
        self.resize(600, 400)
        self.setMinimumSize(600, 400)
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

        self._sections: list[ManualSection] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        self._section_list = QListWidget(splitter)
        self._section_list.setUniformItemSizes(True)
        self._section_list.setSelectionMode(
            QListWidget.SelectionMode.SingleSelection
        )
        self._section_list.currentItemChanged.connect(
            self._on_section_selected)

        self._content_browser = QTextBrowser(splitter)
        self._content_browser.setOpenExternalLinks(True)
        self._content_browser.setOpenLinks(False)
        self._content_browser.anchorClicked.connect(QDesktopServices.openUrl)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

        # Larguras iniciais do painel: lista (esquerda) e conteúdo (direita)
        # Mantém a lista legível e o conteúdo com maior área de leitura.
        self._section_list.setMinimumWidth(160)
        splitter.setSizes([160, 340])

        self._populate_sections(_DEFAULT_SECTIONS)
        # Seleciona a seção "Manual do Sistema" ao abrir pela primeira vez
        self.show_section("manual")

    # ------------------------------------------------------------------
    # UI Helpers
    # ------------------------------------------------------------------
    def _populate_sections(self, sections: Iterable[ManualSection]) -> None:
        self._sections = list(sections)
        self._section_list.clear()

        keys = [section.key for section in self._sections]
        help_map = {key: entry for key, entry in iter_help_entries(keys)}

        for section in self._sections:
            item = QListWidgetItem(section.label)
            item.setData(Qt.ItemDataRole.UserRole, section.key)
            if section.key not in help_map:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self._section_list.addItem(item)

        if self._section_list.count() > 0:
            self._section_list.setCurrentRow(0)

    def _on_section_selected(
        self, current: QListWidgetItem | None, _previous: QListWidgetItem | None
    ) -> None:
        if current is None:
            self._content_browser.clear()
            return

        key = current.data(Qt.ItemDataRole.UserRole)
        if not isinstance(key, str):
            self._content_browser.clear()
            return

        title_html, body_html = get_help_entry(key)
        self._content_browser.setHtml(f"{title_html}\n{body_html}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def show_section(self, key: Optional[str]) -> None:
        """Mostra a seção do manual identificada pela chave fornecida."""
        if key is None:
            return
        for index in range(self._section_list.count()):
            item = self._section_list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == key:
                self._section_list.setCurrentItem(item)
                break

    # ------------------------------------------------------------------
    # Qt overrides
    # ------------------------------------------------------------------
    def closeEvent(self, event: QCloseEvent) -> None:  # pylint: disable=invalid-name
        """Intercepta o evento de fechamento para esconder a janela ao invés de destruí-la."""
        self.hide()
        event.ignore()


_DIALOG_INSTANCE: ManualDialog | None = None


def _ensure_dialog(parent: QWidget | None) -> ManualDialog:
    global _DIALOG_INSTANCE  # pylint: disable=global-statement
    if _DIALOG_INSTANCE is None:
        _DIALOG_INSTANCE = ManualDialog(parent)
    elif parent is not None and _DIALOG_INSTANCE.parent() is None:
        _DIALOG_INSTANCE.setParent(parent)
    return _DIALOG_INSTANCE


def mostrar_manual(
    parent: QWidget | None = None,
    section: Optional[str] = None,
    _focus_only: bool = False,
) -> ManualDialog:
    """Cria ou apresenta o manual do sistema."""

    dialog = _ensure_dialog(parent)
    if section:
        dialog.show_section(section)

    if not dialog.isVisible():
        dialog.show()
    dialog.raise_()
    dialog.activateWindow()

    return dialog


def _manual_launcher_adapter(
    parent: QWidget | None,
    section: Optional[str],
    focus_only: bool,
) -> ManualDialog:
    return mostrar_manual(parent, section, focus_only)


register_manual_launcher(_manual_launcher_adapter)
