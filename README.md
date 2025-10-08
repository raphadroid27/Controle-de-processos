# Controle de Processos

Sistema de gerenciamento de processos para desenhistas com interface gráfica PySide6 e persistência baseada em SQLAlchemy, mantendo bancos SQLite portáteis.

## Funcionalidades

- **Sistema de Login**: Autenticação com usuário e senha (com hash SHA-256)
- **Gerenciamento de Processos**: Controle completo de pedidos e processos
- **Tabela Interativa**: Visualização com QTableWidget incluindo:
  - Cliente
  - Número do Processo  
  - Quantidade de Itens
  - Data de Entrada
  - Data de Processamento
  - Valor do Pedido
- **Totalizadores**: Soma automática de processos, itens e valores
- **Filtros**: Visualização por usuário (para administradores)
- **Camada ORM com SQLAlchemy**: Banco compartilhado para credenciais e bancos individuais por usuário, todos em SQLite portátil
- **Tema escuro automático**: Interface aplicada com PyQtDarkTheme-fork, sincronizada com o tema do sistema
- **Seleção manual de tema**: Menu com opções Claro, Escuro ou Automático diretamente na aplicação

## Estrutura do Projeto

```
Controle-de-processos/
├── .git/                    # Controle de versão Git
├── .gitignore              # Arquivos ignorados pelo Git
├── README.md               # Documentação completa
├── INSTRUCOES.md          # Manual de uso detalhado
├── requirements.txt       # Dependências do projeto
├── run_app.py            # Script principal para executar o aplicativo
├── database/              # Bancos SQLite (system.db + usuario_<slug>.db)
├── scripts/
│   └── (scripts utilitários)
└── src/
    ├── main.py           # Interface gráfica principal (PySide6)
    └── utils/
      ├── database.py   # Camada SQLAlchemy (engine/sessões)
      ├── usuario.py    # Gerenciamento de usuários
      └── session_manager.py  # Controle de sessões e comandos
```

## Requisitos

- Python 3.8 ou superior
- PySide6
- PyQtDarkTheme-fork (qdarktheme)
- SQLAlchemy 2.x
- SQLite3 (incluído no Python)

## Instalação

1. Clone ou baixe o projeto
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

## Como Usar

### Executar o Aplicativo

**Opção 1 - A partir da pasta `src`:**
```bash
cd src
python main.py
```

**Opção 2 - A partir da pasta raiz:**
```bash
python src/main.py
```

### Primeiro Acesso

1. Na tela de login, clique em "Novo Usuário"
2. Crie o primeiro usuário (terá privilégios de administrador automaticamente)
3. Faça login com as credenciais criadas

### Funcionalidades Principais

#### Adicionar Processo
1. Preencha os campos obrigatórios:
   - Cliente
   - Número do Processo
   - Quantidade de Itens
   - Data de Entrada
   - Valor do Pedido
2. Campo opcional: Data de Processamento
3. Clique em "Adicionar"

#### Visualizar Processos
- A tabela exibe todos os processos do usuário logado
- Administradores podem ver processos de todos os usuários
- Use o filtro por usuário para visualizações específicas

#### Totalizadores
- **Total Processos**: Quantidade total de processos
- **Total Itens**: Soma de todos os itens
- **Total Valor**: Soma dos valores em reais

#### Excluir Processo
1. Selecione uma linha na tabela
2. Clique em "Excluir"
3. Confirme a exclusão

## Estrutura do Banco de Dados

A persistência agora é dividida em dois grupos de arquivos SQLite:

- `database/system.db`: banco compartilhado utilizado pelo SQLAlchemy para as tabelas centrais (`usuario`, `system_control` e metadados).
- `database/usuario_<slug>.db`: um banco individual por usuário autenticado contendo somente a tabela `registro`, reduzindo bloqueios quando vários usuários lançam dados simultaneamente.

### Tabela `usuario` (system.db)
- `id`: Chave primária
- `nome`: Nome do usuário (único)
- `senha`: Hash SHA-256 da senha (ou `nova_senha` para resets pendentes)
- `admin`: Booleano para privilégios administrativos
- `criado_em`: Timestamp do momento de criação

### Tabela `system_control` (system.db)
- `type`: Agrupa entradas (ex.: `SESSION`, `COMMAND`)
- `key`: Identificador único da entrada
- `value`: Dados associados (ex.: `usuario|hostname`)
- `last_updated`: Última atualização, em UTC

### Tabela `registro` (usuario_<slug>.db)
- `id`: Chave primária autoincremental por usuário
- `usuario`: Nome do usuário responsável
- `cliente`: Nome do cliente
- `processo`: Número/identificação do processo
- `qtde_itens`: Quantidade de itens (integer)
- `data_entrada`: Data de entrada do pedido
- `data_processo`: Data de processamento (opcional)
- `valor_pedido`: Valor em reais (float)
- `data_lancamento`: Timestamp de criação do registro

## Segurança

- Senhas são armazenadas com hash SHA-256
- Usuários só visualizam seus próprios processos (exceto administradores)
- Validação de entrada em todos os campos
- Confirmação para exclusões

## Desenvolvimento

O projeto utiliza:
- **PySide6**: Interface gráfica moderna e responsiva
- **SQLite**: Banco de dados leve e confiável
- **Arquitetura modular**: Separação clara entre interface, lógica e dados

## Possíveis Melhorias Futuras

- Relatórios em PDF
- Gráficos de produtividade
- Backup automático do banco
- Importação/exportação de dados
- Notificações de prazos
- Histórico de alterações

## Autor

Sistema desenvolvido para controle de processos de desenhistas.