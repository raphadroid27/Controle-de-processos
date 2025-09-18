"""
Módulo para gerenciamento do banco de dados SQLite.

Este módulo fornece funcionalidades para conexão com o banco,
operações CRUD de processos, estatísticas e manutenção das
tabelas de dados do sistema.
"""

import os

# database.py
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Lancamento:
    """Representa um lançamento de processo no sistema."""

    usuario: Optional[str]
    cliente: str
    processo: str
    qtde_itens: str
    data_entrada: str
    data_processo: Optional[str]
    valor_pedido: str


def _preparar_lancamento_para_insert(lanc: Lancamento):
    """Valida e normaliza dados para INSERT.

    Retorna tupla pronta ou mensagem de erro.
    """
    if not all(
        [
            (lanc.usuario or "").strip(),
            lanc.cliente.strip(),
            lanc.processo.strip(),
            lanc.qtde_itens.strip(),
            lanc.data_entrada.strip(),
            lanc.valor_pedido.strip(),
        ]
    ):
        return (
            "Erro: Campos obrigatórios: usuário, cliente, processo, "
            "qtd itens, data entrada, valor."
        )

    try:
        qtde = int(lanc.qtde_itens)
        if qtde <= 0:
            return "Erro: A quantidade de itens deve ser um número positivo."
    except ValueError:
        return "Erro: A quantidade de itens deve ser um número válido."

    try:
        valor = float(lanc.valor_pedido.replace(",", "."))
        if valor <= 0:
            return "Erro: O valor do pedido deve ser maior que zero."
    except ValueError:
        return "Erro: O valor do pedido deve ser um número válido."

    data_proc = (
        (lanc.data_processo or "").strip()
        if lanc.data_processo and str(lanc.data_processo).strip()
        else None
    )

    return (
        (lanc.usuario or "").strip(),
        lanc.cliente.strip(),
        lanc.processo.strip(),
        qtde,
        lanc.data_entrada.strip(),
        data_proc,
        valor,
    )


def _preparar_lancamento_para_update(lanc: Lancamento):
    """Valida e normaliza dados para UPDATE; retorna tupla pronta ou mensagem de erro."""
    if not lanc.cliente or not lanc.processo:
        return "Erro: Cliente e processo são obrigatórios."

    try:
        qtde_int = int(lanc.qtde_itens)
        if qtde_int <= 0:
            return "Erro: Quantidade de itens deve ser um número positivo."
    except ValueError:
        return "Erro: Quantidade de itens deve ser um número válido."

    try:
        valor_float = float(lanc.valor_pedido.replace(",", "."))
        if valor_float < 0:
            return "Erro: Valor do pedido não pode ser negativo."
    except ValueError:
        return "Erro: Valor do pedido deve ser um número válido."

    data_proc = (
        None
        if (not lanc.data_processo or lanc.data_processo == "Não processado")
        else lanc.data_processo
    )

    return (
        lanc.cliente,
        lanc.processo,
        qtde_int,
        lanc.data_entrada,
        data_proc,
        valor_float,
    )


