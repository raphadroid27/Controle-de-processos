"""Módulo da janela principal do aplicativo."""

import logging

from PySide6.QtCore import QFileSystemWatcher, QSignalBlocker, QTimer, Signal
from PySide6.QtGui import QAction, QActionGroup, QKeySequence
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QMessageBox

from src.forms.form_sobre import main as mostrar_sobre
from src.gerenciar_usuarios import GerenciarUsuariosDialog
from src.ui.theme_manager import ThemeManager
from src.utils import session_manager
from src.utils.ui_config import aplicar_icone_padrao
from src.widgets.dashboard_dialog import DashboardDialog
from src.widgets.widget import PedidosWidget


def show_timed_message_box(parent, title, message, timeout_ms=10000):
    """Mostra uma caixa de mensagem com timeout automático."""
    msg_box = QMessageBox(
        QMessageBox.Icon.Information,
        title,
        message,
        QMessageBox.StandardButton.Ok,
        parent,
    )

    # Timer para fechar automaticamente
    timer = QTimer(parent)
    timer.timeout.connect(msg_box.accept)
    timer.setSingleShot(True)
    timer.start(timeout_ms)

    # Mostrar diálogo (modal)
    msg_box.exec()

    # Parar timer se ainda rodando
    timer.stop()


def _criar_menu_com_acoes_checkaveis(  # pylint: disable=too-many-positional-arguments
    menu,
    opcoes,
    action_group,
    actions_dict,
    callback,
    status_prefix="Aplicar",
    parent=None,
):
    """Helper para criar menus com ações checkáveis."""
    for rotulo, valor in opcoes:
        action = QAction(rotulo, parent, checkable=True)
        action.setData(valor)
        action.triggered.connect(callback)
        action.setStatusTip(f"{status_prefix} {rotulo.lower()}")
        action.setToolTip(f"{status_prefix} {rotulo.lower()}")
        menu.addAction(action)
        action_group.addAction(action)
        actions_dict[valor] = action


