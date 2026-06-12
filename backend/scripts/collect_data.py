"""Collect raw dataset artifacts."""

from backend.app.services.dataset_service import get_dataset_service


def main() -> None:
    result = get_dataset_service().collect_data()
    print(f"collect_data completed: {result}")


if __name__ == "__main__":
    main()

