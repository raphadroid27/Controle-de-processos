"""Definições de modelos ORM e estruturas de dados da camada de persistência."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class SharedBase(DeclarativeBase):
    """Base declarativa para o banco compartilhado."""


class UserBase(DeclarativeBase):
    """Base declarativa para os bancos individuais de registro."""


class UsuarioModel(SharedBase):
    """Tabela de usuários do sistema."""

    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    senha: Mapped[str] = mapped_column(String(255), nullable=False)
    admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ativo: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, server_default="1"
    )
    arquivado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.datetime("now"), nullable=False
    )


class SystemControlModel(SharedBase):
    """Tabela de controle de sessões e comandos do sistema."""

    __tablename__ = "system_control"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    value: Mapped[Optional[str]] = mapped_column(String(512))
    last_updated: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.datetime("now"), nullable=False
    )


class RegistroModel(UserBase):
    """Tabela de lançamentos (registro) por usuário."""

    __tablename__ = "registro"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    cliente: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    processo: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    qtde_itens: Mapped[int] = mapped_column(Integer, nullable=False)
    data_entrada: Mapped[date] = mapped_column(Date, nullable=False)
    data_processo: Mapped[Optional[date]] = mapped_column(Date)
    tempo_corte: Mapped[Optional[str]] = mapped_column(String(16))
    valor_pedido: Mapped[float] = mapped_column(Float, nullable=False)
    data_lancamento: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.datetime("now"), nullable=False
    )


@dataclass
class Lancamento:
    """Representa um lançamento de processo no sistema."""

    usuario: Optional[str]
    cliente: str
    processo: str
    qtde_itens: str
    data_entrada: str
    data_processo: Optional[str]
    valor_pedido: str
    tempo_corte: Optional[str] = None


__all__ = [
    "SharedBase",
    "UserBase",
    "UsuarioModel",
    "SystemControlModel",
    "RegistroModel",
    "Lancamento",
]
