"""
Módulo com utilitários para configuração de UI e estilização.

Este módulo contém funções e constantes para padronização
da interface gráfica do sistema, incluindo estilos de botões,
cores temáticas e configurações de layout.

Funcionalidades:
- Configuração padronizada de botões
- Estilos CSS para diferentes tipos de botões
- Constantes de cores e dimensões
- Funções utilitárias para aplicação de estilos
"""

import logging
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import QDate
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHeaderView, QSizePolicy, QTableWidget, QWidget

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).parent.parent.parent / "assets"


def _get_asset_icon(name: str) -> str | None:
    """Retorna caminho POSIX do ícone em assets, se existir."""

    try:
        candidate = ASSETS_DIR / name
        if candidate.exists():
            return candidate.as_posix()
    except Exception:  # pylint: disable=broad-exception-caught
        logger.debug("Falha ao resolver ícone %s", name, exc_info=True)
    return None


# Constantes para padronização de componentes
TAMANHO_FONTE_PADRAO = 10
TAMANHO_FONTE_BOTAO = 12
RAIO_BORDA_BOTAO = 4
PADDING = "2px 4px"
ESPACAMENTO_PADRAO = 10

# Constantes gerais de layout e estilo
ALTURA_PADRAO_COMPONENTE = 25
LARGURA_MINIMA_COMPONENTE = 70
ALTURA_PADRAO_BOTAO = 25
LARGURA_MINIMA_BOTAO = 100
ALTURA_PADRAO_MENU = 18

COR_FUNDO_BRANCO = "#f0f0f0"
COR_FUNDO_ESCURO = "#161719"
COR_FUNDO_CLARO = "#f8f9fa"

# Constantes para diálogos de login
ALTURA_DIALOG_LOGIN = 140
LARGURA_DIALOG_LOGIN = 300
ALTURA_DIALOG_NOVO_USUARIO = 140
LARGURA_DIALOG_NOVO_USUARIO = 300
MARGEM_DIALOG = 10


# Configurações de cores para botões
BUTTON_COLORS = {
    "cinza": {
        "normal": "#9e9e9e",
        "hover": "#757575",
        "pressed": "#616161",
        "text": "white",
    },
    "azul": {
        "normal": "#2196f3",
        "hover": "#1976d2",
        "pressed": "#1565c0",
        "text": "white",
    },
    "amarelo": {
        "normal": "#ffd93d",
        "hover": "#ffcc02",
        "pressed": "#e6b800",
        "text": "#333",
    },
    "vermelho": {
        "normal": "#f44336",
        "hover": "#da190b",
        "pressed": "#b71c1c",
        "text": "white",
    },
    "verde": {
        "normal": "#4caf50",
        "hover": "#45a049",
        "pressed": "#3d8b40",
        "text": "white",
    },
    "laranja": {
        "normal": "#ff9800",
        "hover": "#fb8c00",
        "pressed": "#f57c00",
        "text": "white",
    },
    # Cores extras para compatibilidade com o app atual
    "roxo": {
        "normal": "#9C27B0",
        "hover": "#8E24AA",
        "pressed": "#7B1FA2",
        "text": "white",
    },
    "teal": {
        "normal": "#009688",
        "hover": "#00897B",
        "pressed": "#00796B",
        "text": "white",
    },
    "rosa": {
        "normal": "#EC407A",
        "hover": "#D81B60",
        "pressed": "#C2185B",
        "text": "white",
    },
    "ciano": {
        "normal": "#00BCD4",
        "hover": "#00ACC1",
        "pressed": "#0097A7",
        "text": "white",
    },
}


def aplicar_estilo_botao_desabilitado():
    """Retorna o estilo CSS para botões desabilitados."""
    return """
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
        }
    """


