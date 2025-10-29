"""Gerenciamento de sessões do sistema e comandos, usando comunicação baseada em arquivos (IPC)."""

import logging
import socket
import uuid
from pathlib import Path

from src.utils import ipc_manager
from src.utils.ipc_config import COMMAND_DIR

SESSION_ID = str(uuid.uuid4())
HOSTNAME = socket.gethostname()


def registrar_sessao(usuario: str) -> None:
    """Registra a sessão atual criando seu arquivo de sessão."""
    logging.info(
        "Registrando sessão via arquivo: ID %s para usuário %s em %s",
        SESSION_ID,
        usuario,
        HOSTNAME,
    )
    ipc_manager.create_session_file(SESSION_ID, usuario, HOSTNAME)


def remover_sessao() -> None:
    """Remove a sessão atual do sistema de arquivos."""
    logging.info("Removendo sessão via arquivo: ID %s", SESSION_ID)
    ipc_manager.remove_session_file(SESSION_ID)


def atualizar_heartbeat_sessao() -> None:
    """Atualiza o timestamp do arquivo da sessão para indicar que está online."""
    ipc_manager.touch_session_file(
        SESSION_ID, "", HOSTNAME
    )  # Usuario não necessário aqui, pois já está no arquivo


def obter_sessoes_ativas() -> list[dict]:
    """Retorna lista de sessões ativas."""
    return ipc_manager.get_active_sessions()


def verificar_usuario_ja_logado(usuario_nome: str) -> tuple[bool, dict | None]:
    """Verifica se o usuário já está logado em outra máquina."""
    sessions = ipc_manager.get_sessions_by_user(usuario_nome)
    for session in sessions:
        if session["hostname"] != HOSTNAME:
            return True, {
                "session_id": session["session_id"],
                "hostname": session["hostname"],
            }
    return False, None


def encerrar_sessoes_usuario(usuario_nome: str) -> int:
    """Encerra todas as sessões associadas ao usuário."""
    return ipc_manager.remove_sessions_by_user(usuario_nome)


def remover_sessao_por_id(session_id: str) -> None:
    """Remove uma sessão específica pelo seu ID."""
    logging.info("Removendo sessão específica via arquivo: ID %s", session_id)
    ipc_manager.remove_session_file(session_id)


def definir_comando_sistema(comando: str) -> None:
    """Define um comando do sistema criando um arquivo."""
    ipc_manager.create_command_file(comando)


def obter_comando_sistema() -> str | None:
    """Verifica e retorna comando ativo, limpando-o."""
    if ipc_manager.check_for_command("SHUTDOWN"):
        ipc_manager.clear_command("SHUTDOWN")
        return "SHUTDOWN"
    return None


def limpar_comando_sistema() -> None:
    """Limpa comandos do sistema."""
    ipc_manager.clear_command("SHUTDOWN")


def get_comando_path() -> Path:
    """Retorna o caminho do arquivo de comando SHUTDOWN."""
    return Path(COMMAND_DIR) / "shutdown.cmd"
