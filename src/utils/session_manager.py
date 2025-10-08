"""
Gerenciamento de sessões do sistema com SQLAlchemy.
"""

from __future__ import annotations

import socket
import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.exc import SQLAlchemyError

from .database import SystemControlModel, get_shared_engine
from .database.sessions import executar_sessao_compartilhada

# ID único da sessão atual
SESSION_ID = str(uuid.uuid4())


def criar_tabela_system_control() -> None:
    """Garante a criação da tabela system_control."""

    get_shared_engine()  # cria metadados compartilhados se necessário


def registrar_sessao(usuario_nome: str) -> None:
    """Registra a sessão atual no banco de dados."""

    try:
        hostname = socket.gethostname()
    except OSError as exc:
        print(f"Erro ao registrar sessão: {exc}")
    else:

        def _operacao(session) -> None:
            try:
                session.execute(
                    delete(SystemControlModel)
                    .where(SystemControlModel.type == "SESSION")
                    .where(SystemControlModel.value.like(f"{usuario_nome}|%"))
                )

                nova_sessao = SystemControlModel(
                    type="SESSION",
                    key=SESSION_ID,
                    value=f"{usuario_nome}|{hostname}",
                    last_updated=datetime.now(timezone.utc),
                )
                session.merge(nova_sessao)
                session.commit()
            except SQLAlchemyError:
                session.rollback()
                raise

            print(
                (
                    f"Sessão registrada: {SESSION_ID} para usuário {usuario_nome} "
                    f"no host {hostname}"
                )
            )

        def _on_error(exc: SQLAlchemyError) -> None:
            print(f"Erro ao registrar sessão: {exc}")

        executar_sessao_compartilhada(_operacao, error_handler=_on_error)


def remover_sessao() -> None:
    """Remove a sessão atual do banco de dados ao fechar."""

    def _operacao(session) -> None:
        try:
            session.execute(
                delete(SystemControlModel)
                .where(SystemControlModel.type == "SESSION")
                .where(SystemControlModel.key == SESSION_ID)
            )
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
        print(f"Sessão removida: {SESSION_ID}")

    def _on_error(exc: SQLAlchemyError) -> None:
        print(f"Erro ao remover sessão: {exc}")

    executar_sessao_compartilhada(_operacao, error_handler=_on_error)


def atualizar_heartbeat_sessao() -> None:
    """Atualiza o timestamp da sessão ativa para indicar que está online."""

    def _operacao(session) -> None:
        try:
            session.execute(
                update(SystemControlModel)
                .where(SystemControlModel.type == "SESSION")
                .where(SystemControlModel.key == SESSION_ID)
                .values(last_updated=datetime.now(timezone.utc))
            )
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise

    def _on_error(exc: SQLAlchemyError) -> None:
        print(f"Erro ao atualizar heartbeat da sessão: {exc}")

    executar_sessao_compartilhada(_operacao, error_handler=_on_error)


def obter_sessoes_ativas() -> list[dict]:
    """Retorna lista de todas as sessões ativas."""

    def _operacao(session) -> list[dict]:
        resultados = session.execute(
            select(SystemControlModel)
            .where(SystemControlModel.type == "SESSION")
            .order_by(SystemControlModel.last_updated.desc())
        ).scalars()

        sessoes: list[dict] = []
        for registro in resultados:
            if registro.value and "|" in registro.value:
                usuario, hostname = registro.value.split("|", 1)
                sessoes.append(
                    {
                        "session_id": registro.key,
                        "usuario": usuario,
                        "hostname": hostname,
                        "last_updated": _formatar_timestamp(registro.last_updated),
                    }
                )
        return sessoes

    def _on_error(exc: SQLAlchemyError) -> list[dict]:
        print(f"Erro ao obter sessões ativas: {exc}")
        return []

    return executar_sessao_compartilhada(
        _operacao,
        error_handler=_on_error,
    )


