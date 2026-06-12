"""Automatic evaluation helpers."""


class AutoEvaluator:
    def evaluate_rouge_l(self, predictions: list[str], references: list[str]) -> dict:
        try:
            from rouge_score import rouge_scorer
        except ImportError:
            return {
                "rouge_l_precision": 0,
                "rouge_l_recall": 0,
                "rouge_l_f1": 0,
                "note": "rouge-score 未安装",
            }
        scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
        p_scores, r_scores, f_scores = [], [], []
        for pred, ref in zip(predictions, references):
            result = scorer.score(ref, pred)
            p_scores.append(result["rougeL"].precision)
            r_scores.append(result["rougeL"].recall)
            f_scores.append(result["rougeL"].fmeasure)
        return {
            "rouge_l_precision": round(sum(p_scores) / len(p_scores), 4),
            "rouge_l_recall": round(sum(r_scores) / len(r_scores), 4),
            "rouge_l_f1": round(sum(f_scores) / len(f_scores), 4),
        }

    def evaluate_bleu(self, predictions: list[str], references: list[str]) -> dict:
        try:
            import sacrebleu
        except ImportError:
            return {"bleu": 0, "note": "sacrebleu 未安装"}

        refs = [[reference] for reference in references]
        score = sacrebleu.corpus_bleu(predictions, refs)
        return {
            "bleu": round(score.score, 2),
            "bleu_bp": round(score.bp, 4),
            "bleu_1gram": round(score.counts[0] / max(score.totals[0], 1), 4) if score.counts else 0,
        }

    def evaluate_bert_score(self, predictions: list[str], references: list[str], lang: str = "zh") -> dict:
        try:
            from bert_score import score as bert_score_fn
        except ImportError:
            return {
                "bert_precision": 0,
                "bert_recall": 0,
                "bert_f1": 0,
                "note": "bert-score 未安装",
            }

        precision, recall, f1 = bert_score_fn(predictions, references, lang=lang, verbose=False)
        return {
            "bert_precision": round(precision.mean().item(), 4),
            "bert_recall": round(recall.mean().item(), 4),
            "bert_f1": round(f1.mean().item(), 4),
        }

    def evaluate_hit_at_k(self, retrieved: list[list[str]], relevant: list[list[str]], k: int = 5) -> float:
        if not retrieved or not relevant:
            return 0.0
        hits = 0
        for retrieved_list, relevant_list in zip(retrieved, relevant):
            if set(retrieved_list[:k]) & set(relevant_list):
                hits += 1
        return round(hits / len(retrieved), 4)

    def run_full_evaluation(self, test_data: list[dict]) -> dict:
        if not test_data:
            return {"error": "无评估数据"}

        predictions = [item["prediction"] for item in test_data]
        references = [item["reference"] for item in test_data]
        results = {
            "rouge_l": self.evaluate_rouge_l(predictions, references),
            "bleu": self.evaluate_bleu(predictions, references),
        }
        try:
            results["bert_score"] = self.evaluate_bert_score(predictions, references)
        except Exception as exc:
            results["bert_score"] = {"error": str(exc)}

        if all("retrieved_ids" in item and "relevant_ids" in item for item in test_data):
            retrieved = [item["retrieved_ids"] for item in test_data]
            relevant = [item["relevant_ids"] for item in test_data]
            for k_value in [1, 3, 5]:
                results[f"hit@{k_value}"] = self.evaluate_hit_at_k(retrieved, relevant, k=k_value)
        return results


def format_report(metrics: dict) -> str:
    lines = ["=" * 50, "  自动评估报告", "=" * 50, ""]

    if "rouge_l" in metrics:
        rouge = metrics["rouge_l"]
        lines.append("[ROUGE-L]")
        lines.append(f"  Precision: {rouge.get('rouge_l_precision', 'N/A')}")
        lines.append(f"  Recall:    {rouge.get('rouge_l_recall', 'N/A')}")
        lines.append(f"  F1:        {rouge.get('rouge_l_f1', 'N/A')}")
        lines.append("")

    if "bleu" in metrics:
        bleu = metrics["bleu"]
        lines.append("[BLEU]")
        lines.append(f"  BLEU:      {bleu.get('bleu', 'N/A')}")
        lines.append(f"  BP:        {bleu.get('bleu_bp', 'N/A')}")
        lines.append("")

    if "bert_score" in metrics:
        bert_score = metrics["bert_score"]
        if "error" not in bert_score:
            lines.append("[BERTScore]")
            lines.append(f"  Precision: {bert_score.get('bert_precision', 'N/A')}")
            lines.append(f"  Recall:    {bert_score.get('bert_recall', 'N/A')}")
            lines.append(f"  F1:        {bert_score.get('bert_f1', 'N/A')}")
            lines.append("")

    for k_value in [1, 3, 5]:
        key = f"hit@{k_value}"
        if key in metrics:
            lines.append(f"[Hit@{k_value}]: {metrics[key]}")

    return "\n".join(lines)

