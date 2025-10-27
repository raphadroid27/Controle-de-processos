# Changelog

Histórico de mudanças do aplicativo Controle de Processos

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
