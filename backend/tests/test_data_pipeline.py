"""Tests for migrated data and evaluation helpers."""

from pathlib import Path

from backend.app.rag.data.chunker import Chunker
from backend.app.rag.data.cleaner import Deduplicator, TextCleaner
from backend.app.rag.data.collector import CourseMaterialCollector, NewsCollector
from backend.app.rag.data.models import Document
from backend.app.rag.evaluation.auto_eval import AutoEvaluator, format_report
from backend.app.rag.evaluation.human_eval import HumanEvaluator, HumanScore


def test_news_collector_falls_back_when_online_fetch_fails(monkeypatch):
    def fake_get(*args, **kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr("backend.app.rag.data.collector.requests.get", fake_get)
    collector = NewsCollector(max_articles=3)
    docs = collector.collect()

    assert len(docs) == 3
    assert all(doc.source == "news" for doc in docs)


def test_course_material_collector_generates_defaults_for_missing_dir(tmp_path: Path):
    collector = CourseMaterialCollector(tmp_path / "missing-materials")
    docs = collector.collect()

    assert docs
    assert all(doc.source == "course" for doc in docs)


def test_cleaner_and_deduplicator_pipeline():
    docs = [
        Document(
            id="doc1",
            title="A",
            content="<p>你好  世界，这是一个足够长的测试文本，用来验证清洗与去重流程正常工作。</p>",
            source="course",
        ),
        Document(
            id="doc2",
            title="B",
            content="<p>你好  世界，这是一个足够长的测试文本，用来验证清洗与去重流程正常工作。</p>",
            source="course",
        ),
        Document(id="doc3", title="C", content="短", source="course"),
    ]
    cleaner = TextCleaner()
    dedup = Deduplicator()

    cleaned = cleaner.clean_documents(docs)
    unique_docs = dedup.deduplicate(cleaned)
    filtered = dedup.filter_short(unique_docs, min_length=4)

    assert len(cleaned) == 2
    assert len(unique_docs) == 1
    assert filtered[0].content.startswith("你好 世界")
    assert "<p>" not in filtered[0].content
    assert "  " not in filtered[0].content


def test_chunker_produces_chunks():
    docs = [
        Document(
            id="doc1",
            title="title",
            content="\n\n".join([f"段落 {idx} " + ("内容" * 40) for idx in range(6)]),
            source="course",
        )
    ]
    chunker = Chunker(chunk_size=80, overlap=20)
    chunks = chunker.chunk_all(docs)

    assert chunks
    assert chunks[0].chunk_id.startswith("chunk_")
    assert all(chunk.doc_id == "doc1" for chunk in chunks)


def test_auto_evaluator_and_report():
    evaluator = AutoEvaluator()
    hit = evaluator.evaluate_hit_at_k(
        retrieved=[["a", "b"], ["c", "d"]],
        relevant=[["b"], ["x"]],
        k=2,
    )
    report = format_report(
        {
            "rouge_l": {"rouge_l_precision": 0.1, "rouge_l_recall": 0.2, "rouge_l_f1": 0.3},
            "bleu": {"bleu": 11.2, "bleu_bp": 0.9},
            "hit@1": 0.5,
            "hit@3": 1.0,
        }
    )

    assert hit == 0.5
    assert "自动评估报告" in report
    assert "[Hit@3]" in report


def test_human_evaluator_report(tmp_path: Path):
    output_path = tmp_path / "human_scores.json"
    evaluator = HumanEvaluator(output_path)
    evaluator.record(
        HumanScore(
            question_id="eval_001",
            question="什么是RAG？",
            answer="RAG 是检索增强生成。",
            correctness=5,
            completeness=4,
            fluency=5,
            case_type="success",
            analysis="回答准确。",
        )
    )
    report = evaluator.generate_report()

    assert "人工评估报告" in report
    assert "success" in report
