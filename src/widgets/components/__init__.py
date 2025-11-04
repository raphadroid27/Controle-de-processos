"""Componentes auxiliares para widgets de UI."""

from src.widgets.components.autocomplete import AutocompleteManager
from src.widgets.components.data_service import (
    buscar_registros_filtrados, carregar_clientes_upper,
    listar_anos_disponiveis, listar_periodos_do_ano, obter_estatisticas_totais)
from src.widgets.components.filters import (FiltroControls,
                                            criar_filtros)
from src.widgets.components.form import (PedidoFormControls,
                                         criar_formulario)
from src.widgets.components.layout import (criar_coluna_rotulo,
                                           criar_layout_botao_padrao)
from src.widgets.components.periodo import PeriodoFiltroController
from src.widgets.components.table import (TabelaControls,
                                          criar_tabela,
                                          preencher_tabela)
from src.widgets.components.table_edit import (LinhaPedidoEdicao,
                                               extrair_campos_linha,
                                               obter_registro_id,
                                               validar_edicao_celula)
from src.widgets.components.totais import (TotaisControls,
                                           atualizar_totais,
                                           criar_totais)

__all__ = [
    "buscar_registros_filtrados",
    "carregar_clientes_upper",
    "listar_anos_disponiveis",
    "listar_periodos_do_ano",
    "obter_estatisticas_totais",
    "AutocompleteManager",
    "FiltroControls",
    "criar_filtros",
    "PedidoFormControls",
    "criar_formulario",
    "TabelaControls",
    "criar_tabela",
    "preencher_tabela",
    "LinhaPedidoEdicao",
    "validar_edicao_celula",
    "extrair_campos_linha",
    "obter_registro_id",
    "PeriodoFiltroController",
    "criar_coluna_rotulo",
    "criar_layout_botao_padrao",
    "TotaisControls",
    "criar_totais",
    "atualizar_totais",
]
