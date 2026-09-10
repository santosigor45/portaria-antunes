# Publicação automática na Nautilus

Cada push em `main` executa **Validações básicas** na Oracle ARM64: compilação de sintaxe Python, JSON e shell. Não há suíte de testes de aplicação nesse fluxo. Pull requests não executam no runner próprio; `workflow_dispatch` permite conferir as validações, mas não publica.

Após um push aprovado, **Publicar na Nautilus** usa `ubuntu-24.04` no GitHub para construir imagens `linux/amd64`, identificadas por commit, execução e tentativa. O GitHub envia somente imagens prontas por SSH com comando restrito. O receptor na Nautilus confirma novamente o resultado das validações e que o commit ainda é o atual da branch, depois solicita a troca pelo Dokploy.

O build compara os arquivos com a última versão publicada de cada componente. Documentação e diretórios de testes não provocam build. Mudanças em `.github/` reconstroem os componentes para validar a automação. Na Oli, frontend e backend são selecionados separadamente; alterações acumuladas desde a última publicação também são consideradas.

O receptor preserva variáveis, redes, volumes e configuração do Compose; muda somente a imagem. Confere saúde local e HTTPS público. Uma falha confirmada restaura a imagem anterior; uma resposta inconclusiva do Dokploy bloqueia novas publicações para conferência, sem iniciar uma segunda operação concorrente. Nenhuma migração é executada automaticamente. Mudanças nos arquivos de migração dos projetos Python bloqueiam a ativação até a preparação do banco e aprovação do novo hash no servidor. Alterações de banco não são desfeitas por rollback de imagem.

## Configuração

- Runner: `portaria-oracle`, labels `self-hosted`, `Linux`, `ARM64`, `portaria-validacoes`.
- Variável de repositório `NAUTILUS_DEPLOY_ENABLED=true`; `false` pausa as próximas publicações.
- Environment `production`, restrito à branch `main`.
- Variável `NAUTILUS_DEPLOY_HOST`; secrets do environment `NAUTILUS_DEPLOY_SSH_KEY` e `NAUTILUS_DEPLOY_KNOWN_HOSTS`.
- A chave SSH permite somente `current`, `receive` e `status` deste projeto. O token do Dokploy fica no servidor, fora do GitHub.
- Configuração do receptor: `/etc/nautilus-deploy/portaria.json`; estado: `/var/lib/nautilus-deploy/portaria/`; código: `/opt/nautilus-deploy/`.

## Operação

Acompanhe as duas execuções na aba Actions. Depois de corrigir uma falha de infraestrutura, reexecute o workflow de publicação do commit atual; se a branch avançou, use a validação do push mais recente. Se uma validação foi cancelada antes de terminar, reexecute essa validação de push. Uma execução manual nova de validação não publica.

Antes de liberar uma migração, faça backup, revise a compatibilidade com a imagem anterior, aplique a migração manualmente na Nautilus e atualize `services.<componente>.migrations.approvedDigest` na configuração protegida do servidor. A Oli também compara os heads Alembic com a revisão efetiva do PostgreSQL. Posto e Portaria compartilham MySQL e têm históricos distintos; não executar automaticamente seus upgrades.

Estados `blocked` e `rollback_failed` exigem verificar fila do Dokploy, Compose, imagem e saúde antes de reconciliar `current.json` e remover `inflight.json`. Não apague o bloqueio enquanto existir um deploy pendente. O receptor mantém duas imagens publicadas com sucesso por componente, além da imagem em uso e das imagens iniciais da migração; não faz prune global.

O orçamento de Actions permanece o existente na conta; este fluxo não altera cobrança ou limites. Builds em repositórios privados consomem os minutos incluídos no GitHub.
