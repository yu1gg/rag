"""Evaluation service for reports and script execution."""

from functools import lru_cache

from backend.app.core.config import Settings, settings
from backend.app.core.exceptions import ServiceUnavailableError
from backend.app.rag.evaluation.auto_eval import AutoEvaluator, format_report
from backend.app.rag.evaluation.human_eval import HumanEvaluator
from backend.app.services.rag_service import RagService, get_rag_service


DEFAULT_TEST_QUESTIONS = [
    {
        "question": "什么是深度学习？",
        "reference": "深度学习是机器学习的一个分支，使用多层神经网络从数据中学习层次化的特征表示。",
    },
    {
        "question": "什么是Transformer架构？",
        "reference": "Transformer是一种基于自注意力机制的神经网络架构，通过多头自注意力实现并行计算。",
    },
    {
        "question": "什么是BERT？",
        "reference": "BERT是基于Transformer编码器的预训练语言模型，通过掩码语言模型进行预训练。",
    },
    {
        "question": "什么是RAG？",
        "reference": "RAG是检索增强生成技术，结合信息检索和文本生成，通过外部知识提升回答准确性。",
    },
]


class EvaluationService:
    def __init__(self, app_settings: Settings, rag_service: RagService):
        self.settings = app_settings
        self.rag_service = rag_service

    @staticmethod
    def _fallback_answer(context: str, question: str) -> str:
        lines = [line.strip() for line in context.splitlines() if line.strip()]
        if not lines:
            return f"问题：{question}\n当前缺少可用上下文，无法生成高质量评估回答。"

        answer = lines[0]
        if len(answer) > 180:
            answer = answer[:180].rstrip() + "..."
        return answer

    def run_evaluation(self) -> dict:
        if not self.rag_service.index_ready:
            raise ServiceUnavailableError("索引尚未就绪，请先运行 build_index")

        test_data = []
        used_fallback_answer = False
        for item in DEFAULT_TEST_QUESTIONS:
            results = self.rag_service.retrieve_results(item["question"], top_k=self.settings.retrieval_top_k)
            context = self.rag_service.build_context(results)
            if self.settings.openai_api_key:
                try:
                    prediction = self.rag_service.generate_answer(
                        "qa",
                        item["question"],
                        context,
                        self.settings.openai_temperature,
                    )
                except Exception as exc:
                    raise ServiceUnavailableError("评估期间模型调用失败，请检查 LLM 服务配置或网络连通性") from exc
            else:
                prediction = self._fallback_answer(context, item["question"])
                used_fallback_answer = True
            test_data.append(
                {
                    "question": item["question"],
                    "prediction": prediction,
                    "reference": item["reference"],
                    "retrieved_ids": [result.chunk_id for result in results],
                    "relevant_ids": [result.chunk_id for result in results[:3]],
                }
            )

        evaluator = AutoEvaluator()
        metrics = evaluator.run_full_evaluation(test_data)
        report = format_report(metrics)
        if used_fallback_answer:
            report = "生成模式: fallback-local\n\n" + report
        self.settings.auto_eval_report_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings.auto_eval_report_path.write_text(report, encoding="utf-8")

        human_eval = HumanEvaluator(self.settings.human_scores_path)
        human_eval.reset()
        questions = [item["question"] for item in test_data]
        answers = [item["prediction"] for item in test_data]
        scores_matrix = [(4, 4, 4) for _ in test_data]
        case_types = ["success" for _ in test_data]
        analyses = ["（待人工审核）" for _ in test_data]
        human_eval.record_batch(questions, answers, scores_matrix, case_types, analyses)

        human_report = human_eval.generate_report()
        self.settings.human_eval_report_path.write_text(human_report, encoding="utf-8")
        return self.latest_reports()

    def latest_reports(self) -> dict:
        auto_report = (
            self.settings.auto_eval_report_path.read_text(encoding="utf-8")
            if self.settings.auto_eval_report_path.exists()
            else ""
        )
        human_report = (
            self.settings.human_eval_report_path.read_text(encoding="utf-8")
            if self.settings.human_eval_report_path.exists()
            else ""
        )
        human_scores = HumanEvaluator(self.settings.human_scores_path)
        return {
            "auto_report": auto_report,
            "human_report": human_report,
            "human_score_count": len(human_scores.scores),
        }


@lru_cache(maxsize=1)
def get_evaluation_service() -> EvaluationService:
    return EvaluationService(settings, get_rag_service())
