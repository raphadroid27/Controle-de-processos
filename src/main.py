"""Ponto de entrada principal para o aplicativo de Controle de Pedidos."""

import sys

try:
    from app import ControleProcessosApp
except ImportError as e:
    print(f"Erro ao importar ControleProcessosApp: {e}")
    sys.exit(1)

if __name__ == "__main__":
    app = ControleProcessosApp()
    sys.exit(app.run())
