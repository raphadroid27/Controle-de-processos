"""Controlador auxiliar para os filtros de período do widget de processos."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from PySide6.QtWidgets import QComboBox


@dataclass
class PeriodoFiltroController:
    """Gerencia a configuração e seleção dos filtros de ano/período."""

    combo_ano: QComboBox
    combo_periodo: QComboBox
    listar_anos: Callable[[str | None], Iterable[str]]
    listar_periodos: Callable[[str, str | None], Iterable[dict]]
    obter_usuario: Callable[[], str | None]

    def configurar(self, *, fallback_ano: str | None = None) -> None:
        """Recarrega os combos de ano e período."""
        usuario_filtro = self.obter_usuario()

        self.combo_ano.blockSignals(True)
        self.combo_periodo.blockSignals(True)
        try:
            ano_selecionado = self.combo_ano.currentText()

            self.combo_ano.clear()
            self.combo_ano.addItem("Todos os anos")

            for ano in self.listar_anos(usuario_filtro):
                self.combo_ano.addItem(str(ano))

            self._restaurar_ano(ano_selecionado, fallback_ano)
            self.atualizar_periodos()
        finally:
            self.combo_ano.blockSignals(False)
            self.combo_periodo.blockSignals(False)

    def atualizar_periodos(self) -> None:
        """Atualiza o combo de períodos conforme o ano selecionado."""
        usuario_filtro = self.obter_usuario()
        ano_selecionado = self.combo_ano.currentText()

        self.combo_periodo.clear()
        self.combo_periodo.addItem("Todos os períodos")

        for periodo in self.listar_periodos(ano_selecionado, usuario_filtro):
            self.combo_periodo.addItem(periodo["display"])
            index = self.combo_periodo.count() - 1
            self.combo_periodo.setItemData(
                index,
                {
                    "inicio": periodo["inicio"],
                    "fim": periodo["fim"],
                },
            )

    def on_ano_changed(self) -> None:
        """Manipula a mudança de ano disparada pelo combo."""
        self.combo_periodo.blockSignals(True)
        try:
            self.atualizar_periodos()
        finally:
            self.combo_periodo.blockSignals(False)

    def selecionar_ano(self, ano: str) -> None:
        """Seleciona o ano informado, se existir."""
        if not ano:
            return

        self.combo_ano.blockSignals(True)
        try:
            index = self.combo_ano.findText(ano)
            if index >= 0:
                self.combo_ano.setCurrentIndex(index)
        finally:
            self.combo_ano.blockSignals(False)

    def selecionar_periodo_por_datas(self, display: str) -> None:
        """Seleciona um período a partir de sua representação textual."""
        self.combo_periodo.blockSignals(True)
        try:
            index = self.combo_periodo.findText(display)
            if index >= 0:
                self.combo_periodo.setCurrentIndex(index)
        finally:
            self.combo_periodo.blockSignals(False)

    def obter_periodo_selecionado(self) -> tuple[str | None, str | None]:
        """Retorna as datas de início/fim associadas ao período atual."""
        if self.combo_periodo.currentText() == "Todos os períodos":
            # Quando "Todos os períodos" é selecionado, mas há um ano específico,
            # filtra pelo ano inteiro
            ano_selecionado = self.combo_ano.currentText()
            if ano_selecionado and ano_selecionado != "Todos os anos":
                try:
                    ano_int = int(ano_selecionado)
                    return f"{ano_int}-01-01", f"{ano_int}-12-31"
                except ValueError:
                    pass
            return None, None

        index = self.combo_periodo.currentIndex()
        if index <= 0:
            return None, None

        dados = self.combo_periodo.itemData(index)
        if not isinstance(dados, dict):
            return None, None

        return dados.get("inicio"), dados.get("fim")

    def _restaurar_ano(self, selecionado: str, fallback: str | None) -> None:
        """Restaura o ano previamente selecionado ou usa o fallback informado."""
        index_atual = self.combo_ano.findText(selecionado)
        if index_atual >= 0:
            self.combo_ano.setCurrentIndex(index_atual)
            return

        if fallback:
            index_fallback = self.combo_ano.findText(fallback)
            if index_fallback >= 0:
                self.combo_ano.setCurrentIndex(index_fallback)
