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

from PySide6.QtWidgets import QSizePolicy

# Constantes para padronização de componentes
ALTURA_BOTAO = 32
ALTURA_MINIMA_BOTAO = 28
LARGURA_BOTAO = 80
TAMANHO_FONTE_BOTAO = 11
RAIO_BORDA_BOTAO = 4
PADDING_BOTAO = "2px 4px"
ESPACAMENTO_PADRAO = 10

# Constantes para outros componentes
ALTURA_PADRAO_COMPONENTE = 20
LARGURA_MINIMA_COMPONENTE = 60
PADDING_INTERNO_COMPONENTE = "2px 4px"


# Configurações de cores para botões
CORES_BOTOES = {
    "verde": {
        "normal": "#4CAF50",
        "hover": "#45a049",
        "pressed": "#3d8b40",
        "text": "white",
    },
    "laranja": {
        "normal": "#FF9800",
        "hover": "#F57C00",
        "pressed": "#E65100",
        "text": "white",
    },
    "vermelho": {
        "normal": "#f44336",
        "hover": "#da190b",
        "pressed": "#b71c1c",
        "text": "white",
    },
    "azul": {
        "normal": "#2196f3",
        "hover": "#1976d2",
        "pressed": "#1565c0",
        "text": "white",
    },
    "cinza": {
        "normal": "#9e9e9e",
        "hover": "#757575",
        "pressed": "#616161",
        "text": "white",
    },
    "amarelo": {
        "normal": "#ffd93d",
        "hover": "#ffcc02",
        "pressed": "#e6b800",
        "text": "#333",
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


def obter_estilo_botao(cor, largura=None):
    """
    Retorna o estilo CSS para botões com a cor especificada.

    Args:
        cor: Uma das cores disponíveis: 'verde', 'laranja', 'vermelho', 'azul', 'cinza', 'amarelo'

    Returns:
        String CSS para aplicar ao botão
    """
    if cor not in CORES_BOTOES:
        cor = "cinza"  # fallback para cor padrão

    colors = CORES_BOTOES[cor]
    return f"""
        QPushButton {{
            background-color: {colors['normal']};
            color: {colors['text']};
            border: none;
            padding: {PADDING_BOTAO};
            border-radius: {RAIO_BORDA_BOTAO}px;
            font-weight: bold;
            font-size: {TAMANHO_FONTE_BOTAO}px;
        }}
        QPushButton:hover {{
            background-color: {colors['hover']};
        }}
        QPushButton:pressed {{
            background-color: {colors['pressed']};
        }}
    """


def configurar_botao_padrao(botao, largura_minima=None):
    """
    Função global para configurar qualquer botão com padrão uniforme de altura e largura.

    Args:
        botao: O botão QPushButton a ser configurado
        largura_minima: Largura mínima opcional (usa LARGURA_BOTAO se não especificado)
    """
    from PySide6.QtWidgets import QSizePolicy

    botao.setMinimumHeight(ALTURA_MINIMA_BOTAO)
    botao.setMaximumHeight(ALTURA_BOTAO)
    botao.setMinimumWidth(largura_minima or LARGURA_BOTAO)
    botao.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)


def aplicar_estilo_botao(botao, cor: str, largura_minima=None):
    """
    Aplica estilo completo de botão de forma conveniente.

    Args:
        botao: O botão QPushButton a ser estilizado
        cor: Cor do botão ('verde', 'laranja', 'vermelho', 'azul', 'cinza', 'amarelo')
        largura_minima: Largura mínima do botão (opcional)
    """
    if not hasattr(botao, "setStyleSheet"):
        return

    # Aplicar configuração padrão de tamanho
    configurar_botao_padrao(botao, largura_minima)

    # Aplicar estilo de cor
    botao.setStyleSheet(obter_estilo_botao(cor))


def obter_estilo_botao_adicionar():
    """Retorna o estilo específico para botão Adicionar (verde)."""
    return obter_estilo_botao("verde")


def obter_estilo_botao_limpar():
    """Retorna o estilo específico para botão Limpar Filtros (laranja)."""
    return obter_estilo_botao("laranja")


def obter_estilo_botao_excluir():
    """Retorna o estilo específico para botão Excluir (vermelho)."""
    return obter_estilo_botao("vermelho")


def obter_css_correcao_widgets():
    """
    Retorna CSS para corrigir tamanhos desproporcionais dos widgets.

    Returns:
        str: CSS para correção de tamanhos
    """
    return f"""
    QComboBox {{
        min-height: 1em;
        max-height: {ALTURA_PADRAO_COMPONENTE}px;
        padding: 2px 4px;
        font-size: 10pt;
    }}
    QLineEdit {{
        min-height: 1em;
        max-height: {ALTURA_PADRAO_COMPONENTE}px;
        padding: 2px 4px;
        font-size: 10pt;
    }}
    QLabel {{
        min-height: 1em;
        padding: 2px;
        font-size: 10pt;
    }}
    QGroupBox::title {{
        font-size: 10pt;
        padding: 2px;
    }}
    QToolTip {{
        color: white;
        background-color: #2d2d2d;
        border-radius: 3px;
        padding: 4px 6px;
        font-size: 9pt;
        opacity: 240;
    }}
    """


def obter_css_widgets_auto_ajustaveis():
    """
    Retorna CSS para widgets com largura auto-ajustável.

    Returns:
        dict: CSS para cada tipo de widget com largura flexível
    """
    return {
        "combobox": f"""
            QComboBox {{
                min-width: {LARGURA_MINIMA_COMPONENTE}px;
                min-height: 1em;
                max-height: {ALTURA_PADRAO_COMPONENTE}px;
                padding: {PADDING_INTERNO_COMPONENTE};
                font-size: 10pt;
            }}
        """,
        "lineedit": f"""
            QLineEdit {{
                min-width: {LARGURA_MINIMA_COMPONENTE}px;
                min-height: 1em;
                max-height: {ALTURA_PADRAO_COMPONENTE}px;
                padding: {PADDING_INTERNO_COMPONENTE};
                font-size: 10pt;
            }}
        """,
    }


def aplicar_estilo_widget_auto_ajustavel(widget, tipo_widget):
    """
    Aplica estilo auto-ajustável aos widgets.

    Args:
        widget: Widget a receber o estilo
        tipo_widget: Tipo do widget ('combobox', 'lineedit')
    """
    estilos = obter_css_widgets_auto_ajustaveis()
    if tipo_widget in estilos:
        widget.setStyleSheet(estilos[tipo_widget])


def obter_configuracao_layout_flexivel():
    """
    Retorna configurações de layout para widgets auto-ajustáveis.

    Returns:
        dict: Configurações de layout flexível
    """
    return {
        "altura_padrao": ALTURA_PADRAO_COMPONENTE,
        "largura_minima": LARGURA_MINIMA_COMPONENTE,
        "horizontal_spacing": ESPACAMENTO_PADRAO,
        "vertical_spacing": 3,
    }


def configurar_layout_flexivel(layout):
    """
    Configura um layout para ter widgets auto-ajustáveis.

    Args:
        layout: Layout a ser configurado
    """
    config = obter_configuracao_layout_flexivel()

    if hasattr(layout, 'setColumnStretch'):
        for col in range(4):
            layout.setColumnStretch(col, 1)

    if hasattr(layout, 'setHorizontalSpacing'):
        layout.setHorizontalSpacing(config["horizontal_spacing"])

    if hasattr(layout, 'setVerticalSpacing'):
        layout.setVerticalSpacing(config["vertical_spacing"])


def obter_estilo_progress_bar():
    """Retorna o estilo CSS para a barra de progresso."""
    return """
        QProgressBar {
            border: 1px solid #555;
            border-radius: 5px;
            text-align: center;
            height: 10px;
        }
        QProgressBar::chunk {
            background-color: #007acc;
            border-radius: 4px;
        }
    """
