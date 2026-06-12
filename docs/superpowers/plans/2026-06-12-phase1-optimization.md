# Phase 1 Implementation Plan: Streaming + Conversation + Speed

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add streaming LLM output, multi-turn conversation memory, and response speed optimizations to the RAG chat system.

**Architecture:** Backend gets SSE streaming endpoint (`/rag/qa/stream`), `LLMClient` gets streaming generator, frontend consumes SSE via `EventSource`-like fetch. Conversation history is injected into prompt templates via `{history}` placeholder. Embedding queries get LRU caching; LLM timeout/retry is improved.

**Tech Stack:** FastAPI `StreamingResponse`, OpenAI `stream=True`, Python generators, frontend ReadableStream/fetch streaming

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/rag/generation/llm_client.py` | Modify | Add `chat_stream()` generator with `stream=True` |
| `backend/app/rag/generation/prompts.py` | Modify | Add `{history}` to QA/Summary templates, update `format_prompt()` |
| `backend/app/rag/indexing/embedder.py` | Modify | Add LRU query embedding cache |
| `backend/app/services/rag_service.py` | Modify | Add `answer_question_stream()`, add `history` param, add `generate_answer_stream()` |
| `backend/app/api/v1/routes/rag_routes.py` | Modify | Add `POST /rag/qa/stream` SSE endpoint |
| `frontend/src/api/rag.ts` | Modify | Add `fetchQaStream()` for SSE consumption |
| `frontend/src/api/http.ts` | Modify | Add `requestStream()` helper |
| `frontend/src/views/WorkspaceView.vue` | Modify | Streaming text accumulation, send history, delete old draft after stream done |
| `frontend/src/types/api.ts` | Modify | Add `QaStreamChunk` type |
| `backend/tests/test_rag_service.py` | Modify | Add streaming and history tests |

---

### Task 1: LLMClient Streaming Generator

**Files:**
- Modify: `backend/app/rag/generation/llm_client.py`

- [ ] **Step 1: Add `chat_stream()` method to LLMClient**

Add this method after the existing `chat()` method (around line 48):

```python
def chat_stream(
    self,
    messages: List[dict],
    temperature: float | None = None,
    max_tokens: int | None = None,
):
    """流式调用 LLM，逐 chunk 返回 delta 文本。

    注意：流式模式下不做应用层重试，因为 stream 不可回放。
    网络中断由 OpenAI SDK 自身的 connect timeout 覆盖。
    """
    response = self.client.chat.completions.create(
        model=self.model,
        messages=messages,
        temperature=temperature if temperature is not None else self.temperature,
        max_tokens=max_tokens if max_tokens is not None else self.max_tokens,
        stream=True,
    )
    for chunk in response:
        delta = chunk.choices[0].delta.content if chunk.choices else ""
        if delta:
            yield delta
```

- [ ] **Step 2: Add `answer_stream()` convenience method**

```python
def answer_stream(self, prompt: str, **kwargs):
    """流式单轮问答。"""
    messages = [{"role": "user", "content": prompt}]
    yield from self.chat_stream(messages, **kwargs)
