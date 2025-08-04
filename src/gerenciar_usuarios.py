"""
Módulo para gerenciamento de usuários do sistema.

Este módulo implementa uma interface gráfica para administradores
gerenciarem usuários, incluindo reset de senhas, exclusão de usuários
e alteração de senhas próprias.
"""

from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

from utils import usuario


class GerenciarUsuariosDialog(QDialog):
    """Dialog para gerenciamento de usuários do sistema."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gerenciar Usuários")
        self.setFixedSize(500, 400)
        self.setModal(True)

        self.init_ui()
        self.carregar_usuarios()

        # Inicializar atributos
        self.frame_busca = None
        self.entry_busca = None
        self.botoes_layout = None
        self.btn_resetar_senha = None
        self.btn_excluir = None
        self.btn_alterar_senha = None

    def init_ui(self):
        """Inicializa a interface do usuário."""
        layout = QVBoxLayout()

        # Frame de busca
        self.criar_frame_busca()
        layout.addWidget(self.frame_busca)

        # Lista de usuários
        self.tree_usuarios = QTreeWidget()
        self.tree_usuarios.setHeaderLabels(["ID", "Nome", "Tipo"])
        self.tree_usuarios.setColumnHidden(0, True)  # Esconder coluna ID
        self.tree_usuarios.setColumnWidth(1, 200)
        self.tree_usuarios.setColumnWidth(2, 100)
        layout.addWidget(self.tree_usuarios)

        # Botões de ação
        self.criar_botoes_acao()
        layout.addLayout(self.botoes_layout)

        self.setLayout(layout)

    def criar_frame_busca(self):
        """Cria o frame de busca e filtros de usuários."""
        self.frame_busca = QGroupBox("Filtrar Usuários")
        busca_layout = QGridLayout()

        busca_layout.addWidget(QLabel("Nome:"), 0, 0)

        self.entry_busca = QLineEdit()
        self.entry_busca.textChanged.connect(self.filtrar_usuarios)
        busca_layout.addWidget(self.entry_busca, 0, 1)

        btn_limpar = QPushButton("Limpar")
        btn_limpar.clicked.connect(self.limpar_busca)
        busca_layout.addWidget(btn_limpar, 0, 2)

        self.frame_busca.setLayout(busca_layout)

    def criar_botoes_acao(self):
        """Cria os botões de ação para gerenciamento de usuários."""
        self.botoes_layout = QHBoxLayout()

        self.btn_resetar_senha = QPushButton("Resetar Senha")
        self.btn_resetar_senha.setStyleSheet("background-color: #FFA500;")
        self.btn_resetar_senha.clicked.connect(self.resetar_senha)

        self.btn_excluir = QPushButton("Excluir Usuário")
        self.btn_excluir.setStyleSheet("background-color: #FF4444;")
        self.btn_excluir.clicked.connect(self.excluir_usuario)

        self.btn_alterar_senha = QPushButton("Alterar Minha Senha")
        self.btn_alterar_senha.setStyleSheet("background-color: #4CAF50;")
        self.btn_alterar_senha.clicked.connect(self.alterar_minha_senha)

        self.botoes_layout.addWidget(self.btn_resetar_senha)
        self.botoes_layout.addWidget(self.btn_excluir)
        self.botoes_layout.addWidget(self.btn_alterar_senha)

    def carregar_usuarios(self):
        """Carrega e exibe a lista de usuários na interface."""
        self.tree_usuarios.clear()
        usuarios_lista = usuario.listar_usuarios()

        for user_data in usuarios_lista:
            user_id, nome, admin = user_data
            tipo = "Administrador" if admin else "Usuário"

            item = QTreeWidgetItem([str(user_id), nome, tipo])
            self.tree_usuarios.addTopLevelItem(item)

    def filtrar_usuarios(self):
        """Filtra os usuários exibidos baseado no texto de busca."""
        filtro = self.entry_busca.text().lower()

        for i in range(self.tree_usuarios.topLevelItemCount()):
            item = self.tree_usuarios.topLevelItem(i)
            nome = item.text(1).lower()

            # Mostrar/esconder item baseado no filtro
            item.setHidden(filtro not in nome)

    def limpar_busca(self):
        """Limpa o campo de busca de usuários."""
        self.entry_busca.clear()

    def obter_usuario_selecionado(self):
        """Retorna o ID e nome do usuário selecionado."""
        selected_items = self.tree_usuarios.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Seleção", "Selecione um usuário.")
            return None, None

        item = selected_items[0]
        user_id = int(item.text(0))
        nome = item.text(1)

        return user_id, nome

    def resetar_senha(self):
        """Reseta a senha do usuário selecionado para padrão."""
        user_id, nome = self.obter_usuario_selecionado()
        if user_id is None:
            return

        resposta = QMessageBox.question(
            self,
            "Confirmar Reset",
            f"Resetar a senha do usuário '{nome}'?\nA senha será alterada para 'nova_senha'.",
            QMessageBox.Yes | QMessageBox.No,
        )

        if resposta == QMessageBox.Yes:
            resultado = usuario.resetar_senha_usuario(user_id)

            if "Sucesso" in resultado:
                QMessageBox.information(
                    self,
                    "Sucesso",
                    f"Senha do usuário '{nome}' foi resetada.\n"
                    "Nova senha temporária: 'nova_senha'\n"
                    "O usuário deverá alterar a senha no próximo login.",
                )
            else:
                QMessageBox.warning(self, "Erro", resultado)

    def excluir_usuario(self):
        """Exclui o usuário selecionado do sistema."""
        user_id, nome = self.obter_usuario_selecionado()
        if user_id is None:
            return

        resposta = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o usuário '{nome}'?\nEsta ação não pode ser desfeita.",
            QMessageBox.Yes | QMessageBox.No,
        )

        if resposta == QMessageBox.Yes:
            resultado = usuario.excluir_usuario_por_id(user_id)

            if "Sucesso" in resultado:
                QMessageBox.information(self, "Sucesso", resultado)
                self.carregar_usuarios()  # Recarregar lista
            else:
                QMessageBox.warning(self, "Erro", resultado)

    def alterar_minha_senha(self):
        """Permite ao usuário logado alterar sua própria senha."""
        # Pegar o usuário logado da janela principal (parent)
        main_window = self.parent()

        if not main_window or not hasattr(main_window, "usuario_logado"):
            QMessageBox.warning(
                self, "Erro", "Não foi possível identificar o usuário logado."
            )
            return

        usuario_logado = main_window.usuario_logado

        # Solicitar senha atual
        senha_atual, ok = QInputDialog.getText(
            self, "Senha Atual", "Digite sua senha atual:", QLineEdit.Password
        )

        if not ok or not senha_atual.strip():
            return

        # Solicitar nova senha
        nova_senha, ok = QInputDialog.getText(
            self, "Nova Senha", "Digite a nova senha:", QLineEdit.Password
        )

        if not ok or not nova_senha.strip():
            return

        # Confirmar nova senha
        confirmar_senha, ok = QInputDialog.getText(
            self, "Confirmar Senha", "Confirme a nova senha:", QLineEdit.Password
        )

        if not ok or nova_senha != confirmar_senha:
            QMessageBox.warning(self, "Erro", "As senhas não coincidem.")
            return

        # Alterar senha
        resultado = usuario.alterar_senha_usuario(
            usuario_logado, senha_atual, nova_senha
        )

        if "Sucesso" in resultado:
            QMessageBox.information(
                self, "Sucesso", "Senha alterada com sucesso!")
        else:
            QMessageBox.warning(self, "Erro", resultado)
