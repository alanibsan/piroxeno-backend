from app.config import settings

supabase = None


def get_supabase():
    global supabase

    if supabase is not None:
        return supabase

    if not settings.supabase_url or not settings.supabase_service_role_key:
        return None

    from supabase import create_client

    supabase = create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )

    return supabase