def obter_estilo_botao(cor):
    """
    Retorna o estilo CSS para botões com a cor especificada.

    Args:
        cor: Uma das cores disponíveis: 'verde', 'laranja',
            'vermelho', 'azul', 'cinza', 'amarelo', 'roxo',
            'teal', 'rosa', 'ciano'

    Returns:
        String CSS para aplicar ao botão
    """
    if cor not in BUTTON_COLORS:
        cor = "cinza"  # fallback para cor padrão

    colors = BUTTON_COLORS[cor]
    return f"""
        QPushButton {{
            background-color: {colors['normal']};
            color: {colors['text']};
            border: none;
            padding: {PADDING};
            border-radius: {RAIO_BORDA_BOTAO}px;
            font-weight: bold;
            font-size: {TAMANHO_FONTE_BOTAO}px;
            min-width: {LARGURA_MINIMA_BOTAO}px;
            min-height: {ALTURA_PADRAO_BOTAO}px;
            max-height: {ALTURA_PADRAO_BOTAO}px;
        }}
        QPushButton:hover {{
            background-color: {colors['hover']};
        }}
        QPushButton:pressed {{
            background-color: {colors['pressed']};
        }}
    """


def configurar_widgets_entrada_uniformes(widgets_list):
    """Configura widgets de entrada para ter comportamento uniforme.

    Args:
        widgets_list: Lista de widgets para configurar
    """
    for widget in widgets_list:
        widget.setSizePolicy(QSizePolicy.Policy.Expanding,
                             QSizePolicy.Policy.Fixed)


def aplicar_estilo_botao(botao, cor: str):
    """
    Aplica estilo completo de botão de forma conveniente.

    Args:
        botao: O botão QPushButton a ser estilizado
        cor: Cor do botão ('verde', 'laranja', 'vermelho',
            'azul', 'cinza', 'amarelo')
    """
    if not hasattr(botao, "setStyleSheet"):
        return

    botao.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    # Aplicar estilo de cor
    botao.setStyleSheet(obter_estilo_botao(cor))


def obter_estilo_table_widget():
    """Retorna CSS para QTableWidget com aparência de grade visual."""

    return f"""
        QTableWidget {{
            color: palette(text);
            font-size: {TAMANHO_FONTE_PADRAO}pt;
        }}
        QTableWidget::item {{
            padding: 0px;
        }}
        QHeaderView::section {{
            padding: 0px;
            color: palette(button-text);
            background-color: palette(alternate-base);
        }}
    """


def obter_estilo_progress_bar(theme: str = "light") -> str:
    """Retorna o estilo CSS para a barra de progresso."""

    border_color = "#B6B6B6" if theme == "light" else "#242424"

    return f"""
        QProgressBar {{
            border: 1px solid {border_color};
            border-radius: 5px;
            text-align: center;
            height: {ALTURA_PADRAO_BOTAO}px;
            background-color: palette(base);
            color: palette(text);
            font-size: {TAMANHO_FONTE_PADRAO}pt;
        }}

        QProgressBar::chunk {{
            background-color: palette(highlight);
            border-radius: 4px;
        }}
    """


def aplicar_icone_padrao(widget: QWidget) -> None:
    """
    Aplica o ícone padrão da aplicação a um widget (janela ou diálogo).

    Args:
        widget: O widget (QMainWindow, QDialog, etc.) ao qual aplicar o ícone.
    """
    icon_path = Path(__file__).parent.parent.parent / "assets" / "icone.svg"
    if icon_path.exists():
        icon = QIcon(str(icon_path))
        widget.setWindowIcon(icon)


def obter_data_atual_utc():
    """
    Retorna a data atual em UTC como QDate.

    Isso evita problemas de fuso horário onde a data local pode ser diferente
    da data UTC, permitindo que usuários em fusos horários negativos
    (como UTC-3) possam registrar processos na data correta.
    """
    data_utc = datetime.now(timezone.utc).date()
    return QDate(data_utc.year, data_utc.month, data_utc.day)


# Constantes para dashboard e gráficos
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

# Mapeamento de métricas para dashboard
METRIC_MAP = {
    "Itens": ("itens", int),
    "Valor (R$)": ("valor", float),
    "Propostas": ("proposta", int),
    "Horas": ("horas", float),
}


def configurar_tabela_padrao(tabela):
    """
    Configura uma tabela com as propriedades padrão do dashboard.

    Args:
        tabela: QTableWidget a ser configurada
    """
    tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    tabela.setAlternatingRowColors(True)
    if hasattr(tabela, "setStyleSheet"):
        tabela.setStyleSheet(obter_estilo_table_widget())


