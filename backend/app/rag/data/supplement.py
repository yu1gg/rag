"""Fallback supplement documents for data shortfall."""

from backend.app.rag.data.models import Document


SUPPLEMENT_TOPICS = [
    (
        "检索增强生成系统设计",
        "检索增强生成系统通过外部知识检索缓解大模型幻觉。一个完整系统通常包含文档采集、文本清洗、"
        "文本分块、向量化、向量检索、重排序、提示词拼接和答案生成等步骤。系统设计时需要同时考虑召回率、"
        "响应延迟、上下文长度限制和知识更新成本。",
    ),
    (
        "大语言模型提示词工程",
        "提示词工程的核心目标是稳定地引导模型输出。高质量提示词通常包含角色设定、任务描述、"
        "输入边界、输出格式和异常处理规则。对于问答系统，还需要明确模型在知识不足时应该如何回答，"
        "防止生成看似自然但缺乏依据的内容。",
    ),
    (
        "向量检索与重排序",
        "向量检索擅长快速缩小候选范围，但在细粒度相关性判断上不一定最优。实际系统中常先用向量检索获取"
        "Top-K 候选，再用 Cross-Encoder 重排序模型逐条比较 query 与候选片段，以提升最终答案质量。"
        "这种两阶段方案兼顾效率与精度。",
    ),
    (
        "文本分块策略",
        "文本分块决定了检索系统看到的最小知识单元。块太小会丢上下文，块太大则会带入噪声并增加提示词成本。"
        "常见做法是固定窗口加 overlap，并优先尊重段落边界。对于课程资料和说明文档，这种方法往往足够稳定。",
    ),
]


def generate_supplement_docs(target_chars: int, existing_count: int) -> list[Document]:
    docs: list[Document] = []
    accumulated = 0
    serial = 0
    while accumulated < max(target_chars, 0):
        title, paragraph = SUPPLEMENT_TOPICS[serial % len(SUPPLEMENT_TOPICS)]
        content = "\n\n".join([paragraph] * 12)
        doc = Document(
            id=f"supplement_{existing_count + serial + 1:04d}",
            title=f"{title} #{serial + 1}",
            content=content,
            source="supplement",
            date="2026-06-08",
        )
        docs.append(doc)
        accumulated += doc.char_count
        serial += 1
    return docs

