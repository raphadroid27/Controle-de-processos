"""
Módulo de formatação de dados.

Contém funções utilitárias para formatação de valores monetários, datas e outros dados.
"""

from datetime import datetime


def formatar_valor_monetario(valor):
    """Formata valor monetário com separador de milhares e vírgula decimal."""
    try:
        if isinstance(valor, str):
            # Limpar valor se for string
            valor_limpo = (
                valor.replace("R$", "")
                .replace(" ", "")
                .replace(".", "")
                .replace(",", ".")
            )
            valor = float(valor_limpo)

        # Formatar com separador de milhares (ponto) e decimais (vírgula)
        valor_formatado = (
            f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )
        return f"R$ {valor_formatado}"
    except (ValueError, TypeError):
        return "R$ 0,00"


def converter_data_para_banco(data_str):
    """Converte data do formato DD/MM/AAAA para AAAA-MM-DD para o banco."""
    if not data_str or data_str == "Não processado":
        return ""

    try:
        # Se já está no formato AAAA-MM-DD, retorna como está
        if "-" in data_str and len(data_str) == 10:
            return data_str

        # Converter de DD/MM/AAAA para AAAA-MM-DD
        data_obj = datetime.strptime(data_str, "%d/%m/%Y")
        return data_obj.strftime("%Y-%m-%d")
    except ValueError:
        # Se não conseguir converter, retorna como veio
        return str(data_str)


def formatar_data_para_exibicao(data_str):
    """Converte data do formato AAAA-MM-DD para DD/MM/AAAA."""
    if not data_str:
        return ""

    try:
        # Se já está no formato DD/MM/AAAA, retorna como está
        if "/" in data_str:
            return data_str

        # Converter de AAAA-MM-DD para DD/MM/AAAA
        data_obj = datetime.strptime(data_str, "%Y-%m-%d")
        return data_obj.strftime("%d/%m/%Y")
    except ValueError:
        return str(data_str)
