"""Dialogo de dashboard administrativo."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import matplotlib as mpl
from cycler import cycler

try:  # pragma: no cover - fallback executado apenas sem pandas instalado
    import pandas as pd  # type: ignore[assignment]
except ImportError:  # pragma: no cover
    pd = None  # type: ignore[assignment]
    if TYPE_CHECKING:  # pragma: no cover - apenas para análise estática
        from pandas import DataFrame, Series  # pylint: disable=import-error
    else:
        DataFrame = Any  # type: ignore[assignment]
        Series = Any  # type: ignore[assignment]
else:
    from pandas import DataFrame, Series

from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QDialog, QHBoxLayout, QHeaderView,
                               QLabel, QTableWidget, QTableWidgetItem,
                               QTabWidget, QVBoxLayout, QWidget)

from src.utils.dashboard_metrics import obter_metricas_dashboard
from src.utils.formatters import (formatar_data_para_exibicao,
                                  formatar_valor_monetario)
from src.utils.ui_config import aplicar_icone_padrao

_FIGURE_FACE = "#202124"
_AXES_FACE = "#2b3138"
_AXES_EDGE = "#4a4d52"
_TEXT_COLOR = "#f1f3f4"
_GRID_COLOR = "#3c4043"
_LEGEND_FACE = "#262c33"
_ACCENT_CYCLE = [
    "#4CAF50",
    "#5BC0EB",
    "#F5A623",
    "#9C27B0",
    "#E91E63",
    "#00ACC1",
]

mpl.rcParams.update(
    {
        "figure.facecolor": _FIGURE_FACE,
        "figure.edgecolor": _FIGURE_FACE,
        "axes.facecolor": _AXES_FACE,
        "axes.edgecolor": _AXES_EDGE,
        "axes.labelcolor": _TEXT_COLOR,
        "axes.titlecolor": _TEXT_COLOR,
        "xtick.color": _TEXT_COLOR,
        "ytick.color": _TEXT_COLOR,
        "text.color": _TEXT_COLOR,
        "grid.color": _GRID_COLOR,
        "legend.facecolor": _LEGEND_FACE,
        "legend.edgecolor": _AXES_EDGE,
        "savefig.facecolor": _FIGURE_FACE,
        "savefig.edgecolor": _FIGURE_FACE,
        "axes.prop_cycle": cycler(color=_ACCENT_CYCLE),
    }
)


class MatplotlibCanvas(FigureCanvas):
    """Canvas helper para integrar gráficos do Matplotlib ao Qt."""

    def __init__(self, width: float = 12, height: float = 9, dpi: int = 100):
        """Inicializa o canvas do Matplotlib com as dimensões especificadas."""
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        self.figure.patch.set_facecolor(_FIGURE_FACE)
        super().__init__(self.figure)


class DashboardDialog(QDialog):
    """Exibe métricas agregadas para administradores."""

    _METRIC_MAP = {
        "Itens": ("itens", int),
        "Valor (R$)": ("valor", float),
        "Propostas": ("proposta", int),
    }

    _MESES = [
        (1, "Jan"),
        (2, "Fev"),
        (3, "Mar"),
        (4, "Abr"),
        (5, "Mai"),
        (6, "Jun"),
        (7, "Jul"),
        (8, "Ago"),
        (9, "Set"),
        (10, "Out"),
        (11, "Nov"),
        (12, "Dez"),
    ]

    _INTERVALOS = [
        (7, "Últimos 7 dias"),
        (15, "Últimos 15 dias"),
        (30, "Últimos 30 dias"),
        (90, "Últimos 90 dias"),
        (0, "Todos os registros"),
    ]

    def __init__(self, parent=None):
        """Inicializa o diálogo do dashboard com configurações padrão."""
        super().__init__(parent)
        self._configurar_janela()
        self.metricas: dict[str, Any] = {}
        self.usuarios: list[str] = []
        self.anos: list[int] = []
        self.df_registros = pd.DataFrame() if pd is not None else None
        self.tabs: QTabWidget | None = None
        self.combo_ano: QComboBox | None = None
        self.combo_metrica: QComboBox | None = None
        self.tabela_mensal: QTableWidget | None = None
        self.tabela_totais: QTableWidget | None = None
        self.tabela_medias: QTableWidget | None = None
        self.combo_intervalo: QComboBox | None = None
        self.label_total_horas: QLabel | None = None
        self.tabela_horas: QTableWidget | None = None
        self.tab_graficos: QWidget | None = None
        self.combo_grafico_usuario: QComboBox | None = None
        self.canvas: MatplotlibCanvas | None = None

        if self._exibir_aviso_sem_pandas():
            return

        self._carregar_metricas()
        self._preparar_dataframe_registros()

        if not self.anos:
            self._exibir_aviso_sem_dados()
            return

        self._criar_abas()
        self._atualizar_resumos()

    def _configurar_janela(self) -> None:
        self.setWindowTitle("Dashboard Administrativo")
        self.resize(1100, 700)
        self.setWindowFlag(Qt.WindowType.Window, True)
        self.setWindowFlag(Qt.WindowType.WindowSystemMenuHint, True)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, True)
        self.setSizeGripEnabled(True)

        # Aplicar ícone padrão
        aplicar_icone_padrao(self)

    def _exibir_aviso_sem_pandas(self) -> bool:
        if pd is not None:
            return False
        layout = QVBoxLayout()
        layout.addWidget(
            QLabel(
                "A biblioteca pandas não está instalada. Instale o pacote 'pandas' "
                "para visualizar o dashboard administrativo."
            )
        )
        self.setLayout(layout)
        return True

    def _carregar_metricas(self) -> None:
        self.metricas = obter_metricas_dashboard()
        self.usuarios = self.metricas.get("usuarios", [])
        self.anos = self.metricas.get("anos", [])
        self.df_registros = pd.DataFrame(self.metricas.get("registros", []))

    def _preparar_dataframe_registros(self) -> None:
        if self.df_registros.empty:
            self.df_registros = pd.DataFrame()
            return

        self.df_registros["data"] = pd.to_datetime(
            self.df_registros["data"], errors="coerce"
        )
        self.df_registros = self.df_registros.dropna(subset=["data"])
        self.df_registros["ano"] = (
            pd.to_numeric(self.df_registros["ano"], errors="coerce")
            .fillna(0)
            .astype(int)
        )
        self.df_registros["mes"] = self.df_registros["data"].dt.month.astype(
            int)
        self.df_registros["qtde_itens"] = pd.to_numeric(
            self.df_registros["qtde_itens"], errors="coerce"
        ).fillna(0)
        self.df_registros["valor_pedido"] = pd.to_numeric(
            self.df_registros["valor_pedido"], errors="coerce"
        ).fillna(0.0)
        self.df_registros["proposta"] = pd.to_numeric(
            self.df_registros.get("proposta", 1), errors="coerce"
        ).fillna(0)
        self.df_registros["tempo_segundos"] = (
            pd.to_numeric(self.df_registros["tempo_segundos"], errors="coerce")
            .fillna(0)
            .astype(int)
        )
        self.df_registros["tempo_horas"] = self.df_registros["tempo_segundos"] / 3600.0

    def _exibir_aviso_sem_dados(self) -> None:
        layout = QVBoxLayout()
        layout.addWidget(
            QLabel("Não há dados suficientes para montar o dashboard no momento.")
        )
        self.setLayout(layout)

    def _criar_abas(self) -> None:
        self.tabs = QTabWidget()
        self.tabs.addTab(self._criar_tab_resumo(), "Resumo")
        if not self.df_registros.empty:
            self._criar_tab_graficos()

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def _atualizar_resumos(self) -> None:
        self._atualizar_tabela_totais()
        self._atualizar_tabela_mensal()
        self._atualizar_tabela_medias()
        self._atualizar_tabela_horas()
        if not self.df_registros.empty:
            self._atualizar_graficos()

    # ------------------------------------------------------------------
    # Construção das abas
    # ------------------------------------------------------------------

    def _criar_tab_resumo(self) -> QWidget:
        tab_resumo = QWidget()
        layout = QVBoxLayout(tab_resumo)

        self._adicionar_controles_resumo(layout)
        self._adicionar_paineis_resumo(layout)
        self._adicionar_secao_horas(layout)

        return tab_resumo

    def _adicionar_controles_resumo(self, layout: QVBoxLayout) -> None:
        layout.addLayout(self._montar_controles_resumo())
        layout.addWidget(self._criar_tabela_mensal())

    def _adicionar_paineis_resumo(self, layout: QVBoxLayout) -> None:
        layout.addLayout(self._montar_tabelas_resumo())
        layout.addSpacing(12)

    def _montar_controles_resumo(self) -> QHBoxLayout:
        controles_layout = QHBoxLayout()
        controles_layout.addWidget(QLabel("Ano:"))

        self.combo_ano = QComboBox()
        for ano in self.anos:
            self.combo_ano.addItem(str(ano))
        self.combo_ano.currentTextChanged.connect(
            self._atualizar_tabela_mensal)
        controles_layout.addWidget(self.combo_ano)

        controles_layout.addSpacing(16)
        controles_layout.addWidget(QLabel("Métrica:"))
        self.combo_metrica = QComboBox()
        for titulo in self._METRIC_MAP:
            self.combo_metrica.addItem(titulo)
        self.combo_metrica.currentTextChanged.connect(
            self._atualizar_tabela_mensal)
        controles_layout.addWidget(self.combo_metrica)
        controles_layout.addStretch()
        return controles_layout

    def _criar_tabela_mensal(self) -> QTableWidget:
        self.tabela_mensal = QTableWidget()
        self.tabela_mensal.setColumnCount(len(self._MESES) + 1)
        self.tabela_mensal.setHorizontalHeaderLabels(
            [nome for _, nome in self._MESES] + ["Total"]
        )
        self.tabela_mensal.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.tabela_mensal.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela_mensal.setAlternatingRowColors(True)
        return self.tabela_mensal

    def _montar_tabelas_resumo(self) -> QHBoxLayout:
        tabelas_layout = QHBoxLayout()

        totais_layout = QVBoxLayout()
        totais_layout.addWidget(QLabel("Totais por ano"))
        self.tabela_totais = QTableWidget()
        self.tabela_totais.setColumnCount(4)
        self.tabela_totais.setHorizontalHeaderLabels(
            ["Ano", "Itens", "Valor (R$)", "Propostas"]
        )
        self.tabela_totais.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.tabela_totais.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela_totais.setAlternatingRowColors(True)
        totais_layout.addWidget(self.tabela_totais)

        medias_layout = QVBoxLayout()
        medias_layout.addWidget(QLabel("Médias por dia (por desenhista)"))
        self.tabela_medias = QTableWidget()
        self.tabela_medias.setColumnCount(4)
        self.tabela_medias.setHorizontalHeaderLabels(
            [
                "Usuário",
                "Itens/dia",
                "Propostas/dia",
                "Horas/dia",
            ]
        )
        self.tabela_medias.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.tabela_medias.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela_medias.setAlternatingRowColors(True)
        medias_layout.addWidget(self.tabela_medias)

        tabelas_layout.addLayout(totais_layout)
        tabelas_layout.addLayout(medias_layout)
        return tabelas_layout

    def _adicionar_secao_horas(self, layout: QVBoxLayout) -> None:
        horas_header_layout = QHBoxLayout()
        horas_header_layout.addWidget(QLabel("Horas de corte por dia"))
        horas_header_layout.addStretch()
        layout.addLayout(horas_header_layout)

        horas_controles_layout = QHBoxLayout()
        horas_controles_layout.addWidget(QLabel("Intervalo:"))
        self.combo_intervalo = QComboBox()
        for dias, titulo in self._INTERVALOS:
            self.combo_intervalo.addItem(titulo, dias)
        self.combo_intervalo.currentIndexChanged.connect(
            self._atualizar_tabela_horas)
        horas_controles_layout.addWidget(self.combo_intervalo)
        horas_controles_layout.addStretch()
        layout.addLayout(horas_controles_layout)

        self.label_total_horas = QLabel()
        layout.addWidget(self.label_total_horas)

        self.tabela_horas = QTableWidget()
        self.tabela_horas.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela_horas.setAlternatingRowColors(True)
        self.tabela_horas.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.tabela_horas)

    def _criar_tab_graficos(self) -> None:
        if self.df_registros.empty:
            return

        assert self.tabs is not None

        self.tab_graficos = QWidget()
        layout = QVBoxLayout(self.tab_graficos)

        controles_layout = QHBoxLayout()
        controles_layout.addWidget(QLabel("Desenhista:"))
        self.combo_grafico_usuario = QComboBox()
        self.combo_grafico_usuario.addItem("Todos", None)
        for usuario in self.usuarios:
            self.combo_grafico_usuario.addItem(usuario, usuario)
        self.combo_grafico_usuario.currentIndexChanged.connect(
            self._atualizar_graficos)
        controles_layout.addWidget(self.combo_grafico_usuario)
        controles_layout.addStretch()

        layout.addLayout(controles_layout)

        self.canvas = MatplotlibCanvas(width=12, height=9, dpi=100)
        layout.addWidget(self.canvas)

        self.tabs.addTab(self.tab_graficos, "Gráficos")

    # ------------------------------------------------------------------
    # Atualizações de UI
    # ------------------------------------------------------------------

    def _atualizar_tabela_mensal(self) -> None:
        assert self.combo_ano is not None
        assert self.combo_metrica is not None
        assert self.tabela_mensal is not None

        ano_texto = self.combo_ano.currentText()
        if not ano_texto:
            self.tabela_mensal.setRowCount(0)
            return

        chave_metrica, _ = self._METRIC_MAP[self.combo_metrica.currentText()]
        ano = int(ano_texto)
        dados_ano = self.metricas.get("dados_mensais", {}).get(ano, {})

        row_count = len(self.usuarios) + 1  # +1 para linha de totais
        self.tabela_mensal.setRowCount(row_count)

        for row, usuario in enumerate(self.usuarios):
            self.tabela_mensal.setVerticalHeaderItem(
                row, QTableWidgetItem(usuario))
            total_usuario = 0.0
            for col, (mes, _) in enumerate(self._MESES):
                valor = dados_ano.get(usuario, {}).get(
                    mes, {}).get(chave_metrica, 0)
                total_usuario += valor
                self.tabela_mensal.setItem(
                    row,
                    col,
                    self._criar_item_tabela(
                        self._formatar_valor_metrica(chave_metrica, valor)
                    ),
                )
            self.tabela_mensal.setItem(
                row,
                len(self._MESES),
                self._criar_item_tabela(
                    self._formatar_valor_metrica(chave_metrica, total_usuario)
                ),
            )

        total_row = len(self.usuarios)
        self.tabela_mensal.setVerticalHeaderItem(
            total_row, QTableWidgetItem("Total"))

        for col, (mes, _) in enumerate(self._MESES):
            total_mes = sum(
                dados_ano.get(usuario, {}).get(mes, {}).get(chave_metrica, 0)
                for usuario in self.usuarios
            )
            self.tabela_mensal.setItem(
                total_row,
                col,
                self._criar_item_tabela(
                    self._formatar_valor_metrica(chave_metrica, total_mes)
                ),
            )

        total_geral = sum(
            dados_ano.get(usuario, {}).get(mes, {}).get(chave_metrica, 0)
            for usuario in self.usuarios
            for mes, _ in self._MESES
        )
        self.tabela_mensal.setItem(
            total_row,
            len(self._MESES),
            self._criar_item_tabela(
                self._formatar_valor_metrica(chave_metrica, total_geral)
            ),
        )

    def _atualizar_tabela_totais(self) -> None:
        assert self.tabela_totais is not None

        totais = self.metricas.get("totais_ano", {})
        anos_ordenados = sorted(totais.keys())
        self.tabela_totais.setRowCount(len(anos_ordenados))

        for row, ano in enumerate(anos_ordenados):
            dados = totais.get(ano, {})
            self.tabela_totais.setItem(
                row,
                0,
                self._criar_item_tabela(
                    str(ano), alinhamento=Qt.AlignmentFlag.AlignCenter
                ),
            )
            self.tabela_totais.setItem(
                row,
                1,
                self._criar_item_tabela(str(int(dados.get("itens", 0)))),
            )
            self.tabela_totais.setItem(
                row,
                2,
                self._criar_item_tabela(
                    formatar_valor_monetario(dados.get("valor", 0.0))
                ),
            )
            self.tabela_totais.setItem(
                row,
                3,
                self._criar_item_tabela(str(int(dados.get("proposta", 0)))),
            )

    def _atualizar_tabela_medias(self) -> None:
        assert self.tabela_medias is not None

        medias = self.metricas.get("medias_por_usuario", {})
        media_geral = self.metricas.get("media_geral", {})

        row_count = len(self.usuarios) + 1 if medias else 0
        self.tabela_medias.setRowCount(row_count)

        for row, usuario in enumerate(self.usuarios):
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
                self._formatar_media_decimal(dados.get("itens_por_dia", 0.0)),
                self._formatar_media_decimal(
                    dados.get("proposta_por_dia", 0.0)),
                self._formatar_segundos(dados.get("horas_por_dia", 0)),
            ]

            for col, texto in enumerate(valores):
                alinhamento = (
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                    if col == 0
                    else Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.tabela_medias.setItem(
                    row,
                    col,
                    self._criar_item_tabela(texto, alinhamento=alinhamento),
                )

        if row_count:
            total_row = len(self.usuarios)
            valores_total = [
                "Todos",
                self._formatar_media_decimal(
                    media_geral.get("itens_por_dia", 0.0)),
                self._formatar_media_decimal(
                    media_geral.get("proposta_por_dia", 0.0)),
                self._formatar_segundos(media_geral.get("horas_por_dia", 0)),
            ]

            for col, texto in enumerate(valores_total):
                alinhamento = (
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                    if col == 0
                    else Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self.tabela_medias.setItem(
                    total_row,
                    col,
                    self._criar_item_tabela(texto, alinhamento=alinhamento),
                )

    def _atualizar_tabela_horas(self) -> None:
        assert self.combo_intervalo is not None
        assert self.label_total_horas is not None
        assert self.tabela_horas is not None

        dados_horas = self.metricas.get("horas_por_dia", {})
        dias_ordenados = list(dados_horas.keys())
        if not dias_ordenados:
            self.tabela_horas.setRowCount(0)
            self.label_total_horas.setText(
                "Nenhuma informação de tempo de corte disponível."
            )
            return

        dias_limite = self.combo_intervalo.currentData()
        if dias_limite:
            dias_exibidos = dias_ordenados[:dias_limite]
        else:
            dias_exibidos = dias_ordenados

        colunas = ["Data"] + self.usuarios + ["Total"]
        self.tabela_horas.setColumnCount(len(colunas))
        self.tabela_horas.setHorizontalHeaderLabels(colunas)
        self.tabela_horas.setRowCount(len(dias_exibidos))

        total_periodo = 0

        for row, dia in enumerate(dias_exibidos):
            info = dados_horas[dia]
            total_periodo += info.get("total", 0)
            self.tabela_horas.setItem(
                row,
                0,
                self._criar_item_tabela(
                    formatar_data_para_exibicao(dia),
                    alinhamento=Qt.AlignmentFlag.AlignCenter,
                ),
            )
            for col, usuario in enumerate(self.usuarios, start=1):
                segundos = info.get("por_usuario", {}).get(usuario, 0)
                self.tabela_horas.setItem(
                    row,
                    col,
                    self._criar_item_tabela(self._formatar_segundos(segundos)),
                )
            self.tabela_horas.setItem(
                row,
                len(colunas) - 1,
                self._criar_item_tabela(
                    self._formatar_segundos(info.get("total", 0))),
            )

        self.label_total_horas.setText(
            f"Total acumulado no período: {self._formatar_segundos(total_periodo)}"
        )

    def _atualizar_graficos(self) -> None:
        if self.df_registros.empty or not hasattr(self, "canvas"):
            return

        assert self.canvas is not None

        df_total, df_filtrado, usuario_filtro = self._obter_dados_grafico()

        fig = self.canvas.figure
        fig.clear()

        if df_filtrado.empty:
            self._mostrar_mensagem_sem_dados(fig)
            return

        axes = self._criar_area_graficos(fig)
        self._plotar_metricas_em_barras(df_filtrado, axes)
        self._plotar_series_de_horas(
            df_total,
            df_filtrado,
            usuario_filtro,
            axes["horas"],
        )

        fig.tight_layout()
        self.canvas.draw_idle()

    def _obter_dados_grafico(self) -> tuple[DataFrame, DataFrame, str | None]:
        df_total = self.df_registros.copy()
        usuario_filtro = None
        if hasattr(self, "combo_grafico_usuario"):
            assert self.combo_grafico_usuario is not None
            usuario_filtro = self.combo_grafico_usuario.currentData()

        if usuario_filtro:
            df_filtrado = df_total[df_total["usuario"] == usuario_filtro]
        else:
            df_filtrado = df_total

        return df_total, df_filtrado, usuario_filtro

    def _mostrar_mensagem_sem_dados(self, fig) -> None:
        assert self.canvas is not None

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
        self.canvas.draw_idle()

    def _criar_area_graficos(self, fig) -> dict[str, Any]:
        gs = fig.add_gridspec(4, 2, height_ratios=[1, 1, 1, 1.2])
        axes = {
            "itens_mes": fig.add_subplot(gs[0, 0]),
            "itens_ano": fig.add_subplot(gs[0, 1]),
            "valor_mes": fig.add_subplot(gs[1, 0]),
            "valor_ano": fig.add_subplot(gs[1, 1]),
            "proposta_mes": fig.add_subplot(gs[2, 0]),
            "proposta_ano": fig.add_subplot(gs[2, 1]),
            "horas": fig.add_subplot(gs[3, :]),
        }

        for eixo in axes.values():
            self._estilizar_axes(eixo)

        return axes

    def _plotar_metricas_em_barras(
        self,
        df: DataFrame,
        axes: dict[str, Any],
    ) -> None:
        pivot_itens = self._build_monthly_pivot(df, "qtde_itens")
        pivot_valor = self._build_monthly_pivot(df, "valor_pedido")
        pivot_proposta = self._build_monthly_pivot(df, "proposta")

        self._plot_grouped_bars(
            axes["itens_mes"],
            pivot_itens,
            titulo="Itens por mês",
            rotulo_y="Itens",
            formatter=FuncFormatter(self._int_tick_formatter),
        )

        itens_por_ano = df.groupby("ano")["qtde_itens"].sum().sort_index()
        self._plot_simple_bar(
            axes["itens_ano"],
            itens_por_ano,
            titulo="Itens por ano",
            rotulo_y="Itens",
            formatter=FuncFormatter(self._int_tick_formatter),
        )

        self._plot_grouped_bars(
            axes["valor_mes"],
            pivot_valor,
            titulo="Valor por mês",
            rotulo_y="Valor (R$)",
            formatter=FuncFormatter(self._currency_tick_formatter),
        )

        valor_por_ano = df.groupby("ano")["valor_pedido"].sum().sort_index()
        self._plot_simple_bar(
            axes["valor_ano"],
            valor_por_ano,
            titulo="Valor por ano",
            rotulo_y="Valor (R$)",
            formatter=FuncFormatter(self._currency_tick_formatter),
        )

        self._plot_grouped_bars(
            axes["proposta_mes"],
            pivot_proposta,
            titulo="Propostas por mês",
            rotulo_y="Propostas",
            formatter=FuncFormatter(self._int_tick_formatter),
        )

        proposta_por_ano = df.groupby("ano")["proposta"].sum().sort_index()
        self._plot_simple_bar(
            axes["proposta_ano"],
            proposta_por_ano,
            titulo="Propostas por ano",
            rotulo_y="Propostas",
            formatter=FuncFormatter(self._int_tick_formatter),
        )

    def _plotar_series_de_horas(
        self,
        df_total: DataFrame,
        df_filtrado: DataFrame,
        usuario_filtro: str | None,
        ax_horas,
    ) -> None:
        series_total = (
            df_total.groupby("data")[
                "tempo_segundos"].sum().sort_index() / 3600.0
        )
        series_usuario = (
            df_filtrado.groupby(
                "data")["tempo_segundos"].sum().sort_index() / 3600.0
        )

        if not series_total.empty:
            cor_total = "#7f8c8d" if usuario_filtro else _ACCENT_CYCLE[0]
            estilo_total = "--" if usuario_filtro else "-"
            ax_horas.plot(
                series_total.index,
                series_total.values,
                label="Todos",
                color=cor_total,
                linestyle=estilo_total,
            )

        if usuario_filtro and not series_usuario.empty:
            ax_horas.plot(
                series_usuario.index,
                series_usuario.values,
                label=usuario_filtro,
                color=_ACCENT_CYCLE[2],
            )

        ax_horas.set_title("Horas de corte por dia")
        ax_horas.set_ylabel("Horas")
        ax_horas.grid(True, linestyle="--", color=_GRID_COLOR, alpha=0.4)
        legenda = ax_horas.legend(loc="upper left")
        self._estilizar_legenda(legenda)
        ax_horas.tick_params(axis="x", rotation=45)
        self._estilizar_axes(ax_horas)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _estilizar_axes(self, ax) -> None:
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
    def _formatar_segundos(segundos: int) -> str:
        horas, resto = divmod(int(segundos), 3600)
        minutos, segundos = divmod(resto, 60)
        return f"{horas:02d}:{minutos:02d}:{segundos:02d}"

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
        if chave == "valor":
            return formatar_valor_monetario(valor)
        return f"{int(round(valor)):,}".replace(",", ".")

    @staticmethod
    def _formatar_media_decimal(valor: float) -> str:
        return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _build_monthly_pivot(self, df: DataFrame, coluna: str) -> DataFrame:
        if pd is None:  # pragma: no cover - tratado na inicialização
            raise RuntimeError("Pandas não disponível para gerar o dashboard.")

        if df.empty:
            return pd.DataFrame()

        meses = [mes for mes, _ in self._MESES]
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

    def _plot_grouped_bars(
        self,
        ax,
        pivot: DataFrame,
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

        colunas_meses, rotulos_meses = self._obter_meses_presentes(pivot)

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

        base = self._desenhar_barras_por_ano(
            ax=ax,
            pivot=pivot,
            colunas_meses=colunas_meses,
            largura=largura,
            deslocamento_inicial=deslocamento_inicial,
        )

        ax.set_xticks(base)
        ax.set_xticklabels(rotulos_meses)
        ax.yaxis.set_major_formatter(formatter)
        ax.grid(True, axis="y", linestyle="--", color=_GRID_COLOR, alpha=0.4)
        legenda = ax.legend(loc="upper left", fontsize="small")
        self._estilizar_legenda(legenda)
        self._estilizar_axes(ax)

    def _obter_meses_presentes(
        self,
        pivot: DataFrame,
    ) -> tuple[list[int], list[str]]:
        colunas: list[int] = []
        rotulos: list[str] = []
        for mes, rotulo in self._MESES:
            if mes in pivot.columns:
                colunas.append(mes)
                rotulos.append(rotulo)
        return colunas, rotulos

    def _desenhar_barras_por_ano(
        self,
        *,
        ax,
        pivot: DataFrame,
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

    def _plot_simple_bar(
        self,
        ax,
        serie: Series,
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
        ax.yaxis.set_major_formatter(formatter)
        ax.grid(True, axis="y", linestyle="--", color=_GRID_COLOR, alpha=0.4)
        self._estilizar_axes(ax)

    @staticmethod
    def _int_tick_formatter(valor: float, _pos: int) -> str:
        valor_arredondado = int(round(valor))
        if valor_arredondado < 0:
            return ""
        return f"{valor_arredondado:,}".replace(",", ".")

    @staticmethod
    def _currency_tick_formatter(valor: float, _pos: int) -> str:
        return f"R$ {valor:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
