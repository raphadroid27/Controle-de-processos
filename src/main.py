import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QTableWidget, QTableWidgetItem,
                               QLineEdit, QPushButton, QLabel, QMessageBox,
                               QDialog, QFormLayout, QCheckBox, QTabWidget,
                               QHeaderView, QDateEdit, QComboBox, QFrame)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QAction
import utils.database as db
import utils.usuario as usuario


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login - Controle de Processos")
        self.setFixedSize(300, 150)
        self.usuario_logado = None
        self.is_admin = False

        layout = QFormLayout()

        self.entry_usuario = QLineEdit()
        self.entry_senha = QLineEdit()
        self.entry_senha.setEchoMode(QLineEdit.Password)

        layout.addRow("Usuário:", self.entry_usuario)
        layout.addRow("Senha:", self.entry_senha)

        # Botões
        btn_layout = QHBoxLayout()
        self.btn_login = QPushButton("Login")
        self.btn_novo_usuario = QPushButton("Novo Usuário")

        btn_layout.addWidget(self.btn_login)
        btn_layout.addWidget(self.btn_novo_usuario)

        layout.addRow(btn_layout)

        self.setLayout(layout)

        # Conectar eventos
        self.btn_login.clicked.connect(self.fazer_login)
        self.btn_novo_usuario.clicked.connect(self.abrir_novo_usuario)
        self.entry_senha.returnPressed.connect(self.fazer_login)

    def fazer_login(self):
        nome = self.entry_usuario.text().strip()
        senha = self.entry_senha.text().strip()

        if not nome or not senha:
            QMessageBox.warning(self, "Erro", "Preencha usuário e senha.")
            return

        resultado = usuario.verificar_login(nome, senha)

        if resultado['sucesso']:
            self.usuario_logado = resultado['nome']
            self.is_admin = resultado['admin']
            self.accept()
        else:
            QMessageBox.warning(self, "Erro de Login", resultado['mensagem'])
            self.entry_senha.clear()

    def abrir_novo_usuario(self):
        dialog = NovoUsuarioDialog()
        dialog.exec()


class NovoUsuarioDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Novo Usuário")
        self.setFixedSize(300, 200)

        layout = QFormLayout()

        self.entry_nome = QLineEdit()
        self.entry_senha = QLineEdit()
        self.entry_senha.setEchoMode(QLineEdit.Password)
        self.check_admin = QCheckBox()

        layout.addRow("Nome:", self.entry_nome)
        layout.addRow("Senha:", self.entry_senha)

        # Só mostra opção admin se não existir um
        if not usuario.verificar_admin_existente():
            layout.addRow("Admin:", self.check_admin)

        # Botões
        btn_layout = QHBoxLayout()
        self.btn_salvar = QPushButton("Salvar")
        self.btn_cancelar = QPushButton("Cancelar")

        btn_layout.addWidget(self.btn_salvar)
        btn_layout.addWidget(self.btn_cancelar)

        layout.addRow(btn_layout)

        self.setLayout(layout)

        # Conectar eventos
        self.btn_salvar.clicked.connect(self.salvar_usuario)
        self.btn_cancelar.clicked.connect(self.reject)

    def salvar_usuario(self):
        nome = self.entry_nome.text().strip()
        senha = self.entry_senha.text().strip()
        admin = self.check_admin.isChecked(
        ) if not usuario.verificar_admin_existente() else False

        if not nome or not senha:
            QMessageBox.warning(self, "Erro", "Nome e senha são obrigatórios.")
            return

        resultado = usuario.inserir_usuario(nome, senha, admin)

        if "Sucesso" in resultado:
            QMessageBox.information(self, "Sucesso", resultado)
            self.accept()
        else:
            QMessageBox.warning(self, "Erro", resultado)


