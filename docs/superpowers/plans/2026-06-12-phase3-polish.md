# Phase 3 Implementation Plan: Experience Polish

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Click message to review details, structured JSON logging, script web trigger, and frontend unit tests.

**Architecture:** Frontend detail panel switches from hardcoded "latest message" to a selectable message model. Backend logging is formatted as JSON for grep-friendly structured output. A new `/scripts/{name}` endpoint triggers long-running scripts via background thread. Vitest is installed for frontend unit testing of the chat store.

**Tech Stack:** Vue 3 reactivity, Python logging.Formatter, FastAPI BackgroundTasks, vitest + jsdom

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/views/WorkspaceView.vue` | Modify | Clickable messages, selected message detail |
| `frontend/src/stores/chatWorkspace.ts` | Modify | Track selected message ID |
| `backend/main.py` | Modify | JSON log formatter |
| `backend/app/api/v1/routes/` | Create `scripts_routes.py` | Script trigger endpoint |
| `backend/app/api/v1/__init__.py` | Modify | Register scripts router |
| `frontend/package.json` | Modify | Add vitest dependency |
| `frontend/vitest.config.ts` | Create | Vitest configuration |
| `frontend/src/stores/__tests__/chatWorkspace.test.ts` | Create | Store unit tests |

---

### Task 1: Click Message to Review Details

**Files:**
- Modify: `frontend/src/views/WorkspaceView.vue`
- Modify: `frontend/src/stores/chatWorkspace.ts`

- [ ] **Step 1: Add `selectedMessageId` to chatWorkspace store**

In `frontend/src/stores/chatWorkspace.ts`, add a new ref:

```typescript
const selectedMessageId = ref('')
```

Add `selectedMessageId` to the return object of `useChatWorkspace()`:

```typescript
export function useChatWorkspace() {
  return {
    sessions,
    activeSessionId,
    activeSession,
    currentMode,
    selectedMessageId,
    hydrateWorkspace,
    createSession,
    setCurrentMode,
    setActiveSession,
    deleteSession,
    ensureActiveSession,
    appendMessage,
    updateMessage,
  }
}
```

- [ ] **Step 2: In WorkspaceView, destructure `selectedMessageId`**

In `frontend/src/views/WorkspaceView.vue`, update the destructuring of `useChatWorkspace()` to include `selectedMessageId`:

```typescript
const {
  sessions,
  activeSessionId,
  activeSession,
  currentMode,
  selectedMessageId,
  hydrateWorkspace,
  createSession,
  setCurrentMode,
  setActiveSession,
  deleteSession,
  appendMessage,
  updateMessage,
} = useChatWorkspace()
```

- [ ] **Step 3: Make messages clickable and replace `latestAssistantMessage` computed**

Replace the `latestAssistantMessage` computed with a `selectedDetailMessage` computed that prefers the clicked message:

```typescript
const selectedDetailMessage = computed<ChatMessage | null>(() => {
  const messages = activeSession.value?.messages ?? []
  if (selectedMessageId.value) {
    return messages.find((m) => m.id === selectedMessageId.value) ?? null
  }
  // Fall back to latest assistant message
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    if (messages[index].role === 'assistant') {
      return messages[index]
    }
  }
  return null
})
```

- [ ] **Step 4: Update message list to be clickable with visual feedback**

In the template, add `@click` handler and active class to message articles (around line 97):

```html
<article
  v-for="message in activeSession.messages"
  :key="message.id"
  class="chat-message"
  :class="[
    `chat-message--${message.role}`,
    `chat-message--${message.status}`,
    { 'chat-message--selected': message.id === selectedMessageId },
  ]"
  @click="selectedMessageId = message.id"
>
```

- [ ] **Step 5: Replace all `latestAssistantMessage` references with `selectedDetailMessage`**

In the template, find and replace all occurrences of `latestAssistantMessage` with `selectedDetailMessage` (5 occurrences around lines 279-310 in the detail panel section).

- [ ] **Step 6: Add `chat-message--selected` style to `main.css`**

Add at the end of `frontend/src/assets/main.css`:

```css
.chat-message--selected {
  outline: 2px solid #14213d;
  border-radius: 8px;
}
.chat-message {
  cursor: pointer;
}
```

- [ ] **Step 7: Verify frontend builds**

Run: `cd frontend && npm run build 2>&1 | tail -5`
Expected: No errors

- [ ] **Step 8: Commit**

```bash
git add frontend/src/views/WorkspaceView.vue frontend/src/stores/chatWorkspace.ts frontend/src/assets/main.css
git commit -m "feat: click message to view details in right panel"
```

---

### Task 2: Structured JSON Logging

**Files:**
- Modify: `backend/main.py`

- [ ] **Step 1: Replace `logging.basicConfig` with JSON formatter**

In `backend/main.py`, replace lines 37-40:

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
```

with:

```python
import json
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info and record.exc_info[1]:
            log_entry["error"] = str(record.exc_info[1])
        return json.dumps(log_entry, ensure_ascii=False)


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])
```

- [ ] **Step 2: Verify logging still works**

Run: `python -c "from backend.main import create_app; app = create_app(); print('OK')"`
Check that output has JSON lines

- [ ] **Step 3: Run tests**

Run: `python -m pytest backend/tests/test_api.py -q`
Expected: 7 passed

- [ ] **Step 4: Commit**

```bash
git add backend/main.py
git commit -m "feat: use JSON structured logging format"
```

---

### Task 3: Script Web Trigger Endpoint

**Files:**
- Create: `backend/app/api/v1/routes/scripts_routes.py`
- Modify: `backend/app/api/v1/__init__.py`

