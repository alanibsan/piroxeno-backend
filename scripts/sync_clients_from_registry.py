from app.services.admin_service import sync_clients_from_registry


def main():
    result = sync_clients_from_registry()
    print(f"Synced {result['synced_count']} clients")
    for client_slug in result["clients"]:
        print(client_slug)


if __name__ == "__main__":
    main()
