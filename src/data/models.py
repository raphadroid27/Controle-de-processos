"""Definições de modelos ORM e estruturas de dados da camada de persistência."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (Boolean, Date, DateTime, Float, Index, Integer, String,
                        func)
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
    excluido: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default="0"
    )
    arquivado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.datetime("now"), nullable=False
    )

    __table_args__ = (
        # nome já tem constraint unique que cria índice automaticamente
        Index("idx_usuario_ativo", ativo),
        Index("idx_usuario_excluido", excluido),
    )


class RegistroModel(UserBase):
    """Tabela de lançamentos (registro) por usuário."""

    __tablename__ = "registro"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    cliente: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    pedido: Mapped[str] = mapped_column(
        "pedido", String(255), nullable=False, index=True
    )
    qtde_itens: Mapped[int] = mapped_column(Integer, nullable=False)
    data_entrada: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    data_processo: Mapped[Optional[date]] = mapped_column(Date, index=True)
    tempo_corte: Mapped[Optional[str]] = mapped_column(String(16))
    observacoes: Mapped[Optional[str]] = mapped_column(String(500))
    valor_pedido: Mapped[float] = mapped_column(Float, nullable=False)
    data_lancamento: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.datetime("now"), nullable=False
    )

    __table_args__ = (
        # Índices compostos para filtros comuns
        Index("idx_registro_cliente_upper", func.upper(cliente)),
        Index("idx_registro_pedido_upper", func.upper(pedido)),
        Index("idx_registro_data_processo_entrada", data_processo, data_entrada),
        Index("idx_registro_usuario_cliente", usuario, cliente),
        Index("idx_registro_usuario_data", usuario, data_processo, data_entrada),
        # Índice para ordenação por data_lancamento
        Index("idx_registro_data_lancamento", data_lancamento),
    )


@dataclass
class Lancamento:
    """Representa um lançamento de pedido no sistema."""

    usuario: Optional[str]
    cliente: str
    pedido: str
    qtde_itens: str
    data_entrada: str
    data_processo: Optional[str]
    valor_pedido: str
    tempo_corte: Optional[str] = None
    observacoes: Optional[str] = None


__all__ = [
    "SharedBase",
    "UserBase",
    "UsuarioModel",
    "RegistroModel",
    "Lancamento",
]
