"""
Módulo para gerenciamento de usuários do sistema.

Este módulo fornece funcionalidades para autenticação, criação,
edição e gerenciamento de usuários, incluindo hash de senhas
e controle de permissões administrativas.
"""

import hashlib
import sqlite3

from utils.database import conectar_db


def criar_tabela_usuario():
    """Cria a tabela de usuários no banco de dados."""
    conn = conectar_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            admin BOOLEAN DEFAULT FALSE
        )
        """
        )
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

        cursor.execute(
            """
        INSERT INTO usuario (nome, senha, admin)
        VALUES (?, ?, ?)
        """,
            (nome, senha_hash, admin),
        )
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
            "SELECT nome, admin FROM usuario WHERE nome = ? AND senha = ?",
            (nome, senha_hash),
        )
        usuario = cursor.fetchone()

        if usuario:
            return {"sucesso": True, "nome": usuario[0], "admin": bool(usuario[1])}
        return {"sucesso": False, "mensagem": "Usuário ou senha inválidos"}
    except sqlite3.Error as e:
        return {"sucesso": False, "mensagem": f"Erro no banco de dados: {e}"}
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


def resetar_senha_usuario(nome, nova_senha="nova_senha"):
    """Reseta a senha de um usuário pelo nome."""
    conn = conectar_db()
    cursor = conn.cursor()

    try:
        if nova_senha == "nova_senha":
            # Senha padrão para reset
            senha_hash = nova_senha
        else:
            # Nova senha personalizada
            senha_hash = hash_senha(nova_senha)

        cursor.execute(
            "UPDATE usuario SET senha = ? WHERE nome = ?", (senha_hash, nome)
        )
        conn.commit()

        if cursor.rowcount > 0:
            return "Sucesso: Senha resetada com sucesso."
        return "Erro: Usuário não encontrado."
    except sqlite3.Error as e:
        return f"Erro ao resetar senha: {e}"
    finally:
        if conn:
            conn.close()


def excluir_usuario_por_id(user_id):
    """Exclui um usuário pelo ID."""
    conn = conectar_db()
    cursor = conn.cursor()

    try:
        # Verifica se o usuário existe e se é admin
        cursor.execute("SELECT admin FROM usuario WHERE id = ?", (user_id,))
        usuario = cursor.fetchone()

        if not usuario:
            return "Erro: Usuário não encontrado."

        if usuario[0]:  # Se for admin
            return "Erro: Não é possível excluir um administrador."

        cursor.execute("DELETE FROM usuario WHERE id = ?", (user_id,))
        conn.commit()

        if cursor.rowcount > 0:
            return "Sucesso: Usuário excluído com sucesso."
        return "Erro: Não foi possível excluir o usuário."
    except sqlite3.Error as e:
        return f"Erro ao excluir usuário: {e}"
    finally:
        if conn:
            conn.close()


def alterar_senha_usuario(nome, senha_atual, nova_senha):
    """Permite ao usuário alterar sua própria senha."""
    conn = conectar_db()
    cursor = conn.cursor()

    try:
        # Verifica a senha atual
        senha_atual_hash = hash_senha(senha_atual)
        cursor.execute(
            "SELECT id FROM usuario WHERE nome = ? AND senha = ?",
            (nome, senha_atual_hash),
        )

        if not cursor.fetchone():
            return "Erro: Senha atual incorreta."

        # Atualiza para a nova senha
        nova_senha_hash = hash_senha(nova_senha)
        cursor.execute(
            "UPDATE usuario SET senha = ? WHERE nome = ?", (
                nova_senha_hash, nome)
        )
        conn.commit()

        return "Sucesso: Senha alterada com sucesso."
    except sqlite3.Error as e:
        return f"Erro ao alterar senha: {e}"
    finally:
        if conn:
            conn.close()


def verificar_senha_reset(nome):
    """Verifica se o usuário precisa redefinir a senha."""
    conn = conectar_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT senha FROM usuario WHERE nome = ?", (nome,))
        usuario = cursor.fetchone()

        if usuario and usuario[0] == "nova_senha":
            return True
        return False
    except sqlite3.Error as e:
        print(f"Erro ao verificar senha de reset: {e}")
        return False
    finally:
        if conn:
            conn.close()


def excluir_usuario(nome):
    """Exclui um usuário pelo nome."""
    conn = conectar_db()
    cursor = conn.cursor()

    try:
        # Verifica se o usuário existe e se é admin
        cursor.execute("SELECT admin FROM usuario WHERE nome = ?", (nome,))
        usuario = cursor.fetchone()

        if not usuario:
            return "Erro: Usuário não encontrado."

        if usuario[0]:  # Se for admin
            return "Erro: Não é possível excluir um administrador."

        cursor.execute("DELETE FROM usuario WHERE nome = ?", (nome,))
        conn.commit()

        if cursor.rowcount > 0:
            return "Sucesso: Usuário excluído com sucesso."
        return "Erro: Usuário não encontrado."
    except sqlite3.Error as e:
        return f"Erro ao excluir usuário: {e}"
    finally:
        if conn:
            conn.close()


def resetar_senha_usuario(nome, nova_senha="nova_senha"):
    """Reseta a senha de um usuário pelo nome."""
    conn = conectar_db()
    cursor = conn.cursor()

    try:
        if nova_senha == "nova_senha":
            # Senha padrão para reset
            senha_hash = nova_senha
        else:
            # Nova senha personalizada
            senha_hash = hash_senha(nova_senha)

        cursor.execute(
            "UPDATE usuario SET senha = ? WHERE nome = ?", (senha_hash, nome)
        )
        conn.commit()

        if cursor.rowcount > 0:
            return "Sucesso: Senha resetada com sucesso."
        return "Erro: Usuário não encontrado."
    except sqlite3.Error as e:
        return f"Erro ao resetar senha: {e}"
    finally:
        if conn:
            conn.close()


# Garante que a tabela seja criada na primeira vez que o módulo for importado
criar_tabela_usuario()
