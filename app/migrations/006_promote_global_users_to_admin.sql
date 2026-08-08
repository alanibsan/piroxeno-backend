update app_users
set role = 'admin'
where client_slug is null
  and role = 'user';

update app_users
set role = 'admin',
    client_slug = null,
    is_active = true
where lower(email) = 'alan@piroxeno.com';
