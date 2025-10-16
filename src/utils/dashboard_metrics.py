"""Utilitários para cálculo de métricas do dashboard administrativo."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Any, DefaultDict, Dict, Iterable, List, Set

from sqlalchemy import select

from . import database as db


def _novo_pacote_mensal() -> Dict[str, float]:
    """Gera a estrutura inicial para acumular dados mensais."""
    return {"itens": 0, "valor": 0.0, "os": 0}


@dataclass(slots=True)
class RegistroResumo:
    """Projeção simplificada de um registro para cálculo de métricas."""

    usuario: str
    data_base: date
    qtde_itens: int
    valor_pedido: float
    tempo_segundos: int

    @property
    def ano(self) -> int:
        """Ano associado ao lançamento."""
        return self.data_base.year

    @property
    def mes(self) -> int:
        """Mês numérico do lançamento."""
        return self.data_base.month

    @property
    def dia_iso(self) -> str:
        """Retorna a data base em formato ISO (``YYYY-MM-DD``)."""
        return self.data_base.isoformat()


class DashboardAccumulator:
    """Concentra estruturas intermediárias enquanto percorremos registros."""

    def __init__(self) -> None:
        """Inicializa contadores e coleções auxiliares."""
        self.dados_mensais: DefaultDict[
            int, DefaultDict[str, DefaultDict[int, Dict[str, float]]]
        ] = defaultdict(lambda: defaultdict(lambda: defaultdict(_novo_pacote_mensal)))
        self.totais_ano: DefaultDict[int, Dict[str, float]] = defaultdict(
            _novo_pacote_mensal
        )
        self.horas_por_dia: DefaultDict[str, Dict[str, Any]] = defaultdict(
            lambda: {"total": 0, "por_usuario": defaultdict(int)}
        )
        self.totais_por_usuario: DefaultDict[str, Dict[str, float]] = defaultdict(
            lambda: {"itens": 0.0, "valor": 0.0, "os": 0.0}
        )
        self.dias_por_usuario: DefaultDict[str, Set[str]] = defaultdict(set)
        self.dias_totais: Set[str] = set()
        self.horas_total_por_usuario: DefaultDict[str, int] = defaultdict(int)
        self.horas_dias_por_usuario: DefaultDict[str, Set[str]] = defaultdict(set)
        self.usuarios_registrados: Set[str] = set()
        self.registros_raw: List[Dict[str, Any]] = []

    def acumular(self, registro: RegistroResumo) -> None:
        """Incorpora um registro agregado nas estruturas de cálculo."""
        usuario = registro.usuario
        dia_iso = registro.dia_iso
        ano = registro.ano
        mes = registro.mes

        self.usuarios_registrados.add(usuario)
        self.dias_totais.add(dia_iso)
        self.dias_por_usuario[usuario].add(dia_iso)

        dados_mes = self.dados_mensais[ano][usuario][mes]
        dados_mes["itens"] += registro.qtde_itens
        dados_mes["valor"] += registro.valor_pedido
        dados_mes["os"] += 1

        totais_ano = self.totais_ano[ano]
        totais_ano["itens"] += registro.qtde_itens
        totais_ano["valor"] += registro.valor_pedido
        totais_ano["os"] += 1

        totais_usuario = self.totais_por_usuario[usuario]
        totais_usuario["itens"] += registro.qtde_itens
        totais_usuario["valor"] += registro.valor_pedido
        totais_usuario["os"] += 1

        tempo = registro.tempo_segundos
        if tempo > 0:
            horas_info = self.horas_por_dia[dia_iso]
            horas_info["total"] += tempo
            horas_info["por_usuario"][usuario] += tempo
            self.horas_total_por_usuario[usuario] += tempo
            self.horas_dias_por_usuario[usuario].add(dia_iso)

        self.registros_raw.append(
            {
                "usuario": usuario,
                "data": dia_iso,
                "ano": ano,
                "mes": mes,
                "qtde_itens": registro.qtde_itens,
                "valor_pedido": registro.valor_pedido,
                "os": 1,
                "tempo_segundos": tempo,
            }
        )

    def finalizar(self) -> Dict[str, Any]:
        """Compila o pacote de métricas pronto para consumo no dashboard."""
        horas_ordenadas = self._ordenar_horas_por_dia()
        medias_por_usuario = self._calcular_medias_por_usuario()
        media_geral = self._calcular_media_geral()

        return {
            "usuarios": sorted(self.usuarios_registrados),
            "anos": sorted(self.dados_mensais.keys(), reverse=True),
            "dados_mensais": {
                ano: dict(usuario_dict)
                for ano, usuario_dict in self.dados_mensais.items()
            },
            "totais_ano": dict(self.totais_ano),
            "horas_por_dia": horas_ordenadas,
            "medias_por_usuario": medias_por_usuario,
            "media_geral": media_geral,
            "registros": list(self.registros_raw),
        }

    def _ordenar_horas_por_dia(self) -> Dict[str, Dict[str, Any]]:
        """Ordena o dicionário de horas diárias em ordem decrescente de data."""
        horas_ordenadas = {
            dia: {
                "total": info["total"],
                "por_usuario": dict(info["por_usuario"]),
            }
            for dia, info in sorted(
                self.horas_por_dia.items(), key=lambda item: item[0], reverse=True
            )
        }
        return horas_ordenadas

    def _calcular_medias_por_usuario(self) -> Dict[str, Dict[str, Any]]:
        """Calcula médias diárias e totais específicos por usuário."""
        medias_por_usuario: Dict[str, Dict[str, Any]] = {}
        for usuario in sorted(self.usuarios_registrados):
            dias_ativos = len(self.dias_por_usuario.get(usuario, set()))
            totais_usuario = self.totais_por_usuario.get(usuario, {})
            itens_total = float(totais_usuario.get("itens", 0.0))
            os_total = float(totais_usuario.get("os", 0.0))
            dias_com_horas = len(self.horas_dias_por_usuario.get(usuario, set()))
            horas_total_usuario = self.horas_total_por_usuario.get(usuario, 0)

            medias_por_usuario[usuario] = {
                "dias_ativos": dias_ativos,
                "itens_por_dia": itens_total / dias_ativos if dias_ativos else 0.0,
                "os_por_dia": os_total / dias_ativos if dias_ativos else 0.0,
                "dias_com_horas": dias_com_horas,
                "horas_por_dia": (
                    horas_total_usuario / dias_com_horas if dias_com_horas else 0.0
                ),
            }

        return medias_por_usuario

    def _calcular_media_geral(self) -> Dict[str, Any]:
        """Calcula métricas médias considerando todos os usuários."""
        total_itens_geral = sum(
            valor.get("itens", 0.0) for valor in self.totais_por_usuario.values()
        )
        total_os_geral = sum(
            valor.get("os", 0.0) for valor in self.totais_por_usuario.values()
        )
        dias_totais_contagem = len(self.dias_totais)
        total_horas_geral = sum(info["total"] for info in self.horas_por_dia.values())
        dias_com_horas_geral = len(self.horas_por_dia)

        media_geral = {
            "dias_ativos": dias_totais_contagem,
            "itens_por_dia": (
                total_itens_geral / dias_totais_contagem
                if dias_totais_contagem
                else 0.0
            ),
            "os_por_dia": (
                total_os_geral / dias_totais_contagem if dias_totais_contagem else 0.0
            ),
            "dias_com_horas": dias_com_horas_geral,
            "horas_por_dia": (
                total_horas_geral / dias_com_horas_geral
                if dias_com_horas_geral
                else 0.0
            ),
        }
        return media_geral


def _converter_registro(modelo: db.RegistroModel) -> RegistroResumo | None:
    """Transforma um modelo ORM em ``RegistroResumo`` seguro para agregações."""
    data_base = modelo.data_processo or modelo.data_entrada
    if not data_base:
        return None

    tempo_segundos = db.tempo_corte_para_segundos(modelo.tempo_corte)
    return RegistroResumo(
        usuario=modelo.usuario,
        data_base=data_base,
        qtde_itens=int(modelo.qtde_itens or 0),
        valor_pedido=float(modelo.valor_pedido or 0.0),
        tempo_segundos=tempo_segundos,
    )


def _carregar_registros() -> Iterable[RegistroResumo]:
    """Percorre todos os bancos de usuários gerando ``RegistroResumo``."""
    for slug, _ in db.iter_user_databases():
        session = db.get_sessionmaker_for_slug(slug)()
        try:
            for modelo in session.execute(select(db.RegistroModel)).scalars():
                registro = _converter_registro(modelo)
                if registro:
                    yield registro
        finally:
            session.close()


def obter_metricas_dashboard() -> Dict[str, Any]:
    """Reúne métricas consolidadas para o dashboard administrativo."""
    acumulador = DashboardAccumulator()
    for registro in _carregar_registros():
        acumulador.acumular(registro)
    return acumulador.finalizar()
