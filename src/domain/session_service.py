"""Gerenciamento de sessões do sistema e comandos, usando comunicação baseada em arquivos (IPC)."""

import logging
import socket
import uuid
from pathlib import Path

from src.infrastructure.ipc import manager
from src.infrastructure.ipc.config import COMMAND_DIR

_SESSION_SHUTDOWN_PREFIX = "shutdown_session_"
_ADMIN_SHUTDOWN_FILENAME = "admin_shutdown.cmd"

SESSION_ID = str(uuid.uuid4())
HOSTNAME = socket.gethostname()

__all__ = [
    "SESSION_ID",
    "HOSTNAME",
    "registrar_sessao",
    "remover_sessao",
    "atualizar_heartbeat_sessao",
    "obter_sessoes_ativas",
    "verificar_usuario_ja_logado",
    "encerrar_sessoes_usuario",
    "remover_sessao_por_id",
    "definir_comando_sistema",
    "obter_comando_sistema",
    "limpar_comando_sistema",
    "get_comando_path",
    "get_comando_dir",
    "get_comando_sessao_path",
    "definir_comando_encerrar_sessao",
    "obter_comando_encerrar_sessao",
    "limpar_comando_sessao",
    "get_comando_admin_path",
    "definir_comando_shutdown_admin",
    "obter_comando_shutdown_admin",
    "limpar_comando_shutdown_admin",
]


def registrar_sessao(usuario: str) -> None:
    """Registra a sessão atual criando seu arquivo de sessão."""
    usuario_registrado = (usuario or "").strip()
    logging.info(
        "Registrando sessão via arquivo: ID %s para usuário %s em %s",
        SESSION_ID,
        usuario_registrado,
        HOSTNAME,
    )
    manager.create_session_file(SESSION_ID, usuario_registrado, HOSTNAME)


def remover_sessao() -> None:
    """Remove a sessão atual do sistema de arquivos."""
    logging.info("Removendo sessão via arquivo: ID %s", SESSION_ID)
    manager.remove_session_file(SESSION_ID)


def atualizar_heartbeat_sessao() -> None:
    """Atualiza o timestamp do arquivo da sessão para indicar que está online."""
    manager.touch_session_file(
        SESSION_ID, "", HOSTNAME
    )  # Usuario não necessário aqui, pois já está no arquivo


def obter_sessoes_ativas() -> list[dict]:
    """Retorna lista de sessões ativas."""
    return manager.get_active_sessions()


def verificar_usuario_ja_logado(usuario_nome: str) -> tuple[bool, dict | None]:
    """Verifica se o usuário já possui sessão ativa (independente do host)."""

    sessions = manager.get_sessions_by_user(usuario_nome)
    for session in sessions:
        if session["session_id"] == SESSION_ID:
            continue

        return True, {
            "session_id": session["session_id"],
            "hostname": session.get("hostname", "Desconhecido"),
        }
    return False, None


def encerrar_sessoes_usuario(usuario_nome: str) -> int:
    """Encerra todas as sessões associadas ao usuário."""
    return manager.remove_sessions_by_user(usuario_nome)


def remover_sessao_por_id(session_id: str) -> None:
    """Remove uma sessão específica pelo seu ID."""
    logging.info("Removendo sessão específica via arquivo: ID %s", session_id)
    manager.remove_session_file(session_id)


def definir_comando_sistema(comando: str) -> None:
    """Define um comando do sistema criando um arquivo."""
    manager.create_command_file(comando)


def obter_comando_sistema() -> str | None:
    """Verifica e retorna comando ativo, limpando-o."""
    if manager.check_for_command("SHUTDOWN"):
        manager.clear_command("SHUTDOWN")
        return "SHUTDOWN"
    return None


def limpar_comando_sistema() -> None:
    """Limpa comandos do sistema."""
    manager.clear_command("SHUTDOWN")


def get_comando_path() -> Path:
    """Retorna o caminho do arquivo de comando SHUTDOWN."""
    return Path(COMMAND_DIR) / "shutdown.cmd"


def get_comando_dir() -> Path:
    """Retorna o diretório onde os comandos são armazenados."""
    return Path(COMMAND_DIR)


def get_comando_sessao_path(session_id: str) -> Path:
    """Retorna o caminho do arquivo de comando para encerramento da sessão específica."""
    return Path(COMMAND_DIR) / f"{_SESSION_SHUTDOWN_PREFIX}{session_id}.cmd"


def definir_comando_encerrar_sessao(session_id: str) -> None:
    """Solicita o encerramento de uma sessão específica criando arquivo de comando direcionado."""
    comando_path = get_comando_sessao_path(session_id)
    try:
        comando_path.parent.mkdir(parents=True, exist_ok=True)
        comando_path.write_text("active", encoding="utf-8")
    except OSError as exc:  # pragma: no cover - falha rara de IO
        logging.error(
            "Não foi possível criar comando de encerramento para a sessão %s: %s",
            session_id,
            exc,
        )


def obter_comando_encerrar_sessao(session_id: str) -> bool:
    """Verifica se há comando de encerramento direcionado para esta sessão e o limpa."""
    comando_path = get_comando_sessao_path(session_id)
    if not comando_path.exists():
        return False

    try:
        comando_path.unlink()
    except OSError as exc:  # pragma: no cover - falha rara de IO
        logging.warning(
            "Não foi possível remover comando de encerramento da sessão %s: %s",
            session_id,
            exc,
        )
    return True


def limpar_comando_sessao(session_id: str) -> None:
    """Remove o comando direcionado para uma sessão, caso exista."""
    comando_path = get_comando_sessao_path(session_id)
    if comando_path.exists():
        try:
            comando_path.unlink()
        except OSError as exc:  # pragma: no cover - falha rara de IO
            logging.warning(
                "Erro ao limpar comando de sessão %s: %s",
                session_id,
                exc,
            )


def get_comando_admin_path() -> Path:
    """Retorna o caminho do comando de shutdown do admin."""

    return Path(COMMAND_DIR) / _ADMIN_SHUTDOWN_FILENAME


def definir_comando_shutdown_admin() -> bool:
    """Cria comando solicitando o encerramento da ferramenta administrativa."""

    comando_path = get_comando_admin_path()
    try:
        comando_path.parent.mkdir(parents=True, exist_ok=True)
        comando_path.write_text("shutdown", encoding="utf-8")
        return True
    except OSError as exc:  # pragma: no cover - erro raro de IO
        logging.error(
            "Não foi possível criar comando de shutdown do admin: %s",
            exc,
        )
        return False


def obter_comando_shutdown_admin() -> bool:
    """Verifica se há comando de shutdown do admin pendente e remove-o."""

    comando_path = get_comando_admin_path()
    if not comando_path.exists():
        return False

    try:
        comando_path.unlink()
    except OSError as exc:  # pragma: no cover - falha rara de IO
        logging.warning(
            "Não foi possível remover comando de shutdown do admin: %s",
            exc,
        )
    return True


def limpar_comando_shutdown_admin() -> None:
    """Remove o comando de shutdown do admin, caso exista."""

    comando_path = get_comando_admin_path()
    if comando_path.exists():
        try:
            comando_path.unlink()
        except OSError as exc:  # pragma: no cover - falha rara de IO
            logging.warning(
                "Erro ao limpar comando de shutdown do admin: %s",
                exc,
            )
