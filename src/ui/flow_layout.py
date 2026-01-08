"""Implementação de um FlowLayout para PySide6."""

from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtWidgets import QLayout


class FlowLayout(QLayout):
    """Layout que organiza itens em fluxo, quebrando para a próxima linha se o espaço acabar."""

    def __init__(
        self, parent=None, margin: int = 0, h_spacing: int = 10, v_spacing: int = 10
    ):
        """
        Inicializa o FlowLayout.

        Args:
            parent: O widget pai.
            margin: As margens do conteúdo.
            h_spacing: Espaçamento horizontal entre itens.
            v_spacing: Espaçamento vertical entre itens.
        """
        super().__init__(parent)
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing
        self._items = []
        self.setContentsMargins(margin, margin, margin, margin)

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):  # pylint: disable=invalid-name
        """Adiciona um item ao layout."""
        self._items.append(item)

    def horizontal_spacing(self):
        """Retorna o espaçamento horizontal."""
        return self._h_spacing

    def vertical_spacing(self):
        """Retorna o espaçamento vertical."""
        return self._v_spacing

    def count(self):  # pylint: disable=invalid-name
        """Retorna o número de itens no layout."""
        return len(self._items)

    def itemAt(self, index):  # pylint: disable=invalid-name
        """Retorna o item no índice fornecido."""
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):  # pylint: disable=invalid-name
        """Remove e retorna o item no índice fornecido."""
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):  # pylint: disable=invalid-name
        """Retorna as direções de expansão."""
        return Qt.Orientation(0)

    def hasHeightForWidth(self):  # pylint: disable=invalid-name
        """Retorna True se o layout tem altura para largura."""
        return True

    def heightForWidth(self, width):  # pylint: disable=invalid-name
        """Retorna a altura para a largura fornecida."""
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):  # pylint: disable=invalid-name
        """Define a geometria do layout."""
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):  # pylint: disable=invalid-name
        """Retorna a dica de tamanho."""
        return self.minimumSize()

    def minimumSize(self):  # pylint: disable=invalid-name
        """Retorna o tamanho mínimo."""
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())

        margins = self.contentsMargins()
        size += QSize(
            margins.left() + margins.right(), margins.top() + margins.bottom()
        )
        return size

    def _do_layout(self, rect, test_only):
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing_x = self.horizontal_spacing()
        spacing_y = self.vertical_spacing()

        for item in self._items:
            space_x = spacing_x
            space_y = spacing_y

            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y()
