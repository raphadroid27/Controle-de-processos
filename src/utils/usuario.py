"""
Módulo para gerenciamento de usuários do sistema com SQLAlchemy.

Este módulo fornece funcionalidades para autenticação, criação,
edição e gerenciamento de usuários, incluindo hash de senhas
e controle de permissões administrativas.
"""

from __future__ import annotations

import hashlib

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .database import (UsuarioModel, ensure_user_database, get_shared_engine,
                       remover_banco_usuario)
from .database.sessions import executar_sessao_compartilhada


def criar_tabela_usuario() -> None:
    """Garante a criação da tabela de usuários."""

    get_shared_engine()  # Cria metadados compartilhados se necessário


def hash_senha(senha: str) -> str:
    """Gera hash da senha para armazenamento seguro."""

    return hashlib.sha256(senha.encode()).hexdigest()


def inserir_usuario(nome: str, senha: str, admin: bool = False) -> str:
    """Insere um novo usuário na tabela."""

    nome_limpo = nome.strip()
    senha_limpa = senha.strip()
    if not nome_limpo or not senha_limpa:
        return "Nome e senha são obrigatórios."

    def _operacao(session) -> str:
        existente = session.scalar(
            select(UsuarioModel).where(UsuarioModel.nome == nome_limpo)
        )
        if existente:
            return "Erro: Usuário já existe."

        usuario = UsuarioModel(
            nome=nome_limpo,
            senha=hash_senha(senha_limpa),
            admin=admin,
        )
        session.add(usuario)
        try:
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise

        ensure_user_database(nome_limpo)
        return "Sucesso: Usuário criado com sucesso."

    def _on_error(exc: SQLAlchemyError) -> str:
        if isinstance(exc, IntegrityError):
            return f"Erro: {exc.orig if exc.orig else 'Violação de integridade.'}"
        return f"Erro ao inserir usuário: {exc}"

    return executar_sessao_compartilhada(_operacao, error_handler=_on_error)


def verificar_login(nome: str, senha: str) -> dict:
    """Verifica se o login é válido."""

    def _operacao(session):
        senha_hash = hash_senha(senha)
        usuario = session.scalar(
            select(UsuarioModel).where(
                UsuarioModel.nome == nome.strip(),
                UsuarioModel.senha == senha_hash,
            )
        )
        if usuario:
            return {
                "sucesso": True,
                "nome": usuario.nome,
                "admin": bool(usuario.admin),
            }
        return {"sucesso": False, "mensagem": "Usuário ou senha inválidos"}

    def _on_error(exc: SQLAlchemyError) -> dict:
        return {"sucesso": False, "mensagem": f"Erro no banco de dados: {exc}"}

    return executar_sessao_compartilhada(_operacao, error_handler=_on_error)


def verificar_admin_existente() -> bool:
    """Verifica se já existe um usuário admin no banco de dados."""

    def _operacao(session) -> bool:
        count_admin = session.scalar(
            select(UsuarioModel).where(UsuarioModel.admin.is_(True)).limit(1)
        )
        return count_admin is not None

    return executar_sessao_compartilhada(_operacao, fallback=False)


def listar_usuarios() -> list[tuple[int, str, bool]]:
    """Lista todos os usuários cadastrados."""

    def _operacao(session) -> list[tuple[int, str, bool]]:
        resultados = session.execute(
            select(UsuarioModel.id, UsuarioModel.nome, UsuarioModel.admin).order_by(
                UsuarioModel.nome
            )
        ).all()
        return [(row.id, row.nome, bool(row.admin)) for row in resultados]

    def _on_error(exc: SQLAlchemyError) -> list[tuple[int, str, bool]]:
        print(f"Erro ao listar usuários: {exc}")
        return []

    return executar_sessao_compartilhada(
        _operacao,
        error_handler=_on_error,
    )


def resetar_senha_usuario(nome: str, nova_senha: str = "nova_senha") -> str:
    """Reseta a senha de um usuário pelo nome."""

    def _operacao(session) -> str:
        senha_hash = (
            nova_senha if nova_senha == "nova_senha" else hash_senha(nova_senha)
        )
        try:
            resultado = session.execute(
                update(UsuarioModel)
                .where(UsuarioModel.nome == nome)
                .values(senha=senha_hash)
            )
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise

        if resultado.rowcount and resultado.rowcount > 0:
            return "Sucesso: Senha resetada com sucesso."
        return "Erro: Usuário não encontrado."

    def _on_error(exc: SQLAlchemyError) -> str:
        return f"Erro ao resetar senha: {exc}"

    return executar_sessao_compartilhada(_operacao, error_handler=_on_error)


def excluir_usuario_por_id(user_id: int) -> str:
    """Exclui um usuário pelo ID."""

    def _operacao(session) -> str:
        usuario = session.get(UsuarioModel, user_id)
        if not usuario:
            return "Erro: Usuário não encontrado."
        if usuario.admin:
            return "Erro: Não é possível excluir um administrador."

        try:
            session.delete(usuario)
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise

        remover_banco_usuario(usuario.nome)
        return "Sucesso: Usuário excluído com sucesso."

    def _on_error(exc: SQLAlchemyError) -> str:
        return f"Erro ao excluir usuário: {exc}"

    return executar_sessao_compartilhada(_operacao, error_handler=_on_error)


def alterar_senha_usuario(nome: str, senha_atual: str, nova_senha: str) -> str:
    """Permite ao usuário alterar sua própria senha."""

    def _operacao(session) -> str:
        usuario = session.scalar(
            select(UsuarioModel).where(
                UsuarioModel.nome == nome,
                UsuarioModel.senha == hash_senha(senha_atual),
            )
        )
        if not usuario:
            return "Erro: Senha atual incorreta."

        usuario.senha = hash_senha(nova_senha)
        try:
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
        return "Sucesso: Senha alterada com sucesso."

    def _on_error(exc: SQLAlchemyError) -> str:
        return f"Erro ao alterar senha: {exc}"

    return executar_sessao_compartilhada(_operacao, error_handler=_on_error)


def verificar_senha_reset(nome: str) -> bool:
    """Verifica se o usuário precisa redefinir a senha."""

    def _operacao(session) -> bool:
        senha_atual = session.scalar(
            select(UsuarioModel.senha).where(UsuarioModel.nome == nome)
        )
        return bool(senha_atual == "nova_senha")

    def _on_error(exc: SQLAlchemyError) -> bool:
        print(f"Erro ao verificar senha de reset: {exc}")
        return False

    return executar_sessao_compartilhada(
        _operacao,
        error_handler=_on_error,
    )


def excluir_usuario(nome: str) -> str:
    """Exclui um usuário pelo nome."""

    def _operacao(session) -> str:
        usuario = session.scalar(select(UsuarioModel).where(UsuarioModel.nome == nome))
        if not usuario:
            return "Erro: Usuário não encontrado."
        if usuario.admin:
            return "Erro: Não é possível excluir um administrador."

        try:
            session.execute(delete(UsuarioModel).where(UsuarioModel.nome == nome))
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise

        remover_banco_usuario(usuario.nome)
        return "Sucesso: Usuário excluído com sucesso."

    def _on_error(exc: SQLAlchemyError) -> str:
        return f"Erro ao excluir usuário: {exc}"

    return executar_sessao_compartilhada(_operacao, error_handler=_on_error)


# Garante que a tabela seja criada na primeira vez que o módulo for importado
criar_tabela_usuario()
