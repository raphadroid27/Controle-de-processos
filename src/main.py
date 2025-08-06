"""
Sistema de Controle de Processos para Desenhistas

Este módulo implementa uma interface gráfica completa para gerenciamento
de processos realizados por desenhistas, incluindo sistema de autenticação,
controle de usuários e gestão de dados com banco SQLite.
"""

import sys
from datetime import datetime

from PySide6.QtCore import QDate, Qt, Signal, QTimer
from PySide6.QtGui import QAction, QFont, QKeySequence, QShortcut, QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QCompleter,
    QDateEdit,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QInputDialog,
    QStyledItemDelegate,
    QAbstractItemView,
)

from utils import database as db
from utils import usuario
from utils.ui_config import (
    aplicar_estilo_botao,
    aplicar_estilo_botao_desabilitado,
    configurar_widgets_entrada_uniformes,
    ESPACAMENTO_PADRAO,
    ALTURA_WIDGET_ENTRADA,
    ALTURA_MINIMA_WIDGET_ENTRADA
)
from login_dialog import LoginDialog
from gerenciar_usuarios import GerenciarUsuariosDialog


def formatar_valor_monetario(valor):
    """Formata valor monetário com separador de milhares e vírgula decimal."""
    try:
        if isinstance(valor, str):
            # Limpar valor se for string
            valor_limpo = valor.replace("R$", "").replace(
                " ", "").replace(".", "").replace(",", ".")
            valor = float(valor_limpo)

        # Formatar com separador de milhares (ponto) e decimais (vírgula)
        valor_formatado = f"{valor:,.2f}".replace(
            ",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {valor_formatado}"
    except (ValueError, TypeError):
        return "R$ 0,00"


class DateEditDelegate(QStyledItemDelegate):
    """Delegate personalizado para edição de datas com calendário."""

    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        """Cria o editor de data com calendário."""
        editor = QDateEdit(parent)
        editor.setCalendarPopup(True)
        editor.setDisplayFormat("dd/MM/yyyy")

        # Definir data máxima como hoje
        editor.setMaximumDate(QDate.currentDate())

        # Verificar se é uma coluna de data processo (pode estar vazia)
        data_texto = index.data()
        if data_texto == "Não processado" or not data_texto:
            editor.setSpecialValueText("Não processado")
            editor.setDate(QDate())  # Data nula
        else:
            # Tentar converter a data do formato DD/MM/AAAA
            try:
                if "/" in data_texto:
                    data_obj = datetime.strptime(data_texto, "%d/%m/%Y")
                else:
                    # Formato AAAA-MM-DD do banco
                    data_obj = datetime.strptime(data_texto, "%Y-%m-%d")
                editor.setDate(
                    QDate(data_obj.year, data_obj.month, data_obj.day))
            except (ValueError, AttributeError):
                editor.setDate(QDate.currentDate())

        return editor

    def setEditorData(self, editor, index):
        """Define os dados no editor."""
        value = index.data()
        if value == "Não processado" or not value:
            editor.setDate(QDate())  # Data nula
        else:
            try:
                if "/" in value:
                    data_obj = datetime.strptime(value, "%d/%m/%Y")
                else:
                    data_obj = datetime.strptime(value, "%Y-%m-%d")
                editor.setDate(
                    QDate(data_obj.year, data_obj.month, data_obj.day))
            except (ValueError, AttributeError):
                editor.setDate(QDate.currentDate())

    def setModelData(self, editor, model, index):
        """Define os dados do editor no modelo."""
        date = editor.date()
        if date.isNull() or not date.isValid():
            model.setData(index, "Não processado")
        else:
            # Formatar como DD/MM/AAAA para exibição
            formatted_date = date.toString("dd/MM/yyyy")
            model.setData(index, formatted_date)

    def updateEditorGeometry(self, editor, option, index):
        """Atualiza a geometria do editor."""
        editor.setGeometry(option.rect)


class NavigableLineEdit(QLineEdit):
    """QLineEdit personalizado que permite navegação entre campos com setas."""

    def __init__(self, campos_navegacao=None, parent=None):
        super().__init__(parent)
        self.campos_navegacao = campos_navegacao or []

    def set_campos_navegacao(self, campos):
        """Define a lista de campos para navegação."""
        self.campos_navegacao = campos

    def keyPressEvent(self, event):
        """Intercepta eventos de teclado para navegação."""
        if event.key() == Qt.Key_Left:
            # Navegar para campo anterior se cursor estiver no início
            if self.cursorPosition() == 0 and self.campos_navegacao:
                try:
                    indice_atual = self.campos_navegacao.index(self)
                    indice_anterior = (
                        indice_atual - 1) % len(self.campos_navegacao)
                    self.campos_navegacao[indice_anterior].setFocus()
                    # Posicionar cursor no final do campo anterior
                    if isinstance(self.campos_navegacao[indice_anterior], QLineEdit):
                        self.campos_navegacao[indice_anterior].setCursorPosition(
                            len(self.campos_navegacao[indice_anterior].text())
                        )
                    return
                except ValueError:
                    pass

        elif event.key() == Qt.Key_Right:
            # Navegar para próximo campo se cursor estiver no final
            if self.cursorPosition() == len(self.text()) and self.campos_navegacao:
                try:
                    indice_atual = self.campos_navegacao.index(self)
                    proximo_indice = (
                        indice_atual + 1) % len(self.campos_navegacao)
                    self.campos_navegacao[proximo_indice].setFocus()
                    # Posicionar cursor no início do próximo campo
                    if isinstance(self.campos_navegacao[proximo_indice], QLineEdit):
                        self.campos_navegacao[proximo_indice].setCursorPosition(
                            0)
                    return
                except ValueError:
                    pass

        # Passar o evento para o comportamento padrão
        super().keyPressEvent(event)


class NavigableDateEdit(QDateEdit):
    """QDateEdit personalizado que permite navegação entre campos com setas."""

    def __init__(self, campos_navegacao=None, parent=None):
        super().__init__(parent)
        self.campos_navegacao = campos_navegacao or []

    def set_campos_navegacao(self, campos):
        """Define a lista de campos para navegação."""
        self.campos_navegacao = campos

    def keyPressEvent(self, event):
        """Intercepta eventos de teclado para navegação."""
        if event.key() == Qt.Key_Left and self.campos_navegacao:
            try:
                indice_atual = self.campos_navegacao.index(self)
                indice_anterior = (
                    indice_atual - 1) % len(self.campos_navegacao)
                self.campos_navegacao[indice_anterior].setFocus()
                # Posicionar cursor no final do campo anterior
                if isinstance(self.campos_navegacao[indice_anterior], QLineEdit):
                    self.campos_navegacao[indice_anterior].setCursorPosition(
                        len(self.campos_navegacao[indice_anterior].text())
                    )
                return
            except ValueError:
                pass

        elif event.key() == Qt.Key_Right and self.campos_navegacao:
            try:
                indice_atual = self.campos_navegacao.index(self)
                proximo_indice = (
                    indice_atual + 1) % len(self.campos_navegacao)
                self.campos_navegacao[proximo_indice].setFocus()
                # Posicionar cursor no início do próximo campo
                if isinstance(self.campos_navegacao[proximo_indice], QLineEdit):
                    self.campos_navegacao[proximo_indice].setCursorPosition(0)
                return
            except ValueError:
                pass

        # Passar o evento para o comportamento padrão
        super().keyPressEvent(event)


class ProcessosWidget(QWidget):
    """Widget principal para gerenciamento de processos."""

    def __init__(self, usuario_logado, is_admin):
        super().__init__()
        self.usuario_logado = usuario_logado
        self.is_admin = is_admin

        # Inicializar atributos antes de criar a UI
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

        self.init_ui()
        self.carregar_dados()

    def init_ui(self):
        """Inicializa a interface do usuário."""
        main_layout = QVBoxLayout()

        # Frame de entrada de dados
        self.criar_frame_entrada()
        main_layout.addWidget(self.frame_entrada)

        # Tabela
        self.criar_tabela()
        main_layout.addLayout(self.tabela_layout)

        # Frame de totais
        self.criar_frame_totais()
        main_layout.addWidget(self.frame_totais)

        self.setLayout(main_layout)

        # Configurar atalhos de teclado
        self.configurar_atalhos()

    def configurar_atalhos(self):
        """Configura os atalhos de teclado para a aplicação."""
        # Atalho Enter para adicionar processo (com validação)
        self.shortcut_enter = QShortcut(QKeySequence(Qt.Key_Return), self)
        self.shortcut_enter.activated.connect(self.atalho_adicionar_processo)

        # Atalho Enter (teclado numérico) para adicionar processo (com validação)
        self.shortcut_enter_num = QShortcut(QKeySequence(Qt.Key_Enter), self)
        self.shortcut_enter_num.activated.connect(
            self.atalho_adicionar_processo)

        # Atalho Delete para excluir processo
        self.shortcut_delete = QShortcut(QKeySequence(Qt.Key_Delete), self)
        self.shortcut_delete.activated.connect(self.excluir_processo)

    def configurar_autocompletar_cliente(self):
        """Configura o autocompletar para o campo cliente."""
        try:
            # Buscar clientes únicos do banco de dados
            clientes_raw = db.buscar_clientes_unicos()
            # Converter todos os clientes para maiúscula
            clientes = [cliente.upper() for cliente in clientes_raw]

            # Criar o completer
            self.completer_cliente = QCompleter(clientes, self)
            self.completer_cliente.setCaseSensitivity(Qt.CaseInsensitive)
            self.completer_cliente.setFilterMode(Qt.MatchStartsWith)

            # Aplicar o completer ao campo cliente
            self.entry_cliente.setCompleter(self.completer_cliente)
        except Exception as e:
            print(f"Erro ao configurar autocompletar: {e}")

    def atualizar_autocompletar_cliente(self):
        """Atualiza a lista de sugestões do autocompletar com clientes mais recentes."""
        try:
            # Buscar clientes únicos atualizados
            clientes_raw = db.buscar_clientes_unicos()
            # Converter todos os clientes para maiúscula
            clientes = [cliente.upper() for cliente in clientes_raw]

            # Atualizar o modelo do completer
            if hasattr(self, 'completer_cliente'):
                self.completer_cliente.setModel(None)
                self.completer_cliente = QCompleter(clientes, self)
                self.completer_cliente.setCaseSensitivity(Qt.CaseInsensitive)
                self.completer_cliente.setFilterMode(Qt.MatchStartsWith)
                self.entry_cliente.setCompleter(self.completer_cliente)
        except Exception as e:
            print(f"Erro ao atualizar autocompletar: {e}")

    def configurar_autocompletar_filtro_cliente(self):
        """Configura o autocompletar para o campo de filtro de cliente."""
        try:
            # Buscar clientes únicos do banco de dados
            clientes_raw = db.buscar_clientes_unicos()
            # Converter todos os clientes para maiúscula
            clientes = [cliente.upper() for cliente in clientes_raw]

            # Criar o completer para o filtro
            self.completer_filtro_cliente = QCompleter(clientes, self)
            self.completer_filtro_cliente.setCaseSensitivity(
                Qt.CaseInsensitive)
            self.completer_filtro_cliente.setFilterMode(Qt.MatchStartsWith)

            # Aplicar o completer ao campo de filtro de cliente
            self.entry_filtro_cliente.setCompleter(
                self.completer_filtro_cliente)
        except Exception as e:
            print(f"Erro ao configurar autocompletar do filtro: {e}")

    def atualizar_autocompletar_filtro_cliente(self):
        """Atualiza a lista de sugestões do autocompletar do filtro com clientes mais recentes."""
        try:
            # Buscar clientes únicos atualizados
            clientes_raw = db.buscar_clientes_unicos()
            # Converter todos os clientes para maiúscula
            clientes = [cliente.upper() for cliente in clientes_raw]

            # Atualizar o modelo do completer do filtro
            if hasattr(self, 'completer_filtro_cliente'):
                self.completer_filtro_cliente.setModel(None)
                self.completer_filtro_cliente = QCompleter(clientes, self)
                self.completer_filtro_cliente.setCaseSensitivity(
                    Qt.CaseInsensitive)
                self.completer_filtro_cliente.setFilterMode(Qt.MatchStartsWith)
                self.entry_filtro_cliente.setCompleter(
                    self.completer_filtro_cliente)
        except Exception as e:
            print(f"Erro ao atualizar autocompletar do filtro: {e}")

    def configurar_filtros_mes_ano(self):
        """Configura os combos de mês e ano com dados únicos do banco."""
        try:
            # Determinar qual usuário filtrar para meses e anos
            if self.is_admin:
                if hasattr(self, 'combo_usuario') and self.combo_usuario.currentText() != "Todos os usuários":
                    usuario_filtro = self.combo_usuario.currentText()
                else:
                    usuario_filtro = None
            else:
                # Usuários normais só veem seus próprios dados
                usuario_filtro = self.usuario_logado

            # Bloquear sinais temporariamente
            self.combo_filtro_mes.blockSignals(True)
            self.combo_filtro_ano.blockSignals(True)

            # Salvar seleções atuais
            mes_selecionado = self.combo_filtro_mes.currentText()
            ano_selecionado = self.combo_filtro_ano.currentText()

            # Limpar e adicionar opção "Todos"
            self.combo_filtro_mes.clear()
            self.combo_filtro_mes.addItem("Todos os meses")

            self.combo_filtro_ano.clear()
            self.combo_filtro_ano.addItem("Todos os anos")

            # Buscar meses únicos do banco
            meses_db = db.buscar_meses_unicos(usuario_filtro)
            nomes_meses = {
                "01": "Janeiro", "02": "Fevereiro", "03": "Março",
                "04": "Abril", "05": "Maio", "06": "Junho",
                "07": "Julho", "08": "Agosto", "09": "Setembro",
                "10": "Outubro", "11": "Novembro", "12": "Dezembro"
            }

            for mes in meses_db:
                if mes in nomes_meses:
                    self.combo_filtro_mes.addItem(
                        f"{mes} - {nomes_meses[mes]}")

            # Buscar anos únicos do banco
            anos_db = db.buscar_anos_unicos(usuario_filtro)
            for ano in anos_db:
                self.combo_filtro_ano.addItem(ano)

            # Restaurar seleções se ainda existirem
            mes_index = self.combo_filtro_mes.findText(mes_selecionado)
            if mes_index >= 0:
                self.combo_filtro_mes.setCurrentIndex(mes_index)

            ano_index = self.combo_filtro_ano.findText(ano_selecionado)
            if ano_index >= 0:
                self.combo_filtro_ano.setCurrentIndex(ano_index)

            # Reativar sinais
            self.combo_filtro_mes.blockSignals(False)
            self.combo_filtro_ano.blockSignals(False)

        except Exception as e:
            print(f"Erro ao configurar filtros de mês/ano: {e}")
            # Reativar sinais em caso de erro
            self.combo_filtro_mes.blockSignals(False)
            self.combo_filtro_ano.blockSignals(False)

    def converter_cliente_maiuscula(self, texto):
        """Converte automaticamente o texto do campo cliente para maiúscula."""
        # Bloquear temporariamente o sinal para evitar recursão
        self.entry_cliente.blockSignals(True)

        # Obter posição atual do cursor
        posicao_cursor = self.entry_cliente.cursorPosition()

        # Converter para maiúscula
        texto_maiusculo = texto.upper()

        # Definir o texto em maiúscula
        self.entry_cliente.setText(texto_maiusculo)

        # Restaurar posição do cursor
        self.entry_cliente.setCursorPosition(posicao_cursor)

        # Reativar sinais
        self.entry_cliente.blockSignals(False)

    def atalho_adicionar_processo(self):
        """Adiciona processo via atalho, mas apenas se campos obrigatórios estiverem preenchidos."""
        # Verificar se os campos obrigatórios estão preenchidos
        cliente = self.entry_cliente.text().strip()
        processo = self.entry_processo.text().strip()
        qtde_itens = self.entry_qtde_itens.text().strip()
        valor_pedido = self.entry_valor_pedido.text().strip()

        if cliente and processo and qtde_itens and valor_pedido:
            self.adicionar_processo()
        else:
            # Focar no primeiro campo vazio
            if not cliente:
                self.entry_cliente.setFocus()
            elif not processo:
                self.entry_processo.setFocus()
            elif not qtde_itens:
                self.entry_qtde_itens.setFocus()
            elif not valor_pedido:
                self.entry_valor_pedido.setFocus()

    def configurar_widgets_uniformes(self, widgets_list):
        """Configura widgets para ter tamanho e comportamento uniformes."""
        configurar_widgets_entrada_uniformes(widgets_list)

    def configurar_botao_uniforme(self, botao, largura_minima=None):
        """Configura um botão para ter tamanho e comportamento uniformes usando função global."""
        configurar_botao_padrao(botao, largura_minima)

    def criar_layout_coluna_uniforme(self, label_text, widget, peso=1, espacamento_label=3):
        """Cria um layout de coluna uniforme com label e widget."""
        col_layout = QVBoxLayout()
        col_layout.setSpacing(espacamento_label)
        col_layout.setContentsMargins(0, 0, 0, 0)

        # Label com formatação consistente
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

        # Campos de entrada com navegação
        self.entry_cliente = NavigableLineEdit()
        self.entry_processo = NavigableLineEdit()
        self.entry_qtde_itens = NavigableLineEdit()

        # Data de entrada com limite máximo de hoje
        self.entry_data_entrada = NavigableDateEdit()
        self.entry_data_entrada.setDate(QDate.currentDate())
        self.entry_data_entrada.setCalendarPopup(True)
        self.entry_data_entrada.setMaximumDate(QDate.currentDate())

        # Data de processo com limite máximo de hoje
        self.entry_data_processo = NavigableDateEdit()
        self.entry_data_processo.setCalendarPopup(True)
        self.entry_data_processo.setSpecialValueText("Não processado")
        self.entry_data_processo.setMaximumDate(QDate.currentDate())
        self.entry_data_processo.setDate(QDate.currentDate())  # Data nula

        self.entry_valor_pedido = NavigableLineEdit()
        self.entry_valor_pedido.setPlaceholderText("0.00")

        # Lista de widgets para configuração uniforme
        widgets_entrada = [
            self.entry_cliente,
            self.entry_processo,
            self.entry_qtde_itens,
            self.entry_data_entrada,
            self.entry_data_processo,
            self.entry_valor_pedido
        ]

        # Aplicar configuração uniforme a todos os widgets
        self.configurar_widgets_uniformes(widgets_entrada)

        # Configurar navegação entre campos
        for campo in widgets_entrada:
            campo.set_campos_navegacao(widgets_entrada)

        # Conectar sinal para converter automaticamente para maiúscula
        self.entry_cliente.textChanged.connect(
            self.converter_cliente_maiuscula)

        # Configurar autocompletar para cliente
        self.configurar_autocompletar_cliente()

        # Layout horizontal principal com espaçamento uniforme
        campos_layout = QHBoxLayout()
        campos_layout.setSpacing(10)  # Espaçamento consistente entre colunas
        campos_layout.setContentsMargins(8, 8, 8, 8)  # Margens uniformes

        # Criar colunas com layouts uniformes
        colunas_info = [
            # Peso maior para campos de texto
            ("Cliente:", self.entry_cliente, 3),
            # Peso maior para campos de texto
            ("Processo:", self.entry_processo, 3),
            ("Qtd. Itens:", self.entry_qtde_itens, 2),  # Peso menor para números
            ("Data Entrada:", self.entry_data_entrada, 2),  # Peso menor para datas
            # Peso menor para datas
            ("Data Processo:", self.entry_data_processo, 2),
            ("Valor (R$):", self.entry_valor_pedido, 2)  # Peso menor para valores
        ]

        for label_text, widget, peso in colunas_info:
            col_layout, peso_col = self.criar_layout_coluna_uniforme(
                label_text, widget, peso)
            campos_layout.addLayout(col_layout, peso_col)

        # Botão Adicionar com layout uniforme
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(3)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        # Label vazio para alinhar com outros campos
        label_vazio = QLabel("")
        label_vazio.setMinimumHeight(16)
        label_vazio.setMaximumHeight(18)
        btn_layout.addWidget(label_vazio)

        self.btn_adicionar = QPushButton("Adicionar")
        self.btn_adicionar.setToolTip(
            "Adicionar novo processo (Atalho: Enter)")

        # Aplicar estilo e configuração do botão usando função unificada
        aplicar_estilo_botao(self.btn_adicionar, "verde", 90)

        btn_layout.addWidget(self.btn_adicionar)
        campos_layout.addLayout(btn_layout, 1)  # Peso menor para o botão

        self.frame_entrada.setLayout(campos_layout)

        # Conectar eventos
        self.btn_adicionar.clicked.connect(self.adicionar_processo)

    def criar_tabela(self):
        """Cria a interface da tabela de processos com filtros."""
        self.tabela_layout = QVBoxLayout()

        # Área de filtros (para todos os usuários)
        filtros_frame = QFrame()
        filtros_frame.setFrameStyle(QFrame.StyledPanel)

        # Layout principal dos filtros com widgets distribuídos uniformemente (diretamente no frame)
        filtro_completo_layout = QHBoxLayout()
        # Mesmo espaçamento do frame de entrada
        filtro_completo_layout.setSpacing(10)
        filtro_completo_layout.setContentsMargins(
            8, 8, 8, 8)  # Mesmas margens do frame de entrada

        # Lista para armazenar widgets de filtro para configuração uniforme
        widgets_filtro = []

        # Filtro por usuário (apenas para admins)
        if self.is_admin:
            self.combo_usuario = QComboBox()
            self.combo_usuario.addItem("Todos os usuários")
            widgets_filtro.append(self.combo_usuario)

            usuario_layout, peso_usuario = self.criar_layout_coluna_uniforme(
                "Usuário:", self.combo_usuario, 2)
            filtro_completo_layout.addLayout(usuario_layout, peso_usuario)

            # Conectar mudança no combo para aplicar filtro automaticamente
            self.combo_usuario.currentTextChanged.connect(
                self.on_usuario_changed)

        # Filtro por cliente
        self.entry_filtro_cliente = QLineEdit()
        self.entry_filtro_cliente.setPlaceholderText(
            "Digite o nome do cliente")
        widgets_filtro.append(self.entry_filtro_cliente)

        cliente_layout, peso_cliente = self.criar_layout_coluna_uniforme(
            "Cliente:", self.entry_filtro_cliente, 3)
        filtro_completo_layout.addLayout(cliente_layout, peso_cliente)

        # Conectar mudança no campo de cliente (com delay para não filtrar a cada letra)
        self.timer_cliente = QTimer()
        self.timer_cliente.setSingleShot(True)
        self.timer_cliente.timeout.connect(self.aplicar_filtro)
        self.entry_filtro_cliente.textChanged.connect(
            lambda: self.timer_cliente.start(500))

        # Configurar autocompletar para o filtro de cliente
        self.configurar_autocompletar_filtro_cliente()

        # Filtro por processo
        self.entry_filtro_processo = QLineEdit()
        self.entry_filtro_processo.setPlaceholderText(
            "Digite o nome do processo")
        widgets_filtro.append(self.entry_filtro_processo)

        processo_layout, peso_processo = self.criar_layout_coluna_uniforme(
            "Processo:", self.entry_filtro_processo, 3)
        filtro_completo_layout.addLayout(processo_layout, peso_processo)

        # Conectar mudança no campo de processo (com delay para não filtrar a cada letra)
        self.timer_processo = QTimer()
        self.timer_processo.setSingleShot(True)
        self.timer_processo.timeout.connect(self.aplicar_filtro)
        self.entry_filtro_processo.textChanged.connect(
            lambda: self.timer_processo.start(500))

        # Filtro por mês
        self.combo_filtro_mes = QComboBox()
        self.combo_filtro_mes.addItem("Todos os meses")
        widgets_filtro.append(self.combo_filtro_mes)

        mes_layout, peso_mes = self.criar_layout_coluna_uniforme(
            "Mês:", self.combo_filtro_mes, 2)
        filtro_completo_layout.addLayout(mes_layout, peso_mes)

        # Conectar mudança no combo de mês
        self.combo_filtro_mes.currentTextChanged.connect(self.aplicar_filtro)

        # Filtro por ano
        self.combo_filtro_ano = QComboBox()
        self.combo_filtro_ano.addItem("Todos os anos")
        widgets_filtro.append(self.combo_filtro_ano)

        ano_layout, peso_ano = self.criar_layout_coluna_uniforme(
            "Ano:", self.combo_filtro_ano, 2)
        filtro_completo_layout.addLayout(ano_layout, peso_ano)

        # Conectar mudança no combo de ano
        self.combo_filtro_ano.currentTextChanged.connect(self.aplicar_filtro)

        # Aplicar configuração uniforme a todos os widgets de filtro
        self.configurar_widgets_uniformes(widgets_filtro)

        # Botão limpar filtros com layout uniforme
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(3)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        # Label vazio para alinhar com outros campos
        label_vazio = QLabel("")
        label_vazio.setMinimumHeight(16)
        label_vazio.setMaximumHeight(18)
        btn_layout.addWidget(label_vazio)

        self.btn_limpar_filtros = QPushButton("Limpar Filtros")
        self.btn_limpar_filtros.clicked.connect(self.limpar_filtros)

        # Aplicar estilo e configuração do botão usando função unificada
        aplicar_estilo_botao(self.btn_limpar_filtros, "laranja", 110)

        btn_layout.addWidget(self.btn_limpar_filtros)
        filtro_completo_layout.addLayout(
            btn_layout, 1)  # Peso menor para o botão

        # Adicionar stretch para empurrar elementos para a esquerda quando necessário
        filtro_completo_layout.addStretch()

        # Aplicar o layout diretamente ao frame (sem VBoxLayout intermediário)
        filtros_frame.setLayout(filtro_completo_layout)
        self.tabela_layout.addWidget(filtros_frame)

        # Tabela
        self.tabela = QTableWidget()
        colunas = [
            "Cliente",
            "Processo",
            "Qtd Itens",
            "Data Entrada",
            "Data Processo",
            "Valor (R$)",
        ]

        # Se for admin, mostra coluna usuário
        if self.is_admin:
            colunas.insert(0, "Usuário")

        self.tabela.setColumnCount(len(colunas))
        self.tabela.setHorizontalHeaderLabels(colunas)

        # Configurar seleção da tabela
        self.tabela.setSelectionBehavior(
            QAbstractItemView.SelectRows)  # Selecionar linha inteira
        # Apenas uma linha por vez
        self.tabela.setSelectionMode(QAbstractItemView.SingleSelection)

        # Configurar redimensionamento das colunas com larguras baseadas em porcentagens
        header = self.tabela.horizontalHeader()

        # Definir porcentagens para cada coluna (total deve somar 100%)
        if self.is_admin:
            # Para admin: Usuário, Cliente, Processo, Qtd Itens, Data Entrada, Data Processo, Valor
            # Total: 100% (sem scroll horizontal)
            porcentagens_colunas = [10, 25, 20, 8, 13, 13, 11]  # Total: 100%
        else:
            # Para usuário normal: Cliente, Processo, Qtd Itens, Data Entrada, Data Processo, Valor
            # Total: 100% (sem scroll horizontal)
            porcentagens_colunas = [30, 22, 10, 13, 13, 12]  # Total: 100%

        # Calcular largura total disponível da tabela
        def calcular_larguras_colunas():
            # Obter largura disponível da viewport da tabela
            largura_disponivel = self.tabela.viewport().width()

            # Se a largura ainda não foi calculada (primeira vez), usar largura mínima
            if largura_disponivel <= 0:
                largura_disponivel = 800  # Largura padrão

            # Calcular larguras baseadas nas porcentagens
            larguras_calculadas = []
            largura_total_calculada = 0

            # Calcular todas as larguras exceto a última
            for i, porcentagem in enumerate(porcentagens_colunas[:-1]):
                largura = int((largura_disponivel * porcentagem) / 100)
                largura = max(largura, 50)  # Largura mínima de 50px
                larguras_calculadas.append(largura)
                largura_total_calculada += largura

            # A última coluna recebe o espaço restante para garantir 100% de uso
            largura_ultima_coluna = largura_disponivel - largura_total_calculada
            largura_ultima_coluna = max(
                largura_ultima_coluna, 50)  # Largura mínima de 50px
            larguras_calculadas.append(largura_ultima_coluna)

            return larguras_calculadas

        # Aplicar larguras calculadas
        def aplicar_larguras():
            larguras = calcular_larguras_colunas()
            for i, largura in enumerate(larguras):
                if i < self.tabela.columnCount():
                    header.setSectionResizeMode(i, QHeaderView.Fixed)
                    self.tabela.setColumnWidth(i, largura)

        # Aplicar larguras iniciais
        aplicar_larguras()

        # Conectar redimensionamento da tabela para recalcular larguras
        def on_resize():
            aplicar_larguras()

        # Armazenar função para uso posterior
        # Configurar alinhamento dos cabeçalhos das colunas
        self.aplicar_larguras_colunas = aplicar_larguras
        # Offset para admin (coluna usuário)
        offset = 1 if self.is_admin else 0

        # Processo alinhado ao centro
        processo_col_index = 1 + offset
        processo_header_item = QTableWidgetItem("Processo")
        processo_header_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.tabela.setHorizontalHeaderItem(
            processo_col_index, processo_header_item)

        # Quantidade alinhada ao centro
        qtd_col_index = 2 + offset
        qtd_header_item = QTableWidgetItem("Qtd Itens")
        qtd_header_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.tabela.setHorizontalHeaderItem(qtd_col_index, qtd_header_item)

        # Datas alinhadas ao centro
        data_entrada_col_index = 3 + offset
        data_entrada_header_item = QTableWidgetItem("Data Entrada")
        data_entrada_header_item.setTextAlignment(
            Qt.AlignCenter | Qt.AlignVCenter)
        self.tabela.setHorizontalHeaderItem(
            data_entrada_col_index, data_entrada_header_item)

        data_processo_col_index = 4 + offset
        data_processo_header_item = QTableWidgetItem("Data Processo")
        data_processo_header_item.setTextAlignment(
            Qt.AlignCenter | Qt.AlignVCenter)
        self.tabela.setHorizontalHeaderItem(
            data_processo_col_index, data_processo_header_item)

        # Valor alinhado à direita
        valor_col_index = len(colunas) - 1  # Última coluna (Valor)
        valor_header_item = QTableWidgetItem("Valor (R$)")
        valor_header_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.tabela.setHorizontalHeaderItem(valor_col_index, valor_header_item)

        # Configurar delegates para edição de datas
        date_delegate = DateEditDelegate(self.tabela)

        # Aplicar delegate nas colunas de data
        if self.is_admin:
            # Para admin: Data Entrada = coluna 4, Data Processo = coluna 5
            self.tabela.setItemDelegateForColumn(4, date_delegate)
            self.tabela.setItemDelegateForColumn(5, date_delegate)
        else:
            # Para usuário normal: Data Entrada = coluna 3, Data Processo = coluna 4
            self.tabela.setItemDelegateForColumn(3, date_delegate)
            self.tabela.setItemDelegateForColumn(4, date_delegate)

        # Configurar tooltip para indicar que a tabela é editável
        self.tabela.setToolTip(
            "Clique duas vezes em uma célula para editar diretamente na tabela")

        # Conectar evento de edição da tabela
        self.tabela.itemChanged.connect(self.on_item_changed)

        # Conectar evento de redimensionamento para recalcular larguras das colunas
        self.tabela.resizeEvent = self.on_tabela_resize

        self.tabela_layout.addWidget(self.tabela)

        # Botão excluir abaixo da tabela
        botao_layout = QHBoxLayout()
        self.btn_excluir = QPushButton("Excluir")
        self.btn_excluir.setToolTip(
            "Excluir processo selecionado na tabela (Atalho: Delete)")

        self.btn_excluir.clicked.connect(self.excluir_processo)

        # Aplicar estilo e configuração do botão usando função unificada
        aplicar_estilo_botao(self.btn_excluir, "vermelho")

        # Adicionar estilo específico para estado desabilitado usando estilo base
        estilo_atual = self.btn_excluir.styleSheet()
        estilo_completo = estilo_atual + aplicar_estilo_botao_desabilitado()
        self.btn_excluir.setStyleSheet(estilo_completo)

        botao_layout.addStretch()  # Empurra o botão para a direita
        botao_layout.addWidget(self.btn_excluir)

        self.tabela_layout.addLayout(botao_layout)

    def criar_frame_totais(self):
        """Cria o frame que exibe os totais de processos, itens e valores."""
        self.frame_totais = QFrame()
        self.frame_totais.setFrameStyle(QFrame.StyledPanel)

        layout = QHBoxLayout()
        layout.setSpacing(ESPACAMENTO_PADRAO)  # Usar espaçamento padrão

        # Labels para totais
        self.label_total_processos = QLabel("Total Processos: 0")
        self.label_total_itens = QLabel("Total Itens: 0")
        self.label_total_valor = QLabel("Total Valor: R$ 0,00")

        # Estilo dos labels
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
        """Chamado quando a tabela é redimensionada para recalcular larguras das colunas."""
        # Chamar o evento original de redimensionamento
        QTableWidget.resizeEvent(self.tabela, event)

        # Recalcular larguras das colunas baseadas nas porcentagens
        if hasattr(self, 'aplicar_larguras_colunas'):
            # Usar QTimer para atrasar o cálculo e evitar múltiplas chamadas
            QTimer.singleShot(50, self.aplicar_larguras_colunas)

    def limpar_filtros(self):
        """Limpa todos os filtros aplicados."""
        # Bloquear sinais temporariamente para evitar múltiplas chamadas
        if self.is_admin and hasattr(self, 'combo_usuario'):
            self.combo_usuario.blockSignals(True)
            self.combo_usuario.setCurrentText("Todos os usuários")
            self.combo_usuario.blockSignals(False)

        if hasattr(self, 'entry_filtro_cliente'):
            self.entry_filtro_cliente.blockSignals(True)
            self.entry_filtro_cliente.clear()
            self.entry_filtro_cliente.blockSignals(False)

        if hasattr(self, 'entry_filtro_processo'):
            self.entry_filtro_processo.blockSignals(True)
            self.entry_filtro_processo.clear()
            self.entry_filtro_processo.blockSignals(False)

        if hasattr(self, 'combo_filtro_mes'):
            self.combo_filtro_mes.blockSignals(True)
            self.combo_filtro_mes.setCurrentText("Todos os meses")
            self.combo_filtro_mes.blockSignals(False)

        if hasattr(self, 'combo_filtro_ano'):
            self.combo_filtro_ano.blockSignals(True)
            self.combo_filtro_ano.setCurrentText("Todos os anos")
            self.combo_filtro_ano.blockSignals(False)

        # Aplicar filtros limpos
        self.aplicar_filtro()

    def on_usuario_changed(self):
        """Chamado quando o filtro de usuário muda (apenas para admins)."""
        # Reconfigurar filtros de mês e ano baseado no usuário selecionado
        self.configurar_filtros_mes_ano()
        # Aplicar filtros
        self.aplicar_filtro()

    def carregar_dados(self):
        """Carrega os dados iniciais da aplicação."""
        # Carregar usuários no combo (apenas para admins)
        if self.is_admin and hasattr(self, 'combo_usuario'):
            usuarios_list = db.buscar_usuarios_unicos()
            for user in usuarios_list:
                self.combo_usuario.addItem(user)

        # Configurar filtros de mês e ano com dados únicos
        self.configurar_filtros_mes_ano()

        self.aplicar_filtro()

        # Usar timer para garantir que a rolagem aconteça após os dados serem carregados
        QTimer.singleShot(100, self.rolar_para_ultimo_item)

    def on_item_changed(self, item):
        """Chamado quando um item da tabela é editado."""
        if not item:
            return

        try:
            # Bloquear temporariamente o sinal para evitar recursão
            self.tabela.blockSignals(True)

            row = item.row()
            col = item.column()

            # Determinar qual coluna foi editada (considerando se é admin ou não)
            col_offset = 1 if self.is_admin else 0

            # Colunas editáveis (ignorar coluna usuário se for admin)
            if self.is_admin and col == 0:  # Coluna usuário não é editável
                # Restaurar valor original
                self.aplicar_filtro(rolar_para_ultimo=False)
                return

            # Obter ID do registro
            item_com_id = self.tabela.item(row, 1 if self.is_admin else 0)
            if not item_com_id:
                return

            registro_id = item_com_id.data(Qt.UserRole)
            if not registro_id:
                return

            # Validar e formatar o valor editado baseado na coluna
            col_editada = col - col_offset
            valor_editado = item.text().strip()

            # Validações específicas por coluna
            if col_editada == 2:  # Quantidade de itens
                try:
                    qtde_test = int(valor_editado)
                    if qtde_test <= 0:
                        raise ValueError("Quantidade deve ser positiva")
                except ValueError:
                    QMessageBox.warning(
                        self, "Erro", "Quantidade de itens deve ser um número inteiro positivo.")
                    self.aplicar_filtro(rolar_para_ultimo=False)
                    return
            elif col_editada == 3:  # Data de entrada
                if valor_editado and valor_editado != "Não processado":
                    try:
                        # Validar formato e se não é data futura
                        data_obj = datetime.strptime(valor_editado, "%d/%m/%Y")
                        data_hoje = datetime.now().date()
                        if data_obj.date() > data_hoje:
                            QMessageBox.warning(
                                self, "Erro", "Data de entrada não pode ser maior que a data atual.")
                            self.aplicar_filtro(rolar_para_ultimo=False)
                            return
                    except ValueError:
                        QMessageBox.warning(
                            self, "Erro", "Data de entrada deve estar no formato DD/MM/AAAA.")
                        self.aplicar_filtro(rolar_para_ultimo=False)
                        return
            elif col_editada == 4:  # Data de processo
                if valor_editado and valor_editado != "Não processado":
                    try:
                        # Validar formato e se não é data futura
                        data_obj = datetime.strptime(valor_editado, "%d/%m/%Y")
                        data_hoje = datetime.now().date()
                        if data_obj.date() > data_hoje:
                            QMessageBox.warning(
                                self, "Erro", "Data de processo não pode ser maior que a data atual.")
                            self.aplicar_filtro(rolar_para_ultimo=False)
                            return
                    except ValueError:
                        QMessageBox.warning(
                            self, "Erro", "Data de processo deve estar no formato DD/MM/AAAA.")
                        self.aplicar_filtro(rolar_para_ultimo=False)
                        return
            elif col_editada == 5:  # Valor
                try:
                    # Limpar formatação e testar conversão
                    valor_limpo = valor_editado.replace(
                        "R$", "").replace(" ", "").replace(".", "").replace(",", ".")
                    valor_test = float(valor_limpo)
                    if valor_test < 0:
                        raise ValueError("Valor não pode ser negativo")
                    # Reformatar o valor na célula com separador de milhares
                    item.setText(formatar_valor_monetario(valor_test))
                except ValueError:
                    QMessageBox.warning(
                        self, "Erro", "Valor deve ser um número válido e não negativo.")
                    self.aplicar_filtro(rolar_para_ultimo=False)
                    return

            # Coletar todos os dados da linha
            cliente = self.tabela.item(row, col_offset).text(
            ).strip().upper()  # Garantir maiúscula
            processo = self.tabela.item(row, col_offset + 1).text().strip()
            qtde_itens = self.tabela.item(row, col_offset + 2).text().strip()
            data_entrada_text = self.tabela.item(
                row, col_offset + 3).text().strip()
            data_processo_text = self.tabela.item(
                row, col_offset + 4).text().strip()
            valor_text = self.tabela.item(row, col_offset + 5).text().strip()

            # Converter datas do formato DD/MM/AAAA para AAAA-MM-DD para o banco
            data_entrada = self.converter_data_para_banco(data_entrada_text)

            # Processar data de processo
            if data_processo_text == "Não processado" or not data_processo_text:
                data_processo = ""
            else:
                data_processo = self.converter_data_para_banco(
                    data_processo_text)

            # Processar valor (remover R$, espaços e separadores, converter vírgula decimal para ponto)
            valor_limpo = valor_text.replace(
                "R$", "").replace(" ", "").replace(".", "")
            # Converter vírgula decimal para ponto
            if "," in valor_limpo:
                # Se tem vírgula, é o separador decimal
                valor_pedido = valor_limpo.replace(",", ".")
            else:
                valor_pedido = valor_limpo

            # Atualizar no banco de dados
            resultado = db.atualizar_lancamento(
                registro_id, cliente, processo, qtde_itens,
                data_entrada, data_processo, valor_pedido
            )

            if "Sucesso" in resultado:
                # Reconfigurar filtros de mês e ano se a data de entrada foi alterada
                if col_editada == 3:  # Se foi alterada a data de entrada
                    self.configurar_filtros_mes_ano()
                # Recarregar dados para garantir consistência e atualizar totais
                self.aplicar_filtro(rolar_para_ultimo=False)
            else:
                # Em caso de erro, restaurar dados originais
                self.aplicar_filtro(rolar_para_ultimo=False)
                QMessageBox.warning(self, "Erro", resultado)

        except (ValueError, AttributeError, TypeError) as e:
            # Em caso de erro, restaurar dados originais
            self.aplicar_filtro(rolar_para_ultimo=False)
            QMessageBox.warning(
                self, "Erro", f"Erro ao atualizar registro: {str(e)}")
        finally:
            # Reativar sinais
            self.tabela.blockSignals(False)

    def converter_data_para_banco(self, data_str):
        """Converte data do formato DD/MM/AAAA para AAAA-MM-DD para o banco."""
        if not data_str or data_str == "Não processado":
            return ""

        try:
            # Se já está no formato AAAA-MM-DD, retorna como está
            if "-" in data_str and len(data_str) == 10:
                # Validar se está no formato correto
                datetime.strptime(data_str, "%Y-%m-%d")
                return data_str

            # Converter de DD/MM/AAAA para AAAA-MM-DD
            data_obj = datetime.strptime(data_str, "%d/%m/%Y")
            return data_obj.strftime("%Y-%m-%d")
        except ValueError:
            # Se não conseguir converter, retorna como veio
            return str(data_str)

    def formatar_data_para_exibicao(self, data_str):
        """Converte data do formato AAAA-MM-DD para DD/MM/AAAA."""
        if not data_str:
            return ""

        try:
            # Se já está no formato DD/MM/AAAA, retorna como está
            if "/" in data_str:
                # Validar se está no formato correto
                datetime.strptime(data_str, "%d/%m/%Y")
                return data_str

            # Converter de AAAA-MM-DD para DD/MM/AAAA
            data_obj = datetime.strptime(data_str, "%Y-%m-%d")
            return data_obj.strftime("%d/%m/%Y")
        except ValueError:
            # Se não conseguir converter, retorna como veio
            return str(data_str)

    def aplicar_filtro(self, rolar_para_ultimo=True):
        """Aplica filtros na tabela de processos baseado nos filtros selecionados."""
        # Determinar qual usuário filtrar
        if self.is_admin:
            if hasattr(self, 'combo_usuario') and self.combo_usuario.currentText() != "Todos os usuários":
                usuario_filtro = self.combo_usuario.currentText()
            else:
                usuario_filtro = None
        else:
            # Usuários normais só veem seus próprios dados
            usuario_filtro = self.usuario_logado

        # Determinar filtros de cliente e processo
        cliente_filtro = None
        if hasattr(self, 'entry_filtro_cliente') and self.entry_filtro_cliente.text().strip():
            cliente_filtro = self.entry_filtro_cliente.text().strip().upper()

        processo_filtro = None
        if hasattr(self, 'entry_filtro_processo') and self.entry_filtro_processo.text().strip():
            processo_filtro = self.entry_filtro_processo.text().strip()

        # Determinar filtros de mês e ano
        mes_filtro = None
        if hasattr(self, 'combo_filtro_mes') and self.combo_filtro_mes.currentText() != "Todos os meses":
            # Extrair número do mês (primeiros 2 caracteres)
            mes_filtro = self.combo_filtro_mes.currentText()[:2]

        ano_filtro = None
        if hasattr(self, 'combo_filtro_ano') and self.combo_filtro_ano.currentText() != "Todos os anos":
            ano_filtro = self.combo_filtro_ano.currentText()

        # Buscar dados com filtros aplicados
        registros = db.buscar_lancamentos_filtros_completos(
            usuario_filtro, cliente_filtro, processo_filtro, mes_filtro, ano_filtro)

        # Ordenar por critérios múltiplos para garantir que novos itens apareçam no final
        # Função para extrair critérios de ordenação

        def obter_data_ordenacao(registro):
            data_processo = registro[6]  # Coluna data_processo
            data_lancamento = registro[8]  # Coluna data_lancamento (timestamp)

            # Converter data_lancamento para datetime
            try:
                if data_lancamento:
                    # Tentar diferentes formatos de timestamp
                    if 'T' in str(data_lancamento):
                        # Formato ISO com T (ex: 2025-08-05T14:30:15)
                        timestamp_obj = datetime.fromisoformat(
                            str(data_lancamento).replace('Z', ''))
                    else:
                        # Formato padrão do SQLite (ex: 2025-08-05 14:30:15)
                        timestamp_obj = datetime.strptime(
                            str(data_lancamento), "%Y-%m-%d %H:%M:%S")
                else:
                    timestamp_obj = datetime.min
            except (ValueError, AttributeError) as e:
                print(f"Erro ao converter timestamp '{data_lancamento}': {e}")
                timestamp_obj = datetime.min

            if not data_processo:
                # Se não há data de processo, usar timestamp como critério principal
                # Itens sem data de processo aparecem ordenados por data de criação (mais antigo primeiro)
                return (datetime.min, timestamp_obj)
            else:
                try:
                    # Se há data de processo, ordenar por data de processo, depois por timestamp
                    data_processo_obj = datetime.strptime(
                        data_processo, "%Y-%m-%d")
                    # Combinar data de processo com timestamp para ordenação mais precisa
                    # Isso garante que dentro de um mesmo dia, a ordem seja pela hora de criação
                    return (data_processo_obj, timestamp_obj)
                except ValueError:
                    # Se não conseguir converter data de processo, usar timestamp
                    return (datetime.min, timestamp_obj)

        # Ordenar: primeiro por data de processo (menor para maior), depois por timestamp (mais antigo primeiro)
        registros_ordenados = sorted(
            registros, key=obter_data_ordenacao, reverse=False)

        # Bloquear sinais temporariamente para evitar chamadas desnecessárias
        self.tabela.blockSignals(True)

        # Preencher tabela com registros ordenados
        self.tabela.setRowCount(len(registros_ordenados))

        for row, registro in enumerate(registros_ordenados):
            col = 0

            # Se for admin, primeira coluna é usuário (não editável)
            if self.is_admin:
                item_usuario = QTableWidgetItem(str(registro[1]))
                item_usuario.setFlags(
                    item_usuario.flags() & ~Qt.ItemIsEditable)  # Não editável
                self.tabela.setItem(row, col, item_usuario)
                col += 1

            # Demais colunas (editáveis)
            item_cliente = QTableWidgetItem(
                str(registro[2]).upper())  # Exibir em maiúscula
            self.tabela.setItem(row, col, item_cliente)

            # Processo alinhado ao centro
            item_processo = QTableWidgetItem(str(registro[3]))
            item_processo.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            self.tabela.setItem(row, col + 1, item_processo)

            # Quantidade alinhada ao centro
            item_qtde = QTableWidgetItem(str(registro[4]))
            item_qtde.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            self.tabela.setItem(row, col + 2, item_qtde)

            # Formatar data de entrada DD/MM/AAAA e alinhar ao centro
            data_entrada_formatada = self.formatar_data_para_exibicao(
                registro[5])
            item_data_entrada = QTableWidgetItem(data_entrada_formatada)
            item_data_entrada.setTextAlignment(
                Qt.AlignCenter | Qt.AlignVCenter)
            self.tabela.setItem(row, col + 3, item_data_entrada)

            # Formatar data de processo DD/MM/AAAA e alinhar ao centro
            data_processo_formatada = self.formatar_data_para_exibicao(
                registro[6]) if registro[6] else "Não processado"
            item_data_processo = QTableWidgetItem(data_processo_formatada)
            item_data_processo.setTextAlignment(
                Qt.AlignCenter | Qt.AlignVCenter)
            self.tabela.setItem(row, col + 4, item_data_processo)

            # Formatar valor monetário com separador de milhares e alinhar à direita
            item_valor = QTableWidgetItem(
                formatar_valor_monetario(registro[7]))
            item_valor.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela.setItem(row, col + 5, item_valor)

            # Guardar ID do registro (invisível para o usuário)
            if not self.is_admin:
                # Para usuários normais, usar a primeira coluna (cliente) para armazenar o ID
                self.tabela.item(row, 0).setData(Qt.UserRole, registro[0])
            else:
                # Para admins, usar a segunda coluna (cliente) para armazenar o ID
                self.tabela.item(row, 1).setData(Qt.UserRole, registro[0])

        # Reativar sinais
        self.tabela.blockSignals(False)

        # Atualizar totais com todos os filtros
        cliente_filtro = None
        if hasattr(self, 'entry_filtro_cliente') and self.entry_filtro_cliente.text().strip():
            cliente_filtro = self.entry_filtro_cliente.text().strip().upper()

        processo_filtro = None
        if hasattr(self, 'entry_filtro_processo') and self.entry_filtro_processo.text().strip():
            processo_filtro = self.entry_filtro_processo.text().strip()

        mes_filtro = None
        if hasattr(self, 'combo_filtro_mes') and self.combo_filtro_mes.currentText() != "Todos os meses":
            mes_filtro = self.combo_filtro_mes.currentText()[:2]

        ano_filtro = None
        if hasattr(self, 'combo_filtro_ano') and self.combo_filtro_ano.currentText() != "Todos os anos":
            ano_filtro = self.combo_filtro_ano.currentText()

        self.atualizar_totais(usuario_filtro, cliente_filtro,
                              processo_filtro, mes_filtro, ano_filtro)

        # Rolar para o último item apenas quando solicitado
        if rolar_para_ultimo:
            self.rolar_para_ultimo_item()

    def rolar_para_ultimo_item(self):
        """Rola a tabela para mostrar o último item (mais recente)."""
        if self.tabela.rowCount() > 0:
            # Rolar para a última linha
            ultima_linha = self.tabela.rowCount() - 1
            self.tabela.scrollToBottom()
            # Também garantir que a linha seja selecionada visualmente
            self.tabela.selectRow(ultima_linha)

    def atualizar_totais(self, usuario_filtro=None, cliente_filtro=None, processo_filtro=None, mes_filtro=None, ano_filtro=None):
        """Atualiza os totais exibidos no painel de estatísticas."""
        estatisticas = db.buscar_estatisticas_completas(
            usuario_filtro, cliente_filtro, processo_filtro, mes_filtro, ano_filtro)

        self.label_total_processos.setText(
            f"Total Processos: {estatisticas['total_processos']}"
        )
        self.label_total_itens.setText(
            f"Total Itens: {estatisticas['total_itens']}")
        self.label_total_valor.setText(
            f"Total Valor: {formatar_valor_monetario(estatisticas['total_valor'])}"
        )

    def adicionar_processo(self):
        """Adiciona um novo processo com os dados preenchidos."""
        cliente = self.entry_cliente.text().strip().upper()  # Garantir maiúscula
        processo = self.entry_processo.text().strip()
        qtde_itens = self.entry_qtde_itens.text().strip()

        # Validar data de entrada
        data_entrada_qdate = self.entry_data_entrada.date()
        if data_entrada_qdate > QDate.currentDate():
            QMessageBox.warning(
                self, "Erro", "Data de entrada não pode ser maior que a data atual.")
            return
        data_entrada = data_entrada_qdate.toString("yyyy-MM-dd")

        # Verificar se a data de processo foi preenchida e validar
        data_processo_qdate = self.entry_data_processo.date()
        if not data_processo_qdate.isNull():
            if data_processo_qdate > QDate.currentDate():
                QMessageBox.warning(
                    self, "Erro", "Data de processo não pode ser maior que a data atual.")
                return
            data_processo = data_processo_qdate.toString("yyyy-MM-dd")
        else:
            data_processo = ""

        valor_pedido = self.entry_valor_pedido.text().strip()

        resultado = db.adicionar_lancamento(
            self.usuario_logado,
            cliente,
            processo,
            qtde_itens,
            data_entrada,
            data_processo,
            valor_pedido,
        )

        if "Sucesso" in resultado:
            QMessageBox.information(self, "Sucesso", resultado)
            # Limpar campos
            self.entry_cliente.clear()
            self.entry_processo.clear()
            self.entry_qtde_itens.clear()
            self.entry_data_entrada.setDate(QDate.currentDate())
            self.entry_data_processo.clear()
            self.entry_valor_pedido.clear()

            # Atualizar autocompletar de clientes
            self.atualizar_autocompletar_cliente()
            self.atualizar_autocompletar_filtro_cliente()

            # Reconfigurar filtros de mês e ano (podem ter novos valores)
            self.configurar_filtros_mes_ano()

            # Atualizar tabela
            self.aplicar_filtro()

            # Rolar para o último item (novo processo adicionado)
            self.rolar_para_ultimo_item()

            # Focar no primeiro campo
            self.entry_cliente.setFocus()
        else:
            QMessageBox.warning(self, "Erro", resultado)

    def excluir_processo(self):
        """Exclui o processo selecionado na tabela."""
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.information(
                self, "Seleção", "Selecione um processo na tabela para excluir.\n\nDica: Clique em uma linha da tabela e pressione Delete ou use o botão 'Excluir Selecionado'.")
            return

        # Obter dados do processo para mostrar na confirmação
        if not self.is_admin:
            cliente = self.tabela.item(row, 0).text()  # coluna cliente
            processo = self.tabela.item(row, 1).text()  # coluna processo
        else:
            # coluna cliente (segunda para admin)
            cliente = self.tabela.item(row, 1).text()
            processo = self.tabela.item(row, 2).text()  # coluna processo

        # Confirmar exclusão com informações do processo
        resposta = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir este processo?\n\nCliente: {cliente}\nProcesso: {processo}",
            QMessageBox.Yes | QMessageBox.No,
        )

        if resposta == QMessageBox.Yes:
            # Pegar ID do registro armazenado nos dados do item
            if not self.is_admin:
                item_com_id = self.tabela.item(row, 0)  # coluna cliente
            else:
                # coluna cliente (segunda para admin)
                item_com_id = self.tabela.item(row, 1)

            if item_com_id:
                registro_id = item_com_id.data(Qt.UserRole)
                resultado = db.excluir_lancamento(registro_id)

                if "Sucesso" in resultado:
                    QMessageBox.information(self, "Sucesso", resultado)
                    # Reconfigurar filtros de mês e ano (podem ter perdido valores)
                    self.configurar_filtros_mes_ano()
                    self.aplicar_filtro(rolar_para_ultimo=False)
                else:
                    QMessageBox.warning(self, "Erro", resultado)


