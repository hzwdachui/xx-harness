const BASE = "/api";

async function request(path: string, options?: RequestInit) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  projects: {
    list: () => request("/projects/"),
    create: (data: { name: string; description?: string; boundary?: string }) =>
      request("/projects/", { method: "POST", body: JSON.stringify(data) }),
    get: (id: number) => request(`/projects/${id}`),
    delete: (id: number) => request(`/projects/${id}`, { method: "DELETE" }),
    addRepo: (projectId: number, data: { name: string; git_url: string; default_branch?: string }) =>
      request(`/projects/${projectId}/repos`, { method: "POST", body: JSON.stringify(data) }),
    listRepos: (projectId: number) => request(`/projects/${projectId}/repos`),
  },
  workflows: {
    listByProject: (projectId: number) => request(`/workflows/project/${projectId}`),
    create: (data: any) =>
      request("/workflows/", { method: "POST", body: JSON.stringify(data) }),
    delete: (id: number) => request(`/workflows/${id}`, { method: "DELETE" }),
  },
  agents: {
    list: () => request("/agents/"),
  },
  tasks: {
    listByProject: (projectId: number, status?: string) =>
      request(`/tasks/project/${projectId}${status ? `?status=${status}` : ""}`),
    create: (data: any) => request("/tasks/", { method: "POST", body: JSON.stringify(data) }),
    get: (id: number) => request(`/tasks/${id}`),
    start: (id: number) => request(`/tasks/${id}/start`, { method: "POST" }),
    trace: (id: number) => request(`/tasks/${id}/trace`),
  },
  issues: {
    listByProject: (projectId: number) => request(`/issues/project/${projectId}`),
    create: (data: any) =>
      request("/issues/", { method: "POST", body: JSON.stringify(data) }),
  },
};
