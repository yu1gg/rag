"""Run evaluation reports."""

from backend.app.services.evaluation_service import get_evaluation_service


def main() -> None:
    result = get_evaluation_service().run_evaluation()
    print(
        "run_evaluation completed: "
        f"auto_report_len={len(result['auto_report'])}, "
        f"human_score_count={result['human_score_count']}"
    )


if __name__ == "__main__":
    main()
