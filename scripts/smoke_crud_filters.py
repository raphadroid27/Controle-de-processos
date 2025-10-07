"""Script de teste para operações CRUD e filtros no banco de dados."""

import os
import sys
from datetime import datetime

# Importações com fallback para execução direta sem PYTHONPATH configurado
try:
    from utils import database as db
    from utils.periodo_faturamento import (
        calcular_periodo_faturamento_atual_datas,
    )
except ImportError:  # pragma: no cover - ajuste para ambientes locais
    CURR_DIR = os.path.dirname(__file__)
    REPO_ROOT = os.path.abspath(os.path.join(CURR_DIR, os.pardir))
    SRC_DIR = os.path.join(REPO_ROOT, "src")
    if SRC_DIR not in sys.path:
        sys.path.insert(0, SRC_DIR)
    from utils import database as db  # type: ignore  # noqa: E402
    from utils.periodo_faturamento import (  # type: ignore  # noqa: E402
        calcular_periodo_faturamento_atual_datas,
    )


def run():
    """Executa uma série de operações CRUD e filtros para testar o banco de dados."""
    print("--- Smoke CRUD & Filtros ---")
    usuarios = db.buscar_usuarios_unicos()
    print("Usuarios existentes:", usuarios)

    # Inserção
    hoje = datetime.now().strftime("%Y-%m-%d")
    msg = db.adicionar_lancamento(
        usuario="SMOKE",
        cliente="CLIENTE_X",
        processo="PROC_X",
        qtde_itens="1",
        data_entrada=hoje,
        data_processo="",
        valor_pedido="10,50",
        tempo_corte="01:00:00",
    )
    print("Add:", msg)

    regs = db.buscar_lancamentos_filtros_completos(usuario="SMOKE")
    print("Qtde registros SMOKE:", len(regs))

    if regs:
        rid = regs[-1][0]
        up = db.atualizar_lancamento(
            rid,
            cliente="CLIENTE_X",
            processo="PROC_X",
            qtde_itens="2",
            data_entrada=hoje,
            data_processo="",
            valor_pedido="20,00",
            tempo_corte="02:30:00",
        )
        print("Update:", up)

        stats = db.buscar_estatisticas_completas(usuario="SMOKE")
        print("Stats:", stats)

        delmsg = db.excluir_lancamento(rid)
        print("Delete:", delmsg)

    # Filtros por período atual
    ini, fim = calcular_periodo_faturamento_atual_datas()
    regs_periodo = db.buscar_lancamentos_filtros_completos(
        data_inicio=ini.strftime("%Y-%m-%d"), data_fim=fim.strftime("%Y-%m-%d")
    )
    print("Qtde no período atual:", len(regs_periodo))
    print("--- Fim Smoke ---")


if __name__ == "__main__":
    run()