```

- [ ] **Step 3: Verify file compiles**

Run: `python -c "from backend.app.rag.generation.llm_client import LLMClient; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/app/rag/generation/llm_client.py
git commit -m "feat: add chat_stream() and answer_stream() to LLMClient"
```

---

### Task 2: Prompt Templates with Conversation History

**Files:**
- Modify: `backend/app/rag/generation/prompts.py`

- [ ] **Step 1: Add `{history}` placeholder to QA_TEMPLATE**

Replace the `QA_TEMPLATE` constant:

```python
QA_TEMPLATE = (
    "你是一个课程项目的智能问答助手。请严格基于下面提供的上下文来回答问题。\n\n"
    "{history}"
    "【参考资料】\n"
    "{context}\n\n"
    "【用户问题】\n"
    "{question}\n\n"
    "要求：\n"
    "1. 如果上下文足够回答，请用中文给出准确、完整的答案。\n"
    "2. 如果上下文信息不足，请明确说明\"根据现有资料，我无法回答这个问题\"。\n"
    "3. 不要编造上下文之外的信息。"
)
```

- [ ] **Step 2: Add `{history}` placeholder to SUMMARY_TEMPLATE**

Replace the `SUMMARY_TEMPLATE` constant:

```python
SUMMARY_TEMPLATE = (
    "你是一个文本摘要助手。请对以下文本进行摘要压缩。\n\n"
    "{history}"
    "【待摘要文本】\n"
    "{context}\n\n"
    "要求：\n"
    "1. 先提取关键句子，再归纳概括。\n"
    "2. 输出结构为：核心主题、关键要点、详细摘要。\n"
    "3. 摘要长度控制在原文的15%-30%。\n"
    "4. 用中文输出。"
)
```

- [ ] **Step 3: Update `format_prompt()` to accept and pass `history`**

```python
def format_prompt(
    self, mode: str, question: str, context: str, history: str = ""
) -> str:
    template = {"qa": self.QA_TEMPLATE, "summary": self.SUMMARY_TEMPLATE}.get(mode)
    if template is None:
        raise ValueError(f"Unknown prompt mode: {mode}")
    return template.format(context=context, question=question, history=history)
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/rag/generation/prompts.py
git commit -m "feat: add {history} placeholder to prompt templates"
```

---

### Task 3: SSE Streaming Endpoint (Backend)

**Files:**
- Modify: `backend/app/rag/services/rag_service.py`
- Modify: `backend/app/api/v1/routes/rag_routes.py`

- [ ] **Step 1: Add `generate_answer_stream()` to RagService**

Add this method after `generate_answer()`:

```python
def generate_answer_stream(
    self,
    mode: str,
    question: str,
    context: str,
    temperature: float,
    max_tokens: int | None = None,
    history: str = "",
):
    prompt = self._get_prompts().format_prompt(
        mode, question, context, history=history
    )
    yield from self._get_llm().answer_stream(
        prompt, temperature=temperature, max_tokens=max_tokens
    )
```

- [ ] **Step 2: Add `answer_question_stream()` generator to RagService**

```python
def answer_question_stream(
    self,
    question: str,
    top_k: int,
    temperature: float,
    method: str = "vector",
    history: list[dict] | None = None,
):
    """流式 QA：先检索，然后逐 chunk 输出 LLM 回答。

    每个 chunk 是一段纯文本，最后 yield references 的 JSON。
    """
    import json

    total_start = perf_counter()
    results, metrics = self._retrieve_results_with_metrics(question, top_k, method=method)

    context, _ = self.build_qa_context(results)
    history_str = self._format_chat_history(history) if history else ""

    # 先发送 retrieval 完成的信号和 metrics（作为首条 SSE 事件）
    yield json.dumps({"type": "meta", "metrics": {"result_count": len(results)}}) + "\n"

    # 然后逐 chunk 输出 LLM 回复
    for chunk in self.generate_answer_stream(
        "qa", question, context, temperature,
        max_tokens=max(1, self.settings.qa_max_tokens),
        history=history_str,
    ):
        yield json.dumps({"type": "chunk", "text": chunk}) + "\n"

    # 最后发送 references
    yield json.dumps({
        "type": "done",
        "references": self._build_references(results),
        "metrics": {"total_s": round(perf_counter() - total_start, 4)},
    }) + "\n"
```

- [ ] **Step 3: Add `_format_chat_history()` helper**

```python
@staticmethod
def _format_chat_history(history: list[dict]) -> str:
    """将对话历史格式化为 prompt 可用的字符串。"""
    if not history:
        return ""
    lines = ["【对话历史】"]
    for turn in history[-6:]:  # 最多保留最近 6 轮（3 组问答）
        role = "用户" if turn.get("role") == "user" else "助手"
        content = turn.get("content", "")
        lines.append(f"{role}：{content}")
    lines.append("")
    return "\n".join(lines)
```

- [ ] **Step 4: Add `POST /rag/qa/stream` endpoint to rag_routes.py**

```python
from fastapi.responses import StreamingResponse
import json


@router.post("/qa/stream")
def qa_stream(
    payload: QaRequest,
    service: RagService = Depends(get_rag_service),
):
    def generate():
        for line in service.answer_question_stream(
            question=payload.question,
            top_k=payload.top_k,
            temperature=payload.temperature,
            method=payload.method,
        ):
            yield f"data: {line}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

