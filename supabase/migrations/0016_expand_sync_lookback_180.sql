-- Permite carga histórica manual de até 180 dias sem alterar a janela diária padrão.

alter table public.sync_runs
    drop constraint if exists sync_runs_lookback_days;

alter table public.sync_runs
    add constraint sync_runs_lookback_days
    check (lookback_days between 1 and 180);
