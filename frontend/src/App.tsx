import { Routes, Route, Link } from "react-router-dom";
import { ProjectList } from "./pages/ProjectList";
import { ProjectDetail } from "./pages/ProjectDetail";
import { WorkflowEditor } from "./pages/WorkflowEditor";
import { TaskCreate } from "./pages/TaskCreate";
import { TaskTrace } from "./pages/TaskTrace";

export default function App() {
  return (
    <div style={{ maxWidth: 1200, margin: "0 auto", padding: 20 }}>
      <nav style={{ marginBottom: 24, display: "flex", gap: 16 }}>
        <Link to="/">Projects</Link>
      </nav>
      <Routes>
        <Route path="/" element={<ProjectList />} />
        <Route path="/projects/:id" element={<ProjectDetail />} />
        <Route path="/projects/:id/workflows/new" element={<WorkflowEditor />} />
        <Route path="/projects/:id/tasks/new" element={<TaskCreate />} />
        <Route path="/tasks/:id/trace" element={<TaskTrace />} />
      </Routes>
    </div>
  );
}