class MainWindow(QMainWindow):
    """Janela principal do aplicativo."""

    logout_requested = Signal()

    def __init__(self, usuario_logado, is_admin):
        """Inicializa a janela principal."""
        super().__init__()
        self.usuario_logado = usuario_logado
        self.is_admin = is_admin
        self._logout_voluntario = False  # Flag para indicar logout voluntário
        self._theme_manager = ThemeManager.instance()
        self._theme_actions: dict[str, QAction] = {}
        self._theme_action_group: QActionGroup | None = None
        self._style_actions: dict[str, QAction] = {}
        self._style_action_group: QActionGroup | None = None
        self._color_actions: dict[str, QAction] = {}
        self._color_action_group: QActionGroup | None = None

        self.setWindowTitle("Controle de Processos")
        self.setMinimumSize(800, 600)

        # Aplicar ícone padrão
        aplicar_icone_padrao(self)

        self.setCentralWidget(PedidosWidget(usuario_logado, is_admin))

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

        # Usar QFileSystemWatcher para monitorar comandos em vez de polling
        self.command_watcher = QFileSystemWatcher(self)
        comando_path = session_manager.get_comando_path()
        # Sempre adicionar o caminho, mesmo que o arquivo não exista ainda
        self.command_watcher.addPath(str(comando_path))
        self.command_watcher.fileChanged.connect(
            self.verificar_comando_sistema)

        # Timer de backup para verificação periódica (fallback)
        self.command_timer = QTimer()
        self.command_timer.timeout.connect(self.verificar_comando_sistema)
        self.command_timer.start(10000)  # Verificar a cada 10 segundos

    def atualizar_heartbeat(self):
        """Atualiza o heartbeat da sessão e verifica se a sessão ainda é válida."""
        try:
            # Verificar se a sessão ainda existe
            sessoes = session_manager.obter_sessoes_ativas()
            sessao_atual_existe = any(
                s["session_id"] == session_manager.SESSION_ID for s in sessoes
            )

            if not sessao_atual_existe:
                # Verificar se foi logout voluntário
                if not self._logout_voluntario:
                    # Sessão foi removida por outro login
                    show_timed_message_box(
                        self,
                        "Sessão Encerrada",
                        "Sua sessão foi encerrada por outro login.\n"
                        "A aplicação será fechada.",
                        5000,
                    )
                    # Agendar o fechamento da aplicação após a mensagem ser exibida
                    QTimer.singleShot(500, QApplication.quit)
                return

            # Atualizar heartbeat se a sessão ainda existe
            session_manager.atualizar_heartbeat_sessao()

        except (OSError, RuntimeError) as e:
            # Em caso de erro, assumir que a sessão não é válida
            logging.error("Erro ao verificar sessão: %s", e)
            QApplication.quit()

    def verificar_comando_sistema(self):
        """Verifica se há comandos do sistema para executar."""
        comando_global = session_manager.obter_comando_sistema()
        if comando_global == "SHUTDOWN":
            show_timed_message_box(
                self,
                "Sistema",
                "O administrador solicitou o fechamento do sistema.\n"
                "A aplicação será encerrada.",
                10000,
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

            atualizar_action = QAction("Atualizar", self)
            atualizar_action.triggered.connect(self.atualizar_tabela)
            atualizar_action.setShortcut(QKeySequence("F5"))
            atualizar_action.setStatusTip(
                "Atualizar a tabela com os registros")
            atualizar_action.setToolTip("Atualizar tabela (F5)")
            admin_menu.addAction(atualizar_action)

        self._criar_menu_tema(menubar)

        ajuda_menu = menubar.addMenu("Ajuda")

        sobre_action = QAction("Sobre", self)
        sobre_action.triggered.connect(self.abrir_sobre)
        sobre_action.setStatusTip("Informações sobre a aplicação")
        sobre_action.setToolTip("Sobre")
        ajuda_menu.addAction(sobre_action)

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
        except (ImportError, AttributeError, RuntimeError) as exc:
            QMessageBox.warning(
                self,
                "Erro",
                f"Não foi possível abrir o dashboard: {exc}",
            )

    def abrir_sobre(self):
        """Abre o diálogo Sobre."""
        try:
            mostrar_sobre(self)
        except (ImportError, AttributeError, RuntimeError) as exc:
            QMessageBox.warning(
                self,
                "Erro",
                f"Não foi possível abrir a janela Sobre: {exc}",
            )

    def atualizar_tabela(self):
        """Atualiza a tabela principal com os registros."""
        widget_central = self.centralWidget()
        if isinstance(widget_central, PedidosWidget):
            widget_central.aplicar_filtro()

    def fazer_logout(self):
        """Faz logout e retorna para a tela de login."""
        resposta = QMessageBox.question(
            self,
            "Logout",
            "Tem certeza que deseja fazer logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if resposta == QMessageBox.StandardButton.Yes:
            self._logout_voluntario = True  # Marcar como logout voluntário
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

        _criar_menu_com_acoes_checkaveis(
            menu=tema_menu,
            opcoes=opcoes,
            action_group=self._theme_action_group,
            actions_dict=self._theme_actions,
            callback=self._on_tema_selecionado,
            status_prefix="Aplicar tema",
            parent=self,
        )

        tema_menu.addSeparator()
        estilo_menu = tema_menu.addMenu("Estilo")
        self._style_action_group = QActionGroup(self)
        self._style_action_group.setExclusive(True)
        self._style_actions.clear()

        estilos_opcoes = [
            ("Fusion", "Fusion"),
            ("Windows", "Windows"),
        ]

        _criar_menu_com_acoes_checkaveis(
            menu=estilo_menu,
            opcoes=estilos_opcoes,
            action_group=self._style_action_group,
            actions_dict=self._style_actions,
            callback=self._on_estilo_selecionado,
            status_prefix="Aplicar estilo",
            parent=self,
        )

        # Marcar o estilo atual
        current_style = self._theme_manager.current_style
        if current_style in self._style_actions:
            self._style_actions[current_style].setChecked(True)

        tema_menu.addSeparator()
        cores_menu = tema_menu.addMenu("Cor de destaque")
        self._color_action_group = QActionGroup(self)
        self._color_action_group.setExclusive(True)
        self._color_actions.clear()

        cores_opcoes = [
            (rotulo, chave)
            for chave, (rotulo, _hex) in ThemeManager.color_options().items()
        ]

        _criar_menu_com_acoes_checkaveis(
            menu=cores_menu,
            opcoes=cores_opcoes,
            action_group=self._color_action_group,
            actions_dict=self._color_actions,
            callback=self._on_cor_tema_selecionada,
            status_prefix="Aplicar destaque",
            parent=self,
        )

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
        if estilo != self._theme_manager.current_style:
            self._theme_manager.apply_style(estilo)

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
