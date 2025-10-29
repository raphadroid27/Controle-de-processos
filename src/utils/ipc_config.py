"""Constantes e funções para configuração de IPC via sistema de arquivos."""

import os
import sys


def obter_dir_base() -> str:
    """Retorna o diretório base da aplicação."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


BASE_DIR = obter_dir_base()

# Diretório oculto para IPC
RUNTIME_DIR = os.path.join(BASE_DIR, ".runtime")
SESSION_DIR = os.path.join(RUNTIME_DIR, "sessions")
COMMAND_DIR = os.path.join(RUNTIME_DIR, "commands")
CACHE_DIR = os.path.join(RUNTIME_DIR, "cache")
