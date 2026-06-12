"""Prompt template manager."""

from typing import List


class PromptTemplate:
    QA_TEMPLATE = """你是一位专业、耐心的课程助教。请根据以下参考资料回答用户的问题。
要求：
1. 如果参考资料足以回答，请给出准确、完整的答案
2. 如果参考资料不足以回答，请明确告知"该问题超出了我目前的知识范围"
3. 回答应清晰易懂，适合学生理解

{history}
参考资料：
{context}

用户问题：{question}"""

    SUMMARY_TEMPLATE = """请按照以下步骤对文本进行摘要：

第1步 - 提取关键句：识别原文中最能体现核心内容的3-5个句子
第2步 - 归纳概括：将关键信息提炼为简洁的概括性表述
第3步 - 结构化输出：
  - 【核心主题】：一句话概括全文主旨
  - 【关键要点】：以要点形式列出3-5个核心观点
  - 【详细摘要】：连贯的摘要段落

摘要总长度应控制在原文的15%-30%之间。

{history}
原文：
{context}"""

    KNOWLEDGE_QA_TEMPLATE = """请根据以下参考资料回答用户的问题。每个参考资料的编号格式为[来源N]。
要求：
1. 基于参考资料给出准确答案
2. 在答案中标注所引用的来源编号，例如"根据[来源1]和[来源3]..."
3. 如果参考资料中不包含相关信息，请明确说明

{history}
参考资料：
{context}

用户问题：{question}"""

    @staticmethod
    def format_context(results: List) -> str:
        parts = []
        for i, result in enumerate(results, 1):
            parts.append(f"[来源{i}] chunk_id: {result.chunk_id}\n{result.content}")
        return "\n\n---\n\n".join(parts)

    def format_prompt(self, mode: str, question: str, context: str, history: str = "") -> str:
        templates = {
            "qa": self.QA_TEMPLATE,
            "summary": self.SUMMARY_TEMPLATE,
            "knowledge_qa": self.KNOWLEDGE_QA_TEMPLATE,
        }
        template = templates.get(mode)
        if template is None:
            raise ValueError(f"未知模式: {mode}，可选: qa, summary, knowledge_qa")
        return template.format(context=context, question=question, history=history)

