"""
Widget principal para gerenciamento de pedidos.

Contém a interface principal do sistema com formulário de entrada,
tabela de dados e controles de filtros.
"""

import logging
from datetime import date, datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QMessageBox, QVBoxLayout, QWidget

from src.utils import database as db
from src.utils.formatters import (
    formatar_data_para_exibicao,
    formatar_valor_monetario,
    normalizar_nome_cliente,
    normalizar_valor_padrao_brasileiro,
)
from src.utils.periodo_faturamento import (
    calcular_periodo_faturamento_atual_datas,
    calcular_periodo_faturamento_para_data_datas,
)
from src.utils.ui_config import ESPACAMENTO_PADRAO, obter_data_atual_utc
from src.widgets.components import filters, autocomplete, table_edit, totais
from src.widgets.components import data_service as data
from src.widgets.components import (form,
                                    periodo, table)


logger = logging.getLogger(__name__)


class PedidosWidget(QWidget):
    """Widget principal para gerenciamento de pedidos."""

    def __init__(self, usuario_logado, is_admin):
        """Inicializa o widget principal com configurações do usuário."""
        super().__init__()
        self.is_admin = is_admin
        self.usuario_logado = usuario_logado

        self.frame_entrada = None
        self.botoes_layout = None
        self.frame_totais = None
        self.btn_adicionar = None
        self.btn_excluir = None
        self.entry_cliente = None
        self.entry_pedido = None
        self.entry_qtde_itens = None
        self.entry_data_entrada = None
        self.entry_data_processo = None
        self.entry_tempo_corte = None
        self.entry_valor_pedido = None
        self.tabela_layout = None
        self.tabela = None
        self.entry_filtro_cliente = None
        self.entry_filtro_pedido = None
        self.timer_cliente = None
        self.timer_pedido = None
        self.btn_limpar_filtros = None
        self.label_total_pedidos = None
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
        self.autocomplete_manager = autocomplete.AutocompleteManager(
            parent=self,
            carregar_clientes=data.carregar_clientes_upper,
        )
        self.periodo_controller = None
        self._timer_atualizacao_datas = None

        self.init_ui()
        self._configurar_atualizacao_automatica_datas()
        self.carregar_dados()

    def init_ui(self):
        """Inicializa a interface do usuário."""
        main_layout = QVBoxLayout()

        self._criar_frame_entrada()
        main_layout.addWidget(self.frame_entrada)

        self._criar_tabela()
        main_layout.addLayout(self.tabela_layout)

        self._criar_frame_totais()
        main_layout.addWidget(self.frame_totais)

        self.setLayout(main_layout)

        self.configurar_atalhos()

    def configurar_atalhos(self):
        """Configura os atalhos de teclado para a aplicação."""
        self.shortcut_enter = QShortcut(QKeySequence(Qt.Key.Key_Return), self)
        self.shortcut_enter.activated.connect(self.atalho_adicionar_pedido)

        self.shortcut_enter_num = QShortcut(
            QKeySequence(Qt.Key.Key_Enter), self)
        self.shortcut_enter_num.activated.connect(
            self.atalho_adicionar_pedido)

        self.shortcut_delete = QShortcut(QKeySequence(Qt.Key.Key_Delete), self)
        self.shortcut_delete.activated.connect(self.excluir_pedido)

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

    def _converter_cliente_maiuscula(self, texto):
        """Convert the client field text to uppercase automatically."""
        self.entry_cliente.blockSignals(True)
        try:
            posicao_cursor = self.entry_cliente.cursorPosition()
            texto_normalizado = normalizar_nome_cliente(texto)
            self.entry_cliente.setText(texto_normalizado)
            self.entry_cliente.setCursorPosition(
                min(posicao_cursor, len(texto_normalizado)))
        finally:
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

    def _on_valor_pedido_editado(self, texto: str) -> None:
        """Formata o valor digitado para o padrão brasileiro (ex.: 123,45)."""
        if self.entry_valor_pedido is None:
            return

        self.entry_valor_pedido.blockSignals(True)
        try:
            valor_formatado = normalizar_valor_padrao_brasileiro(texto)
            self.entry_valor_pedido.setText(valor_formatado)
            self.entry_valor_pedido.setCursorPosition(len(valor_formatado))
        finally:
            self.entry_valor_pedido.blockSignals(False)

    def showEvent(self, event):  # pylint: disable=invalid-name
        """Garante atualização de datas quando o widget volta a ser exibido."""
        super().showEvent(event)
        self._verificar_atualizacao_datas_formulario(forcar=True)

    def _configurar_atualizacao_automatica_datas(self) -> None:
        """Configura a atualização periódica dos campos de data."""
        self._verificar_atualizacao_datas_formulario(forcar=True)

        if self._timer_atualizacao_datas is None:
            self._timer_atualizacao_datas = QTimer(self)
            # Atualiza a cada 1 hora para capturar viradas de dia sem custo alto.
            self._timer_atualizacao_datas.setInterval(60 * 60 * 1000)
            self._timer_atualizacao_datas.timeout.connect(
                self._verificar_atualizacao_datas_formulario
            )
            self._timer_atualizacao_datas.start()

    def _verificar_atualizacao_datas_formulario(self, forcar: bool = False) -> None:
        """Verifica se é necessário atualizar datas e limites do formulário."""
        nova_data = obter_data_atual_utc()
        max_entrada = (
            self.entry_data_entrada.maximumDate()
            if self.entry_data_entrada is not None
            else None
        )
        max_processo = (
            self.entry_data_processo.maximumDate()
            if self.entry_data_processo is not None
            else None
        )

        if (
            not forcar
            and self._timer_atualizacao_datas is not None
            and max_entrada == nova_data
            and (max_processo is None or max_processo == nova_data)
        ):
            return

        self._atualizar_limite_e_valor_data(
            self.entry_data_entrada,
            nova_data,
            preservar_nulos=False,
        )
        self._atualizar_limite_e_valor_data(
            self.entry_data_processo,
            nova_data,
            preservar_nulos=True,
        )

    @staticmethod
    def _atualizar_limite_e_valor_data(
        campo,
        nova_data,
        *,
        preservar_nulos: bool,
    ) -> None:
        if campo is None or nova_data is None:
            return

        campo.blockSignals(True)
        try:
            data_antiga = campo.maximumDate()
            campo.setMaximumDate(nova_data)

            valor_atual = campo.date()
            if preservar_nulos and hasattr(valor_atual, "isNull") and valor_atual.isNull():
                return

            if valor_atual == data_antiga:
                campo.setDate(nova_data)
        finally:
            campo.blockSignals(False)

    def atalho_adicionar_pedido(self):
        """Adiciona pedido via atalho se campos obrigatórios estiverem ok."""
        cliente = self.entry_cliente.text().strip()
        pedido = self.entry_pedido.text().strip()
        qtde_itens = self.entry_qtde_itens.text().strip()
        valor_pedido = self.entry_valor_pedido.text().strip()

        if cliente and pedido and qtde_itens and valor_pedido:
            self.adicionar_pedido()
        else:
            if not cliente:
                self.entry_cliente.setFocus()
            elif not pedido:
                self.entry_pedido.setFocus()
            elif not qtde_itens:
                self.entry_qtde_itens.setFocus()
            elif not valor_pedido:
                self.entry_valor_pedido.setFocus()

    def _criar_frame_entrada(self):
        """Cria o frame de entrada de dados."""
        controles = form.criar_formulario(
            parent=self,
            on_tempo_editado=self._on_tempo_corte_editado,
            on_cliente_editado=self._converter_cliente_maiuscula,
            on_valor_editado=self._on_valor_pedido_editado,
            on_submit=self.adicionar_pedido,
        )

        self.frame_entrada = controles.frame
        self.entry_cliente = controles.cliente
        self.entry_pedido = controles.pedido
        self.entry_qtde_itens = controles.qtde_itens
        self.entry_data_entrada = controles.data_entrada
        self.entry_data_processo = controles.data_processo
        self.entry_tempo_corte = controles.tempo_corte
        self.entry_valor_pedido = controles.valor_pedido
        self.btn_adicionar = controles.btn_adicionar

        self.autocomplete_manager.configure_form(self.entry_cliente)

    def _criar_tabela(self):
        """Cria a interface da tabela de pedidos com filtros."""
        self.tabela_layout = QVBoxLayout()
        filtros = filters.criar_filtros(
            parent=self,
            is_admin=self.is_admin,
            on_cliente_timeout=self.aplicar_filtro,
            on_pedido_timeout=self.aplicar_filtro,
            on_ano_changed=self.on_ano_changed,
            on_periodo_changed=self.aplicar_filtro,
            on_usuario_changed=self.on_usuario_changed,
            on_limpar=self.limpar_filtros,
        )
        self.tabela_layout.addWidget(filtros.frame)

        self.combo_usuario = filtros.combo_usuario if self.is_admin else None
        self.entry_filtro_cliente = filtros.entry_cliente
        self.entry_filtro_pedido = filtros.entry_pedido
        self.combo_filtro_ano = filtros.combo_ano
        self.combo_filtro_periodo = filtros.combo_periodo
        self.btn_limpar_filtros = filtros.btn_limpar
        self.timer_cliente = filtros.timer_cliente
        self.timer_pedido = filtros.timer_pedido

        self.periodo_controller = periodo.PeriodoFiltroController(
            combo_ano=self.combo_filtro_ano,
            combo_periodo=self.combo_filtro_periodo,
            listar_anos=data.listar_anos_disponiveis,
            listar_periodos=data.listar_periodos_do_ano,
            obter_usuario=self._calcular_usuario_filtro,
        )

        self.autocomplete_manager.configure_filter(self.entry_filtro_cliente)

        tabela_controls = table.criar_tabela(
            parent=self,
            is_admin=self.is_admin,
            on_item_changed=self.on_item_changed,
            on_excluir=self.excluir_pedido,
        )

        self.tabela = tabela_controls.tabela
        self.btn_excluir = tabela_controls.btn_excluir
        self.aplicar_larguras_colunas = tabela_controls.aplicar_larguras

        self.tabela_layout.addWidget(tabela_controls.frame)

    def _criar_frame_totais(self):
        """Cria o frame que exibe os totais (pedidos, itens, valores)."""
        controles_totais = totais.criar_totais(
            parent=self,
            espacamento=ESPACAMENTO_PADRAO,
        )

        self.controles_totais = controles_totais
        self.frame_totais = controles_totais.frame
        self.label_total_pedidos = controles_totais.label_pedidos
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

        if hasattr(self, "entry_filtro_pedido"):
            self.entry_filtro_pedido.blockSignals(True)
            self.entry_filtro_pedido.clear()
            self.entry_filtro_pedido.blockSignals(False)

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
            logger.exception(
                "Erro ao aplicar filtro do período corrente: %s", e)
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

    # pylint: disable=R0912,R0914

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

            registro_id = table_edit.obter_registro_id(
                self.tabela, row, self.is_admin
            )
            if not registro_id:
                return

            col_editada = col - col_offset
            valor_editado = item.text().strip()

            ok, erro_msg = table_edit.validar_edicao_celula(
                col_editada, valor_editado
            )
            if not ok:
                if erro_msg:
                    QMessageBox.warning(self, "Erro", erro_msg)
                self.aplicar_filtro(rolar_para_ultimo=False)
                return

            dados_linha = table_edit.extrair_campos_linha(
                self.tabela,
                row,
                col_offset,
            )

            # Validação cruzada de datas
            if col_editada in (3, 4):  # data_entrada ou data_processo
                ok_datas, msg_datas = self._validar_datas_entrada_processo(
                    dados_linha.data_entrada, dados_linha.data_processo
                )
                if not ok_datas:
                    QMessageBox.warning(self, "Erro", msg_datas)
                    self.aplicar_filtro(rolar_para_ultimo=False)
                    return

            resultado = db.atualizar_lancamento(
                registro_id,
                **dados_linha.to_update_kwargs(),
            )

            if "Sucesso" in resultado and col_editada == 3:
                self.configurar_filtros_ano_periodo()

            if "Sucesso" in resultado:
                # Verificar se o período do registro editado precisa ajustar o filtro
                if col_editada in (3, 4):  # data_entrada ou data_processo
                    # Usar data_processo se disponível, senão data_entrada
                    data_registro_str = (
                        dados_linha.data_processo or dados_linha.data_entrada
                    )
                    if data_registro_str:
                        data_registro = datetime.strptime(
                            data_registro_str, "%Y-%m-%d")
                        periodo_inicio, periodo_fim = (
                            calcular_periodo_faturamento_para_data_datas(
                                data_registro)
                        )

                        # Verificar se o filtro já está no período do registro
                        periodo_selecionado_inicio, periodo_selecionado_fim = (
                            self.periodo_controller.obter_periodo_selecionado()
                            if self.periodo_controller
                            else (None, None)
                        )
                        filtro_no_periodo_registro = (
                            periodo_selecionado_inicio
                            == periodo_inicio.strftime("%Y-%m-%d")
                            and periodo_selecionado_fim
                            == periodo_fim.strftime("%Y-%m-%d")
                        )

                        if not filtro_no_periodo_registro:
                            self._ajustar_periodo_para_registro(
                                periodo_inicio,
                                periodo_fim,
                                dados_linha.cliente,
                                dados_linha.pedido,
                                dados_linha.data_entrada,
                            )

            if "Sucesso" not in resultado:
                QMessageBox.warning(self, "Erro", resultado)

            self.aplicar_filtro(rolar_para_ultimo=False)

        except (ValueError, AttributeError, TypeError) as e:
            self.aplicar_filtro(rolar_para_ultimo=False)
            QMessageBox.warning(
                self, "Erro", f"Erro ao atualizar registro: {str(e)}")
        finally:
            self.tabela.blockSignals(False)

    def _validar_datas_entrada_processo(
        self, data_entrada: str | None, data_processo: str | None
    ) -> tuple[bool, str | None]:
        """Valida se data de entrada não é maior que data de processo."""
        if not data_entrada or not data_processo:
            return True, None
        try:
            dt_entrada = datetime.strptime(data_entrada, "%Y-%m-%d").date()
            dt_processo = datetime.strptime(data_processo, "%Y-%m-%d").date()
            if dt_entrada > dt_processo:
                return (
                    False,
                    "Data de entrada não pode ser maior que a data de processo.",
                )
        except ValueError:
            return False, "Datas inválidas."
        return True, None

    # pylint: disable=R0914,R0917

    def _ajustar_periodo_para_registro(
        self,
        periodo_inicio: date,
        periodo_fim: date,
        cliente: str,
        pedido: str,
        data_entrada: str,
    ) -> None:
        """Ajusta o filtro de período se necessário para o registro."""
        if not self.periodo_controller:
            return

        periodo_selecionado_inicio, periodo_selecionado_fim = (
            self.periodo_controller.obter_periodo_selecionado()
        )
        filtro_no_periodo_registro = (
            periodo_selecionado_inicio == periodo_inicio.strftime("%Y-%m-%d")
            and periodo_selecionado_fim == periodo_fim.strftime("%Y-%m-%d")
        )

        if not filtro_no_periodo_registro:
            # Garantir que o ano esteja disponível
            ano_periodo = str(periodo_inicio.year)
            combo_ano = self.periodo_controller.combo_ano
            if ano_periodo not in [
                combo_ano.itemText(i) for i in range(combo_ano.count())
            ]:
                combo_ano.addItem(ano_periodo)
                # Ordenar os anos
                anos = []
                for i in range(1, combo_ano.count()):
                    anos.append(combo_ano.itemText(i))
                anos.sort(reverse=True)
                combo_ano.clear()
                combo_ano.addItem("Todos os anos")
                for ano in anos:
                    combo_ano.addItem(ano)

            controller = self.periodo_controller
            controller.selecionar_ano(ano_periodo)
            controller.atualizar_periodos()

            # Selecionar o período
            periodo_display = (
                f"{periodo_inicio.strftime('%d/%m')} a {periodo_fim.strftime('%d/%m')}"
            )
            controller.selecionar_periodo_por_datas(periodo_display)

            # Destacar o item
            QTimer.singleShot(
                100,
                lambda: self.selecionar_registro_recente(
                    cliente, pedido, data_entrada
                ),
            )

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
        """Obtém filtros de cliente e pedido a partir dos campos de texto."""
        cliente_filtro = None
        if (
            hasattr(self, "entry_filtro_cliente")
            and self.entry_filtro_cliente.text().strip()
        ):
            cliente_filtro = self.entry_filtro_cliente.text().strip().upper()

        pedido_filtro = None
        if (
            hasattr(self, "entry_filtro_pedido")
            and self.entry_filtro_pedido.text().strip()
        ):
            pedido_filtro = self.entry_filtro_pedido.text().strip()

        return cliente_filtro, pedido_filtro

    def _obter_periodo_selecionado(self):
        """Retorna (data_inicio, data_fim) do período selecionado, se houver."""
        if not self.periodo_controller:
            return None, None
        return self.periodo_controller.obter_periodo_selecionado()

    def aplicar_filtro(self, rolar_para_ultimo=True):
        """Aplica filtros e preenche a tabela."""
        usuario_filtro = self._calcular_usuario_filtro()
        cliente_filtro, pedido_filtro = self._obter_filtros_texto()
        data_inicio, data_fim = self._obter_periodo_selecionado()

        registros_ordenados = data.buscar_registros_filtrados(
            usuario=usuario_filtro,
            cliente=cliente_filtro,
            pedido=pedido_filtro,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        table.preencher_tabela(
            tabela=self.tabela,
            registros=registros_ordenados,
            is_admin=self.is_admin,
        )

        filtros = {
            "usuario": usuario_filtro,
            "cliente": cliente_filtro,
            "pedido": pedido_filtro,
            "data_inicio": data_inicio,
            "data_fim": data_fim,
        }

        self.atualizar_totais(filtros)

        if rolar_para_ultimo:
            self.rolar_para_ultimo_item()

    def limpar_formulario(self):
        """Limpa todos os campos do formulário de entrada."""
        self.entry_cliente.clear()
        self.entry_pedido.clear()
        self.entry_qtde_itens.clear()
        self.entry_data_entrada.setDate(obter_data_atual_utc())
        self.entry_data_processo.clear()
        self.entry_tempo_corte.clear()
        self.entry_valor_pedido.clear()

    def rolar_para_ultimo_item(self):
        """Rola a tabela até o último item e o seleciona visivelmente."""
        if self.tabela.rowCount() > 0:
            ultima_linha = self.tabela.rowCount() - 1
            self.tabela.scrollToBottom()
            self.tabela.selectRow(ultima_linha)
            # Define a célula atual para maior visibilidade
            self.tabela.setCurrentCell(ultima_linha, 0)
            self.tabela.setFocus()  # Dá foco à tabela para destacar a seleção

    def selecionar_registro_recente(
        self, cliente: str, pedido: str, data_entrada: str
    ):
        """Select the recently added record in the table.

        Based on the provided data.
        """
        offset = 1 if self.is_admin else 0
        data_entrada_formatada = formatar_data_para_exibicao(data_entrada)

        for row in range(self.tabela.rowCount()):
            # Verificar se os dados da linha correspondem ao registro recém-adicionado
            cliente_tabela = self.tabela.item(row, offset).text()
            pedido_tabela = self.tabela.item(row, 1 + offset).text()
            data_entrada_tabela = self.tabela.item(row, 3 + offset).text()

            if (
                cliente_tabela.upper() == cliente.upper()
                and pedido_tabela == pedido
                and data_entrada_tabela == data_entrada_formatada
            ):
                # Encontrou o registro, selecionar e rolar para ele
                self.tabela.selectRow(row)
                self.tabela.setCurrentCell(row, offset)
                self.tabela.scrollToItem(self.tabela.item(row, offset))
                self.tabela.setFocus()
                break

    def atualizar_totais(self, filtros: dict | None = None):
        """Atualiza os totalizadores do painel."""
        if not self.controles_totais:
            return

        filtros = filtros or {}
        estatisticas = data.obter_estatisticas_totais(filtros)

        totais.atualizar_totais(
            self.controles_totais,
            total_pedidos=estatisticas.total_pedidos,
            total_itens=estatisticas.total_itens,
            total_valor=estatisticas.total_valor,
            formatar_valor=formatar_valor_monetario,
            media_dias_processamento=estatisticas.media_dias_processamento,
            media_itens_por_dia=estatisticas.media_itens_por_dia,
            estimativa_itens_mes=estatisticas.estimativa_itens_mes,
            horas_processadas_dia=estatisticas.horas_processadas_dia,
        )

    # pylint: disable=R0914

    def adicionar_pedido(self):
        """Valida campos e insere novo pedido no banco."""
        form_data = {
            "cliente": normalizar_nome_cliente(self.entry_cliente.text()),
            "pedido": self.entry_pedido.text().strip(),
            "qtde_itens": self.entry_qtde_itens.text().strip(),
            "valor_pedido": self.entry_valor_pedido.text().strip(),
            "tempo_corte": self.entry_tempo_corte.text().strip(),
        }

        data_entrada_qdate = self.entry_data_entrada.date()
        if data_entrada_qdate > obter_data_atual_utc():
            QMessageBox.warning(
                self, "Erro", "Data de entrada não pode ser maior que a data atual."
            )
            return
        data_entrada = data_entrada_qdate.toString("yyyy-MM-dd")

        data_processo_qdate = self.entry_data_processo.date()
        if not data_processo_qdate.isNull():
            if data_processo_qdate > obter_data_atual_utc():
                QMessageBox.warning(
                    self,
                    "Erro",
                    "Data de processo não pode ser maior que a data atual.",
                )
                return
            if data_processo_qdate < data_entrada_qdate:
                QMessageBox.warning(
                    self,
                    "Erro",
                    "Data de processo não pode ser menor que a data de entrada.",
                )
                return
            data_processo = data_processo_qdate.toString("yyyy-MM-dd")
        else:
            data_processo = ""

        # Capturar anos disponíveis antes da adição
        usuario_filtro = self._calcular_usuario_filtro()
        anos_antes = set(
            data.listar_anos_disponiveis(usuario_filtro))

        resultado = db.adicionar_lancamento(
            usuario=self.usuario_logado,
            cliente=form_data["cliente"],
            pedido=form_data["pedido"],
            qtde_itens=form_data["qtde_itens"],
            data_entrada=data_entrada,
            data_processo=data_processo,
            valor_pedido=form_data["valor_pedido"],
            tempo_corte=form_data["tempo_corte"],
        )

        if "Sucesso" in resultado:
            QMessageBox.information(self, "Sucesso", resultado)
            self.limpar_formulario()

            self.autocomplete_manager.refresh_all()

            # Verificar se novos anos foram criados e recarregar filtros se necessário
            anos_depois = set(
                data.listar_anos_disponiveis(usuario_filtro))
            novos_anos_criados = anos_depois != anos_antes

            if novos_anos_criados:
                self.configurar_filtros_ano_periodo()

            # Selecionar automaticamente o período correspondente ao novo registro
            # Usar data de processo se disponível, senão usar data de entrada
            data_registro = datetime.strptime(
                data_processo if data_processo else data_entrada, "%Y-%m-%d"
            )
            periodo_inicio, periodo_fim = calcular_periodo_faturamento_para_data_datas(
                data_registro
            )

            # Verificar se o filtro já está no período do registro
            periodo_selecionado_inicio, periodo_selecionado_fim = (
                self.periodo_controller.obter_periodo_selecionado()
                if self.periodo_controller
                else (None, None)
            )
            filtro_no_periodo_registro = (
                periodo_selecionado_inicio == periodo_inicio.strftime(
                    "%Y-%m-%d")
                and periodo_selecionado_fim == periodo_fim.strftime("%Y-%m-%d")
            )

            if not filtro_no_periodo_registro:
                self._ajustar_periodo_para_registro(
                    periodo_inicio,
                    periodo_fim,
                    form_data["cliente"],
                    form_data["pedido"],
                    data_entrada,
                )

            self.aplicar_filtro()
            self.entry_cliente.setFocus()
        else:
            QMessageBox.warning(self, "Erro", resultado)

    def excluir_pedido(self):
        """Exclui o pedido selecionado na tabela."""
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.information(
                self,
                "Seleção",
                (
                    "Selecione um pedido na tabela para excluir.\n\n"
                    "Dica: Clique em uma linha e pressione Delete ou "
                    "use o botão 'Excluir Selecionado'."
                ),
            )
            return

        if not self.is_admin:
            cliente = self.tabela.item(row, 0).text()
            pedido = self.tabela.item(row, 1).text()
        else:
            cliente = self.tabela.item(row, 1).text()
            pedido = self.tabela.item(row, 2).text()

        resposta = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            (
                "Tem certeza que deseja excluir este pedido?\n\n"
                f"Cliente: {cliente}\nPedido: {pedido}"
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
                    # Removido: self.configurar_filtros_ano_periodo() - não é necessário
                    # recarregar filtros após excluir um registro
                    self.aplicar_filtro(rolar_para_ultimo=False)
                else:
                    QMessageBox.warning(self, "Erro", resultado)
