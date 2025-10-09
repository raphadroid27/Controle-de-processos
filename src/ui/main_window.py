"""Módulo da janela principal do aplicativo."""

from PySide6.QtCore import QSignalBlocker, QTimer, Signal
from PySide6.QtGui import QAction, QActionGroup, QKeySequence
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QMessageBox

from ..gerenciar_usuarios import GerenciarUsuariosDialog
from ..utils import session_manager
from ..widgets.dashboard_dialog import DashboardDialog
from ..widgets.processos_widget import ProcessosWidget
from .theme_manager import ThemeManager


class MainWindow(QMainWindow):
    """Janela principal do aplicativo."""

    logout_requested = Signal()

    def __init__(self, usuario_logado, is_admin):
        super().__init__()
        self.usuario_logado = usuario_logado
        self.is_admin = is_admin
        self._theme_manager = ThemeManager.instance()
        self._theme_actions: dict[str, QAction] = {}
        self._theme_action_group: QActionGroup | None = None
        self._style_actions: dict[str, QAction] = {}
        self._style_action_group: QActionGroup | None = None
        self._color_actions: dict[str, QAction] = {}
        self._color_action_group: QActionGroup | None = None

        self.setWindowTitle("Controle de Processos")
        self.setMinimumSize(800, 600)

        self.setCentralWidget(ProcessosWidget(usuario_logado, is_admin))

        self.criar_menu()
        self._theme_manager.register_listener(self._on_tema_atualizado)
        self._theme_manager.register_color_listener(
            self._on_cor_tema_atualizada)

        status_text = f"Logado como: {usuario_logado}"
        if is_admin:
            status_text += " (Admin)"

        self._usuario_status_label = QLabel(status_text)
        self.statusBar().addPermanentWidget(self._usuario_status_label)

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
        self._theme_manager.unregister_listener(self._on_tema_atualizado)
        self._theme_manager.unregister_color_listener(
            self._on_cor_tema_atualizada)
        session_manager.remover_sessao()
        event.accept()

    def criar_menu(self):
        """Cria os menus (Arquivo/Admin)."""
        menubar = self.menuBar()

        arquivo_menu = menubar.addMenu("Arquivo")

        logout_action = QAction("Logout", self)
        logout_action.triggered.connect(self.fazer_logout)
        logout_action.setShortcut(QKeySequence("Ctrl+Shift+L"))
        logout_action.setStatusTip("Encerrar sessão atual e retornar ao login")
        logout_action.setToolTip("Logout (Ctrl+Shift+L)")
        arquivo_menu.addAction(logout_action)

        arquivo_menu.addSeparator()

        sair_action = QAction("Sair", self)
        sair_action.triggered.connect(self.close)
        sair_action.setShortcut(QKeySequence("Ctrl+Q"))
        sair_action.setStatusTip("Fechar a aplicação")
        sair_action.setToolTip("Sair do sistema (Ctrl+Q)")
        arquivo_menu.addAction(sair_action)

        if self.is_admin:
            admin_menu = menubar.addMenu("Admin")

            usuarios_action = QAction("Gerenciar Usuários", self)
            usuarios_action.triggered.connect(self.abrir_gerenciar_usuarios)
            usuarios_action.setShortcut(QKeySequence("Ctrl+G"))
            usuarios_action.setStatusTip(
                "Abrir gerenciamento de usuários e sessões")
            usuarios_action.setToolTip("Gerenciar usuários (Ctrl+G)")
            admin_menu.addAction(usuarios_action)

            dashboard_action = QAction("Dashboard", self)
            dashboard_action.triggered.connect(self.abrir_dashboard)
            dashboard_action.setShortcut(QKeySequence("Ctrl+D"))
            dashboard_action.setStatusTip("Visualizar indicadores gerenciais")
            dashboard_action.setToolTip("Abrir dashboard (Ctrl+D)")
            admin_menu.addAction(dashboard_action)

        self._criar_menu_tema(menubar)

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

    def abrir_dashboard(self):
        """Abre o dashboard administrativo."""
        try:
            dialog = DashboardDialog(self)
            dialog.exec()
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.warning(
                self,
                "Erro",
                f"Não foi possível abrir o dashboard: {exc}",
            )

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

    # ------------------------------------------------------------------
    # Tema
    # ------------------------------------------------------------------

    def _criar_menu_tema(self, menubar) -> None:
        tema_menu = menubar.addMenu("Tema")
        self._theme_action_group = QActionGroup(self)
        self._theme_action_group.setExclusive(True)
        self._theme_actions.clear()

        opcoes = [
            ("Claro", "light"),
            ("Escuro", "dark"),
        ]

        for rotulo, modo in opcoes:
            action = QAction(rotulo, self, checkable=True)
            action.setData(modo)
            action.triggered.connect(self._on_tema_selecionado)
            action.setStatusTip(f"Aplicar tema {rotulo.lower()}")
            action.setToolTip(f"Aplicar tema {rotulo.lower()}")
            tema_menu.addAction(action)
            self._theme_action_group.addAction(action)
            self._theme_actions[modo] = action

        tema_menu.addSeparator()
        estilo_menu = tema_menu.addMenu("Estilo")
        self._style_action_group = QActionGroup(self)
        self._style_action_group.setExclusive(True)
        self._style_actions.clear()

        estilos_opcoes = [
            ("Fusion", "Fusion"),
            ("Windows", "Windows"),
        ]

        for rotulo, estilo in estilos_opcoes:
            action = QAction(rotulo, self, checkable=True)
            action.setData(estilo)
            action.triggered.connect(self._on_estilo_selecionado)
            action.setStatusTip(f"Aplicar estilo {rotulo}")
            action.setToolTip(f"Aplicar estilo {rotulo}")
            estilo_menu.addAction(action)
            self._style_action_group.addAction(action)
            self._style_actions[estilo] = action

        # Marcar o estilo atual
        current_style = QApplication.style().objectName()
        if current_style in self._style_actions:
            self._style_actions[current_style].setChecked(True)

        tema_menu.addSeparator()
        cores_menu = tema_menu.addMenu("Cor de destaque")
        self._color_action_group = QActionGroup(self)
        self._color_action_group.setExclusive(True)
        self._color_actions.clear()

        for chave, (rotulo, _hex) in ThemeManager.color_options().items():
            action = QAction(rotulo, self, checkable=True)
            action.setData(chave)
            action.triggered.connect(self._on_cor_tema_selecionada)
            action.setStatusTip(f"Aplicar destaque {rotulo.lower()}")
            action.setToolTip(f"Cor de destaque {rotulo.lower()}")
            cores_menu.addAction(action)
            self._color_action_group.addAction(action)
            self._color_actions[chave] = action

        self._marcar_tema(self._theme_manager.current_mode)
        self._marcar_cor(self._theme_manager.current_color)

    def _on_tema_selecionado(self) -> None:
        action = self.sender()
        if not isinstance(action, QAction):
            return
        modo = action.data()
        if not isinstance(modo, str):
            return
        if modo != self._theme_manager.current_mode:
            self._theme_manager.apply_theme(modo)

    def _on_estilo_selecionado(self) -> None:
        action = self.sender()
        if not isinstance(action, QAction):
            return
        estilo = action.data()
        if not isinstance(estilo, str):
            return
        current_style = QApplication.style().objectName()
        if estilo != current_style:
            if estilo:  # Se não for vazio
                QApplication.setStyle(estilo)
            # Para estilo padrão (vazio), não faz nada - mantém o atual
            # Forçar repaint de todos os widgets
            for widget in QApplication.allWidgets():
                widget.repaint()

    def _on_tema_atualizado(self, modo: str) -> None:
        self._marcar_tema(modo)

    def _marcar_tema(self, modo: str) -> None:
        for chave, action in self._theme_actions.items():
            with QSignalBlocker(action):
                action.setChecked(chave == modo)

    def _on_cor_tema_selecionada(self) -> None:
        action = self.sender()
        if not isinstance(action, QAction):
            return
        cor = action.data()
        if not isinstance(cor, str):
            return
        if cor != self._theme_manager.current_color:
            self._theme_manager.apply_color(cor)

    def _on_cor_tema_atualizada(self, cor: str) -> None:
        self._marcar_cor(cor)

    def _marcar_cor(self, cor: str) -> None:
        for chave, action in self._color_actions.items():
            with QSignalBlocker(action):
                action.setChecked(chave == cor)
