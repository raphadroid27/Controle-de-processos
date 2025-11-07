"""Métodos para plotagem de gráficos no dashboard."""

from typing import TYPE_CHECKING, Any

import matplotlib as mpl
import pandas as pd  # pylint: disable=E0401
from matplotlib.ticker import FuncFormatter

from src.core.formatters import segundos_para_horas
from src.ui.styles import (
    _ACCENT_CYCLE,
    _AXES_EDGE,
    _AXES_FACE,
    _GRID_COLOR,
    _LEGEND_FACE,
    _TEXT_COLOR,
    METRIC_MAP,
)

if TYPE_CHECKING:
    from pandas import DataFrame, Series  # noqa: F401

    from .dashboard_dialog import DashboardDialog  # noqa: F401

# Rótulos para períodos de faturamento nos gráficos (quebrados em 2 linhas)
_ROTULOS_PERIODOS = [
    "26/12 a\n25/01",
    "26/01 a\n25/02",
    "26/02 a\n25/03",
    "26/03 a\n25/04",
    "26/04 a\n25/05",
    "26/05 a\n25/06",
    "26/06 a\n25/07",
    "26/07 a\n25/08",
    "26/08 a\n25/09",
    "26/09 a\n25/10",
    "26/10 a\n25/11",
    "26/11 a\n25/12",
]


