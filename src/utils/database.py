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
            "data_entrada, data_processo, valor_pedido, data_lancamento FROM registro "
            "WHERE usuario = ? ORDER BY "
            "CASE WHEN data_processo IS NULL THEN 1 ELSE 0 END, "
            "data_processo ASC, data_entrada ASC"
        )
        cursor.execute(query, (usuario,))
    else:
        query = (
            "SELECT id, usuario, cliente, processo, qtde_itens, "
            "data_entrada, data_processo, valor_pedido, data_lancamento FROM registro "
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


def buscar_clientes_unicos_por_usuario(usuario=None):
    """Retorna uma lista de clientes únicos filtrados por usuário."""
    conn = conectar_db()
    cursor = conn.cursor()

    if usuario:
        cursor.execute(
            "SELECT DISTINCT cliente FROM registro WHERE usuario = ? ORDER BY cliente",
            (usuario,)
        )
    else:
        cursor.execute(
            "SELECT DISTINCT cliente FROM registro ORDER BY cliente")

    clientes = [row[0] for row in cursor.fetchall()]
    conn.close()
    return clientes


def buscar_processos_unicos_por_usuario(usuario=None):
    """Retorna uma lista de processos únicos filtrados por usuário."""
    conn = conectar_db()
    cursor = conn.cursor()

    if usuario:
        cursor.execute(
            "SELECT DISTINCT processo FROM registro WHERE usuario = ? ORDER BY processo",
            (usuario,)
        )
    else:
        cursor.execute(
            "SELECT DISTINCT processo FROM registro ORDER BY processo")

    processos = [row[0] for row in cursor.fetchall()]
    conn.close()
    return processos


def buscar_lancamentos_filtros_completos(usuario=None, cliente=None, processo=None, data_inicio=None, data_fim=None):
    """Busca lançamentos aplicando múltiplos filtros com busca parcial."""
    conn = conectar_db()
    cursor = conn.cursor()

    # Montar query dinamicamente baseado nos filtros
    conditions = []
    params = []

    if usuario:
        conditions.append("usuario = ?")
        params.append(usuario)

    if cliente:
        conditions.append("UPPER(cliente) LIKE ?")
        params.append(f"{cliente.upper()}%")

    if processo:
        conditions.append("UPPER(processo) LIKE ?")
        params.append(f"{processo.upper()}%")

    if data_inicio and data_fim:
        conditions.append("data_processo BETWEEN ? AND ?")
        params.append(data_inicio)
        params.append(data_fim)

    query = "SELECT * FROM registro"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY data_lancamento"

    cursor.execute(query, params)
    registros = cursor.fetchall()
    conn.close()
    return registros


def buscar_estatisticas_completas(usuario=None, cliente=None, processo=None, data_inicio=None, data_fim=None):
    """Calcula estatísticas aplicando múltiplos filtros com busca parcial."""
    conn = conectar_db()
    cursor = conn.cursor()

    # Montar query dinamicamente baseado nos filtros
    conditions = []
    params = []

    if usuario:
        conditions.append("usuario = ?")
        params.append(usuario)

    if cliente:
        conditions.append("UPPER(cliente) LIKE ?")
        params.append(f"{cliente.upper()}%")

    if processo:
        conditions.append("UPPER(processo) LIKE ?")
        params.append(f"{processo.upper()}%")

    if data_inicio and data_fim:
        conditions.append("data_processo BETWEEN ? AND ?")
        params.append(data_inicio)
        params.append(data_fim)

    query = "SELECT COUNT(*) as total_processos, SUM(qtde_itens) as total_itens, SUM(valor_pedido) as total_valor FROM registro"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    cursor.execute(query, params)
    resultado = cursor.fetchone()
    conn.close()

    return {
        "total_processos": resultado[0] if resultado[0] else 0,
        "total_itens": resultado[1] if resultado[1] else 0,
        "total_valor": resultado[2] if resultado[2] else 0.0,
    }


def buscar_meses_unicos(usuario=None):
    """Busca os meses únicos que possuem registros no banco de dados."""
    conn = conectar_db()
    cursor = conn.cursor()

    conditions = []
    params = []

    if usuario:
        conditions.append("usuario = ?")
        params.append(usuario)

    query = "SELECT DISTINCT strftime('%m', data_processo) as mes FROM registro"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY mes"

    cursor.execute(query, params)
    meses = cursor.fetchall()
    conn.close()

    # Retornar apenas os números dos meses (sem None)
    return [mes[0] for mes in meses if mes[0] is not None]


def buscar_anos_unicos(usuario=None):
    """Busca os anos únicos que possuem registros no banco de dados."""
    conn = conectar_db()
    cursor = conn.cursor()

    conditions = []
    params = []

    if usuario:
        conditions.append("usuario = ?")
        params.append(usuario)

    query = "SELECT DISTINCT strftime('%Y', data_processo) as ano FROM registro"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    # Anos em ordem decrescente (mais recente primeiro)
    query += " ORDER BY ano DESC"

    cursor.execute(query, params)
    anos = cursor.fetchall()
    conn.close()

    # Retornar apenas os anos (sem None)
    return [ano[0] for ano in anos if ano[0] is not None]


def buscar_periodos_faturamento_por_ano(ano, usuario=None):
    """Busca os períodos de faturamento de um ano específico (26/MM a 25/MM+1)."""
    from datetime import datetime
    
    conn = conectar_db()
    cursor = conn.cursor()
    
    conditions = ["data_processo IS NOT NULL"]
    params = []
    
    if usuario:
        conditions.append("usuario = ?")
        params.append(usuario)
    
    # Buscar datas do ano especificado e do ano seguinte (para períodos que cruzam anos)
    ano_int = int(ano)
    conditions.append("(strftime('%Y', data_processo) = ? OR strftime('%Y', data_processo) = ?)")
    params.extend([str(ano_int), str(ano_int + 1)])
    
    query = f"SELECT DISTINCT data_processo FROM registro WHERE {' AND '.join(conditions)} ORDER BY data_processo"
    
    cursor.execute(query, params)
    datas = cursor.fetchall()
    conn.close()
    
    # Converter as datas para objetos datetime e determinar períodos do ano especificado
    periodos = set()
    
    for data_tupla in datas:
        data_str = data_tupla[0]
        try:
            data_obj = datetime.strptime(data_str, '%Y-%m-%d')
            
            # Determinar o período de faturamento desta data
            if data_obj.day >= 26:
                # Período atual: 26/MM a 25/(MM+1)
                inicio_mes = data_obj.month
                inicio_ano = data_obj.year
                
                # Calcular mês seguinte
                if inicio_mes == 12:
                    fim_mes = 1
                    fim_ano = inicio_ano + 1
                else:
                    fim_mes = inicio_mes + 1
                    fim_ano = inicio_ano
            else:
                # Período anterior: 26/(MM-1) a 25/MM
                fim_mes = data_obj.month
                fim_ano = data_obj.year
                
                # Calcular mês anterior
                if fim_mes == 1:
                    inicio_mes = 12
                    inicio_ano = fim_ano - 1
                else:
                    inicio_mes = fim_mes - 1
                    inicio_ano = fim_ano
            
            # Só incluir períodos que começam no ano especificado
            if inicio_ano == ano_int:
                periodo_inicio = f"{inicio_ano}-{inicio_mes:02d}-26"
                periodo_fim = f"{fim_ano}-{fim_mes:02d}-25"
                periodos.add((periodo_inicio, periodo_fim))
            
        except ValueError:
            continue  # Pular datas inválidas
    
    # Converter para lista e ordenar por data de início (mais recente primeiro)
    periodos_lista = sorted(list(periodos), key=lambda x: x[0], reverse=True)
    
    # Retornar períodos formatados para exibição
    periodos_formatados = []
    for inicio, fim in periodos_lista:
        try:
            data_inicio = datetime.strptime(inicio, '%Y-%m-%d')
            data_fim = datetime.strptime(fim, '%Y-%m-%d')
            
            # Formato abreviado: 26/12 a 25/01
            formato_inicio = data_inicio.strftime('%d/%m')
            formato_fim = data_fim.strftime('%d/%m')
            
            periodos_formatados.append({
                'display': f"{formato_inicio} a {formato_fim}",
                'inicio': inicio,
                'fim': fim
            })
        except ValueError:
            continue
    
    return periodos_formatados


def buscar_periodos_faturamento_unicos(usuario=None):
    """Busca os períodos de faturamento únicos (26 de um mês até 25 do mês seguinte)."""
    from datetime import datetime, timedelta
    from calendar import monthrange
    
    conn = conectar_db()
    cursor = conn.cursor()
    
    conditions = []
    params = []
    
    if usuario:
        conditions.append("usuario = ?")
        params.append(usuario)
    
    query = "SELECT DISTINCT data_processo FROM registro WHERE data_processo IS NOT NULL"
    if conditions:
        query += " AND " + " AND ".join(conditions)
    query += " ORDER BY data_processo"
    
    cursor.execute(query, params)
    datas = cursor.fetchall()
    conn.close()
    
    # Converter as datas para objetos datetime e determinar períodos
    periodos = set()
    
    for data_tupla in datas:
        data_str = data_tupla[0]
        try:
            # Assumindo formato YYYY-MM-DD
            data_obj = datetime.strptime(data_str, '%Y-%m-%d')
            
            # Determinar o período de faturamento desta data
            if data_obj.day >= 26:
                # Período atual: 26/MM a 25/(MM+1)
                inicio_mes = data_obj.month
                inicio_ano = data_obj.year
                
                # Calcular mês seguinte
                if inicio_mes == 12:
                    fim_mes = 1
                    fim_ano = inicio_ano + 1
                else:
                    fim_mes = inicio_mes + 1
                    fim_ano = inicio_ano
                    
                periodo_inicio = f"{inicio_ano}-{inicio_mes:02d}-26"
                periodo_fim = f"{fim_ano}-{fim_mes:02d}-25"
            else:
                # Período anterior: 26/(MM-1) a 25/MM
                fim_mes = data_obj.month
                fim_ano = data_obj.year
                
                # Calcular mês anterior
                if fim_mes == 1:
                    inicio_mes = 12
                    inicio_ano = fim_ano - 1
                else:
                    inicio_mes = fim_mes - 1
                    inicio_ano = fim_ano
                    
                periodo_inicio = f"{inicio_ano}-{inicio_mes:02d}-26"
                periodo_fim = f"{fim_ano}-{fim_mes:02d}-25"
            
            periodos.add((periodo_inicio, periodo_fim))
            
        except ValueError:
            continue  # Pular datas inválidas
    
    # Converter para lista e ordenar por data de início (mais recente primeiro)
    periodos_lista = sorted(list(periodos), key=lambda x: x[0], reverse=True)
    
    # Retornar períodos formatados para exibição
    periodos_formatados = []
    for inicio, fim in periodos_lista:
        try:
            data_inicio = datetime.strptime(inicio, '%Y-%m-%d')
            data_fim = datetime.strptime(fim, '%Y-%m-%d')
            
            formato_inicio = data_inicio.strftime('%d/%m/%Y')
            formato_fim = data_fim.strftime('%d/%m/%Y')
            
            periodos_formatados.append({
                'display': f"{formato_inicio} a {formato_fim}",
                'inicio': inicio,
                'fim': fim
            })
        except ValueError:
            continue
    
    return periodos_formatados


# Garante que a tabela seja criada na primeira vez que o módulo foi importado
criar_tabela_registro()
