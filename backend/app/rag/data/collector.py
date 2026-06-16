"""Multi-source data collectors used by backend scripts."""

import json
import time
from pathlib import Path
from typing import Optional

import requests

from backend.app.rag.data.io import load_qa_pairs
from backend.app.rag.data.models import Document, QAPair


class ArxivCollector:
    def __init__(self, max_results: int = 20, query: str = "deep learning"):
        self.max_results = max_results
        self.query = query

    def collect(self) -> list[Document]:
        try:
            import arxiv

            client = arxiv.Client()
            search = arxiv.Search(
                query=self.query,
                max_results=self.max_results,
                sort_by=arxiv.SortCriterion.Relevance,
            )
            docs = []
            for idx, result in enumerate(client.results(search), 1):
                docs.append(
                    Document(
                        id=f"arxiv_{idx:04d}",
                        title=result.title,
                        content=result.summary.replace("\n", " "),
                        source="arxiv",
                        url=result.entry_id,
                        date=str(result.published.date()) if result.published else None,
                    )
                )
            return docs
        except Exception:
            return self._collect_via_api()

    def _collect_via_api(self) -> list[Document]:
        import urllib.parse
        import xml.etree.ElementTree as ET

        base_url = "http://export.arxiv.org/api/query"
        query = urllib.parse.quote(self.query)
        url = f"{base_url}?search_query=all:{query}&max_results={self.max_results}"

        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code != 200:
                return []
            root = ET.fromstring(resp.text)
        except Exception:
            return []

        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", ns)
        docs = []
        for idx, entry in enumerate(entries, 1):
            title = entry.find("atom:title", ns)
            summary = entry.find("atom:summary", ns)
            url_el = entry.find("atom:id", ns)
            published = entry.find("atom:published", ns)
            docs.append(
                Document(
                    id=f"arxiv_{idx:04d}",
                    title=title.text.strip() if title is not None and title.text else "",
                    content=summary.text.strip()[:2000] if summary is not None and summary.text else "",
                    source="arxiv",
                    url=url_el.text if url_el is not None else None,
                    date=published.text[:10] if published is not None and published.text else None,
                )
            )
        return docs


class NewsCollector:
    def __init__(self, max_articles: int = 15):
        self.max_articles = max_articles

    def collect(self) -> list[Document]:
        docs = self._fetch_online()
        if len(docs) >= self.max_articles:
            return docs[: self.max_articles]

        supplement = self.max_articles - len(docs)
        docs.extend(self._generate_samples(supplement))
        return docs

    def _fetch_online(self) -> list[Document]:
        docs = []
        try:
            resp = requests.get(
                "https://hacker-news.firebaseio.com/v0/topstories.json",
                timeout=10,
            )
            if resp.status_code != 200:
                return docs
            story_ids = resp.json()[: self.max_articles * 2]
        except Exception:
            return docs

        count = 0
        for sid in story_ids:
            if count >= self.max_articles:
                break
            try:
                item_resp = requests.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{sid}.json",
                    timeout=10,
                )
                if item_resp.status_code != 200:
                    continue
                item = item_resp.json()
                title = item.get("title", "")
                if not title:
                    continue
                text = item.get("text", "") or ""
                content = f"{title}\n\n{text}" if text else title
                docs.append(
                    Document(
                        id=f"news_{count + 1:04d}",
                        title=title,
                        content=content,
                        source="news",
                        url=item.get("url") or None,
                    )
                )
                count += 1
                time.sleep(0.1)
            except Exception:
                continue
        return docs

    def _generate_samples(self, count: int) -> list[Document]:
        templates = [
            (
                "人工智能技术在医疗领域的应用取得新突破",
                "近日，多家医院引入基于深度学习的医学影像分析系统，在肺部CT、眼底筛查等场景中诊断准确率超过95%。"
                "专家表示，AI辅助诊断将大幅提升基层医疗水平。",
            ),
            (
                "大语言模型在科研中的应用日益广泛",
                "研究人员利用大语言模型加速文献综述撰写、代码生成和数据分析。"
                "据统计，超过60%的科研人员已在日常工作中使用LLM工具，工作效率平均提升了40%。",
            ),
            (
                "自然语言处理技术助力教育智能化",
                "基于NLP技术的智能教育平台可根据学生个性化需求提供定制化学习方案。"
                "系统通过分析学生的学习行为和答题情况，自动调整教学内容和难度。",
            ),
            (
                "深度学习在自动驾驶中的关键作用",
                "自动驾驶技术的核心感知模块依赖于深度学习模型。卷积神经网络和Transformer架构"
                "被广泛应用于图像识别、目标检测和路径规划等关键任务。",
            ),
            (
                "向量数据库技术成为AI基础设施新热点",
                "随着大模型应用的普及，向量数据库作为检索增强生成的核心组件受到广泛关注。"
                "FAISS、Milvus 等开源方案被大量企业采用。",
            ),
        ]

        docs = []
        for idx in range(count):
            title, content = templates[idx % len(templates)]
            docs.append(
                Document(
                    id=f"news_fallback_{idx + 1:04d}",
                    title=title,
                    content=f"{title}。{content}",
                    source="news",
                    date="2026-06-08",
                )
            )
        return docs


