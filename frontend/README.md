# Frontend

Ver 2.0 前端采用 `Vue 3 + Vite + TypeScript`。

## 安装

```powershell
cd frontend
npm install
```

## 启动

```powershell
npm run dev -- --host 127.0.0.1 --port 3001
```

主要人工交互入口：`http://127.0.0.1:3001`

## 构建

```powershell
npm run build
```

当前第三轮已接通真实交互页面：

- `/`
- `/qa`
- `/summary`
- `/search`

- `/qa`：问题输入、参数控制、回答展示、参考片段展示
- `/summary`：长文本输入、摘要结果展示
- `/search`：检索问题输入、Top-K 控制、参考片段展示

后端 `http://127.0.0.1:8050/docs` 继续作为接口调试入口保留。
