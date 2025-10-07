"""
Widget principal para gerenciamento de processos.

Contém a interface principal do sistema com formulário de entrada,
tabela de dados e controles de filtros.
"""

from PySide6.QtCore import QDate, Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QMessageBox, QVBoxLayout, QWidget

from ..utils import database as db
from ..utils.formatters import formatar_valor_monetario
from ..utils.periodo_faturamento import \
    calcular_periodo_faturamento_atual_datas
from ..utils.ui_config import ESPACAMENTO_PADRAO
from .components import processos_autocomplete
from .components import processos_data_service as processos_data
from .components import (processos_filters, processos_form, processos_periodo,
                         processos_table, processos_table_edit,
                         processos_totais)


class ProcessosWidget(QWidget):
    """Widget principal para gerenciamento de processos."""

    def __init__(self, usuario_logado, is_admin):
        super().__init__()
        self.is_admin = is_admin
        self.usuario_logado = usuario_logado

        self.frame_entrada = None
        self.botoes_layout = None
        self.frame_totais = None
        self.btn_adicionar = None
        self.btn_excluir = None
        self.entry_cliente = None
        self.entry_processo = None
        self.entry_qtde_itens = None
        self.entry_data_entrada = None
        self.entry_data_processo = None
        self.entry_tempo_corte = None
        self.entry_valor_pedido = None
        self.tabela_layout = None
        self.tabela = None
        self.entry_filtro_cliente = None
        self.entry_filtro_processo = None
        self.timer_cliente = None
        self.timer_processo = None
        self.btn_limpar_filtros = None
        self.label_total_processos = None
        self.label_total_itens = None
        self.label_total_valor = None
        self.shortcut_enter = None
        self.shortcut_enter_num = None
        self.shortcut_delete = None
        self.combo_usuario = None
        self.combo_filtro_ano = None
        self.combo_filtro_periodo = None
        self.aplicar_larguras_colunas = None
        self.controles_totais = None
        self.autocomplete_manager = processos_autocomplete.AutocompleteManager(
            parent=self,
            carregar_clientes=processos_data.carregar_clientes_upper,
        )
        self.periodo_controller = None

        self.init_ui()
        self.carregar_dados()

    def init_ui(self):
        """Inicializa a interface do usuário."""
        main_layout = QVBoxLayout()

        self.criar_frame_entrada()
        main_layout.addWidget(self.frame_entrada)

        self.criar_tabela()
        main_layout.addLayout(self.tabela_layout)

        self.criar_frame_totais()
        main_layout.addWidget(self.frame_totais)

        self.setLayout(main_layout)

        self.configurar_atalhos()

    def configurar_atalhos(self):
        """Configura os atalhos de teclado para a aplicação."""
        self.shortcut_enter = QShortcut(QKeySequence(Qt.Key.Key_Return), self)
        self.shortcut_enter.activated.connect(self.atalho_adicionar_processo)

        self.shortcut_enter_num = QShortcut(QKeySequence(Qt.Key.Key_Enter), self)
        self.shortcut_enter_num.activated.connect(self.atalho_adicionar_processo)

        self.shortcut_delete = QShortcut(QKeySequence(Qt.Key.Key_Delete), self)
        self.shortcut_delete.activated.connect(self.excluir_processo)

    def configurar_filtros_ano_periodo(self):
        """Configura combos de ano e período de faturamento com dados únicos."""
        if not self.periodo_controller:
            return

        try:
            data_inicio_atual, _ = calcular_periodo_faturamento_atual_datas()
            fallback_ano = str(data_inicio_atual.year)
        except (RuntimeError, AttributeError, TypeError, ValueError):
            fallback_ano = None

        self.periodo_controller.configurar(fallback_ano=fallback_ano)

    def on_ano_changed(self):
        """Reage à mudança de ano no filtro."""
        if self.periodo_controller:
            self.periodo_controller.on_ano_changed()
        self.aplicar_filtro()

    def converter_cliente_maiuscula(self, texto):
        """Converte automaticamente o texto do campo cliente para maiúscula."""
        self.entry_cliente.blockSignals(True)
        posicao_cursor = self.entry_cliente.cursorPosition()
        texto_maiusculo = texto.upper()
        self.entry_cliente.setText(texto_maiusculo)
        self.entry_cliente.setCursorPosition(posicao_cursor)
        self.entry_cliente.blockSignals(False)

    def _on_tempo_corte_editado(self, texto):
        """Insere automaticamente os separadores de tempo (HH:MM:SS)."""
        if self.entry_tempo_corte is None:
            return

        digitos = "".join(ch for ch in texto if ch.isdigit())[:6]

        if not digitos:
            self.entry_tempo_corte.blockSignals(True)
            self.entry_tempo_corte.setText("")
            self.entry_tempo_corte.blockSignals(False)
            return

        horas = digitos[:2]
        minutos = digitos[2:4]
        segundos = digitos[4:6]

        partes = [horas]
        if len(digitos) > 2:
            partes.append(minutos)
        if len(digitos) > 4:
            partes.append(segundos)

        formato = ":".join(partes)

        self.entry_tempo_corte.blockSignals(True)
        self.entry_tempo_corte.setText(formato)
        self.entry_tempo_corte.blockSignals(False)
        self.entry_tempo_corte.setCursorPosition(len(formato))

    def atalho_adicionar_processo(self):
        """Adiciona processo via atalho se campos obrigatórios estiverem ok."""
        cliente = self.entry_cliente.text().strip()
        processo = self.entry_processo.text().strip()
        qtde_itens = self.entry_qtde_itens.text().strip()
        valor_pedido = self.entry_valor_pedido.text().strip()

        if cliente and processo and qtde_itens and valor_pedido:
            self.adicionar_processo()
        else:
            if not cliente:
                self.entry_cliente.setFocus()
            elif not processo:
                self.entry_processo.setFocus()
            elif not qtde_itens:
                self.entry_qtde_itens.setFocus()
            elif not valor_pedido:
                self.entry_valor_pedido.setFocus()

    def criar_frame_entrada(self):
        """Cria o frame de entrada de dados."""
        controles = processos_form.criar_formulario(
            parent=self,
            on_tempo_editado=self._on_tempo_corte_editado,
            on_cliente_editado=self.converter_cliente_maiuscula,
            on_submit=self.adicionar_processo,
        )

        self.frame_entrada = controles.frame
        self.entry_cliente = controles.cliente
        self.entry_processo = controles.processo
        self.entry_qtde_itens = controles.qtde_itens
        self.entry_data_entrada = controles.data_entrada
        self.entry_data_processo = controles.data_processo
        self.entry_tempo_corte = controles.tempo_corte
        self.entry_valor_pedido = controles.valor_pedido
        self.btn_adicionar = controles.btn_adicionar

        self.autocomplete_manager.configure_form(self.entry_cliente)

    def criar_tabela(self):
        """Cria a interface da tabela de processos com filtros."""
        self.tabela_layout = QVBoxLayout()
        filtros = processos_filters.criar_filtros(
            parent=self,
            is_admin=self.is_admin,
            on_cliente_timeout=self.aplicar_filtro,
            on_processo_timeout=self.aplicar_filtro,
            on_ano_changed=self.on_ano_changed,
            on_periodo_changed=self.aplicar_filtro,
            on_usuario_changed=self.on_usuario_changed,
            on_limpar=self.limpar_filtros,
        )
        self.tabela_layout.addWidget(filtros.frame)

        self.combo_usuario = filtros.combo_usuario if self.is_admin else None
        self.entry_filtro_cliente = filtros.entry_cliente
        self.entry_filtro_processo = filtros.entry_processo
        self.combo_filtro_ano = filtros.combo_ano
        self.combo_filtro_periodo = filtros.combo_periodo
        self.btn_limpar_filtros = filtros.btn_limpar
        self.timer_cliente = filtros.timer_cliente
        self.timer_processo = filtros.timer_processo

        self.periodo_controller = processos_periodo.PeriodoFiltroController(
            combo_ano=self.combo_filtro_ano,
            combo_periodo=self.combo_filtro_periodo,
            listar_anos=processos_data.listar_anos_disponiveis,
            listar_periodos=processos_data.listar_periodos_do_ano,
            obter_usuario=self._calcular_usuario_filtro,
        )

        self.autocomplete_manager.configure_filter(self.entry_filtro_cliente)

        tabela_controls = processos_table.criar_tabela(
            parent=self,
            is_admin=self.is_admin,
            on_item_changed=self.on_item_changed,
            on_excluir=self.excluir_processo,
        )

        self.tabela = tabela_controls.tabela
        self.btn_excluir = tabela_controls.btn_excluir
        self.aplicar_larguras_colunas = tabela_controls.aplicar_larguras

        self.tabela_layout.addWidget(tabela_controls.frame)

    def criar_frame_totais(self):
        """Cria o frame que exibe os totais (processos, itens, valores)."""
        controles_totais = processos_totais.criar_totais(
            parent=self,
            espacamento=ESPACAMENTO_PADRAO,
        )

        self.controles_totais = controles_totais
        self.frame_totais = controles_totais.frame
        self.label_total_processos = controles_totais.label_processos
        self.label_total_itens = controles_totais.label_itens
        self.label_total_valor = controles_totais.label_valor

    def limpar_filtros(self):
        """Limpa filtros mantendo o período corrente selecionado."""
        if self.is_admin and hasattr(self, "combo_usuario"):
            self.combo_usuario.blockSignals(True)
            self.combo_usuario.setCurrentText("Todos os usuários")
            self.combo_usuario.blockSignals(False)

        if hasattr(self, "entry_filtro_cliente"):
            self.entry_filtro_cliente.blockSignals(True)
            self.entry_filtro_cliente.clear()
            self.entry_filtro_cliente.blockSignals(False)

        if hasattr(self, "entry_filtro_processo"):
            self.entry_filtro_processo.blockSignals(True)
            self.entry_filtro_processo.clear()
            self.entry_filtro_processo.blockSignals(False)

        self.aplicar_filtro_periodo_corrente()
        self.aplicar_filtro()

    def aplicar_filtro_periodo_corrente(self):
        """Seleciona automaticamente o período corrente."""
        if not self.periodo_controller:
            return

        try:
            data_inicio_atual, data_fim_atual = (
                calcular_periodo_faturamento_atual_datas()
            )
        except (RuntimeError, AttributeError, TypeError, ValueError) as e:
            print(f"Erro ao aplicar filtro do período corrente: {e}")
            return

        ano_atual = str(data_inicio_atual.year)
        periodo_display = (
            f"{data_inicio_atual.strftime('%d/%m')} a "
            f"{data_fim_atual.strftime('%d/%m')}"
        )

        self.periodo_controller.selecionar_ano(ano_atual)
        self.periodo_controller.on_ano_changed()
        self.periodo_controller.selecionar_periodo_por_datas(periodo_display)

    def on_usuario_changed(self):
        """Reage à mudança de usuário no filtro (admins)."""
        self.configurar_filtros_ano_periodo()
        self.aplicar_filtro_periodo_corrente()
        self.aplicar_filtro()

    def carregar_dados(self):
        """Carrega usuários, configura filtros e aplica período corrente."""
        if self.is_admin and hasattr(self, "combo_usuario"):
            usuarios_list = db.buscar_usuarios_unicos()
            for user in usuarios_list:
                self.combo_usuario.addItem(user)

        self.configurar_filtros_ano_periodo()
        self.aplicar_filtro_periodo_corrente()
        self.aplicar_filtro()
        QTimer.singleShot(100, self.rolar_para_ultimo_item)

    def on_item_changed(self, item):
        """Aplica validações e persiste alterações ao editar a tabela."""
        if not item:
            return

        try:
            self.tabela.blockSignals(True)
            row = item.row()
            col = item.column()
            col_offset = 1 if self.is_admin else 0

            if self.is_admin and col == 0:
                self.aplicar_filtro(rolar_para_ultimo=False)
                return

            registro_id = processos_table_edit.obter_registro_id(
                self.tabela, row, self.is_admin
            )
            if not registro_id:
                return

            col_editada = col - col_offset
            valor_editado = item.text().strip()

            ok, erro_msg = processos_table_edit.validar_edicao_celula(
                col_editada, valor_editado
            )
            if not ok:
                if erro_msg:
                    QMessageBox.warning(self, "Erro", erro_msg)
                self.aplicar_filtro(rolar_para_ultimo=False)
                return

            dados_linha = processos_table_edit.extrair_campos_linha(
                self.tabela,
                row,
                col_offset,
            )

            resultado = db.atualizar_lancamento(
                registro_id,
                **dados_linha.to_update_kwargs(),
            )

            if "Sucesso" in resultado and col_editada == 3:
                self.configurar_filtros_ano_periodo()

            if "Sucesso" not in resultado:
                QMessageBox.warning(self, "Erro", resultado)

            self.aplicar_filtro(rolar_para_ultimo=False)

        except (ValueError, AttributeError, TypeError) as e:
            self.aplicar_filtro(rolar_para_ultimo=False)
            QMessageBox.warning(self, "Erro", f"Erro ao atualizar registro: {str(e)}")
        finally:
            self.tabela.blockSignals(False)

    def _calcular_usuario_filtro(self):
        """Determina o filtro de usuário considerando admin/usuário."""
        if self.is_admin:
            if (
                hasattr(self, "combo_usuario")
                and self.combo_usuario.currentText() != "Todos os usuários"
            ):
                return self.combo_usuario.currentText()
            return None
        return self.usuario_logado

    def _obter_filtros_texto(self):
        """Obtém filtros de cliente e processo a partir dos campos de texto."""
        cliente_filtro = None
        if (
            hasattr(self, "entry_filtro_cliente")
            and self.entry_filtro_cliente.text().strip()
        ):
            cliente_filtro = self.entry_filtro_cliente.text().strip().upper()

        processo_filtro = None
        if (
            hasattr(self, "entry_filtro_processo")
            and self.entry_filtro_processo.text().strip()
        ):
            processo_filtro = self.entry_filtro_processo.text().strip()

        return cliente_filtro, processo_filtro

    def _obter_periodo_selecionado(self):
        """Retorna (data_inicio, data_fim) do período selecionado, se houver."""
        if not self.periodo_controller:
            return None, None
        return self.periodo_controller.obter_periodo_selecionado()

    def aplicar_filtro(self, rolar_para_ultimo=True):
        """Aplica filtros e preenche a tabela."""
        usuario_filtro = self._calcular_usuario_filtro()
        cliente_filtro, processo_filtro = self._obter_filtros_texto()
        data_inicio, data_fim = self._obter_periodo_selecionado()

        registros_ordenados = processos_data.buscar_registros_filtrados(
            usuario=usuario_filtro,
            cliente=cliente_filtro,
            processo=processo_filtro,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        processos_table.preencher_tabela(
            tabela=self.tabela,
            registros=registros_ordenados,
            is_admin=self.is_admin,
        )

        filtros = {
            "usuario": usuario_filtro,
            "cliente": cliente_filtro,
            "processo": processo_filtro,
            "data_inicio": data_inicio,
            "data_fim": data_fim,
        }

        self.atualizar_totais(filtros)

        if rolar_para_ultimo:
            self.rolar_para_ultimo_item()

    def rolar_para_ultimo_item(self):
        """Rola a tabela até o último item."""
        if self.tabela.rowCount() > 0:
            ultima_linha = self.tabela.rowCount() - 1
            self.tabela.scrollToBottom()
            self.tabela.selectRow(ultima_linha)

    def atualizar_totais(self, filtros: dict | None = None):
        """Atualiza os totalizadores do painel."""
        if not self.controles_totais:
            return

        filtros = filtros or {}
        estatisticas = processos_data.obter_estatisticas_totais(filtros)

        processos_totais.atualizar_totais(
            self.controles_totais,
            total_processos=estatisticas["total_processos"],
            total_itens=estatisticas["total_itens"],
            total_valor=estatisticas["total_valor"],
            formatar_valor=formatar_valor_monetario,
        )

    def adicionar_processo(self):
        """Valida campos e insere novo processo no banco."""
        cliente = self.entry_cliente.text().strip().upper()
        processo = self.entry_processo.text().strip()
        qtde_itens = self.entry_qtde_itens.text().strip()

        data_entrada_qdate = self.entry_data_entrada.date()
        if data_entrada_qdate > QDate.currentDate():
            QMessageBox.warning(
                self, "Erro", "Data de entrada não pode ser maior que a data atual."
            )
            return
        data_entrada = data_entrada_qdate.toString("yyyy-MM-dd")

        data_processo_qdate = self.entry_data_processo.date()
        if not data_processo_qdate.isNull():
            if data_processo_qdate > QDate.currentDate():
                QMessageBox.warning(
                    self,
                    "Erro",
                    "Data de processo não pode ser maior que a data atual.",
                )
                return
            data_processo = data_processo_qdate.toString("yyyy-MM-dd")
        else:
            data_processo = ""

        valor_pedido = self.entry_valor_pedido.text().strip()
        tempo_corte = self.entry_tempo_corte.text().strip()

        resultado = db.adicionar_lancamento(
            usuario=self.usuario_logado,
            cliente=cliente,
            processo=processo,
            qtde_itens=qtde_itens,
            data_entrada=data_entrada,
            data_processo=data_processo,
            valor_pedido=valor_pedido,
            tempo_corte=tempo_corte,
        )

        if "Sucesso" in resultado:
            QMessageBox.information(self, "Sucesso", resultado)
            self.entry_cliente.clear()
            self.entry_processo.clear()
            self.entry_qtde_itens.clear()
            self.entry_data_entrada.setDate(QDate.currentDate())
            self.entry_data_processo.clear()
            self.entry_tempo_corte.clear()
            self.entry_valor_pedido.clear()

            self.autocomplete_manager.refresh_all()
            self.configurar_filtros_ano_periodo()
            self.aplicar_filtro()
            self.rolar_para_ultimo_item()
            self.entry_cliente.setFocus()
        else:
            QMessageBox.warning(self, "Erro", resultado)

    def excluir_processo(self):
        """Exclui o processo selecionado na tabela."""
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.information(
                self,
                "Seleção",
                (
                    "Selecione um processo na tabela para excluir.\n\n"
                    "Dica: Clique em uma linha e pressione Delete ou "
                    "use o botão 'Excluir Selecionado'."
                ),
            )
            return

        if not self.is_admin:
            cliente = self.tabela.item(row, 0).text()
            processo = self.tabela.item(row, 1).text()
        else:
            cliente = self.tabela.item(row, 1).text()
            processo = self.tabela.item(row, 2).text()

        resposta = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            (
                "Tem certeza que deseja excluir este processo?\n\n"
                f"Cliente: {cliente}\nProcesso: {processo}"
            ),
            QMessageBox.Yes | QMessageBox.No,
        )

        if resposta == QMessageBox.Yes:
            if not self.is_admin:
                item_com_id = self.tabela.item(row, 0)
            else:
                item_com_id = self.tabela.item(row, 1)

            if item_com_id:
                registro_id = item_com_id.data(Qt.UserRole)
                resultado = db.excluir_lancamento(registro_id)
                if "Sucesso" in resultado:
                    QMessageBox.information(self, "Sucesso", resultado)
                    self.configurar_filtros_ano_periodo()
                    self.aplicar_filtro(rolar_para_ultimo=False)
                else:
                    QMessageBox.warning(self, "Erro", resultado)