# ---------------------------------------------------------------------------
# Estilos detalhados para widgets (baseado em estilos.py de referência)
# ---------------------------------------------------------------------------


def obter_estilo_combo_box(theme: str = "light", arrow_file: str | None = None) -> str:
    """Retorna CSS para QComboBox."""

    border_color = "#B6B6B6" if theme == "light" else "#242424"
    arrow_block = ""
    if arrow_file:
        arrow_block = f"""

    QComboBox::down-arrow {{
        image: url("{arrow_file}");
        width: 10px;
        height: 10px;
    }}
"""

    return f"""
    QComboBox {{
        min-width: {LARGURA_MINIMA_COMPONENTE}px;
        min-height: {ALTURA_PADRAO_COMPONENTE}px;
        max-height: {ALTURA_PADRAO_COMPONENTE}px;
        padding: {PADDING};
        font-size: {TAMANHO_FONTE_PADRAO}pt;
        font-weight: bold;
        border: 1px solid {border_color};
        border-radius: none;
        background-color: palette(base);
        color: palette(text);
    }}

    QComboBox::drop-down {{
        border: none;
        background-color: transparent;
    }}
{arrow_block}
    QComboBox QAbstractItemView {{
        background-color: palette(base);
        color: palette(text);
        border: none;
        selection-background-color: palette(highlight);
        selection-color: palette(highlighted-text);
    }}

    QComboBox::item {{
        min-height: {ALTURA_PADRAO_MENU}px;
        max-height: {ALTURA_PADRAO_MENU}px;
        padding: 5px 10px 5px -20px;
    }}

    QComboBox::item:selected {{
        background-color: palette(highlight);
        color: palette(highlighted-text);
        border-radius: 5px;
        margin: 2px 0px;
    }}

    QComboBox:hover {{
        border: 1px solid palette(highlight);
    }}
    """


def obter_estilo_date_edit(theme: str = "light", arrow_file: str | None = None) -> str:
    """Retorna CSS para QDateEdit com visual alinhado ao QComboBox."""

    border_color = "#B6B6B6" if theme == "light" else "#242424"
    arrow_block = ""
    if arrow_file:
        arrow_block = f"""

    QDateEdit::down-arrow {{
        image: url(\"{arrow_file}\");
        width: 10px;
        height: 10px;
        margin-right: 4px;
    }}
"""

    return f"""
    QDateEdit {{
        min-width: {LARGURA_MINIMA_COMPONENTE}px;
        min-height: {ALTURA_PADRAO_COMPONENTE}px;
        max-height: {ALTURA_PADRAO_COMPONENTE}px;
        padding: {PADDING};
        font-size: {TAMANHO_FONTE_PADRAO}pt;
        font-weight: bold;
        border: 1px solid {border_color};
        border-radius: none;
        background-color: palette(base);
        color: palette(text);
    }}

    QDateEdit::drop-down {{
        width: 18px;
        border: none;
        background-color: transparent;
    }}
{arrow_block}
    QDateEdit:hover {{
        border: 1px solid palette(highlight);
    }}

    QDateEdit:focus {{
        border: 1px solid palette(highlight);
    }}
    """


def obter_estilo_line_edit(theme: str = "light") -> str:
    """Retorna CSS para QLineEdit."""

    border_color = "#B6B6B6" if theme == "light" else "#242424"

    return f"""
    QLineEdit {{
        background-color: palette(base);
        color: palette(text);
        min-width: {LARGURA_MINIMA_COMPONENTE}px;
        min-height: {ALTURA_PADRAO_COMPONENTE}px;
        max-height: {ALTURA_PADRAO_COMPONENTE}px;
        padding: {PADDING};
        font-size: {TAMANHO_FONTE_PADRAO}pt;
        font-weight: bold;
        border: 1px solid {border_color};
        border-radius: none;
    }}

    QLineEdit:hover {{
        border: 1px solid palette(highlight);
    }}

    QLineEdit:focus {{
        border: 1px solid palette(highlight);
    }}
    """