class CourseMaterialCollector:
    def __init__(self, materials_dir: str | Path):
        self.materials_dir = Path(materials_dir)

    def collect(self, directory: Optional[str | Path] = None) -> list[Document]:
        target = Path(directory) if directory is not None else self.materials_dir
        if not target.exists():
            return self._generate_defaults()

        docs = []
        for filepath in sorted(target.glob("*")):
            if filepath.suffix.lower() in (".md", ".txt", ".markdown"):
                try:
                    content = filepath.read_text(encoding="utf-8")
                    docs.append(
                        Document(
                            id=f"course_{filepath.stem}",
                            title=filepath.stem.replace("_", " "),
                            content=content,
                            source="course",
                        )
                    )
                except Exception:
                    continue

        if not docs:
            return self._generate_defaults()
        return docs

    def _generate_defaults(self) -> list[Document]:
        chapters = {
            "深度学习基础概念": "深度学习是机器学习的一个分支，使用多层神经网络从数据中学习层次化的特征表示。"
            "与传统机器学习方法不同，深度学习能够自动从原始数据中提取特征，无需人工设计。",
            "Transformer架构详解": "Transformer是一种基于自注意力机制的神经网络架构，核心创新包括多头自注意力、"
            "位置编码、层归一化和残差连接。",
            "预训练语言模型原理": "预训练语言模型通过在大规模语料上进行自监督学习来获取通用语言表示。"
            "BERT 使用掩码语言模型，GPT 使用自回归语言模型。",
            "检索增强生成RAG技术": "检索增强生成结合信息检索和文本生成，解决大模型的幻觉和知识陈旧问题。"
            "文档分块、向量检索、重排序和提示词拼接是关键环节。",
        }
        materials = []
        for idx, (title, content) in enumerate(chapters.items(), 1):
            materials.append(
                Document(
                    id=f"course_{idx:04d}",
                    title=title,
                    content="\n\n".join([content] * 8),
                    source="course",
                    date="2026-06-08",
                )
            )
        return materials


class QAPairCollector:
    def __init__(self, min_pairs: int = 200, qa_pairs_path: str | Path | None = None):
        self.min_pairs = min_pairs
        self.qa_pairs_path = Path(qa_pairs_path) if qa_pairs_path is not None else None

    def collect(self) -> list[QAPair]:
        existing = []
        if self.qa_pairs_path is not None and self.qa_pairs_path.exists():
            try:
                existing = load_qa_pairs(self.qa_pairs_path)
            except Exception:
                existing = []

        if len(existing) < self.min_pairs:
            existing.extend(self._generate(self.min_pairs - len(existing)))
        return existing

    def _generate(self, count: int) -> list[QAPair]:
        topics = [
            (
                "深度学习",
                "深度学习是机器学习的一个分支，使用多层神经网络从数据中学习层次化的特征表示。",
            ),
            (
                "Transformer",
                "Transformer 是一种基于自注意力机制的架构，能够并行处理序列并建模长距离依赖。",
            ),
            (
                "BERT",
                "BERT 是基于 Transformer Encoder 的预训练语言模型，通过双向上下文编码提升语言理解能力。",
            ),
            (
                "RAG",
                "RAG 通过检索外部知识并注入上下文，帮助大模型生成更准确、更可追溯的回答。",
            ),
        ]
        templates = [
            ("什么是{term}？", "{term}是{definition}"),
            ("请解释{term}的基本概念。", "{term}的基本概念是：{definition}"),
            ("{term}的核心原理是什么？", "{definition}"),
            ("{term}有哪些典型应用？", "{term}常用于自然语言处理、信息检索、知识问答和教育智能化。{definition}"),
        ]

        qa_pairs = []
        generated = 0
        topic_idx = 0
        while generated < count:
            term, definition = topics[topic_idx % len(topics)]
            tpl_question, tpl_answer = templates[generated % len(templates)]
            qa_pairs.append(
                QAPair(
                    id=f"qa_{generated + 1:04d}",
                    question=tpl_question.format(term=term),
                    answer=tpl_answer.format(term=term, definition=definition),
                    source="auto_generated",
                )
            )
            generated += 1
            topic_idx += 1
        return qa_pairs


