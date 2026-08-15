-- MÓDULO 05/06 — FUNÇÕES DO HUB E FILA CAPI
-- Banco alvo: PostgreSQL / Supabase.
-- Pré-requisito: executar database/005-cria-hub-feedback-meta.sql.
-- Esta migration não contém tokens da Meta.

alter table public.meta_hub_clientes
  add column if not exists action_source_padrao text not null default 'other';

alter table public.meta_hub_clientes
  add column if not exists meta_test_event_code text;

create or replace function public.meta_hub_sha256(valor text)
returns text
language sql
immutable
strict
as $$
  select encode(digest(valor, 'sha256'), 'hex');
$$;

create or replace function public.meta_hub_receber_evento(p_payload jsonb)
returns jsonb
language plpgsql
as $$
declare
  v_cliente public.meta_hub_clientes%rowtype;
  v_lead public.meta_hub_leads%rowtype;
  v_evento_id uuid;
  v_evento text;
  v_evento_externo_id text;
  v_lead_externo_id text;
  v_sistema_origem text;
  v_ocorrido_em timestamptz;
  v_mapa record;
  v_event_id text;
  v_user_data jsonb := '{}'::jsonb;
  v_custom_data jsonb := '{}'::jsonb;
  v_payload_meta jsonb;
  v_publico_tipo text;
  v_publico_id uuid;
  v_email text;
  v_telefone text;
  v_external_id text;
  v_hash text;
  v_linhas integer := 0;
  v_fila_criada boolean := false;
