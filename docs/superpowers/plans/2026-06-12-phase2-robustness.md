# Phase 2 Implementation Plan: Engineering Robustness

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix deprecated patterns, network error handling gaps, missing 404 route, hardcoded config, and async route inconsistencies.

**Architecture:** Five independent clean-up tasks — `@app.on_event` → lifespan context manager, `http.ts` network/timeout hardening, catch-all 404 redirect in Vue Router, `api_prefix` moved to `.env`, and 4 `async def` routes converted to sync `def`.

**Tech Stack:** FastAPI lifespan, Vue Router catch-all, TypeScript fetch error handling, Python dotenv

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `backend/main.py` | Modify | Replace `@app.on_event("startup")` with lifespan context manager |
| `frontend/src/api/http.ts` | Modify | Add network error catch, timeout, use getErrorMessage |
| `frontend/src/router/index.ts` | Modify | Add catch-all 404 redirect to `/` |
| `backend/app/core/config.py` | Modify | Read `api_prefix` from `.env` |
| `backend/.env.example` | Modify | Add `API_PREFIX` entry |
| `backend/app/api/v1/routes/health_routes.py` | Modify | `async def` → `def` |
| `backend/app/api/v1/routes/dataset_routes.py` | Modify | `async def` → `def` |
| `backend/app/api/v1/routes/index_routes.py` | Modify | `async def` → `def` |
| `backend/app/api/v1/routes/evaluation_routes.py` | Modify | `async def` → `def` |

---

### Task 1: FastAPI Lifespan Migration

**Files:**
- Modify: `backend/main.py`

Replace `@app.on_event("startup")` (deprecated) with the lifespan context manager pattern.

- [ ] **Step 1: Replace the `@app.on_event("startup")` block**

In `backend/main.py`, find lines 103-115:
```python
    @app.on_event("startup")
    def prewarm_rag_service() -> None:
        # 预热只覆盖检索链路，不主动调用外部 LLM。
        # 这样可以把"索引加载 + 本地模型初始化"的冷启动成本前移到服务启动时，
        # 同时避免因为外部 API 波动导致后端完全起不来。
        if not settings.prewarm_rag_on_startup:
            logger.info("RAG prewarm disabled by configuration.")
            return
        try:
            summary = get_rag_service().prewarm_for_serving()
            logger.info("RAG prewarm summary: %s", summary)
        except Exception as exc:  # pragma: no cover - startup environment varies
            logger.warning("RAG prewarm failed: %s", exc)
```

Replace with a lifespan context manager. Add this import at the top:
```python
from contextlib import asynccontextmanager
```

