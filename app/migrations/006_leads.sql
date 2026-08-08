create table if not exists public.leads (
    id uuid primary key default gen_random_uuid(),
    client_slug text not null,
    conversation_id uuid references public.conversations(id) on delete set null,
    session_id text,
    email text,
    phone text,
    interest text,
    fields jsonb not null default '{}'::jsonb,
    source text not null default 'chatbot',
    first_seen_at timestamptz not null default now(),
    last_seen_at timestamptz not null default now(),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists leads_client_slug_created_at_idx
    on public.leads (client_slug, created_at desc);

create index if not exists leads_client_slug_email_idx
    on public.leads (client_slug, email);

create index if not exists leads_client_slug_phone_idx
    on public.leads (client_slug, phone);

create or replace function public.update_leads_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists trg_leads_updated_at on public.leads;
create trigger trg_leads_updated_at
before update on public.leads
for each row
execute function public.update_leads_updated_at();