def definir_comando_sistema(comando: str) -> None:
    """Define um comando do sistema (ex: 'SHUTDOWN', 'UPDATE')."""

    def _operacao(session) -> None:
        try:
            session.merge(
                SystemControlModel(
                    type="COMMAND",
                    key="SYSTEM_CMD",
                    value=comando,
                    last_updated=datetime.now(timezone.utc),
                )
            )
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise

    def _on_error(exc: SQLAlchemyError) -> None:
        print(f"Erro ao definir comando do sistema: {exc}")

    executar_sessao_compartilhada(_operacao, error_handler=_on_error)


def obter_comando_sistema() -> str | None:
    """Busca no banco e retorna o comando atual do sistema."""

    def _operacao(session) -> str | None:
        return session.scalar(
            select(SystemControlModel.value).where(
                SystemControlModel.type == "COMMAND",
                SystemControlModel.key == "SYSTEM_CMD",
            )
        )

    def _on_error(exc: SQLAlchemyError) -> str | None:
        print(f"Erro ao obter comando do sistema: {exc}")

    return executar_sessao_compartilhada(
        _operacao,
        error_handler=_on_error,
    )


def limpar_comando_sistema() -> None:
    """Limpa o comando do sistema."""

    def _operacao(session) -> None:
        try:
            session.execute(
                delete(SystemControlModel)
                .where(SystemControlModel.type == "COMMAND")
                .where(SystemControlModel.key == "SYSTEM_CMD")
            )
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise

    def _on_error(exc: SQLAlchemyError) -> None:
        print(f"Erro ao limpar comando do sistema: {exc}")

    executar_sessao_compartilhada(_operacao, error_handler=_on_error)


def verificar_usuario_ja_logado(usuario_nome: str) -> tuple[bool, dict | None]:
    """Verifica se o usuário já está logado em outra máquina."""

    def _operacao(session) -> tuple[bool, dict | None]:
        registro = session.scalar(
            select(SystemControlModel)
            .where(SystemControlModel.type == "SESSION")
            .where(SystemControlModel.value.like(f"{usuario_nome}|%"))
        )

        if registro and registro.value and "|" in registro.value:
            _, hostname = registro.value.split("|", 1)
            try:
                current_hostname = socket.gethostname()
            except OSError:
                current_hostname = hostname
            if hostname == current_hostname:
                return False, None
            return True, {"session_id": registro.key, "hostname": hostname}
        return False, None

    def _on_error(exc: SQLAlchemyError) -> tuple[bool, dict | None]:
        print(f"Erro ao verificar usuário logado: {exc}")
        return False, None

    return executar_sessao_compartilhada(
        _operacao,
        error_handler=_on_error,
    )


def remover_sessao_por_id(session_id: str) -> bool:
    """Remove uma sessão específica pelo seu ID."""

    def _operacao(session) -> bool:
        try:
            resultado = session.execute(
                delete(SystemControlModel)
                .where(SystemControlModel.type == "SESSION")
                .where(SystemControlModel.key == session_id)
            )
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
        return bool(resultado.rowcount)

    def _on_error(exc: SQLAlchemyError) -> bool:
        print(f"Erro ao remover sessão por ID: {exc}")
        return False

    return executar_sessao_compartilhada(
        _operacao,
        error_handler=_on_error,
    )


def encerrar_sessoes_usuario(usuario_nome: str) -> int:
    """Encerra todas as sessões associadas ao usuário informado."""

    def _operacao(session) -> int:
        try:
            resultado = session.execute(
                delete(SystemControlModel)
                .where(SystemControlModel.type == "SESSION")
                .where(SystemControlModel.value.like(f"{usuario_nome}|%"))
            )
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
        return int(resultado.rowcount or 0)

    def _on_error(exc: SQLAlchemyError) -> int:
        print(f"Erro ao encerrar sessões do usuário {usuario_nome}: {exc}")
        return 0

    return executar_sessao_compartilhada(
        _operacao,
        error_handler=_on_error,
    )


def _formatar_timestamp(valor: datetime | None) -> str:
    if not valor:
        return ""
    return valor.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
