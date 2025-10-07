"""Popula bancos individuais com dados fictícios para testes."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable, List
import random

from src.utils import database as db

CLIENTES = [
    "ACME Engenharia",
    "Beta Construções",
    "Cidade Planejada",
    "Delta Projetos",
    "Estilo Arquitetura",
    "Futura Urbanismo",
    "Green Homes",
    "Habitar Engenharia",
    "Inova Projetos",
    "Júpiter Construções",
    "Kairós Design",
    "Lótus Empreendimentos",
]

TIPOS_PROCESSO = [
    "Residencial",
    "Comercial",
    "Industrial",
    "Reforma",
    "Ampliação",
    "Regularização",
    "Estrutural",
]

ESCOPOS = [
    "Pré-projeto",
    "Projeto executivo",
    "Consultoria técnica",
    "Aprovação prefeitura",
    "Revisão layout",
    "Compatibilização",
]


@dataclass
class Config:
    seed: int
    registros_por_mes: int
    anos: List[int]


def _gerar_tempo_corte(rng: random.Random) -> str:
    if rng.random() < 0.25:
        return ""

    horas = rng.randint(0, 5)
    minutos = rng.randint(0, 59)
    segundos = rng.randint(0, 59)
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"


def _meses_para_ano(ano: int, hoje: date) -> Iterable[int]:
    if ano < hoje.year:
        return range(1, 13)
    limite = max(1, min(12, hoje.month))
    return range(1, limite + 1)


def _montar_nome_processo(usuario: str, ano: int, mes: int, sequencial: int) -> str:
    prefixo = "".join(
        caractere
        for caractere in usuario.upper()
        if caractere.isalnum()
    )[:5]
    if not prefixo:
        prefixo = "USR"
    return f"{prefixo}-{ano}{mes:02d}-{sequencial:03d}"


def _gerar_registros_para_usuario(
    usuario: str,
    cfg: Config,
    *,
    hoje: date,
) -> int:
    rng = random.Random(cfg.seed + hash(usuario) % 10_000)
    existentes = set(db.buscar_processos_unicos_por_usuario(usuario))
    inseridos = 0
    sequencial = 1

    for ano in cfg.anos:
        for mes in _meses_para_ano(ano, hoje):
            for _ in range(cfg.registros_por_mes):
                processo = _montar_nome_processo(usuario, ano, mes, sequencial)
                sequencial += 1
                if processo in existentes:
                    continue

                dia = rng.randint(1, 28)
                data_processo = date(ano, mes, dia)
                delta_dias = rng.randint(0, 5)
                data_entrada = data_processo - timedelta(days=delta_dias)
                cliente = rng.choice(CLIENTES)
                descricao = rng.choice(TIPOS_PROCESSO)
                escopo = rng.choice(ESCOPOS)
                processo_rotulo = f"{processo} | {escopo}"
                qtde_itens = rng.randint(1, 40)
                valor = round(rng.uniform(150.0, 7500.0), 2)
                tempo_corte = _gerar_tempo_corte(rng)

                if processo_rotulo in existentes:
                    continue

                resultado = db.adicionar_lancamento(
                    usuario=usuario,
                    cliente=f"{cliente} ({descricao})",
                    processo=processo_rotulo,
                    qtde_itens=str(qtde_itens),
                    data_entrada=data_entrada.isoformat(),
                    data_processo=data_processo.isoformat(),
                    valor_pedido=f"{valor:.2f}",
                    tempo_corte=tempo_corte,
                )

                if resultado.startswith("Sucesso"):
                    inseridos += 1
                    existentes.add(processo_rotulo)
                else:
                    print(
                        f"[WARN] {usuario}: falha ao inserir {processo}: {resultado}")

    return inseridos


def popular_dados(cfg: Config) -> None:
    usuarios = db.buscar_usuarios_unicos()
    if not usuarios:
        print("Nenhum usuário cadastrado no sistema compartilhado.")
        return

    hoje = date.today()
    total = 0

    for usuario in usuarios:
        db.ensure_user_database(usuario)
        inseridos = _gerar_registros_para_usuario(usuario, cfg, hoje=hoje)
        total += inseridos
        print(f"Usuário {usuario}: +{inseridos} registros fictícios")

    print("-" * 60)
    print(
        f"Total inserido: {total} registros gerados para {len(usuarios)} usuários.")


def _parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description="Gera dados fictícios (2023-2025) para todos os bancos individuais."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=2025,
        help="Semente para geração pseudoaleatória (padrão: 2025)",
    )
    parser.add_argument(
        "--registros-por-mes",
        type=int,
        default=3,
        help="Quantidade de registros gerados por mês e por usuário (padrão: 3)",
    )
    args = parser.parse_args()
    anos = [2023, 2024, 2025]
    return Config(seed=args.seed, registros_por_mes=args.registros_por_mes, anos=anos)


def main() -> None:
    cfg = _parse_args()
    popular_dados(cfg)


if __name__ == "__main__":
    main()
