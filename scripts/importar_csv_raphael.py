"""Script para importar lançamentos de CSV para o banco do usuário raphael."""

import csv
import sys
from pathlib import Path

# pylint: disable=import-error
from src.utils.database.crud import adicionar_lancamento
from src.utils.database.models import Lancamento

# Adicionar o diretório raiz ao sys.path para importar módulos src
sys.path.insert(0, str(Path(__file__).parent.parent))


def processar_valor_qtde(qtde_itens_str):
    """Processa a quantidade de itens."""
    try:
        qtde_float = float(qtde_itens_str)
        return str(int(qtde_float))
    except ValueError:
        return "1"  # default se inválido


def processar_valor(valor_str):
    """Processa o valor."""
    try:
        valor = float(valor_str.replace(",", "."))
        return str(valor if valor != 0 else 0.001)
    except ValueError:
        return "0.001"


def criar_lancamento(row, usuario):
    """Cria um objeto Lancamento a partir de uma linha do CSV."""
    cliente = row.get("Cliente", row.get("\ufeffCliente", "")).strip()
    processo = row.get("Proposta", "").strip()
    qtde_itens_str = row.get("Itens /Quant total", "").strip()
    data_entrada = row.get("Data entrada", "").strip()
    data_processo = row.get("Data processo", "").strip()
    valor_str = row.get("Valor", "").strip()

    qtde_itens = processar_valor_qtde(qtde_itens_str)
    valor = processar_valor(valor_str)

    return Lancamento(
        usuario=usuario,
        cliente=cliente,
        processo=processo,
        qtde_itens=qtde_itens,
        data_entrada=data_entrada,
        data_processo=data_processo if data_processo else None,
        valor_pedido=valor,
        tempo_corte=None,
    )


def detectar_encoding(arquivo):
    """Detecta o encoding do arquivo CSV."""
    encodings = ["utf-8", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            with open(arquivo, "r", encoding=enc) as f:
                csv.DictReader(f)
                next(csv.DictReader(f))  # Tentar ler uma linha
                return enc
        except (UnicodeDecodeError, StopIteration):
            continue
    return None


def processar_arquivo(arquivo, usuario, total_linhas, sucessos, erros):
    """Processa um arquivo CSV."""
    print(f"\nProcessando {arquivo.name}...")
    enc_usado = detectar_encoding(arquivo)
    if enc_usado is None:
        print(
            f"Erro: Não foi possível ler {arquivo.name} com encodings testados.")
        return total_linhas, sucessos, erros

    with open(arquivo, "r", encoding=enc_usado) as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_linhas += 1
            lanc = criar_lancamento(row, usuario)
            resultado = adicionar_lancamento(lanc)
            if resultado.startswith("Sucesso"):
                sucessos += 1
            else:
                erros += 1
                print(
                    f"Erro na linha {total_linhas} de {arquivo.name}: {resultado}")
    return total_linhas, sucessos, erros


def importar_csv_usuario():
    """Importa todos os CSVs de uma pasta para o banco do usuário."""

    pasta_csv = Path(__file__).parent.parent / \
        "dados" / "lancamento_raphael_2025"
    usuario = "Raphael"

    arquivos = list(pasta_csv.glob("*.csv"))
    total_arquivos = len(arquivos)
    total_linhas = 0
    sucessos = 0
    erros = 0

    print(f"Encontrados {total_arquivos} arquivos CSV.")

    for arquivo in arquivos:
        total_linhas, sucessos, erros = processar_arquivo(
            arquivo, usuario, total_linhas, sucessos, erros
        )

    print("\nResumo da importação:")
    print(f"Total de arquivos processados: {total_arquivos}")
    print(f"Total de linhas processadas: {total_linhas}")
    print(f"Sucessos: {sucessos}")
    print(f"Erros: {erros}")


if __name__ == "__main__":
    importar_csv_usuario()
