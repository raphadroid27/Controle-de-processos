"""Gerenciamento dos campos de autocompletar para o widget de processos."""

from __future__ import annotations

from typing import Callable, Iterable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCompleter, QLineEdit, QWidget


class AutocompleteManager:
    """Centraliza a configuração dos autocompletes utilizados no widget."""

    def __init__(
        self,
        *,
        parent: QWidget,
        carregar_clientes: Callable[[], Iterable[str]],
    ):
        """Inicializa gerenciador de autocompletar com pai e função de carregamento."""
        self._parent = parent
        self._carregar_clientes = carregar_clientes
        self._form_entry: QLineEdit | None = None
        self._filter_entry: QLineEdit | None = None

    def configure_form(self, entry: QLineEdit) -> None:
        """Aplica autocompletar ao campo do formulário principal."""
        self._form_entry = entry
        self._aplicar_completer(entry)

    def configure_filter(self, entry: QLineEdit) -> None:
        """Aplica autocompletar ao campo de filtro de cliente."""
        self._filter_entry = entry
        self._aplicar_completer(entry)

    def refresh_form(self) -> None:
        """Atualiza as sugestões do autocompletar do formulário."""
        if self._form_entry is None:
            return
        self._aplicar_completer(self._form_entry)

    def refresh_filter(self) -> None:
        """Atualiza as sugestões do autocompletar do filtro."""
        if self._filter_entry is None:
            return
        self._aplicar_completer(self._filter_entry)

    def refresh_all(self) -> None:
        """Atualiza todos os autocompletes configurados."""
        self.refresh_form()
        self.refresh_filter()

    def _aplicar_completer(self, entry: QLineEdit) -> None:
        clientes = list(self._carregar_clientes())
        completer = QCompleter(clientes, self._parent)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchStartsWith)

        entry.blockSignals(True)
        entry.setCompleter(completer)
        entry.blockSignals(False)
