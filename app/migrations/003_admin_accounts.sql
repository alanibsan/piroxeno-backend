create table if not exists public.app_users (
    id uuid primary key default gen_random_uuid(),
    email text not null unique,
    role text not null check (role in ('admin', 'user')),
    client_slug text,
    is_active boolean not null default true,
    created_at timestamptz not null default now()
);

create index if not exists app_users_client_slug_idx
    on public.app_users (client_slug);

-- Suggested model:
-- admin: can manage all clients, domains, licenses and users.
-- user: can only view the client_slug assigned to their account.
--
-- When you connect this to Supabase Auth, keep auth.users as the identity
-- source and use this table for app-specific role/client permissions.
