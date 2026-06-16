# Reference Origin Display — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pass document metadata (title, source, url, date) through the full pipeline so the frontend can display each reference chunk's document origin with a clickable source link.

**Architecture:** Add 4 fields to Chunk dataclass, propagate through Chunker → VectorStore → SearchResult → _build_references → ReferenceItem → ReferenceList display. Requires index rebuild.

**Tech Stack:** Python dataclasses, Vue 3 props, no new dependencies

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/rag/data/models.py` | Modify | Add doc_title, source, url, date to Chunk |
| `backend/app/rag/data/chunker.py` | Modify | Pass Document metadata to Chunk |
| `backend/app/rag/indexing/vector_store.py` | Modify | Store metadata fields |
| `backend/app/services/index_service.py` | Modify | Pass new fields to store.add() |
| `backend/app/rag/retrieval/retriever.py` | Modify | Populate SearchResult fields from metadata |
| `backend/app/rag/retrieval/keyword_retriever.py` | Modify | Carry metadata in _ChunkRecord |
| `backend/app/services/rag_service.py` | Modify | Output metadata in _build_references |
| `frontend/src/types/api.ts` | Modify | Add fields to ReferenceItem |
| `frontend/src/components/ReferenceList.vue` | Modify | Display doc origin |

---

### Task 1: Backend Models + Chunker

**Files:**
- Modify: `backend/app/rag/data/models.py`
- Modify: `backend/app/rag/data/chunker.py`

- [ ] **Step 1: Add fields to Chunk dataclass**

In `models.py`, add to the Chunk dataclass:
```python
@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    content: str
    char_start: int
    char_end: int
    token_count: int
    doc_title: str = ""
    source: str = ""
    url: str = ""
    date: str = ""
```

- [ ] **Step 2: Pass Document metadata in Chunker**

In `chunker.py`, update both Chunk construction sites (lines 46-53 and lines 71-78):

```python
Chunk(
    chunk_id=f"{doc.id}_chunk_{chunk_idx:04d}",
    doc_id=doc.id,
    content=current_text.strip(),
    char_start=current_char_start,
    char_end=current_char_start + len(current_text),
    token_count=token_count,
    doc_title=doc.title,
    source=doc.source,
    url=doc.url or "",
    date=doc.date or "",
)
```

Apply this to BOTH Chunk() calls (the one at line 46 and the one at line 71).

- [ ] **Step 3: Verify compilation**

Run: `python -c "from backend.app.rag.data.models import Chunk; c = Chunk('id','doc','text',0,10,5,doc_title='t',source='s',url='u',date='d'); print(c.doc_title)"`
Expected: `t`

- [ ] **Step 4: Commit**

```bash
git add backend/app/rag/data/models.py backend/app/rag/data/chunker.py
git commit -m "feat: add doc_title, source, url, date to Chunk and pass through Chunker"
```

---

### Task 2: VectorStore + IndexService

**Files:**
- Modify: `backend/app/rag/indexing/vector_store.py`
- Modify: `backend/app/services/index_service.py`

- [ ] **Step 1: Extend VectorStore.add() signature and metadata**

Change `add()` signature to accept new lists and store them:
```python
def add(
    self,
    chunk_ids: List[str],
    vectors: np.ndarray,
    contents: List[str],
    doc_ids: List[str],
    doc_titles: List[str] | None = None,
    sources: List[str] | None = None,
    urls: List[str] | None = None,
    dates: List[str] | None = None,
):
    if vectors.shape[0] == 0:
        return

    vectors = np.asarray(vectors, dtype=np.float32)
    if vectors.ndim == 1:
        vectors = vectors.reshape(1, -1)

    start_id = self.index.ntotal
    self.index.add(vectors)

    for i, (chunk_id, content, doc_id) in enumerate(zip(chunk_ids, contents, doc_ids)):
        meta = {
            "chunk_id": chunk_id,
            "doc_id": doc_id,
            "content": content,
        }
        if doc_titles:
            meta["doc_title"] = doc_titles[i]
        if sources:
            meta["source"] = sources[i]
        if urls:
            meta["url"] = urls[i]
        if dates:
            meta["date"] = dates[i]
        self.metadata[start_id + i] = meta
```

- [ ] **Step 2: Update IndexService.build_index()**

Pass new lists to `store.add()`:
```python
doc_titles = [chunk.doc_title for chunk in chunks]
sources = [chunk.source for chunk in chunks]
urls = [chunk.url for chunk in chunks]
dates = [chunk.date for chunk in chunks]

