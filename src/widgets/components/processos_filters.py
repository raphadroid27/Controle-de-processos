"""Componentes de filtro para o widget de processos."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (QComboBox, QGroupBox, QHBoxLayout, QLineEdit,
                               QPushButton)

from ...utils.ui_config import (aplicar_estilo_botao,
                                aplicar_estilo_botao_desabilitado,
                                configurar_widgets_entrada_uniformes)
from ..navigable_widgets import NavigableComboBox, NavigableLineEdit
from .processos_layout import criar_coluna_rotulo, criar_layout_botao_padrao

__all__ = ["FiltroControls", "criar_filtros"]


@dataclass
class FiltroControls:
    """Agrupa widgets e timers associados aos filtros do painel."""

    frame: QGroupBox
    combo_usuario: Optional[QComboBox]
    entry_cliente: QLineEdit
    entry_processo: QLineEdit
    combo_ano: QComboBox
    combo_periodo: QComboBox
    btn_limpar: QPushButton
    timer_cliente: QTimer
    timer_processo: QTimer


def criar_filtros(
    *,
    parent,
    is_admin: bool,
    on_cliente_timeout: Callable[[], None],
    on_processo_timeout: Callable[[], None],
    on_ano_changed: Callable[[str], None],
    on_periodo_changed: Callable[[str], None],
    on_usuario_changed: Callable[[str], None],
    on_limpar: Callable[[], None],
) -> FiltroControls:
    """Cria o frame e widgets do painel de filtros."""

    # pylint: disable=too-many-locals, too-many-statements

    frame = QGroupBox("Buscar registros", parent)

    layout = QHBoxLayout()
    layout.setSpacing(10)
    layout.setContentsMargins(8, 8, 8, 8)

    combo_usuario = None
    if is_admin:
        combo_usuario = NavigableComboBox(frame)
        combo_usuario.addItem("Todos os usuários")
        combo_usuario.currentTextChanged.connect(on_usuario_changed)
        combo_usuario.setToolTip(
            "Selecione um usuário específico para visualizar apenas seus registros."
        )
        coluna_usuario, peso_usuario = criar_coluna_rotulo("Usuário:", combo_usuario, 2)
        layout.addLayout(coluna_usuario, peso_usuario)

    entry_cliente = NavigableLineEdit(frame)
    entry_cliente.setPlaceholderText("Digite o nome do cliente")
    entry_cliente.setToolTip(
        "Filtrar registros pelo prefixo do nome do cliente. O filtro é aplicado automaticamente."
    )
    timer_cliente = QTimer(frame)
    timer_cliente.setSingleShot(True)
    timer_cliente.timeout.connect(on_cliente_timeout)

    entry_cliente.textChanged.connect(lambda _: timer_cliente.start(500))
    coluna_cliente, peso_cliente = criar_coluna_rotulo("Cliente:", entry_cliente, 3)
    layout.addLayout(coluna_cliente, peso_cliente)

    entry_processo = NavigableLineEdit(frame)
    entry_processo.setPlaceholderText("Digite o nome do processo")
    entry_processo.setToolTip(
        "Filtrar processos pelo prefixo informado. Clique em Limpar para remover."
    )
    coluna_processo, peso_processo = criar_coluna_rotulo("Processo:", entry_processo, 3)
    layout.addLayout(coluna_processo, peso_processo)

    timer_processo = QTimer(frame)
    timer_processo.setSingleShot(True)
    timer_processo.timeout.connect(on_processo_timeout)

    entry_processo.textChanged.connect(lambda _: timer_processo.start(500))

    combo_ano = NavigableComboBox(frame)
    combo_ano.addItem("Todos os anos")
    combo_ano.currentTextChanged.connect(on_ano_changed)
    combo_ano.setToolTip("Escolha um ano específico para restringir os resultados.")
    coluna_ano, peso_ano = criar_coluna_rotulo("Ano:", combo_ano, 2)
    layout.addLayout(coluna_ano, peso_ano)

    combo_periodo = NavigableComboBox(frame)
    combo_periodo.addItem("Todos os períodos")
    combo_periodo.currentTextChanged.connect(on_periodo_changed)
    combo_periodo.setToolTip(
        "Selecione um intervalo de faturamento (26 a 25) para refinar a busca."
    )
    coluna_periodo, peso_periodo = criar_coluna_rotulo("Período:", combo_periodo, 3)
    layout.addLayout(coluna_periodo, peso_periodo)

    btn_limpar = QPushButton("Limpar Filtros", frame)
    btn_limpar.setToolTip(
        "Limpar filtros de cliente e processo, mantendo o mês corrente"
    )
    aplicar_estilo_botao(btn_limpar, "laranja", largura_minima=110)
    btn_limpar.clicked.connect(on_limpar)
    estilo_atual = btn_limpar.styleSheet()
    btn_limpar.setStyleSheet(estilo_atual + aplicar_estilo_botao_desabilitado())
    layout.addLayout(criar_layout_botao_padrao(btn_limpar), 1)

    layout.addStretch()
    frame.setLayout(layout)

    widgets_uniformes = [entry_cliente, entry_processo, combo_ano, combo_periodo]
    if combo_usuario is not None:
        widgets_uniformes.append(combo_usuario)
    configurar_widgets_entrada_uniformes(widgets_uniformes)

    navegacao_campos = [
        w
        for w in [
            combo_usuario,
            entry_cliente,
            entry_processo,
            combo_ano,
            combo_periodo,
        ]
        if w is not None
    ]
    for campo in navegacao_campos:
        if hasattr(campo, "set_campos_navegacao"):
            campo.set_campos_navegacao(navegacao_campos)

    return FiltroControls(
        frame=frame,
        combo_usuario=combo_usuario,
        entry_cliente=entry_cliente,
        entry_processo=entry_processo,
        combo_ano=combo_ano,
        combo_periodo=combo_periodo,
        btn_limpar=btn_limpar,
        timer_cliente=timer_cliente,
        timer_processo=timer_processo,
    )