def obter_estilo_label() -> str:
    """Retorna CSS para QLabel e variações."""

    return f"""
    QLabel {{
        background-color: transparent;
        color: palette(window-text);
        font-size: {TAMANHO_FONTE_PADRAO}pt;
        min-width: {LARGURA_MINIMA_COMPONENTE}px;
        min-height: {ALTURA_PADRAO_COMPONENTE}px;
        max-height: {ALTURA_PADRAO_COMPONENTE}px;
        padding: {PADDING};
        font-weight: bold;
    }}

    QLabel#label_titulo {{
        font-size: {TAMANHO_FONTE_PADRAO-1}pt;
        color: palette(window-text);
        background-color: transparent;
        padding: 0px 0px;
        min-width: auto;
        font-weight: normal;
    }}

    QLabel#label_titulo_negrito {{
        font-size: {TAMANHO_FONTE_PADRAO}pt;
        color: palette(window-text);
        padding: 0px 0px;
        min-width: auto;
        font-weight: bold;
    }}

    QLabel#label_texto {{
        font-size: {TAMANHO_FONTE_PADRAO}pt;
        color: palette(window-text);
        padding: 0px 0px;
        min-height: auto;
        max-height: auto;
        font-weight: normal;
    }}

    """


def obter_estilo_group_box() -> str:
    """Retorna CSS para QGroupBox."""

    return """
    QGroupBox {
        color: palette(window-text);
        margin-top: 10px; /* espaço para o título */
        font-weight: bold;
    }

    QGroupBox#sem_borda {
        color: palette(window-text);
        border: none;
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        left: 7px;
        padding: 0 3px 0 3px;
        color: palette(window-text);
        background: palette(window);
    }
    """


def obter_estilo_tooltip() -> str:
    """Retorna CSS para QToolTip."""

    return f"""
    QToolTip {{
        background-color: palette(base);
        color: palette(text);
        border: 1px solid palette(dark);
        font-size: {TAMANHO_FONTE_PADRAO}pt;
    }}
    """


def obter_estilo_menu_bar() -> str:
    """Retorna CSS para QMenuBar."""

    return f"""
    QMenuBar {{
        background-color: palette(window);
        color: palette(window-text);
        padding: 5px 0px;
        font-size: {TAMANHO_FONTE_PADRAO}pt;
        spacing: 1px;
        min-height: {ALTURA_PADRAO_MENU}px;
        max-height: {ALTURA_PADRAO_MENU}px;
    }}

    QMenuBar::item:selected {{
        background-color: palette(highlight);
        color: palette(highlighted-text);
        border-radius: 5px;
    }}
    """


def obter_estilo_menu(check_icon: str | None) -> str:
    """Retorna CSS para QMenu e seus indicadores."""

    checked_bg = ""
    if check_icon:
        checked_bg = f"""
        image: url("{check_icon}");
"""

    return f"""
    QMenu {{
        background-color: palette(base);
        border: none;
        font-size: {TAMANHO_FONTE_PADRAO}pt;
    }}

    QMenu::item {{
        min-height: {ALTURA_PADRAO_MENU}px;
        max-height: {ALTURA_PADRAO_MENU}px;
        padding: 5px 10px;
    }}

    QMenu::item:selected {{
        background-color: palette(highlight);
        color: palette(highlighted-text);
        border-radius: 5px;
        margin: 2px 0px;
    }}

    QMenu::indicator {{
        width: 12px;
        height: 12px;
        margin-left: 6px;
        border-radius: 3px;
    }}

    QMenu::indicator:unchecked {{
        border: 1px solid #595959;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 palette(button),
                                    stop:1 palette(base));
    }}

    QMenu::indicator:checked {{
        border: 1px solid #595959;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 palette(button),
                                    stop:1 palette(base));
{checked_bg}    }}

    QMenu::indicator:hover {{
        border: 1px solid palette(highlight);
    }}
    """


