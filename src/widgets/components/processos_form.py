"""Componentes reutilizáveis do formulário de processos."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QPushButton

from ...utils.ui_config import (
    aplicar_estilo_botao,
    configurar_widgets_entrada_uniformes,
)
from ..navigable_widgets import NavigableDateEdit, NavigableLineEdit
from .processos_layout import criar_coluna_rotulo, criar_layout_botao_padrao

__all__ = ["ProcessoFormControls", "criar_formulario"]


@dataclass
class ProcessoFormControls:
    """Agrupa os widgets relevantes do formulário de processos."""

    frame: QGroupBox
    cliente: NavigableLineEdit
    processo: NavigableLineEdit
    qtde_itens: NavigableLineEdit
    data_entrada: NavigableDateEdit
    data_processo: NavigableDateEdit
    tempo_corte: NavigableLineEdit
    valor_pedido: NavigableLineEdit
    btn_adicionar: QPushButton


def criar_formulario(
    *,
    parent,
    on_tempo_editado: Callable[[str], None],
    on_cliente_editado: Callable[[str], None],
    on_submit: Callable[[], None],
) -> ProcessoFormControls:
    """Monta o formulário de cadastro de processos."""

    # pylint: disable=too-many-locals

    frame = QGroupBox("Novo registro", parent)

    entry_cliente = NavigableLineEdit(frame)
    entry_cliente.setPlaceholderText("Informe o cliente responsável")
    entry_cliente.setToolTip(
        "Nome do cliente. Use Tab para avançar e Ctrl+Enter para adicionar rapidamente."
    )
    entry_processo = NavigableLineEdit(frame)
    entry_processo.setPlaceholderText("Descreva o processo")
    entry_processo.setToolTip(
        "Descrição do processo ou atividade. Campos obrigatórios são marcados."
    )
    entry_qtde_itens = NavigableLineEdit(frame)
    entry_qtde_itens.setPlaceholderText("0")
    entry_qtde_itens.setToolTip(
        "Quantidade de itens do processo. Apenas números positivos."
    )

    entry_data_entrada = NavigableDateEdit(frame)
    entry_data_entrada.setDate(QDate.currentDate())
    entry_data_entrada.setCalendarPopup(True)
    entry_data_entrada.setMaximumDate(QDate.currentDate())
    entry_data_entrada.setToolTip("Data de entrada do pedido. Não pode ser futura.")

    entry_data_processo = NavigableDateEdit(frame)
    entry_data_processo.setCalendarPopup(True)
    entry_data_processo.setSpecialValueText("Não processado")
    entry_data_processo.setMaximumDate(QDate.currentDate())
    entry_data_processo.setDate(QDate.currentDate())
    entry_data_processo.setToolTip(
        "Data de processamento. Mantenha em 'Não processado' se ainda pendente."
    )

    entry_tempo_corte = NavigableLineEdit(frame)
    entry_tempo_corte.setPlaceholderText("HH:MM:SS")
    entry_tempo_corte.textEdited.connect(on_tempo_editado)
    entry_tempo_corte.setToolTip(
        "Tempo de corte no formato HH:MM:SS. O sistema valida automaticamente."
    )

    entry_valor_pedido = NavigableLineEdit(frame)
    entry_valor_pedido.setPlaceholderText("0.00")
    entry_valor_pedido.setToolTip(
        "Valor total em reais. Utilize vírgula ou ponto como separador decimal."
    )

    widgets: Sequence[NavigableLineEdit | NavigableDateEdit] = (
        entry_cliente,
        entry_processo,
        entry_qtde_itens,
        entry_data_entrada,
        entry_data_processo,
        entry_tempo_corte,
        entry_valor_pedido,
    )

    configurar_widgets_entrada_uniformes(list(widgets))
    for campo in widgets:
        campo.set_campos_navegacao(list(widgets))

    entry_cliente.textChanged.connect(on_cliente_editado)

    campos_layout = QHBoxLayout()
    campos_layout.setSpacing(10)
    campos_layout.setContentsMargins(8, 8, 8, 8)

    colunas_info = (
        ("Cliente:", entry_cliente, 3),
        ("Processo:", entry_processo, 3),
        ("Qtd. Itens:", entry_qtde_itens, 2),
        ("Data Entrada:", entry_data_entrada, 2),
        ("Data Processo:", entry_data_processo, 2),
        ("Tempo Corte:", entry_tempo_corte, 2),
        ("Valor (R$):", entry_valor_pedido, 2),
    )

    for texto, widget, peso in colunas_info:
        coluna, peso_col = criar_coluna_rotulo(texto, widget, peso)
        campos_layout.addLayout(coluna, peso_col)

    btn_adicionar = QPushButton("Adicionar", frame)
    btn_adicionar.setToolTip("Adicionar novo processo (Atalho: Enter)")
    aplicar_estilo_botao(btn_adicionar, "verde", largura_minima=90)
    btn_adicionar.clicked.connect(on_submit)
    btn_layout = criar_layout_botao_padrao(btn_adicionar)
    campos_layout.addLayout(btn_layout, 1)

    frame.setLayout(campos_layout)

    return ProcessoFormControls(
        frame=frame,
        cliente=entry_cliente,
        processo=entry_processo,
        qtde_itens=entry_qtde_itens,
        data_entrada=entry_data_entrada,
        data_processo=entry_data_processo,
        tempo_corte=entry_tempo_corte,
        valor_pedido=entry_valor_pedido,
        btn_adicionar=btn_adicionar,
    )
