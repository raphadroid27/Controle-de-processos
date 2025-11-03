"""
Módulo de formatação de dados.

Contém funções utilitárias para formatação de valores monetários, datas e outros dados.
"""

from datetime import datetime


def normalizar_valor_padrao_brasileiro(valor: str) -> str:
    """Normaliza texto numérico para o formato monetário brasileiro simples."""
    digitos = "".join(ch for ch in valor if ch.isdigit())
    if not digitos:
        return ""

    centavos = digitos[-2:].rjust(2, "0")
    parte_inteira = digitos[:-2] or "0"
    parte_inteira_formatada = f"{int(parte_inteira):,}".replace(",", ".")
    return f"{parte_inteira_formatada},{centavos}"


def formatar_valor_monetario(valor: float | str) -> str:
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
            f"{valor:,.2f}".replace(",", "X").replace(
                ".", ",").replace("X", ".")
        )
        return f"R$ {valor_formatado}"
    except (ValueError, TypeError):
        return "R$ 0,00"


def converter_data_para_banco(data_str):
    """Convert data from DD/MM/YYYY format to YYYY-MM-DD for database."""
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


def formatar_data_para_exibicao(data_str: str) -> str:
    """Convert data from YYYY-MM-DD format to DD/MM/YYYY for display."""
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


def formatar_numero_decimal(valor: float, casas_decimais: int = 2) -> str:
    """
    Formata um número decimal com separadores brasileiros.

    Args:
        valor: O valor numérico a ser formatado
        casas_decimais: Número de casas decimais (padrão: 2)

    Returns:
        String formatada com separador de milhares (ponto) e decimal (vírgula)
    """
    formato = f"{valor:,.{casas_decimais}f}"
    return formato.replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_segundos(segundos: int) -> str:
    """
    Formata segundos em formato HH:MM:SS.

    Args:
        segundos: Total de segundos a serem formatados

    Returns:
        String no formato HH:MM:SS
    """
    horas, resto = divmod(int(segundos), 3600)
    minutos, segundos = divmod(resto, 60)
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"


def segundos_para_horas(segundos: float) -> float:
    """
    Converte segundos para horas.

    Args:
        segundos: Valor em segundos

    Returns:
        Valor em horas (float)
    """
    return segundos / 3600.0
