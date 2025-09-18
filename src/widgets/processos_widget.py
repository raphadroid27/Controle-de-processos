"""
Widget principal para gerenciamento de processos.

Contém a interface principal do sistema com formulário de entrada,
tabela de dados e controles de filtros.
"""

import sqlite3
from datetime import datetime

from PySide6.QtCore import QDate, Qt, QTimer
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QCompleter,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..ui.delegates import DateEditDelegate
from ..utils import database as db
from ..utils.formatters import (
    converter_data_para_banco,
    formatar_data_para_exibicao,
    formatar_valor_monetario,
)
from ..utils.periodo_faturamento import calcular_periodo_faturamento_atual_datas
from ..utils.ui_config import (
    ESPACAMENTO_PADRAO,
    aplicar_estilo_botao,
    aplicar_estilo_botao_desabilitado,
    configurar_widgets_entrada_uniformes,
)
from .navigable_widgets import NavigableDateEdit, NavigableLineEdit


class ProcessosWidget(QWidget):
    """Widget principal para gerenciamento de processos."""

    def __init__(self, usuario_logado, is_admin):
        super().__init__()
        self.is_admin = is_admin
        self.usuario_logado = usuario_logado

        self.frame_entrada = None
        self.botoes_layout = None
        self.frame_totais = None
        self.btn_adicionar = None
        self.btn_excluir = None
        self.entry_cliente = None
        self.entry_processo = None
        self.entry_qtde_itens = None
        self.entry_data_entrada = None
        self.entry_data_processo = None
        self.entry_valor_pedido = None
        self.tabela_layout = None
        self.tabela = None
        self.entry_filtro_cliente = None
        self.entry_filtro_processo = None
        self.timer_cliente = None
        self.timer_processo = None
        self.btn_limpar_filtros = None
        self.label_total_processos = None
        self.label_total_itens = None
        self.label_total_valor = None
        self.shortcut_enter = None
        self.shortcut_enter_num = None
        self.shortcut_delete = None
        self.completer_cliente = None
        self.completer_filtro_cliente = None
        self.combo_usuario = None
        self.combo_filtro_ano = None
        self.combo_filtro_periodo = None
        self.aplicar_larguras_colunas = None

        self.init_ui()
        self.carregar_dados()

    def init_ui(self):
        """Inicializa a interface do usuário."""
        main_layout = QVBoxLayout()

        self.criar_frame_entrada()
        main_layout.addWidget(self.frame_entrada)

        self.criar_tabela()
        main_layout.addLayout(self.tabela_layout)

        self.criar_frame_totais()
        main_layout.addWidget(self.frame_totais)

        self.setLayout(main_layout)

        self.configurar_atalhos()

    def configurar_atalhos(self):
        """Configura os atalhos de teclado para a aplicação."""
        self.shortcut_enter = QShortcut(QKeySequence(Qt.Key.Key_Return), self)
        self.shortcut_enter.activated.connect(self.atalho_adicionar_processo)

        self.shortcut_enter_num = QShortcut(
            QKeySequence(Qt.Key.Key_Enter), self)
        self.shortcut_enter_num.activated.connect(
            self.atalho_adicionar_processo)

        self.shortcut_delete = QShortcut(QKeySequence(Qt.Key.Key_Delete), self)
        self.shortcut_delete.activated.connect(self.excluir_processo)

    def _carregar_clientes_upper(self):
        try:
            clientes_raw = db.buscar_clientes_unicos()
            return [cliente.upper() for cliente in clientes_raw]
        except (sqlite3.Error, RuntimeError, AttributeError, TypeError) as e:
            print(f"Erro ao carregar clientes: {e}")
            return []

    def _novo_completer(self, palavras):
        completer = QCompleter(palavras, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchStartsWith)
        return completer

    def configurar_autocompletar_cliente(self):
        """Configura o autocompletar para o campo cliente."""
        clientes = self._carregar_clientes_upper()
        self.completer_cliente = self._novo_completer(clientes)
        self.entry_cliente.setCompleter(self.completer_cliente)

    def atualizar_autocompletar_cliente(self):
        """Atualiza autocompletar com clientes recentes."""
        clientes = self._carregar_clientes_upper()
        if hasattr(self, "completer_cliente"):
            self.completer_cliente.setModel(None)
            self.completer_cliente = self._novo_completer(clientes)
            self.entry_cliente.setCompleter(self.completer_cliente)

    def configurar_autocompletar_filtro_cliente(self):
        """Configura autocompletar do filtro de cliente."""
        clientes = self._carregar_clientes_upper()
        self.completer_filtro_cliente = self._novo_completer(clientes)
        self.entry_filtro_cliente.setCompleter(self.completer_filtro_cliente)

    def atualizar_autocompletar_filtro_cliente(self):
        """Atualiza autocompletar do filtro com clientes mais recentes."""
        clientes = self._carregar_clientes_upper()
        if hasattr(self, "completer_filtro_cliente"):
            self.completer_filtro_cliente.setModel(None)
            self.completer_filtro_cliente = self._novo_completer(clientes)
            self.entry_filtro_cliente.setCompleter(
                self.completer_filtro_cliente)

    def configurar_filtros_ano_periodo(self):
        """Configura combos de ano e período de faturamento com dados únicos."""
        try:
            if self.is_admin:
                if (
                    hasattr(self, "combo_usuario")
                    and self.combo_usuario.currentText() != "Todos os usuários"
                ):
                    usuario_filtro = self.combo_usuario.currentText()
                else:
                    usuario_filtro = None
            else:
                usuario_filtro = self.usuario_logado

            self.combo_filtro_ano.blockSignals(True)
            self.combo_filtro_periodo.blockSignals(True)

            ano_selecionado = self.combo_filtro_ano.currentText()

            self.combo_filtro_ano.clear()
            self.combo_filtro_ano.addItem("Todos os anos")

            anos_db = db.buscar_anos_unicos(usuario_filtro)

            data_inicio_atual, _ = calcular_periodo_faturamento_atual_datas()
            ano_atual = str(data_inicio_atual.year)
            if ano_atual not in anos_db:
                anos_db.append(ano_atual)

            anos_db.sort(reverse=True)
            for ano in anos_db:
                self.combo_filtro_ano.addItem(ano)

            ano_index = self.combo_filtro_ano.findText(ano_selecionado)
            if ano_index >= 0:
                self.combo_filtro_ano.setCurrentIndex(ano_index)
            else:
                ano_atual_index = self.combo_filtro_ano.findText(ano_atual)
                if ano_atual_index >= 0:
                    self.combo_filtro_ano.setCurrentIndex(ano_atual_index)

            self.configurar_periodos_do_ano()

            self.combo_filtro_ano.blockSignals(False)
            self.combo_filtro_periodo.blockSignals(False)

        except (
            sqlite3.Error,
            RuntimeError,
            AttributeError,
            TypeError,
            ValueError,
        ) as e:
            print(f"Erro ao configurar filtros de ano/período: {e}")
            self.combo_filtro_ano.blockSignals(False)
            self.combo_filtro_periodo.blockSignals(False)

    def configurar_periodos_do_ano(self):
        """Configura o combo de períodos baseado no ano selecionado."""
        try:
            if self.is_admin:
                if (
                    hasattr(self, "combo_usuario")
                    and self.combo_usuario.currentText() != "Todos os usuários"
                ):
                    usuario_filtro = self.combo_usuario.currentText()
                else:
                    usuario_filtro = None
            else:
                usuario_filtro = self.usuario_logado

            self.combo_filtro_periodo.clear()
            self.combo_filtro_periodo.addItem("Todos os períodos")

            ano_selecionado = self.combo_filtro_ano.currentText()

            if ano_selecionado != "Todos os anos":
                periodos_db = db.buscar_periodos_faturamento_por_ano(
                    ano_selecionado, usuario_filtro
                )

                data_inicio_atual, data_fim_atual = (
                    calcular_periodo_faturamento_atual_datas()
                )
                ano_atual = str(data_inicio_atual.year)

                if ano_selecionado == ano_atual:
                    periodo_atual_display = (
                        f"{data_inicio_atual.strftime('%d/%m')} a "
                        f"{data_fim_atual.strftime('%d/%m')}"
                    )

                    periodo_atual_existe = any(
                        p["display"] == periodo_atual_display for p in periodos_db
                    )
                    if not periodo_atual_existe:
                        periodos_db.insert(
                            0,
                            {
                                "display": periodo_atual_display,
                                "inicio": data_inicio_atual.strftime("%Y-%m-%d"),
                                "fim": data_fim_atual.strftime("%Y-%m-%d"),
                            },
                        )

                for periodo in periodos_db:
                    self.combo_filtro_periodo.addItem(periodo["display"])
                    index = self.combo_filtro_periodo.count() - 1
                    self.combo_filtro_periodo.setItemData(
                        index, {
                            "inicio": periodo["inicio"], "fim": periodo["fim"]}
                    )

        except (
            sqlite3.Error,
            RuntimeError,
            AttributeError,
            TypeError,
            ValueError,
        ) as e:
            print(f"Erro ao configurar períodos do ano: {e}")

    def on_ano_changed(self):
        """Reage à mudança de ano no filtro."""
        self.combo_filtro_periodo.blockSignals(True)
        self.configurar_periodos_do_ano()
        self.combo_filtro_periodo.blockSignals(False)
        self.aplicar_filtro()

    def converter_cliente_maiuscula(self, texto):
        """Converte automaticamente o texto do campo cliente para maiúscula."""
        self.entry_cliente.blockSignals(True)
        posicao_cursor = self.entry_cliente.cursorPosition()
        texto_maiusculo = texto.upper()
        self.entry_cliente.setText(texto_maiusculo)
        self.entry_cliente.setCursorPosition(posicao_cursor)
        self.entry_cliente.blockSignals(False)

    def atalho_adicionar_processo(self):
        """Adiciona processo via atalho se campos obrigatórios estiverem ok."""
        cliente = self.entry_cliente.text().strip()
        processo = self.entry_processo.text().strip()
        qtde_itens = self.entry_qtde_itens.text().strip()
        valor_pedido = self.entry_valor_pedido.text().strip()

        if cliente and processo and qtde_itens and valor_pedido:
            self.adicionar_processo()
        else:
            if not cliente:
                self.entry_cliente.setFocus()
            elif not processo:
                self.entry_processo.setFocus()
            elif not qtde_itens:
                self.entry_qtde_itens.setFocus()
            elif not valor_pedido:
                self.entry_valor_pedido.setFocus()

    def configurar_widgets_uniformes(self, widgets_list):
        """Configura widgets para tamanhos uniformes."""
        configurar_widgets_entrada_uniformes(widgets_list)

    def criar_layout_coluna_uniforme(
        self, label_text, widget, peso=1, espacamento_label=3
    ):
        """Cria layout de coluna uniforme (label + widget)."""
        col_layout = QVBoxLayout()
        col_layout.setSpacing(espacamento_label)
        col_layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(label_text)
        label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        label.setMinimumHeight(16)
        label.setMaximumHeight(18)

        col_layout.addWidget(label)
        col_layout.addWidget(widget)

        return col_layout, peso

    def criar_frame_entrada(self):
        """Cria o frame de entrada de dados."""
        self.frame_entrada = QFrame()
        self.frame_entrada.setFrameStyle(QFrame.StyledPanel)

        self.entry_cliente = NavigableLineEdit()
        self.entry_processo = NavigableLineEdit()
        self.entry_qtde_itens = NavigableLineEdit()

        self.entry_data_entrada = NavigableDateEdit()
        self.entry_data_entrada.setDate(QDate.currentDate())
        self.entry_data_entrada.setCalendarPopup(True)
        self.entry_data_entrada.setMaximumDate(QDate.currentDate())

        self.entry_data_processo = NavigableDateEdit()
        self.entry_data_processo.setCalendarPopup(True)
        self.entry_data_processo.setSpecialValueText("Não processado")
        self.entry_data_processo.setMaximumDate(QDate.currentDate())
        self.entry_data_processo.setDate(QDate.currentDate())

        self.entry_valor_pedido = NavigableLineEdit()
        self.entry_valor_pedido.setPlaceholderText("0.00")

        widgets_entrada = [
            self.entry_cliente,
            self.entry_processo,
            self.entry_qtde_itens,
            self.entry_data_entrada,
            self.entry_data_processo,
            self.entry_valor_pedido,
        ]

        self.configurar_widgets_uniformes(widgets_entrada)

        for campo in widgets_entrada:
            campo.set_campos_navegacao(widgets_entrada)

        self.entry_cliente.textChanged.connect(
            self.converter_cliente_maiuscula)
        self.configurar_autocompletar_cliente()

        campos_layout = QHBoxLayout()
        campos_layout.setSpacing(10)
        campos_layout.setContentsMargins(8, 8, 8, 8)

        colunas_info = [
            ("Cliente:", self.entry_cliente, 3),
            ("Processo:", self.entry_processo, 3),
            ("Qtd. Itens:", self.entry_qtde_itens, 2),
            ("Data Entrada:", self.entry_data_entrada, 2),
            ("Data Processo:", self.entry_data_processo, 2),
            ("Valor (R$):", self.entry_valor_pedido, 2),
        ]

        for label_text, widget, peso in colunas_info:
            col_layout, peso_col = self.criar_layout_coluna_uniforme(
                label_text, widget, peso
            )
            campos_layout.addLayout(col_layout, peso_col)

        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(3)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        label_vazio = QLabel("")
        label_vazio.setMinimumHeight(16)
        label_vazio.setMaximumHeight(18)
        btn_layout.addWidget(label_vazio)

        self.btn_adicionar = QPushButton("Adicionar")
        self.btn_adicionar.setToolTip(
            "Adicionar novo processo (Atalho: Enter)")
        aplicar_estilo_botao(self.btn_adicionar, "verde", 90)
        btn_layout.addWidget(self.btn_adicionar)
        campos_layout.addLayout(btn_layout, 1)

        self.frame_entrada.setLayout(campos_layout)
        self.btn_adicionar.clicked.connect(self.adicionar_processo)

    def criar_tabela(self):
        """Cria a interface da tabela de processos com filtros."""
        self.tabela_layout = QVBoxLayout()

        filtros_frame = QFrame()
        filtros_frame.setFrameStyle(QFrame.StyledPanel)

        filtro_completo_layout = QHBoxLayout()
        filtro_completo_layout.setSpacing(10)
        filtro_completo_layout.setContentsMargins(8, 8, 8, 8)

        widgets_filtro = []

        if self.is_admin:
            self.combo_usuario = QComboBox()
            self.combo_usuario.addItem("Todos os usuários")
            widgets_filtro.append(self.combo_usuario)

            usuario_layout, peso_usuario = self.criar_layout_coluna_uniforme(
                "Usuário:", self.combo_usuario, 2
            )
            filtro_completo_layout.addLayout(usuario_layout, peso_usuario)
            self.combo_usuario.currentTextChanged.connect(
                self.on_usuario_changed)

        self.entry_filtro_cliente = QLineEdit()
        self.entry_filtro_cliente.setPlaceholderText(
            "Digite o nome do cliente")
        widgets_filtro.append(self.entry_filtro_cliente)

        cliente_layout, peso_cliente = self.criar_layout_coluna_uniforme(
            "Cliente:", self.entry_filtro_cliente, 3
        )
        filtro_completo_layout.addLayout(cliente_layout, peso_cliente)

        self.timer_cliente = QTimer()
        self.timer_cliente.setSingleShot(True)
        self.timer_cliente.timeout.connect(self.aplicar_filtro)
        self.entry_filtro_cliente.textChanged.connect(
            lambda: self.timer_cliente.start(500)
        )

        self.configurar_autocompletar_filtro_cliente()

        self.entry_filtro_processo = QLineEdit()
        self.entry_filtro_processo.setPlaceholderText(
            "Digite o nome do processo")
        widgets_filtro.append(self.entry_filtro_processo)

        processo_layout, peso_processo = self.criar_layout_coluna_uniforme(
            "Processo:", self.entry_filtro_processo, 3
        )
        filtro_completo_layout.addLayout(processo_layout, peso_processo)

        self.timer_processo = QTimer()
        self.timer_processo.setSingleShot(True)
        self.timer_processo.timeout.connect(self.aplicar_filtro)
        self.entry_filtro_processo.textChanged.connect(
            lambda: self.timer_processo.start(500)
        )

        self.combo_filtro_ano = QComboBox()
        self.combo_filtro_ano.addItem("Todos os anos")
        widgets_filtro.append(self.combo_filtro_ano)

        ano_layout, peso_ano = self.criar_layout_coluna_uniforme(
            "Ano:", self.combo_filtro_ano, 2
        )
        filtro_completo_layout.addLayout(ano_layout, peso_ano)
        self.combo_filtro_ano.currentTextChanged.connect(self.on_ano_changed)

        self.combo_filtro_periodo = QComboBox()
        self.combo_filtro_periodo.addItem("Todos os períodos")
        widgets_filtro.append(self.combo_filtro_periodo)

        periodo_layout, peso_periodo = self.criar_layout_coluna_uniforme(
            "Período:", self.combo_filtro_periodo, 3
        )
        filtro_completo_layout.addLayout(periodo_layout, peso_periodo)

        self.combo_filtro_periodo.currentTextChanged.connect(
            self.aplicar_filtro)

        self.configurar_widgets_uniformes(widgets_filtro)

        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(3)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        label_vazio = QLabel("")
        label_vazio.setMinimumHeight(16)
        label_vazio.setMaximumHeight(18)
        btn_layout.addWidget(label_vazio)

        self.btn_limpar_filtros = QPushButton("Limpar Filtros")
        self.btn_limpar_filtros.setToolTip(
            "Limpar filtros de cliente e processo, mantendo o mês corrente"
        )
        self.btn_limpar_filtros.clicked.connect(self.limpar_filtros)

        aplicar_estilo_botao(self.btn_limpar_filtros, "laranja", 110)

        btn_layout.addWidget(self.btn_limpar_filtros)
        filtro_completo_layout.addLayout(btn_layout, 1)

        filtro_completo_layout.addStretch()

        filtros_frame.setLayout(filtro_completo_layout)
        self.tabela_layout.addWidget(filtros_frame)

        self.tabela = QTableWidget()
        colunas = [
            "Cliente",
            "Processo",
            "Qtd Itens",
            "Data Entrada",
            "Data Processo",
            "Valor (R$)",
        ]

        if self.is_admin:
            colunas.insert(0, "Usuário")

        self.tabela.setColumnCount(len(colunas))
        self.tabela.setHorizontalHeaderLabels(colunas)

        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setSelectionMode(QAbstractItemView.SingleSelection)

        header = self.tabela.horizontalHeader()

        if self.is_admin:
            porcentagens_colunas = [10, 25, 20, 8, 13, 13, 11]
        else:
            porcentagens_colunas = [30, 22, 10, 13, 13, 12]

        def calcular_larguras_colunas():
            largura_disponivel = self.tabela.viewport().width()
            if largura_disponivel <= 0:
                largura_disponivel = 800
            larguras_calculadas = []
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

        def aplicar_larguras():
            larguras = calcular_larguras_colunas()
            for i, largura in enumerate(larguras):
                if i < self.tabela.columnCount():
                    header.setSectionResizeMode(i, QHeaderView.Fixed)
                    self.tabela.setColumnWidth(i, largura)

        aplicar_larguras()

        self.aplicar_larguras_colunas = aplicar_larguras
        offset = 1 if self.is_admin else 0

        processo_col_index = 1 + offset
        processo_header_item = QTableWidgetItem("Processo")
        processo_header_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.tabela.setHorizontalHeaderItem(
            processo_col_index, processo_header_item)

        qtd_col_index = 2 + offset
        qtd_header_item = QTableWidgetItem("Qtd Itens")
        qtd_header_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.tabela.setHorizontalHeaderItem(qtd_col_index, qtd_header_item)

        data_entrada_col_index = 3 + offset
        data_entrada_header_item = QTableWidgetItem("Data Entrada")
        data_entrada_header_item.setTextAlignment(
            Qt.AlignCenter | Qt.AlignVCenter)
        self.tabela.setHorizontalHeaderItem(
            data_entrada_col_index, data_entrada_header_item
        )

        data_processo_col_index = 4 + offset
        data_processo_header_item = QTableWidgetItem("Data Processo")
        data_processo_header_item.setTextAlignment(
            Qt.AlignCenter | Qt.AlignVCenter)
        self.tabela.setHorizontalHeaderItem(
            data_processo_col_index, data_processo_header_item
        )

        valor_col_index = len(colunas) - 1
        valor_header_item = QTableWidgetItem("Valor (R$)")
        valor_header_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.tabela.setHorizontalHeaderItem(valor_col_index, valor_header_item)

        date_delegate = DateEditDelegate(self.tabela)
        if self.is_admin:
            self.tabela.setItemDelegateForColumn(4, date_delegate)
            self.tabela.setItemDelegateForColumn(5, date_delegate)
        else:
            self.tabela.setItemDelegateForColumn(3, date_delegate)
            self.tabela.setItemDelegateForColumn(4, date_delegate)

        self.tabela.setToolTip(
            "Clique duas vezes em uma célula para editar diretamente na tabela"
        )
        self.tabela.itemChanged.connect(self.on_item_changed)
        self.tabela.resizeEvent = self.on_tabela_resize

        self.tabela_layout.addWidget(self.tabela)

        botao_layout = QHBoxLayout()
        self.btn_excluir = QPushButton("Excluir")
        self.btn_excluir.setToolTip(
            "Excluir processo selecionado na tabela (Atalho: Delete)"
        )
        self.btn_excluir.clicked.connect(self.excluir_processo)
        aplicar_estilo_botao(self.btn_excluir, "vermelho")
        estilo_atual = self.btn_excluir.styleSheet()
        estilo_completo = estilo_atual + aplicar_estilo_botao_desabilitado()
        self.btn_excluir.setStyleSheet(estilo_completo)
        botao_layout.addStretch()
        botao_layout.addWidget(self.btn_excluir)
        self.tabela_layout.addLayout(botao_layout)

    def criar_frame_totais(self):
        """Cria o frame que exibe os totais (processos, itens, valores)."""
        self.frame_totais = QFrame()
        self.frame_totais.setFrameStyle(QFrame.StyledPanel)

        layout = QHBoxLayout()
        layout.setSpacing(ESPACAMENTO_PADRAO)

        self.label_total_processos = QLabel("Total Processos: 0")
        self.label_total_itens = QLabel("Total Itens: 0")
        self.label_total_valor = QLabel("Total Valor: R$ 0,00")

        font = QFont()
        font.setBold(True)
        self.label_total_processos.setFont(font)
        self.label_total_itens.setFont(font)
        self.label_total_valor.setFont(font)

        layout.addWidget(self.label_total_processos)
        layout.addWidget(self.label_total_itens)
        layout.addWidget(self.label_total_valor)
        layout.addStretch()

        self.frame_totais.setLayout(layout)

    def on_tabela_resize(self, event):
        """Recalcula larguras das colunas ao redimensionar."""
        QTableWidget.resizeEvent(self.tabela, event)
        if hasattr(self, "aplicar_larguras_colunas"):
            QTimer.singleShot(50, self.aplicar_larguras_colunas)

    def limpar_filtros(self):
        """Limpa filtros mantendo o período corrente selecionado."""
        if self.is_admin and hasattr(self, "combo_usuario"):
            self.combo_usuario.blockSignals(True)
            self.combo_usuario.setCurrentText("Todos os usuários")
            self.combo_usuario.blockSignals(False)

        if hasattr(self, "entry_filtro_cliente"):
            self.entry_filtro_cliente.blockSignals(True)
            self.entry_filtro_cliente.clear()
            self.entry_filtro_cliente.blockSignals(False)

        if hasattr(self, "entry_filtro_processo"):
            self.entry_filtro_processo.blockSignals(True)
            self.entry_filtro_processo.clear()
            self.entry_filtro_processo.blockSignals(False)

        self.aplicar_filtro_periodo_corrente()
        self.aplicar_filtro()

    def aplicar_filtro_periodo_corrente(self):
        """Seleciona automaticamente o período corrente."""
        try:
            data_inicio_atual, data_fim_atual = (
                calcular_periodo_faturamento_atual_datas()
            )
            ano_atual = str(data_inicio_atual.year)

            if hasattr(self, "combo_filtro_ano"):
                self.combo_filtro_ano.blockSignals(True)
                ano_index = self.combo_filtro_ano.findText(ano_atual)
                if ano_index >= 0:
                    self.combo_filtro_ano.setCurrentIndex(ano_index)
                    self.configurar_periodos_do_ano()
                self.combo_filtro_ano.blockSignals(False)

            if hasattr(self, "combo_filtro_periodo"):
                self.combo_filtro_periodo.blockSignals(True)
                periodo_atual_display = (
                    f"{data_inicio_atual.strftime('%d/%m')} a "
                    f"{data_fim_atual.strftime('%d/%m')}"
                )
                periodo_index = self.combo_filtro_periodo.findText(
                    periodo_atual_display
                )
                if periodo_index >= 0:
                    self.combo_filtro_periodo.setCurrentIndex(periodo_index)
                self.combo_filtro_periodo.blockSignals(False)
        except (RuntimeError, AttributeError, TypeError, ValueError) as e:
            print(f"Erro ao aplicar filtro do período corrente: {e}")

    def on_usuario_changed(self):
        """Reage à mudança de usuário no filtro (admins)."""
        self.configurar_filtros_ano_periodo()
        self.aplicar_filtro_periodo_corrente()
        self.aplicar_filtro()

    def carregar_dados(self):
        """Carrega usuários, configura filtros e aplica período corrente."""
        if self.is_admin and hasattr(self, "combo_usuario"):
            usuarios_list = db.buscar_usuarios_unicos()
            for user in usuarios_list:
                self.combo_usuario.addItem(user)

        self.configurar_filtros_ano_periodo()
        self.aplicar_filtro_periodo_corrente()
        self.aplicar_filtro()
        QTimer.singleShot(100, self.rolar_para_ultimo_item)

    def on_item_changed(self, item):
        """Aplica validações e persiste alterações ao editar a tabela."""
        if not item:
            return

        try:
            self.tabela.blockSignals(True)
            row = item.row()
            col = item.column()
            col_offset = 1 if self.is_admin else 0

            if self.is_admin and col == 0:
                self.aplicar_filtro(rolar_para_ultimo=False)
                return

            item_com_id = self.tabela.item(row, 1 if self.is_admin else 0)
            if not item_com_id:
                return

            registro_id = item_com_id.data(Qt.UserRole)
            if not registro_id:
                return

            col_editada = col - col_offset
            valor_editado = item.text().strip()

            ok, erro_msg = self._validar_edicao_celula(
                col_editada, valor_editado)
            if not ok:
                if erro_msg:
                    QMessageBox.warning(self, "Erro", erro_msg)
                self.aplicar_filtro(rolar_para_ultimo=False)
                return

            (
                cliente,
                processo,
                qtde_itens,
                data_entrada,
                data_processo,
                valor_pedido,
            ) = self._extrair_campos_linha(row, col_offset)

            resultado = db.atualizar_lancamento(
                registro_id,
                cliente=cliente,
                processo=processo,
                qtde_itens=qtde_itens,
                data_entrada=data_entrada,
                data_processo=data_processo,
                valor_pedido=valor_pedido,
            )

            if "Sucesso" in resultado:
                if col_editada == 3:
                    self.configurar_filtros_ano_periodo()
                self.aplicar_filtro(rolar_para_ultimo=False)
            else:
                self.aplicar_filtro(rolar_para_ultimo=False)
                QMessageBox.warning(self, "Erro", resultado)

        except (ValueError, AttributeError, TypeError) as e:
            self.aplicar_filtro(rolar_para_ultimo=False)
            QMessageBox.warning(
                self, "Erro", f"Erro ao atualizar registro: {str(e)}")
        finally:
            self.tabela.blockSignals(False)

    def _validar_edicao_celula(self, col_editada, valor_editado):
        """Valida conteúdo de célula editada. Retorna (ok, erro_msg)."""
        if col_editada == 2:
            try:
                qtde_test = int(valor_editado)
                if qtde_test <= 0:
                    raise ValueError
            except ValueError:
                return False, "Quantidade de itens deve ser um número inteiro positivo."
            return True, None
        if col_editada in (3, 4):
            if valor_editado and valor_editado != "Não processado":
                try:
                    data_obj = datetime.strptime(valor_editado, "%d/%m/%Y")
                    if data_obj.date() > datetime.now().date():
                        if col_editada == 3:
                            return False, (
                                "Data de entrada não pode ser maior que a data atual."
                            )
                        return False, (
                            "Data de processo não pode ser maior que a data atual."
                        )
                except ValueError:
                    if col_editada == 3:
                        return (
                            False,
                            "Data de entrada deve estar no formato DD/MM/AAAA.",
                        )
                    return False, "Data de processo deve estar no formato DD/MM/AAAA."
            return True, None
        if col_editada == 5:
            try:
                valor_limpo = (
                    valor_editado.replace("R$", "")
                    .replace(" ", "")
                    .replace(".", "")
                    .replace(",", ".")
                )
                valor_test = float(valor_limpo)
                if valor_test < 0:
                    raise ValueError
            except ValueError:
                return False, "Valor deve ser um número válido e não negativo."
            return True, None
        return True, None

    def _extrair_campos_linha(self, row, col_offset):
        """Extrai campos da linha e converte para formatos de banco."""
        cliente = self.tabela.item(row, col_offset).text().strip().upper()
        processo = self.tabela.item(row, col_offset + 1).text().strip()
        qtde_itens = self.tabela.item(row, col_offset + 2).text().strip()
        data_entrada_text = self.tabela.item(
            row, col_offset + 3).text().strip()
        data_processo_text = self.tabela.item(
            row, col_offset + 4).text().strip()
        valor_text = self.tabela.item(row, col_offset + 5).text().strip()

        data_entrada = converter_data_para_banco(data_entrada_text)
        if data_processo_text == "Não processado" or not data_processo_text:
            data_processo = ""
        else:
            data_processo = converter_data_para_banco(data_processo_text)

        valor_limpo = valor_text.replace(
            "R$", "").replace(" ", "").replace(".", "")
        valor_pedido = (
            valor_limpo.replace(
                ",", ".") if "," in valor_limpo else valor_limpo
        )

        return cliente, processo, qtde_itens, data_entrada, data_processo, valor_pedido

    def _calcular_usuario_filtro(self):
        """Determina o filtro de usuário considerando admin/usuário."""
        if self.is_admin:
            if (
                hasattr(self, "combo_usuario")
                and self.combo_usuario.currentText() != "Todos os usuários"
            ):
                return self.combo_usuario.currentText()
            return None
        return self.usuario_logado

    def _obter_filtros_texto(self):
        """Obtém filtros de cliente e processo a partir dos campos de texto."""
        cliente_filtro = None
        if (
            hasattr(self, "entry_filtro_cliente")
            and self.entry_filtro_cliente.text().strip()
        ):
            cliente_filtro = self.entry_filtro_cliente.text().strip().upper()

        processo_filtro = None
        if (
            hasattr(self, "entry_filtro_processo")
            and self.entry_filtro_processo.text().strip()
        ):
            processo_filtro = self.entry_filtro_processo.text().strip()

        return cliente_filtro, processo_filtro

    def _obter_periodo_selecionado(self):
        """Retorna (data_inicio, data_fim) do período selecionado, se houver."""
        data_inicio = None
        data_fim = None
        if (
            hasattr(self, "combo_filtro_periodo")
            and self.combo_filtro_periodo.currentText() != "Todos os períodos"
        ):
            index_selecionado = self.combo_filtro_periodo.currentIndex()
            if index_selecionado > 0:
                dados_periodo = self.combo_filtro_periodo.itemData(
                    index_selecionado)
                if dados_periodo:
                    data_inicio = dados_periodo["inicio"]
                    data_fim = dados_periodo["fim"]
        return data_inicio, data_fim

    def _ordenacao_chave(self, registro):
        """Chave de ordenação por (data_processo, data_lancamento)."""
        data_processo = registro[6]
        data_lancamento = registro[8]
        try:
            if data_lancamento:
                if "T" in str(data_lancamento):
                    timestamp_obj = datetime.fromisoformat(
                        str(data_lancamento).replace("Z", "")
                    )
                else:
                    timestamp_obj = datetime.strptime(
                        str(data_lancamento), "%Y-%m-%d %H:%M:%S"
                    )
            else:
                timestamp_obj = datetime.min
        except (ValueError, AttributeError) as e:
            print(f"Erro ao converter timestamp '{data_lancamento}': {e}")
            timestamp_obj = datetime.min

        if not data_processo:
            return (datetime.min, timestamp_obj)
        try:
            data_processo_obj = datetime.strptime(data_processo, "%Y-%m-%d")
            return (data_processo_obj, timestamp_obj)
        except ValueError:
            return (datetime.min, timestamp_obj)

    def aplicar_filtro(self, rolar_para_ultimo=True):
        """Aplica filtros e preenche a tabela."""
        usuario_filtro = self._calcular_usuario_filtro()
        cliente_filtro, processo_filtro = self._obter_filtros_texto()
        data_inicio, data_fim = self._obter_periodo_selecionado()

        registros = db.buscar_lancamentos_filtros_completos(
            usuario=usuario_filtro,
            cliente=cliente_filtro,
            processo=processo_filtro,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )
        registros_ordenados = sorted(
            registros, key=self._ordenacao_chave, reverse=False
        )

        self.tabela.blockSignals(True)
        self.tabela.setRowCount(len(registros_ordenados))

        for row, registro in enumerate(registros_ordenados):
            col = 0

            if self.is_admin:
                item_usuario = QTableWidgetItem(str(registro[1]))
                item_usuario.setFlags(
                    item_usuario.flags() & ~Qt.ItemIsEditable)
                self.tabela.setItem(row, col, item_usuario)
                col += 1

            item_cliente = QTableWidgetItem(str(registro[2]).upper())
            self.tabela.setItem(row, col, item_cliente)

            item_processo = QTableWidgetItem(str(registro[3]))
            item_processo.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            self.tabela.setItem(row, col + 1, item_processo)

            item_qtde = QTableWidgetItem(str(registro[4]))
            item_qtde.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            self.tabela.setItem(row, col + 2, item_qtde)

            data_entrada_formatada = formatar_data_para_exibicao(registro[5])
            item_data_entrada = QTableWidgetItem(data_entrada_formatada)
            item_data_entrada.setTextAlignment(
                Qt.AlignCenter | Qt.AlignVCenter)
            self.tabela.setItem(row, col + 3, item_data_entrada)

            data_processo_formatada = (
                formatar_data_para_exibicao(registro[6])
                if registro[6]
                else "Não processado"
            )
            item_data_processo = QTableWidgetItem(data_processo_formatada)
            item_data_processo.setTextAlignment(
                Qt.AlignCenter | Qt.AlignVCenter)
            self.tabela.setItem(row, col + 4, item_data_processo)

            item_valor = QTableWidgetItem(
                formatar_valor_monetario(registro[7]))
            item_valor.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela.setItem(row, col + 5, item_valor)

            if not self.is_admin:
                self.tabela.item(row, 0).setData(Qt.UserRole, registro[0])
            else:
                self.tabela.item(row, 1).setData(Qt.UserRole, registro[0])

        self.tabela.blockSignals(False)

        filtros = {"usuario": usuario_filtro}
        cliente_processo = self._obter_filtros_texto()
        filtros["cliente"] = cliente_processo[0]
        filtros["processo"] = cliente_processo[1]
        periodo = self._obter_periodo_selecionado()
        filtros["data_inicio"], filtros["data_fim"] = periodo

        self.atualizar_totais(filtros)

        if rolar_para_ultimo:
            self.rolar_para_ultimo_item()

    def rolar_para_ultimo_item(self):
        """Rola a tabela até o último item."""
        if self.tabela.rowCount() > 0:
            ultima_linha = self.tabela.rowCount() - 1
            self.tabela.scrollToBottom()
            self.tabela.selectRow(ultima_linha)

    def atualizar_totais(self, filtros: dict | None = None):
        """Atualiza os totalizadores do painel."""
        filtros = filtros or {}
        estatisticas = db.buscar_estatisticas_completas(
            usuario=filtros.get("usuario"),
            cliente=filtros.get("cliente"),
            processo=filtros.get("processo"),
            data_inicio=filtros.get("data_inicio"),
            data_fim=filtros.get("data_fim"),
        )

        self.label_total_processos.setText(
            f"Total Processos: {estatisticas['total_processos']}"
        )
        self.label_total_itens.setText(
            f"Total Itens: {estatisticas['total_itens']}")
        self.label_total_valor.setText(
            f"Total Valor: {formatar_valor_monetario(estatisticas['total_valor'])}"
        )

    def adicionar_processo(self):
        """Valida campos e insere novo processo no banco."""
        cliente = self.entry_cliente.text().strip().upper()
        processo = self.entry_processo.text().strip()
        qtde_itens = self.entry_qtde_itens.text().strip()

        data_entrada_qdate = self.entry_data_entrada.date()
        if data_entrada_qdate > QDate.currentDate():
            QMessageBox.warning(
                self, "Erro", "Data de entrada não pode ser maior que a data atual."
            )
            return
        data_entrada = data_entrada_qdate.toString("yyyy-MM-dd")

        data_processo_qdate = self.entry_data_processo.date()
        if not data_processo_qdate.isNull():
            if data_processo_qdate > QDate.currentDate():
                QMessageBox.warning(
                    self,
                    "Erro",
                    "Data de processo não pode ser maior que a data atual.",
                )
                return
            data_processo = data_processo_qdate.toString("yyyy-MM-dd")
        else:
            data_processo = ""

        valor_pedido = self.entry_valor_pedido.text().strip()

        resultado = db.adicionar_lancamento(
            usuario=self.usuario_logado,
            cliente=cliente,
            processo=processo,
            qtde_itens=qtde_itens,
            data_entrada=data_entrada,
            data_processo=data_processo,
            valor_pedido=valor_pedido,
        )

        if "Sucesso" in resultado:
            QMessageBox.information(self, "Sucesso", resultado)
            self.entry_cliente.clear()
            self.entry_processo.clear()
            self.entry_qtde_itens.clear()
            self.entry_data_entrada.setDate(QDate.currentDate())
            self.entry_data_processo.clear()
            self.entry_valor_pedido.clear()

            self.atualizar_autocompletar_cliente()
            self.atualizar_autocompletar_filtro_cliente()
            self.configurar_filtros_ano_periodo()
            self.aplicar_filtro()
            self.rolar_para_ultimo_item()
            self.entry_cliente.setFocus()
        else:
            QMessageBox.warning(self, "Erro", resultado)

    def excluir_processo(self):
        """Exclui o processo selecionado na tabela."""
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.information(
                self,
                "Seleção",
                (
                    "Selecione um processo na tabela para excluir.\n\n"
                    "Dica: Clique em uma linha e pressione Delete ou "
                    "use o botão 'Excluir Selecionado'."
                ),
            )
            return

        if not self.is_admin:
            cliente = self.tabela.item(row, 0).text()
            processo = self.tabela.item(row, 1).text()
        else:
            cliente = self.tabela.item(row, 1).text()
            processo = self.tabela.item(row, 2).text()

        resposta = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            (
                "Tem certeza que deseja excluir este processo?\n\n"
                f"Cliente: {cliente}\nProcesso: {processo}"
            ),
            QMessageBox.Yes | QMessageBox.No,
        )

        if resposta == QMessageBox.Yes:
            if not self.is_admin:
                item_com_id = self.tabela.item(row, 0)
            else:
                item_com_id = self.tabela.item(row, 1)

            if item_com_id:
                registro_id = item_com_id.data(Qt.UserRole)
                resultado = db.excluir_lancamento(registro_id)
                if "Sucesso" in resultado:
                    QMessageBox.information(self, "Sucesso", resultado)
                    self.configurar_filtros_ano_periodo()
                    self.aplicar_filtro(rolar_para_ultimo=False)
                else:
                    QMessageBox.warning(self, "Erro", resultado)
