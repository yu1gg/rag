"""Build FAISS index from chunks."""

from backend.app.services.index_service import get_index_service


def main() -> None:
    result = get_index_service().build_index()
    print(f"build_index completed: {result}")


if __name__ == "__main__":
    main()

