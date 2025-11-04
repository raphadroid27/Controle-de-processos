"""Módulo principal da aplicação de Controle de Pedidos."""

import sys

from PySide6.QtWidgets import QApplication, QDialog

from src.login_dialog import LoginDialog
from src.ui.main_window import MainWindow
from src.ui.theme_manager import ThemeManager
from src.utils import database as db
from src.utils import ipc_manager
from src.utils.usuario import criar_tabela_usuario


class ControleProcessosApp:
    """Classe principal da aplicação."""

    def __init__(self):
        """Inicializa a aplicação."""
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Controle de Pedidos")
        self.app.setOrganizationName("Controle de Pedidos")
        self.app.setOrganizationDomain("controle-de-pedidos.local")

        self.theme_manager = ThemeManager.instance()
        self.theme_manager.initialize()
        self.main_window = None

        # Inicialização explícita das tabelas para evitar ciclos de import
        db.inicializar_todas_tabelas()
        ipc_manager.ensure_ipc_dirs_exist()
        criar_tabela_usuario()
        # db.limpar_bancos_orfaos()

    def run(self):
        """Executa a aplicação."""
        if self.mostrar_login() == 0:
            return 0
        return self.app.exec()

    def mostrar_login(self):
        """Mostra a tela de login e abre a janela principal ao autenticar."""
        login_dialog = LoginDialog()

        if login_dialog.exec() == QDialog.Accepted:
            if self.main_window:
                self.main_window.close()

            self.main_window = MainWindow(
                login_dialog.usuario_logado,
                login_dialog.is_admin,
            )
            self.main_window.logout_requested.connect(self.mostrar_login)
            self.main_window.show()
            return 1
        return 0


def main():
    """Ponto de entrada para execução direta da aplicação."""
    app = ControleProcessosApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
