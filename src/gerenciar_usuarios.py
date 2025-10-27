"""
Módulo para gerenciamento de usuários do sistema.

Este módulo implementa uma interface gráfica para administradores
gerenciarem usuários, incluindo reset de senhas, exclusão de
usuários, alteração de senhas próprias e controle de sessões ativas.
"""

from datetime import datetime, timezone

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (QDialog, QGridLayout, QGroupBox, QHBoxLayout,
                               QInputDialog, QLabel, QLineEdit, QMessageBox,
                               QPushButton, QTabWidget, QTreeWidget,
                               QTreeWidgetItem, QVBoxLayout, QWidget)

from src.utils import session_manager, usuario
from src.utils.ui_config import aplicar_estilo_botao, aplicar_icone_padrao


class GerenciarUsuariosDialog(QDialog):
    """Dialog para gerenciamento de usuários e sessões do sistema."""

    def __init__(self, parent=None):
        """Inicializa o diálogo de gerenciamento de usuários."""
        super().__init__(parent)
        self.setWindowTitle("Gerenciar Usuários e Sessões")
        self.setFixedSize(600, 400)
        self.setModal(True)

        # Aplicar ícone padrão
        aplicar_icone_padrao(self)

        # Atributos inicializados para satisfazer Pylint
        # (definidos em métodos auxiliares)
        self.frame_busca = None
        self.entry_busca = None
        self.botoes_layout = None
        self.btn_resetar_senha = None
        self.btn_arquivar = None
        self.btn_restaurar = None
        self.btn_excluir = None
        self.btn_alterar_senha = None
        self.botoes_sessoes_layout = None
        self.btn_atualizar_sessoes = None
        self.btn_shutdown_sistema = None
        self.tree_usuarios = None
        self.tree_sessoes = None

        self.init_ui()
        self.carregar_usuarios()
        self.carregar_sessoes()

    def init_ui(self):
        """Inicializa a interface do usuário com abas distintas."""
        layout = QVBoxLayout()

        self.tabs = QTabWidget()
        self.tabs.addTab(self._criar_tab_usuarios(), "Usuários")
        self.tabs.addTab(self._criar_tab_sessoes(), "Sessões")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def _criar_tab_usuarios(self) -> QWidget:
        """Monta a aba de gerenciamento de usuários."""
        container = QWidget()
        tab_layout = QVBoxLayout(container)

        self.criar_frame_busca()
        tab_layout.addWidget(self.frame_busca)

        self.tree_usuarios = QTreeWidget()
        self.tree_usuarios.setHeaderLabels(["ID", "Nome", "Tipo", "Status"])
        self.tree_usuarios.setColumnHidden(0, True)  # Esconder coluna ID
        self.tree_usuarios.setColumnWidth(1, 150)
        self.tree_usuarios.setColumnWidth(2, 80)
        self.tree_usuarios.setColumnWidth(3, 200)
        self.tree_usuarios.setToolTip(
            "Selecione um usuário para gerenciar ações disponíveis."
        )
        tab_layout.addWidget(self.tree_usuarios)
        self.tree_usuarios.currentItemChanged.connect(self.atualizar_estado_botoes)

        self.criar_botoes_acao()
        tab_layout.addLayout(self.botoes_layout)

        return container

    def _criar_tab_sessoes(self) -> QWidget:
        """Monta a aba de sessões ativas."""
        container = QWidget()
        tab_layout = QVBoxLayout(container)
        tab_layout.addWidget(QLabel("Sessões Ativas:"))

        self.tree_sessoes = QTreeWidget()
        self.tree_sessoes.setHeaderLabels(["Usuário", "Computador", "Última Atividade"])
        self.tree_sessoes.setColumnWidth(0, 120)
        self.tree_sessoes.setColumnWidth(1, 120)
        self.tree_sessoes.setColumnWidth(2, 160)
        self.tree_sessoes.setToolTip(
            "Visualize as sessões ativas e selecione uma para ações disponíveis."
        )
        tab_layout.addWidget(self.tree_sessoes)

        self.criar_botoes_sessoes()
        tab_layout.addLayout(self.botoes_sessoes_layout)

        return container

    def criar_frame_busca(self):
        """Cria o frame de busca e filtros de usuários."""
        self.frame_busca = QGroupBox("Filtrar Usuários")
        busca_layout = QGridLayout()

        busca_layout.addWidget(QLabel("Nome:"), 0, 0)

        self.entry_busca = QLineEdit()
        self.entry_busca.setPlaceholderText("Digite parte do nome ou status")
        self.entry_busca.setToolTip(
            """Digite parte do nome ou do status (ex.: ativo, arquivado)
para filtrar a lista.
Use as teclas de seta para navegar pelos resultados."""
        )
        self.entry_busca.textChanged.connect(self.filtrar_usuarios)
        busca_layout.addWidget(self.entry_busca, 0, 1)

        btn_limpar = QPushButton("Limpar")
        btn_limpar.clicked.connect(self.limpar_busca)
        btn_limpar.setToolTip(
            "Limpa o campo de busca e exibe novamente todos os usuários."
        )
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
        self.btn_resetar_senha.setToolTip(
            "Resetar a senha do usuário selecionado (Ctrl+Shift+R)"
        )
        self.btn_resetar_senha.setShortcut(QKeySequence("Ctrl+Shift+R"))

        self.btn_arquivar = QPushButton("Arquivar")
        self.btn_arquivar.clicked.connect(self.arquivar_usuario)
        aplicar_estilo_botao(self.btn_arquivar, "roxo", 80)
        self.btn_arquivar.setToolTip(
            "Arquivar usuário e revogar acesso imediato (Ctrl+Shift+A)"
        )
        self.btn_arquivar.setShortcut(QKeySequence("Ctrl+Shift+A"))

        self.btn_restaurar = QPushButton("Restaurar")
        self.btn_restaurar.clicked.connect(self.restaurar_usuario)
        aplicar_estilo_botao(self.btn_restaurar, "verde", 80)
        self.btn_restaurar.setToolTip("Restaurar usuário arquivado (Ctrl+Shift+T)")
        self.btn_restaurar.setShortcut(QKeySequence("Ctrl+Shift+T"))

        self.btn_excluir = QPushButton("Excluir Usuário")
        self.btn_excluir.clicked.connect(self.excluir_usuario)
        aplicar_estilo_botao(self.btn_excluir, "vermelho", 80)
        self.btn_excluir.setToolTip(
            "Excluir definitivamente um usuário arquivado (Ctrl+Shift+Del)"
        )
        self.btn_excluir.setShortcut(QKeySequence("Ctrl+Shift+Del"))

        self.btn_alterar_senha = QPushButton("Alterar Minha Senha")
        self.btn_alterar_senha.clicked.connect(self.alterar_senha)
        aplicar_estilo_botao(self.btn_alterar_senha, "azul", 80)
        self.btn_alterar_senha.setToolTip(
            "Alterar a senha do usuário logado (Ctrl+Alt+S)"
        )
        self.btn_alterar_senha.setShortcut(QKeySequence("Ctrl+Alt+S"))

        self.botoes_layout.addWidget(self.btn_resetar_senha)
        self.botoes_layout.addWidget(self.btn_arquivar)
        self.botoes_layout.addWidget(self.btn_restaurar)
        self.botoes_layout.addWidget(self.btn_excluir)
        self.botoes_layout.addWidget(self.btn_alterar_senha)

    def criar_botoes_sessoes(self):
        """Cria os botões de ação para gerenciamento de sessões."""
        self.botoes_sessoes_layout = QHBoxLayout()

        self.btn_atualizar_sessoes = QPushButton("Atualizar")
        self.btn_atualizar_sessoes.clicked.connect(self.carregar_sessoes)
        aplicar_estilo_botao(self.btn_atualizar_sessoes, "azul", 80)
        self.btn_atualizar_sessoes.setToolTip("Atualizar a lista de sessões (F5)")
        self.btn_atualizar_sessoes.setShortcut(QKeySequence("F5"))

        self.btn_shutdown_sistema = QPushButton("Shutdown Sistema")
        self.btn_shutdown_sistema.clicked.connect(self.shutdown_sistema)
        aplicar_estilo_botao(self.btn_shutdown_sistema, "roxo", 80)
        self.btn_shutdown_sistema.setToolTip(
            "Enviar comando de desligamento para todas as instâncias (Ctrl+Shift+Q)"
        )
        self.btn_shutdown_sistema.setShortcut(QKeySequence("Ctrl+Shift+Q"))

        self.botoes_sessoes_layout.addWidget(self.btn_atualizar_sessoes)
        self.botoes_sessoes_layout.addWidget(self.btn_shutdown_sistema)

    def carregar_usuarios(self):
        """Carrega e exibe os usuários do sistema."""
        self.tree_usuarios.clear()

        usuarios_list = usuario.listar_usuarios()

        for user in usuarios_list:
            arquivado_em = user.get("arquivado_em")
            if isinstance(arquivado_em, str):
                try:
                    arquivado_em = datetime.fromisoformat(arquivado_em)
                except ValueError:
                    arquivado_em = None

            if user.get("ativo", False):
                status = "Ativo"
            else:
                if isinstance(arquivado_em, datetime):
                    # Garantir conversão correta para local
                    if arquivado_em.tzinfo is None:
                        arquivado_em = arquivado_em.replace(tzinfo=timezone.utc)
                    arquivado_em_local = arquivado_em.astimezone()
                    status = (
                        f"Arquivado em {arquivado_em_local.strftime('%d/%m/%Y %H:%M')}"
                    )
                else:
                    status = "Arquivado"

            item = QTreeWidgetItem(
                [
                    str(user["id"]),
                    user["nome"],
                    "Admin" if user.get("admin") else "Usuário",
                    status,
                ]
            )
            item.setData(0, Qt.ItemDataRole.UserRole, user)
            self.tree_usuarios.addTopLevelItem(item)

        if self.tree_usuarios.topLevelItemCount() > 0:
            self.tree_usuarios.setCurrentItem(self.tree_usuarios.topLevelItem(0))
        else:
            self.atualizar_estado_botoes(None, None)

    def carregar_sessoes(self):
        """Carrega e exibe as sessões ativas."""
        self.tree_sessoes.clear()

        sessoes = session_manager.obter_sessoes_ativas()

        for sessao in sessoes:
            item = QTreeWidgetItem(
                [sessao["usuario"], sessao["hostname"], sessao["last_updated"]]
            )
            # Armazenar o session_id no item para uso posterior
            # Qt.UserRole = 0x0100
            item.setData(0, 0x0100, sessao["session_id"])
            self.tree_sessoes.addTopLevelItem(item)

    def atualizar_estado_botoes(self, item_atual, _item_anterior):
        """Habilita ou desabilita botões conforme o usuário selecionado."""
        dados = None
        if item_atual is not None:
            dados = item_atual.data(0, Qt.ItemDataRole.UserRole)

        ativo = bool(dados.get("ativo")) if isinstance(dados, dict) else False
        admin = bool(dados.get("admin")) if isinstance(dados, dict) else False
        possui_usuario = isinstance(dados, dict)

        if self.btn_resetar_senha is not None:
            self.btn_resetar_senha.setEnabled(possui_usuario and ativo)
        if self.btn_arquivar is not None:
            self.btn_arquivar.setEnabled(possui_usuario and ativo and not admin)
        if self.btn_restaurar is not None:
            self.btn_restaurar.setEnabled(possui_usuario and not ativo)
        if self.btn_excluir is not None:
            self.btn_excluir.setEnabled(possui_usuario and not admin and not ativo)

    def filtrar_usuarios(self):
        """Filtra os usuários baseado no texto de busca."""
        filtro = self.entry_busca.text().lower()

        for i in range(self.tree_usuarios.topLevelItemCount()):
            item = self.tree_usuarios.topLevelItem(i)
            if item:
                nome = item.text(1).lower()
                status = item.text(3).lower() if item.columnCount() > 3 else ""
                # Mostrar/esconder baseado no filtro
                item.setHidden(filtro not in nome and filtro not in status)

    def limpar_busca(self):
        """Limpa o campo de busca."""
        self.entry_busca.clear()

    def resetar_senha(self):
        """Reseta a senha do usuário selecionado."""
        item_selecionado = self.tree_usuarios.currentItem()
        if not item_selecionado:
            QMessageBox.warning(
                self, "Erro", "Selecione um usuário para resetar a senha."
            )
            return

        dados_usuario = item_selecionado.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(dados_usuario, dict):
            QMessageBox.warning(self, "Erro", "Não foi possível identificar o usuário.")
            return

        if not dados_usuario.get("ativo", False):
            QMessageBox.warning(
                self,
                "Usuário arquivado",
                "Restaure o usuário antes de resetar a senha.",
            )
            return

        nome_usuario = dados_usuario["nome"]

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
            QMessageBox.warning(self, "Erro", "Selecione um usuário para excluir.")
            return

        dados_usuario = item_selecionado.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(dados_usuario, dict):
            QMessageBox.warning(self, "Erro", "Não foi possível identificar o usuário.")
            return

        nome_usuario = dados_usuario["nome"]

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
                return
            QMessageBox.warning(self, "Erro", resultado)
            self.atualizar_estado_botoes(item_selecionado, None)

    def arquivar_usuario(self):
        """Arquiva o usuário selecionado, mantendo seus dados."""
        item_selecionado = self.tree_usuarios.currentItem()
        if not item_selecionado:
            QMessageBox.warning(self, "Erro", "Selecione um usuário para arquivar.")
            return

        dados_usuario = item_selecionado.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(dados_usuario, dict):
            QMessageBox.warning(self, "Erro", "Não foi possível identificar o usuário.")
            return

        if dados_usuario.get("admin"):
            QMessageBox.warning(
                self,
                "Ação não permitida",
                "Não é possível arquivar um usuário administrador.",
            )
            return

        if not dados_usuario.get("ativo", False):
            QMessageBox.information(
                self,
                "Usuário arquivado",
                "O usuário selecionado já está arquivado.",
            )
            return

        nome_usuario = dados_usuario["nome"]

        resposta = QMessageBox.question(
            self,
            "Confirmar Arquivamento",
            (
                f"Arquivar o usuário '{nome_usuario}' irá revogar o acesso imediato,\n"
                "mas os dados históricos serão preservados. Deseja continuar?"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if resposta == QMessageBox.StandardButton.Yes:
            resultado = usuario.arquivar_usuario(nome_usuario)
            if "Sucesso" in resultado:
                QMessageBox.information(self, "Usuário arquivado", resultado)
                self.carregar_usuarios()
                return
            QMessageBox.warning(self, "Erro", resultado)
            self.atualizar_estado_botoes(item_selecionado, None)

    def restaurar_usuario(self):
        """Restaura um usuário previamente arquivado."""
        item_selecionado = self.tree_usuarios.currentItem()
        if not item_selecionado:
            QMessageBox.warning(self, "Erro", "Selecione um usuário para restaurar.")
            return

        dados_usuario = item_selecionado.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(dados_usuario, dict):
            QMessageBox.warning(self, "Erro", "Não foi possível identificar o usuário.")
            return

        if dados_usuario.get("ativo", False):
            QMessageBox.information(
                self,
                "Usuário ativo",
                "O usuário selecionado já está ativo.",
            )
            return

        nome_usuario = dados_usuario["nome"]

        resposta = QMessageBox.question(
            self,
            "Confirmar Restauração",
            (
                f"Deseja restaurar o acesso do usuário '{nome_usuario}'?\n"
                "O banco individual será reativado automaticamente."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if resposta == QMessageBox.StandardButton.Yes:
            resultado = usuario.restaurar_usuario(nome_usuario)
            if "Sucesso" in resultado:
                QMessageBox.information(self, "Usuário restaurado", resultado)
                self.carregar_usuarios()
                return
            QMessageBox.warning(self, "Erro", resultado)
            self.atualizar_estado_botoes(item_selecionado, None)

    def alterar_senha(self):
        """Permite ao usuário logado alterar sua própria senha."""
        # Obter o usuário logado da janela principal
        main_window = self.parent()
        if not hasattr(main_window, "usuario_logado"):
            QMessageBox.warning(
                self, "Erro", "Não foi possível identificar o usuário logado."
            )
            return

        usuario_logado = main_window.usuario_logado

        # Solicitar senha atual
        senha_atual, ok = QInputDialog.getText(
            self,
            "Senha Atual",
            "Digite sua senha atual:",
            QLineEdit.EchoMode.Password,
        )

        if not ok or not senha_atual.strip():
            return

        # Solicitar nova senha
        nova_senha, ok = QInputDialog.getText(
            self,
            "Nova Senha",
            "Digite a nova senha:",
            QLineEdit.EchoMode.Password,
        )

        if not ok or not nova_senha.strip():
            return

        # Confirmar nova senha
        confirmar_senha, ok = QInputDialog.getText(
            self,
            "Confirmar Senha",
            "Confirme a nova senha:",
            QLineEdit.EchoMode.Password,
        )

        if not ok or confirmar_senha != nova_senha:
            QMessageBox.warning(self, "Erro", "As senhas não conferem.")
            return

        # Alterar senha
        resultado = usuario.alterar_senha_usuario(
            usuario_logado, senha_atual, nova_senha
        )

        if "Sucesso" in resultado:
            QMessageBox.information(self, "Sucesso", "Senha alterada com sucesso!")
        else:
            QMessageBox.warning(self, "Erro", resultado)

    def shutdown_sistema(self):
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
            session_manager.definir_comando_sistema("SHUTDOWN")
            QMessageBox.information(
                self,
                "Comando Enviado",
                "Comando de shutdown enviado para todas as instâncias.\n"
                "As aplicações serão fechadas automaticamente.",
            )
            self.carregar_sessoes()
