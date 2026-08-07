create table if not exists public.conversations (
    id uuid primary key default gen_random_uuid(),
    client_slug text not null,
    session_id text not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (client_slug, session_id)
);

create table if not exists public.messages (
    id uuid primary key default gen_random_uuid(),
    conversation_id uuid not null references public.conversations(id) on delete cascade,
    client_slug text not null,
    role text not null check (role in ('user', 'assistant', 'system')),
    content text not null,
    tokens_prompt integer,
    tokens_completion integer,
    total_tokens integer,
    duration_ms numeric,
    created_at timestamptz not null default now()
);

create index if not exists conversations_client_slug_idx
    on public.conversations (client_slug);

create index if not exists conversations_client_session_idx
    on public.conversations (client_slug, session_id);

create index if not exists messages_conversation_created_at_idx
    on public.messages (conversation_id, created_at);

create index if not exists messages_client_slug_created_at_idx
    on public.messages (client_slug, created_at);

create or replace function public.set_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists conversations_set_updated_at on public.conversations;

create trigger conversations_set_updated_at
before update on public.conversations
for each row
execute function public.set_updated_at();