store.add(chunk_ids, vectors, contents, doc_ids, doc_titles, sources, urls, dates)
```

- [ ] **Step 3: Verify compilation**

Run: `python -c "from backend.app.rag.indexing.vector_store import VectorStore; from backend.app.services.index_service import IndexService; print('OK')"`

- [ ] **Step 4: Commit**

```bash
git add backend/app/rag/indexing/vector_store.py backend/app/services/index_service.py
git commit -m "feat: store doc_title, source, url, date in VectorStore metadata"
```

---

### Task 3: Retriever + KeywordRetriever + RagService

**Files:**
- Modify: `backend/app/rag/retrieval/retriever.py`
- Modify: `backend/app/rag/retrieval/keyword_retriever.py`
- Modify: `backend/app/services/rag_service.py`

- [ ] **Step 1: Populate SearchResult in Retriever.hydrate_results()**

Change the SearchResult construction:
```python
SearchResult(
    chunk_id=meta.get("chunk_id", ""),
    doc_id=meta.get("doc_id", ""),
    content=meta.get("content", ""),
    score=score,
    doc_title=meta.get("doc_title", ""),
    source=meta.get("source", ""),
)
```

- [ ] **Step 2: Add metadata to KeywordRetriever's _ChunkRecord**

Add fields to `_ChunkRecord`:
```python
@dataclass
class _ChunkRecord:
    internal_id: int
    chunk_id: str
    doc_id: str
    content: str
    doc_title: str = ""
    source: str = ""
    url: str = ""
    date: str = ""
```

Update the constructor to read from metadata:
```python
self._records.append(
    _ChunkRecord(
        internal_id=int(internal_id),
        chunk_id=meta.get("chunk_id", ""),
        doc_id=meta.get("doc_id", ""),
        content=content,
        doc_title=meta.get("doc_title", ""),
        source=meta.get("source", ""),
        url=meta.get("url", ""),
        date=meta.get("date", ""),
    )
)
```

Update `retrieve()` SearchResult construction:
```python
SearchResult(
    chunk_id=rec.chunk_id,
    doc_id=rec.doc_id,
    content=rec.content,
    score=norm,
    doc_title=rec.doc_title,
    source=rec.source,
)
```

- [ ] **Step 3: Update RagService._build_references()**

Add new fields to the output dict:
```python
{
    "index": idx,
    "chunk_id": result.chunk_id,
    "doc_id": result.doc_id,
    "score": result.score,
    "excerpt": excerpt,
    "doc_title": result.doc_title,
    "source": result.source,
}
```

- [ ] **Step 4: Verify compilation**

Run: `python -c "from backend.app.rag.retrieval.retriever import SearchResult; from backend.app.rag.retrieval.keyword_retriever import KeywordRetriever; from backend.app.services.rag_service import RagService; print('OK')"`

- [ ] **Step 5: Commit**

```bash
git add backend/app/rag/retrieval/retriever.py backend/app/rag/retrieval/keyword_retriever.py backend/app/services/rag_service.py
git commit -m "feat: propagate doc metadata to SearchResult and references"
```

---

### Task 4: Frontend Type + Display

**Files:**
- Modify: `frontend/src/types/api.ts`
- Modify: `frontend/src/components/ReferenceList.vue`

- [ ] **Step 1: Add fields to ReferenceItem**

```typescript
export interface ReferenceItem {
  index: number
  chunk_id: string
  doc_id: string
  score: number
  excerpt: string
  doc_title?: string
  source?: string
  url?: string
  date?: string
}
```

- [ ] **Step 2: Update ReferenceList.vue template**

Replace the bottom of each card (`.reference-id` line) with a source info row:

```html
        <div class="reference-source">
          <span v-if="item.doc_title" class="reference-source__title">{{ item.doc_title }}</span>
          <span class="reference-source__meta">
            <span v-if="item.source">{{ item.source }}</span>
            <span v-if="item.date">{{ item.date }}</span>
            <a
              v-if="item.url"
              :href="item.url"
              target="_blank"
              rel="noopener noreferrer"
              class="reference-source__link"
            >&nearr; 查看原文</a>
          </span>
        </div>
```

- [ ] **Step 3: Add source row styles (scoped)**

```css
.reference-source {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--graphite);
  display: grid;
  gap: 4px;
}

.reference-source__title {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--ink);
  line-height: 1.4;
}

.reference-source__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 0.75rem;
  color: var(--muted);
}

.reference-source__link {
  color: var(--cinnabar);
  text-decoration: none;
  font-weight: 500;
}
.reference-source__link:hover {
  text-decoration: underline;
}
```

- [ ] **Step 4: Remove old `.reference-id` line from template** (the `chunk: {{ item.chunk_id }}` line)

- [ ] **Step 5: Verify build**

```bash
cd frontend && npm run build 2>&1 | tail -5
```
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add frontend/src/types/api.ts frontend/src/components/ReferenceList.vue
git commit -m "feat: display doc origin (title, source, url, date) in reference cards"
```

---

### Task 5: Rebuild Index and Verify

- [ ] **Step 1: Rechunk and rebuild index**

```bash
python -m backend.scripts.chunk_data
python -m backend.scripts.build_index
```

- [ ] **Step 2: Run all backend tests**

```bash
python -m pytest backend/tests/ -q
```
Expected: ~29 passed

- [ ] **Step 3: Verify frontend**

```bash
cd frontend && npm run build 2>&1 | tail -5 && npx vitest run 2>&1 | tail -5
```
Expected: Build OK, 5 tests passed

- [ ] **Step 4: Final commit and push**

```bash
git add -A
git commit -m "chore: rebuild index with doc metadata, final verification"
git push
```
