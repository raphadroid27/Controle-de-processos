"""Dialogo de dashboard administrativo."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import matplotlib as mpl

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

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QDialog, QHBoxLayout, QHeaderView,
                               QLabel, QTableWidget, QTabWidget, QVBoxLayout,
                               QWidget)

from src.utils.dashboard_metrics import obter_metricas_dashboard
from src.utils.formatters import segundos_para_horas
from src.utils.periodo_faturamento import \
    calcular_periodo_faturamento_para_data
from src.utils.ui_config import (METRIC_MAP, aplicar_icone_padrao,
                                 configurar_tabela_padrao)
from src.widgets.components.matplotlib_canvas import MatplotlibCanvas
from src.widgets.dashboard_plotting import DashboardPlotting
from src.widgets.dashboard_tables import DashboardTableUpdates


class DashboardDialog(QDialog):
    """Exibe métricas agregadas para administradores."""

    _PERIODOS = [
        (1, "26/12 a 25/01"),
        (2, "26/01 a 25/02"),
        (3, "26/02 a 25/03"),
        (4, "26/03 a 25/04"),
        (5, "26/04 a 25/05"),
        (6, "26/05 a 25/06"),
        (7, "26/06 a 25/07"),
        (8, "26/07 a 25/08"),
        (9, "26/08 a 25/09"),
        (10, "26/09 a 25/10"),
        (11, "26/10 a 25/11"),
        (12, "26/11 a 25/12"),
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
        self.combo_grafico_metrica: QComboBox | None = None
        self.canvas: MatplotlibCanvas | None = None
        self.periodos_atuais: list[dict] = []
        self.rotulos_periodos: list[str] = []
        self.tooltip_annotation: mpl.text.Annotation | None = None

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
        # Alterado para usar o mês de faturamento em vez do mês calendário
        self.df_registros["mes"] = self.df_registros["data"].apply(
            lambda d: int(calcular_periodo_faturamento_para_data(
                d.to_pydatetime())[0])
        )
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
        self.df_registros["tempo_horas"] = self.df_registros["tempo_segundos"].apply(
            segundos_para_horas
        )

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
        DashboardTableUpdates.atualizar_tabela_totais(self)
        DashboardTableUpdates.atualizar_tabela_mensal(self)
        DashboardTableUpdates.atualizar_tabela_medias(self)
        DashboardTableUpdates.atualizar_tabela_horas(self)
        if not self.df_registros.empty:
            DashboardPlotting.atualizar_graficos(self)

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
            lambda: DashboardTableUpdates.atualizar_tabela_mensal(self)
        )
        controles_layout.addWidget(self.combo_ano)

        controles_layout.addSpacing(16)
        controles_layout.addWidget(QLabel("Métrica:"))
        self.combo_metrica = QComboBox()
        for titulo in METRIC_MAP:
            self.combo_metrica.addItem(titulo)
        self.combo_metrica.currentTextChanged.connect(
            lambda: DashboardTableUpdates.atualizar_tabela_mensal(self)
        )
        controles_layout.addWidget(self.combo_metrica)
        controles_layout.addStretch()
        return controles_layout

    def _criar_tabela_mensal(self) -> QTableWidget:
        self.tabela_mensal = QTableWidget()
        self.tabela_mensal.setColumnCount(13)  # 12 períodos + 1 total
        # Headers serão definidos dinamicamente em _atualizar_tabela_mensal
        configurar_tabela_padrao(self.tabela_mensal)
        return self.tabela_mensal

    def _montar_tabelas_resumo(self) -> QHBoxLayout:
        tabelas_layout = QHBoxLayout()

        totais_layout = QVBoxLayout()
        totais_layout.addWidget(QLabel("Totais por ano"))
        self.tabela_totais = QTableWidget()
        self.tabela_totais.setColumnCount(5)
        self.tabela_totais.setHorizontalHeaderLabels(
            ["Ano", "Itens", "Valor (R$)", "Propostas", "Horas"]
        )
        configurar_tabela_padrao(self.tabela_totais)
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
        configurar_tabela_padrao(self.tabela_medias)
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
            lambda: DashboardTableUpdates.atualizar_tabela_horas(self)
        )
        horas_controles_layout.addWidget(self.combo_intervalo)
        horas_controles_layout.addStretch()
        layout.addLayout(horas_controles_layout)

        self.label_total_horas = QLabel()
        layout.addWidget(self.label_total_horas)

        self.tabela_horas = QTableWidget()
        configurar_tabela_padrao(self.tabela_horas)
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
            lambda: DashboardPlotting.atualizar_graficos(self)
        )
        controles_layout.addWidget(self.combo_grafico_usuario)

        controles_layout.addSpacing(16)
        controles_layout.addWidget(QLabel("Métrica:"))
        self.combo_grafico_metrica = QComboBox()
        for titulo in METRIC_MAP:
            self.combo_grafico_metrica.addItem(titulo)
        self.combo_grafico_metrica.currentIndexChanged.connect(
            lambda: DashboardPlotting.atualizar_graficos(self)
        )
        controles_layout.addWidget(self.combo_grafico_metrica)

        controles_layout.addStretch()

        layout.addLayout(controles_layout)

        self.canvas = MatplotlibCanvas(width=12, height=9, dpi=100)
        self.canvas.mpl_connect(
            "motion_notify_event",
            lambda event: DashboardPlotting.on_hover_grafico(self, event),
        )
        layout.addWidget(self.canvas)

        self.tabs.addTab(self.tab_graficos, "Gráficos")
