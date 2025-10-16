"""Componentes auxiliares para widgets de UI."""

from .processos_autocomplete import AutocompleteManager
from .processos_data_service import (
    buscar_registros_filtrados,
    carregar_clientes_upper,
    listar_anos_disponiveis,
    listar_periodos_do_ano,
    obter_estatisticas_totais,
)
from .processos_filters import FiltroControls, criar_filtros
from .processos_form import ProcessoFormControls, criar_formulario
from .processos_layout import criar_coluna_rotulo, criar_layout_botao_padrao
from .processos_periodo import PeriodoFiltroController
from .processos_table import TabelaControls, criar_tabela, preencher_tabela
from .processos_table_edit import (
    LinhaProcessoEdicao,
    extrair_campos_linha,
    obter_registro_id,
    validar_edicao_celula,
)
from .processos_totais import TotaisControls, atualizar_totais, criar_totais

__all__ = [
    "buscar_registros_filtrados",
    "carregar_clientes_upper",
    "listar_anos_disponiveis",
    "listar_periodos_do_ano",
    "obter_estatisticas_totais",
    "AutocompleteManager",
    "FiltroControls",
    "criar_filtros",
    "ProcessoFormControls",
    "criar_formulario",
    "TabelaControls",
    "criar_tabela",
    "preencher_tabela",
    "LinhaProcessoEdicao",
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