Update imports at top of rag_routes.py:
```python
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
```

- [ ] **Step 5: Verify backend compiles and existing tests pass**

Run: `python -m pytest backend/tests/test_api.py -q`
Expected: All existing tests pass (7 passed)

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/rag_service.py backend/app/api/v1/routes/rag_routes.py
git commit -m "feat: add SSE streaming endpoint POST /rag/qa/stream"
```

---

### Task 4: Frontend SSE Consumer

**Files:**
- Modify: `frontend/src/api/http.ts`
- Modify: `frontend/src/api/rag.ts`
- Modify: `frontend/src/types/api.ts`
- Modify: `frontend/src/views/WorkspaceView.vue`

- [ ] **Step 1: Add `QaStreamEvent` types to `frontend/src/types/api.ts`**

```typescript
export interface QaStreamMeta {
  type: 'meta'
  metrics: { result_count: number }
}

export interface QaStreamChunk {
  type: 'chunk'
  text: string
}

export interface QaStreamDone {
  type: 'done'
  references: ReferenceItem[]
  metrics: { total_s: number }
}

export type QaStreamEvent = QaStreamMeta | QaStreamChunk | QaStreamDone
```

- [ ] **Step 2: Add `requestStream()` to `frontend/src/api/http.ts`**

Add after the `request()` function and its export at the bottom:

```typescript
export async function* requestStream(
  path: string,
  init?: RequestInit,
): AsyncGenerator<string, void, undefined> {
  const url = `${API_BASE_URL}${path}`
  const response = await fetch(url, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers as Record<string, string> | undefined),
    },
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `请求失败（HTTP ${response.status}）`)
  }

  if (!response.body) {
    throw new Error('服务不支持流式响应')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') return
          yield data
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}
```

- [ ] **Step 3: Add `fetchQaStream()` to `frontend/src/api/rag.ts`**

```typescript
import type { QaStreamEvent } from '../types/api'

