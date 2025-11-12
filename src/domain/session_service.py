"""Gerenciamento de sessões do sistema e comandos de IPC."""

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
    "verificar_sessao_admin_duplicada",
    "encerrar_sessoes_usuario",
    "encerrar_sessoes_usuario_por_admin",
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


def registrar_sessao(usuario: str, *, admin_tool: bool = False) -> None:
    """Registra a sessão atual criando seu arquivo de sessão."""
    usuario_registrado = (usuario or "").strip()
    session_type = "admin_tool" if admin_tool else "app"
    logging.info(
        "Registrando sessão via arquivo: ID %s para usuário %s em %s (tipo: %s)",
        SESSION_ID,
        usuario_registrado,
        HOSTNAME,
        session_type,
    )
    manager.create_session_file(
        SESSION_ID, usuario_registrado, HOSTNAME, session_type=session_type
    )


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


def verificar_usuario_ja_logado(
    usuario_nome: str, *, ignorar_admin_tools: bool = False
) -> tuple[bool, dict | None]:
    """Verifica se o usuário já possui sessão ativa (independente do host).

    Args:
        usuario_nome: Nome do usuário a verificar
        ignorar_admin_tools: Se True, ignora sessões do tipo 'admin_tool'
    """
    return _verificar_sessao_por_tipo(
        usuario_nome,
        tipo_ignorar="admin_tool" if ignorar_admin_tools else None,
    )


def verificar_sessao_admin_duplicada(usuario_nome: str) -> tuple[bool, dict | None]:
    """Verifica se o usuário já possui sessão administrativa ativa.

    Args:
        usuario_nome: Nome do usuário a verificar

    Returns:
        Tupla (tem_duplicata, info_sessao) com detalhes se encontrada
    """
    return _verificar_sessao_por_tipo(
        usuario_nome,
        tipo_procurado="admin_tool",
    )


def _verificar_sessao_por_tipo(
    usuario_nome: str,
    *,
    tipo_procurado: str | None = None,
    tipo_ignorar: str | None = None,
) -> tuple[bool, dict | None]:
    """Função auxiliar para verificar sessões com filtro de tipo.

    Args:
        usuario_nome: Nome do usuário a verificar
        tipo_procurado: Se especificado, procura apenas este tipo de sessão
        tipo_ignorar: Se especificado, ignora este tipo de sessão

    Returns:
        Tupla (tem_sessao, info_sessao)
    """
    sessions = manager.get_sessions_by_user(usuario_nome)
    for session in sessions:
        if session["session_id"] == SESSION_ID:
            continue

        session_type = session.get("session_type", "app")

        # Se tipo_procurado especificado, aceitar apenas esse tipo
        if tipo_procurado and session_type != tipo_procurado:
            continue

        # Se tipo_ignorar especificado, pular esse tipo
        if tipo_ignorar and session_type == tipo_ignorar:
            continue

        return True, {
            "session_id": session["session_id"],
            "hostname": session.get("hostname", "Desconhecido"),
            "session_type": session_type,
        }
    return False, None


def encerrar_sessoes_usuario(usuario_nome: str) -> int:
    """Encerra todas as sessões associadas ao usuário (por outro login).

    Remove as sessões SEM enviar comando de encerramento.
    Usada quando outro login do mesmo usuário remove a sessão anterior.
    """
    return manager.remove_sessions_by_user(usuario_nome)


def encerrar_sessoes_usuario_por_admin(usuario_nome: str) -> int:
    """Encerra todas as sessões do usuário enviando comando (ação administrativa).

    Envia o comando de encerramento para CADA sessão do usuário ANTES de removê-la,
    garantindo que a aplicação receba a mensagem de encerramento pelo admin.
    Usada quando o admin arquiva ou exclui um usuário.
    """
    sessions = manager.get_sessions_by_user(usuario_nome)

    # Enviar comando de encerramento para cada sessão
    for session in sessions:
        session_id = session["session_id"]
        # Enviar comando para que a app receba a mensagem correta
        definir_comando_encerrar_sessao(session_id)
        logging.info(
            "Enviando comando de encerramento para sessão: %s", session_id)

    # Remover as sessões após enviar comandos
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
    """Retorna o caminho do comando para encerramento da sessão específica."""
    return Path(COMMAND_DIR) / f"{_SESSION_SHUTDOWN_PREFIX}{session_id}.cmd"


def definir_comando_encerrar_sessao(session_id: str) -> None:
    """Solicita encerramento criando arquivo de comando direcionado."""
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