begin
  if p_payload is null then
    raise exception 'payload obrigatório';
  end if;

  select *
    into v_cliente
  from public.meta_hub_clientes
  where chave_cliente = nullif(trim(p_payload->>'cliente'), '')
    and ativo = true
  limit 1;

  if not found then
    raise exception 'cliente não encontrado ou inativo: %', p_payload->>'cliente';
  end if;

  v_evento := nullif(trim(p_payload->>'evento'), '');
  v_evento_externo_id := nullif(trim(p_payload->>'evento_externo_id'), '');
  v_lead_externo_id := nullif(trim(p_payload->>'lead_externo_id'), '');
  v_sistema_origem := coalesce(nullif(trim(p_payload->>'sistema_origem'), ''), 'desconhecido');

  if v_evento not in (
    'conversa_iniciada',
    'lead_identificado',
    'lead_qualificado',
    'agendamento',
    'proposta',
    'venda',
    'desqualificado'
  ) then
    raise exception 'evento inválido: %', v_evento;
  end if;

  if v_evento_externo_id is null then
    raise exception 'evento_externo_id obrigatório';
  end if;

  if v_lead_externo_id is null then
    raise exception 'lead_externo_id obrigatório';
  end if;

  begin
    v_ocorrido_em := (p_payload->>'ocorrido_em')::timestamptz;
  exception when others then
    raise exception 'ocorrido_em deve ser ISO 8601 válido';
  end;

  insert into public.meta_hub_leads (
    cliente_id,
    lead_externo_id,
    sistema_origem,
    sessao_id,
    primeiro_evento_em,
    ultimo_evento_em,
    meta_lead_id,
    fbc,
    fbp,
    ctwa_clid,
    conta_anuncio,
    id_campanha,
    id_conjunto,
    id_anuncio,
    origem_atribuicao,
    confianca_atribuicao,
    pode_compartilhar_meta,
    pode_usar_publico
  )
  values (
    v_cliente.id,
    v_lead_externo_id,
    v_sistema_origem,
    nullif(trim(p_payload->>'sessao_id'), ''),
    v_ocorrido_em,
    v_ocorrido_em,
    nullif(trim(p_payload#>>'{atribuicao,meta_lead_id}'), ''),
    nullif(trim(p_payload#>>'{atribuicao,fbc}'), ''),
    nullif(trim(p_payload#>>'{atribuicao,fbp}'), ''),
    nullif(trim(p_payload#>>'{atribuicao,ctwa_clid}'), ''),
    coalesce(nullif(trim(p_payload#>>'{atribuicao,conta_anuncio}'), ''), v_cliente.conta_anuncio),
    nullif(trim(p_payload#>>'{atribuicao,id_campanha}'), ''),
    nullif(trim(p_payload#>>'{atribuicao,id_conjunto}'), ''),
    nullif(trim(p_payload#>>'{atribuicao,id_anuncio}'), ''),
    coalesce(nullif(trim(p_payload#>>'{atribuicao,origem_atribuicao}'), ''), 'desconhecida'),
    coalesce(nullif(trim(p_payload#>>'{atribuicao,confianca_atribuicao}'), ''), 'desconhecida'),
    coalesce((p_payload->>'pode_compartilhar_meta')::boolean, false),
    coalesce((p_payload->>'pode_usar_publico')::boolean, false)
  )
  on conflict (cliente_id, lead_externo_id)
  do update set
    sistema_origem = excluded.sistema_origem,
    sessao_id = coalesce(excluded.sessao_id, meta_hub_leads.sessao_id),
    primeiro_evento_em = least(
      coalesce(meta_hub_leads.primeiro_evento_em, excluded.primeiro_evento_em),
      excluded.primeiro_evento_em
    ),
    ultimo_evento_em = greatest(
      coalesce(meta_hub_leads.ultimo_evento_em, excluded.ultimo_evento_em),
      excluded.ultimo_evento_em
    ),
    meta_lead_id = coalesce(meta_hub_leads.meta_lead_id, excluded.meta_lead_id),
    fbc = coalesce(meta_hub_leads.fbc, excluded.fbc),
    fbp = coalesce(meta_hub_leads.fbp, excluded.fbp),
    ctwa_clid = coalesce(meta_hub_leads.ctwa_clid, excluded.ctwa_clid),
    conta_anuncio = coalesce(meta_hub_leads.conta_anuncio, excluded.conta_anuncio),
    id_campanha = coalesce(meta_hub_leads.id_campanha, excluded.id_campanha),
    id_conjunto = coalesce(meta_hub_leads.id_conjunto, excluded.id_conjunto),
    id_anuncio = coalesce(meta_hub_leads.id_anuncio, excluded.id_anuncio),
    origem_atribuicao = case
      when meta_hub_leads.origem_atribuicao = 'desconhecida'
        then excluded.origem_atribuicao
      else meta_hub_leads.origem_atribuicao
    end,
    confianca_atribuicao = case
      when meta_hub_leads.confianca_atribuicao = 'desconhecida'
        then excluded.confianca_atribuicao
      else meta_hub_leads.confianca_atribuicao
    end,
    pode_compartilhar_meta = case
      when p_payload ? 'pode_compartilhar_meta'
        then (p_payload->>'pode_compartilhar_meta')::boolean
      else meta_hub_leads.pode_compartilhar_meta
    end,
    pode_usar_publico = case
      when p_payload ? 'pode_usar_publico'
        then (p_payload->>'pode_usar_publico')::boolean
      else meta_hub_leads.pode_usar_publico
    end,
    atualizado_em = now()
  returning * into v_lead;

  -- O HUB armazena apenas hashes de identificadores de matching.
  v_email := lower(nullif(trim(p_payload#>>'{identificadores,email}'), ''));
  if v_email is not null then
    v_hash := public.meta_hub_sha256(v_email);
    insert into public.meta_hub_identificadores (lead_id, tipo, valor_hash)
    values (v_lead.id, 'em', v_hash)
    on conflict do nothing;
  end if;

  -- O integrador deve enviar telefone com código do país. Aqui removemos apenas caracteres não numéricos.
  v_telefone := regexp_replace(
    coalesce(p_payload#>>'{identificadores,telefone}', ''),
    '[^0-9]',
    '',
    'g'
  );
  if v_telefone <> '' then
    v_hash := public.meta_hub_sha256(v_telefone);
    insert into public.meta_hub_identificadores (lead_id, tipo, valor_hash)
    values (v_lead.id, 'ph', v_hash)
    on conflict do nothing;
  end if;

  v_external_id := coalesce(
    nullif(trim(p_payload#>>'{identificadores,external_id}'), ''),
    v_lead_externo_id
  );
  if v_external_id is not null then
    v_hash := public.meta_hub_sha256(v_external_id);
    insert into public.meta_hub_identificadores (lead_id, tipo, valor_hash)
    values (v_lead.id, 'external_id', v_hash)
    on conflict do nothing;
  end if;

  -- Idempotência: retry do sistema de origem não cria novo evento lógico.
  insert into public.meta_hub_eventos (
    cliente_id,
    lead_id,
    evento_externo_id,
    evento,
    ocorrido_em,
    score_qualificacao,
    valor,
    moeda,
    metadata
  )
  values (
    v_cliente.id,
    v_lead.id,
    v_evento_externo_id,
    v_evento,
    v_ocorrido_em,
    nullif(p_payload->>'score_qualificacao', '')::numeric,
    nullif(p_payload->>'valor', '')::numeric,
    coalesce(nullif(upper(trim(p_payload->>'moeda')), ''), 'BRL'),
    coalesce(p_payload->'metadata', '{}'::jsonb)
  )
  on conflict (cliente_id, evento_externo_id)
  do update set evento_externo_id = meta_hub_eventos.evento_externo_id
  returning id into v_evento_id;

  -- Só cria feedback quando cliente, lead e mapa permitem.
  select m.evento_meta, m.habilitado
    into v_mapa
  from public.meta_hub_mapa_eventos_meta m
  where m.cliente_id = v_cliente.id
    and m.evento_interno = v_evento
  limit 1;

  if v_cliente.enviar_feedback_meta
     and v_lead.pode_compartilhar_meta
     and coalesce(v_mapa.habilitado, false)
  then
    select coalesce(
      jsonb_object_agg(tipo, valores),
      '{}'::jsonb
    )
    into v_user_data
    from (
      select tipo, jsonb_agg(valor_hash order by valor_hash) as valores
      from public.meta_hub_identificadores
      where lead_id = v_lead.id
      group by tipo
    ) x;

    v_user_data := v_user_data || jsonb_strip_nulls(jsonb_build_object(
      'lead_id', v_lead.meta_lead_id,
      'fbc', v_lead.fbc,
      'fbp', v_lead.fbp
    ));

    v_custom_data := jsonb_strip_nulls(jsonb_build_object(
      'meta_ads_growth_evento', v_evento,
      'score_qualificacao', nullif(p_payload->>'score_qualificacao', '')::numeric,
      'value', nullif(p_payload->>'valor', '')::numeric,
      'currency', coalesce(nullif(upper(trim(p_payload->>'moeda')), ''), 'BRL')
    ));

    v_event_id := v_cliente.chave_cliente || '|' || v_evento_externo_id;

    v_payload_meta := jsonb_build_object(
      'data',
      jsonb_build_array(
        jsonb_strip_nulls(jsonb_build_object(
          'event_name', v_mapa.evento_meta,
          'event_time', floor(extract(epoch from v_ocorrido_em))::bigint,
          'event_id', v_event_id,
          'action_source', coalesce(
            nullif(trim(p_payload->>'action_source'), ''),
            v_cliente.action_source_padrao,
            'other'
          ),
          'user_data', v_user_data,
          'custom_data', v_custom_data
        ))
      )
    );

    insert into public.meta_hub_fila_capi (
      cliente_id,
      lead_id,
      evento_id,
      event_id,
      evento_meta,
      payload,
      status,
      proxima_tentativa_em
    )
    values (
      v_cliente.id,
      v_lead.id,
      v_evento_id,
      v_event_id,
      v_mapa.evento_meta,
      v_payload_meta,
      'pendente',
      now()
    )
    on conflict (event_id) do nothing;

    get diagnostics v_linhas = row_count;
    v_fila_criada := v_linhas > 0;
  end if;

  -- Atualiza a fila do público correspondente, quando houver público configurado.
  if v_lead.pode_usar_publico then
    v_publico_tipo := case v_evento
      when 'lead_qualificado' then 'qualificados'
      when 'agendamento' then 'agendados'
      when 'venda' then 'clientes'
      when 'desqualificado' then 'desqualificados'
      else null
    end;

    if v_publico_tipo is not null then
      select p.id
        into v_publico_id
      from public.meta_hub_publicos p
      where p.cliente_id = v_cliente.id
        and p.tipo = v_publico_tipo
        and p.ativo = true
      limit 1;

      if v_publico_id is not null then
        insert into public.meta_hub_publico_membros (
          publico_id,
          lead_id,
          status,
          atualizado_em
        )
        values (
          v_publico_id,
          v_lead.id,
          'pendente',
          now()
        )
        on conflict (publico_id, lead_id)
        do update set
          status = case
            when meta_hub_publico_membros.status = 'adicionado'
              then 'adicionado'
            else 'pendente'
          end,
          atualizado_em = now();
      end if;
    end if;
  end if;

  return jsonb_build_object(
    'ok', true,
    'cliente', v_cliente.chave_cliente,
    'lead_id', v_lead.id,
    'lead_externo_id', v_lead.lead_externo_id,
    'evento_id', v_evento_id,
    'evento', v_evento,
    'fila_capi_criada', v_fila_criada,
    'pode_compartilhar_meta', v_lead.pode_compartilhar_meta,
    'pode_usar_publico', v_lead.pode_usar_publico,
    'modo_teste', coalesce((p_payload->>'modo_teste')::boolean, false)
  );
end;
$$;

comment on function public.meta_hub_receber_evento(jsonb) is
'Recebe evento canônico do HUB, faz upsert do lead, guarda hashes, registra funil e cria outbox CAPI quando permitido.';
