"""
Módulo para dialogs de autenticação do sistema.

Este módulo contém as classes LoginDialog e NovoUsuarioDialog
para gerenciar a autenticação e criação de usuários.
"""

from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
)

from .utils import session_manager, usuario
from .utils.ui_config import (
    ALTURA_DIALOG_LOGIN,
    ALTURA_DIALOG_NOVO_USUARIO,
    ESPACAMENTO_PADRAO,
    LARGURA_DIALOG_LOGIN,
    LARGURA_DIALOG_NOVO_USUARIO,
    MARGEM_DIALOG,
    aplicar_estilo_botao,
    aplicar_icone_padrao,
    configurar_widgets_entrada_uniformes,
)


class LoginDialog(QDialog):
    """Dialog de login para autenticação de usuários."""

    def __init__(self):
        """Inicializa o diálogo de login."""
        super().__init__()
        self.setWindowTitle("Login - Controle de Processos")
        self.setFixedSize(LARGURA_DIALOG_LOGIN, ALTURA_DIALOG_LOGIN)
        self.setModal(True)
        self.usuario_logado = None
        self.is_admin = False

        # Aplicar ícone padrão
        aplicar_icone_padrao(self)

        self.init_ui()

    def init_ui(self):
        """Inicializa a interface do usuário com melhor distribuição."""
        layout = QFormLayout()
        layout.setSpacing(ESPACAMENTO_PADRAO)
        layout.setContentsMargins(
            MARGEM_DIALOG, MARGEM_DIALOG, MARGEM_DIALOG, MARGEM_DIALOG
        )

        # Campos de entrada
        self.entry_usuario = QLineEdit()
        self.entry_usuario.setPlaceholderText("Digite seu nome de usuário")
        self.entry_usuario.setToolTip(
            """Informe seu usuário cadastrado.
Use Tab para avançar para o campo de senha."""
        )

        self.entry_senha = QLineEdit()
        self.entry_senha.setEchoMode(QLineEdit.EchoMode.Password)
        self.entry_senha.setPlaceholderText("Digite sua senha")
        self.entry_senha.setToolTip(
            "Digite sua senha. Pressione Enter para tentar o login."
        )

        # Aplicar altura uniforme aos campos
        configurar_widgets_entrada_uniformes([self.entry_usuario, self.entry_senha])

        layout.addRow("Usuário:", self.entry_usuario)
        layout.addRow("Senha:", self.entry_senha)

        # Espaçador para empurrar botões para o final
        spacer = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        layout.addItem(spacer)

        # Botões com layout horizontal no final
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(ESPACAMENTO_PADRAO)

        self.btn_login = QPushButton("Login")
        self.btn_novo_usuario = QPushButton("Novo Usuário")

        # Aplicar estilo padronizado com larguras iguais
        aplicar_estilo_botao(self.btn_login, "azul", 120)
        aplicar_estilo_botao(self.btn_novo_usuario, "verde", 120)

        self.btn_login.setToolTip("Autenticar no sistema (Ctrl+Enter)")
        self.btn_login.setShortcut(QKeySequence("Ctrl+Enter"))

        self.btn_novo_usuario.setToolTip(
            "Abrir formulário para cadastrar um novo usuário (Ctrl+Shift+N)"
        )
        self.btn_novo_usuario.setShortcut(QKeySequence("Ctrl+Shift+N"))

        btn_layout.addWidget(self.btn_login)
        btn_layout.addWidget(self.btn_novo_usuario)

        layout.addRow(btn_layout)

        self.setLayout(layout)

        # Conectar eventos
        self.btn_login.clicked.connect(self.fazer_login)
        self.btn_novo_usuario.clicked.connect(self.abrir_novo_usuario)
        self.entry_senha.returnPressed.connect(self.fazer_login)
        self.entry_usuario.returnPressed.connect(self.entry_senha.setFocus)

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

        # Verificar se usuário já está logado em outra máquina
        ja_logado, info_sessao = session_manager.verificar_usuario_ja_logado(nome)
        if ja_logado and info_sessao:
            resposta = QMessageBox.question(
                self,
                "Usuário já logado",
                (
                    f"O usuário '{nome}' já está logado no computador "
                    f"'{info_sessao['hostname']}'.\n\n"
                    "Deseja encerrar a sessão anterior e fazer login neste computador?"
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if resposta == QMessageBox.StandardButton.Yes:
                # Remove a sessão anterior
                if hasattr(session_manager, "remover_sessao_por_id"):
                    session_manager.remover_sessao_por_id(
                        # type: ignore[attr-defined]
                        info_sessao["session_id"]
                    )
                else:
                    # Fallback: limpar comando e seguir (mantém compatibilidade)
                    session_manager.limpar_comando_sistema()
            else:
                return

        resultado = usuario.verificar_login(nome, senha)

        if resultado["sucesso"]:
            # Registra a nova sessão
            session_manager.registrar_sessao(nome)

            self.usuario_logado = resultado["nome"]
            self.is_admin = resultado["admin"]
            self.accept()
        else:
            QMessageBox.warning(self, "Erro de Login", resultado["mensagem"])
            self.entry_senha.clear()
            self.entry_senha.setFocus()

    def solicitar_nova_senha(self, nome):
        """Solicita nova senha quando o usuário tem senha de reset."""
        nova_senha, ok = QInputDialog.getText(
            self,
            "Nova Senha Requerida",
            "Sua senha foi resetada. Digite uma nova senha:",
            QLineEdit.EchoMode.Password,
        )

        if ok and nova_senha.strip():
            resultado = usuario.alterar_senha_usuario(nome, "nova_senha", nova_senha)
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
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(
                self,
                "Sucesso",
                "Usuário criado com sucesso! Você pode fazer login agora.",
            )


class NovoUsuarioDialog(QDialog):
    """Dialog para criação de novos usuários."""

    def __init__(self):
        """Inicializa o diálogo de novo usuário."""
        super().__init__()
        self.setWindowTitle("Novo Usuário")
        self.setFixedSize(LARGURA_DIALOG_NOVO_USUARIO, ALTURA_DIALOG_NOVO_USUARIO)
        self.setModal(True)

        # Aplicar ícone padrão
        aplicar_icone_padrao(self)

        self.init_ui()

    def init_ui(self):
        """Inicializa a interface do usuário."""
        layout = QFormLayout()
        layout.setSpacing(ESPACAMENTO_PADRAO)
        layout.setContentsMargins(
            MARGEM_DIALOG, MARGEM_DIALOG, MARGEM_DIALOG, MARGEM_DIALOG
        )

        # Campos de entrada
        self.entry_nome = QLineEdit()
        self.entry_nome.setPlaceholderText("Digite o nome do usuário")
        self.entry_nome.setToolTip(
            """Nome de usuário desejado.
Deve ser único e sem espaços extras nas extremidades."""
        )

        self.entry_senha = QLineEdit()
        self.entry_senha.setEchoMode(QLineEdit.EchoMode.Password)
        self.entry_senha.setPlaceholderText("Digite a senha")
        self.entry_senha.setToolTip(
            "Senha inicial do usuário. Utilize pelo menos 4 caracteres."
        )

        # Aplicar altura uniforme aos campos
        configurar_widgets_entrada_uniformes([self.entry_nome, self.entry_senha])

        layout.addRow("Nome:", self.entry_nome)
        layout.addRow("Senha:", self.entry_senha)

        # Só mostra opção admin se não existir um
        if not usuario.verificar_admin_existente():
            self.check_admin = QCheckBox()
            self.check_admin.setToolTip(
                "Tornar este usuário administrador (recurso disponível somente até o "
                "primeiro admin existir)."
            )
            layout.addRow("Admin:", self.check_admin)
            self.setFixedSize(
                LARGURA_DIALOG_NOVO_USUARIO, (ALTURA_DIALOG_NOVO_USUARIO + 20)
            )

        # Espaçador para empurrar botões para o final
        spacer = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        layout.addItem(spacer)

        # Botões com layout horizontal no final
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(ESPACAMENTO_PADRAO)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_salvar = QPushButton("Salvar")

        # Aplicar estilo padronizado com larguras iguais
        aplicar_estilo_botao(self.btn_cancelar, "vermelho", 110)
        aplicar_estilo_botao(self.btn_salvar, "verde", 110)

        self.btn_cancelar.setToolTip("Fechar o formulário sem criar usuário (Esc)")
        self.btn_cancelar.setShortcut(QKeySequence("Esc"))

        self.btn_salvar.setToolTip("Salvar novo usuário (Ctrl+S)")
        self.btn_salvar.setShortcut(QKeySequence("Ctrl+S"))

        btn_layout.addWidget(self.btn_cancelar)
        btn_layout.addWidget(self.btn_salvar)

        layout.addRow(btn_layout)

        self.setLayout(layout)

        # Conectar eventos
        self.btn_salvar.clicked.connect(self.salvar_usuario)
        self.btn_cancelar.clicked.connect(self.reject)

        # Navegação com Enter
        self.entry_nome.returnPressed.connect(self.entry_senha.setFocus)
        self.entry_senha.returnPressed.connect(self.salvar_usuario)

    def salvar_usuario(self):
        """Salva o novo usuário no banco de dados."""
        nome = self.entry_nome.text().strip()
        senha = self.entry_senha.text().strip()

        if not nome or not senha:
            QMessageBox.warning(self, "Erro", "Nome e senha são obrigatórios.")
            return

        if len(senha) < 4:
            QMessageBox.warning(
                self, "Erro", "A senha deve ter pelo menos 4 caracteres."
            )
            return

        # Verificar se é admin
        is_admin = hasattr(self, "check_admin") and self.check_admin.isChecked()

        resultado = usuario.inserir_usuario(nome, senha, is_admin)

        if "Sucesso" in resultado:
            QMessageBox.information(self, "Sucesso", resultado)
            self.accept()
        else:
            QMessageBox.warning(self, "Erro", resultado)
