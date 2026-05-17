# xx-harness

围绕 Claude Code 构建的 AI Agent 编排、约束和学习系统。核心理念来自 Harness Engineering：基础设施才是瓶颈，不是模型智能。

## 快速开始

```bash
# 安装
python3.12 -m venv venv && source venv/bin/activate
pip install -e ".[dev]"

# 启动 Web 后端
python run.py

# 启动前端
cd frontend && npm run dev
```

Web 管理界面 → `http://localhost:5173` | API 文档 → `http://localhost:8720/docs`

## 架构

```
Claude Code 对话 ──┐
                   ├──→ 编排引擎 (DAG) ──→ Claude Code 进程
Web 管理界面 ──────┘         │
                          数据层 (Adapter → SQLite)
```

- **管理平面**：Web 配置项目、约束、Agent、工作流、任务
- **执行平面**：编排引擎按 DAG 调度 Claude Code 进程，git worktree 隔离工作空间
- **数据层**：Adapter 模式，当前 SQLite，可切换 PostgreSQL/MySQL

## 核心概念

| 概念 | 说明 |
|------|------|
| 项目 | 顶层容器，关联多个仓库，定义边界和约束 |
| 工作流 | DAG 节点编排，可配置审查门和 skill |
| 任务 | exploration / development / testing / deployment / custom |
| Agent | 可注册任意 agent，内置 5 个角色（研究员/规划师/执行者/审查者/测试者），每个 agent 可配置自然语言 skills |
| 学习 | KnownIssue + ConstraintRule，项目级/全局级 |
