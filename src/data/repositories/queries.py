"""Consultas e agregações sobre os registros de pedidos.

Este módulo implementa um sistema de cache multinível para otimizar consultas:

Cache LRU (Least Recently Used):
- maxsize=128: Cache para estatísticas gerais por usuário
- maxsize=256: Cache para listas de valores únicos (clientes, pedidos, meses, anos)
- maxsize=512: Cache para períodos de faturamento

A estratégia de cache:
1. Funções públicas não são cacheadas diretamente
2. Funções privadas com sufixo '_cache' implementam o cache LRU
3. Cache é invalidado via limpar_caches_consultas() após operações de escrita
4. Valores são armazenados como tuplas imutáveis para compatibilidade com lru_cache

Nota: Caches são mantidos em memória durante toda a execução da aplicação.
Para liberar memória ou após mudanças nos dados, use limpar_caches_consultas().
"""

from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache
from typing import Any, Iterable, List, Optional, Tuple

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from src.core.periodo_faturamento import calcular_periodo_faturamento_atual_datas
from src.data.config import encode_registro_id, slugify_usuario
from src.data.helpers import format_datetime, parse_iso_date
from src.data.models import RegistroModel, UsuarioModel
from src.data.sessions import (
    get_sessionmaker_for_slug,
    get_shared_session,
    get_user_session,
    iter_user_databases,
)


@dataclass
class FiltrosLancamentos:
    """Classe para encapsular filtros de lançamentos."""

    usuario: Optional[str] = None
    cliente: Optional[str] = None
    pedido: Optional[str] = None
    data_inicio: Optional[str] = None
    data_fim: Optional[str] = None
    limite: Optional[int] = None
    offset: Optional[int] = None


def _congelar_dict(dados: dict[str, Any]) -> tuple[tuple[str, Any], ...]:
    """Converte um dicionário em uma estrutura imutável ordenada."""

    return tuple(sorted(dados.items()))


