"""Canvas helper para integrar gráficos do Matplotlib ao Qt."""

from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from src.utils.ui_config import _FIGURE_FACE


class MatplotlibCanvas(FigureCanvas):
    """Canvas helper para integrar gráficos do Matplotlib ao Qt."""

    def __init__(self, width: float = 12, height: float = 9, dpi: int = 100):
        """Inicializa o canvas do Matplotlib com as dimensões especificadas."""
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        self.figure.patch.set_facecolor(_FIGURE_FACE)
        super().__init__(self.figure)
