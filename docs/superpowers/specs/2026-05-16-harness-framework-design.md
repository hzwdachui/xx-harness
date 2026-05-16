# xx-harness 框架设计

## 1. 概述

xx-harness 是一个围绕 AI Coding Agent 构建约束机制、反馈回路、工作流控制和持续改进循环的系统工程框架。核心理念来自 Harness Engineering：瓶颈不在模型智能，而在基础设施。

框架分为两个平面：
- **管理平面**：Web 管理后台，负责项目配置、Agent 管理、任务编排和审查
- **执行平面**：Worker 节点，在沙箱中运行 Claude Code 执行具体任务

两个平面通过 PostgreSQL 数据库解耦通信，不要求网络互通。

## 2. 架构

```
┌──────────────────────────┐
│     React 前端            │
└────────────┬─────────────┘
             │ HTTP
┌────────────▼─────────────┐
│  FastAPI 管理后台           │
└────────────┬─────────────┘
             │ DB 连接
             ▼
┌──────────────────────────┐
│      PostgreSQL           │
│  · 管理数据                │
│  · 任务通道（两平面协议）     │
│  · Worker 注册             │
└────┬───────┬───────┬─────┘
     │       │       │
  ┌──▼──┐ ┌──▼──┐ ┌──▼──┐
  │W1   │ │W2   │ │W3   │  Worker 节点
  │(服) │ │(服) │ │(本) │
  └─────┘ └─────┘ └─────┘
```

管理平面和执行平面可任意组合部署：服务器+服务器、服务器+本地、本地+本地。

## 3. 技术选型

| 层 | 技术 |
|----|------|
| 前端 | TypeScript + React |
| 后端 | Python + FastAPI |
| 数据库 | PostgreSQL |
| 任务队列 | 通过 PG 轮询（MVP 不引入 Redis） |
| Agent 引擎 | Claude Code |
| 部署 | Docker Compose |

## 4. 核心数据模型

```
Project ──1:N──> Repository
  │                │
  │                ├──1:1──> RepoHarnessConfig
  │                └──1:N──> Task
  │                              │
  │                              ├──1:1──> TaskPlan
  │                              ├──1:N──> AgentSession
  │                              └──1:N──> Review
  │
  ├──1:1──> ProjectHarnessConfig
  └──M:N──> User
```

### 4.1 管理数据

| 实体 | 关键字段 | 说明 |
|------|---------|------|
| Project | name, team_members | 项目是顶层容器 |
| Repository | project_id, name, git_url, default_branch | 一个项目可关联多个仓库 |
| User | username, role | 团队成员 |
| ProjectHarnessConfig | project_id, review_gates(json), constraints(json) | 项目级跨仓库约束 |
| RepoHarnessConfig | repo_id, agents_md, claude_md, linter_rules(json) | 仓库级 Harness 配置 |

### 4.2 Agent 管理

| 实体 | 说明 |
|------|------|
| AgentTemplate | 系统级 Agent 定义：角色、权限、system prompt |
| WorkflowTemplate | 可选：保存常用的 Agent 编排组合 |

内置 Agent 角色：研究员（只读）、规划师（只读+写计划）、执行者（读写+git）、审查者（只读+linter）。

### 4.3 任务通道（两平面协议）

| 实体 | 关键字段 | 说明 |
|------|---------|------|
| Task | repo_id, title, description, status, priority, worker_id, assigned_agents(json), progress | Worker 通过 status 字段认领任务 |
| TaskPlan | task_id, content(md), status(draft→reviewing→approved→rejected) | 规划产物 |
| AgentSession | task_id, repo_id, session_type, progress_summary, log_ref | 每次 Claude Code 会话记录 |
| Review | task_id, review_type(plan/code), reviewer_id, status, feedback | 人工审查节点 |

### 4.4 学习和约束

| 实体 | 级别 | 说明 |
|------|------|------|
| GlobalRule | 通用 | 跨项目约束规则，所有项目默认继承 |
| ProjectRule | 项目 | 项目特有约束，覆盖/追加通用规则 |
| GlobalKnownIssue | 通用 | 通用失败案例库 |
| ProjectKnownIssue | 项目 | 项目特定失败案例 |

Agent 执行时规则加载顺序：通用规则 → 项目规则覆盖/追加 → 注入到 Agent 会话。

失败案例提升流程：项目级记录 → 团队判断是否通用化 → 提升到 GlobalKnownIssue + GlobalRule。

### 4.5 Worker 注册

| 实体 | 关键字段 | 说明 |
|------|---------|------|
| WorkerRegistry | worker_id, host, capabilities(json), last_heartbeat, status | Worker 注册和心跳 |

## 5. Task 状态机

```
pending → running → plan_ready ─→ plan_approved → executing → code_review
                ↓         ↓              ↓           ↓            ↓
              failed    plan_rejected  failed      failed   changes_requested
                                                              ↓
                                                         executing ← (修复)
```

## 6. 上下文管理（三层体系）

对齐 Harness Engineering 的分层上下文设计：

| 层级 | 加载时机 | 内容 |
|------|---------|------|
| Tier 1 会话常驻 | Worker 每次启动会话自动加载 | 项目级 CLAUDE.md + 仓库级 AGENTS.md + FeatureList |
| Tier 2 按需加载 | 特定 Agent 被调度时注入 | TaskPlan + 同仓库最近 N 次会话摘要 + LinterRules |
| Tier 3 持久化知识库 | Agent 主动查询 | 完整会话历史、设计文档、已知失败案例 |

## 7. 学习循环

```
Agent 执行 → 遇到失败 → Review 被拒
                              ↓
              ┌─ 简单错误 → 更新 AGENTS.md
              ├─ 模式性错误 → 新增 Linter 规则（含修复指令）
              └─ 结构性错误 → 更新 ProjectHarnessConfig 约束
                              ↓
              团队判断是否通用化 → 提升到 GlobalRule
```

每次 Review 拒绝后，系统引导团队将失败转化为 harness 规则。

## 8. Worker 执行流程

```
1. 连 PG，注册 + 心跳
2. SELECT 匹配的 pending 任务
3. UPDATE status = running, worker_id = self
4. SELECT 项目 harness 规则（通用 + 项目级）
5. 组装上下文（Tier 1 + Tier 2）
6. 启动沙箱 → 运行 Claude Code
7. 监控执行，定期 UPDATE progress
8. 执行完毕后 UPDATE status + INSERT session 记录
9. 回到步骤 2
```

## 9. MVP 范围

- 项目/仓库 CRUD
- Harness 基础配置（AGENTS.md / CLAUDE.md 编辑器）
- 4 个内置 Agent 模板（研究员、规划师、执行者、审查者）
- 任务创建 + 规划→审查→执行→审查 工作流
- 单 Worker，PG 轮询
- 项目级学习（ProjectKnownIssue）
- Docker Compose 部署

## 10. 后续版本

**V2**：通用级学习、多 Worker、自定义 Linter、WorkflowTemplate、审查审批 UI

**V3**：无人值守、熵管理 Agent、浏览器自动化测试、完整学习闭环
