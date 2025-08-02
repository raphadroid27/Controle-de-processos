import sqlite3
import hashlib
from utils.database import conectar_db


def criar_tabela_usuario():
    """Cria a tabela de usuários no banco de dados."""
    conn = conectar_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
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


def hash_senha(senha):
    """Gera hash da senha para armazenamento seguro."""
    return hashlib.sha256(senha.encode()).hexdigest()


def inserir_usuario(nome, senha, admin=False):
    """Insere um novo usuário na tabela."""
    if not nome.strip() or not senha.strip():
        return "Nome e senha são obrigatórios."

    conn = conectar_db()
    cursor = conn.cursor()

    try:
        # Verifica se o usuário já existe
        cursor.execute("SELECT nome FROM usuario WHERE nome = ?", (nome,))
        if cursor.fetchone():
            return "Erro: Usuário já existe."

        # Hash da senha antes de salvar
        senha_hash = hash_senha(senha)

        cursor.execute("""
        INSERT INTO usuario (nome, senha, admin)
        VALUES (?, ?, ?)
        """, (nome, senha_hash, admin))
        conn.commit()
        return "Sucesso: Usuário criado com sucesso."
    except sqlite3.Error as e:
        return f"Erro ao inserir usuário: {e}"
    finally:
        if conn:
            conn.close()


def verificar_login(nome, senha):
    """Verifica se o login é válido."""
    conn = conectar_db()
    cursor = conn.cursor()

    try:
        senha_hash = hash_senha(senha)
        cursor.execute(
            "SELECT nome, admin FROM usuario WHERE nome = ? AND senha = ?", (nome, senha_hash))
        usuario = cursor.fetchone()

        if usuario:
            return {
                'sucesso': True,
                'nome': usuario[0],
                'admin': bool(usuario[1])
            }
        else:
            return {'sucesso': False, 'mensagem': 'Usuário ou senha inválidos'}
    except sqlite3.Error as e:
        return {'sucesso': False, 'mensagem': f'Erro no banco de dados: {e}'}
    finally:
        if conn:
            conn.close()


def verificar_admin_existente():
    """Verifica se já existe um usuário admin no banco de dados."""
    conn = conectar_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM usuario WHERE admin = 1")
        count = cursor.fetchone()[0]
        return count > 0
    except sqlite3.Error as e:
        print(f"Erro ao verificar admin: {e}")
        return False
    finally:
        if conn:
            conn.close()


def listar_usuarios():
    """Lista todos os usuários cadastrados."""
    conn = conectar_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, nome, admin FROM usuario ORDER BY nome")
        usuarios = cursor.fetchall()
        return usuarios
    except sqlite3.Error as e:
        print(f"Erro ao listar usuários: {e}")
        return []
    finally:
        if conn:
            conn.close()


# Garante que a tabela seja criada na primeira vez que o módulo for importado
criar_tabela_usuario()
