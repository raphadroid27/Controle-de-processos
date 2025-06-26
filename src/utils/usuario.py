import sqlite3
from utils.database import conectar_db

def criar_tabela_usuario():
    """Cria a tabela de usuários no banco de dados."""
    conn = conectar_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            senha TEXT NOT NULL,
            admin BOOLEAN DEFAULT FALSE
        )
        """)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Erro ao criar tabela: {e}")
    finally:
        if conn:
            conn.close()

def inserir_usuario(nome, senha, admin=False):
    """Insere um novo usuário na tabela."""

    if not nome.strip() or not senha.strip():
        return "Nome e senha são obrigatórios."

    conn = conectar_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        INSERT INTO usuario (nome, senha, admin)
        VALUES (?, ?, ?)
        """, (nome, senha, admin))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Erro ao inserir usuário: {e}")
    finally:
        if conn:
            conn.close()

criar_tabela_usuario()
