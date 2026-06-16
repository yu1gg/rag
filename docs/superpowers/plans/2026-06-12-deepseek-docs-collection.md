# DeepSeek 文档采集 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scrape all 20 DeepSeek API documentation pages, convert to Documents, and feed through the existing data pipeline (clean → chunk → build_index).

**Architecture:** New `DeepSeekDocsCollector` class in `collector.py` uses `requests` + `BeautifulSoup` to scrape each page, extract text content, and return `Document` objects. `DatasetService.collect_data()` appends them to the document pool. No new dependencies needed (both already in requirements.txt).

**Tech Stack:** Python `requests`, `BeautifulSoup` (bs4), existing `Document` dataclass

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/rag/data/collector.py` | Modify | Add `DeepSeekDocsCollector` class |
| `backend/app/services/dataset_service.py` | Modify | Include deepseek docs in collect_data() |

---

### Task 1: Add DeepSeekDocsCollector and Wire into Pipeline

**Files:**
- Modify: `backend/app/rag/data/collector.py`
- Modify: `backend/app/services/dataset_service.py`

- [ ] **Step 1: Add `DeepSeekDocsCollector` to `collector.py`**

Add this class after the last existing collector class (after `QAPairCollector`):

```python
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

            # 提取正文内容
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
                # 内容太短，可能页面结构异常，跳过
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
```

- [ ] **Step 2: Add import in `collector.py`**

No new import needed — `requests`, `Document`, `time` already imported.

- [ ] **Step 3: Wire into `dataset_service.py`**

In `collect_data()`, add the deepseek collector after the other collectors (before the supplement check):

```python
        from backend.app.rag.data.collector import DeepSeekDocsCollector

        deepseek_docs = DeepSeekDocsCollector().collect()

        all_docs = arxiv_docs + news_docs + course_docs + deepseek_docs
```

Change line 48 from:
```python
        all_docs = arxiv_docs + news_docs + course_docs
```
to:
```python
        all_docs = arxiv_docs + news_docs + course_docs + deepseek_docs
```

- [ ] **Step 4: Verify compilation**

```bash
python -c "from backend.app.rag.data.collector import DeepSeekDocsCollector; c = DeepSeekDocsCollector(); print(len(c.PAGES), 'pages configured')"
```
Expected: `20 pages configured`

- [ ] **Step 5: Commit**

```bash
git add backend/app/rag/data/collector.py backend/app/services/dataset_service.py
git commit -m "feat: add DeepSeekDocsCollector for scraping api-docs.deepseek.com"
```

---

### Task 2: Run Collection + Full Pipeline

- [ ] **Step 1: Collect DeepSeek docs**

```bash
python -m backend.scripts.collect_data 2>&1 | tail -3
```
Expected: Output shows `collect_data completed` with increased document count

- [ ] **Step 2: Run clean → chunk → build**

```bash
python -m backend.scripts.clean_data 2>&1
python -m backend.scripts.chunk_data 2>&1
python -m backend.scripts.build_index 2>&1 | tail -3
```

- [ ] **Step 3: Verify a DeepSeek doc is in the index**

```bash
python -c "
import json
with open('backend/storage/index/chunk_meta.json', 'r', encoding='utf-8') as f:
    meta = json.load(f)
found = [v for v in meta.values() if v.get('source') == 'deepseek_docs']
print(f'DeepSeek chunks in index: {len(found)}')
for f in found[:3]:
    print(f'  doc_title={f.get(\"doc_title\",\"?\")[:40]}  source={f.get(\"source\")}')
"
```

- [ ] **Step 4: Run all tests**

```bash
python -m pytest backend/tests/ -q 2>&1 | tail -3
```
Expected: ~29 passed

- [ ] **Step 5: Final commit and push**

```bash
git add -A
git commit -m "chore: run full pipeline with DeepSeek docs, final verification"
git push
```
