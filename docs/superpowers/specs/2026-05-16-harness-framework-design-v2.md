# xx-harness 框架设计 v2

## 1. 概述

xx-harness 是一套增强 Claude Code 的约束、编排和学习系统。核心理念：瓶颈在基础设施，不在模型智能。

**两个入口，一套编排引擎：**

```
Claude Code 对话 ──┐
                   ├──→ 编排引擎 (Python) ──→ Claude Code 进程
Web 管理界面 ──────┘         │
                          SQLite (唯一状态源)
```

## 2. 核心架构

```
┌──────────────┐     ┌──────────────┐
│ Claude Code  │     │   Web 前端    │
│ (对话触发)    │     │ (管理+触发)   │
└──────┬───────┘     └──────┬───────┘
       │                    │
       │              ┌─────▼─────┐
       │              │  Web 后端  │
       │              │ (FastAPI)  │
       │              └─────┬─────┘
       │                    │
       └──────────┬─────────┘
                  │
          ┌───────▼───────┐
          │   编排引擎      │
          │   (Python)    │
          │ · DAG 调度     │
          │ · 上下文组装    │
          │ · 审查门控制    │
          └───────┬───────┘
                  │
  ┌───────────────┼───────────────┐
  ▼               ▼               ▼
CC进程1         CC进程2         CC进程N
(任意agent)     (任意agent)     (任意agent)
  │               │               │
  └───────────────┼───────────────┘
                  │
          ┌───────▼───────┐
          │    SQLite      │
          │ · 项目配置      │
          │ · Agent 定义    │
          │ · 工作流 DAG    │
          │ · 任务状态       │
          │ · 失败案例库     │
          │ · 会话记录       │
          └────────────────┘
```

**唯一编排路径：** 两种入口都调用编排引擎，引擎按 DAG 串行或并行启动 Claude Code 进程，上下文全部来自 SQLite。

## 3. 技术选型

| 层 | 技术 |
|----|------|
| 编排引擎 | Python |
| Web 后端 | Python + FastAPI |
| Web 前端 | TypeScript + React |
| 数据库 | SQLite（后续可迁移到 MySQL/PostgreSQL） |
| Agent 引擎 | Claude Code |

## 4. 核心数据模型

```
Project ──1:N──> Workflow
  │                │
  │                └──1:N──> WorkflowNode ──1:1──> AgentTemplate
  │
  ├──1:N──> ConstraintRule (项目级约束)
  ├──1:N──> Task
  │            │
  │            ├── task_type: exploration / development / testing / deployment / custom
  │            ├──1:N──> TaskNodeRun
  │            └──1:N──> TaskSplit
  │
  └──1:N──> KnownIssue
```

### 4.0 任务类型

| 类型 | 说明 | 默认工作流 |
|------|------|-----------|
| `exploration` | 代码分析、技术调研、依赖梳理 | researcher → [summary] |
| `development` | 功能开发、重构 | researcher → planner → [review?] → executor(s) → tester → [review?] |
| `testing` | 单测/集成/E2E 测试编写或运行 | researcher → tester → [review?] |
| `deployment` | 部署、发布 | tester → deployer |
| `custom` | 用户自定义 | 创建时手动选择或定义工作流 |

| 实体 | 关键字段 | 说明 |
|------|---------|------|
| Project | name, repo_path, description, boundary | 项目是顶层容器，定义边界 |
| Workflow | project_id, name, dag(json) | 项目可配多个工作流 |
| WorkflowNode | workflow_id, agent_id, depends_on, review_gate(bool), context(json) | DAG 节点 |
| AgentTemplate | name, role, system_prompt, tools(json) | 可复用的 Agent 角色定义 |
| ConstraintRule | project_id, rule_type, content, level(global/project) | 约束规则，支持全局和项目级 |

### 4.2 任务与执行

| 实体 | 关键字段 | 说明 |
|------|---------|------|
| Task | project_id, task_type, workflow_id, title, description, status, complexity | 一次任务，类型决定默认工作流 |
| TaskSplit | task_id, parent_split_id, description, focus_path, status | 任务拆分树 |
| TaskNodeRun | task_id, node_id, split_id, agent_id, status, cc_session_id, result | 每个 DAG 节点的执行记录 |

### 4.3 学习

| 实体 | 关键字段 | 说明 |
|------|---------|------|
| KnownIssue | project_id, error_pattern, root_cause, rule_update, level | 失败案例库 |
| AgentSession | task_id, node_run_id, session_log, summary | Claude Code 会话记录 |

## 5. DAG 编排模型

### 5.1 节点类型

