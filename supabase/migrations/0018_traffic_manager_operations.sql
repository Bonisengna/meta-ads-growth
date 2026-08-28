-- Operational Meta Ads fields for pacing, creatives and page/video metrics.
-- Existing tables keep their RLS policies and historical rows.

alter table public.campaigns
    add column if not exists buying_type text,
    add column if not exists daily_budget numeric(14,2),
    add column if not exists lifetime_budget numeric(14,2),
    add column if not exists budget_remaining numeric(14,2),
    add column if not exists start_time timestamptz,
    add column if not exists stop_time timestamptz;

alter table public.campaigns
    drop constraint if exists campaigns_daily_budget_check,
    add constraint campaigns_daily_budget_check
        check (daily_budget is null or daily_budget >= 0),
    drop constraint if exists campaigns_lifetime_budget_check,
    add constraint campaigns_lifetime_budget_check
        check (lifetime_budget is null or lifetime_budget >= 0),
    drop constraint if exists campaigns_budget_remaining_check,
    add constraint campaigns_budget_remaining_check
        check (budget_remaining is null or budget_remaining >= 0);

alter table public.adsets
    add column if not exists budget_remaining numeric(14,2),
    add column if not exists start_time timestamptz,
    add column if not exists end_time timestamptz;

alter table public.adsets
    drop constraint if exists adsets_budget_remaining_check,
    add constraint adsets_budget_remaining_check
        check (budget_remaining is null or budget_remaining >= 0);

alter table public.ads
    add column if not exists creative_name text,
    add column if not exists creative_type text,
    add column if not exists thumbnail_url text,
    add column if not exists image_url text,
    add column if not exists video_id text,
    add column if not exists video_duration_seconds numeric(12,3),
    add column if not exists primary_text text,
    add column if not exists headline text,
    add column if not exists call_to_action_type text,
    add column if not exists destination_url text;

alter table public.ads
    drop constraint if exists ads_video_duration_seconds_check,
    add constraint ads_video_duration_seconds_check
        check (video_duration_seconds is null or video_duration_seconds >= 0);

do $$
declare
    metric_table text;
begin
    foreach metric_table in array array[
        'campaign_metrics', 'adset_metrics', 'ad_metrics'
    ]
    loop
        execute format(
            'alter table public.%I
                add column if not exists landing_page_views bigint not null default 0,
                add column if not exists video_views_3s bigint not null default 0,
                add column if not exists video_plays bigint not null default 0,
                add column if not exists video_p25 bigint not null default 0,
                add column if not exists video_p50 bigint not null default 0,
                add column if not exists video_p75 bigint not null default 0,
                add column if not exists video_p95 bigint not null default 0,
                add column if not exists thruplays bigint not null default 0',
            metric_table
        );
        execute format(
            'alter table public.%I
                drop constraint if exists %I,
                add constraint %I check (
                    landing_page_views >= 0 and video_views_3s >= 0 and
                    video_plays >= 0 and video_p25 >= 0 and video_p50 >= 0 and
                    video_p75 >= 0 and video_p95 >= 0 and thruplays >= 0
                )',
            metric_table,
            metric_table || '_operational_metrics_check',
            metric_table || '_operational_metrics_check'
        );
    end loop;
end $$;

comment on column public.campaign_metrics.landing_page_views is
    'Meta action landing_page_view collected daily.';
comment on column public.campaign_metrics.video_views_3s is
    'Meta video_3_sec_watched_actions collected daily.';
comment on column public.ads.thumbnail_url is
    'Remote Meta creative thumbnail. The URL may expire and is refreshed by sync.';