class DeepSeekDocsCollector:
    """爬取 DeepSeek API 文档 (https://api-docs.deepseek.com/zh-cn)。"""

    BASE = "https://api-docs.deepseek.com/zh-cn"

    PAGES = [
        ("deepseek_0001", "首次调用 API", "/"),
        ("deepseek_0002", "模型与价格", "/quick_start/pricing"),
        ("deepseek_0003", "Token 用量计算", "/quick_start/token_usage"),
        ("deepseek_0004", "限速与隔离", "/quick_start/rate_limit"),
        ("deepseek_0005", "错误码", "/quick_start/error_codes"),
        ("deepseek_0006", "思考模式", "/guides/thinking_mode"),
        ("deepseek_0007", "多轮对话", "/guides/multi_round_chat"),
        ("deepseek_0008", "对话前缀续写", "/guides/chat_prefix_completion"),
        ("deepseek_0009", "FIM 补全", "/guides/fim_completion"),
        ("deepseek_0010", "JSON Output", "/guides/json_mode"),
        ("deepseek_0011", "Tool Calls", "/guides/tool_calls"),
        ("deepseek_0012", "上下文硬盘缓存", "/guides/kv_cache"),
        ("deepseek_0013", "Anthropic API", "/guides/anthropic_api"),
        ("deepseek_0014", "API 文档", "/api/deepseek-api"),
        ("deepseek_0015", "新闻", "/news/news260424"),
        ("deepseek_0016", "常见问题", "/faq"),
        ("deepseek_0017", "更新日志", "/updates"),
        ("deepseek_0018", "接入 Agent 工具", "/quick_start/agent_integrations/claude_code"),
        ("deepseek_0019", "Langcli", "/quick_start/langcli"),
        ("deepseek_0020", "推理模式 (Reasoning)", "/guides/reasoning"),
    ]

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def collect(self) -> list[Document]:
        from bs4 import BeautifulSoup

        today = __import__("datetime").date.today().isoformat()
        docs: list[Document] = []

        for doc_id, title, path in self.PAGES:
            url = f"{self.BASE}{path}"
            try:
                response = requests.get(url, timeout=self.timeout, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; DeepSeekDocsBot/1.0)"
                })
                response.raise_for_status()
            except Exception as exc:
                import logging
                logging.getLogger(__name__).warning(
                    "DeepSeekDocsCollector: failed to fetch %s: %s", url, exc
                )
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            content_parts = []
            main = soup.find("main") or soup.find("article") or soup
            for el in main.find_all(["h1", "h2", "h3", "h4", "p", "pre", "li", "code"]):
                text = el.get_text(strip=True)
                if not text:
                    continue
                if el.name in ("h1", "h2", "h3", "h4"):
                    prefix = "#" * (3 - int(el.name[1]) + 1) if el.name[1] in "234" else "##"
                    content_parts.append(f"{prefix} {text}")
                elif el.name == "pre":
                    content_parts.append(f"```\n{text}\n```")
                else:
                    content_parts.append(text)

            content = "\n\n".join(content_parts)
            if len(content) < 100:
                import logging
                logging.getLogger(__name__).warning(
                    "DeepSeekDocsCollector: content too short (%d chars) for %s",
                    len(content), title
                )
                continue

            docs.append(Document(
                id=doc_id,
                title=title,
                content=content,
                source="deepseek_docs",
                url=url,
                date=today,
            ))

        return docs

