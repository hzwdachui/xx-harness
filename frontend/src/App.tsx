import { Routes, Route } from "react-router-dom";
import { ThemeProvider } from "./context/ThemeContext";
import { Layout } from "./components/Layout";
import { ProjectList } from "./pages/ProjectList";
import { ProjectDetail } from "./pages/ProjectDetail";
import { WorkflowEditor } from "./pages/WorkflowEditor";
import { WorkflowDetail } from "./pages/WorkflowDetail";
import { TaskCreate } from "./pages/TaskCreate";
import { TaskTrace } from "./pages/TaskTrace";
import { AgentList } from "./pages/AgentList";
import { Settings } from "./pages/Settings";

export default function App() {
  return (
    <ThemeProvider>
      <Layout>
        <Routes>
          <Route path="/" element={<ProjectList />} />
          <Route path="/projects/:id" element={<ProjectDetail />} />
          <Route path="/projects/:id/workflows/new" element={<WorkflowEditor />} />
          <Route path="/projects/:id/workflows/:workflowId/edit" element={<WorkflowEditor />} />
          <Route path="/projects/:id/workflows/:workflowId" element={<WorkflowDetail />} />
          <Route path="/projects/:id/tasks/new" element={<TaskCreate />} />
          <Route path="/tasks/:taskId/trace" element={<TaskTrace />} />
          <Route path="/agents" element={<AgentList />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
    </ThemeProvider>
  );
}
