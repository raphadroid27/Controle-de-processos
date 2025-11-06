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
from src.ui.styles import aplicar_estilo_botao, aplicar_icone_padrao


class GerenciarSessoesWidget(QWidget):
    """Widget reutilizável para visualizar e controlar sessões ativas."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.tree_sessoes = QTreeWidget()
        self.btn_atualizar_sessoes = QPushButton("Atualizar")
        self.btn_shutdown_sistema = QPushButton("Shutdown Sistema")

        self._init_ui()
        self.carregar_sessoes()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Sessões Ativas:"))

        self.tree_sessoes.setHeaderLabels(
            ["Usuário", "Computador", "Última Atividade"]
        )
        self.tree_sessoes.setColumnWidth(0, 140)
        self.tree_sessoes.setColumnWidth(1, 140)
        self.tree_sessoes.setColumnWidth(2, 180)
        self.tree_sessoes.setToolTip(
            "Visualize as sessões ativas e selecione uma para ações disponíveis."
        )
        layout.addWidget(self.tree_sessoes)

        botoes_layout = QHBoxLayout()
        botoes_layout.addStretch()

        self.btn_atualizar_sessoes.clicked.connect(self.carregar_sessoes)
        aplicar_estilo_botao(self.btn_atualizar_sessoes, "azul", 90)
        self.btn_atualizar_sessoes.setToolTip(
            "Atualizar a lista de sessões (F5)")
        self.btn_atualizar_sessoes.setShortcut(QKeySequence("F5"))

        self.btn_shutdown_sistema.clicked.connect(self.shutdown_sistema)
        aplicar_estilo_botao(self.btn_shutdown_sistema, "roxo", 140)
        self.btn_shutdown_sistema.setToolTip(
            "Enviar comando de desligamento para todas as instâncias (Ctrl+Shift+Q)"
        )
        self.btn_shutdown_sistema.setShortcut(QKeySequence("Ctrl+Shift+Q"))

        botoes_layout.addWidget(self.btn_atualizar_sessoes)
        botoes_layout.addWidget(self.btn_shutdown_sistema)

        layout.addLayout(botoes_layout)

    def carregar_sessoes(self) -> None:
        """Carrega e exibe as sessões ativas."""
        self.tree_sessoes.clear()
        sessoes = session_service.obter_sessoes_ativas()

        for sessao in sessoes:
            item = QTreeWidgetItem(
                [sessao["usuario"], sessao["hostname"], sessao["last_updated"]]
            )
            item.setData(0, 0x0100, sessao["session_id"])
            self.tree_sessoes.addTopLevelItem(item)

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
