"""Módulo principal da aplicação de Controle de Pedidos."""

# pylint: disable=duplicate-code
# A lógica de verificação de sessão ativa é similar ao admin_app.py
# mas mantida separada por contextos distintos de aplicação

import logging
import sys

from PySide6.QtWidgets import QApplication, QDialog

from src import data as db
from src.domain.usuario_service import criar_tabela_usuario
from src.infrastructure.ipc.manager import ensure_ipc_dirs_exist
from src.infrastructure.logging.config import configurar_logging
from src.infrastructure.maintenance import executar_manutencao_automatica
from src.ui.dialogs.login_dialog import LoginDialog
from src.ui.main_window import MainWindow
from src.ui.theme_manager import ThemeManager


class ControleProcessosApp:
    """Classe principal da aplicação."""

    def __init__(self):
        """Inicializa a aplicação."""
        configurar_logging()
        self.logger = logging.getLogger(__name__)
        self.logger.info("Inicializando ControleProcessosApp")
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Controle de Pedidos")
        self.app.setOrganizationName("Controle de Pedidos")
        self.app.setOrganizationDomain("controle-de-pedidos.local")

        self.theme_manager = ThemeManager.instance()
        self.theme_manager.initialize()
        self.main_window = None

        # Inicialização explícita das tabelas para evitar ciclos de import
        db.inicializar_todas_tabelas()
        ensure_ipc_dirs_exist()
        criar_tabela_usuario()

        # Limpeza de operações pendentes da sessão anterior
        self.logger.info("Limpando operações pendentes...")
        db.limpar_usuarios_excluidos()  # Retenta remover bancos de usuários excluidos
        db.limpar_bancos_orfaos()  # Remove bancos órfãos

        # Executar manutenção automática em background (otimiza se necessário)
        try:
            executar_manutencao_automatica()
        except (OSError, RuntimeError) as exc:
            self.logger.warning("Manutenção automática falhou: %s", exc)

    def _handle_logout(self):
        """Slot para tratar logout da MainWindow."""
        self.logger.info("Logout detectado via signal")
        self.mostrar_login()
        # Se mostrar_login retornar 0 (cancelado), app continua rodando
        # Se retornar 1 (login bem-sucedido), app continua rodando normalmente

    def run(self):
        """Executa a aplicação."""
        if self.mostrar_login() == 0:
            self.logger.info("Encerrando aplicação sem abrir janela principal")
            return 0
        self.logger.info("Aplicação iniciada com sessão autenticada")
        return self.app.exec()

    def mostrar_login(self):
        """Mostra a tela de login e abre a janela principal ao autenticar."""
        # pylint: disable=import-outside-toplevel
        # Imports dentro do método para evitar importação circular
        from PySide6.QtWidgets import QMessageBox

        from src.domain import session_service

        # Não registrar sessão automaticamente - faremos após verificações
        login_dialog = LoginDialog(registrar_sessao=False)

        if login_dialog.exec() == QDialog.Accepted:
            usuario_autenticado = login_dialog.usuario_logado

            # Verificar se já existe sessão ativa para este usuário
            # (ignorar sessões de ferramenta administrativa)
            ja_logado, info_sessao = session_service.verificar_usuario_ja_logado(
                usuario_autenticado, ignorar_admin_tools=True
            )

            if ja_logado and info_sessao:
                hostname_destino = info_sessao.get("hostname", "Desconhecido")
                if hostname_destino == session_service.HOSTNAME:
                    destino_texto = (
                        "neste mesmo computador (sessão anterior ainda aberta)."
                    )
                else:
                    destino_texto = f"no computador '{hostname_destino}'."

                resposta = QMessageBox.question(
                    login_dialog,
                    "Usuário já logado",
                    (
                        f"O usuário '{usuario_autenticado}' já está logado "
                        f"{destino_texto}\n\n"
                        "Deseja encerrar a sessão anterior e fazer login "
                        "neste computador?"
                    ),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )

                if resposta == QMessageBox.StandardButton.Yes:
                    session_service.definir_comando_encerrar_sessao(
                        info_sessao["session_id"]
                    )
                    session_service.remover_sessao_por_id(
                        info_sessao["session_id"])
                else:
                    return 0

            # Registrar nova sessão após todas as verificações
            session_service.registrar_sessao(
                usuario_autenticado, admin_tool=False)

            # Desconectar e fechar MainWindow anterior se existir
            if self.main_window:
                try:
                    # Desconectar do slot de logout
                    self.main_window.logout_requested.disconnect(
                        self._handle_logout)
                except (RuntimeError, TypeError):
                    # Sinal não estava conectado, o que é normal na primeira vez
                    pass
                # Fechar a janela anterior
                old_window = self.main_window
                self.main_window = None  # Liberar a referência
                old_window.close()  # Agora pode ser destruída pelo garbage collector
                old_window.deleteLater()  # Agendar deleção

            # Criar nova janela
            self.main_window = MainWindow(
                usuario_autenticado,
                login_dialog.is_admin,
            )
            # Usar slot dedicado para tratar logout
            self.main_window.logout_requested.connect(self._handle_logout)
            self.main_window.show()
            self.logger.info(
                "Usuário '%s' autenticado (admin=%s)",
                usuario_autenticado,
                login_dialog.is_admin,
            )
            return 1
        return 0


def main():
    """Ponto de entrada para execução direta da aplicação."""
    app = ControleProcessosApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
