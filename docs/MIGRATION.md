# Migração de Estrutura - Controle de Processos

## Resumo

A estrutura do projeto foi reorganizada seguindo princípios de Clean Architecture para melhor separação de responsabilidades.

## Nova Estrutura

```
src/
├── core/                      # Lógica de negócio central
│   ├── formatters.py         # Formatação de dados
│   ├── periodo_faturamento.py # Cálculos de período
│   └── tempo_corte.py        # Processamento de tempo
│
├── data/                      # Camada de dados
│   ├── config.py             # Configuração de banco
│   ├── models.py             # Modelos ORM
│   ├── helpers.py            # Helpers de dados
│   ├── sessions.py           # Gerenciamento de sessões DB
│   └── repositories/         # Repositórios CRUD
│       ├── crud.py           # Operações básicas
│       └── queries.py        # Consultas complexas
│
├── domain/                    # Serviços de domínio
│   ├── usuario_service.py    # Lógica de usuários
│   ├── session_service.py    # Gerenciamento de sessões
│   └── dashboard_service.py  # Métricas e dashboard
│
├── infrastructure/            # Infraestrutura técnica
│   ├── ipc/                  # Comunicação entre processos
│   │   ├── config.py         # Configuração IPC
│   │   └── manager.py        # Gerenciador IPC
│   └── logging/              # Logging
│       └── config.py         # Configuração de logs
│
└── ui/                        # Interface gráfica
    ├── main_window.py        # Janela principal
    ├── theme_manager.py      # Gerenciamento de temas
    ├── delegates.py          # Delegates personalizados
    ├── styles.py             # Estilos e constantes UI
    │
    ├── dialogs/              # Diálogos
    │   ├── login_dialog.py
    │   ├── dashboard_dialog.py
    │   ├── dashboard_plotting.py
    │   ├── dashboard_tables.py
    │   ├── manual_dialog.py
    │   └── sobre_dialog.py
    │
    ├── widgets/              # Widgets reutilizáveis
    │   ├── processos_widget.py  # Widget principal
    │   ├── usuarios_widget.py   # Gerenciamento de usuários
    │   ├── sessoes_widget.py    # Gerenciamento de sessões
    │   ├── navigable_widgets.py # Widgets navegáveis
    │   └── components/          # Componentes menores
    │
    └── resources/            # Recursos de UI
        └── help_loader.py    # Carregador de ajuda

docs/
└── help/                     # Conteúdo do manual (HTML)
    ├── manual.html
    ├── visao_geral.html
    ├── filtros.html
    ├── totais.html
    ├── dashboard.html
    ├── autenticacao.html
    ├── admin.html
    └── sobre.html
```

## Principais Mudanças

### Arquivos Movidos

| Antigo | Novo |
|--------|------|
| `src/utils/formatters.py` | `src/core/formatters.py` |
| `src/utils/periodo_faturamento.py` | `src/core/periodo_faturamento.py` |
| `src/utils/tempo_corte.py` | `src/core/tempo_corte.py` |
| `src/utils/database/*` | `src/data/*` |
| `src/utils/database/crud.py` | `src/data/repositories/crud.py` |
| `src/utils/database/queries.py` | `src/data/repositories/queries.py` |
| `src/utils/usuario.py` | `src/domain/usuario_service.py` |
| `src/utils/session_manager.py` | `src/domain/session_service.py` |
| `src/utils/dashboard_metrics.py` | `src/domain/dashboard_service.py` |
| `src/utils/ipc_config.py` | `src/infrastructure/ipc/config.py` |
| `src/utils/ipc_manager.py` | `src/infrastructure/ipc/manager.py` |
| `src/utils/logging_config.py` | `src/infrastructure/logging/config.py` |
| `src/utils/ui_config.py` | `src/ui/styles.py` |
| `src/login_dialog.py` | `src/ui/dialogs/login_dialog.py` |
| `src/gerenciar_usuarios.py` | `src/ui/widgets/usuarios_widget.py` |
| `src/gerenciar_sessoes.py` | `src/ui/widgets/sessoes_widget.py` |
| `src/widgets/widget.py` | `src/ui/widgets/processos_widget.py` |
| `src/widgets/dashboard_dialog.py` | `src/ui/dialogs/dashboard_dialog.py` |
| `src/forms/form_manual.py` | `src/ui/dialogs/manual_dialog.py` |
| `src/forms/form_sobre.py` | `src/ui/dialogs/sobre_dialog.py` |
| `src/forms/common/context_help.py` | `src/ui/resources/help_loader.py` |
| `src/forms/common/help_content/*.html` | `docs/help/*.html` |

### Classes Renomeadas

- `PedidosWidget` → `ProcessosWidget`

### Imports Atualizados

Todos os imports foram automaticamente atualizados usando os scripts:
- `scripts/update_imports.py` - Primeira fase (270 imports atualizados em 52 arquivos)
- `scripts/update_imports_phase2.py` - Segunda fase (28 imports adicionais em 16 arquivos)

## Benefícios

1. **Separação clara de responsabilidades** - Cada camada tem função bem definida
2. **Facilita testes** - Camadas isoladas são mais testáveis
3. **Reduz acoplamento** - Dependências mais explícitas
4. **Escalabilidade** - Adicionar features sem bagunçar estrutura
5. **Padrões de mercado** - Segue Clean Architecture/DDD simplificado

## Compatibilidade

- ✅ Aplicação principal (`src.app`) testada e funcionando
- ✅ Aplicação admin (`src.admin_app`) com imports atualizados
- ✅ Manual HTML movido para `docs/help/`
- ✅ Todos os imports automaticamente ajustados

## Próximos Passos

1. Remover diretórios e arquivos antigos duplicados
2. Executar testes completos
3. Atualizar documentação (README principal)
4. Commit das mudanças

## Data da Migração

**5 de novembro de 2025**
