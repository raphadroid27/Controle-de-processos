"""
Módulo para gerenciamento do banco de dados SQLite.

Este módulo fornece funcionalidades para conexão com o banco,
operações CRUD de processos, estatísticas e manutenção das
tabelas de dados do sistema.
"""

# database.py
import sqlite3
import os


def conectar_db():
    """Conecta ao banco de dados SQLite e o retorna."""
    # Caminho para o banco de dados no diretório raiz do projeto
    # database.py está em src/utils/, então precisamos subir 2 níveis
    db_path = os.path.join(os.path.dirname(
        os.path.dirname(os.path.dirname(__file__))), "processos.db")
    conn = sqlite3.connect(db_path)
    return conn


def criar_tabela_registro():
    """Cria a tabela de processos se ela ainda não existir."""
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS registro (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL,
            cliente TEXT NOT NULL,
            processo TEXT NOT NULL,
            qtde_itens INTEGER NOT NULL,
            data_entrada DATE NOT NULL,
            data_processo DATE,
            valor_pedido REAL NOT NULL,
            data_lancamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Erro ao criar tabela: {e}")
    finally:
        if conn:
            conn.close()


def adicionar_lancamento(
    usuario, cliente, processo, qtde_itens, data_entrada, data_processo, valor_pedido
):
    """Adiciona um novo registro de processo ao banco de dados."""
    # Validação dos dados de entrada
    campos_obrigatorios = [
        usuario.strip(),
        cliente.strip(),
        processo.strip(),
        qtde_itens.strip(),
        data_entrada.strip(),
        valor_pedido.strip(),
    ]

    if not all(campos_obrigatorios):
        return (
            "Erro: Campos obrigatórios: usuário, cliente, processo, "
            "qtd itens, data entrada, valor."
        )

    try:
        qtde = int(qtde_itens)
        if qtde <= 0:
            return "Erro: A quantidade de itens deve ser um número positivo."
    except ValueError:
        return "Erro: A quantidade de itens deve ser um número válido."

    try:
        valor = float(valor_pedido.replace(",", "."))
        if valor <= 0:
            return "Erro: O valor do pedido deve ser maior que zero."
    except ValueError:
        return "Erro: O valor do pedido deve ser um número válido."

    conn = conectar_db()
    cursor = conn.cursor()

    # Se data_processo estiver vazia, deixa como NULL
    data_proc = (
        data_processo.strip() if data_processo and data_processo.strip() else None
    )

    try:
        cursor.execute(
            """
        INSERT INTO registro (usuario, cliente, processo, qtde_itens, 
                            data_entrada, data_processo, valor_pedido)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                usuario.strip(),
                cliente.strip(),
                processo.strip(),
                qtde,
                data_entrada.strip(),
                data_proc,
                valor,
            ),
        )
        conn.commit()
        return "Sucesso: Processo adicionado!"
    except sqlite3.Error as e:
        return f"Erro ao inserir no banco de dados: {e}"
    finally:
        if conn:
            conn.close()


def excluir_lancamento(id_registro):
    """Exclui um registro de processo do banco de dados pelo ID."""
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


def buscar_lancamentos_filtros(usuario=None):
    """Busca registros do banco de dados com base em filtros."""
    conn = conectar_db()
    cursor = conn.cursor()

    if usuario:
        query = (
            "SELECT id, usuario, cliente, processo, qtde_itens, "
            "data_entrada, data_processo, valor_pedido FROM registro "
            "WHERE usuario = ? ORDER BY "
            "CASE WHEN data_processo IS NULL THEN 1 ELSE 0 END, "
            "data_processo ASC, data_entrada ASC"
        )
        cursor.execute(query, (usuario,))
    else:
        query = (
            "SELECT id, usuario, cliente, processo, qtde_itens, "
            "data_entrada, data_processo, valor_pedido FROM registro "
            "ORDER BY "
            "CASE WHEN data_processo IS NULL THEN 1 ELSE 0 END, "
            "data_processo ASC, data_entrada ASC"
        )
        cursor.execute(query)

    registros = cursor.fetchall()
    conn.close()
    return registros


def buscar_estatisticas(usuario=None):
    """Busca estatísticas dos processos (totais)."""
    conn = conectar_db()
    cursor = conn.cursor()

    if usuario:
        cursor.execute(
            """
        SELECT 
            COUNT(*) as total_processos,
            SUM(qtde_itens) as total_itens,
            SUM(valor_pedido) as total_valor
        FROM registro WHERE usuario = ?
        """,
            (usuario,),
        )
    else:
        cursor.execute(
            """
        SELECT 
            COUNT(*) as total_processos,
            SUM(qtde_itens) as total_itens,
            SUM(valor_pedido) as total_valor
        FROM registro
        """
        )

    resultado = cursor.fetchone()
    conn.close()

    return {
        "total_processos": resultado[0] or 0,
        "total_itens": resultado[1] or 0,
        "total_valor": resultado[2] or 0.0,
    }


def atualizar_lancamento(id_registro, cliente, processo, qtde_itens, data_entrada, data_processo, valor_pedido):
    """Atualiza um lançamento existente no banco de dados."""
    try:
        # Validações
        if not cliente or not processo:
            return "Erro: Cliente e processo são obrigatórios."

        try:
            qtde_itens = int(qtde_itens)
            if qtde_itens <= 0:
                return "Erro: Quantidade de itens deve ser um número positivo."
        except ValueError:
            return "Erro: Quantidade de itens deve ser um número válido."

        try:
            valor_pedido = float(valor_pedido.replace(",", "."))
            if valor_pedido < 0:
                return "Erro: Valor do pedido não pode ser negativo."
        except ValueError:
            return "Erro: Valor do pedido deve ser um número válido."

        # Se data_processo está vazia ou é "Não processado", usar NULL
        if not data_processo or data_processo == "Não processado":
            data_processo = None

        conn = conectar_db()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE registro 
            SET cliente = ?, processo = ?, qtde_itens = ?, 
                data_entrada = ?, data_processo = ?, valor_pedido = ?
            WHERE id = ?
            """,
            (cliente, processo, qtde_itens, data_entrada,
             data_processo, valor_pedido, id_registro)
        )

        if cursor.rowcount == 0:
            return "Erro: Registro não encontrado."

        conn.commit()
        return "Sucesso: Processo atualizado com sucesso!"

    except sqlite3.Error as e:
        return f"Erro no banco de dados: {e}"
    finally:
        if conn:
            conn.close()


def buscar_usuarios_unicos():
    """Retorna uma lista de nomes de usuarios únicos já cadastrados."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT usuario FROM registro ORDER BY usuario")
    usuarios = [row[0] for row in cursor.fetchall()]
    conn.close()
    return usuarios


def buscar_clientes_unicos():
    """Retorna uma lista de nomes de clientes únicos já cadastrados."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT cliente FROM registro ORDER BY cliente")
    clientes = [row[0] for row in cursor.fetchall()]
    conn.close()
    return clientes


# Garante que a tabela seja criada na primeira vez que o módulo foi importado
criar_tabela_registro()
