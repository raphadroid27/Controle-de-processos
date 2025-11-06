"""Ponto de entrada principal para o aplicativo de Controle de Pedidos."""

from __future__ import annotations

import logging
import sys

from src.app import ControleProcessosApp
from src.infrastructure.logging.config import configurar_logging


def main() -> None:
    """Executa a aplicação principal com logging configurado."""
    configurar_logging()
    logging.getLogger(__name__).info("Inicializando ControleProcessosApp via main")
    app = ControleProcessosApp()
    sys.exit(app.run())


if __name__ == "__main__":  # pragma: no mutate - ponto de entrada
    main()
