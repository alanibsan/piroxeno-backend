create table if not exists public.client_registry (
    client_slug text primary key,
    config jsonb not null default '{}'::jsonb,
    prompt text not null default '',
    embed text not null default '',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create or replace function public.update_client_registry_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists trg_client_registry_updated_at on public.client_registry;
create trigger trg_client_registry_updated_at
before update on public.client_registry
for each row
execute function public.update_client_registry_updated_at();
