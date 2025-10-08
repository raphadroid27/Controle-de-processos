"""Gerenciamento de engines e sessões para os bancos compartilhado e individuais."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Callable, Dict, Iterator, Optional, Tuple, TypeVar

from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from .config import DATABASE_DIR, SHARED_DB_PATH, slugify_usuario, user_db_path
from .models import SharedBase, UserBase, UsuarioModel

_user_sessionmakers: Dict[Path, sessionmaker[Session]] = {}

T = TypeVar("T")


def _criar_engine_sqlite(db_path: Path) -> Engine:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    url = f"sqlite+pysqlite:///{db_path.resolve()}"
    return create_engine(
        url,
        future=True,
        connect_args={"check_same_thread": False, "timeout": 30},
        pool_pre_ping=True,
    )


@lru_cache(maxsize=1)
def _shared_engine_cached() -> Engine:
    engine = _criar_engine_sqlite(SHARED_DB_PATH)
    SharedBase.metadata.create_all(engine)
    _ensure_usuario_schema(engine)
    return engine


def get_shared_engine() -> Engine:
    """Retorna (lazy) o engine do banco compartilhado."""

    return _shared_engine_cached()


@lru_cache(maxsize=1)
def _shared_sessionmaker_cached() -> sessionmaker[Session]:
    return sessionmaker(bind=get_shared_engine(), expire_on_commit=False, future=True)


def get_shared_session() -> Session:
    """Obtém uma sessão para o banco compartilhado."""

    return _shared_sessionmaker_cached()()


def _ensure_registro_schema(engine: Engine) -> None:
    try:
        inspector = inspect(engine)
        colunas = {col["name"] for col in inspector.get_columns("registro")}
        if "tempo_corte" not in colunas:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE registro ADD COLUMN tempo_corte TEXT"))
    except SQLAlchemyError:
        pass


def _ensure_usuario_schema(engine: Engine) -> None:
    try:
        inspector = inspect(engine)
        colunas = {col["name"] for col in inspector.get_columns("usuario")}
        statements: list[str] = []
        if "ativo" not in colunas:
            statements.append(
                "ALTER TABLE usuario ADD COLUMN ativo INTEGER NOT NULL DEFAULT 1"
            )
        if "arquivado_em" not in colunas:
            statements.append("ALTER TABLE usuario ADD COLUMN arquivado_em TEXT")

        if statements:
            with engine.begin() as conn:
                for stmt in statements:
                    conn.execute(text(stmt))
    except SQLAlchemyError:
        pass


def _get_user_sessionmaker(slug: str) -> sessionmaker[Session]:
    path = user_db_path(slug=slug)
    if path not in _user_sessionmakers:
        engine = _criar_engine_sqlite(path)
        UserBase.metadata.create_all(engine)
        _ensure_registro_schema(engine)
        _user_sessionmakers[path] = sessionmaker(
            bind=engine, expire_on_commit=False, future=True
        )
    return _user_sessionmakers[path]


def get_sessionmaker_for_slug(slug: str) -> sessionmaker[Session]:
    """Retorna o *sessionmaker* associado ao banco individual do slug."""

    return _get_user_sessionmaker(slug)


def get_user_session(usuario: str) -> Session:
    """Obtém sessão para o banco individual do usuário informado."""

    slug = slugify_usuario(usuario)
    session_factory = _get_user_sessionmaker(slug)
    session = session_factory()
    session.info["usuario_slug"] = slug
    return session


def iter_user_databases(
    *, incluir_arquivados: bool = False
) -> Iterator[Tuple[str, Path]]:
    """Itera sobre bancos individuais considerando o status do usuário."""

    slugs_validos: set[str] | None = None
    if not incluir_arquivados:
        with get_shared_session() as session:
            nomes_ativos = session.scalars(
                select(UsuarioModel.nome).where(UsuarioModel.ativo.is_(True))
            ).all()
        slugs_validos = {slugify_usuario(nome) for nome in nomes_ativos}

    if DATABASE_DIR.exists():
        for path in DATABASE_DIR.glob("usuario_*.db"):
            slug = path.stem.replace("usuario_", "", 1)
            if not slug:
                continue
            if slugs_validos is not None and slug not in slugs_validos:
                continue
            yield slug, path


def ensure_user_database(usuario: str) -> None:
    """Garante que o banco individual do usuário exista."""

    session = get_user_session(usuario)
    session.close()


def inicializar_todas_tabelas() -> None:
    """Mantida por compatibilidade: garante criação de schemas."""

    get_shared_engine()  # cria tabelas compartilhadas


def remover_banco_usuario(usuario: str) -> bool:
    """Remove o banco individual de um usuário (se existir)."""

    path = user_db_path(usuario=usuario)
    if path.exists():
        try:
            path.unlink()
            _user_sessionmakers.pop(path, None)
            return True
        except OSError:
            return False
    return False


def executar_sessao_compartilhada(
    operacao: Callable[[Session], T],
    *,
    fallback: Optional[T] = None,
    error_handler: Callable[[SQLAlchemyError], T] | None = None,
) -> T:
    """Executa ``operacao`` gerenciando abertura/fechamento da sessão."""

    session = get_shared_session()
    try:
        return operacao(session)
    except SQLAlchemyError as exc:
        if error_handler:
            return error_handler(exc)
        if fallback is not None:
            return fallback
        raise
    finally:
        session.close()


__all__ = [
    "get_shared_engine",
    "get_shared_session",
    "get_sessionmaker_for_slug",
    "get_user_session",
    "iter_user_databases",
    "ensure_user_database",
    "inicializar_todas_tabelas",
    "remover_banco_usuario",
    "executar_sessao_compartilhada",
]