class ProcessosWidget(QWidget):
    def __init__(self, usuario_logado, is_admin):
        super().__init__()
        self.usuario_logado = usuario_logado
        self.is_admin = is_admin

        self.init_ui()
        self.carregar_dados()

    def init_ui(self):
        layout = QVBoxLayout()

        # Frame de entrada de dados
        self.criar_frame_entrada()
        layout.addWidget(self.frame_entrada)

        # Tabela
        self.criar_tabela()
        layout.addLayout(self.tabela_layout)

        # Frame de totais
        self.criar_frame_totais()
        layout.addWidget(self.frame_totais)

        self.setLayout(layout)

    def criar_frame_entrada(self):
        self.frame_entrada = QFrame()
        self.frame_entrada.setFrameStyle(QFrame.StyledPanel)

        layout = QFormLayout()

        # Campos de entrada
        self.entry_cliente = QLineEdit()
        self.entry_processo = QLineEdit()
        self.entry_qtde_itens = QLineEdit()
        self.entry_data_entrada = QDateEdit()
        self.entry_data_entrada.setDate(QDate.currentDate())
        self.entry_data_entrada.setCalendarPopup(True)

        self.entry_data_processo = QDateEdit()
        self.entry_data_processo.setCalendarPopup(True)
        self.entry_data_processo.setSpecialValueText("Não processado")
        self.entry_data_processo.setDate(QDate())  # Data nula

        self.entry_valor_pedido = QLineEdit()
        self.entry_valor_pedido.setPlaceholderText("0.00")

        # Layout horizontal para os campos
        campos_layout = QHBoxLayout()

        # Coluna 1
        col1 = QVBoxLayout()
        col1.addWidget(QLabel("Cliente:"))
        col1.addWidget(self.entry_cliente)
        campos_layout.addLayout(col1)

        # Coluna 2
        col2 = QVBoxLayout()
        col2.addWidget(QLabel("Processo:"))
        col2.addWidget(self.entry_processo)
        campos_layout.addLayout(col2)

        # Coluna 3
        col3 = QVBoxLayout()
        col3.addWidget(QLabel("Qtd. Itens:"))
        col3.addWidget(self.entry_qtde_itens)
        campos_layout.addLayout(col3)

        # Coluna 4
        col4 = QVBoxLayout()
        col4.addWidget(QLabel("Data Entrada:"))
        col4.addWidget(self.entry_data_entrada)
        campos_layout.addLayout(col4)

        # Coluna 5
        col5 = QVBoxLayout()
        col5.addWidget(QLabel("Data Processo:"))
        col5.addWidget(self.entry_data_processo)
        campos_layout.addLayout(col5)

        # Coluna 6
        col6 = QVBoxLayout()
        col6.addWidget(QLabel("Valor (R$):"))
        col6.addWidget(self.entry_valor_pedido)
        campos_layout.addLayout(col6)

        # Botões
        col7 = QVBoxLayout()
        self.btn_adicionar = QPushButton("Adicionar")
        self.btn_excluir = QPushButton("Excluir")
        self.btn_excluir.setStyleSheet("background-color: #ff4444;")

        col7.addWidget(self.btn_adicionar)
        col7.addWidget(self.btn_excluir)
        campos_layout.addLayout(col7)

        self.frame_entrada.setLayout(campos_layout)

        # Conectar eventos
        self.btn_adicionar.clicked.connect(self.adicionar_processo)
        self.btn_excluir.clicked.connect(self.excluir_processo)

    def criar_tabela(self):
        self.tabela_layout = QVBoxLayout()

        # Filtros
        filtro_layout = QHBoxLayout()
        filtro_layout.addWidget(QLabel("Filtrar por usuário:"))

        self.combo_usuario = QComboBox()
        self.combo_usuario.addItem("Todos os usuários")
        filtro_layout.addWidget(self.combo_usuario)

        self.btn_filtrar = QPushButton("Filtrar")
        self.btn_filtrar.clicked.connect(self.aplicar_filtro)
        filtro_layout.addWidget(self.btn_filtrar)

        filtro_layout.addStretch()
        self.tabela_layout.addLayout(filtro_layout)

        # Tabela
        self.tabela = QTableWidget()
        colunas = ["Cliente", "Processo", "Qtd Itens",
                   "Data Entrada", "Data Processo", "Valor (R$)"]

        # Se for admin, mostra coluna usuário
        if self.is_admin:
            colunas.insert(0, "Usuário")

        self.tabela.setColumnCount(len(colunas))
        self.tabela.setHorizontalHeaderLabels(colunas)

        # Configurar redimensionamento das colunas
        header = self.tabela.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        self.tabela_layout.addWidget(self.tabela)

    def criar_frame_totais(self):
        self.frame_totais = QFrame()
        self.frame_totais.setFrameStyle(QFrame.StyledPanel)

        layout = QHBoxLayout()

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

    def carregar_dados(self):
        # Carregar usuários no combo
        if self.is_admin:
            usuarios_list = db.buscar_usuarios_unicos()
            for user in usuarios_list:
                self.combo_usuario.addItem(user)

        self.aplicar_filtro()

    def aplicar_filtro(self):
        # Determinar qual usuário filtrar
        if self.is_admin and self.combo_usuario.currentText() != "Todos os usuários":
            usuario_filtro = self.combo_usuario.currentText()
        elif not self.is_admin:
            usuario_filtro = self.usuario_logado
        else:
            usuario_filtro = None

        # Buscar dados
        registros = db.buscar_lancamentos_filtros(usuario_filtro)

        # Preencher tabela
        self.tabela.setRowCount(len(registros))

        for row, registro in enumerate(registros):
            col = 0

            # Se for admin, primeira coluna é usuário
            if self.is_admin:
                self.tabela.setItem(row, col, QTableWidgetItem(
                    str(registro[1])))  # usuário
                col += 1

            # Demais colunas
            self.tabela.setItem(row, col, QTableWidgetItem(
                str(registro[2])))     # cliente
            self.tabela.setItem(
                row, col+1, QTableWidgetItem(str(registro[3])))   # processo
            self.tabela.setItem(
                row, col+2, QTableWidgetItem(str(registro[4])))   # qtde_itens
            self.tabela.setItem(
                # data_entrada
                row, col+3, QTableWidgetItem(str(registro[5])))
            self.tabela.setItem(row, col+4, QTableWidgetItem(
                # data_processo
                str(registro[6]) if registro[6] else "Não processado"))
            self.tabela.setItem(
                # valor
                row, col+5, QTableWidgetItem(f"R$ {registro[7]:.2f}".replace('.', ',')))

            # Guardar ID do registro (invisível para o usuário)
            item_id = QTableWidgetItem(str(registro[0]))
            # Armazenar ID como dados do item
            item_id.setData(Qt.UserRole, registro[0])
            if not self.is_admin:
                # Para usuários normais, usar a primeira coluna (cliente) para armazenar o ID
                self.tabela.item(row, 0).setData(Qt.UserRole, registro[0])
            else:
                # Para admins, usar a segunda coluna (cliente) para armazenar o ID
                self.tabela.item(row, 1).setData(Qt.UserRole, registro[0])

        # Atualizar totais
        self.atualizar_totais(usuario_filtro)

    def atualizar_totais(self, usuario_filtro=None):
        estatisticas = db.buscar_estatisticas(usuario_filtro)

        self.label_total_processos.setText(
            f"Total Processos: {estatisticas['total_processos']}")
        self.label_total_itens.setText(
            f"Total Itens: {estatisticas['total_itens']}")
        self.label_total_valor.setText(
            f"Total Valor: R$ {estatisticas['total_valor']:.2f}".replace('.', ','))

    def adicionar_processo(self):
        cliente = self.entry_cliente.text().strip()
        processo = self.entry_processo.text().strip()
        qtde_itens = self.entry_qtde_itens.text().strip()
        data_entrada = self.entry_data_entrada.date().toString("yyyy-MM-dd")

        # Verificar se a data de processo foi preenchida
        if not self.entry_data_processo.date().isNull():
            data_processo = self.entry_data_processo.date().toString("yyyy-MM-dd")
        else:
            data_processo = ""

        valor_pedido = self.entry_valor_pedido.text().strip()

        resultado = db.adicionar_lancamento(
            self.usuario_logado, cliente, processo, qtde_itens,
            data_entrada, data_processo, valor_pedido
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

            # Atualizar tabela
            self.aplicar_filtro()

            # Focar no primeiro campo
            self.entry_cliente.setFocus()
        else:
            QMessageBox.warning(self, "Erro", resultado)

    def excluir_processo(self):
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(
                self, "Seleção", "Selecione um processo para excluir.")
            return

        # Confirmar exclusão
        resposta = QMessageBox.question(self, "Confirmar Exclusão",
                                        "Tem certeza que deseja excluir este processo?",
                                        QMessageBox.Yes | QMessageBox.No)

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
                    self.aplicar_filtro()
                else:
                    QMessageBox.warning(self, "Erro", resultado)


class MainWindow(QMainWindow):
    def __init__(self, usuario_logado, is_admin):
        super().__init__()
        self.usuario_logado = usuario_logado
        self.is_admin = is_admin

        self.setWindowTitle(
            f"Controle de Processos - Usuário: {usuario_logado}")
        self.setGeometry(100, 100, 1200, 800)

        # Widget central
        self.setCentralWidget(ProcessosWidget(usuario_logado, is_admin))

        # Menu
        self.criar_menu()

        # Status bar
        self.statusBar().showMessage(
            f"Logado como: {usuario_logado} {'(Admin)' if is_admin else ''}")

    def criar_menu(self):
        menubar = self.menuBar()

        # Menu Arquivo
        arquivo_menu = menubar.addMenu('Arquivo')

        sair_action = QAction('Sair', self)
        sair_action.triggered.connect(self.close)
        arquivo_menu.addAction(sair_action)

        # Menu Admin (apenas para administradores)
        if self.is_admin:
            admin_menu = menubar.addMenu('Admin')

            usuarios_action = QAction('Gerenciar Usuários', self)
            usuarios_action.triggered.connect(self.abrir_gerenciar_usuarios)
            admin_menu.addAction(usuarios_action)

    def abrir_gerenciar_usuarios(self):
        QMessageBox.information(self, "Em Desenvolvimento",
                                "Funcionalidade de gerenciamento de usuários será implementada em breve.")


class ControleProcessosApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Controle de Processos")

    def run(self):
        # Mostrar dialog de login
        login_dialog = LoginDialog()

        if login_dialog.exec() == QDialog.Accepted:
            # Login bem-sucedido, abrir janela principal
            main_window = MainWindow(
                login_dialog.usuario_logado, login_dialog.is_admin)
            main_window.show()

            return self.app.exec()
        else:
            # Login cancelado
            return 0


if __name__ == "__main__":
    app = ControleProcessosApp()
    sys.exit(app.run())
