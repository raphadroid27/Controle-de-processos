# database.py
import sqlite3
from datetime import datetime

def conectar_db():
    """Conecta ao banco de dados SQLite e o retorna."""
    # O arquivo 'processos.db' será criado na mesma pasta se não existir.
    conn = sqlite3.connect('processos.db')
    return conn

def criar_tabela_registro():
    """Cria a tabela de produção se ela ainda não existir."""
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS registro (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL,
            cliente TEXT NOT NULL,
            numero_os TEXT NOT NULL,
            qtde_itens INTEGER NOT NULL,
            data_pedido DATE NOT NULL,
            data_lancamento DATE NOT NULL,
            valor_pedido TEXT NOT NULL
        )
        """)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Erro ao criar tabela: {e}")
    finally:
        if conn:
            conn.close()

def adicionar_lancamento(usuario, cliente, numero_os, qtde_itens, data_pedido, valor_pedido):
    """Adiciona um novo registro de produção ao banco de dados."""
    # Validação dos dados de entrada
    if not usuario.strip() or not cliente.strip() or not numero_os.strip() or not qtde_itens.strip() or not data_pedido.strip() or not valor_pedido.strip():
        return "Erro: Todos os campos são obrigatórios."
    try:
        qtde = int(qtde_itens)
        if qtde <= 0:
            return "Erro: A quantidade de itens deve ser um número positivo."
    except ValueError:
        return "Erro: A quantidade de itens deve ser um número válido."

    conn = conectar_db()
    cursor = conn.cursor()
    data_hoje = datetime.now().date()
    
    try:
        cursor.execute("""
        INSERT INTO registro (usuario, cliente, numero_os, qtde_itens, data_lancamento, data_pedido, valor_pedido)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (usuario.strip(), cliente.strip(), numero_os.strip(), qtde, data_hoje, data_pedido.strip(), valor_pedido.strip()))
        conn.commit()
        return "Sucesso: Lançamento adicionado!"
    except sqlite3.Error as e:
        return f"Erro ao inserir no banco de dados: {e}"
    finally:
        if conn:
            conn.close()

def excluir_lancamento(id_registro):
    """Exclui um registro de produção do banco de dados pelo ID."""
    conn = conectar_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM registro WHERE id = ?", (id_registro,))
        conn.commit()
        if cursor.rowcount == 0:
            return "Erro: Registro não encontrado."
        return "Sucesso: Registro excluído!"
    except sqlite3.Error as e:
        return f"Erro ao excluir registro: {e}"
    finally:
        if conn:
            conn.close()

def buscar_lancamentos_filtros():
    """Busca registros do banco de dados com base em um filtro de cliente."""
    conn = conectar_db()
    cursor = conn.cursor()

    query = "SELECT id, usuario, cliente, numero_os, qtde_itens, data_lancamento, data_pedido FROM registro"
    params = []

    query += " ORDER BY data_lancamento DESC"

    cursor.execute(query, params)
    registros = cursor.fetchall()
    conn.close()
    return registros

def buscar_usuarios_unicos():
    """Retorna uma lista de nomes de usuarios únicos já cadastrados."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT usuario FROM registro ORDER BY usuario")
    usuarios = [row[0] for row in cursor.fetchall()]
    conn.close()
    return usuarios

# Garante que a tabela seja criada na primeira vez que o módulo for importado
criar_tabela_registro()
