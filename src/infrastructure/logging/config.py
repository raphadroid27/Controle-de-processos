"""Configuração centralizada de logging para o sistema."""

from __future__ import annotations

import logging
import logging.config
from pathlib import Path
from typing import Any, Dict

# Diretório padrão para manter os arquivos de log.
LOG_DIR = Path("logs")
# Caminho padrão do arquivo de log principal.
LOG_FILE_PATH = LOG_DIR / "controle_processos.log"

_DEFAULT_CONFIG: Dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "padrao": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "padrao",
        },
        "arquivo": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_FILE_PATH),
            "maxBytes": 5_000_000,
            "backupCount": 3,
            "encoding": "utf-8",
            "formatter": "padrao",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "arquivo"],
    },
}


def configurar_logging(*, config: Dict[str, Any] | None = None) -> None:
    """Aplica a configuração de logging da aplicação (idempotente)."""
    if getattr(configurar_logging, "_configured", False):
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging_config = config or _DEFAULT_CONFIG
    logging.config.dictConfig(logging_config)
    setattr(configurar_logging, "_configured", True)
