# DescompliADS — Acompanhamento oficial do projeto

Atualizado em: **02/09/2026 às 12:42 (America/Sao_Paulo)**
Branch de desenvolvimento: **`meta-ads-pro`**

Este documento é a fonte de verdade do andamento do DescompliADS no GitHub.
Ele deve ser atualizado ao iniciar ou encerrar qualquer gate para que não seja
necessário reler todo o código para descobrir o estado do produto.

## Regra de passagem entre gates

Um gate seguinte só pode entrar em implementação quando o anterior estiver
marcado como **CONCLUÍDO** e possuir evidências registradas neste documento.

Para concluir um gate, todos os itens aplicáveis devem estar comprovados:

- [ ] escopo e critérios de aceite aprovados;
- [ ] implementação concluída;
- [ ] testes automatizados aprovados;
- [ ] migrações aplicadas e verificadas, quando existirem;
- [ ] documentação e procedimento de recuperação atualizados;
- [ ] commit e push realizados na branch correta;
- [ ] deploy realizado, quando o gate afetar produção;
- [ ] validação funcional ou operacional em produção;
- [ ] pendências e riscos residuais registrados;
- [ ] estado espelhado no Notion.

### Significado dos estados

- **CONCLUÍDO:** todos os critérios do gate foram comprovados.
- **EM VALIDAÇÃO:** implementação pronta, mas ainda falta publicação, deploy ou evidência operacional.
- **EM ANDAMENTO:** implementação sendo realizada.
- **BLOQUEADO:** existe uma dependência que impede continuar.
- **PLANEJADO:** escopo conhecido, mas implementação ainda não autorizada.
- **NÃO DEFINIDO:** ainda não deve ser detalhado para evitar antecipar decisões.

## Visão atual

| Gate | Objetivo | Estado | Pode avançar? |
|---|---|---|---|
| Gate 1 | Confiança e semântica dos dados | **CONCLUÍDO** | Sim |
| Gate 2 | Confiabilidade da sincronização | **CONCLUÍDO** | Sim |
| Gate 3 | Central operacional do gestor | **PLANEJADO / LIBERADO** | Sim |
| Gate 4 | A definir após o Gate 3 | **NÃO DEFINIDO** | Não |

## Gate 1 — Confiança e semântica dos dados

**Estado:** CONCLUÍDO
**Objetivo:** garantir que os números exibidos tenham origem, fórmula,
disponibilidade e atualização compreensíveis.

### Entregue

- [x] contrato de confiança dos dados no dashboard;
- [x] métricas aditivas somadas corretamente;
- [x] taxas recalculadas a partir dos totais;
- [x] alcance e frequência tratados como métricas não aditivas;
- [x] atribuição da conta Meta e registro por impressão explicitados;
- [x] entidades `ARCHIVED` preservadas nas análises históricas;
- [x] reconciliação de 7, 30, 180 e 360 dias;
- [x] documentação das fórmulas e limitações;
- [x] evidência de reconciliação real registrada.

### Evidências

- Commit: `522e326` — `Complete data confidence gate`.
- Documento: [`docs/fases/gate-1-confianca-dados.md`](fases/gate-1-confianca-dados.md).
- Resultado registrado para 360 dias: investimento, impressões, cliques,
  cliques no link e conversas reconciliados entre Meta e Supabase.

## Gate 2 — Confiabilidade da sincronização

**Estado:** CONCLUÍDO
**Resultado:** Gate 3 liberado para implementação.

### Entregue e validado

- [x] sincronização diária no worker separado da API;
- [x] reprocessamento do dia atual e dos dois dias anteriores;
- [x] backfill configurável de até 360 dias;
- [x] proteção contra execuções simultâneas;
- [x] retries controlados para falhas temporárias;
- [x] estados `SUCCESS`, `PARTIAL` e `FAILED`;
- [x] alertas para token expirado e conta desatualizada;
- [x] fila persistente para o botão **Sincronizar agora**;
- [x] progresso e resultado expostos para a interface;
- [x] relatório de entidades importadas, atualizadas e arquivadas;
- [x] reprocessamento de uma execução que falhou;
- [x] procedimento de recuperação documentado;
- [x] migrações `0020_sync_control.sql` e `0021_sync_control_indexes.sql` aplicadas e verificadas;
- [x] testes automatizados locais aprovados.

### Critérios finais

- [x] criar o commit específico do Gate 2;
- [x] fazer push para `origin/meta-ads-pro`;
- [x] implantar a nova versão da API e do worker na VPS;
- [x] confirmar que API e worker usam as migrações `0020` e `0021`;
- [x] observar vários ciclos consecutivos na versão implantada;
- [x] reproduzir uma falha controlada e comprovar a recuperação em produção;
- [x] registrar IDs, horários e resultados das execuções de aceite;
- [x] confirmar que nenhum token ou segredo aparece nos registros examinados;
- [x] atualizar este documento e o Notion para **CONCLUÍDO**.

### Evidências disponíveis

