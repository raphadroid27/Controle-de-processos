"""
Gerenciamento de sessões do sistema, incluindo registro,
remoção e verificação de sessões ativas dos usuários.
"""

import socket
import uuid
from datetime import datetime, timezone

from .database import conectar_db


# ID único da sessão atual
SESSION_ID = str(uuid.uuid4())


def criar_tabela_system_control():
    """Cria a tabela de controle do sistema se ela não existir."""
    conn = conectar_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_control (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    except Exception as e:
        print(f"Erro ao criar tabela system_control: {e}")
    finally:
        if conn:
            conn.close()


def registrar_sessao(usuario_nome):
    """Registra a sessão atual no banco de dados."""
    try:
        hostname = socket.gethostname()
        conn = conectar_db()
        cursor = conn.cursor()

        # Remove sessão anterior do mesmo usuário se existir
        cursor.execute("""
            DELETE FROM system_control 
            WHERE type = 'SESSION' AND value LIKE ?
        """, (f"{usuario_nome}|%",))

        # Registra nova sessão
        session_value = f"{usuario_nome}|{hostname}"
        cursor.execute("""
            INSERT OR REPLACE INTO system_control 
            (type, key, value, last_updated) 
            VALUES (?, ?, ?, ?)
        """, ("SESSION", SESSION_ID, session_value, datetime.now(timezone.utc)))

        conn.commit()
        print(
            f"Sessão registrada: {SESSION_ID} para usuário {usuario_nome} no host {hostname}")

    except Exception as e:
        print(f"Erro ao registrar sessão: {e}")
    finally:
        if conn:
            conn.close()


def remover_sessao():
    """Remove a sessão atual do banco de dados ao fechar."""
    try:
        conn = conectar_db()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM system_control 
            WHERE type = 'SESSION' AND key = ?
        """, (SESSION_ID,))

        conn.commit()
        print(f"Sessão removida: {SESSION_ID}")

    except Exception as e:
        print(f"Erro ao remover sessão: {e}")
    finally:
        if conn:
            conn.close()


def atualizar_heartbeat_sessao():
    """Atualiza o timestamp da sessão ativa para indicar que está online."""
    try:
        conn = conectar_db()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE system_control 
            SET last_updated = ? 
            WHERE type = 'SESSION' AND key = ?
        """, (datetime.now(timezone.utc), SESSION_ID))

        conn.commit()

    except Exception as e:
        print(f"Erro ao atualizar heartbeat da sessão: {e}")
    finally:
        if conn:
            conn.close()


def obter_sessoes_ativas():
    """Retorna lista de todas as sessões ativas."""
    try:
        conn = conectar_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT key, value, last_updated 
            FROM system_control 
            WHERE type = 'SESSION'
            ORDER BY last_updated DESC
        """)

        sessoes = []
        for row in cursor.fetchall():
            session_key, session_value, last_updated = row
            if '|' in session_value:
                usuario, hostname = session_value.split('|', 1)
                sessoes.append({
                    'session_id': session_key,
                    'usuario': usuario,
                    'hostname': hostname,
                    'last_updated': last_updated
                })

        return sessoes

    except Exception as e:
        print(f"Erro ao obter sessões ativas: {e}")
        return []
    finally:
        if conn:
            conn.close()


def definir_comando_sistema(comando):
    """Define um comando do sistema (ex: 'SHUTDOWN', 'UPDATE', etc.)."""
    try:
        conn = conectar_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO system_control 
            (type, key, value, last_updated) 
            VALUES (?, ?, ?, ?)
        """, ("COMMAND", "SYSTEM_CMD", comando, datetime.now(timezone.utc)))

        conn.commit()

    except Exception as e:
        print(f"Erro ao definir comando do sistema: {e}")
    finally:
        if conn:
            conn.close()


def obter_comando_sistema():
    """Busca no banco e retorna o comando atual do sistema."""
    try:
        conn = conectar_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT value FROM system_control 
            WHERE type = 'COMMAND' AND key = 'SYSTEM_CMD'
        """)

        result = cursor.fetchone()
        return result[0] if result else None

    except Exception as e:
        print(f"Erro ao obter comando do sistema: {e}")
        return None
    finally:
        if conn:
            conn.close()


def limpar_comando_sistema():
    """Limpa o comando do sistema."""
    try:
        conn = conectar_db()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM system_control 
            WHERE type = 'COMMAND' AND key = 'SYSTEM_CMD'
        """)

        conn.commit()

    except Exception as e:
        print(f"Erro ao limpar comando do sistema: {e}")
    finally:
        if conn:
            conn.close()


def verificar_usuario_ja_logado(usuario_nome):
    """Verifica se o usuário já está logado em outra máquina."""
    try:
        conn = conectar_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT key, value FROM system_control 
            WHERE type = 'SESSION' AND value LIKE ?
        """, (f"{usuario_nome}|%",))

        result = cursor.fetchone()
        if result:
            session_key, session_value = result
            _, hostname = session_value.split('|', 1)
            current_hostname = socket.gethostname()

            # Se está na mesma máquina, permite
            if hostname == current_hostname:
                return False, None

            # Se está em máquina diferente, retorna info
            return True, {
                'session_id': session_key,
                'hostname': hostname
            }

        return False, None

    except Exception as e:
        print(f"Erro ao verificar usuário logado: {e}")
        return False, None
    finally:
        if conn:
            conn.close()
