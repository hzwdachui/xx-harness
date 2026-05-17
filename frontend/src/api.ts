const BASE = "/api";

async function request(path: string, options?: RequestInit) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `API error: ${res.status}`);
  }
  return res.json();
}

/* ===== Types ===== */

export type TaskStatus = "pending" | "queued" | "running" | "completed" | "failed" | "cancelled" | "waiting_review" | "plan_ready" | "plan_approved" | "executing" | "code_review";

export const S = {
  PENDING: "pending", QUEUED: "queued", RUNNING: "running",
  COMPLETED: "completed", FAILED: "failed", CANCELLED: "cancelled",
  WAITING_REVIEW: "waiting_review", PLAN_READY: "plan_ready",
  PLAN_APPROVED: "plan_approved", EXECUTING: "executing", CODE_REVIEW: "code_review",
} as const;

export interface Project {
  id: number; name: string; description?: string; boundary?: string; created_at?: string;
}

export interface Agent {
  id: number; name: string; role: string; system_prompt: string; skills: string;
}

export interface NodeDef {
  agent_name: string; depends_on: number[]; review_gate: boolean; skill: string;
  skill_args?: string; context_json?: Record<string, unknown>;
}

export interface WorkflowItem {
  workflow: { id: number; project_id: number; name: string; task_type: string };
  nodes: { id: number; workflow_id: number; agent_id: number; depends_on: number[];
           review_gate: boolean; skill: string; skill_args: string;
           context_json: Record<string, unknown>; position: number }[];
}

export interface Task {
  id: number; project_id: number; task_type: string; workflow_id: number | null;
  title: string; description: string; status: TaskStatus; complexity: string; created_at: string;
}

export interface TraceRun {
  node_id: string; agent_name?: string; status: TaskStatus; result?: Record<string, unknown>;
}

export interface TraceData {
  task_id: number; runs: TraceRun[];
}

export interface TaskDetail {
  task: Task;
  node_runs: { id: number; task_id: number; node_id: number; agent_id: number;
               status: TaskStatus; result_json: Record<string, unknown>;
               started_at: string | null; finished_at: string | null; }[];
}

export interface Issue {
  id: number; project_id: number; error_pattern: string; root_cause: string;
  rule_update?: string; level: string; created_at?: string;
}

/* ===== API client ===== */

export const api = {
  projects: {
    list: (): Promise<Project[]> => request("/projects/"),
    create: (data: { name: string; description?: string; boundary?: string }): Promise<{ id: number }> =>
      request("/projects/", { method: "POST", body: JSON.stringify(data) }),
    get: (id: number): Promise<Project> => request(`/projects/${id}`),
    update: (id: number, data: { name?: string; description?: string; boundary?: string }): Promise<Project> =>
      request(`/projects/${id}`, { method: "PUT", body: JSON.stringify(data) }),
    delete: (id: number): Promise<{ ok: boolean }> => request(`/projects/${id}`, { method: "DELETE" }),
    addRepo: (projectId: number, data: { name: string; git_url: string; default_branch?: string }) =>
      request(`/projects/${projectId}/repos`, { method: "POST", body: JSON.stringify(data) }),
    listRepos: (projectId: number) => request(`/projects/${projectId}/repos`),
  },
  workflows: {
    listByProject: (projectId: number): Promise<WorkflowItem[]> =>
      request(`/workflows/project/${projectId}`),
    create: (data: { name: string; task_type: string; project_id: number;
                     nodes: { agent_name: string; depends_on: number[];
                               review_gate: boolean; skill: string }[] }): Promise<{ id: number }> =>
      request("/workflows/", { method: "POST", body: JSON.stringify(data) }),
    update: (id: number, data: { name: string; task_type: string; project_id: number;
      nodes: { agent_name: string; depends_on: number[]; review_gate: boolean; skill: string }[] }): Promise<{ id: number }> =>
      request(`/workflows/${id}`, { method: "PUT", body: JSON.stringify(data) }),
    delete: (id: number): Promise<{ ok: boolean }> =>
      request(`/workflows/${id}`, { method: "DELETE" }),
  },
  agents: {
    list: (): Promise<Agent[]> => request("/agents/"),
    create: (data: { name: string; role: string; system_prompt?: string; skills?: string }): Promise<Agent> =>
      request("/agents/", { method: "POST", body: JSON.stringify(data) }),
    update: (id: number, data: { name?: string; role?: string; system_prompt?: string; skills?: string }): Promise<Agent> =>
      request(`/agents/${id}`, { method: "PUT", body: JSON.stringify(data) }),
    delete: (id: number): Promise<{ ok: boolean }> =>
      request(`/agents/${id}`, { method: "DELETE" }),
  },
  tasks: {
    listByProject: (projectId: number, status?: string): Promise<Task[]> =>
      request(`/tasks/project/${projectId}${status ? `?status=${status}` : ""}`),
    create: (data: { project_id: number; title: string; task_type: string;
                     description?: string; workflow_id?: number | null }): Promise<{ id: number }> =>
      request("/tasks/", { method: "POST", body: JSON.stringify(data) }),
    get: (id: number): Promise<TaskDetail> => request(`/tasks/${id}`),
    start: (id: number): Promise<{ ok: boolean; status: string }> =>
      request(`/tasks/${id}/start`, { method: "POST" }),
    cancel: (id: number): Promise<{ ok: boolean; status: string }> =>
      request(`/tasks/${id}/cancel`, { method: "POST" }),
    retry: (id: number): Promise<{ ok: boolean; status: string }> =>
      request(`/tasks/${id}/retry`, { method: "POST" }),
    trace: (id: number): Promise<TraceData> => request(`/tasks/${id}/trace`),
  },
  issues: {
    listByProject: (projectId: number): Promise<Issue[]> =>
      request(`/issues/project/${projectId}`),
    create: (data: { project_id?: number; error_pattern: string;
                     root_cause: string; rule_update?: string; level?: string }) =>
      request("/issues/", { method: "POST", body: JSON.stringify(data) }),
  },
};
