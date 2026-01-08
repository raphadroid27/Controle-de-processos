# Changelog

Histórico de mudanças do aplicativo  Controle de Pedidos

## 1.3.0 (08/01/2026)

- Modernização da interface com ícones (FontAwesome) em menus, botões e diálogos
- Flexibilização da digitação de datas no formulário e na tabela (permite edição livre com validação apenas na confirmação)
- Adição de novas métricas de tempo: "Média tempo corte/dia" e "Tempo corte total"
- Ajuste na lógica de cálculo de médias para considerar apenas dias com produção
- Melhorias visuais e de usabilidade em diálogos de login, novos usuários e dashboard
- Refatoração extensa de código para melhor consistência, formatação e tratamento de erros

## 1.2.1 (12/11/2025)

- Melhoria na gestão de sessões e usuários, com limpeza de dados excluídos e ajustes de mensagens de feedback
- Implementação de arquivamento e remoção de bancos de dados de usuários
- Simplificação da formatação de código e revisão de textos de ajuda para maior clareza e consistência

## 1.2.0 (07/11/2025)

- Migração de terminologia de "processo(s)" para "pedido(s)" em toda aplicação
- Padronização de nomenclaturas para "Controle de Pedidos" e "Ferramenta Administrativa"
- Aprimoramento do sistema de gerenciamento de sessões (tipos, heartbeat, controles e comandos)
- Implementação de timer de inatividade no login e otimização periódica automática dos bancos de dados
- Centralização do sistema de logging e migração de subprocess para QProcess
- Otimização de desempenho com cache de métricas do dashboard e limpeza automática de caches
- Adição de exibição de horas processadas no dia e remoção de estimativa de itens/mês
- Normalização automática de clientes e valores nos formulários
- Atualização automática de datas e ajuste do tamanho mínimo da janela para 850x600
- Adição de manual completo com ajuda contextual e atualização da documentação
- Reorganização da arquitetura seguindo Clean Architecture

## 1.1.0 (29/10/2025)

- Implementação de sistema de IPC (comunicação entre processos) e reorganização de sessões
- Adição de restauração automática do período selecionado nos filtros
- Implementação de gráficos interativos no dashboard com atualização dinâmica de tabelas
- Ajuste da lógica de cálculo de períodos de faturamento e interface do dashboard
- Correção do cálculo de ano e mês nas métricas baseado no período de faturamento
- Remoção de script obsoleto de importação de CSV
- Atualização do título do changelog para "Controle de Pedidos"

## 1.0.1 (28/10/2025)

- Migração de terminologia de 'OS' para 'Proposta' em toda aplicação
- Atualização de placeholders e tooltips do campo de proposta para maior clareza
- Simplificação do método de exibição de login e melhorias de legibilidade
- Adição de timezone ao gerenciamento de datas do sistema
- Melhorias gerais de código e adição de ação de atualização no menu administrativo

## 1.0.0 (25/10/2025)

- Implementação inicial da aplicação "Controle de Processos" (primeiro release)
- Estrutura modular com separação de módulos, widgets e utilitários
- Interface completa com login, cadastro, gerenciamento de usuários e painel principal
- Sistema de filtros avançados (mês/ano/cliente/processo) com autocompletar
- Funcionalidades CRUD completas com validações, ordenação e edição in-place
- Navegação por teclado e atalhos para agilizar o uso
- Gerenciamento de sessões com controle de permissões e acesso administrativo
- Sistema de persistência com importação de CSV e limpeza automática de bancos órfãos
- Suporte a tema escuro com qdarktheme e ícones personalizados
- Scripts de automação para versionamento, análise de código e importações
- Refatoração completa para melhor legibilidade e manutenibilidade
- Formatação de valores monetários e mensagens de feedback ao usuário
- Documentação completa com README e instruções de uso
