# project_X Ver 2.0

仓库已完成 Ver 2.0 优化，当前正式入口分为：

- `backend/`：FastAPI 后端
- `frontend/`：Vue 3 + Vite 前端
- `docs/`：方案与设计文档

根目录旧版 `main.py`、`src/`、`config/`、`data/` 和旧 `requirements.txt` 已退役，不再保留兼容启动方式。

## 启动方式

### 后端

```powershell
pip install -r backend/requirements.txt
uvicorn backend.main:app --host 127.0.0.1 --port 8050
python backend/main.py
```

后端 `http://127.0.0.1:8050/docs` 作为接口调试入口保留。

常用脚本入口：

```powershell
python -m backend.scripts.collect_data
python -m backend.scripts.clean_data
python -m backend.scripts.chunk_data
python -m backend.scripts.build_index
python -m backend.scripts.run_evaluation
```

### 前端

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 3001
```

主要人工交互入口：`http://127.0.0.1:3001`

当前前端已提供以下可直接操作的页面：

- `/`
- `/qa`
- `/summary`

## 文档

- 重构方案：[docs/ver2.0/项目重构书.md](docs/ver2.0/项目重构书.md)
- 历史方案：[docs/ver1.0](docs/ver1.0)
