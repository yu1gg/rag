# Backend

Ver 2.0 后端使用 `FastAPI` 提供正式服务入口，并承接数据准备、索引构建与评估脚本。

## 安装

```powershell
pip install -r backend/requirements.txt
```

## 配置

1. 复制 `backend/.env.example` 为 `backend/.env`
2. 填写 `OPENAI_API_KEY`

## 启动

```powershell
uvicorn backend.main:app --host 127.0.0.1 --port 8050
python backend/main.py
```

接口文档默认位于 `http://127.0.0.1:8050/docs`，用于接口调试和联调。

## 脚本

```powershell
python -m backend.scripts.collect_data
python -m backend.scripts.clean_data
python -m backend.scripts.chunk_data
python -m backend.scripts.build_index
python -m backend.scripts.run_evaluation
```

## 说明

- `GET /api/v1/health`、`/datasets/stats`、`/index/status`、`/evaluations/latest` 可直接用于状态检查。
- `rag/qa` 与 `rag/summary` 仍需要有效的 `OPENAI_API_KEY`。
- 直接运行 `python backend/main.py` 时，`main()` 会复用 `backend/.env` 里的 `APP_HOST` 与 `APP_PORT`，便于在 VSCode 中按文件启动后端。
- `build_index` 在本地缺少嵌入模型时会退化到离线哈希向量模式。
- `run_evaluation` 在缺少 `OPENAI_API_KEY` 时会生成本地 fallback 报告；如果已经配置密钥但模型调用失败，会显式返回错误，避免把真实故障伪装成评估成功。
