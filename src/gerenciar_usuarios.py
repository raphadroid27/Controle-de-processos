"""
Módulo para gerenciamento de usuários do sistema.

Este módulo implementa uma interface gráfica para administradores
gerenciarem usuários, incluindo reset de senhas, exclusão de
usuários, alteração de senhas próprias e controle de sessões ativas.
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
from utils import session_manager
from utils.ui_config import aplicar_estilo_botao


class GerenciarUsuariosDialog(QDialog):
    """Dialog para gerenciamento de usuários e sessões do sistema."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gerenciar Usuários e Sessões")
        self.setFixedSize(600, 400)
        self.setModal(True)

        self.init_ui()
        self.carregar_usuarios()
        self.carregar_sessoes()

    def init_ui(self):
        """Inicializa a interface do usuário."""
        layout = QVBoxLayout()

        # Frame de busca
        self.criar_frame_busca()
        layout.addWidget(self.frame_busca)

        # Layout horizontal para dividir usuários e sessões
        main_layout = QHBoxLayout()

        # Seção de usuários
        usuarios_layout = QVBoxLayout()
        usuarios_layout.addWidget(QLabel("Usuários:"))

        self.tree_usuarios = QTreeWidget()
        self.tree_usuarios.setHeaderLabels(["ID", "Nome", "Tipo"])
        self.tree_usuarios.setColumnHidden(0, True)  # Esconder coluna ID
        self.tree_usuarios.setColumnWidth(1, 150)
        self.tree_usuarios.setColumnWidth(2, 80)
        usuarios_layout.addWidget(self.tree_usuarios)

        # Botões de ação para usuários
        self.criar_botoes_acao()
        usuarios_layout.addLayout(self.botoes_layout)

        main_layout.addLayout(usuarios_layout)

        # Seção de sessões ativas
        sessoes_layout = QVBoxLayout()
        sessoes_layout.addWidget(QLabel("Sessões Ativas:"))

        self.tree_sessoes = QTreeWidget()
        self.tree_sessoes.setHeaderLabels(
            ["Usuário", "Computador", "Última Atividade"])
        self.tree_sessoes.setColumnWidth(0, 80)
        self.tree_sessoes.setColumnWidth(1, 80)
        self.tree_sessoes.setColumnWidth(2, 80)
        sessoes_layout.addWidget(self.tree_sessoes)

        # Botões de ação para sessões
        self.criar_botoes_sessoes()
        sessoes_layout.addLayout(self.botoes_sessoes_layout)

        main_layout.addLayout(sessoes_layout)

        layout.addLayout(main_layout)

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
        # Aplicar estilo cinza padrão
        aplicar_estilo_botao(btn_limpar, "cinza")
        busca_layout.addWidget(btn_limpar, 0, 2)

        self.frame_busca.setLayout(busca_layout)

    def criar_botoes_acao(self):
        """Cria os botões de ação para gerenciamento de usuários."""
        self.botoes_layout = QHBoxLayout()

        self.btn_resetar_senha = QPushButton("Resetar Senha")
        self.btn_resetar_senha.clicked.connect(self.resetar_senha)
        aplicar_estilo_botao(self.btn_resetar_senha, "laranja", 80)

        self.btn_excluir = QPushButton("Excluir Usuário")
        self.btn_excluir.clicked.connect(self.excluir_usuario)
        aplicar_estilo_botao(self.btn_excluir, "vermelho", 80)

        self.btn_alterar_senha = QPushButton("Alterar Minha Senha")
        self.btn_alterar_senha.clicked.connect(self.alterar_senha)
        aplicar_estilo_botao(self.btn_alterar_senha, "azul", 80)

        self.botoes_layout.addWidget(self.btn_resetar_senha)
        self.botoes_layout.addWidget(self.btn_excluir)
        self.botoes_layout.addWidget(self.btn_alterar_senha)

    def criar_botoes_sessoes(self):
        """Cria os botões de ação para gerenciamento de sessões."""
        self.botoes_sessoes_layout = QHBoxLayout()

        self.btn_atualizar_sessoes = QPushButton("Atualizar")
        self.btn_atualizar_sessoes.clicked.connect(self.carregar_sessoes)
        aplicar_estilo_botao(self.btn_atualizar_sessoes, "azul", 80)

        self.btn_shutdown_sistema = QPushButton("Shutdown Sistema")
        self.btn_shutdown_sistema.clicked.connect(self.shutdown_sistema)
        aplicar_estilo_botao(self.btn_shutdown_sistema, "roxo", 80)

        self.botoes_sessoes_layout.addWidget(self.btn_atualizar_sessoes)
        self.botoes_sessoes_layout.addWidget(self.btn_shutdown_sistema)

    def carregar_usuarios(self):
        """Carrega e exibe os usuários do sistema."""
        self.tree_usuarios.clear()

        usuarios_list = usuario.listar_usuarios()

        for user in usuarios_list:
            item = QTreeWidgetItem([
                str(user[0]),  # ID
                user[1],       # Nome
                "Admin" if user[2] else "Usuário"  # Tipo
            ])
            self.tree_usuarios.addTopLevelItem(item)

    def carregar_sessoes(self):
        """Carrega e exibe as sessões ativas."""
        self.tree_sessoes.clear()

        sessoes = session_manager.obter_sessoes_ativas()

        for sessao in sessoes:
            item = QTreeWidgetItem([
                sessao['usuario'],
                sessao['hostname'],
                sessao['last_updated']
            ])
            # Armazenar o session_id no item para uso posterior
            # Qt.UserRole = 0x0100
            item.setData(0, 0x0100, sessao['session_id'])
            self.tree_sessoes.addTopLevelItem(item)

    def filtrar_usuarios(self):
        """Filtra os usuários baseado no texto de busca."""
        filtro = self.entry_busca.text().lower()

        for i in range(self.tree_usuarios.topLevelItemCount()):
            item = self.tree_usuarios.topLevelItem(i)
            if item:
                nome = item.text(1).lower()
                # Mostrar/esconder baseado no filtro
                item.setHidden(filtro not in nome)

    def limpar_busca(self):
        """Limpa o campo de busca."""
        self.entry_busca.clear()

    def resetar_senha(self):
        """Reseta a senha do usuário selecionado."""
        item_selecionado = self.tree_usuarios.currentItem()
        if not item_selecionado:
            QMessageBox.warning(
                self, "Erro", "Selecione um usuário para resetar a senha.")
            return

        nome_usuario = item_selecionado.text(1)

        resposta = QMessageBox.question(
            self,
            "Confirmar Reset",
            f"Resetar senha do usuário '{nome_usuario}' para senha padrão?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if resposta == QMessageBox.StandardButton.Yes:
            resultado = usuario.resetar_senha_usuario(nome_usuario)

            if "Sucesso" in resultado:
                QMessageBox.information(self, "Sucesso", resultado)
            else:
                QMessageBox.warning(self, "Erro", resultado)

    def excluir_usuario(self):
        """Exclui o usuário selecionado."""
        item_selecionado = self.tree_usuarios.currentItem()
        if not item_selecionado:
            QMessageBox.warning(
                self, "Erro", "Selecione um usuário para excluir.")
            return

        nome_usuario = item_selecionado.text(1)

        resposta = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o usuário '{nome_usuario}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if resposta == QMessageBox.StandardButton.Yes:
            resultado = usuario.excluir_usuario(nome_usuario)

            if "Sucesso" in resultado:
                QMessageBox.information(self, "Sucesso", resultado)
                self.carregar_usuarios()  # Recarregar lista
            else:
                QMessageBox.warning(self, "Erro", resultado)

    def alterar_senha(self):
        """Permite ao usuário logado alterar sua própria senha."""
        # Obter o usuário logado da janela principal
        main_window = self.parent()
        if not hasattr(main_window, 'usuario_logado'):
            QMessageBox.warning(
                self, "Erro", "Não foi possível identificar o usuário logado."
            )
            return

        usuario_logado = main_window.usuario_logado

        # Solicitar senha atual
        senha_atual, ok = QInputDialog.getText(
            self, "Senha Atual", "Digite sua senha atual:", QLineEdit.EchoMode.Password
        )

        if not ok or not senha_atual.strip():
            return

        # Solicitar nova senha
        nova_senha, ok = QInputDialog.getText(
            self, "Nova Senha", "Digite a nova senha:", QLineEdit.EchoMode.Password
        )

        if not ok or not nova_senha.strip():
            return

        # Confirmar nova senha
        confirmar_senha, ok = QInputDialog.getText(
            self, "Confirmar Senha", "Confirme a nova senha:", QLineEdit.EchoMode.Password
        )

        if not ok or confirmar_senha != nova_senha:
            QMessageBox.warning(self, "Erro", "As senhas não conferem.")
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

    def shutdown_sistema(self):
        """Envia comando de shutdown para todas as instâncias do sistema."""
        resposta = QMessageBox.question(
            self,
            "Shutdown do Sistema",
            "Deseja enviar comando de fechamento para todas as instâncias do sistema?\n\n"
            "Isso irá fechar automaticamente todas as aplicações ativas.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if resposta == QMessageBox.StandardButton.Yes:
            session_manager.definir_comando_sistema("SHUTDOWN")
            QMessageBox.information(
                self,
                "Comando Enviado",
                "Comando de shutdown enviado para todas as instâncias.\n"
                "As aplicações serão fechadas automaticamente."
            )
            self.carregar_sessoes()
