"""Funções utilitárias para manipulação do tempo de corte."""

from __future__ import annotations

from typing import Optional, Tuple

__all__ = ["normalizar_tempo_corte", "tempo_corte_para_segundos"]


def normalizar_tempo_corte(valor: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Normaliza um valor de tempo de corte para o formato ``HH:MM:SS``.

    Retorna uma tupla ``(valor_normalizado, mensagem_erro)``. Caso o valor seja
    ``None`` ou vazio, a normalização resulta em ``None`` e não há mensagem de
    erro. Se o valor não estiver em um formato válido, o valor normalizado será
    ``None`` e a mensagem conterá o motivo da falha.
    """
    if valor is None:
        return None, None

    valor = valor.strip()
    if not valor:
        return None, None

    partes = valor.split(":")
    if len(partes) != 3:
        return None, "Erro: Tempo de corte deve estar no formato HH:MM:SS."

    try:
        horas, minutos, segundos = (int(parte) for parte in partes)
    except ValueError:
        return None, "Erro: Tempo de corte deve conter apenas números."

    if horas < 0 or not 0 <= minutos < 60 or not 0 <= segundos < 60:
        return None, "Erro: Tempo de corte deve estar no formato HH:MM:SS."

    horas_formatadas = str(horas).zfill(2)
    tempo_formatado = f"{horas_formatadas}:{minutos:02d}:{segundos:02d}"
    return tempo_formatado, None


def tempo_corte_para_segundos(valor: Optional[str]) -> int:
    """Convert time duration from ``HH:MM:SS`` format to seconds."""
    if not valor:
        return 0

    partes = valor.split(":")
    if len(partes) != 3:
        return 0

    try:
        horas, minutos, segundos = (int(parte) for parte in partes)
    except ValueError:
        return 0

    return horas * 3600 + minutos * 60 + segundos
