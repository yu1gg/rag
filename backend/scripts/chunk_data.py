"""Chunk cleaned documents."""

from backend.app.services.dataset_service import get_dataset_service


def main() -> None:
    result = get_dataset_service().chunk_data()
    print(f"chunk_data completed: {result}")


if __name__ == "__main__":
    main()

