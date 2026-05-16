# xx-harness

AI Agent 编排框架 — 围绕 Claude Code 的约束、工作流和学习系统。

## 技术栈

- Python 3.12+ / FastAPI / SQLite (adapter 模式)
- React 18 + TypeScript / Vite
- 先用 venv 激活：`source venv/bin/activate`

## 项目结构

```
src/
├── db/       # 数据层：adapter 接口 + SQLite + schema + repositories
├── engine/   # 编排层：workspace + DAG + context + runner + orchestrator
├── web/      # Web 层：FastAPI app + routes + websocket
├── models.py # 数据类
├── config.py # 配置
frontend/     # React SPA
tests/        # pytest
```

## 运行

```bash
python run.py              # 后端 :8720
cd frontend && npm run dev # 前端 :5173（代理到后端）
pytest tests/ -v           # 29 个测试
```

## 代码约定

- 枚举用 `TaskStatus.RUNNING.value` 不直接用字符串
- 数据层走 adapter 接口，不硬编码 SQLite
- 路由用 `from src.web.routes._errors import not_found` 统一 404
- 新增包用 `from __future__ import annotations`（兼容 3.12-）