def _descongelar_dict(congelado: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    """Restaura um dicionário a partir da representação imutável."""

    return dict(congelado)


def garantir_periodo_atual(periodos: List[dict]) -> None:
    """Garante que o período atual de faturamento esteja na lista de períodos.

    Se o período atual não estiver presente, ele é inserido no início da lista.

    Args:
        periodos: Lista de dicionários com períodos de faturamento
    """
    data_inicio_atual, data_fim_atual = calcular_periodo_faturamento_atual_datas()

    inicio_atual_fmt = data_inicio_atual.strftime("%d/%m")
    fim_atual_fmt = data_fim_atual.strftime("%d/%m")
    periodo_atual_display = f"{inicio_atual_fmt} a {fim_atual_fmt}"

    periodo_atual_existe = any(
        periodo.get("display") == periodo_atual_display for periodo in periodos
    )

    if not periodo_atual_existe:
        periodos.insert(
            0,
            {
                "display": periodo_atual_display,
                "inicio": data_inicio_atual.strftime("%Y-%m-%d"),
                "fim": data_fim_atual.strftime("%Y-%m-%d"),
            },
        )


def _montar_condicoes(
    *,
    cliente: Optional[str] = None,
    pedido: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
):
    condicoes = []

    if cliente:
        condicoes.append(func.upper(RegistroModel.cliente).like(f"{cliente.upper()}%"))

    if pedido:
        condicoes.append(func.upper(RegistroModel.pedido).like(f"{pedido.upper()}%"))

    if data_inicio and data_fim:
        data_inicio_parsed = parse_iso_date(data_inicio)
        data_fim_parsed = parse_iso_date(data_fim)
        if data_inicio_parsed and data_fim_parsed:
            # Filtrar por data_processo se existir, senão por data_entrada
            condicoes.append(
                or_(  # type: ignore[arg-type]
                    and_(
                        RegistroModel.data_processo.is_not(None),
                        RegistroModel.data_processo.between(
                            data_inicio_parsed, data_fim_parsed
                        ),
                    ),
                    and_(
                        RegistroModel.data_processo.is_(None),
                        RegistroModel.data_entrada.between(
                            data_inicio_parsed, data_fim_parsed
                        ),
                    ),
                )
            )

    return condicoes


def _buscar_registros_em_session(
    session: Session,
    *,
    slug: str,
    condicoes,
    limite: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[Tuple[Any, ...]]:
    stmt = select(RegistroModel)
    for cond in condicoes:
        stmt = stmt.where(cond)

    if limite is not None:
        stmt = stmt.limit(limite)
    if offset is not None:
        stmt = stmt.offset(offset)

    resultados = session.execute(stmt).scalars().all()
    dados = []
    for registro in resultados:
        dados.append(
            (
                encode_registro_id(slug, registro.id),
                registro.usuario,
                registro.cliente,
                registro.pedido,
                registro.qtde_itens,
                registro.data_entrada.isoformat(),
                registro.data_processo.isoformat() if registro.data_processo else None,
                registro.tempo_corte,
                registro.observacoes,
                float(registro.valor_pedido),
                format_datetime(registro.data_lancamento),
            )
        )
    return dados


# pylint: disable=R0917,R0914


def buscar_lancamentos_filtros_completos(
    filtros: Optional[FiltrosLancamentos] = None,
    *,
    usuario: Optional[str] = None,
    cliente: Optional[str] = None,
    pedido: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    limite: Optional[int] = None,
    offset: Optional[int] = None,
):
    """Lista lançamentos considerando filtros de usuário, cliente, pedido e datas."""

    if filtros:
        usuario = filtros.usuario or usuario
        cliente = filtros.cliente or cliente
        pedido = filtros.pedido or pedido
        data_inicio = filtros.data_inicio or data_inicio
        data_fim = filtros.data_fim or data_fim
        limite = filtros.limite or limite
        offset = filtros.offset or offset

    condicoes = _montar_condicoes(
        cliente=cliente,
        pedido=pedido,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )

    registros: List[Tuple[Any, ...]] = []

    if usuario:
        slug = slugify_usuario(usuario)
        with closing(get_user_session(usuario)) as session:
            registros.extend(
                _buscar_registros_em_session(
                    session,
                    slug=slug,
                    condicoes=condicoes,
                    limite=limite,
                    offset=offset,
                )
            )
    else:
        for slug, _ in iter_user_databases():
            with closing(get_sessionmaker_for_slug(slug)()) as session:
                registros.extend(
                    _buscar_registros_em_session(
                        session,
                        slug=slug,
                        condicoes=condicoes,
                        limite=limite,
                        offset=offset,
                    )
                )

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


def _calcular_estatisticas_agregadas(
    condicoes,
    usuario: Optional[str] = None,
) -> dict:
    """Calcula estatísticas agregadas (total_pedidos,
    total_itens, total_valor) para as condições dadas."""

    total_proc = total_itens = 0
    total_valor = 0.0

    if usuario:
        with closing(get_user_session(usuario)) as session:
            tp, ti, tv = _agregar_em_session(session, condicoes)
            total_proc += tp
            total_itens += ti
            total_valor += tv
    else:
        for slug, _ in iter_user_databases():
            with closing(get_sessionmaker_for_slug(slug)()) as session:
                tp, ti, tv = _agregar_em_session(session, condicoes)
                total_proc += tp
                total_itens += ti
                total_valor += tv

    return {
        "total_pedidos": total_proc,
        "total_itens": total_itens,
        "total_valor": total_valor,
    }


@lru_cache(maxsize=128)
def _buscar_estatisticas_cache(usuario: Optional[str]) -> tuple[int, int, float]:
    """Cache LRU para estatísticas globais.

    maxsize=128: Suficiente para cachear estatísticas de ~100 usuários ativos
    mais algumas combinações de filtros comuns.
    """
    condicoes = _montar_condicoes()
    totais = _calcular_estatisticas_agregadas(condicoes, usuario)
    return (
        int(totais.get("total_pedidos", 0)),
        int(totais.get("total_itens", 0)),
        float(totais.get("total_valor", 0.0)),
    )


def buscar_estatisticas(usuario: Optional[str] = None):
    """Obtém totais agregados globais ou por usuário para indicadores principais.

    Args:
        usuario: Nome do usuário para filtrar estatísticas (None = todos)

    Returns:
        Dicionário com total_pedidos, total_itens e total_valor

    Note:
        Resultados são cacheados. Use limpar_caches_consultas() após inserções.
    """

    total_pedidos, total_itens, total_valor = _buscar_estatisticas_cache(usuario)
    return {
        "total_pedidos": total_pedidos,
        "total_itens": total_itens,
        "total_valor": total_valor,
    }


@lru_cache(maxsize=256)
def _buscar_estatisticas_completas_cache(
    usuario: Optional[str],
    cliente: Optional[str],
    pedido: Optional[str],
    data_inicio: Optional[str],
    data_fim: Optional[str],
) -> tuple[int, int, float]:
    condicoes = _montar_condicoes(
        cliente=cliente,
        pedido=pedido,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )
    totais = _calcular_estatisticas_agregadas(condicoes, usuario)
    return (
        int(totais.get("total_pedidos", 0)),
        int(totais.get("total_itens", 0)),
        float(totais.get("total_valor", 0.0)),
    )


def buscar_estatisticas_completas(
    usuario: Optional[str] = None,
    cliente: Optional[str] = None,
    pedido: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
):
    """Retorna totais agregados considerando filtros aplicados."""

    total_pedidos, total_itens, total_valor = _buscar_estatisticas_completas_cache(
        usuario,
        cliente,
        pedido,
        data_inicio,
        data_fim,
    )
    return {
        "total_pedidos": total_pedidos,
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
        with closing(get_user_session(usuario)) as session:
            stmt = select(getattr(RegistroModel, campo).distinct())
            valores.update(value for (value,) in session.execute(stmt) if value)
    else:
        for slug, _ in iter_user_databases():
            with closing(get_sessionmaker_for_slug(slug)()) as session:
                stmt = select(getattr(RegistroModel, campo).distinct())
                valores.update(value for (value,) in session.execute(stmt) if value)

    return sorted(valores)


def buscar_usuarios_unicos(*, incluir_arquivados: bool = False) -> List[str]:
    """Lista nomes de usuários cadastrados, opcionalmente incluindo arquivados."""

    with get_shared_session() as session:
        stmt = select(UsuarioModel.nome).order_by(UsuarioModel.nome)
        if not incluir_arquivados:
            stmt = stmt.where(UsuarioModel.ativo.is_(True))
        nomes = session.scalars(stmt).all()
    return list(nomes)


@lru_cache(maxsize=256)
def _clientes_unicos_cache(usuario: Optional[str]) -> tuple[str, ...]:
    """Cache LRU para lista de clientes únicos.

    maxsize=256: Comporta múltiplos usuários e consultas globais sem filtro.
    """
    return tuple(_buscar_valores_unicos("cliente", usuario))


def buscar_clientes_unicos(usuario: Optional[str] = None) -> List[str]:
    """Retorna clientes distintos globalmente ou para um usuário específico."""

    return list(_clientes_unicos_cache(usuario))


@lru_cache(maxsize=256)
def _pedidos_unicos_cache(usuario: Optional[str]) -> tuple[str, ...]:
    """Cache LRU para lista de pedidos únicos.

    maxsize=256: Comporta múltiplos usuários e consultas globais.
    """
    return tuple(_buscar_valores_unicos("pedido", usuario))


def buscar_pedidos_unicos_por_usuario(usuario: Optional[str] = None) -> List[str]:
    """Retorna os identificadores de pedido distintos para o escopo indicado."""

    return list(_pedidos_unicos_cache(usuario))


@lru_cache(maxsize=256)
def _meses_unicos_cache(usuario: Optional[str]) -> tuple[str, ...]:
    meses: set[str] = set()
    registros = buscar_lancamentos_filtros_completos(usuario=usuario)
    for registro in registros:
        data_proc = registro[6]
        if data_proc:
            meses.add(data_proc[5:7])
    return tuple(sorted(meses))


def buscar_meses_unicos(usuario: Optional[str] = None) -> List[str]:
    """Recupera meses (MM) com lançamentos processados para o usuário ou geral."""

    return list(_meses_unicos_cache(usuario))


@lru_cache(maxsize=256)
def _anos_unicos_cache(usuario: Optional[str]) -> tuple[str, ...]:
    anos: set[str] = set()
    registros = buscar_lancamentos_filtros_completos(usuario=usuario)
    for registro in registros:
        data_proc = registro[6]
        if data_proc:
            anos.add(data_proc[:4])
    return tuple(sorted(anos, reverse=True))


def buscar_anos_unicos(usuario: Optional[str] = None) -> List[str]:
    """Retorna anos distintos com lançamentos processados para o escopo fornecido."""

    return list(_anos_unicos_cache(usuario))


@lru_cache(maxsize=256)
def _listar_datas_pedido_filtradas_cache(
    usuario: Optional[str],
    ano: Optional[int],
    incluir_ano_seguinte: bool,
) -> tuple[str, ...]:
    registros = buscar_lancamentos_filtros_completos(usuario=usuario)
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
    return tuple(sorted(set(datas)))


def _listar_datas_pedido_filtradas(
    usuario: Optional[str] = None,
    ano: Optional[int] = None,
    incluir_ano_seguinte: bool = False,
) -> List[str]:
    """Lista datas de processamento filtradas opcionalmente."""

    return list(
        _listar_datas_pedido_filtradas_cache(
            usuario,
            ano,
            incluir_ano_seguinte,
        )
    )


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


def _gerar_periodos_faturamento_por_ano(
    ano: str,
    usuario: Optional[str],
) -> List[dict[str, Any]]:
    ano_int = int(ano)

    # Verificar se é o ano atual
    data_inicio_atual, _ = calcular_periodo_faturamento_atual_datas()
    ano_atual = str(data_inicio_atual.year)

    if ano == ano_atual:
        # Para o ano atual, mostrar apenas períodos que existem (com dados)
        datas = _listar_datas_pedido_filtradas(
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
                    month = int(inicio[5:7])
                    numero = 1 if month == 12 else month + 1
                    chave = (inicio, fim)
                    if chave not in vistos:
                        vistos.add(chave)
                        periodos.append(
                            {
                                "display": display,
                                "inicio": inicio,
                                "fim": fim,
                                "numero": numero,
                            }
                        )
    else:
        # Para anos anteriores, gerar todos os 12 períodos do ano
        periodos = []
        for mes in range(1, 13):
            if mes == 1:
                # Janeiro: 26/12/(ano-1) a 25/01/ano
                inicio_date = date(ano_int - 1, 12, 26)
                fim_date = date(ano_int, 1, 25)
            else:
                # Outros meses: 26/(mes-1) a 25/mes
                inicio_date = date(ano_int, mes - 1, 26)
                fim_date = date(ano_int, mes, 25)

            inicio = inicio_date.isoformat()
            fim = fim_date.isoformat()

            display = _formatar_periodo_exibicao(inicio, fim, com_ano=False)
            if display:
                periodos.append(
                    {
                        "display": display,
                        "inicio": inicio,
                        "fim": fim,
                        "numero": mes,
                    }
                )

    # type: ignore[arg-type, return-value]
    periodos.sort(key=lambda p: p["inicio"], reverse=True)
    return periodos


@lru_cache(maxsize=128)
def _buscar_periodos_faturamento_por_ano_cache(
    ano: str,
    usuario: Optional[str],
) -> tuple[tuple[tuple[str, Any], ...], ...]:
    periodos = _gerar_periodos_faturamento_por_ano(ano, usuario)
    return tuple(_congelar_dict(periodo) for periodo in periodos)


def buscar_periodos_faturamento_por_ano(ano: str, usuario: Optional[str] = None):
    """Produz os períodos de faturamento (26/25) de um ano específico."""

    periodos_congelados = _buscar_periodos_faturamento_por_ano_cache(ano, usuario)
    return [_descongelar_dict(periodo) for periodo in periodos_congelados]


def _gerar_periodos_faturamento_unicos(
    usuario: Optional[str],
) -> List[dict[str, Any]]:
    datas = _listar_datas_pedido_filtradas(usuario=usuario)
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


@lru_cache(maxsize=128)
def _buscar_periodos_faturamento_unicos_cache(
    usuario: Optional[str],
) -> tuple[tuple[tuple[str, Any], ...], ...]:
    periodos = _gerar_periodos_faturamento_unicos(usuario)
    return tuple(_congelar_dict(periodo) for periodo in periodos)


def buscar_periodos_faturamento_unicos(usuario: Optional[str] = None):
    """Retorna todos os períodos de faturamento únicos encontrados nos lançamentos."""

    periodos_congelados = _buscar_periodos_faturamento_unicos_cache(usuario)
    return [_descongelar_dict(periodo) for periodo in periodos_congelados]


def limpar_caches_consultas() -> None:
    """Limpa caches derivados de consultas para refletir mudanças nos dados."""

    _clientes_unicos_cache.cache_clear()
    _pedidos_unicos_cache.cache_clear()
    _meses_unicos_cache.cache_clear()
    _anos_unicos_cache.cache_clear()
    _listar_datas_pedido_filtradas_cache.cache_clear()
    _buscar_periodos_faturamento_por_ano_cache.cache_clear()
    _buscar_periodos_faturamento_unicos_cache.cache_clear()
    _buscar_estatisticas_cache.cache_clear()
    _buscar_estatisticas_completas_cache.cache_clear()

    try:
        # Import adiado para evitar ciclos entre consultas e métricas de dashboard.
        # pylint: disable=import-outside-toplevel, cyclic-import
        from src.domain.dashboard_service import limpar_cache_metricas_dashboard
    except ImportError:
        return
    limpar_cache_metricas_dashboard()
