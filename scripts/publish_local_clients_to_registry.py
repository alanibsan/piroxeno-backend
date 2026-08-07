from app.services.admin_service import publish_local_clients_to_registry


def main():
    result = publish_local_clients_to_registry()
    print(f"Published {result['published_count']} clients")
    for client_slug in result["clients"]:
        print(client_slug)


if __name__ == "__main__":
    main()
