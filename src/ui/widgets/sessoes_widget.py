"""Componentes de gerenciamento de sessões ativas."""

from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.domain import session_service
from src.infrastructure.ipc import manager as ipc_manager
from src.ui.styles import aplicar_estilo_botao, aplicar_icone_padrao


class GerenciarSessoesWidget(QWidget):
    """Widget reutilizável para visualizar e controlar sessões ativas."""

    def __init__(self, parent=None):
        """Inicializa o widget de sessões."""
        super().__init__(parent)

        self.tree_sessoes = QTreeWidget()
        self.btn_atualizar_sessoes = QPushButton("Atualizar")
        self.btn_encerrar_sessao = QPushButton("Encerrar Sessão")
        self.btn_limpar_inativas = QPushButton("Limpar Inativas")
        self.btn_shutdown_sistema = QPushButton("Shutdown Sistema")

        self._init_ui()
        self.carregar_sessoes()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Sessões Ativas:"))

        self.tree_sessoes.setHeaderLabels(
            ["Usuário", "Aplicação", "Computador", "Última Atividade"]
        )
        self.tree_sessoes.setColumnWidth(0, 120)
        self.tree_sessoes.setColumnWidth(1, 160)
        self.tree_sessoes.setColumnWidth(2, 120)
        self.tree_sessoes.setColumnWidth(3, 160)
        self.tree_sessoes.setToolTip(
            "Visualize as sessões ativas e selecione uma para ações disponíveis."
        )
        layout.addWidget(self.tree_sessoes)

        botoes_layout = QHBoxLayout()
        botoes_layout.addStretch()

        self.btn_atualizar_sessoes.clicked.connect(self.carregar_sessoes)
        aplicar_estilo_botao(self.btn_atualizar_sessoes, "azul", 90)
        self.btn_atualizar_sessoes.setToolTip("Atualizar a lista de sessões (F5)")
        self.btn_atualizar_sessoes.setShortcut(QKeySequence("F5"))

        self.btn_encerrar_sessao.clicked.connect(self.encerrar_sessao_selecionada)
        aplicar_estilo_botao(self.btn_encerrar_sessao, "vermelho", 130)
        self.btn_encerrar_sessao.setToolTip("Encerrar a sessão selecionada (Del)")
        self.btn_encerrar_sessao.setShortcut(QKeySequence("Del"))

        self.btn_limpar_inativas.clicked.connect(self.limpar_sessoes_inativas)
        aplicar_estilo_botao(self.btn_limpar_inativas, "laranja", 120)
        self.btn_limpar_inativas.setToolTip(
            "Remover sessões inativas (sem heartbeat há mais de 2 minutos)"
        )

        self.btn_shutdown_sistema.clicked.connect(self.shutdown_sistema)
        aplicar_estilo_botao(self.btn_shutdown_sistema, "roxo", 140)
        self.btn_shutdown_sistema.setToolTip(
            "Enviar comando de desligamento para todas as instâncias (Ctrl+Shift+Q)"
        )
        self.btn_shutdown_sistema.setShortcut(QKeySequence("Ctrl+Shift+Q"))

        botoes_layout.addWidget(self.btn_atualizar_sessoes)
        botoes_layout.addWidget(self.btn_encerrar_sessao)
        botoes_layout.addWidget(self.btn_limpar_inativas)
        botoes_layout.addWidget(self.btn_shutdown_sistema)

        layout.addLayout(botoes_layout)

    def carregar_sessoes(self) -> None:
        """Carrega e exibe as sessões ativas."""
        self.tree_sessoes.clear()
        sessoes = session_service.obter_sessoes_ativas()

        for sessao in sessoes:
            # Determinar nome da aplicação baseado no tipo de sessão
            session_type = sessao.get("session_type", "app")
            if session_type == "admin_tool":
                app_name = "Ferramenta Administrativa"
            else:
                app_name = "Controle de Pedidos"

            item = QTreeWidgetItem(
                [
                    sessao["usuario"],
                    app_name,
                    sessao["hostname"],
                    sessao["last_updated"],
                ]
            )
            item.setData(0, 0x0100, sessao["session_id"])
            self.tree_sessoes.addTopLevelItem(item)

    def encerrar_sessao_selecionada(self) -> None:
        """Encerra a sessão selecionada na árvore."""
        item_selecionado = self.tree_sessoes.currentItem()
        if not item_selecionado:
            QMessageBox.warning(
                self, "Aviso", "Selecione uma sessão na lista para encerrar."
            )
            return

        session_id = item_selecionado.data(0, 0x0100)
        usuario = item_selecionado.text(0)
        app_name = item_selecionado.text(1)
        hostname = item_selecionado.text(2)

        # Não permitir encerrar a própria sessão
        if session_id == session_service.SESSION_ID:
            QMessageBox.warning(
                self,
                "Aviso",
                "Você não pode encerrar sua própria sessão.\n"
                "Use 'Logout' ou 'Sair' no menu Arquivo.",
            )
            return

        resposta = QMessageBox.question(
            self,
            "Encerrar Sessão",
            (
                f"Deseja encerrar a sessão de '{usuario}' em '{hostname}'?\n"
                f"Aplicação: {app_name}\n\n"
                "A aplicação será fechada automaticamente naquele computador."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if resposta == QMessageBox.StandardButton.Yes:
            session_service.definir_comando_encerrar_sessao(session_id)
            QMessageBox.information(
                self,
                "Comando Enviado",
                f"Comando de encerramento enviado para a sessão de '{usuario}'.\n"
                "A sessão será fechada automaticamente em alguns segundos.",
            )
            self.carregar_sessoes()

    def limpar_sessoes_inativas(self) -> None:
        """Remove manualmente sessões inativas (sem heartbeat)."""
        resposta = QMessageBox.question(
            self,
            "Limpar Sessões Inativas",
            (
                "Deseja remover sessões não atualizadas há 2 minutos?\n\n"
                "Isso remove sessões de aplicações que podem ter "
                "crashado ou sido fechadas incorretamente."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if resposta == QMessageBox.StandardButton.Yes:
            # Contar sessões antes
            sessoes_antes = len(session_service.obter_sessoes_ativas())

            # Limpar inativas
            ipc_manager.cleanup_inactive_sessions(timeout_seconds=120)

            # Contar sessões depois
            sessoes_depois = len(session_service.obter_sessoes_ativas())
            removidas = sessoes_antes - sessoes_depois

            if removidas > 0:
                QMessageBox.information(
                    self,
                    "Limpeza Concluída",
                    f"{removidas} sessão(ões) inativa(s) removida(s).",
                )
            else:
                QMessageBox.information(
                    self,
                    "Limpeza Concluída",
                    "Nenhuma sessão inativa encontrada.",
                )

            self.carregar_sessoes()

    def shutdown_sistema(self) -> None:
        """Envia comando de shutdown para todas as instâncias do sistema."""
        resposta = QMessageBox.question(
            self,
            "Shutdown do Sistema",
            (
                "Deseja enviar comando de fechamento para todas as instâncias do "
                "sistema?\n\n"
                "Isso irá fechar automaticamente todas as aplicações ativas."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if resposta == QMessageBox.StandardButton.Yes:
            session_service.definir_comando_sistema("SHUTDOWN")
            QMessageBox.information(
                self,
                "Comando Enviado",
                "Comando de shutdown enviado para todas as instâncias.\n"
                "As aplicações serão fechadas automaticamente.",
            )
            self.carregar_sessoes()


class GerenciarSessoesDialog(QDialog):
    """Diálogo independente que encapsula o widget de sessões."""

    def __init__(self, parent=None, *, modal: bool = True):
        """Inicializa o diálogo de sessões."""
        super().__init__(parent)

        self.setWindowTitle("Sessões Ativas")
        self.setFixedSize(600, 400)
        self.setModal(modal)

        aplicar_icone_padrao(self)

        self._widget = GerenciarSessoesWidget(self)

        layout = QVBoxLayout()
        layout.addWidget(self._widget)
        self.setLayout(layout)

    def carregar_sessoes(self) -> None:
        """Atualiza o conteúdo do diálogo externo."""
        self._widget.carregar_sessoes()
