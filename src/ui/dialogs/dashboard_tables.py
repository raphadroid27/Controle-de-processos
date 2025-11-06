"""Métodos para atualização de tabelas no dashboard."""

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidgetItem

from src import data as db
from src.core.formatters import (formatar_data_para_exibicao,
                                  formatar_numero_decimal, formatar_segundos,
                                  formatar_valor_monetario)
from src.ui.styles import METRIC_MAP

if TYPE_CHECKING:
    from .dashboard_dialog import DashboardDialog


class DashboardTableUpdates:
    """Classe auxiliar para métodos de atualização de tabelas."""

    @staticmethod
    def atualizar_tabela_mensal(dialog: "DashboardDialog") -> None:
        """Atualiza a tabela mensal com dados do ano e métrica selecionados."""
        assert dialog.combo_ano is not None
        assert dialog.combo_metrica is not None
        assert dialog.tabela_mensal is not None

        ano_texto = dialog.combo_ano.currentText()
        if not ano_texto:
            dialog.tabela_mensal.setRowCount(0)
            return

        chave_metrica, _ = METRIC_MAP[dialog.combo_metrica.currentText()]
        ano = int(ano_texto)
        dados_ano = dialog.metricas.get("dados_mensais", {}).get(ano, {})

        # Obter e configurar períodos
        DashboardTableUpdates._configurar_periodos(dialog, ano)

        # Configurar estrutura da tabela
        DashboardTableUpdates._configurar_estrutura_tabela(dialog)

        # Preencher dados
        DashboardTableUpdates._preencher_dados_tabela(
            dialog, dados_ano, chave_metrica)

    @staticmethod
    def _configurar_periodos(dialog: "DashboardDialog", ano: int) -> None:
        """Configura os períodos para o ano selecionado."""
        periodos = db.buscar_periodos_faturamento_por_ano(str(ano))
        periodos.sort(key=lambda p: p["inicio"])
        dialog.periodos_atuais = periodos
        dialog.rotulos_periodos = [p["display"] for p in periodos]

    @staticmethod
    def _configurar_estrutura_tabela(dialog: "DashboardDialog") -> None:
        """Configura a estrutura básica da tabela mensal."""
        num_periodos = len(dialog.rotulos_periodos)
        dialog.tabela_mensal.setColumnCount(num_periodos + 1)
        dialog.tabela_mensal.setHorizontalHeaderLabels(
            dialog.rotulos_periodos + ["Total"]
        )
        row_count = len(dialog.usuarios) + 1  # +1 para linha de totais
        dialog.tabela_mensal.setRowCount(row_count)

    @staticmethod
    def _preencher_dados_tabela(
        dialog: "DashboardDialog", dados_ano: dict, chave_metrica: str
    ) -> None:
        """Preenche os dados na tabela mensal."""
        # Preencher dados por usuário
        for row, usuario in enumerate(dialog.usuarios):
            dialog.tabela_mensal.setVerticalHeaderItem(
                row, QTableWidgetItem(usuario))
            DashboardTableUpdates._preencher_linha_usuario(
                dialog, dados_ano, chave_metrica, row, usuario
            )

        # Linha de totais
        total_row = len(dialog.usuarios)
        dialog.tabela_mensal.setVerticalHeaderItem(
            total_row, QTableWidgetItem("Total"))
        DashboardTableUpdates._preencher_linha_totais(
            dialog, dados_ano, chave_metrica, total_row
        )

    @staticmethod
    def _preencher_linha_usuario(
        dialog: "DashboardDialog",
        dados_ano: dict,
        chave_metrica: str,
        row: int,
        usuario: str,
    ) -> float:
        """Preenche uma linha de dados para um usuário específico."""
        total_usuario = 0.0
        num_periodos = len(dialog.rotulos_periodos)

        for col, periodo in enumerate(dialog.periodos_atuais):
            valor = (
                dados_ano.get(usuario, {})
                .get(periodo["numero"], {})
                .get(chave_metrica, 0)
            )
            total_usuario += valor
            dialog.tabela_mensal.setItem(
                row,
                col,
                DashboardTableUpdates._criar_item_tabela(
                    DashboardTableUpdates._formatar_valor_metrica(
                        chave_metrica, valor)
                ),
            )

        dialog.tabela_mensal.setItem(
            row,
            num_periodos,
            DashboardTableUpdates._criar_item_tabela(
                DashboardTableUpdates._formatar_valor_metrica(
                    chave_metrica, total_usuario
                )
            ),
        )
        return total_usuario

    @staticmethod
    def _preencher_linha_totais(
        dialog: "DashboardDialog", dados_ano: dict, chave_metrica: str, total_row: int
    ) -> None:
        """Preenche a linha de totais da tabela."""
        num_periodos = len(dialog.rotulos_periodos)

        for col, periodo in enumerate(dialog.periodos_atuais):
            total_mes = sum(
                dados_ano.get(usuario, {})
                .get(periodo["numero"], {})
                .get(chave_metrica, 0)
                for usuario in dialog.usuarios
            )
            dialog.tabela_mensal.setItem(
                total_row,
                col,
                DashboardTableUpdates._criar_item_tabela(
                    DashboardTableUpdates._formatar_valor_metrica(
                        chave_metrica, total_mes
                    )
                ),
            )

        total_geral = sum(
            dados_ano.get(usuario, {}).get(
                periodo["numero"], {}).get(chave_metrica, 0)
            for usuario in dialog.usuarios
            for periodo in dialog.periodos_atuais
        )
        dialog.tabela_mensal.setItem(
            total_row,
            num_periodos,
            DashboardTableUpdates._criar_item_tabela(
                DashboardTableUpdates._formatar_valor_metrica(
                    chave_metrica, total_geral
                )
            ),
        )

    @staticmethod
    def atualizar_tabela_totais(dialog: "DashboardDialog") -> None:
        """Atualiza a tabela de totais por ano."""
        assert dialog.tabela_totais is not None

        totais = dialog.metricas.get("totais_ano", {})
        anos_ordenados = sorted(totais.keys())
        dialog.tabela_totais.setRowCount(len(anos_ordenados))

        for row, ano in enumerate(anos_ordenados):
            dados = totais.get(ano, {})
            dialog.tabela_totais.setItem(
                row,
                0,
                DashboardTableUpdates._criar_item_tabela(
                    str(ano), alinhamento=Qt.AlignmentFlag.AlignCenter
                ),
            )
            dialog.tabela_totais.setItem(
                row,
                1,
                DashboardTableUpdates._criar_item_tabela(
                    str(int(dados.get("itens", 0)))
                ),
            )
            dialog.tabela_totais.setItem(
                row,
                2,
                DashboardTableUpdates._criar_item_tabela(
                    formatar_valor_monetario(dados.get("valor", 0.0))
                ),
            )
            dialog.tabela_totais.setItem(
                row,
                3,
                DashboardTableUpdates._criar_item_tabela(
                    str(int(dados.get("proposta", 0)))
                ),
            )
            dialog.tabela_totais.setItem(
                row,
                4,
                DashboardTableUpdates._criar_item_tabela(
                    formatar_segundos(dados.get("horas", 0))
                ),
            )

    @staticmethod
    def atualizar_tabela_medias(dialog: "DashboardDialog") -> None:
        """Atualiza a tabela de médias por usuário."""
        assert dialog.tabela_medias is not None

        medias = dialog.metricas.get("medias_por_usuario", {})
        media_geral = dialog.metricas.get("media_geral", {})

        row_count = len(dialog.usuarios) + 1 if medias else 0
        dialog.tabela_medias.setRowCount(row_count)

        for row, usuario in enumerate(dialog.usuarios):
            dados = medias.get(
                usuario,
                {
                    "dias_ativos": 0,
                    "itens_por_dia": 0.0,
                    "proposta_por_dia": 0.0,
                    "dias_com_horas": 0,
                    "horas_por_dia": 0.0,
                },
            )

            valores = [
                usuario,
                formatar_numero_decimal(dados.get("itens_por_dia", 0.0)),
                formatar_numero_decimal(dados.get("proposta_por_dia", 0.0)),
                formatar_segundos(dados.get("horas_por_dia", 0)),
            ]

            for col, texto in enumerate(valores):
                alinhamento = (
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                    if col == 0
                    else Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                dialog.tabela_medias.setItem(
                    row,
                    col,
                    DashboardTableUpdates._criar_item_tabela(
                        texto, alinhamento=alinhamento
                    ),
                )

        if row_count:
            total_row = len(dialog.usuarios)
            valores_total = [
                "Todos",
                formatar_numero_decimal(media_geral.get("itens_por_dia", 0.0)),
                formatar_numero_decimal(
                    media_geral.get("proposta_por_dia", 0.0)),
                formatar_segundos(media_geral.get("horas_por_dia", 0)),
            ]

            for col, texto in enumerate(valores_total):
                alinhamento = (
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                    if col == 0
                    else Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                dialog.tabela_medias.setItem(
                    total_row,
                    col,
                    DashboardTableUpdates._criar_item_tabela(
                        texto, alinhamento=alinhamento
                    ),
                )

    @staticmethod
    def atualizar_tabela_horas(dialog: "DashboardDialog") -> None:
        """Atualiza a tabela de horas por dia."""
        assert dialog.combo_intervalo is not None
        assert dialog.label_total_horas is not None
        assert dialog.tabela_horas is not None

        dados_horas = dialog.metricas.get("horas_por_dia", {})
        dias_ordenados = list(dados_horas.keys())
        if not dias_ordenados:
            dialog.tabela_horas.setRowCount(0)
            dialog.label_total_horas.setText(
                "Nenhuma informação de tempo de corte disponível."
            )
            return

        dias_limite = dialog.combo_intervalo.currentData()
        if dias_limite:
            dias_exibidos = dias_ordenados[:dias_limite]
        else:
            dias_exibidos = dias_ordenados

        colunas = ["Data"] + dialog.usuarios + ["Total"]
        dialog.tabela_horas.setColumnCount(len(colunas))
        dialog.tabela_horas.setHorizontalHeaderLabels(colunas)
        dialog.tabela_horas.setRowCount(len(dias_exibidos))

        total_periodo = 0

        for row, dia in enumerate(dias_exibidos):
            info = dados_horas[dia]
            total_periodo += info.get("total", 0)
            dialog.tabela_horas.setItem(
                row,
                0,
                DashboardTableUpdates._criar_item_tabela(
                    formatar_data_para_exibicao(dia),
                    alinhamento=Qt.AlignmentFlag.AlignCenter,
                ),
            )
            for col, usuario in enumerate(dialog.usuarios, start=1):
                segundos = info.get("por_usuario", {}).get(usuario, 0)
                dialog.tabela_horas.setItem(
                    row,
                    col,
                    DashboardTableUpdates._criar_item_tabela(
                        formatar_segundos(segundos)
                    ),
                )
            dialog.tabela_horas.setItem(
                row,
                len(colunas) - 1,
                DashboardTableUpdates._criar_item_tabela(
                    formatar_segundos(info.get("total", 0))
                ),
            )

        dialog.label_total_horas.setText(
            f"Total acumulado no período: {formatar_segundos(total_periodo)}"
        )

    @staticmethod
    def _criar_item_tabela(
        texto: str,
        alinhamento: int = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
    ) -> QTableWidgetItem:
        item = QTableWidgetItem(texto)
        item.setTextAlignment(alinhamento)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item

    @staticmethod
    def _formatar_valor_metrica(chave: str, valor) -> str:
        formatters = {
            "valor": formatar_valor_monetario,
            "horas": lambda v: formatar_segundos(int(round(v))),
        }
        formatter = formatters.get(chave)
        if formatter:
            return formatter(valor)
        return f"{int(round(valor)):,}".replace(",", ".")
