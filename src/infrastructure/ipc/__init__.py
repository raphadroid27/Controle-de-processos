"""Módulo de comunicação entre processos (IPC)."""

from src.infrastructure.ipc import manager
from src.infrastructure.ipc.config import COMMAND_DIR, IPC_DIR, RUNTIME_DIR, SESSION_DIR

__all__ = [
    "COMMAND_DIR",
    "IPC_DIR",
    "RUNTIME_DIR",
    "SESSION_DIR",
    "manager",
]
