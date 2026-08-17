-- Índice recomendado pelo Performance Advisor para a FK de alertas por conta.
create index integration_alerts_meta_account_id
    on public.integration_alerts(meta_account_id)
    where meta_account_id is not null;
