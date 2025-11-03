# Changelog

Histórico de mudanças do aplicativo Controle de Processos

## 1.1.0 (29/10/2025)

- refatora: implementa gerenciamento de IPC e reorganiza sessões do sistema
- refatora: adiciona restauração do período selecionado no filtro de processos
- recurso: adiciona funcionalidades de gráficos do dashboard e atualização de tabelas
- refatora: ajusta lógica de cálculo de períodos de faturamento e atualiza interface do dashboard
- refatora: ajusta cálculo de ano e mês nas métricas do dashboard com base no período de faturamento
- remove: exclui script de importação de CSV para o banco do usuário
- refatora: atualiza o título do changelog para refletir o nome correto do aplicativo

## 1.0.1 (28/10/2025)

- refatoração: renomeia 'os'/'OS' para 'proposta'/'propostas' em código, dashboards, dialogs, componentes CRUD e filtros
- refatoração: atualiza placeholders e tooltips do campo de proposta para maior clareza
- refatoração: simplifica método mostrar_login e remove quebras de linha desnecessárias para melhorar legibilidade
- refatoração: adiciona timezone ao gerenciamento de datas
- refatoração: melhorias gerais de legibilidade e adiciona ação de atualização no menu de administração

## 1.0.0 (25/10/2025)

- Implementação inicial da aplicação "Controle de Processos" (primeiro release).
- Estrutura principal da aplicação e modularização: separação de módulos, widgets e utilitários, reorganização do main.py e adição de __init__.py em utils.
- Interface de usuário completa: telas de login e cadastro, janela principal, gerenciamento de usuários, painel de processos com filtros (mês/ano/cliente/processo), autocompletar, navegação por teclado e edição in-place.
- Funcionalidades de CRUD para processos: criação, edição, exclusão, validações de datas e valores, ordenação e filtros avançados; histórico e cálculo de estimativas/estatísticas no painel de totais.
- Gerenciamento de sessão e permissões: login/logout, verificação de admin e controle de acesso a funções administrativas.
- Persistência e migrações: atualizações no banco de dados de processos, importação de lançamentos via CSV e remoção/limpeza de bancos órfãos; .gitignore atualizado.
- Temas e aparência: suporte a tema escuro (manual e com qdarktheme), ícones adicionados (ICO, PNG, SVG) e aplicação de estilo via ThemeManager.
- Utilitários e automação: scripts para atualização de versão/changelog, análise de qualidade de código e scripts de importação; configuração do pylint.
- Melhorias de qualidade do código: ampla refatoração (legibilidade, formatação de importações, remoção de código morto, centralização de constantes), normalização de comparações e atualização de hashing para SHA‑256.
- Ajustes de usabilidade: padronização de dimensões/margens, formatação de valores monetários, mensagens de feedback e atalhos de teclado.
- Documentação e README atualizados com instruções de execução e mudanças relevantes.
- Primeiro commit e conjunto inicial de recursos/refatorações prontos para sequelas e correções futuras.
