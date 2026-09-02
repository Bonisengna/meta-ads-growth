# DescompliADS — Acompanhamento oficial do projeto

Atualizado em: **01/09/2026**
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
| Gate 2 | Confiabilidade da sincronização | **EM VALIDAÇÃO** | Não |
| Gate 3 | Central operacional do gestor | **PLANEJADO / BLOQUEADO PELO GATE 2** | Não |
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

**Estado:** EM VALIDAÇÃO
**Bloqueia:** início da implementação do Gate 3.

### Implementado e validado localmente

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

### Falta para concluir

- [x] criar o commit específico do Gate 2;
- [x] fazer push para `origin/meta-ads-pro`;
- [ ] implantar a nova versão da API e do worker na VPS;
- [ ] confirmar que API e worker usam as migrações `0020` e `0021`;
- [ ] observar vários ciclos consecutivos na versão implantada;
- [ ] reproduzir uma falha controlada e comprovar a recuperação em produção;
- [ ] registrar IDs, horários e resultados das execuções de aceite;
- [ ] confirmar que nenhum token ou segredo aparece nos logs;
- [ ] atualizar este documento e o Notion para **CONCLUÍDO**.

### Evidências disponíveis

- Commit: `1175da0` — `Complete sync reliability gate`.
- Documento: [`docs/fases/gate-2-confiabilidade-sincronizacao.md`](fases/gate-2-confiabilidade-sincronizacao.md).

## Gate 3 — Central operacional do gestor

**Estado:** PLANEJADO / BLOQUEADO PELO GATE 2
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

Todos os itens de **Falta para concluir** do Gate 2 devem estar marcados como
concluídos, acompanhados das evidências de produção.

## Registro de atualização

Ao terminar uma sessão relevante, acrescente uma entrada curta:

| Data | Gate | Estado | O que mudou | Evidência | Próximo passo |
|---|---|---|---|---|---|
| 01/09/2026 | Gate 2 | Em validação | Implementação local inventariada; Gate 3 planejado e bloqueado | Documentos dos Gates 1 e 2 + estado do Git | Publicar e validar o Gate 2 |

## Backlog posterior

Itens como IA, CRM, Webhooks, automações de alteração na Meta e definição do
Gate 4 permanecem fora do escopo atual. Eles só devem ser priorizados depois da
conclusão formal do Gate 3.
