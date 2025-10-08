"""Consultas e agregações sobre os registros de processos."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, List, Optional, Tuple

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from .config import encode_registro_id, slugify_usuario
from .helpers import format_datetime, parse_iso_date
from .models import RegistroModel, UsuarioModel
from .sessions import (get_sessionmaker_for_slug, get_shared_session,
                       get_user_session, iter_user_databases)


def _montar_condicoes(
    *,
    cliente: Optional[str] = None,
    processo: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
):
    condicoes = []

    if cliente:
        condicoes.append(func.upper(RegistroModel.cliente).like(f"{cliente.upper()}%"))

    if processo:
        condicoes.append(
            func.upper(RegistroModel.processo).like(f"{processo.upper()}%")
        )

    if data_inicio and data_fim:
        data_inicio_parsed = parse_iso_date(data_inicio)
        data_fim_parsed = parse_iso_date(data_fim)
        if data_inicio_parsed and data_fim_parsed:
            condicoes.append(
                and_(
                    RegistroModel.data_processo.is_not(None),
                    RegistroModel.data_processo.between(
                        data_inicio_parsed, data_fim_parsed
                    ),
                )
            )

    return condicoes


def _buscar_registros_em_session(
    session: Session,
    *,
    slug: str,
    condicoes,
) -> List[Tuple[Any, ...]]:
    stmt = select(RegistroModel)
    for cond in condicoes:
        stmt = stmt.where(cond)

    resultados = session.execute(stmt).scalars().all()
    dados = []
    for registro in resultados:
        dados.append(
            (
                encode_registro_id(slug, registro.id),
                registro.usuario,
                registro.cliente,
                registro.processo,
                registro.qtde_itens,
                registro.data_entrada.isoformat(),
                registro.data_processo.isoformat() if registro.data_processo else None,
                registro.tempo_corte,
                float(registro.valor_pedido),
                format_datetime(registro.data_lancamento),
            )
        )
    return dados


def buscar_lancamentos_filtros(usuario: Optional[str] = None):
    """Retorna os lançamentos filtrados apenas pelo usuário informado."""

    return buscar_lancamentos_filtros_completos(usuario=usuario)


def buscar_lancamentos_filtros_completos(
    usuario: Optional[str] = None,
    cliente: Optional[str] = None,
    processo: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
):
    """Lista lançamentos considerando filtros de usuário, cliente, processo e datas."""

    condicoes = _montar_condicoes(
        cliente=cliente,
        processo=processo,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )

    registros: List[Tuple[Any, ...]] = []

    if usuario:
        slug = slugify_usuario(usuario)
        session = get_user_session(usuario)
        try:
            registros.extend(
                _buscar_registros_em_session(session, slug=slug, condicoes=condicoes)
            )
        finally:
            session.close()
    else:
        for slug, _ in iter_user_databases():
            session = get_sessionmaker_for_slug(slug)()
            try:
                registros.extend(
                    _buscar_registros_em_session(
                        session, slug=slug, condicoes=condicoes
                    )
                )
            finally:
                session.close()

    return registros


def _agregar_em_session(session: Session, condicoes) -> Tuple[int, int, float]:
    """Calcula totais de registros, itens e valor dentro de uma sessão filtrada."""

    stmt = select(RegistroModel.qtde_itens, RegistroModel.valor_pedido)
    for cond in condicoes:
        stmt = stmt.where(cond)

    total_registros = 0
    total_itens = 0
    total_valor = 0.0

    for qtde_itens, valor_pedido in session.execute(stmt).all():
        total_registros += 1
        total_itens += int(qtde_itens or 0)
        total_valor += float(valor_pedido or 0.0)

    return total_registros, total_itens, total_valor


def buscar_estatisticas(usuario: Optional[str] = None):
    """Obtém totais agregados globais ou por usuário para indicadores principais."""

    condicoes = _montar_condicoes()
    total_proc = total_itens = 0
    total_valor = 0.0

    if usuario:
        session = get_user_session(usuario)
        try:
            tp, ti, tv = _agregar_em_session(session, condicoes)
        finally:
            session.close()
        total_proc += tp
        total_itens += ti
        total_valor += tv
    else:
        for slug, _ in iter_user_databases():
            session = get_sessionmaker_for_slug(slug)()
            try:
                tp, ti, tv = _agregar_em_session(session, condicoes)
            finally:
                session.close()
            total_proc += tp
            total_itens += ti
            total_valor += tv

    return {
        "total_processos": total_proc,
        "total_itens": total_itens,
        "total_valor": total_valor,
    }


def buscar_estatisticas_completas(
    usuario: Optional[str] = None,
    cliente: Optional[str] = None,
    processo: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
):
    """Retorna totais agregados considerando filtros textuais e de período."""

    condicoes = _montar_condicoes(
        cliente=cliente,
        processo=processo,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )

    total_proc = total_itens = 0
    total_valor = 0.0

    if usuario:
        session = get_user_session(usuario)
        try:
            tp, ti, tv = _agregar_em_session(session, condicoes)
        finally:
            session.close()
        total_proc += tp
        total_itens += ti
        total_valor += tv
    else:
        for slug, _ in iter_user_databases():
            session = get_sessionmaker_for_slug(slug)()
            try:
                tp, ti, tv = _agregar_em_session(session, condicoes)
            finally:
                session.close()
            total_proc += tp
            total_itens += ti
            total_valor += tv

    return {
        "total_processos": total_proc,
        "total_itens": total_itens,
        "total_valor": total_valor,
    }


def _buscar_valores_unicos(
    campo: str,
    usuario: Optional[str] = None,
) -> List[str]:
    """Recupera valores distintos de um determinado campo opcionalmente por usuário."""

    valores: set[str] = set()

    if usuario:
        session = get_user_session(usuario)
        try:
            stmt = select(getattr(RegistroModel, campo).distinct())
            valores.update(value for (value,) in session.execute(stmt) if value)
        finally:
            session.close()
    else:
        for slug, _ in iter_user_databases():
            session = get_sessionmaker_for_slug(slug)()
            try:
                stmt = select(getattr(RegistroModel, campo).distinct())
                valores.update(value for (value,) in session.execute(stmt) if value)
            finally:
                session.close()

    return sorted(valores)


def buscar_usuarios_unicos(*, incluir_arquivados: bool = False) -> List[str]:
    """Lista nomes de usuários cadastrados, opcionalmente incluindo arquivados."""

    with get_shared_session() as session:
        stmt = select(UsuarioModel.nome).order_by(UsuarioModel.nome)
        if not incluir_arquivados:
            stmt = stmt.where(UsuarioModel.ativo.is_(True))
        nomes = session.scalars(stmt).all()
    return list(nomes)


def buscar_clientes_unicos(usuario: Optional[str] = None) -> List[str]:
    """Retorna clientes distintos globalmente ou para um usuário específico."""

    return _buscar_valores_unicos("cliente", usuario)


def buscar_clientes_unicos_por_usuario(usuario: Optional[str] = None) -> List[str]:
    """Mantida por compatibilidade: encaminha para ``buscar_clientes_unicos``."""

    return buscar_clientes_unicos(usuario)


def buscar_processos_unicos_por_usuario(usuario: Optional[str] = None) -> List[str]:
    """Retorna os nomes de processo distintos para o escopo indicado."""

    return _buscar_valores_unicos("processo", usuario)


def buscar_meses_unicos(usuario: Optional[str] = None) -> List[str]:
    """Recupera meses (MM) com lançamentos processados para o usuário ou geral."""

    meses: set[str] = set()
    registros = buscar_lancamentos_filtros(usuario=usuario)
    for registro in registros:
        data_proc = registro[6]
        if data_proc:
            meses.add(data_proc[5:7])
    return sorted(meses)


def buscar_anos_unicos(usuario: Optional[str] = None) -> List[str]:
    """Retorna anos distintos com lançamentos processados para o escopo fornecido."""

    anos: set[str] = set()
    registros = buscar_lancamentos_filtros(usuario=usuario)
    for registro in registros:
        data_proc = registro[6]
        if data_proc:
            anos.add(data_proc[:4])
    return sorted(anos, reverse=True)


def _listar_datas_processo_filtradas(
    usuario: Optional[str] = None,
    ano: Optional[int] = None,
    incluir_ano_seguinte: bool = False,
) -> List[str]:
    """Lista datas de processo filtradas por usuário e ano, podendo incluir ano seguinte."""

    registros = buscar_lancamentos_filtros(usuario=usuario)
    datas = []
    for registro in registros:
        data_proc = registro[6]
        if not data_proc:
            continue
        ano_proc = int(data_proc[:4])
        if ano is not None:
            if incluir_ano_seguinte:
                if ano_proc not in (ano, ano + 1):
                    continue
            elif ano_proc != ano:
                continue
        datas.append(data_proc)
    return sorted(set(datas))


def _periodo_faturamento_datas(data_str: str) -> Optional[Tuple[str, str]]:
    """Calcula o intervalo de faturamento (26 a 25) correspondente à data informada."""

    try:
        data_obj = datetime.strptime(data_str, "%Y-%m-%d")
    except ValueError:
        return None

    if data_obj.day >= 26:
        inicio = date(data_obj.year, data_obj.month, 26)
        if data_obj.month == 12:
            fim = date(data_obj.year + 1, 1, 25)
        else:
            fim = date(data_obj.year, data_obj.month + 1, 25)
    else:
        if data_obj.month == 1:
            inicio = date(data_obj.year - 1, 12, 26)
        else:
            inicio = date(data_obj.year, data_obj.month - 1, 26)
        fim = date(data_obj.year, data_obj.month, 25)

    return inicio.isoformat(), fim.isoformat()


def _formatar_periodo_exibicao(
    inicio: str, fim: str, com_ano: bool = False
) -> Optional[str]:
    """Formata um intervalo de datas para exibição, com ou sem ano explícito."""

    try:
        data_inicio = datetime.strptime(inicio, "%Y-%m-%d")
        data_fim = datetime.strptime(fim, "%Y-%m-%d")
    except ValueError:
        return None

    if com_ano:
        formato_inicio = data_inicio.strftime("%d/%m/%Y")
        formato_fim = data_fim.strftime("%d/%m/%Y")
    else:
        formato_inicio = data_inicio.strftime("%d/%m")
        formato_fim = data_fim.strftime("%d/%m")
    return f"{formato_inicio} a {formato_fim}"


def buscar_periodos_faturamento_por_ano(ano: str, usuario: Optional[str] = None):
    """Produz os períodos de faturamento (26/25) de um ano específico."""

    ano_int = int(ano)
    datas = _listar_datas_processo_filtradas(
        usuario=usuario,
        ano=ano_int,
        incluir_ano_seguinte=True,
    )

    periodos = []
    vistos = set()
    for data in datas:
        intervalo = _periodo_faturamento_datas(data)
        if intervalo and int(intervalo[0][:4]) == ano_int:
            inicio, fim = intervalo
            display = _formatar_periodo_exibicao(inicio, fim, com_ano=False)
            if display:
                chave = (inicio, fim)
                if chave not in vistos:
                    vistos.add(chave)
                    periodos.append({"display": display, "inicio": inicio, "fim": fim})

    periodos.sort(key=lambda p: p["inicio"], reverse=True)
    return periodos


def buscar_periodos_faturamento_unicos(usuario: Optional[str] = None):
    """Retorna todos os períodos de faturamento únicos encontrados nos lançamentos."""

    datas = _listar_datas_processo_filtradas(usuario=usuario)
    periodos = []
    for data in datas:
        intervalo = _periodo_faturamento_datas(data)
        if not intervalo:
            continue
        inicio, fim = intervalo
        display = _formatar_periodo_exibicao(inicio, fim, com_ano=True)
        if display:
            periodos.append({"display": display, "inicio": inicio, "fim": fim})

    vistos = set()
    resultado = []
    for periodo in sorted(periodos, key=lambda p: p["inicio"], reverse=True):
        chave = (periodo["inicio"], periodo["fim"])
        if chave not in vistos:
            vistos.add(chave)
            resultado.append(periodo)
    return resultado
