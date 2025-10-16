"""
Delegates personalizados para edição de células na tabela.

Contém delegates para edição de datas com calendário e outros tipos de dados.
"""

from datetime import datetime

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QDateEdit, QStyledItemDelegate


class DateEditDelegate(QStyledItemDelegate):
    """Delegate personalizado para edição de datas com calendário."""

    def __init__(self, parent=None):  # pylint: disable=useless-parent-delegation
        """Inicializa o delegate de edição de data."""
        super().__init__(parent)

    def createEditor(
        self, parent, option, index
    ):  # pylint: disable=invalid-name,unused-argument
        """Cria o editor de data com calendário."""
        editor = QDateEdit(parent)
        editor.setCalendarPopup(True)
        editor.setDisplayFormat("dd/MM/yyyy")

        # Definir data máxima como hoje
        editor.setMaximumDate(QDate.currentDate())

        # Verificar se é uma coluna de data processo (pode estar vazia)
        data_texto = index.data()
        if data_texto == "Não processado" or not data_texto:
            editor.setSpecialValueText("Não processado")
            editor.setDate(QDate())  # Data nula
        else:
            # Tentar converter a data do formato DD/MM/AAAA
            try:
                if "/" in data_texto:
                    data_obj = datetime.strptime(data_texto, "%d/%m/%Y")
                else:
                    # Formato AAAA-MM-DD do banco
                    data_obj = datetime.strptime(data_texto, "%Y-%m-%d")
                editor.setDate(QDate(data_obj.year, data_obj.month, data_obj.day))
            except (ValueError, AttributeError):
                editor.setDate(QDate.currentDate())

        return editor

    def setEditorData(self, editor, index):  # pylint: disable=invalid-name
        """Define os dados no editor."""
        value = index.data()
        if value == "Não processado" or not value:
            editor.setDate(QDate())  # Data nula
        else:
            try:
                if "/" in value:
                    data_obj = datetime.strptime(value, "%d/%m/%Y")
                else:
                    data_obj = datetime.strptime(value, "%Y-%m-%d")
                editor.setDate(QDate(data_obj.year, data_obj.month, data_obj.day))
            except (ValueError, AttributeError):
                editor.setDate(QDate.currentDate())

    def setModelData(self, editor, model, index):  # pylint: disable=invalid-name
        """Define os dados do editor no modelo."""
        date = editor.date()
        if date.isNull() or not date.isValid():
            model.setData(index, "Não processado")
        else:
            # Formatar como DD/MM/AAAA para exibição
            formatted_date = date.toString("dd/MM/yyyy")
            model.setData(index, formatted_date)

    def updateEditorGeometry(
        self, editor, option, index
    ):  # pylint: disable=invalid-name,unused-argument
        """Atualiza a geometria do editor."""
        editor.setGeometry(option.rect)
