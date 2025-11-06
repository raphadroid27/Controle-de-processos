"""Aplicação administrativa independente para gerenciamento de usuários e sessões."""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QFileSystemWatcher
from PySide6.QtWidgets import (QApplication, QDialog, QMessageBox, QTabWidget,
                               QVBoxLayout)

from src.ui.widgets.sessoes_widget import GerenciarSessoesWidget
from src.ui.widgets.usuarios_widget import GerenciarUsuariosWidget
from src.ui.dialogs.login_dialog import LoginDialog
from src.ui.theme_manager import ThemeManager
from src import data as db
from src.infrastructure.ipc.manager import ensure_ipc_dirs_exist
from src.domain import session_service
from src.infrastructure.ipc.config import COMMAND_DIR
from src.infrastructure.logging.config import configurar_logging
from src.ui.styles import aplicar_icone_padrao
from src.domain.usuario_service import criar_tabela_usuario

ADMIN_LOCK_PATH = Path(COMMAND_DIR) / "admin.lock"
_ADMIN_WATCHERS: list[QFileSystemWatcher] = []


class AdminToolsDialog(QDialog):
    """Janela principal das ferramentas administrativas com abas."""

    def __init__(self, usuario_admin: str, parent=None):
        super().__init__(parent)

        self.usuario_logado = usuario_admin
        self.setModal(False)
        self.setFixedSize(600, 400)
        self.setWindowTitle(f"Ferramentas Administrativas - {usuario_admin}")

        aplicar_icone_padrao(self)

        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        self.usuarios_widget = GerenciarUsuariosWidget(self)
        self.sessoes_widget = GerenciarSessoesWidget(self)

        self.tabs.addTab(self.usuarios_widget, "Usuários")
        self.tabs.addTab(self.sessoes_widget, "Sessões")
        self.tabs.currentChanged.connect(self._on_tab_changed)

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def _on_tab_changed(self, index: int) -> None:
        """Atualiza a aba de sessões sempre que for exibida."""
        if self.tabs.widget(index) is self.sessoes_widget:
            self.sessoes_widget.carregar_sessoes()


def _executar_login_admin() -> Optional[str]:
    """Exibe o diálogo de login até que um administrador seja autenticado."""

    while True:
        dialog = LoginDialog(registrar_sessao=False)
        dialog.setWindowTitle("Login Administrativo")
        resultado = dialog.exec()

        if resultado != QDialog.Accepted:
            return None

        if not dialog.is_admin:
            session_service.remover_sessao()
            QMessageBox.warning(
                dialog,
                "Acesso negado",
                "Somente administradores podem acessar a ferramenta de gestão.",
            )
            continue

        return dialog.usuario_logado or "Administrador"


def _admin_lock_em_uso() -> bool:
    """Indica se já existe uma instância administrativa ativa."""

    return ADMIN_LOCK_PATH.exists()


def _criar_admin_lock(usuario: str) -> bool:
    """Cria o arquivo de trava que impede múltiplas instâncias."""

    dados = {"usuario": usuario, "hostname": session_service.HOSTNAME}

    try:
        ADMIN_LOCK_PATH.write_text(json.dumps(dados), encoding="utf-8")
        return True
    except OSError as exc:  # pragma: no cover - erro raro de IO
        QMessageBox.critical(
            None,
            "Erro ao iniciar",
            (
                "Não foi possível reservar o acesso administrativo.\n"
                f"Detalhes: {exc}"
            ),
        )
        return False


def _remover_admin_lock() -> None:
    """Remove a trava administrativa, se existir."""

    try:
        ADMIN_LOCK_PATH.unlink(missing_ok=True)
    except OSError:
        pass


def _ler_admin_lock_info() -> dict[str, str]:
    """Retorna informações gravadas na trava administrativa."""

    try:
        conteudo = ADMIN_LOCK_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        return {"usuario": "Desconhecido", "hostname": "Desconhecido"}

    if not conteudo:
        return {"usuario": "Desconhecido", "hostname": "Desconhecido"}

    try:
        dados = json.loads(conteudo)
        usuario = dados.get("usuario", "Desconhecido")
        hostname = dados.get("hostname", "Desconhecido")
        return {"usuario": usuario or "Desconhecido", "hostname": hostname or "Desconhecido"}
    except json.JSONDecodeError:
        return {"usuario": conteudo, "hostname": "Desconhecido"}


def _solicitar_encerramento_admin_existente(app: QApplication) -> bool:
    """Cria comando solicitando que a instância administrativa ativa encerre."""

    if not session_service.definir_comando_shutdown_admin():
        QMessageBox.critical(
            None,
            "Erro ao solicitar encerramento",
            (
                "Não foi possível solicitar o encerramento da instância administrativa ativa.\n"
                "Verifique o acesso a disco e tente novamente."
            ),
        )
        return False

    # Permitir que a instância ativa processe o evento
    app.processEvents()
    return True


