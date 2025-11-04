"""Operações de CRUD sobre os registros de pedidos por usuário."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.exc import SQLAlchemyError

from src.utils.database.config import decode_registro_id
from src.utils.database.helpers import (preparar_lancamento_para_insert,
                                        preparar_lancamento_para_update)
from src.utils.database.models import Lancamento, RegistroModel
from src.utils.database.queries import limpar_caches_consultas
from src.utils.database.sessions import (ensure_user_database,
                                         get_sessionmaker_for_slug,
                                         get_user_session)


def adicionar_lancamento(
    lancamento: Optional[Lancamento] = None,
    *,
    usuario: Optional[str] = None,
    cliente: Optional[str] = None,
    pedido: Optional[str] = None,
    qtde_itens: Optional[str] = None,
    data_entrada: Optional[str] = None,
    data_processo: Optional[str] = None,
    valor_pedido: Optional[str] = None,
    tempo_corte: Optional[str] = None,
    observacoes: Optional[str] = None,
) -> str:
    """Adiciona um novo registro no banco individual do usuário."""
    if lancamento is None:
        if None in (usuario, cliente, pedido, qtde_itens, data_entrada, valor_pedido):
            return (
                "Erro: Campos obrigatórios: usuário, cliente, pedido, "
                "qtd itens, data entrada, valor."
            )
        lanc = Lancamento(
            usuario=usuario,
            cliente=cliente or "",
            pedido=pedido or "",
            qtde_itens=qtde_itens or "",
            data_entrada=data_entrada or "",
            data_processo=data_processo or "",
            valor_pedido=valor_pedido or "",
            tempo_corte=tempo_corte or "",
            observacoes=observacoes or "",
        )
    else:
        lanc = lancamento

    preparado = preparar_lancamento_para_insert(lanc)
    if isinstance(preparado, str):
        return preparado

    ensure_user_database(preparado["usuario"])
    session = get_user_session(preparado["usuario"])

    try:
        registro = RegistroModel(**preparado)
        session.add(registro)
        session.commit()
        limpar_caches_consultas()
        return "Sucesso: registro adicionado!"
    except SQLAlchemyError as exc:
        session.rollback()
        return f"Erro ao inserir no banco de dados: {exc}"
    finally:
        session.close()


def excluir_lancamento(identificador: str | int) -> str:
    """Exclui um lançamento dado o identificador composto slug:id."""
    if isinstance(identificador, int):
        return "Erro: Identificador de registro inválido para o novo formato."

    decoded = decode_registro_id(identificador)
    if not decoded:
        return "Erro: Identificador de registro inválido."

    slug, registro_id = decoded
    session = get_sessionmaker_for_slug(slug)()

    try:
        registro = session.get(RegistroModel, registro_id)
        if not registro:
            return "Erro: Registro não encontrado."
        session.delete(registro)
        session.commit()
        limpar_caches_consultas()
        return "Sucesso: Registro excluído!"
    except SQLAlchemyError as exc:
        session.rollback()
        return f"Erro ao excluir registro: {exc}"
    finally:
        session.close()


def atualizar_lancamento(  # pylint: disable=too-many-locals
    identificador: str | int,
    lancamento: Optional[Lancamento] = None,
    *,
    cliente: Optional[str] = None,
    pedido: Optional[str] = None,
    qtde_itens: Optional[str] = None,
    data_entrada: Optional[str] = None,
    data_processo: Optional[str] = None,
    valor_pedido: Optional[str] = None,
    tempo_corte: Optional[str] = None,
    observacoes: Optional[str] = None,
) -> str:
    """Atualiza um lançamento existente."""
    if isinstance(identificador, int):
        return "Erro: Identificador de registro inválido para o novo formato."

    decoded = decode_registro_id(identificador)
    if not decoded:
        return "Erro: Identificador de registro inválido."

    slug, registro_id = decoded

    if lancamento is None:
        lanc = Lancamento(
            usuario=None,
            cliente=cliente or "",
            pedido=pedido or "",
            qtde_itens=qtde_itens or "",
            data_entrada=data_entrada or "",
            data_processo=data_processo or "",
            valor_pedido=valor_pedido or "",
            tempo_corte=tempo_corte or "",
            observacoes=observacoes or "",
        )
    else:
        lanc = lancamento

    preparado = preparar_lancamento_para_update(lanc)
    if isinstance(preparado, str):
        return preparado

    session = get_sessionmaker_for_slug(slug)()

    try:
        registro = session.get(RegistroModel, registro_id)
        if not registro:
            return "Erro: Registro não encontrado."

        for campo, valor in preparado.items():
            setattr(registro, campo, valor)

        session.commit()
        limpar_caches_consultas()
        return "Sucesso: Registro atualizado com sucesso!"
    except SQLAlchemyError as exc:
        session.rollback()
        return f"Erro no banco de dados: {exc}"
    finally:
        session.close()


__all__ = [
    "Lancamento",
    "adicionar_lancamento",
    "atualizar_lancamento",
    "excluir_lancamento",
]
