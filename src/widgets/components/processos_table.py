"""Componentes de tabela para o widget de processos."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Sequence

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QAbstractItemView, QFrame, QHBoxLayout,
                               QHeaderView, QPushButton, QTableWidget,
                               QTableWidgetItem, QVBoxLayout)

from ...ui.delegates import DateEditDelegate
from ...utils.formatters import (formatar_data_para_exibicao,
                                 formatar_valor_monetario)
from ...utils.ui_config import (aplicar_estilo_botao,
                                aplicar_estilo_botao_desabilitado)

__all__ = ["TabelaControls", "criar_tabela", "preencher_tabela"]


@dataclass
class TabelaControls:
    """Agrupa os widgets relacionados à tabela principal."""

    frame: QFrame
    tabela: QTableWidget
    btn_excluir: QPushButton
    aplicar_larguras: Callable[[], None]


def _definir_colunas(tabela: QTableWidget, is_admin: bool) -> List[str]:
    colunas = [
        "Cliente",
        "Processo",
        "Qtd Itens",
        "Data Entrada",
        "Data Processo",
        "Tempo Corte",
        "Valor (R$)",
    ]

    if is_admin:
        colunas.insert(0, "Usuário")

    tabela.setColumnCount(len(colunas))
    tabela.setHorizontalHeaderLabels(colunas)
    return colunas


def criar_tabela(
    *,
    parent,
    is_admin: bool,
    on_item_changed: Callable[[QTableWidgetItem], None],
    on_excluir: Callable[[], None],
) -> TabelaControls:
    # pylint: disable=too-many-locals, too-many-statements
    """Cria o quadro contendo a tabela principal e o botão de exclusão."""

    frame = QFrame(parent)
    frame.setFrameStyle(QFrame.StyledPanel)

    layout = QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(10)

    tabela = QTableWidget(frame)
    colunas = _definir_colunas(tabela, is_admin)

    tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
    tabela.setSelectionMode(QAbstractItemView.SingleSelection)

    header = tabela.horizontalHeader()
    porcentagens_colunas = (
        [10, 22, 18, 9, 11, 11, 8, 11] if is_admin else [28, 20, 10, 12, 12, 8, 10]
    )

    def calcular_larguras_colunas() -> List[int]:
        largura_disponivel = tabela.viewport().width()
        if largura_disponivel <= 0:
            largura_disponivel = 800
        larguras_calculadas: List[int] = []
        largura_total_calculada = 0
        for porcentagem in porcentagens_colunas[:-1]:
            largura = int((largura_disponivel * porcentagem) / 100)
            largura = max(largura, 50)
            larguras_calculadas.append(largura)
            largura_total_calculada += largura
        largura_ultima_coluna = largura_disponivel - largura_total_calculada
        largura_ultima_coluna = max(largura_ultima_coluna, 50)
        larguras_calculadas.append(largura_ultima_coluna)
        return larguras_calculadas

    def aplicar_larguras() -> None:
        for indice, largura in enumerate(calcular_larguras_colunas()):
            if indice < tabela.columnCount():
                header.setSectionResizeMode(indice, QHeaderView.Fixed)
                tabela.setColumnWidth(indice, largura)

    aplicar_larguras()

    offset = 1 if is_admin else 0

    processo_col_index = 1 + offset
    processo_header_item = QTableWidgetItem("Processo")
    processo_header_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
    tabela.setHorizontalHeaderItem(processo_col_index, processo_header_item)

    qtd_col_index = 2 + offset
    qtd_header_item = QTableWidgetItem("Qtd Itens")
    qtd_header_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
    tabela.setHorizontalHeaderItem(qtd_col_index, qtd_header_item)

    data_entrada_col_index = 3 + offset
    data_entrada_header_item = QTableWidgetItem("Data Entrada")
    data_entrada_header_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
    tabela.setHorizontalHeaderItem(data_entrada_col_index, data_entrada_header_item)

    data_processo_col_index = 4 + offset
    data_processo_header_item = QTableWidgetItem("Data Processo")
    data_processo_header_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
    tabela.setHorizontalHeaderItem(data_processo_col_index, data_processo_header_item)

    tempo_corte_col_index = 5 + offset
    tempo_corte_header_item = QTableWidgetItem("Tempo Corte")
    tempo_corte_header_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
    tabela.setHorizontalHeaderItem(tempo_corte_col_index, tempo_corte_header_item)

    valor_col_index = len(colunas) - 1
    valor_header_item = QTableWidgetItem("Valor (R$)")
    valor_header_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
    tabela.setHorizontalHeaderItem(valor_col_index, valor_header_item)

    date_delegate = DateEditDelegate(tabela)
    if is_admin:
        tabela.setItemDelegateForColumn(4, date_delegate)
        tabela.setItemDelegateForColumn(5, date_delegate)
    else:
        tabela.setItemDelegateForColumn(3, date_delegate)
        tabela.setItemDelegateForColumn(4, date_delegate)

    tabela.setToolTip(
        "Clique duas vezes em uma célula para editar diretamente na tabela"
    )
    tabela.itemChanged.connect(on_item_changed)

    def _on_resize(event):
        QTableWidget.resizeEvent(tabela, event)  # type: ignore[misc]
        QTimer.singleShot(50, aplicar_larguras)

    tabela.resizeEvent = _on_resize  # type: ignore[assignment]

    layout.addWidget(tabela)

    btn_excluir = QPushButton("Excluir", frame)
    btn_excluir.setToolTip("Excluir processo selecionado na tabela (Atalho: Delete)")
    btn_excluir.clicked.connect(on_excluir)
    aplicar_estilo_botao(btn_excluir, "vermelho")
    estilo_completo = btn_excluir.styleSheet() + aplicar_estilo_botao_desabilitado()
    btn_excluir.setStyleSheet(estilo_completo)

    botoes_layout = QHBoxLayout()
    botoes_layout.addStretch()
    botoes_layout.addWidget(btn_excluir)

    layout.addLayout(botoes_layout)
    frame.setLayout(layout)

    return TabelaControls(
        frame=frame,
        tabela=tabela,
        btn_excluir=btn_excluir,
        aplicar_larguras=aplicar_larguras,
    )


def preencher_tabela(
    *,
    tabela: QTableWidget,
    registros: Sequence[Sequence[object]],
    is_admin: bool,
) -> None:
    # pylint: disable=too-many-locals
    """Preenche a tabela com os registros fornecidos."""

    tabela.blockSignals(True)
    try:
        tabela.setRowCount(len(registros))
        offset = 1 if is_admin else 0

        for row, registro in enumerate(registros):
            if is_admin:
                item_usuario = QTableWidgetItem(str(registro[1]))
                item_usuario.setFlags(item_usuario.flags() & ~Qt.ItemIsEditable)
                tabela.setItem(row, 0, item_usuario)

            item_cliente = QTableWidgetItem(str(registro[2]).upper())
            tabela.setItem(row, offset + 0, item_cliente)

            item_processo = QTableWidgetItem(str(registro[3]))
            item_processo.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            tabela.setItem(row, offset + 1, item_processo)

            item_qtde = QTableWidgetItem(str(registro[4]))
            item_qtde.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            tabela.setItem(row, offset + 2, item_qtde)

            data_entrada_formatada = formatar_data_para_exibicao(registro[5])
            item_data_entrada = QTableWidgetItem(data_entrada_formatada)
            item_data_entrada.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            tabela.setItem(row, offset + 3, item_data_entrada)

            data_processo_formatada = (
                formatar_data_para_exibicao(registro[6])
                if registro[6]
                else "Não processado"
            )
            item_data_processo = QTableWidgetItem(data_processo_formatada)
            item_data_processo.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            tabela.setItem(row, offset + 4, item_data_processo)

            tempo_corte_display = registro[7] or ""
            item_tempo_corte = QTableWidgetItem(tempo_corte_display)
            item_tempo_corte.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            tabela.setItem(row, offset + 5, item_tempo_corte)

            item_valor = QTableWidgetItem(formatar_valor_monetario(registro[8]))
            item_valor.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            tabela.setItem(row, offset + 6, item_valor)

            tabela.item(row, offset + 0).setData(Qt.UserRole, registro[0])
    finally:
        tabela.blockSignals(False)
