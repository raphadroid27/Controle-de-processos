"""Utilitários para exibição de mensagens no sistema."""

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox


def show_auto_close_message(  # pylint: disable=too-many-positional-arguments
    parent,
    title: str,
    message: str,
    informative_text: str = "",
    timeout_ms: int = 3000,
    icon=QMessageBox.Icon.Information,
) -> None:
    """Exibe uma mensagem que fecha automaticamente após o timeout.

    Args:
        parent: Widget pai da mensagem
        title: Título da janela
        message: Texto principal da mensagem
        informative_text: Texto informativo adicional
        timeout_ms: Tempo em milissegundos até fechar automaticamente
        icon: Ícone da mensagem (Information, Warning, Critical, etc.)
    """
    msg = QMessageBox(parent)
    msg.setIcon(icon)
    msg.setWindowTitle(title)
    msg.setText(message)
    if informative_text:
        msg.setInformativeText(informative_text)
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.show()

    def fechar_msg():
        msg.accept()

    QTimer.singleShot(timeout_ms, fechar_msg)


def show_timed_message_box(parent, title, message, timeout_ms=10000):
    """Mostra uma caixa de mensagem com timeout automático (compatibilidade).

    Nota: Esta função mantém compatibilidade com código existente.
    Para novos usos, considere usar show_auto_close_message().
    """
    msg_box = QMessageBox(
        QMessageBox.Icon.Information,
        title,
        message,
        QMessageBox.StandardButton.Ok,
        parent,
    )

    # Timer para fechar automaticamente
    timer = QTimer(parent)
    timer.timeout.connect(msg_box.accept)
    timer.setSingleShot(True)
    timer.start(timeout_ms)

    # Mostrar diálogo (modal)
    msg_box.exec()

    # Parar timer se ainda rodando
    timer.stop()
