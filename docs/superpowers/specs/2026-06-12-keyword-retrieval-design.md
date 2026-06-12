# Keyword Retrieval (BM25) 设计规格

> 日期：2026-06-12  
> 状态：待实现  
> 关联：方案 A — 独立 `KeywordRetriever` 类

## 1. 目标

在现有 FAISS 向量检索基础上，新增基于 BM25 的关键词检索方法。前端 QA 模式增加切换按钮，允许用户每次发送时在"向量检索"和"关键词检索"之间选择。

## 2. 动机

- 向量检索擅长语义匹配，但可能漏掉精确关键词命中
- 关键词检索（BM25）对专有名词、术语、缩写匹配更精准
- 两者互补，由用户根据问题类型自行选择

## 3. 后端设计

### 3.1 新文件：`backend/app/rag/retrieval/keyword_retriever.py`

```python
class KeywordRetriever:
    def __init__(self, metadata: dict[int, dict]):
        # 从 VectorStore.metadata 提取所有 chunk 文本
        # 用 jieba 分词后构建 BM25 索引（rank-bm25）
        # 保存 (internal_id, chunk_id, doc_id, content) 映射

    def retrieve(self, query: str, k: int = 5) -> list[SearchResult]:
        # jieba 分词 query → BM25 打分 → top_k → 包装为 SearchResult
```

要点：
- 构造函数接收 `VectorStore.metadata`（与 Retriever 共享数据源）
- 返回类型与 `Retriever.retrieve()` 一致：`List[SearchResult]`
- jieba 分词同时处理中英文混合文本
- BM25 索引在构造函数中一次性构建（chunk 数量有限，内存开销可控）

### 3.2 修改：`backend/app/services/rag_service.py`

- 新增 `_get_keyword_retriever()` 懒加载方法
- `answer_question(question, top_k, temperature, method="vector")` 新增 `method` 参数
- `_retrieve_results_with_metrics(question, top_k, method="vector")` 新增 `method` 参数
  - `method="vector"`：走现有 `_get_retriever()` 路径
  - `method="keyword"`：走 `_get_keyword_retriever()` 路径
- 后续 rerank / context 构建 / LLM 调用流程不变

### 3.3 修改：`backend/app/schemas/rag.py`

`QaRequest` 新增字段：
```python
method: str = Field(default="vector", pattern="^(vector|keyword)$")
```

### 3.4 修改：`backend/app/api/v1/routes/rag_routes.py`

`/qa` 端点传递 `payload.method` 到 `service.answer_question()`。

### 3.5 新增依赖

`backend/requirements.txt` 新增：
```
rank-bm25
jieba
```

## 4. 前端设计

### 4.1 修改：`frontend/src/types/api.ts`

`QaPayload` 新增：
```ts
method?: 'vector' | 'keyword'
```

### 4.2 修改：`frontend/src/types/chat.ts`

`ChatMessageMeta` 新增：
```ts
method?: string
```

### 4.3 修改：`frontend/src/views/WorkspaceView.vue`

- QA 模式 composer 工具栏新增切换按钮：
  ```
  [向量检索] [关键词检索]    Top-K [5]    Temperature [0.7]
  ```
- 新增 `retrievalMethod` ref，默认 `'vector'`
- `buildQaPayload()` 输出包含 `method`
- `handleSubmit` 的 QA 分支将 method 写入 meta
- Summary 模式下该切换按钮隐藏（summary 不使用检索）

## 5. 数据流

```
用户输入 query + 选择 method
  → QaPayload { question, top_k, temperature, method }
  → POST /api/v1/rag/qa
  → RagService.answer_question(method=...)
    → method="vector"   → Retriever → FAISS search
    → method="keyword"  → KeywordRetriever → BM25 search
  → hydrate_results → List[SearchResult]
  → rerank (可选)
  → build_qa_context
  → LLM 生成答案
  → 返回 { answer, references }
```

## 6. 向后兼容

- `method` 字段默认值为 `"vector"`
- 不传 `method` 时行为与现有一致
- 现有测试和 API 调用者无需修改

## 7. 测试

- `test_keyword_retriever.py`：单元测试 BM25 分词、打分、top_k 截断
- `test_api.py`：新增 `test_qa_keyword_method_success_response`
- 现有测试全部保持通过

## 8. 不做什么

- 不引入混合检索（向量+关键词融合排序）— 当前只需二选一
- 不改 Summary 模式 — summary 不使用检索
- 不改变索引构建流程 — chunk 数据源不变
