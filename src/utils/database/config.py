"""Funções utilitárias de configuração para o pacote de persistência."""

from __future__ import annotations

import hashlib
import re
import sys
import unicodedata
from pathlib import Path
from typing import Optional, Tuple


def resolve_runtime_root() -> Path:
    """Determina o diretório base da aplicação em tempo de execução."""
    if getattr(sys, "frozen", False):  # PyInstaller ou similar
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[3]


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
            raise ValueError("Informe 'usuario' ou 'slug' para localizar o banco.")
        slug = slugify_usuario(usuario)
    return DATABASE_DIR / f"usuario_{slug}.db"


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
    "encode_registro_id",
    "decode_registro_id",
]