def obter_estilo_checkbox(check_icon: str | None) -> str:
    """Retorna CSS para QCheckBox e seus indicadores."""

    icon_block = ""
    if check_icon:
        icon_block = f"""
        background-image: url("{check_icon}");
        background-repeat: no-repeat;
        background-position: center;
"""

    return f"""
    QCheckBox {{
        spacing: 8px;
        font-size: {TAMANHO_FONTE_PADRAO}pt;
        font-weight: normal;
    }}

    QCheckBox::indicator {{
        width: 12px;
        height: 12px;
        margin-left: 6px;
        border-radius: 3px;
    }}

    QCheckBox::indicator:unchecked {{
        border: 1px solid #595959;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 palette(button),
                                    stop:1 palette(base));
    }}

    QCheckBox::indicator:unchecked:hover,
    QCheckBox::indicator:checked:hover {{
        border: 1px solid palette(highlight);
    }}

    QCheckBox::indicator:checked {{
        border: 1px solid #595959;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 palette(button),
                                    stop:1 palette(base));
{icon_block}    }}

    QCheckBox::indicator:checked:disabled,
    QCheckBox::indicator:unchecked:disabled {{
        border: 1px solid #595959;
        background-color: palette(midlight);
    }}
    """


def obter_estilo_message_box() -> str:
    """Retorna CSS para QMessageBox."""

    return f"""
    QMessageBox {{
        background-color: palette(window);
        color: palette(window-text);
    }}

    QMessageBox QLabel {{
        max-height: 99999px;
        min-width: 0;
        padding: 0;
        min-height: 0;
        font-size: {TAMANHO_FONTE_PADRAO}pt;
        font-weight: normal;
    }}
    """


def obter_estilo_list_widget() -> str:
    """Retorna CSS para QListWidget (lista_categoria)."""

    return f"""
    QListWidget#lista_categoria {{
        border: none;
        font-size: {TAMANHO_FONTE_PADRAO}pt;
        background-color: palette(window);
    }}

    QListWidget#lista_categoria::item {{
        color: palette(text);
        border-radius: 5px;
        padding: 4px 8px;
        margin: 3px 0;
    }}

    QListWidget#lista_categoria::item:hover {{
        background-color: palette(base);
        color: palette(text);
    }}

    QListWidget#lista_categoria::item:selected {{
        background-color: palette(highlight);
        color: palette(highlighted-text);
        padding-left: 5px;
        padding-right: 5px;
        border-radius: 6px;
    }}
    """


def obter_estilo_container_manual() -> str:
    """Retorna CSS para QWidget (container_manual)."""

    return """
    QWidget#container_manual {
        border: none;
        border-radius: 5px;
        background-color: palette(base);
        margin-top: 0px;
    }
    """


def obter_estilo_text_browser() -> str:
    """Retorna CSS para QTextBrowser."""

    return f"""
    QTextBrowser {{
        font-size: {TAMANHO_FONTE_PADRAO}pt;
    }}
    """

# pylint: disable=too-many-locals


def get_widgets_styles(theme: str = "light") -> str:
    """Retorna todos os estilos CSS combinados para a aplicação."""

    tema_normalizado = (theme or "light").lower()
    check_icon = _get_asset_icon(
        "check_white.svg") if tema_normalizado == "dark" else _get_asset_icon("check.svg")
    arrow_icon = _get_asset_icon(
        "arrow_down_white.svg") if tema_normalizado == "dark" else _get_asset_icon("arrow_down.svg")

    combo = obter_estilo_combo_box(tema_normalizado, arrow_icon)
    dateedit = obter_estilo_date_edit(tema_normalizado, arrow_icon)
    lineedit = obter_estilo_line_edit(tema_normalizado)
    label = obter_estilo_label()
    groupbox = obter_estilo_group_box()
    tooltip = obter_estilo_tooltip()
    menubar = obter_estilo_menu_bar()
    menu = obter_estilo_menu(check_icon)
    checkbox = obter_estilo_checkbox(check_icon)
    messagebox = obter_estilo_message_box()
    listwidget = obter_estilo_list_widget()
    container = obter_estilo_container_manual()
    textbrowser = obter_estilo_text_browser()
    progress = obter_estilo_progress_bar(tema_normalizado)

    return f"""
    {combo}
    {dateedit}
    {lineedit}
    {label}
    {groupbox}
    {tooltip}
    {menubar}
    {menu}
    {checkbox}
    {messagebox}
    {listwidget}
    {container}
    {textbrowser}
    {progress}
    """
