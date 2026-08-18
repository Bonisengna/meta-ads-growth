-- Prompts internos pertencem aos desenvolvedores e nunca são expostos ao painel ou à Data API.

create schema if not exists private;

revoke all on schema private from public, anon, authenticated;
grant usage on schema private to service_role;

create table private.ai_prompts (
    id uuid primary key default gen_random_uuid(),
    agent_slug text not null,
    version integer not null check (version > 0),
    prompt_content text not null check (length(prompt_content) > 0),
    active boolean not null default false,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (agent_slug, version)
);

create unique index ai_prompts_one_active_version
    on private.ai_prompts(agent_slug)
    where active;

alter table private.ai_prompts enable row level security;
revoke all on table private.ai_prompts from public, anon, authenticated;
grant select, insert, update, delete on table private.ai_prompts to service_role;

comment on table private.ai_prompts is
    'Prompts internos sem acesso pelo frontend, usuários autenticados ou Data API pública.';
