"""Funções utilitárias de configuração para o pacote de persistência."""

from __future__ import annotations

import hashlib
import logging
import re
import sys
import time
import unicodedata
from pathlib import Path
from typing import Optional, Tuple


def resolve_runtime_root() -> Path:
    """Determina o diretório base da aplicação em tempo de execução."""
    if getattr(sys, "frozen", False):  # PyInstaller ou similar
        return Path(sys.executable).resolve().parent
    # Em desenvolvimento: subir 2 pastas (src/data/config.py -> raiz do projeto).
    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = resolve_runtime_root()
DATABASE_DIR = PROJECT_ROOT / "database"
SHARED_DB_PATH = DATABASE_DIR / "system.db"

DATABASE_DIR.mkdir(parents=True, exist_ok=True)


def slugify_usuario(usuario: str) -> str:
    """Cria um slug estável para nome de usuário (para nomear arquivos)."""
    if not usuario:
        usuario = "usuario"

    normalized = unicodedata.normalize("NFKD", usuario)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_name = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_name).strip("-_").lower()
    if not ascii_name:
        ascii_name = "usuario"

    hash_suffix = hashlib.sha256(usuario.encode("utf-8")).hexdigest()[:8]
    return f"{ascii_name}-{hash_suffix}"


def user_db_path(*, usuario: Optional[str] = None, slug: Optional[str] = None) -> Path:
    """Resolve o caminho para o banco individual do usuário informado."""
    if slug is None:
        if usuario is None:
            raise ValueError(
                "Informe 'usuario' ou 'slug' para localizar o banco.")
        slug = slugify_usuario(usuario)
    return DATABASE_DIR / f"usuario_{slug}.db"


def marcar_banco_como_arquivado(usuario: str) -> bool:
    """Marca o banco de dados como arquivado renomeando o arquivo.

    Adiciona prefixo 'ARCHIVED_' ao nome do arquivo para indicar visualmente
    que o usuário está arquivado.

    Args:
        usuario: Nome do usuário

    Returns:
        True se conseguiu renomear, False caso contrário
    """
    logger = logging.getLogger(__name__)

    db_path = user_db_path(usuario=usuario)
    logger.debug("Tentando marcar como arquivado: %s", db_path)

    if not db_path.exists():
        logger.debug("Arquivo nao existe: %s", db_path)
        return False

    # Verifica se já está marcado como arquivado
    if db_path.name.startswith("ARCHIVED_"):
        logger.debug("Ja marcado como arquivado: %s", db_path)
        return True

    # Fecha conexões abertas no banco ANTES de renomear
    # Importa aqui para evitar circular import
    try:
        # pylint: disable=import-outside-toplevel
        from src.data.sessions import _user_sessionmakers

        path = db_path
        sessionmaker_removido = _user_sessionmakers.pop(path, None)
        if sessionmaker_removido:
            engine = sessionmaker_removido.kw.get("bind")
            if engine:
                try:
                    engine.dispose()
                    logger.debug("Engine disposto com sucesso")
                except Exception as e:  # pylint: disable=broad-exception-caught
                    logger.warning("Erro ao descartar engine: %s", e)

        time.sleep(0.2)  # Aguarda liberacao de handles
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.warning("Erro ao encerrar conexoes: %s", e)

    novo_nome = f"ARCHIVED_{db_path.name}"
    novo_path = db_path.parent / novo_nome

    try:
        logger.debug("Renomeando %s para %s", db_path, novo_path)
        db_path.rename(novo_path)
        logger.debug("Renomeacao bem-sucedida")
        return True
    except OSError as e:  # pylint: disable=broad-exception-caught
        logger.error("Erro ao renomear: %s", e)
        return False


def desmarcar_banco_como_arquivado(usuario: str) -> bool:
    """Remove a marcação de arquivo arquivado renomeando o arquivo.

    Remove prefixo 'ARCHIVED_' do nome do arquivo quando o usuário é restaurado.

    Args:
        usuario: Nome do usuário

    Returns:
        True se conseguiu renomear, False caso contrário
    """
    logger = logging.getLogger(__name__)

    slug = slugify_usuario(usuario)
    db_path_arquivado = DATABASE_DIR / f"ARCHIVED_usuario_{slug}.db"
    db_path_normal = DATABASE_DIR / f"usuario_{slug}.db"

    logger.debug("Tentando desmarcar como arquivado:")
    logger.debug("  Procurando: %s", db_path_arquivado)
    logger.debug("  Novo nome: %s", db_path_normal)

    if not db_path_arquivado.exists():
        logger.debug("Arquivo arquivado nao existe: %s", db_path_arquivado)
        return False

    try:
        logger.debug("Renomeando %s para %s",
                     db_path_arquivado, db_path_normal)
        db_path_arquivado.rename(db_path_normal)
        logger.debug("Desmarcacao bem-sucedida")
        return True
    except OSError as e:  # pylint: disable=broad-exception-caught
        logger.error("Erro ao renomear: %s", e)
        return False


def encode_registro_id(slug: str, registro_id: int) -> str:
    """Codifica o identificador composto slug:id usado externamente."""
    return f"{slug}:{registro_id}"


def decode_registro_id(identificador: str) -> Optional[Tuple[str, int]]:
    """Decodifica o identificador composto ``slug:id`` utilizado na UI."""
    if not identificador or ":" not in identificador:
        return None
    slug, _, id_str = identificador.partition(":")
    try:
        return slug, int(id_str)
    except ValueError:
        return None


__all__ = [
    "DATABASE_DIR",
    "SHARED_DB_PATH",
    "PROJECT_ROOT",
    "slugify_usuario",
    "user_db_path",
    "marcar_banco_como_arquivado",
    "desmarcar_banco_como_arquivado",
    "encode_registro_id",
    "decode_registro_id",
]
