from app.db import supabase
import hashlib


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def run():
    print("Starting API key hash migration...")

    clients = supabase.table("clients").select("*").execute().data

    if not clients:
        print("No clients found.")
        return

    for client in clients:
        api_key = client.get("api_key")

        if not api_key:
            print(f"Skipping client {client['id']} (no api_key)")
            continue

        hashed = hash_key(api_key)

        supabase.table("clients").update({
            "api_key_hash": hashed
        }).eq("id", client["id"]).execute()

        print(f"Updated client {client['id']}")

    print("Migration completed.")


if __name__ == "__main__":
    run()
