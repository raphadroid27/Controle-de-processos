"""Tarefas de manutenção periódica do sistema.

Este módulo fornece funcionalidades para manutenção automática
dos bancos de dados, incluindo otimização periódica em background.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import text

from src.data.config import SHARED_DB_PATH
from src.data.sessions import (
    get_sessionmaker_for_slug,
    get_shared_engine,
    iter_user_databases,
)

logger = logging.getLogger(__name__)

# Diretório para arquivos de controle de manutenção
_RUNTIME_DIR = Path(".runtime") / "controle_processos"
_LAST_OPTIMIZATION_FILE = _RUNTIME_DIR / "last_optimization.txt"


def _precisa_otimizacao() -> bool:
    """Verifica se passou tempo suficiente desde a última otimização.

    Returns:
        True se precisa otimizar (nunca otimizou ou passou 7 dias)
    """
    if not _LAST_OPTIMIZATION_FILE.exists():
        return True

    try:
        last_opt = _LAST_OPTIMIZATION_FILE.read_text(encoding="utf-8").strip()
        last_date = datetime.fromisoformat(last_opt)
        return datetime.now() - last_date > timedelta(days=7)  # Otimizar a cada 7 dias
    except (ValueError, OSError):
        return True


def _registrar_otimizacao() -> None:
    """Registra o momento da última otimização."""
    try:
        _RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        _LAST_OPTIMIZATION_FILE.write_text(
            datetime.now().isoformat(), encoding="utf-8"
        )
    except OSError as exc:
        logger.warning("Não foi possível registrar otimização: %s", exc)


def otimizar_banco_background(db_path: Path) -> None:
    """Executa otimização leve em background.

    Esta função executa apenas ANALYZE e PRAGMA optimize,
    que são operações rápidas e não bloqueantes.

    Args:
        db_path: Caminho do banco de dados a otimizar
    """
    try:
        if db_path == SHARED_DB_PATH:
            engine = get_shared_engine()
        else:
            slug = db_path.stem.replace("usuario_", "", 1)
            maker = get_sessionmaker_for_slug(slug)
            engine = maker.kw["bind"]

        with engine.begin() as conn:
            # Analisar estatísticas (rápido)
            conn.execute(text("ANALYZE"))
            # Otimizar query planner (rápido)
            conn.execute(text("PRAGMA optimize"))

        logger.info("Banco otimizado: %s", db_path.name)
    except (OSError, RuntimeError) as exc:
        logger.exception("Erro ao otimizar banco %s: %s", db_path.name, exc)


def executar_manutencao_automatica() -> None:
    """Executa manutenção automática se necessário.

    Esta função é chamada na inicialização da aplicação e verifica
    se é necessário executar otimização nos bancos de dados.
    A otimização é executada no máximo uma vez a cada 7 dias.
    """
    if not _precisa_otimizacao():
        logger.debug(
            "Manutenção automática não necessária (última execução recente)")
        return

    logger.info("Iniciando manutenção automática dos bancos de dados")

    # Otimizar banco compartilhado
    otimizar_banco_background(SHARED_DB_PATH)

    # Otimizar bancos de usuários
    count = 0
    for _, db_path in iter_user_databases():
        otimizar_banco_background(db_path)
        count += 1

    _registrar_otimizacao()
    logger.info(
        "Manutenção automática concluída: 1 compartilhado + %d usuário(s)",
        count,
    )


__all__ = ["executar_manutencao_automatica", "otimizar_banco_background"]
