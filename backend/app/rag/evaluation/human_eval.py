"""Human evaluation persistence and reporting."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class HumanScore:
    question_id: str
    question: str
    answer: str
    correctness: int
    completeness: int
    fluency: int
    case_type: str = ""
    analysis: str = ""


class HumanEvaluator:
    def __init__(self, output_path: str | Path):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.scores: list[HumanScore] = []
        self._load()

    def _load(self) -> None:
        if self.output_path.exists():
            data = json.loads(self.output_path.read_text(encoding="utf-8"))
            self.scores = [HumanScore(**item) for item in data]

    def _save(self) -> None:
        data = [asdict(score) for score in self.scores]
        self.output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def reset(self) -> None:
        self.scores = []
        self._save()

    def record(self, score: HumanScore) -> None:
        self.scores.append(score)
        self._save()

    def record_batch(
        self,
        questions: list[str],
        answers: list[str],
        scores_matrix: list[tuple[int, int, int]],
        case_types: list[str] | None = None,
        analyses: list[str] | None = None,
    ) -> None:
        for idx, (question, answer) in enumerate(zip(questions, answers)):
            correctness, completeness, fluency = scores_matrix[idx]
            case_type = case_types[idx] if case_types else ""
            analysis = analyses[idx] if analyses else ""
            self.record(
                HumanScore(
                    question_id=f"eval_{len(self.scores) + 1:03d}",
                    question=question,
                    answer=answer,
                    correctness=correctness,
                    completeness=completeness,
                    fluency=fluency,
                    case_type=case_type,
                    analysis=analysis,
                )
            )

    def statistics(self) -> dict:
        if not self.scores:
            return {"error": "无评分记录"}
        total = len(self.scores)
        avg_correctness = sum(score.correctness for score in self.scores) / total
        avg_completeness = sum(score.completeness for score in self.scores) / total
        avg_fluency = sum(score.fluency for score in self.scores) / total

        by_type: dict[str, dict] = {}
        for score in self.scores:
            case_type = score.case_type or "未分类"
            if case_type not in by_type:
                by_type[case_type] = {"count": 0, "avg_c": 0, "avg_cp": 0, "avg_f": 0}
            by_type[case_type]["count"] += 1
            by_type[case_type]["avg_c"] += score.correctness
            by_type[case_type]["avg_cp"] += score.completeness
            by_type[case_type]["avg_f"] += score.fluency

        for case_type, data in by_type.items():
            count = data["count"]
            data["avg_c"] = round(data["avg_c"] / count, 2)
            data["avg_cp"] = round(data["avg_cp"] / count, 2)
            data["avg_f"] = round(data["avg_f"] / count, 2)

        return {
            "total_samples": total,
            "avg_correctness": round(avg_correctness, 2),
            "avg_completeness": round(avg_completeness, 2),
            "avg_fluency": round(avg_fluency, 2),
            "by_case_type": by_type,
        }

    def generate_report(self) -> str:
        stats = self.statistics()
        lines = ["=" * 50, "  人工评估报告", "=" * 50, ""]
        if "error" in stats:
            lines.append(stats["error"])
            return "\n".join(lines)

        lines.append(f"评估样本数: {stats['total_samples']}")
        lines.append(f"平均正确性: {stats['avg_correctness']}/5")
        lines.append(f"平均完整性: {stats['avg_completeness']}/5")
        lines.append(f"平均流畅性: {stats['avg_fluency']}/5")
        lines.append("")
        if stats["by_case_type"]:
            lines.append("按案例类型统计:")
            for case_type, data in stats["by_case_type"].items():
                lines.append(
                    f"  [{case_type}] 数量={data['count']}, 正确性={data['avg_c']}, "
                    f"完整性={data['avg_cp']}, 流畅性={data['avg_f']}"
                )
        lines.append("")
        lines.append("详细记录:")
        for score in self.scores:
            lines.append(f"  [{score.question_id}] {score.question[:50]}...")
            lines.append(
                f"    正确性={score.correctness} 完整性={score.completeness} "
                f"流畅性={score.fluency} 类型={score.case_type}"
            )
            if score.analysis:
                lines.append(f"    分析: {score.analysis[:100]}")
        return "\n".join(lines)