class MainWindow(QMainWindow):
    """Janela principal do aplicativo."""

    logout_requested = Signal()

    def __init__(self, usuario_logado, is_admin):
        super().__init__()
        self.usuario_logado = usuario_logado
        self.is_admin = is_admin

        self.setWindowTitle(
            f"Controle de Processos - Usuário: {usuario_logado}")
        self.setMinimumSize(800, 600)

        # Widget central
        self.setCentralWidget(ProcessosWidget(usuario_logado, is_admin))

        # Menu
        self.criar_menu()

        # Status bar
        self.statusBar().showMessage(
            f"Logado como: {usuario_logado} {'(Admin)' if is_admin else ''}"
        )

    def criar_menu(self):
        """Cria o menu da aplicação."""
        menubar = self.menuBar()

        # Menu Arquivo
        arquivo_menu = menubar.addMenu("Arquivo")

        logout_action = QAction("Logout", self)
        logout_action.triggered.connect(self.fazer_logout)
        arquivo_menu.addAction(logout_action)

        arquivo_menu.addSeparator()  # Separador visual

        sair_action = QAction("Sair", self)
        sair_action.triggered.connect(self.close)
        arquivo_menu.addAction(sair_action)

        # Menu Admin (apenas para administradores)
        if self.is_admin:
            admin_menu = menubar.addMenu("Admin")

            usuarios_action = QAction("Gerenciar Usuários", self)
            usuarios_action.triggered.connect(self.abrir_gerenciar_usuarios)
            admin_menu.addAction(usuarios_action)

    def abrir_gerenciar_usuarios(self):
        """Abre o diálogo de gerenciamento de usuários."""
        try:

            dialog = GerenciarUsuariosDialog(self)
            dialog.exec()
        except ImportError as e:
            QMessageBox.warning(
                self, "Erro", f"Erro ao carregar gerenciador de usuários: {e}"
            )
        except (OSError, RuntimeError) as e:
            QMessageBox.warning(self, "Erro", f"Erro inesperado: {e}")

    def fazer_logout(self):
        """Realiza o logout do usuário atual e volta para a tela de login."""
        resposta = QMessageBox.question(
            self,
            "Logout",
            "Tem certeza que deseja fazer logout?",
            QMessageBox.Yes | QMessageBox.No
        )

        if resposta == QMessageBox.Yes:
            # Emitir sinal de logout para a aplicação principal gerenciar
            self.logout_requested.emit()
            # Fechar a janela atual
            self.close()


class ControleProcessosApp:
    """Classe principal da aplicação."""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Controle de Processos")
        self.main_window = None

    def run(self):
        """Executa a aplicação."""
        self.mostrar_login()
        return self.app.exec()

    def mostrar_login(self):
        """Mostra a tela de login."""
        login_dialog = LoginDialog()

        if login_dialog.exec() == QDialog.Accepted:
            # Login bem-sucedido, abrir janela principal
            if self.main_window:
                self.main_window.close()

            self.main_window = MainWindow(
                login_dialog.usuario_logado,
                login_dialog.is_admin
            )
            # Conectar o sinal de logout da janela principal
            self.main_window.logout_requested.connect(self.mostrar_login)
            self.main_window.show()
        else:
            # Login cancelado
            QApplication.quit()


if __name__ == "__main__":
    app = ControleProcessosApp()
    sys.exit(app.run())
