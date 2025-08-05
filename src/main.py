"""
Sistema de Controle de Processos para Desenhistas

Este módulo implementa uma interface gráfica completa para gerenciamento
de processos realizados por desenhistas, incluindo sistema de autenticação,
controle de usuários e gestão de dados com banco SQLite.
"""

import sys

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
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
)

from utils import database as db
from utils import usuario
from gerenciar_usuarios import GerenciarUsuariosDialog


class LoginDialog(QDialog):
    """Dialog de login para autenticação de usuários."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login - Controle de Processos")
        self.setFixedSize(300, 150)
        self.usuario_logado = None
        self.is_admin = False

        self.entry_data_processo = None
        self.entry_cliente = None
        self.entry_processo = None
        self.entry_qtde_itens = None
        self.entry_data_entrada = None

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
        """Realiza a autenticação do usuário."""
        nome = self.entry_usuario.text().strip()
        senha = self.entry_senha.text().strip()

        if not nome or not senha:
            QMessageBox.warning(self, "Erro", "Preencha usuário e senha.")
            return

        # Verificar se precisa redefinir senha
        if usuario.verificar_senha_reset(nome):
            self.solicitar_nova_senha(nome)
            return

        resultado = usuario.verificar_login(nome, senha)

        if resultado["sucesso"]:
            self.usuario_logado = resultado["nome"]
            self.is_admin = resultado["admin"]
            self.accept()
        else:
            QMessageBox.warning(self, "Erro de Login", resultado["mensagem"])
            self.entry_senha.clear()

    def solicitar_nova_senha(self, nome):
        """Solicita nova senha quando o usuário tem senha de reset."""

        nova_senha, ok = QInputDialog.getText(
            self,
            "Nova Senha Requerida",
            "Sua senha foi resetada. Digite uma nova senha:",
            QLineEdit.Password,
        )

        if ok and nova_senha.strip():
            resultado = usuario.alterar_senha_usuario(
                nome, "nova_senha", nova_senha)
            if "Sucesso" in resultado:
                QMessageBox.information(
                    self, "Sucesso", "Senha alterada com sucesso. Faça login novamente."
                )
                self.entry_senha.clear()
            else:
                QMessageBox.warning(self, "Erro", resultado)
        else:
            QMessageBox.warning(self, "Erro", "Nova senha é obrigatória.")

    def abrir_novo_usuario(self):
        """Abre o diálogo para criação de novo usuário."""
        dialog = NovoUsuarioDialog()
        dialog.exec()


class NovoUsuarioDialog(QDialog):
    """Dialog para criação de novos usuários."""

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
        """Salva o novo usuário no banco de dados."""
        nome = self.entry_nome.text().strip()
        senha = self.entry_senha.text().strip()
        admin = (
            self.check_admin.isChecked()
            if not usuario.verificar_admin_existente()
            else False
        )

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
        self.btn_filtrar = None
        self.tabela_layout = None
        self.tabela = None
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

    def criar_frame_entrada(self):
        """Cria o frame de entrada de dados."""
        self.frame_entrada = QFrame()
        self.frame_entrada.setFrameStyle(QFrame.StyledPanel)

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
        self.entry_data_processo.setDate(QDate.currentDate())  # Data nula

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
        """Cria a interface da tabela de processos com filtros."""
        self.tabela_layout = QVBoxLayout()

        # Filtros (apenas para admins)
        if self.is_admin:
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

        # Configurar redimensionamento das colunas
        header = self.tabela.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        self.tabela_layout.addWidget(self.tabela)

    def criar_frame_totais(self):
        """Cria o frame que exibe os totais de processos, itens e valores."""
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
        """Carrega os dados iniciais da aplicação."""
        # Carregar usuários no combo (apenas para admins)
        if self.is_admin and hasattr(self, 'combo_usuario'):
            usuarios_list = db.buscar_usuarios_unicos()
            for user in usuarios_list:
                self.combo_usuario.addItem(user)

        self.aplicar_filtro()

    def aplicar_filtro(self):
        """Aplica filtros na tabela de processos baseado no usuário selecionado."""
        # Determinar qual usuário filtrar
        if self.is_admin:
            if hasattr(self, 'combo_usuario') and self.combo_usuario.currentText() != "Todos os usuários":
                usuario_filtro = self.combo_usuario.currentText()
            else:
                usuario_filtro = None
        else:
            # Usuários normais só veem seus próprios dados
            usuario_filtro = self.usuario_logado

        # Buscar dados
        registros = db.buscar_lancamentos_filtros(usuario_filtro)

        # Preencher tabela
        self.tabela.setRowCount(len(registros))

        for row, registro in enumerate(registros):
            col = 0

            # Se for admin, primeira coluna é usuário
            if self.is_admin:
                self.tabela.setItem(
                    row, col, QTableWidgetItem(str(registro[1]))
                )  # usuário
                col += 1

            # Demais colunas
            self.tabela.setItem(row, col, QTableWidgetItem(
                str(registro[2])))  # cliente
            self.tabela.setItem(
                row, col + 1, QTableWidgetItem(str(registro[3]))
            )  # processo
            self.tabela.setItem(
                row, col + 2, QTableWidgetItem(str(registro[4]))
            )  # qtde_itens
            self.tabela.setItem(
                # data_entrada
                row,
                col + 3,
                QTableWidgetItem(str(registro[5])),
            )
            self.tabela.setItem(
                row,
                col + 4,
                QTableWidgetItem(
                    # data_processo
                    str(registro[6])
                    if registro[6]
                    else "Não processado"
                ),
            )
            self.tabela.setItem(
                # valor
                row,
                col + 5,
                QTableWidgetItem(f"R$ {registro[7]:.2f}".replace(".", ",")),
            )

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
        """Atualiza os totais exibidos no painel de estatísticas."""
        estatisticas = db.buscar_estatisticas(usuario_filtro)

        self.label_total_processos.setText(
            f"Total Processos: {estatisticas['total_processos']}"
        )
        self.label_total_itens.setText(
            f"Total Itens: {estatisticas['total_itens']}")
        self.label_total_valor.setText(
            f"Total Valor: R$ {estatisticas['total_valor']:.2f}".replace(
                ".", ",")
        )

    def adicionar_processo(self):
        """Adiciona um novo processo com os dados preenchidos."""
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

            # Atualizar tabela
            self.aplicar_filtro()

            # Focar no primeiro campo
            self.entry_cliente.setFocus()
        else:
            QMessageBox.warning(self, "Erro", resultado)

    def excluir_processo(self):
        """Exclui o processo selecionado na tabela."""
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(
                self, "Seleção", "Selecione um processo para excluir.")
            return

        # Confirmar exclusão
        resposta = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            "Tem certeza que deseja excluir este processo?",
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
                    self.aplicar_filtro()
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