export async function* fetchQaStream(
  payload: QaPayload,
): AsyncGenerator<QaStreamEvent, void, undefined> {
  const stream = requestStream('/rag/qa/stream', {
    method: 'POST',
    body: JSON.stringify(payload),
  })

  for await (const line of stream) {
    yield JSON.parse(line) as QaStreamEvent
  }
}
```

Add the import of `requestStream`:
```typescript
import { request, requestStream } from './http'
```

- [ ] **Step 4: Update `handleSubmit()` in WorkspaceView.vue for streaming**

Replace the QA branch inside `try { ... }` (around lines 549-562) with:

```typescript
try {
  if (currentMode.value === 'qa') {
    const qaPayload = payload as QaPayload
    let accumulatedText = ''
    let streamReferences: ReferenceItem[] = []

    for await (const event of fetchQaStream(qaPayload)) {
      if (event.type === 'chunk') {
        accumulatedText += event.text
        updateMessage(session.id, pendingMessage.id, {
          text: accumulatedText,
          status: 'success',
          meta: {
            query: qaPayload.question,
            topK: qaPayload.top_k,
            temperature: qaPayload.temperature,
            method: qaPayload.method,
          },
        })
      } else if (event.type === 'done') {
        streamReferences = event.references
        updateMessage(session.id, pendingMessage.id, {
          text: accumulatedText || '问答接口已返回，但答案为空。',
          status: 'success',
          meta: {
            references: streamReferences,
            query: qaPayload.question,
            topK: qaPayload.top_k,
            temperature: qaPayload.temperature,
            method: qaPayload.method,
          },
        })
      }
    }
  } else {
    // Summary stays non-streaming for now
    const response = await fetchSummary(payload as SummaryPayload)
    const summary = response.data?.summary?.trim() ?? ''
    updateMessage(session.id, pendingMessage.id, {
      text: summary || '摘要接口已返回，但摘要为空。',
      status: 'success',
      meta: {
        inputLength: (payload as SummaryPayload).text.length,
        outputLength: summary.length,
        temperature: (payload as SummaryPayload).temperature,
      },
    })
  }
```

Add imports at top of `<script setup>`:
```typescript
import { fetchQaStream, fetchSummary } from '../api/rag'
import type { ReferenceItem } from '../types/api'
```

Remove the old `fetchQa` import (keep `fetchSummary`):
```typescript
import { fetchQaStream, fetchSummary } from '../api/rag'
```

- [ ] **Step 5: Remove `isSubmitting` blocking during streaming**

Change the `isSubmitting` gate — allow draft clearing immediately on stream start rather than waiting for completion. In `handleSubmit()`, move `draft.value = ''` to right after `appendMessage` calls (before the `for await`), and set `isSubmitting.value = false` when the stream ends.

The key change: inside try block, after `await scrollToBottom()`, add:
```typescript
draft.value = ''
isSubmitting.value = false
```

And remove the `draft.value = ''` from the bottom of the try block and `draft.value = rawInput` from the catch block.

- [ ] **Step 6: Verify frontend compiles**

Run: `cd frontend && npm run build 2>&1 | tail -5`
Expected: No TypeScript errors

- [ ] **Step 7: Commit**

```bash
git add frontend/src/api/http.ts frontend/src/api/rag.ts frontend/src/types/api.ts frontend/src/views/WorkspaceView.vue
git commit -m "feat: add SSE streaming consumer in frontend"
```

---

### Task 5: Multi-Turn Conversation History

**Files:**
- Modify: `frontend/src/views/WorkspaceView.vue`
- Modify: `frontend/src/types/chat.ts`
- Modify: `frontend/src/api/rag.ts`
- Modify: `backend/app/schemas/rag.py`

- [ ] **Step 1: Add `history` to `QaPayload` in `frontend/src/types/api.ts`**

```typescript
export interface QaPayload {
  question: string
  top_k?: number
  temperature?: number
  method?: 'vector' | 'keyword'
  history?: { role: 'user' | 'assistant'; content: string }[]
}
```

- [ ] **Step 2: Add `history` field to `QaRequest` in `backend/app/schemas/rag.py`**

```python
class QaRequest(BaseModel):
    question: str
    top_k: int = Field(default=5, ge=1, le=10)
    temperature: float = Field(default=0.7, ge=0.0, le=1.5)
    method: str = Field(default="vector", pattern="^(vector|keyword)$")
    history: list[dict] | None = Field(default=None)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("question 不能为空")
        return stripped
```

- [ ] **Step 3: Pass history from route to service in `rag_routes.py`**

Update the `/qa` endpoint and `/qa/stream` endpoint to pass history:

```python
result = service.answer_question(
    question=payload.question,
    top_k=payload.top_k,
    temperature=payload.temperature,
    method=payload.method,
    history=payload.history,
)
```

Add `history` parameter to `answer_question()` signature in `rag_service.py`:

```python
def answer_question(
    self, question: str, top_k: int, temperature: float,
    method: str = "vector", history: list[dict] | None = None,
) -> dict:
```

Update `answer_question_stream()` to accept history (already done in Task 3).

Update the `generate_answer()` call inside `answer_question()` to pass history:

```python
history_str = self._format_chat_history(history) if history else ""
prompt = self._get_prompts().format_prompt(
    "qa", question, context, history=history_str
)
```

- [ ] **Step 4: Update `buildQaPayload()` in WorkspaceView.vue to include history**

```typescript
function buildQaPayload(): QaPayload | null {
  const question = draft.value.trim()
  if (!question) {
    validationError.value = '请输入问题后再发送。'
    return null
  }
  if (!Number.isInteger(topK.value) || topK.value < 1 || topK.value > 10) {
    validationError.value = 'Top-K 必须是 1 到 10 之间的整数。'
    return null
  }
  if (!Number.isFinite(temperature.value) || temperature.value < 0 || temperature.value > 1.5) {
    validationError.value = 'Temperature 必须在 0 到 1.5 之间。'
    return null
  }

  // Build history from current session's last messages (up to 6 turns)
  const session = activeSession.value
  const history: { role: 'user' | 'assistant'; content: string }[] = []
  if (session) {
    const recentMessages = session.messages.slice(-6)
    for (const msg of recentMessages) {
      if (msg.status !== 'loading') {
        history.push({
          role: msg.role,
          content: msg.text,
        })
      }
    }
  }

  return {
    question,
    top_k: topK.value,
    temperature: temperature.value,
    method: retrievalMethod.value,
    history,
  }
}
```

- [ ] **Step 5: Run tests**

Run: `python -m pytest backend/tests/test_api.py -q`
Expected: All 7 tests pass

- [ ] **Step 6: Verify frontend builds**

Run: `cd frontend && npm run build 2>&1 | tail -5`
Expected: No errors

- [ ] **Step 7: Commit**

```bash
git add backend/app/schemas/rag.py backend/app/api/v1/routes/rag_routes.py backend/app/services/rag_service.py frontend/src/types/api.ts frontend/src/views/WorkspaceView.vue
git commit -m "feat: add multi-turn conversation history to QA"
```

---

### Task 6: Embedding Query Cache

**Files:**
- Modify: `backend/app/rag/indexing/embedder.py`

- [ ] **Step 1: Add LRU cache to `encode_query()`**

```python
from functools import lru_cache
import hashlib


class Embedder:
    # ... existing code ...

    def encode_query(self, query: str) -> np.ndarray:
        # Check cache first
        cache_key = hashlib.md5(query.encode("utf-8")).hexdigest()
        if cache_key in self._query_cache:
            return self._query_cache[cache_key]

        self._ensure_model()
        if self._use_fallback:
            vec = self._encode_fallback([query]).flatten()
        else:
            vec = self._model.encode(
                [query],
                normalize_embeddings=True,
            )
            vec = np.asarray(vec, dtype=np.float32).flatten()

        # Store in cache (max 128 entries)
        if len(self._query_cache) >= 128:
            # FIFO eviction
            oldest_key = next(iter(self._query_cache))
            del self._query_cache[oldest_key]
        self._query_cache[cache_key] = vec

        return vec
```

Add `self._query_cache: dict[str, np.ndarray] = {}` to `__init__()`:

```python
def __init__(self, model_name: str = "BAAI/bge-m3", device: str = "auto", local_only: bool = True):
    # ... existing assignments ...
    self._query_cache: dict[str, np.ndarray] = {}
```

- [ ] **Step 2: Verify compiles**

Run: `python -c "from backend.app.rag.indexing.embedder import Embedder; print('OK')"`

- [ ] **Step 3: Commit**

```bash
git add backend/app/rag/indexing/embedder.py
git commit -m "feat: add LRU query embedding cache"
```

---

### Task 7: LLM Retry/Timeout Optimization

**Files:**
- Modify: `backend/app/rag/generation/llm_client.py`
- Modify: `backend/app/core/config.py`

- [ ] **Step 1: Reduce default retry sleep in `chat()`**

Change the retry delay from exponential `2**attempt` to shorter constant:

```python
def chat(
    self,
    messages: List[dict],
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    last_error = None
    for attempt in range(self._max_retries):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature if temperature is not None else self.temperature,
                max_tokens=max_tokens if max_tokens is not None else self.max_tokens,
                stream=False,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            last_error = exc
            if attempt < self._max_retries - 1:
                import time
                time.sleep(0.5)  # reduced from 2**attempt to constant 0.5s
    raise RuntimeError(f"LLM call failed after {self._max_retries} attempts: {last_error}") from last_error
```

- [ ] **Step 2: Verify OpenAI timeout is configured from settings**

Check that `OPENAI_TIMEOUT` is used. In `config.py`:

```python
self.openai_timeout = int(os.getenv("OPENAI_TIMEOUT", "20"))
```

The `LLMClient.__init__` already uses `timeout=llm_cfg.get("timeout", 20)` — verified. No change needed.

- [ ] **Step 3: Commit**

```bash
git add backend/app/rag/generation/llm_client.py
git commit -m "perf: reduce LLM retry sleep from exponential to 0.5s"
```

---

### Task 8: Final Verification

- [ ] **Step 1: Run all backend tests**

Run: `python -m pytest backend/tests/ -q`
Expected: All tests pass (~27 tests)

- [ ] **Step 2: Verify frontend builds**

Run: `cd frontend && npm run build 2>&1 | tail -5`
Expected: Build succeeds

- [ ] **Step 3: Final commit and push**

```bash
git add -A
git commit -m "chore: final verification of Phase 1 optimizations"
git push
```