def conectar_db():
    """Conecta ao banco de dados SQLite e o retorna."""
    # Caminho para o banco de dados no diretório raiz do projeto
    # database.py está em src/utils/, então precisamos subir 2 níveis
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(
            os.path.dirname(__file__))), "processos.db"
    )
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
    lancamento: Lancamento | None = None,
    *,
    usuario: str | None = None,
    cliente: str | None = None,
    processo: str | None = None,
    qtde_itens: str | None = None,
    data_entrada: str | None = None,
    data_processo: str | None = None,
    valor_pedido: str | None = None,
):
    """Adiciona um novo registro de processo ao banco de dados.

    Aceita um objeto `Lancamento` ou campos nomeados (compatibilidade).
    """
    if lancamento is None:
        if None in (usuario, cliente, processo, qtde_itens, data_entrada, valor_pedido):
            return (
                "Erro: Campos obrigatórios: usuário, cliente, processo, "
                "qtd itens, data entrada, valor."
            )
        lanc = Lancamento(
            usuario=usuario,
            cliente=cliente or "",
            processo=processo or "",
            qtde_itens=qtde_itens or "",
            data_entrada=data_entrada or "",
            data_processo=data_processo or "",
            valor_pedido=valor_pedido or "",
        )
    else:
        lanc = lancamento
    try:
        prep = _preparar_lancamento_para_insert(lanc)
        if isinstance(prep, str):
            return prep

        with conectar_db() as conn:
            conn.execute(
                """
    INSERT INTO registro (usuario, cliente, processo, qtde_itens,
                data_entrada, data_processo, valor_pedido)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
                prep,
            )
        return "Sucesso: Processo adicionado!"
    except sqlite3.Error as e:
        return f"Erro ao inserir no banco de dados: {e}"
    finally:
        pass


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


def atualizar_lancamento(
    id_registro,
    lancamento: Lancamento | None = None,
    *,
    cliente: str | None = None,
    processo: str | None = None,
    qtde_itens: str | None = None,
    data_entrada: str | None = None,
    data_processo: str | None = None,
    valor_pedido: str | None = None,
):
    """Atualiza um lançamento existente no banco de dados.

    Aceita um objeto `Lancamento` ou campos nomeados (compatibilidade).
    Campo `usuario` é ignorado na atualização.
    """
    if lancamento is None:
        lanc = Lancamento(
            usuario=None,
            cliente=cliente or "",
            processo=processo or "",
            qtde_itens=qtde_itens or "",
            data_entrada=data_entrada or "",
            data_processo=data_processo or "",
            valor_pedido=valor_pedido or "",
        )
    else:
        lanc = lancamento
    prep = _preparar_lancamento_para_update(lanc)
    if isinstance(prep, str):
        return prep

    try:
        with conectar_db() as conn:
            cursor = conn.execute(
                """
                UPDATE registro
                SET cliente = ?, processo = ?, qtde_itens = ?,
                    data_entrada = ?, data_processo = ?, valor_pedido = ?
                WHERE id = ?
                """,
                (*prep, id_registro),
            )
            if cursor.rowcount == 0:
                return "Erro: Registro não encontrado."
        return "Sucesso: Processo atualizado com sucesso!"

    except sqlite3.Error as e:
        return f"Erro no banco de dados: {e}"


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
            (usuario,),
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
            (
                "SELECT DISTINCT processo FROM registro "
                "WHERE usuario = ? ORDER BY processo"
            ),
            (usuario,),
        )
    else:
        cursor.execute(
            "SELECT DISTINCT processo FROM registro ORDER BY processo")

    processos = [row[0] for row in cursor.fetchall()]
    conn.close()
    return processos


def _montar_filtros(
    usuario=None, cliente=None, processo=None, data_inicio=None, data_fim=None
):
    """Monta condições e parâmetros para filtros comuns.

    Retorna tupla (conditions, params) adequada para composição de queries.
    """
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
        params.extend([data_inicio, data_fim])

    return conditions, params


def buscar_lancamentos_filtros_completos(
    usuario=None, cliente=None, processo=None, data_inicio=None, data_fim=None
):
    """Busca lançamentos aplicando múltiplos filtros com busca parcial."""
    conn = conectar_db()
    cursor = conn.cursor()

    conditions, params = _montar_filtros(
        usuario=usuario,
        cliente=cliente,
        processo=processo,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )

    partes = [
        "SELECT * FROM registro",
        "WHERE " + " AND ".join(conditions) if conditions else "",
        "ORDER BY data_lancamento",
    ]
    query = " ".join([p for p in partes if p])

    cursor.execute(query, params)
    registros = cursor.fetchall()
    conn.close()
    return registros


def buscar_estatisticas_completas(
    usuario=None, cliente=None, processo=None, data_inicio=None, data_fim=None
):
    """Calcula estatísticas aplicando múltiplos filtros com busca parcial."""
    conn = conectar_db()
    cursor = conn.cursor()

    conditions, params = _montar_filtros(
        usuario=usuario,
        cliente=cliente,
        processo=processo,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )

    partes = [
        (
            "SELECT COUNT(*) as total_processos, "
            "SUM(qtde_itens) as total_itens, "
            "SUM(valor_pedido) as total_valor FROM registro"
        ),
        "WHERE " + " AND ".join(conditions) if conditions else "",
    ]
    query = " ".join([p for p in partes if p])

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


def _periodo_faturamento_datas(data_str):
    """Calcula datas (inicio, fim) do período de faturamento.

    Considera uma data no formato YYYY-MM-DD e retorna uma tupla
    (inicio_iso, fim_iso) ou None se a data for inválida.
    """
    try:
        data_obj = datetime.strptime(data_str, "%Y-%m-%d")

        if data_obj.day >= 26:
            inicio_mes = data_obj.month
            inicio_ano = data_obj.year
            if inicio_mes == 12:
                fim_mes = 1
                fim_ano = inicio_ano + 1
            else:
                fim_mes = inicio_mes + 1
                fim_ano = inicio_ano
        else:
            fim_mes = data_obj.month
            fim_ano = data_obj.year
            if fim_mes == 1:
                inicio_mes = 12
                inicio_ano = fim_ano - 1
            else:
                inicio_mes = fim_mes - 1
                inicio_ano = fim_ano

        inicio = f"{inicio_ano}-{inicio_mes:02d}-26"
        fim = f"{fim_ano}-{fim_mes:02d}-25"
        return inicio, fim
    except ValueError:
        return None


def _formatar_periodo_exibicao(inicio, fim, com_ano=False):
    """Formata período para exibição."""
    try:
        data_inicio = datetime.strptime(inicio, "%Y-%m-%d")
        data_fim = datetime.strptime(fim, "%Y-%m-%d")
        if com_ano:
            formato_inicio = data_inicio.strftime("%d/%m/%Y")
            formato_fim = data_fim.strftime("%d/%m/%Y")
        else:
            formato_inicio = data_inicio.strftime("%d/%m")
            formato_fim = data_fim.strftime("%d/%m")
        return f"{formato_inicio} a {formato_fim}"
    except ValueError:
        return None


def buscar_periodos_faturamento_por_ano(ano, usuario=None):
    """Busca os períodos de faturamento de um ano específico (26/MM a 25/MM+1)."""
    ano_int = int(ano)
    datas = _listar_datas_processo_filtradas(
        usuario=usuario,
        ano=ano_int,
        incluir_ano_seguinte=True,
    )

    periodos_lista = sorted(
        [
            p
            for p in (_periodo_faturamento_datas(data) for data in datas)
            if p and int(p[0][:4]) == ano_int
        ],
        key=lambda x: x[0],
        reverse=True,
    )

    return [
        {"display": d, "inicio": i, "fim": f}
        for (i, f) in periodos_lista
        if (d := _formatar_periodo_exibicao(i, f, com_ano=False))
    ]


def buscar_periodos_faturamento_unicos(usuario=None):
    """Busca os períodos de faturamento únicos (26 de um mês até 25 do mês seguinte)."""
    datas = _listar_datas_processo_filtradas(usuario=usuario)

    periodos_lista = sorted(
        [p for p in (_periodo_faturamento_datas(data) for data in datas) if p],
        key=lambda x: x[0],
        reverse=True,
    )

    return [
        {"display": d, "inicio": i, "fim": f}
        for (i, f) in periodos_lista
        if (d := _formatar_periodo_exibicao(i, f, com_ano=True))
    ]


def _listar_datas_processo_filtradas(
    usuario=None, ano: int | None = None, incluir_ano_seguinte: bool = False
):
    """Retorna lista de datas distintas de processamento aplicando filtros opcionais."""
    conditions = ["data_processo IS NOT NULL"]
    params: list[str] = []

    if usuario:
        conditions.append("usuario = ?")
        params.append(usuario)

    if ano is not None:
        conditions.append(
            "(strftime('%Y', data_processo) = ? OR strftime('%Y', data_processo) = ?)"
            if incluir_ano_seguinte
            else "strftime('%Y', data_processo) = ?"
        )
        params.append(str(ano))
        if incluir_ano_seguinte:
            params.append(str(ano + 1))

    query = " ".join(
        [
            "SELECT DISTINCT data_processo FROM registro",
            "WHERE " + " AND ".join(conditions) if conditions else "",
            "ORDER BY data_processo",
        ]
    )

    with conectar_db() as conn:
        cur = conn.execute(query, params)
        rows = cur.fetchall()

    return [row[0] for row in rows]


def inicializar_todas_tabelas():
    """[DEPRECATED] Use inicialização em app.py para evitar ciclos de import."""
    criar_tabela_registro()


# Garante que a tabela seja criada na primeira vez que o módulo foi importado
criar_tabela_registro()
