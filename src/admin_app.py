"""Aplicação administrativa independente para gerenciamento de usuários e sessões."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QFileSystemWatcher
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog

from src.gerenciar_usuarios import GerenciarUsuariosDialog
from src.login_dialog import LoginDialog
from src.ui.theme_manager import ThemeManager
from src.utils import database as db, ipc_manager, session_manager
from src.utils.ipc_config import COMMAND_DIR
from src.utils.usuario import criar_tabela_usuario

ADMIN_LOCK_PATH = Path(COMMAND_DIR) / "admin.lock"
_ADMIN_WATCHERS: list[QFileSystemWatcher] = []


def _executar_login_admin() -> Optional[str]:
    """Exibe o diálogo de login até que um administrador seja autenticado."""

    while True:
        dialog = LoginDialog(registrar_sessao=False)
        dialog.setWindowTitle("Login Administrativo")
        resultado = dialog.exec()

        if resultado != QDialog.Accepted:
            return None

        if not dialog.is_admin:
            session_manager.remover_sessao()
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

    dados = {"usuario": usuario, "hostname": session_manager.HOSTNAME}

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

    if not session_manager.definir_comando_shutdown_admin():
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
            session_manager.limpar_comando_shutdown_admin()
            return True
        time.sleep(0.2)
    if not _admin_lock_em_uso():
        session_manager.limpar_comando_shutdown_admin()
        return True
    return False


def _processar_comando_shutdown(app: QApplication, janela: QDialog) -> None:
    """Processa o comando de encerramento direcionado ao admin."""

    if not session_manager.obter_comando_shutdown_admin():
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
    comando_dir = session_manager.get_comando_dir()
    watcher.addPath(str(comando_dir))

    admin_shutdown_path = session_manager.get_comando_admin_path()
    watcher.addPath(str(admin_shutdown_path))

    watcher.directoryChanged.connect(
        lambda _: _processar_comando_shutdown(app, janela))
    watcher.fileChanged.connect(
        lambda _: _processar_comando_shutdown(app, janela))

    _ADMIN_WATCHERS.append(watcher)


def main() -> int:
    """Ponto de entrada da aplicação administrativa."""

    app = QApplication(sys.argv)
    app.setApplicationName("Controle de Pedidos")
    app.setApplicationDisplayName("Controle de Pedidos - Administração")
    app.setOrganizationName("Controle de Pedidos")
    app.setOrganizationDomain("controle-de-pedidos.local")

    db.inicializar_todas_tabelas()
    ipc_manager.ensure_ipc_dirs_exist()
    criar_tabela_usuario()

    theme_manager = ThemeManager.instance()
    theme_manager.initialize()

    if _admin_lock_em_uso():
        lock_info = _ler_admin_lock_info()
        usuario_travado = lock_info.get("usuario", "Desconhecido")
        hostname_travado = lock_info.get("hostname", "Desconhecido")
        if hostname_travado == session_manager.HOSTNAME:
            destino_texto = "este mesmo computador (instância ainda aberta)"
        elif hostname_travado == "Desconhecido":
            destino_texto = "a instância ativa (local não informado)"
        else:
            destino_texto = f"o computador '{hostname_travado}'"
        resposta = QMessageBox.question(
            None,
            "Administração em uso",
            (
                "Já existe uma instância da ferramenta administrativa ativa (usuário: "
                f"{usuario_travado}) em {destino_texto}.\n\nDeseja solicitar o encerramento da instância em uso?"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if resposta == QMessageBox.StandardButton.Yes:
            if not _solicitar_encerramento_admin_existente(app):
                return 0

            if not _aguardar_remocao_lock(app):
                QMessageBox.warning(
                    None,
                    "Administração ainda em uso",
                    (
                        "Não foi possível encerrar a instância administrativa atual.\n"
                        "Finalize-a manualmente e tente novamente."
                    ),
                )
                return 0
        else:
            return 0

    usuario_admin = _executar_login_admin()
    if not usuario_admin:
        session_manager.remover_sessao()
        return 0

    if not _criar_admin_lock(usuario_admin):
        session_manager.remover_sessao()
        return 1

    janela = GerenciarUsuariosDialog(modal=False)
    janela.setWindowTitle(f"Gerenciar Usuários e Sessões - {usuario_admin}")
    janela.finished.connect(app.quit)
    _configurar_monitoramento_shutdown(app, janela)

    session_manager.limpar_comando_shutdown_admin()
    janela.show()

    try:
        return app.exec()
    finally:
        _remover_admin_lock()
        session_manager.limpar_comando_shutdown_admin()
        _ADMIN_WATCHERS.clear()
        session_manager.remover_sessao()


if __name__ == "__main__":
    sys.exit(main())
