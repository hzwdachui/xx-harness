---
name: xx-harness
description: Use when the user asks to create or manage AI agent orchestration projects, workflows, tasks, or agents in xx-harness. Also use when the user says "create a task", "start a workflow", "check trace", "manage agents", or references the harness API directly.
---

# xx-harness

AI Agent 编排框架 — 通过 API 管理 project → workflow → task，由 orchestrator 调度 Claude Code agent 执行。

## 启动

```bash
cd /Users/wangziqi/Work/xx-harness && source venv/bin/activate && python run.py &
```
后端在 `http://localhost:8720`。前端 `http://localhost:5173` 按需启动。

## 数据模型关系

```
Project ──1:N──> Workflow ──1:N──> WorkflowNode (agent_id, depends_on[], review_gate, skill)
Project ──1:N──> Task ──1:N──> TaskNodeRun (node_id, status, result_json)
            Agent (name, role, system_prompt, tools_json)
```

Workflow 定义 DAG 结构，Task 是 Workflow 的一次执行实例，TaskNodeRun 记录每个 node 的执行结果。

Orchestrator 调度逻辑：读取 task → 找到 workflow → 按 depends_on 拓扑排序 → 逐个节点调用 `claude -p --output-format json` 执行。

## API 速查

所有 API base: `http://localhost:8720/api`

### Projects
```bash
curl -s http://localhost:8720/api/projects/                          # GET 列表
curl -s -X POST http://localhost:8720/api/projects/ \                # POST 创建
  -H "Content-Type: application/json" \
  -d '{"name":"my-project","description":"描述"}'
curl -s -X PUT http://localhost:8720/api/projects/1 \                # PUT 更新
  -H "Content-Type: application/json" \
  -d '{"name":"new-name","description":"new desc"}'
curl -s -X DELETE http://localhost:8720/api/projects/1               # DELETE
```

### Agents — 注册可用的 AI agent
```bash
curl -s http://localhost:8720/api/agents/                            # GET 列表
curl -s -X POST http://localhost:8720/api/agents/ \                  # POST 创建
  -H "Content-Type: application/json" \
  -d '{"name":"researcher","role":"researcher","system_prompt":"探索代码库，分析结构，输出调研报告"}'
curl -s -X PUT http://localhost:8720/api/agents/1 \                  # PUT 更新
  -H "Content-Type: application/json" \
  -d '{"system_prompt":"新的 prompt"}'
curl -s -X DELETE http://localhost:8720/api/agents/1                 # DELETE
```

Agent 字段: `name`(唯一), `role`, `system_prompt`, `tools_json`(默认"[]")

### Workflows — 定义 DAG 编排结构
```bash
curl -s http://localhost:8720/api/workflows/project/1                # GET 某项目下所有
curl -s -X POST http://localhost:8720/api/workflows/ \               # POST 创建
  -H "Content-Type: application/json" \
  -d '{
    "name":"dev-flow","task_type":"development","project_id":1,
    "nodes":[
      {"agent_name":"researcher","depends_on":[],"review_gate":false,"skill":""},
      {"agent_name":"planner","depends_on":[0],"review_gate":true,"skill":"superpowers:writing-plans"},
      {"agent_name":"executor","depends_on":[1],"review_gate":false,"skill":""}
    ]
  }'
curl -s -X PUT http://localhost:8720/api/workflows/1 \               # PUT 更新
  ...same body as POST...
curl -s -X DELETE http://localhost:8720/api/workflows/1              # DELETE
```

Node 字段: `agent_name`(必填，对应 agents 中的 name), `depends_on`(0-based 索引数组), `review_gate`, `skill`, `skill_args`, `context_json`

task_type 枚举: `development`, `exploration`, `testing`, `deployment`, `custom`

### Tasks — 执行实例
```bash
curl -s http://localhost:8720/api/tasks/project/1                    # GET 某项目下所有
curl -s "http://localhost:8720/api/tasks/project/1?status=running"   # 按状态过滤
curl -s -X POST http://localhost:8720/api/tasks/ \                   # POST 创建
  -H "Content-Type: application/json" \
  -d '{"project_id":1,"title":"修复登录 bug","task_type":"development","description":"详细描述","workflow_id":1}'
curl -s -X POST http://localhost:8720/api/tasks/1/start              # POST 启动（触发 orchestrator）
curl -s http://localhost:8720/api/tasks/1                            # GET 详情（含 node_runs）
curl -s http://localhost:8720/api/tasks/1/trace                      # GET trace（轻量轮询用）
```

Task 状态: `pending` → `running` → `completed` / `failed`
NodeRun 状态: `pending` → `running` → `done` / `failed` / `waiting_review`

### Version
```bash
curl -s http://localhost:8720/api/version
```

## 典型使用流程

### 1. 快速执行一个开发任务
```
用户: "帮我创建一个 task 来修复登录 bug"

1. 确认 project 存在: GET /api/projects/
2. 确认 workflow 存在: GET /api/workflows/project/{id}
3. 创建 task: POST /api/tasks/ {"project_id":1,"title":"修复登录 bug","task_type":"development","workflow_id":1}
4. 启动: POST /api/tasks/{id}/start
5. 监控: GET /api/tasks/{id}/trace (每 5-10s 轮询直到 status=completed/failed)
6. 报告结果给用户
```

### 2. 创建新项目完整流程
```
1. POST /api/projects/ 创建项目
2. POST /api/agents/ 注册所需 agents（如果默认5个不够）
3. POST /api/workflows/ 定义 DAG 结构
4. POST /api/tasks/ + POST /api/tasks/{id}/start 创建并启动
5. 轮询 trace 直到完成
```

### 3. 查看执行结果
```
GET /api/tasks/{id} → 看 task.status + node_runs[].result_json
GET /api/tasks/{id}/trace → 轻量版，适合轮询
```

node_runs[].result_json 包含:
- `output`: claude CLI 的 JSON 输出（含 result 字段为实际文本）
- `exit_code`: 0=成功
- `stderr`: 错误信息
- `error`: 异常信息（如 timeout）

## 常用组合

**创建 task 并等待完成**：
```bash
# 创建
TID=$(curl -s -X POST http://localhost:8720/api/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"project_id":1,"title":"你的标题","task_type":"development","workflow_id":1}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# 启动
curl -s -X POST "http://localhost:8720/api/tasks/$TID/start"

# 等待完成
until [ "$(curl -s http://localhost:8720/api/tasks/$TID | python3 -c "import sys,json; print(json.load(sys.stdin)['task']['status'])")" != "running" ]; do sleep 10; done

# 查看结果
curl -s "http://localhost:8720/api/tasks/$TID" | python3 -c "
import sys,json; d=json.load(sys.stdin)
print(f'Status: {d[\"task\"][\"status\"]}')
for r in d['node_runs']:
    rj=r.get('result_json') or {}
    print(f'Node {r[\"node_id\"]}: {r[\"status\"]}')
    out=str(rj.get('output',''))
    if out:
        import json; print(json.loads(out).get('result','')[:500])
"
```

## 注意事项

- `workflow_id` 可选，不传时 orchestrator 按 task_type 自动匹配默认 workflow
- `depends_on` 是 0-based 索引，[0] 表示依赖第一个 node
- `review_gate=true` 的 node 完成后状态变为 `waiting_review`，需人工确认
- orchestrator 以 BackgroundTasks 运行，如果后端 reload 会中断
- Claude Code CLI 必须在 PATH 中（`claude` 命令可用）
- 当前 project_id=1 是 "xx-harness" 项目
