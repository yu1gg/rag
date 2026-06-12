"""Clean collected documents."""

from backend.app.services.dataset_service import get_dataset_service


def main() -> None:
    result = get_dataset_service().clean_data()
    print(f"clean_data completed: {result}")


if __name__ == "__main__":
    main()

