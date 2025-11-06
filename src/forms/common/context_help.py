"""Conteúdo centralizado de ajuda contextual para a aplicação."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, Iterable, Iterator, List, Optional, Tuple

from PySide6.QtWidgets import QMessageBox, QWidget

HelpEntry = Tuple[str, str]
ManualLauncher = Callable[[Optional[QWidget], Optional[str], bool], object]

_manual_launcher: ManualLauncher | None = None

_DEFAULT_ENTRY: HelpEntry = (
    "Ajuda indisponível",
    "<p>Conteúdo ainda não disponível para esta seção.</p>",
)

_HELP_CONTENT: Dict[str, HelpEntry] = {}

_HELP_DIR = Path(__file__).with_name("help_content")

_SECTION_FILE_MAP = {
    "manual": "manual.html",
    "visao_geral": "visao_geral.html",
    "filtros": "filtros.html",
    "totais": "totais.html",
    "dashboard": "dashboard.html",
    "autenticacao": "autenticacao.html",
    "admin": "admin.html",
    "sobre": "sobre.html",
}


def _extract_title(html: str) -> Optional[str]:
    start = html.find("<h2")
    if start == -1:
        return None
    end = html.find("</h2>", start)
    if end == -1:
        return None
    end += len("</h2>")
    return html[start:end]


def _load_help_contents() -> None:
    """Carrega o conteúdo dos arquivos HTML em cache em memória."""

    if _HELP_CONTENT:
        return

    for key, filename in _SECTION_FILE_MAP.items():
        path = _HELP_DIR / filename
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue

        title = _extract_title(text) or f"<h2>{key.title()}</h2>"
        body = text
        stripped = body.lstrip()
        if title and stripped.startswith(title):
            body = stripped[len(title) :].lstrip()
        _HELP_CONTENT[key] = (title, body)


def register_manual_launcher(launcher: ManualLauncher) -> None:
    """Registra função responsável por apresentar ou focar o manual."""

    global _manual_launcher  # pylint: disable=global-statement
    _manual_launcher = launcher


def show_help(key: str, parent: QWidget | None = None) -> None:
    """Exibe o conteúdo de ajuda associado à chave informada."""

    _load_help_contents()

    try:
        if _manual_launcher is not None:
            _manual_launcher(parent, key, True)
            return
    except RuntimeError:  # pragma: no cover - fallback
        pass

    title, message = _HELP_CONTENT.get(key, _DEFAULT_ENTRY)
    QMessageBox.information(parent, title, message)


def get_help_entry(key: str) -> HelpEntry:
    """Retorna a entrada de ajuda correspondente à chave fornecida."""

    _load_help_contents()
    return _HELP_CONTENT.get(key, _DEFAULT_ENTRY)


def iter_help_entries(
    keys: Iterable[str] | None = None,
    *,
    include_missing: bool = True,
) -> Iterator[Tuple[str, HelpEntry]]:
    """Itera sobre as entradas de ajuda no manual."""

    _load_help_contents()

    if keys is not None:
        seen: List[str] = []
        for key in keys:
            if key in seen:
                continue
            entry = _HELP_CONTENT.get(key)
            if entry is None:
                if include_missing:
                    seen.append(key)
                    yield key, _DEFAULT_ENTRY
                continue
            seen.append(key)
            yield key, entry

        for key, entry in _HELP_CONTENT.items():
            if key not in seen:
                yield key, entry
        return

    yield from _HELP_CONTENT.items()
