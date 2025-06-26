import customtkinter as ctk
from tkinter import ttk
import utils.database as db
import utils.usuario as usuario
from tkinter import messagebox

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
    
        # Janela principal
        self.title("Controle de Processos")
        self.geometry("800x600")

        # Criação da tabela
        self.criar_frame_usuario()
        self.criar_frame_tabela()
        self.criar_frame_lancamento()

        self.atualizar_tabela()

    def criar_frame_usuario(self):
        """Cria o frame de usuário, onde o usuario pode ser selecionado."""
        self.frame_usuario = ctk.CTkFrame(self)
        self.frame_usuario.pack(expand=True, fill="both")

        ctk.CTkLabel(self.frame_usuario, text="Usuário:").pack(side="left")
        self.entry_usuario = ctk.CTkEntry(self.frame_usuario)
        self.entry_usuario.pack(side="left")

        self.btn_novo_usuario = ctk.CTkButton(self.frame_usuario, text="Novo Usuário", command=self.formulario_novo_usuario)
        self.btn_novo_usuario.pack(side="left")

        self.btn_login = ctk.CTkButton(self.frame_usuario, text="Login",)
        self.btn_login.pack(side="left")

        self.btn_logout = ctk.CTkButton(self.frame_usuario, text="Logout")
        self.btn_logout.pack(side="left")

        self.btn_admin = ctk.CTkButton(self.frame_usuario, text="Admin")
        self.btn_admin.pack(side="left")

    def criar_frame_tabela(self):

        self.frame_tabela = ctk.CTkFrame(self)
        self.frame_tabela.pack(expand=True, fill="both")

        colunas = ("ID", "usuario", "Cliente", "Número OS", "Quantidade de Itens", "Data de Lançamento","Data do Pedido", "Valor do Pedido")
        self.tabela_processos = ttk.Treeview(self.frame_tabela, columns=colunas, show="headings")
        for coluna in colunas:
            self.tabela_processos["displaycolumns"] = ["Cliente", "Número OS", "Quantidade de Itens", "Data de Lançamento","Data do Pedido", "Valor do Pedido"]
            self.tabela_processos.heading(coluna, text=coluna)
            self.tabela_processos.column(coluna, anchor="center", width=100)

        self.tabela_processos.pack(expand=True, fill="both")

    def criar_frame_lancamento(self):
        """Cria o frame de lançamento, onde os dados do processo são inseridos."""
        self.frame_lancamento = ctk.CTkFrame(self)
        self.frame_lancamento.pack(expand=True, fill="both")

        for i in range(7):
            self.frame_lancamento.grid_columnconfigure(i, weight=1)

        # Criação dos campos de entrada
        ctk.CTkLabel(self.frame_lancamento, text="Cliente:").grid(row=0, column=0)
        self.entry_cliente = ctk.CTkEntry(self.frame_lancamento)
        self.entry_cliente.grid(row=1, column=0)

        ctk.CTkLabel(self.frame_lancamento, text="Número OS:").grid(row=0, column=1)
        self.entry_numero_os = ctk.CTkEntry(self.frame_lancamento)
        self.entry_numero_os.grid(row=1, column=1)

        ctk.CTkLabel(self.frame_lancamento, text="Qtd. de Itens:").grid(row=0, column=2)
        self.entry_qtde_itens = ctk.CTkEntry(self.frame_lancamento)
        self.entry_qtde_itens.grid(row=1, column=2)

        ctk.CTkLabel(self.frame_lancamento, text="Data do Pedido:").grid(row=0, column=3)
        self.entry_data_pedido = ctk.CTkEntry(self.frame_lancamento)
        self.entry_data_pedido.grid(row=1, column=3)

        ctk.CTkLabel(self.frame_lancamento, text="Valor do Pedido:").grid(row=0, column=4)
        self.entry_valor_pedido = ctk.CTkEntry(self.frame_lancamento)
        self.entry_valor_pedido.grid(row=1, column=4)

        self.btn_lancar = ctk.CTkButton(self.frame_lancamento, text="Lançar", command=self.registro_lancamento)
        self.btn_lancar.grid(row=1, column=5)

        self.btn_excluir = ctk.CTkButton(self.frame_lancamento, text="Excluir", fg_color="red", command=self.excluir_lancamento)
        self.btn_excluir.grid(row=1, column=6)

    def registro_lancamento(self):
        registro = db.adicionar_lancamento(self.entry_usuario.get(),
                                            self.entry_cliente.get(),
                                            self.entry_numero_os.get(),
                                            self.entry_qtde_itens.get(),
                                            self.entry_data_pedido.get(),
                                            self.entry_valor_pedido.get())

        if "Sucesso" in registro:
            messagebox.showinfo("Sucesso", "Produção registrada com sucesso!")
            # Limpa os campos para o próximo lançamento, mantendo o usuario
            self.entry_usuario.delete(0, 'end')
            self.entry_cliente.delete(0, 'end')
            self.entry_numero_os.delete(0, 'end')
            self.entry_qtde_itens.delete(0, 'end')
            self.entry_data_pedido.delete(0, 'end')
            self.entry_valor_pedido.delete(0, 'end')
            self.entry_cliente.focus() # Foco no campo de Cliente
        else:
            messagebox.showerror("Erro de Validação", registro)

        self.atualizar_tabela()

    def excluir_lancamento(self):
        """Exclui o registro selecionado na tabela."""
        selected_item = self.tabela_processos.selection()[0] 
        if not selected_item:
            messagebox.showwarning("Seleção Inválida",
                                   "Por favor, selecione um registro para excluir.")
            return

        item_id = self.tabela_processos.item(selected_item, 'values')[0]
        db.excluir_lancamento(item_id)
        self.atualizar_tabela()

    def atualizar_tabela(self):
        """Atualiza a tabela com os registros do banco de dados."""
        registros = db.buscar_lancamentos_filtros()
        for item in self.tabela_processos.get_children():
            self.tabela_processos.delete(item)

        for registro in registros:
            self.tabela_processos.insert("", "end", values=registro)

    def formulario_novo_usuario(self):
        """Função para abrir o formulário de novo usuário."""
        self.novo_usuario_window = ctk.CTkToplevel(self)
        self.novo_usuario_window.title("Novo Usuário")
        self.novo_usuario_window.geometry("400x300")
        self.novo_usuario_window.focus_set()  # Foca na nova janela
        self.novo_usuario_window.grab_set()  # Bloqueia a janela principal enquanto esta estiver aberta

        # Campos para o novo usuário
        ctk.CTkLabel(self.novo_usuario_window, text="Nome:").grid(row=0, column=0)
        self.entry_nome = ctk.CTkEntry(self.novo_usuario_window)
        self.entry_nome.grid(row=0, column=1)

        ctk.CTkLabel(self.novo_usuario_window, text="Senha:").grid(row=1, column=0)
        self.entry_senha = ctk.CTkEntry(self.novo_usuario_window, show="*")
        self.entry_senha.grid(row=1, column=1)

        # Só exibe a checkbox de admin se não existir um admin
        self.check_admin = None
        if not usuario.verificar_admin_existente():
            ctk.CTkLabel(self.novo_usuario_window, text="Admin:").grid(row=2, column=0)
            self.check_admin = ctk.CTkCheckBox(self.novo_usuario_window, text="")
            self.check_admin.grid(row=2, column=1)
            btn_row = 3
        else:
            btn_row = 2

        self.btn_salvar = ctk.CTkButton(self.novo_usuario_window, text="Salvar", command=self.salvar_novo_usuario)
        self.btn_salvar.grid(row=btn_row, column=0, columnspan=2)

    def salvar_novo_usuario(self):
        """Salva o novo usuário no banco de dados."""
        nome = self.entry_nome.get()
        senha = self.entry_senha.get()
        admin = self.check_admin.get() if self.check_admin else False

        usuario.inserir_usuario(nome, senha, admin)
        self.novo_usuario_window.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()