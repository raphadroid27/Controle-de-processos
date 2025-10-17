"""Utilitários para edição e extração de dados da tabela de processos."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidget

from ...utils.formatters import converter_data_para_banco

__all__ = [
    "LinhaProcessoEdicao",
    "validar_edicao_celula",
    "extrair_campos_linha",
    "obter_registro_id",
]


@dataclass
class LinhaProcessoEdicao:
    """Representa os valores de uma linha da tabela após edição."""

    cliente: str
    processo: str
    qtde_itens: str
    data_entrada: str
    data_processo: str
    tempo_corte: str
    observacoes: str
    valor_pedido: str

    def to_update_kwargs(self) -> dict[str, str]:
        """Retorna os campos prontos para atualização no banco."""
        return {
            "cliente": self.cliente,
            "processo": self.processo,
            "qtde_itens": self.qtde_itens,
            "data_entrada": self.data_entrada,
            "data_processo": self.data_processo,
            "tempo_corte": self.tempo_corte,
            "observacoes": self.observacoes,
            "valor_pedido": self.valor_pedido,
        }


def validar_edicao_celula(
    col_editada: int, valor_editado: str
) -> Tuple[bool, str | None]:
    """Valida o conteúdo da célula editada."""
    validators = {
        2: _validar_qtde,
        3: _validar_data_entrada,
        4: _validar_data_processo,
        5: _validar_tempo_corte,
        6: _validar_observacoes,
        7: _validar_valor,
    }

    validador = validators.get(col_editada)
    if not validador:
        return True, None
    return validador(valor_editado)


def extrair_campos_linha(
    tabela: QTableWidget,
    row: int,
    col_offset: int,
) -> LinhaProcessoEdicao:
    """Extrai os campos da linha informada, convertendo para formatos de banco."""
    cliente = _texto_item(tabela, row, col_offset).upper()
    processo = _texto_item(tabela, row, col_offset + 1)
    qtde_itens = _texto_item(tabela, row, col_offset + 2)

    data_entrada_text = _texto_item(tabela, row, col_offset + 3)
    data_processo_text = _texto_item(tabela, row, col_offset + 4)
    tempo_corte_text = _texto_item(tabela, row, col_offset + 5)
    observacoes_text = _texto_item(tabela, row, col_offset + 6)
    valor_text = _texto_item(tabela, row, col_offset + 7)

    data_entrada = converter_data_para_banco(data_entrada_text)
    if data_processo_text == "Não processado" or not data_processo_text:
        data_processo = ""
    else:
        data_processo = converter_data_para_banco(data_processo_text)

    valor_pedido = valor_text.replace("R$", "").strip()

    return LinhaProcessoEdicao(
        cliente,
        processo,
        qtde_itens,
        data_entrada,
        data_processo,
        tempo_corte_text,
        observacoes_text,
        valor_pedido,
    )


def obter_registro_id(tabela: QTableWidget, row: int, is_admin: bool) -> int | None:
    """Obtém o ID do registro armazenado na linha da tabela."""
    coluna_id = 1 if is_admin else 0
    item = tabela.item(row, coluna_id)
    if not item:
        return None
    return item.data(Qt.ItemDataRole.UserRole)


def _texto_item(tabela: QTableWidget, row: int, col: int) -> str:
    item = tabela.item(row, col)
    if not item:
        raise ValueError("Item da tabela não encontrado.")
    return item.text().strip()


def _validar_qtde(valor_editado: str) -> Tuple[bool, str | None]:
    try:
        qtde_test = int(valor_editado)
        if qtde_test <= 0:
            raise ValueError
    except ValueError:
        return False, "Quantidade de itens deve ser um número inteiro positivo."
    return True, None


def _validar_data_entrada(valor_editado: str) -> Tuple[bool, str | None]:
    return _validar_data(valor_editado, "entrada")


def _validar_data_processo(valor_editado: str) -> Tuple[bool, str | None]:
    return _validar_data(valor_editado, "processo")


def _validar_data(valor_editado: str, tipo: str) -> Tuple[bool, str | None]:
    if not valor_editado or valor_editado == "Não processado":
        return True, None

    try:
        data_obj = datetime.strptime(valor_editado, "%d/%m/%Y")
    except ValueError:
        mensagem = "Data de entrada" if tipo == "entrada" else "Data de processo"
        return False, f"{mensagem} deve estar no formato DD/MM/AAAA."

    if data_obj.date() > datetime.now().date():
        mensagem = "Data de entrada" if tipo == "entrada" else "Data de processo"
        return False, f"{mensagem} não pode ser maior que a data atual."

    return True, None


def _validar_tempo_corte(valor_editado: str) -> Tuple[bool, str | None]:
    if not valor_editado:
        return True, None

    partes = valor_editado.split(":")
    if len(partes) != 3:
        return False, "Tempo de corte deve estar no formato HH:MM:SS."

    try:
        horas, minutos, segundos = (int(p) for p in partes)
    except ValueError:
        return False, "Tempo de corte deve conter apenas números."

    if horas < 0 or not 0 <= minutos < 60 or not 0 <= segundos < 60:
        return False, "Tempo de corte deve estar no formato HH:MM:SS."

    return True, None


def _validar_observacoes(observacoes_editadas: str) -> Tuple[bool, str | None]:
    if len(observacoes_editadas) > 500:
        return False, "Observações devem ter no máximo 500 caracteres."
    return True, None


def _validar_valor(valor_editado: str) -> Tuple[bool, str | None]:
    try:
        valor_limpo = (
            valor_editado.replace("R$", "")
            .replace(" ", "")
            .replace(".", "")
            .replace(",", ".")
        )
        valor_test = float(valor_limpo)
        if valor_test < 0:
            raise ValueError
    except ValueError:
        return False, "Valor deve ser um número válido e não negativo."
    return True, None