- Commit: `1175da0` — `Complete sync reliability gate`.
- Deploy da API e do worker na VPS informado em 02/09/2026 às 12:13 (America/Sao_Paulo).
- Documento: [`docs/fases/gate-2-confiabilidade-sincronizacao.md`](fases/gate-2-confiabilidade-sincronizacao.md).

### Evidência final de aceite — 02/09/2026

- API pública respondeu `200` em `/health` no ambiente `production`;
- OpenAPI publicado contém `/api/v1/meta-sync/requests`, `/recover` e `/runs`;
- tabelas e colunas das migrações `0020` e `0021` responderam em produção;
- fila `sync_requests` recusou leitura anônima com código PostgreSQL `42501`;
- `/api/v1/meta-sync/runs` recusou acesso sem login com HTTP `401`;
- dez execuções recentes consecutivas estavam em `SUCCESS`;
- execução agendada `7a8e5232-8bb9-4934-b87e-01185cf63719` terminou em `SUCCESS`;
- recuperação da falha histórica `ca114930-ea86-4793-83f7-fc7d9f2ee4a0` foi solicitada pelo pedido `2b89a63d-1d82-4c30-b464-d27a82d1d089`;
- execução de recuperação `54e51e98-f798-485c-935a-9cf9e0e7370d` terminou em `RECOVERY/SUCCESS`, com uma conta concluída e nenhuma falha;
- conta `CONTACAZA85_1` atualizou entidades e métricas e permaneceu sem alertas abertos;
- busca pelos segredos configurados e por padrões de token não encontrou exposição nos registros examinados;
- backend: `107 passed`;
- frontend: lint e build de produção aprovados;
- o primeiro build local encontrou um bloqueio `EPERM` no cache `.next`; após remover somente o cache regenerável, o build foi concluído.

## Gate 3 — Central operacional do gestor

**Estado:** PLANEJADO / LIBERADO
**Objetivo:** permitir que o gestor trabalhe diariamente sem abrir
constantemente o Gerenciador da Meta.

### Escopo aprovado para o planejamento

- [ ] ritmo do orçamento mensal;
- [ ] gasto realizado, saldo e projeção;
- [ ] orçamento por campanha ou conjunto;
- [ ] identificação de campanhas ativas sem entrega;
- [ ] pesquisa em campanha, conjunto e anúncio;
- [ ] filtros, ordenação e escolha persistente de colunas;
- [ ] navegação campanha → conjunto → anúncio;
- [ ] comparação lado a lado entre entidades do mesmo nível;
- [ ] criativos com miniatura, texto, título, formato e CTA;
- [ ] visualizações de vídeo em 3 segundos;
- [ ] retenção de vídeo em 25%, 50%, 75% e 95%;
- [ ] ThruPlay e taxa de ThruPlay;
- [ ] LPV, taxa de chegada, custo por LPV e leads por LPV;
- [ ] exportação CSV da visualização filtrada;
- [ ] comportamento responsivo e acessível;
- [ ] testes automatizados e validação funcional.

### Base já existente que deve ser preservada

- ritmo mensal, gasto, saldo e projeção;
- orçamento e consumo por campanha e conjunto;
- hierarquia expansível campanha → conjunto → anúncio;
- pesquisa e filtros básicos de campanhas;
- escolha de colunas;
- comparação básica de duas campanhas;
- coleta de criativos e métricas de vídeo e página;
- preservação de entidades `ARCHIVED`.

### Lacunas conhecidas

- pesquisa e filtros ainda não abrangem plenamente conjuntos e anúncios;
- comparação ainda está limitada a campanhas;
- métricas de vídeo e página não estão expostas na tabela operacional;
- regra de “sem entrega” usa somente investimento e precisa considerar impressões;
- inspeção do criativo ainda é básica;
- exportação CSV ainda não existe.

### Condição para iniciar

Condição satisfeita em 02/09/2026 com a conclusão formal do Gate 2.

## Registro de atualização

Ao terminar uma sessão relevante, acrescente uma entrada curta:

| Data | Gate | Estado | O que mudou | Evidência | Próximo passo |
|---|---|---|---|---|---|
| 01/09/2026 | Gate 2 | Em validação | Implementação local inventariada; Gate 3 planejado e bloqueado | Documentos dos Gates 1 e 2 + estado do Git | Publicar e validar o Gate 2 |
| 02/09/2026 12:13 | Gate 2 | Em validação | API e worker implantados na VPS | Implantação informada pela responsável do projeto | Confirmar migrações e observar ciclos consecutivos |
| 02/09/2026 12:42 | Gate 2 | Concluído | Produção, ciclos, segurança e recuperação validados | 10 sucessos consecutivos; recuperação `54e51e98-f798-485c-935a-9cf9e0e7370d`; 107 testes; lint e build | Iniciar o Gate 3 |

## Backlog posterior

Itens como IA, CRM, Webhooks, automações de alteração na Meta e definição do
Gate 4 permanecem fora do escopo atual. Eles só devem ser priorizados depois da
conclusão formal do Gate 3.