class DashboardPlotting:
    """Classe auxiliar para métodos de plotagem."""

    # Configuração de métricas para plotagem
    METRIC_CONFIG = {
        "itens": ("qtde_itens", "Itens", "_int_tick_formatter"),
        "valor": (
            "valor_pedido",
            "Valor (R$)",
            "_currency_tick_formatter",
        ),
        "proposta": (
            "proposta",
            "Propostas",
            "_int_tick_formatter",
        ),
        "horas": (
            "tempo_segundos",
            "Horas",
            "_hours_tick_formatter",
        ),
    }

    @staticmethod
    def atualizar_graficos(dialog: "DashboardDialog") -> None:
        """Atualiza os gráficos com base nos filtros selecionados."""
        if dialog.df_registros.empty or not hasattr(dialog, "canvas"):
            return

        assert dialog.canvas is not None
        assert dialog.combo_grafico_metrica is not None

        df_filtrado = DashboardPlotting._obter_dados_grafico(dialog)

        fig = dialog.canvas.figure
        fig.clear()

        dialog.tooltip_annotation = None

        if df_filtrado.empty:
            DashboardPlotting._mostrar_mensagem_sem_dados(dialog, fig)
            return

        metrica_selecionada = dialog.combo_grafico_metrica.currentText()
        chave_metrica, _ = METRIC_MAP[metrica_selecionada]

        axes = DashboardPlotting._criar_area_graficos(fig)

        DashboardPlotting._plotar_metricas_em_barras(
            dialog, df_filtrado, axes, metrica_selecionada, chave_metrica
        )

        fig.tight_layout()
        dialog.canvas.draw_idle()

    @staticmethod
    def _obter_dados_grafico(dialog: "DashboardDialog") -> "DataFrame":
        df_total = dialog.df_registros.copy()
        usuario_filtro = None
        if hasattr(dialog, "combo_grafico_usuario"):
            assert dialog.combo_grafico_usuario is not None
            usuario_filtro = dialog.combo_grafico_usuario.currentData()

        if usuario_filtro:
            df_filtrado = df_total[df_total["usuario"] == usuario_filtro]
        else:
            df_filtrado = df_total

        return df_filtrado

    @staticmethod
    def _mostrar_mensagem_sem_dados(dialog: "DashboardDialog", fig) -> None:
        assert dialog.canvas is not None

        ax = fig.add_subplot(111)
        ax.axis("off")
        ax.text(
            0.5,
            0.5,
            "Sem dados para o filtro selecionado.",
            ha="center",
            va="center",
            color=_TEXT_COLOR,
        )
        dialog.canvas.draw_idle()

    @staticmethod
    def _criar_area_graficos(fig) -> dict[str, Any]:
        gs = fig.add_gridspec(2, 1, height_ratios=[1, 1])
        axes = {
            "metrica_mes": fig.add_subplot(gs[0, 0]),
            "metrica_ano": fig.add_subplot(gs[1, 0]),
        }

        for eixo in axes.values():
            DashboardPlotting._estilizar_axes(eixo)

        return axes

    @staticmethod
    def _plotar_metricas_em_barras(
        dialog: "DashboardDialog",
        df: "DataFrame",
        axes: dict[str, Any],
        titulo_metrica: str,
        chave_metrica: str,
    ) -> None:
        if chave_metrica not in DashboardPlotting.METRIC_CONFIG:
            return

        coluna_df, rotulo_y, formatter_name = DashboardPlotting.METRIC_CONFIG[
            chave_metrica
        ]
        formatter_func = getattr(DashboardPlotting, formatter_name)
        formatter = FuncFormatter(formatter_func)

        pivot = DashboardPlotting._build_monthly_pivot(
            dialog, df, coluna_df, para_graficos=True
        )

        if chave_metrica == "horas":
            pivot = pivot.apply(segundos_para_horas)

        DashboardPlotting._plot_grouped_bars(
            dialog,
            axes["metrica_mes"],
            pivot,
            titulo=f"{titulo_metrica} por mês",
            rotulo_y=rotulo_y,
            formatter=formatter,
        )

        serie_por_ano = df.groupby("ano")[coluna_df].sum().sort_index()
        if chave_metrica == "horas":
            serie_por_ano = serie_por_ano.apply(segundos_para_horas)
        DashboardPlotting._plot_simple_bar(
            axes["metrica_ano"],
            serie_por_ano,
            titulo=f"{titulo_metrica} por ano",
            rotulo_y=rotulo_y,
            formatter=formatter,
        )

    @staticmethod
    def _formatar_valor_tooltip(eixo, valor: float) -> str:
        """Formata um valor para o tooltip baseado no formatador do eixo Y."""
        formatter = eixo.yaxis.get_major_formatter()
        if isinstance(formatter, FuncFormatter):
            # Nossos formatters são (valor, pos)
            return formatter(valor, 0)
        # Fallback
        return f"{valor:,.2f}"

    @staticmethod
    def on_hover_grafico(dialog: "DashboardDialog", event) -> None:
        """Chamado quando o mouse se move sobre o canvas."""
        if not dialog.canvas:
            return

        # Limpa a anotação anterior se ela existir
        if dialog.tooltip_annotation:
            try:
                dialog.tooltip_annotation.remove()
            except (ValueError, AttributeError):
                pass  # Pode já ter sido removida
            dialog.tooltip_annotation = None

        if not event.inaxes:
            # Se o mouse saiu, apenas desenha a remoção
            dialog.canvas.draw_idle()
            return

        eixo = event.inaxes
        artista_encontrado = None

        # Apenas verifica barras (patches)
        for artista in eixo.patches:
            if (
                isinstance(artista, mpl.patches.Rectangle)
                and artista.contains(event)[0]
            ):
                artista_encontrado = artista
                break

        if artista_encontrado:
            valor = artista_encontrado.get_height()
            if valor == 0:  # Não mostra tooltip para valor 0
                dialog.canvas.draw_idle()
                return

            texto = DashboardPlotting._formatar_valor_tooltip(eixo, valor)

            # Posição da anotação
            x = artista_encontrado.get_x() + artista_encontrado.get_width() / 2.0
            y = artista_encontrado.get_y() + artista_encontrado.get_height()

            bbox_props = {
                "boxstyle": "round,pad=0.3",
                "fc": _LEGEND_FACE,
                "ec": _AXES_EDGE,
                "lw": 1,
                "alpha": 0.9,
            }
            dialog.tooltip_annotation = eixo.annotate(
                texto,
                xy=(x, y),
                xytext=(0, 10),  # 10 pontos acima
                textcoords="offset points",
                ha="center",
                va="bottom",
                color=_TEXT_COLOR,
                bbox=bbox_props,
                zorder=10,
            )

        dialog.canvas.draw_idle()

    @staticmethod
    def _estilizar_axes(ax) -> None:
        ax.set_facecolor(_AXES_FACE)
        for spine in ax.spines.values():
            spine.set_color(_AXES_EDGE)
        ax.tick_params(colors=_TEXT_COLOR)
        ax.yaxis.label.set_color(_TEXT_COLOR)
        ax.xaxis.label.set_color(_TEXT_COLOR)
        ax.title.set_color(_TEXT_COLOR)

    @staticmethod
    def _estilizar_legenda(legenda) -> None:
        if legenda is None:
            return
        legenda.get_frame().set_facecolor(_LEGEND_FACE)
        legenda.get_frame().set_edgecolor(_AXES_EDGE)
        for texto in legenda.get_texts():
            texto.set_color(_TEXT_COLOR)

    @staticmethod
    def _build_monthly_pivot(
        dialog: "DashboardDialog",
        df: "DataFrame",
        coluna: str,
        *,
        para_graficos: bool = False,
    ) -> "DataFrame":

        if pd is None:  # pragma: no cover - tratado na inicialização
            raise RuntimeError("Pandas não disponível para gerar o dashboard.")

        if df.empty:
            return pd.DataFrame()

        if para_graficos:
            # Para gráficos, usa todos os meses (1-12) para consistência
            meses = list(range(1, 13))
        else:
            # Para tabelas, usa os períodos do ano selecionado
            meses = [p["numero"] for p in dialog.periodos_atuais]

        pivot = (
            df.pivot_table(
                index="ano",
                columns="mes",
                values=coluna,
                aggfunc="sum",
                fill_value=0,
            )
            .sort_index()
            .reindex(columns=meses, fill_value=0)
        )
        return pivot

    @staticmethod
    def _plot_grouped_bars(
        dialog: "DashboardDialog",
        ax,
        pivot: "DataFrame",
        *,
        titulo: str,
        rotulo_y: str,
        formatter: FuncFormatter,
    ) -> None:
        ax.clear()
        ax.set_title(titulo)
        ax.set_ylabel(rotulo_y)

        if pivot.empty or pivot.to_numpy().sum() == 0:
            ax.axis("off")
            ax.text(
                0.5,
                0.5,
                "Sem dados",
                ha="center",
                va="center",
                color=_TEXT_COLOR,
            )
            return

        colunas_meses, rotulos_meses = DashboardPlotting._obter_meses_presentes(
            dialog, pivot, para_graficos=True
        )

        if not colunas_meses:
            ax.axis("off")
            ax.text(
                0.5,
                0.5,
                "Sem dados",
                ha="center",
                va="center",
                color=_TEXT_COLOR,
            )
            return

        num_anos = max(len(pivot.index), 1)
        largura = 0.8 / num_anos
        deslocamento_inicial = -((num_anos - 1) * largura) / 2

        base = DashboardPlotting._desenhar_barras_por_ano(
            ax=ax,
            pivot=pivot,
            colunas_meses=colunas_meses,
            largura=largura,
            deslocamento_inicial=deslocamento_inicial,
        )

        ax.set_xticks(base)
        ax.set_xticklabels(rotulos_meses, fontsize=8)
        ax.yaxis.set_major_formatter(formatter)
        ax.grid(True, axis="y", linestyle="--", color=_GRID_COLOR, alpha=0.4)
        legenda = ax.legend(loc="upper left", fontsize="small")
        DashboardPlotting._estilizar_legenda(legenda)
        DashboardPlotting._estilizar_axes(ax)

    @staticmethod
    def _obter_meses_presentes(
        dialog: "DashboardDialog",
        pivot: "DataFrame",
        *,
        para_graficos: bool = False,
    ) -> tuple[list[int], list[str]]:
        colunas: list[int] = []
        rotulos: list[str] = []

        if para_graficos:
            # Rótulos curtos para gráficos (quebrados em 2 linhas)
            rotulos_periodos = _ROTULOS_PERIODOS
        else:
            # Para tabelas, usa os períodos do ano selecionado
            rotulos_periodos = dialog.rotulos_periodos

        for mes in range(1, 13):
            if mes in pivot.columns and mes - 1 < len(rotulos_periodos):
                colunas.append(mes)
                rotulos.append(rotulos_periodos[mes - 1])
        return colunas, rotulos

    @staticmethod
    def _desenhar_barras_por_ano(
        *,
        ax,
        pivot: "DataFrame",
        colunas_meses: list[int],
        largura: float,
        deslocamento_inicial: float,
    ) -> list[int]:
        base = list(range(len(colunas_meses)))
        for indice_ano, ano in enumerate(pivot.index.tolist()):
            valores = pivot.loc[ano, colunas_meses].values
            posicoes = [
                indice + deslocamento_inicial + indice_ano * largura for indice in base
            ]
            ax.bar(posicoes, valores, width=largura, label=str(ano))
        return base

    @staticmethod
    def _plot_simple_bar(
        ax,
        serie: "Series",
        *,
        titulo: str,
        rotulo_y: str,
        formatter: FuncFormatter,
    ) -> None:
        ax.clear()
        ax.set_title(titulo)
        ax.set_ylabel(rotulo_y)

        if serie.empty or serie.sum() == 0:
            ax.axis("off")
            ax.text(
                0.5,
                0.5,
                "Sem dados",
                ha="center",
                va="center",
                color=_TEXT_COLOR,
            )
            return

        ax.bar(serie.index.astype(str), serie.values, color=_ACCENT_CYCLE[0])
        ax.tick_params(axis='x', labelsize=9)
        ax.yaxis.set_major_formatter(formatter)
        ax.grid(True, axis="y", linestyle="--", color=_GRID_COLOR, alpha=0.4)
        DashboardPlotting._estilizar_axes(ax)

    @staticmethod
    def _int_tick_formatter(valor: float, _pos: int) -> str:
        valor_arredondado = int(round(valor))
        if valor_arredondado < 0:
            return ""
        return f"{valor_arredondado:,}".replace(",", ".")

    @staticmethod
    def _currency_tick_formatter(valor: float, _pos: int) -> str:
        return f"R$ {valor:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @staticmethod
    def _hours_tick_formatter(valor: float, _pos: int) -> str:
        return f"{valor:.1f}h"
