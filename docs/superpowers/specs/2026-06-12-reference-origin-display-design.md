# 批注来源追溯 — 设计规格

> 日期：2026-06-12  
> 目标：点击批注来源卡片，显示 chunk 所属文档的标题、来源类型、日期和原文链接

## 数据链路修复

全链路 8 处改动，将文档元数据（title, source, url, date）从 Document 传递到前端 ReferenceItem。

```
Document { title, source, url, date }
  → Chunk { +doc_title, +source, +url, +date }        # models.py
  → Chunker 传递元数据                                   # chunker.py
  → VectorStore metadata 存入                           # vector_store.py
  → SearchResult 填充                                   # retriever.py
  → _build_references 输出                              # rag_service.py
  → ReferenceItem 新增字段                               # api.ts  
  → ReferenceList 展示                                  # ReferenceList.vue
  → 卡片展开交互
```

## 各阶段改动

### 1. `backend/app/rag/data/models.py`
Chunk dataclass 新增：`doc_title: str = ""`, `source: str = ""`, `url: str = ""`, `date: str = ""`

### 2. `backend/app/rag/data/chunker.py`
`chunk()` 方法构造 Chunk 时传入文档元数据：
```python
doc_title=doc.title, source=doc.source, url=doc.url or "", date=doc.date or ""
```

### 3. `backend/app/rag/indexing/vector_store.py`
`add()` 方法签名扩展，metadata 存入 `doc_title`, `source`, `url`, `date`

### 4. `backend/app/rag/retrieval/retriever.py`
`hydrate_results()` 从 metadata 读取并填充 SearchResult 的 `doc_title` 和 `source`

### 5. `backend/app/rag/retrieval/keyword_retriever.py`
KeywordRetriever 的 `_ChunkRecord` 和 `retrieve()` 也需要带 title/source/url/date

### 6. `backend/app/services/rag_service.py`
`_build_references()` 输出新增字段：
```python
{"doc_title": result.doc_title, "source": result.source, "url": result.url, "date": result.date}
```

### 7. `frontend/src/types/api.ts`
ReferenceItem 接口新增：`doc_title?: string`, `source?: string`, `url?: string`, `date?: string`

### 8. `frontend/src/components/ReferenceList.vue`
卡片底部改为显示来源信息行：
```
简略资料 · arxiv · 2024-03-15 · ↗ 查看原文
```
有 url 时显示可点击链接，无 url 时只显示来源类型和日期。chunk_id 放到 tooltip 或折叠。

### 9. `backend/scripts/build_index.py` / `backend/app/services/index_service.py`
`build_index()` 中调用 `store.add()` 时传入新增字段。

## 数据量影响

每个 chunk metadata 增加约 150 bytes（title + source + url + date），108 chunks 约 16KB。

## 约束

- 重建索引：metadata 格式变化，需要运行 `python -m backend.scripts.chunk_data` + `python -m backend.scripts.build_index`
- 向后兼容：旧索引无新字段时，前端显示 `--` 占位
- 测试更新：test_data_pipeline, test_rag_service, test_api, test_keyword_retriever