- [ ] **Step 1: Create `backend/app/api/v1/routes/scripts_routes.py`**

```python
"""Script trigger routes — Web 入口触发离线脚本。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter

from backend.app.core.response import error_response, success_response

router = APIRouter(prefix="/scripts", tags=["scripts"])

SCRIPT_DIR = Path(__file__).resolve().parents[4] / "scripts"
ALLOWED_SCRIPTS = {
    "collect_data",
    "clean_data",
    "chunk_data",
    "build_index",
    "run_evaluation",
}


@router.post("/{name}")
def trigger_script(name: str) -> dict:
    if name not in ALLOWED_SCRIPTS:
        return error_response(f"未知脚本: {name}，可用: {', '.join(sorted(ALLOWED_SCRIPTS))}", code=404)

    script_path = SCRIPT_DIR / f"{name}.py"
    if not script_path.exists():
        return error_response(f"脚本文件不存在: {script_path}", code=404)

    try:
        result = subprocess.run(
            [sys.executable, "-m", f"backend.scripts.{name}"],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=SCRIPT_DIR.parents[1],
        )
        return success_response({
            "script": name,
            "returncode": result.returncode,
            "stdout": result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout,
            "stderr": result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr,
        })
    except subprocess.TimeoutExpired:
        return error_response(f"脚本 {name} 执行超时（300s）", code=504)
    except Exception as exc:
        return error_response(f"脚本 {name} 执行失败: {exc}", code=500)
```

- [ ] **Step 2: Register scripts router in `backend/app/api/v1/__init__.py`**

Read `backend/app/api/v1/__init__.py` and add the scripts router import and include:

```python
from backend.app.api.v1.routes.scripts_routes import router as scripts_router
```

And add to the `api_router.include_router()` calls:
```python
api_router.include_router(scripts_router)
```

- [ ] **Step 3: Verify compilation**

Run: `python -c "from backend.main import create_app; app = create_app(); print('OK')"`

- [ ] **Step 4: Run tests**

Run: `python -m pytest backend/tests/ -q`
Expected: ~29 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/v1/routes/scripts_routes.py backend/app/api/v1/__init__.py
git commit -m "feat: add script web trigger endpoint POST /scripts/{name}"
```

---

### Task 4: Frontend Unit Tests (vitest)

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/vitest.config.ts`
- Create: `frontend/src/stores/__tests__/chatWorkspace.test.ts`

- [ ] **Step 1: Install vitest**

```bash
cd frontend && npm install -D vitest @vue/test-utils jsdom 2>&1 | tail -5
```

- [ ] **Step 2: Add test script to `frontend/package.json`**

Add to the `scripts` section:
```json
"test": "vitest run",
"test:watch": "vitest"
```

- [ ] **Step 3: Create `frontend/vitest.config.ts`**

```typescript
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    globals: true,
  },
})
```

- [ ] **Step 4: Create `frontend/src/stores/__tests__/chatWorkspace.test.ts`**

```typescript
import { describe, it, expect, beforeEach } from 'vitest'
import { useChatWorkspace } from '../chatWorkspace'

describe('chatWorkspace', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('initializes with default mode qa', () => {
    const store = useChatWorkspace()
    store.hydrateWorkspace('qa')
    expect(store.currentMode.value).toBe('qa')
    expect(store.activeSession.value).not.toBeNull()
  })

  it('creates a new session', () => {
    const store = useChatWorkspace()
    store.hydrateWorkspace('qa')
    const initialCount = store.sessions.value.length
    store.createSession('summary')
    expect(store.sessions.value.length).toBe(initialCount + 1)
    expect(store.currentMode.value).toBe('summary')
  })

  it('appends and updates messages', () => {
    const store = useChatWorkspace()
    store.hydrateWorkspace('qa')
    const session = store.activeSession.value!

    const msg = store.appendMessage({
      role: 'user', mode: 'qa', text: 'hello', status: 'success',
    })
    expect(session.messages.length).toBe(1)
    expect(session.messages[0].text).toBe('hello')

    store.updateMessage(session.id, msg.id, { text: 'updated' })
    expect(session.messages[0].text).toBe('updated')
  })

  it('deletes sessions', () => {
    const store = useChatWorkspace()
    store.hydrateWorkspace('qa')
    const session = store.activeSession.value!
    store.deleteSession(session.id)
    // After deleting the only session, a new one is created
    expect(store.sessions.value.length).toBe(1)
  })

  it('normalizes mode to qa for unknown values', () => {
    const store = useChatWorkspace()
    store.hydrateWorkspace('qa')
    store.setCurrentMode('summary' as any)
    expect(store.currentMode.value).toBe('summary')
    store.setCurrentMode('unknown' as any)
    expect(store.currentMode.value).toBe('qa')
  })
})
```

- [ ] **Step 5: Run tests**

```bash
cd frontend && npx vitest run 2>&1 | tail -15
```
Expected: 5 tests passed

- [ ] **Step 6: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/vitest.config.ts frontend/src/stores/__tests__/chatWorkspace.test.ts
git commit -m "test: add vitest and chatWorkspace store unit tests"
```

---

### Task 5: Final Verification

- [ ] **Step 1: Run all backend tests**

Run: `python -m pytest backend/tests/ -q`
Expected: ~29 passed

- [ ] **Step 2: Run frontend tests**

Run: `cd frontend && npx vitest run 2>&1 | tail -5`
Expected: 5 passed

- [ ] **Step 3: Verify frontend builds**

Run: `cd frontend && npm run build 2>&1 | tail -5`
Expected: Build succeeds

- [ ] **Step 4: Final commit and push**

```bash
git add -A
git commit -m "chore: final verification of Phase 3 polish improvements"
git push
```
