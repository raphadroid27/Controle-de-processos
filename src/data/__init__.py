"""Interface pública da camada de persistência baseada em SQLAlchemy."""

from __future__ import annotations
from src.core.tempo_corte import tempo_corte_para_segundos
from src.data.sessions import (ensure_user_database,
                               get_sessionmaker_for_slug,
                               get_shared_engine, get_shared_session,
                               inicializar_todas_tabelas,
                               iter_user_databases,
                               limpar_bancos_orfaos,
                               remover_banco_usuario)

from src.data.repositories.crud import (adicionar_lancamento,
                                        atualizar_lancamento, excluir_lancamento)
from src.data.models import (Lancamento, RegistroModel,
                             UsuarioModel)
from src.data.repositories.queries import (buscar_anos_unicos,
                                           buscar_clientes_unicos,
                                           buscar_estatisticas,
                                           buscar_estatisticas_completas,
                                           buscar_lancamentos_filtros_completos,
                                           buscar_meses_unicos,
                                           buscar_pedidos_unicos_por_usuario,
                                           buscar_periodos_faturamento_por_ano,
                                           buscar_periodos_faturamento_unicos,
                                           buscar_usuarios_unicos,
                                           limpar_caches_consultas)

# Aliases para compatibilidade
buscar_lancamentos_filtrados = buscar_lancamentos_filtros_completos
obter_estatisticas_gerais = buscar_estatisticas_completas

__all__ = [
    "Lancamento",
    "UsuarioModel",
    "RegistroModel",
    "adicionar_lancamento",
    "atualizar_lancamento",
    "excluir_lancamento",
    "buscar_lancamentos_filtros_completos",
    "buscar_estatisticas",
    "buscar_estatisticas_completas",
    "buscar_clientes_unicos",
    "buscar_pedidos_unicos_por_usuario",
    "buscar_usuarios_unicos",
    "buscar_meses_unicos",
    "buscar_anos_unicos",
    "buscar_periodos_faturamento_por_ano",
    "buscar_periodos_faturamento_unicos",
    "limpar_caches_consultas",
    "ensure_user_database",
    "iter_user_databases",
    "remover_banco_usuario",
    "get_shared_session",
    "get_shared_engine",
    "get_sessionmaker_for_slug",
    "inicializar_todas_tabelas",
    "limpar_bancos_orfaos",
    "tempo_corte_para_segundos",
]
