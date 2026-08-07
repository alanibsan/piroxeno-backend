import argparse

from app.db import get_supabase
from app.services.auth_service import hash_password


def main():
    parser = argparse.ArgumentParser(description="Create or update a Piroxeno admin user.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--role", choices=["admin", "user"], default="admin")
    parser.add_argument("--client-slug", default=None)
    args = parser.parse_args()

    if len(args.password) < 10:
        raise SystemExit("Password must be at least 10 characters long.")

    supabase = get_supabase()
    if supabase is None:
        raise SystemExit("Supabase is not configured.")

    payload = {
        "email": args.email.lower().strip(),
        "role": args.role,
        "client_slug": args.client_slug,
        "is_active": True,
        "password_hash": hash_password(args.password),
    }
    response = (
        supabase.table("app_users")
        .upsert(payload, on_conflict="email")
        .execute()
    )
    user = response.data[0] if response.data else payload
    print(f"Ready: {user['email']} ({user['role']})")


if __name__ == "__main__":
    main()
