alter table public.app_users
    add column if not exists password_hash text,
    add column if not exists last_login_at timestamptz,
    add column if not exists updated_at timestamptz not null default now();

create or replace function update_app_users_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists trg_app_users_updated_at on public.app_users;
create trigger trg_app_users_updated_at
before update on public.app_users
for each row
execute function update_app_users_updated_at();
