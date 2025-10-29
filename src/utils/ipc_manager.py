"""Módulo para Gerenciamento de Comunicação entre Processos (IPC) via sistema de arquivos."""

import ctypes
import json
import logging
import os
import shutil
import time
from datetime import datetime
from typing import Any, Dict, List

from src.utils.ipc_config import (COMMAND_DIR, RUNTIME_DIR,
                                  SESSION_DIR)

FILE_ATTRIBUTE_HIDDEN = 0x02

# --- Funções de Nível de Sistema Operacional ---


def _hide_path(path: str) -> None:
    """Define o atributo 'oculto' em um arquivo ou diretório no Windows."""
    if os.name == "nt":
        try:
            ctypes.windll.kernel32.SetFileAttributesW(
                path, FILE_ATTRIBUTE_HIDDEN)
        except (AttributeError, OSError):
            pass  # Silenciar warnings não críticos


def ensure_ipc_dirs_exist() -> None:
    """Garante que os diretórios de IPC existam e tenta ocultá-los."""
    try:
        if not os.path.exists(RUNTIME_DIR):
            os.makedirs(SESSION_DIR, exist_ok=True)
            os.makedirs(COMMAND_DIR, exist_ok=True)
            _hide_path(RUNTIME_DIR)
        else:
            os.makedirs(SESSION_DIR, exist_ok=True)
            os.makedirs(COMMAND_DIR, exist_ok=True)
    except OSError as e:
        logging.critical("Não foi possível criar os diretórios de IPC: %s", e)
        raise


# --- Gerenciamento de Sessões ---


def create_session_file(session_id: str, usuario: str, hostname: str) -> None:
    """Cria um arquivo para representar uma sessão ativa, armazenando usuario e hostname."""
    session_file = os.path.join(SESSION_DIR, f"{session_id}.session")
    data = {"usuario": usuario, "hostname": hostname}
    try:
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except IOError as e:
        logging.error(
            "Erro ao criar arquivo de sessão '%s': %s", session_id, e)


def remove_session_file(session_id: str) -> None:
    """Remove um arquivo de sessão."""
    session_file = os.path.join(SESSION_DIR, f"{session_id}.session")
    if os.path.exists(session_file):
        try:
            os.remove(session_file)
        except OSError as e:
            logging.error(
                "Erro ao remover arquivo de sessão '%s': %s", session_id, e)


def touch_session_file(session_id: str, usuario: str, hostname: str) -> None:
    """Atualiza o timestamp de modificação de um arquivo de sessão (heartbeat)."""
    session_file = os.path.join(SESSION_DIR, f"{session_id}.session")
    try:
        os.utime(session_file, None)
    except OSError:
        logging.warning(
            "Arquivo de sessão '%s' não encontrado para heartbeat. Recriando.",
            session_id,
        )
        create_session_file(session_id, usuario, hostname)


def get_active_sessions() -> List[Dict[str, Any]]:
    """Retorna uma lista de dicionários com detalhes das sessões ativas."""
    sessions = []
    if not os.path.isdir(SESSION_DIR):
        return []

    try:
        session_files = [f for f in os.listdir(
            SESSION_DIR) if f.endswith(".session")]
        for filename in session_files:
            session_id = filename.replace(".session", "")
            filepath = os.path.join(SESSION_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    usuario = data.get("usuario", "Desconhecido")
                    hostname = data.get("hostname", "N/A")
                last_modified_timestamp = os.path.getmtime(filepath)
                last_updated = datetime.fromtimestamp(last_modified_timestamp).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                sessions.append(
                    {
                        "session_id": session_id,
                        "usuario": usuario,
                        "hostname": hostname,
                        "last_updated": last_updated,
                    }
                )
            except (json.JSONDecodeError, FileNotFoundError, OSError) as e:
                logging.warning(
                    "Não foi possível ler o arquivo de sessão '%s': %s", filename, e
                )
                continue
        return sessions
    except OSError as e:
        logging.error("Erro ao listar sessões ativas: %s", e)
        return []


def get_sessions_by_user(usuario: str) -> List[Dict[str, Any]]:
    """Retorna sessões ativas para um usuário específico."""
    return [s for s in get_active_sessions() if s["usuario"] == usuario]


def remove_sessions_by_user(usuario: str) -> int:
    """Remove todas as sessões de um usuário e retorna o número removido."""
    sessions = get_sessions_by_user(usuario)
    for session in sessions:
        remove_session_file(session["session_id"])
    return len(sessions)


def cleanup_inactive_sessions(timeout_seconds: int = 120) -> None:
    """Remove arquivos de sessão que não foram atualizados dentro do timeout."""
    now = time.time()
    for session in get_active_sessions():
        session_file = os.path.join(
            SESSION_DIR, f"{session['session_id']}.session")
        try:
            last_modified = os.path.getmtime(session_file)
            if (now - last_modified) > timeout_seconds:
                remove_session_file(session["session_id"])
        except FileNotFoundError:
            continue
        except OSError as e:
            logging.error(
                "Erro ao verificar sessão inativa '%s': %s", session["session_id"], e
            )


# --- Gerenciamento de Comandos ---


_COMMAND_MAP = {
    # Nome único para evitar conflito com outros apps
    "SHUTDOWN": "shutdown.cmd",
}


def create_command_file(command: str) -> None:
    """Cria um arquivo de comando para sinalizar uma ação a todas as instâncias."""
    command_filename = _COMMAND_MAP.get(command.upper())
    if not command_filename:
        logging.error("Comando desconhecido: %s", command)
        return

    command_file = os.path.join(COMMAND_DIR, command_filename)
    try:
        with open(command_file, "w", encoding="utf-8") as f:
            f.write("active")
    except IOError as e:
        logging.error("Erro ao criar arquivo de comando '%s': %s", command, e)


def check_for_command(command: str) -> bool:
    """Verifica se um arquivo de comando existe."""
    command_filename = _COMMAND_MAP.get(command.upper())
    if not command_filename:
        return False
    return os.path.exists(os.path.join(COMMAND_DIR, command_filename))


def clear_command(command: str) -> None:
    """Remove um arquivo de comando."""
    command_filename = _COMMAND_MAP.get(command.upper())
    if not command_filename:
        return

    command_file = os.path.join(COMMAND_DIR, command_filename)
    if os.path.exists(command_file):
        try:
            os.remove(command_file)
        except OSError as e:
            logging.error(
                "Erro ao remover arquivo de comando '%s': %s", command, e)


def clear_all_commands() -> None:
    """Remove todos os arquivos de comando, limpando o diretório."""
    if os.path.isdir(COMMAND_DIR):
        try:
            shutil.rmtree(COMMAND_DIR)
            os.makedirs(COMMAND_DIR, exist_ok=True)
        except OSError as e:
            logging.error("Erro ao limpar diretório de comandos: %s", e)