def _aguardar_remocao_lock(app: QApplication, timeout_ms: int = 7000) -> bool:
    """Aguarda até que a trava administrativa seja removida."""

    deadline = time.monotonic() + (timeout_ms / 1000)
    while time.monotonic() < deadline:
        app.processEvents()
        if not _admin_lock_em_uso():
            session_service.limpar_comando_shutdown_admin()
            return True
        time.sleep(0.2)
    if not _admin_lock_em_uso():
        session_service.limpar_comando_shutdown_admin()
        return True
    return False


def _processar_comando_shutdown(app: QApplication, janela: QDialog) -> None:
    """Processa o comando de encerramento direcionado ao admin."""

    if not session_service.obter_comando_shutdown_admin():
        return

    QMessageBox.information(
        janela,
        "Administração Encerrada",
        "Outra instância solicitou o encerramento desta ferramenta administrativa.",
    )
    _remover_admin_lock()
    janela.close()
    app.quit()


def _configurar_monitoramento_shutdown(app: QApplication, janela: QDialog) -> None:
    """Configura watcher para comandos de shutdown do admin."""

    watcher = QFileSystemWatcher(janela)
    comando_dir = session_service.get_comando_dir()
    watcher.addPath(str(comando_dir))

    admin_shutdown_path = session_service.get_comando_admin_path()
    watcher.addPath(str(admin_shutdown_path))

    watcher.directoryChanged.connect(
        lambda _: _processar_comando_shutdown(app, janela))
    watcher.fileChanged.connect(
        lambda _: _processar_comando_shutdown(app, janela))

    _ADMIN_WATCHERS.append(watcher)


def _tratar_instancia_ativa(app: QApplication, logger: logging.Logger) -> bool:
    """Gerencia o fluxo quando já existe uma instância administrativa ativa."""

    if not _admin_lock_em_uso():
        return True

    lock_info = _ler_admin_lock_info()
    usuario_travado = lock_info.get("usuario", "Desconhecido")
    hostname_travado = lock_info.get("hostname", "Desconhecido")
    if hostname_travado == session_service.HOSTNAME:
        destino_texto = "este mesmo computador (instância ainda aberta)"
    elif hostname_travado == "Desconhecido":
        destino_texto = "a instância ativa (local não informado)"
    else:
        destino_texto = f"o computador '{hostname_travado}'"

    mensagem = (
        "Já existe uma instância da ferramenta administrativa ativa (usuário: "
        f"{usuario_travado}) em {destino_texto}.\n\n"
        "Deseja solicitar o encerramento da instância em uso?"
    )

    resposta = QMessageBox.question(
        None,
        "Administração em uso",
        mensagem,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )

    if resposta != QMessageBox.StandardButton.Yes:
        logger.info(
            "Usuário optou por não encerrar a instância administrativa ativa")
        return False

    if not _solicitar_encerramento_admin_existente(app):
        logger.error(
            "Falha ao solicitar encerramento de instância administrativa ativa")
        return False

    if _aguardar_remocao_lock(app):
        return True

    QMessageBox.warning(
        None,
        "Administração ainda em uso",
        (
            "Não foi possível encerrar a instância administrativa atual.\n"
            "Finalize-a manualmente e tente novamente."
        ),
    )
    return False


def main() -> int:
    """Ponto de entrada da aplicação administrativa."""
    configurar_logging()
    logger = logging.getLogger(__name__)
    logger.info("Inicializando ferramenta administrativa")
    app = QApplication(sys.argv)
    app.setApplicationName("Controle de Pedidos")
    app.setApplicationDisplayName("Controle de Pedidos - Administração")
    app.setOrganizationName("Controle de Pedidos")
    app.setOrganizationDomain("controle-de-pedidos.local")

    db.inicializar_todas_tabelas()
    ensure_ipc_dirs_exist()
    criar_tabela_usuario()

    theme_manager = ThemeManager.instance()
    theme_manager.initialize()

    if not _tratar_instancia_ativa(app, logger):
        return 0

    usuario_admin = _executar_login_admin()
    if not usuario_admin:
        session_service.remover_sessao()
        logger.info("Login administrativo cancelado")
        return 0

    if not _criar_admin_lock(usuario_admin):
        session_service.remover_sessao()
        logger.error(
            "Não foi possível criar admin.lock para '%s'", usuario_admin)
        return 1

    janela = AdminToolsDialog(usuario_admin)
    janela.finished.connect(app.quit)
    _configurar_monitoramento_shutdown(app, janela)

    session_service.limpar_comando_shutdown_admin()
    janela.show()

    try:
        logger.info("Ferramenta administrativa iniciada para '%s'",
                    usuario_admin)
        return app.exec()
    finally:
        _remover_admin_lock()
        session_service.limpar_comando_shutdown_admin()
        _ADMIN_WATCHERS.clear()
        session_service.remover_sessao()
        logger.info("Ferramenta administrativa finalizada")


if __name__ == "__main__":
    sys.exit(main())