每个节点指定一个 Agent 角色，包含：
- **agent**：使用的 Agent 模板
- **depends_on**：依赖的前置节点（决定并行/串行）
- **review_gate**：节点完成后是否需要人工审查
- **context**：注入的额外上下文（关注路径、特定规则等）

### 5.2 不同类型的工作流示例

**开发任务 (development)：**
```
               ┌──────────┐
               │ 研究员    │
               └────┬─────┘
                    │
               ┌────▼─────┐
               │ 规划师    │
               └────┬─────┘
                    │
               [审查门: on]
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
  ┌──────────┐ ┌──────────┐ ┌──────────┐
  │ 执行者A  │ │ 执行者B  │ │ 执行者C  │
  └────┬─────┘ └────┬─────┘ └────┬─────┘
       │            │            │
       └────────────┼────────────┘
                    │
               ┌────▼─────┐
               │ 测试者    │
               └────┬─────┘
                    │
               [审查门: on]
                    │
               ┌────▼─────┐
               │ 部署者    │ (可选)
               └──────────┘
```

**探索任务 (exploration)：**
```
  ┌──────────┐
  │ 研究员    │
  └────┬─────┘
       │
  ┌────▼─────┐
  │ 分析报告   │ ← 产出到 SQLite / 供对话查看
  └──────────┘
```

**单测试任务 (testing)：**
```
  ┌──────────┐     ┌──────────┐
  │ 研究员    │────→│ 测试者    │
  └──────────┘     └────┬─────┘
                        │
                   [审查门: on]
```

### 5.3 编排引擎行为

```
function run_task(task_id, trigger_source):
    workflow = load_workflow(task_id)
    dag = parse_dag(workflow)
    
    for each ready_node in dag.ready_nodes():  # 无未完成依赖的节点
        batch = group_parallel(ready_node)     # 无依赖关系的并行执行
        for each node in batch:
            ctx = assemble_context(node, task_id)  # SQLite 查上下文
            result = start_claude_code(node.agent, ctx)
            save_to_sqlite(result)
        
        for each node in batch:
            if node.review_gate:
                wait_for_human(node)
    
    if trigger_source == "web":
        notify_user(task_id, "complete")
```

## 6. 上下文传递

每个 Claude Code 进程启动时，编排引擎组装三层上下文，全部来自 SQLite + 文件系统：

| 层级 | 内容 | 来源 |
|------|------|------|
| Tier 1 常驻 | 项目 CLAUDE.md + 当前 task 信息 + DAG 位置 | project + task 表 |
| Tier 2 节点注入 | 上游节点产物 + 相关失败案例 + 约束规则 | task_node_run + known_issue + constraint_rule 表 |
| Tier 3 可查询 | 全量历史会话、设计文档 | agent_session 表 + 仓库文件 |

## 7. 学习循环

```
Agent 失败 → 记录 KnownIssue
                  │
     ┌────────────┼────────────┐
     ▼            ▼            ▼
  简单错误     模式性错误    结构性错误
  更新规则     新增 Linter    更新约束
                  │
          团队判断是否通用化 → 提升 level=global
```

## 8. 两个入口

| | Claude Code 对话 | Web 界面 |
|---|---|---|
| 触发方式 | 对话中自然语言 | 点击"开始任务" |
| 编排路径 | 通过 MCP/bash 调编排引擎 | Web 后端调编排引擎 |
| 编排引擎 | 同一个 | 同一个 |
| 上下文 | 同一套 SQLite | 同一套 SQLite |
| 进度查看 | 对话内 | Web 实时 trace |
| 审查确认 | 对话内 | Web 页面 |

## 9. 工作流选择

- 项目可配置多个 workflow
- 创建 task 时，系统根据 **task_type** + **complexity** 自动推荐 workflow
- task_type 有默认映射（探索→exploration 流程，开发→development 流程，测试→testing 流程）
- 开发者可强制指定不同 workflow
- 项目可为每种 task_type 定义覆盖的默认 workflow

## 10. MVP 范围

- SQLite 数据库 + 核心表
- 编排引擎（Python）：DAG 解析 → Claude Code 进程管理 → 上下文组装
- 两种入口打通：Claude Code 对话 + Web 后端
- 内置 Agent 模板：研究员、规划师、执行者、审查者、测试者
- 简单 Web 界面：项目配置、工作流编辑、创建 task（支持不同 task_type）、查看 trace
- 项目级学习：KnownIssue 记录 + ConstraintRule 更新
- 审查门（可配置开关）
- 任务类型：exploration、development、testing，各自默认工作流

## 11. 后续版本

**V2**：通用级学习、多任务并行编排、自定义 Linter、Agent 模板热更新
**V3**：无人值守调度、熵管理、浏览器自动化测试、DAG 可视化编辑器