Then add the lifespan function BEFORE `create_app()`:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时预热 RAG 检索链路。"""
    if settings.prewarm_rag_on_startup:
        try:
            summary = get_rag_service().prewarm_for_serving()
            logger.info("RAG prewarm summary: %s", summary)
        except Exception as exc:  # pragma: no cover - startup environment varies
            logger.warning("RAG prewarm failed: %s", exc)
    else:
        logger.info("RAG prewarm disabled by configuration.")
    yield
```

And pass it to `FastAPI(...)` constructor in `create_app()`:
```python
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url=None,
        lifespan=lifespan,
    )
```

Remove the `@app.on_event("startup")` block entirely.

- [ ] **Step 2: Verify tests still pass**

Run: `python -m pytest backend/tests/test_api.py -q`
Expected: 7 passed (or all tests pass)

- [ ] **Step 3: Commit**

```bash
git add backend/main.py
git commit -m "refactor: migrate @app.on_event to lifespan context manager"
```

---

### Task 2: Frontend Network Error Handling

**Files:**
- Modify: `frontend/src/api/http.ts`
- Modify: `frontend/src/api/error.ts`

- [ ] **Step 1: Update `error.ts` to handle more error types**

Replace the content of `frontend/src/api/error.ts`:
```typescript
export function getErrorMessage(
  error: unknown,
  fallback = '请求失败，请稍后重试。',
): string {
  if (error instanceof Error) {
    const message = error.message.trim()
    if (message) {
      return message
    }
  }

  if (error instanceof TypeError) {
    return '网络连接失败，请检查网络后重试。'
  }

  return fallback
}
```

- [ ] **Step 2: Update `request()` in `http.ts` to catch network errors**

Replace the `request()` function in `frontend/src/api/http.ts`:

The current function does not catch `TypeError` from `fetch()` when the network is down. Wrap the `fetch()` call with try/catch:

```typescript
export async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<ApiEnvelope<T>> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      signal: AbortSignal.timeout(30000),
      headers: {
        'Content-Type': 'application/json',
        ...(init?.headers ?? {}),
      },
      ...init,
    })
  } catch (err) {
    throw new Error('网络连接失败，请检查后端服务是否启动。')
  }

  const rawText = await response.text()
  let payload: ApiEnvelope<T> | null = null

  if (rawText) {
    try {
      payload = JSON.parse(rawText) as ApiEnvelope<T>
    } catch {
      if (response.ok) {
        throw new Error('服务返回了无法解析的响应。')
      }
      throw new Error(`请求失败（HTTP ${response.status}），且响应不是有效 JSON。`)
    }
  }

  if (!response.ok) {
    throw new Error(payload?.message?.trim() || `请求失败（HTTP ${response.status}）`)
  }
  if (!payload) {
    throw new Error('服务返回了空响应。')
  }
  return payload
}
```

- [ ] **Step 3: Update `requestStream()` in `http.ts` to catch network errors**

Wrap the `fetch()` call in `requestStream()` similarly:

```typescript
export async function* requestStream(
  path: string,
  init?: RequestInit,
): AsyncGenerator<string, void, undefined> {
  const url = `${API_BASE_URL}${path}`
  let response: Response
  try {
    response = await fetch(url, {
      signal: AbortSignal.timeout(120000),
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...(init?.headers as Record<string, string> | undefined),
      },
    })
  } catch (err) {
    throw new Error('网络连接失败，请检查后端服务是否启动。')
  }

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

- [ ] **Step 4: Verify frontend builds**

Run: `cd frontend && npm run build 2>&1 | tail -5`
Expected: No errors

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api/http.ts frontend/src/api/error.ts
git commit -m "fix: add network error handling and 30s timeout to fetch"
```

---

### Task 3: Frontend 404 Catch-All Route

**Files:**
- Modify: `frontend/src/router/index.ts`

- [ ] **Step 1: Add catch-all route**

Add a catch-all route at the end of the routes array in `frontend/src/router/index.ts`:

```typescript
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    redirect: '/',
  },
```

This goes before the closing `]` of the routes array.

- [ ] **Step 2: Verify frontend builds**

Run: `cd frontend && npm run build 2>&1 | tail -5`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/router/index.ts
git commit -m "fix: add catch-all 404 route redirecting to home"
```

---

### Task 4: api_prefix Configuration

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `backend/.env.example`

- [ ] **Step 1: Read `api_prefix` from environment**

In `backend/app/core/config.py`, line 75, change:
```python
        self.api_prefix = "/api/v1"
```
to:
```python
        self.api_prefix = _env("API_PREFIX", "/api/v1")
```

- [ ] **Step 2: Add `API_PREFIX` to `.env.example`**

Read `backend/.env.example` and add after the `APP_PORT` line:
```
# API 路径前缀
API_PREFIX=/api/v1
```

- [ ] **Step 3: Verify compilation**

Run: `python -c "from backend.app.core.config import settings; print(settings.api_prefix)"`
Expected: `/api/v1`

- [ ] **Step 4: Commit**

```bash
git add backend/app/core/config.py backend/.env.example
git commit -m "refactor: read api_prefix from env variable"
```

---

### Task 5: Async Route Correction

**Files:**
- Modify: `backend/app/api/v1/routes/health_routes.py`
- Modify: `backend/app/api/v1/routes/dataset_routes.py`
- Modify: `backend/app/api/v1/routes/index_routes.py`
- Modify: `backend/app/api/v1/routes/evaluation_routes.py`

- [ ] **Step 1: Convert `health_routes.py`**

Change:
```python
async def health() -> dict:
```
to:
```python
def health() -> dict:
```

- [ ] **Step 2: Convert `dataset_routes.py`**

Change:
```python
async def dataset_stats(service: DatasetService = Depends(get_dataset_service)) -> dict:
```
to:
```python
def dataset_stats(service: DatasetService = Depends(get_dataset_service)) -> dict:
```

- [ ] **Step 3: Convert `index_routes.py`**

Change:
```python
async def index_status(service: IndexService = Depends(get_index_service)) -> dict:
```
to:
```python
def index_status(service: IndexService = Depends(get_index_service)) -> dict:
```

- [ ] **Step 4: Convert `evaluation_routes.py`**

Change:
```python
async def latest_evaluations(service: EvaluationService = Depends(get_evaluation_service)) -> dict:
```
to:
```python
def latest_evaluations(service: EvaluationService = Depends(get_evaluation_service)) -> dict:
```

- [ ] **Step 5: Run all backend tests**

Run: `python -m pytest backend/tests/ -q`
Expected: ~29 passed

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/v1/routes/health_routes.py backend/app/api/v1/routes/dataset_routes.py backend/app/api/v1/routes/index_routes.py backend/app/api/v1/routes/evaluation_routes.py
git commit -m "refactor: convert sync async def routes to def"
```

---

### Task 6: Final Verification

- [ ] **Step 1: Run all backend tests**

Run: `python -m pytest backend/tests/ -q`
Expected: ~29 passed

- [ ] **Step 2: Verify frontend builds**

Run: `cd frontend && npm run build 2>&1 | tail -5`
Expected: Build succeeds

- [ ] **Step 3: Final commit and push**

```bash
git add -A
git commit -m "chore: final verification of Phase 2 robustness improvements"
git push
```
