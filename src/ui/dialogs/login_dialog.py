"""
Módulo para dialogs de autenticação do sistema.

Este módulo contém as classes LoginDialog e NovoUsuarioDialog
para gerenciar a autenticação e criação de usuários.
"""

# pylint: disable=duplicate-code
# A lógica de verificação de sessão duplicada é similar ao app.py
# mas mantida no dialog para validação durante o login

import qtawesome as qta
from PySide6.QtCore import QTimer
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QWidget,
)

from src.domain import session_service, usuario_service
from src.domain.session_service import (
    HOSTNAME,
    definir_comando_encerrar_sessao,
    remover_sessao_por_id,
    verificar_usuario_ja_logado,
)
from src.ui.styles import (
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

    def __init__(self, parent=None, *, registrar_sessao: bool = True):
        """Inicializa o diálogo de login."""
        super().__init__(parent)
        self.setWindowTitle("Login - Controle de Pedidos")
        self.setFixedSize(LARGURA_DIALOG_LOGIN, ALTURA_DIALOG_LOGIN)
        self.setModal(True)
        self.usuario_logado = None
        self.is_admin = False
        self._registrar_sessao = registrar_sessao

        # Aplicar ícone padrão
        aplicar_icone_padrao(self)

        # Timer de inatividade (5 minutos = 300.000 ms)
        self._inactivity_timer = QTimer(self)
        self._inactivity_timer.setInterval(300000)  # 5 minutos
        self._inactivity_timer.timeout.connect(self._fechar_por_inatividade)
        self._inactivity_timer.setSingleShot(True)

        self.init_ui()

        # Iniciar timer após configurar UI
        self._inactivity_timer.start()

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
        configurar_widgets_entrada_uniformes(
            [self.entry_usuario, self.entry_senha])

        label_usuario = QLabel("Usuário:")
        label_usuario.setObjectName("label_titulo_negrito")
        layout.addRow(label_usuario, self.entry_usuario)

        label_senha = QLabel("Senha:")
        label_senha.setObjectName("label_titulo_negrito")
        layout.addRow(label_senha, self.entry_senha)

        # Espaçador para empurrar botões para o final
        spacer = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        layout.addItem(spacer)

        # Botões com layout horizontal no final
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(ESPACAMENTO_PADRAO)

        self.btn_login = QPushButton("Login")
        self.btn_login.setIcon(qta.icon("fa5s.sign-in-alt"))
        self.btn_novo_usuario = QPushButton("Novo Usuário")
        self.btn_novo_usuario.setIcon(qta.icon("fa5s.user-plus"))

        # Aplicar estilo padronizado com larguras iguais
        aplicar_estilo_botao(self.btn_login, "azul")
        aplicar_estilo_botao(self.btn_novo_usuario, "verde")

        self.btn_login.setDefault(True)
        self.btn_login.setToolTip("Autenticar no sistema (Enter)")

        self.btn_novo_usuario.setToolTip(
            "Cadastrar um novo usuário (Ctrl+Shift+N)")
        self.btn_novo_usuario.setShortcut(QKeySequence("Ctrl+Shift+N"))

        btn_layout.addWidget(self.btn_login)
        btn_layout.addWidget(self.btn_novo_usuario)

        layout.addRow(btn_layout)

        self.setLayout(layout)

        # Conectar eventos
        self.btn_login.clicked.connect(self.fazer_login)
        self.btn_novo_usuario.clicked.connect(self.abrir_novo_usuario)
        self.entry_usuario.returnPressed.connect(self.entry_senha.setFocus)

        # Conectar eventos de interação para resetar timer
        self.entry_usuario.textChanged.connect(self._resetar_timer_inatividade)
        self.entry_senha.textChanged.connect(self._resetar_timer_inatividade)

    def _resetar_timer_inatividade(self):
        """Reseta o timer de inatividade quando há interação do usuário."""
        if self._inactivity_timer.isActive():
            self._inactivity_timer.stop()
        self._inactivity_timer.start()

    def _fechar_por_inatividade(self):
        """Fecha o diálogo após período de inatividade."""
        self.reject()

    def closeEvent(self, event):  # pylint: disable=invalid-name
        """Limpa resources ao fechar o diálogo."""
        if hasattr(self, "_inactivity_timer") and self._inactivity_timer.isActive():
            self._inactivity_timer.stop()
        event.accept()

    def fazer_login(self):
        """Realiza a autenticação do usuário."""
        # Resetar timer ao tentar login
        self._resetar_timer_inatividade()

        nome = self.entry_usuario.text().strip()
        senha = self.entry_senha.text().strip()

        # Verificar se precisa redefinir senha
        if usuario_service.verificar_senha_reset(nome):
            self.solicitar_nova_senha(nome)
            return

        resultado = usuario_service.verificar_login(nome, senha)

        if resultado["sucesso"]:
            nome_autenticado = resultado["nome"]

            # Apenas verificar duplicatas se for para registrar sessão
            # (quando registrar_sessao=False, a verificação é feita externamente)
            if self._registrar_sessao:
                # Ignorar sessões de ferramenta administrativa ao verificar duplicatas
                ja_logado, info_sessao = verificar_usuario_ja_logado(
                    nome_autenticado, ignorar_admin_tools=True
                )
                if ja_logado and info_sessao:
                    hostname_destino = info_sessao.get(
                        "hostname", "Desconhecido")
                    if hostname_destino == HOSTNAME:
                        destino_texto = (
                            "neste mesmo computador (sessão anterior ainda aberta)."
                        )
                    else:
                        destino_texto = f"no computador '{hostname_destino}'."

                    resposta = QMessageBox.question(
                        self,
                        "Usuário já logado",
                        (
                            f"O usuário '{nome_autenticado}' já está logado "
                            f"{destino_texto}\n\n"
                            "Deseja encerrar a sessão anterior e fazer "
                            "login neste computador?"
                        ),
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No,
                    )

                    if resposta == QMessageBox.StandardButton.Yes:
                        definir_comando_encerrar_sessao(
                            info_sessao["session_id"])
                        remover_sessao_por_id(info_sessao["session_id"])
                    else:
                        return

                session_service.registrar_sessao(
                    nome_autenticado, admin_tool=False)

            self.usuario_logado = nome_autenticado
            self.is_admin = resultado["admin"]

            # Parar timer ao fazer login com sucesso
            self._inactivity_timer.stop()

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
            resultado = usuario_service.alterar_senha_usuario(
                nome, "nova_senha", nova_senha
            )
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
        # Resetar timer ao abrir diálogo de novo usuário
        self._resetar_timer_inatividade()

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
        self.setFixedSize(LARGURA_DIALOG_NOVO_USUARIO,
                          ALTURA_DIALOG_NOVO_USUARIO)
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
        configurar_widgets_entrada_uniformes(
            [self.entry_nome, self.entry_senha])

        label_nome = QLabel("Nome:")
        label_nome.setObjectName("label_titulo_negrito")
        layout.addRow(label_nome, self.entry_nome)

        label_senha = QLabel("Senha:")
        label_senha.setObjectName("label_titulo_negrito")
        layout.addRow(label_senha, self.entry_senha)

        # Só mostra opção admin se não existir um
        if not usuario_service.verificar_admin_existente():
            self.check_admin = QCheckBox()
            self.check_admin.setToolTip(
                "Tornar este usuário administrador (recurso disponível somente até o "
                "primeiro admin existir)."
            )

            # Container para alinhar checkbox
            container_admin = QWidget()
            layout_admin = QHBoxLayout(container_admin)
            layout_admin.setContentsMargins(
                0, 2, 0, 0)  # Pequeno ajuste vertical
            layout_admin.addWidget(self.check_admin)
            layout_admin.addStretch()

            label_admin = QLabel("Admin:")
            label_admin.setObjectName("label_titulo_negrito")
            layout.addRow(label_admin, container_admin)
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
        self.btn_cancelar.setIcon(qta.icon("fa5s.times"))
        self.btn_salvar = QPushButton("Salvar")
        self.btn_salvar.setIcon(qta.icon("fa5s.save"))

        # Aplicar estilo padronizado com larguras iguais
        aplicar_estilo_botao(self.btn_cancelar, "vermelho")
        aplicar_estilo_botao(self.btn_salvar, "verde")

        self.btn_cancelar.setToolTip(
            "Fechar o formulário sem criar usuário (Esc)")
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
        is_admin = hasattr(
            self, "check_admin") and self.check_admin.isChecked()

        resultado = usuario_service.inserir_usuario(nome, senha, is_admin)

        if "Sucesso" in resultado:
            QMessageBox.information(self, "Sucesso", resultado)
            self.accept()
        else:
            QMessageBox.warning(self, "Erro", resultado)
