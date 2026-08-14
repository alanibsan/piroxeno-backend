create table if not exists public.website_events (
    id uuid primary key default gen_random_uuid(),
    site text not null default 'piroxeno',
    event_name text not null default 'page_view',
    path text,
    url text,
    referrer text,
    title text,
    language text,
    timezone text,
    screen_width int,
    screen_height int,
    visitor_id text,
    session_id text,
    ip_hash text,
    country text,
    region text,
    city text,
    user_agent text,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists website_events_created_at_idx
    on public.website_events (created_at desc);

create index if not exists website_events_site_created_at_idx
    on public.website_events (site, created_at desc);

create index if not exists website_events_path_created_at_idx
    on public.website_events (path, created_at desc);

create or replace view public.website_traffic_daily as
select
    date_trunc('day', created_at)::date as day,
    site,
    path,
    country,
    count(*) as page_views,
    count(distinct visitor_id) filter (where visitor_id is not null) as unique_visitors,
    count(distinct session_id) filter (where session_id is not null) as sessions
from public.website_events
group by 1, 2, 3, 4;

create or replace view public.website_referrers_daily as
select
    date_trunc('day', created_at)::date as day,
    site,
    coalesce(nullif(referrer, ''), 'direct') as referrer,
    count(*) as page_views,
    count(distinct visitor_id) filter (where visitor_id is not null) as unique_visitors
from public.website_events
group by 1, 2, 3;
