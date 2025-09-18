"""Módulo da janela principal do aplicativo."""

from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox

from ..gerenciar_usuarios import GerenciarUsuariosDialog
from ..utils import session_manager
from ..widgets.processos_widget import ProcessosWidget


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

        self.setCentralWidget(ProcessosWidget(usuario_logado, is_admin))

        self.criar_menu()

        self.statusBar().showMessage(
            f"Logado como: {usuario_logado} {'(Admin)' if is_admin else ''}"
        )

        self.heartbeat_timer = QTimer()
        self.heartbeat_timer.timeout.connect(self.atualizar_heartbeat)
        self.heartbeat_timer.start(30000)

        self.command_timer = QTimer()
        self.command_timer.timeout.connect(self.verificar_comando_sistema)
        self.command_timer.start(5000)

    def atualizar_heartbeat(self):
        """Atualiza o heartbeat da sessão."""
        session_manager.atualizar_heartbeat_sessao()

    def verificar_comando_sistema(self):
        """Verifica se há comandos do sistema para executar."""
        comando_global = session_manager.obter_comando_sistema()
        if comando_global == "SHUTDOWN":
            QMessageBox.information(
                self,
                "Sistema",
                (
                    "O administrador solicitou o fechamento do sistema.\n"
                    "A aplicação será encerrada."
                ),
            )
            session_manager.limpar_comando_sistema()
            QApplication.quit()

    def closeEvent(self, event):  # pylint: disable=invalid-name
        """Remove a sessão ao fechar a janela."""
        session_manager.remover_sessao()
        event.accept()

    def criar_menu(self):
        """Cria os menus (Arquivo/Admin)."""
        menubar = self.menuBar()

        arquivo_menu = menubar.addMenu("Arquivo")

        logout_action = QAction("Logout", self)
        logout_action.triggered.connect(self.fazer_logout)
        arquivo_menu.addAction(logout_action)

        arquivo_menu.addSeparator()

        sair_action = QAction("Sair", self)
        sair_action.triggered.connect(self.close)
        arquivo_menu.addAction(sair_action)

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
        """Faz logout e retorna para a tela de login."""
        resposta = QMessageBox.question(
            self,
            "Logout",
            "Tem certeza que deseja fazer logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if resposta == QMessageBox.StandardButton.Yes:
            session_manager.remover_sessao()
            self.logout_requested.emit()
            self.close()
