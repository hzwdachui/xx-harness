import { Link, useLocation, useParams } from "react-router-dom";
import { type ReactNode } from "react";
import { useTheme } from "../context/ThemeContext";

export function Layout({ children }: { children: ReactNode }) {
  const { id } = useParams<{ id?: string }>();
  const location = useLocation();
  const { theme, toggle } = useTheme();
  const projectId = id ? Number(id) : null;

  const isActive = (path: string) => {
    if (path === "/") return location.pathname === "/";
    return location.pathname.startsWith(path);
  };

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <aside className="sidebar">
        <Link to="/" className="sidebar-brand">
          <div className="sidebar-brand-icon">X</div>
          <h1>XX-HARNESS</h1>
        </Link>

        <div className="sidebar-section">
          <div className="sidebar-section-label">NAVIGATE</div>
        </div>
        <nav className="sidebar-nav">
          <Link to="/" className={`sidebar-nav-item ${isActive("/") ? "active" : ""}`}>
            <span className="dot" />
            PROJECTS
          </Link>
          <Link to="/agents" className={`sidebar-nav-item ${isActive("/agents") ? "active" : ""}`}>
            <span className="dot" />
            AGENTS
          </Link>
        </nav>

        {projectId && (
          <>
            <div className="sidebar-section">
              <div className="sidebar-section-label">PROJECT #{projectId}</div>
            </div>
            <nav className="sidebar-nav">
              <Link
                to={`/projects/${projectId}`}
                className={`sidebar-nav-item ${isActive(`/projects/${projectId}`) ? "active" : ""}`}
              >
                <span className="dot" />
                OVERVIEW
              </Link>
              <Link
                to={`/projects/${projectId}/tasks/new`}
                className={`sidebar-nav-item ${isActive(`/projects/${projectId}/tasks/new`) ? "active" : ""}`}
              >
                <span className="dot" />
                NEW TASK
              </Link>
              <Link
                to={`/projects/${projectId}/workflows/new`}
                className={`sidebar-nav-item ${isActive(`/projects/${projectId}/workflows/new`) ? "active" : ""}`}
              >
                <span className="dot" />
                NEW WORKFLOW
              </Link>
            </nav>
          </>
        )}

        <div className="sidebar-footer">
          <Link to="/settings" className={`sidebar-nav-item ${isActive("/settings") ? "active" : ""}`} style={{ marginBottom: 8, padding: "8px 12px" }}>
            SETTINGS
          </Link>
          <button className="theme-toggle" onClick={toggle} title={`Switch to ${theme === "light" ? "dark" : "light"} mode`}>
            <span className="theme-toggle-icon">{theme === "light" ? "☾" : "☀"}</span>
            {theme === "light" ? "DARK" : "LIGHT"}
          </button>
        </div>
      </aside>

      <main className="main-layout">{children}</main>
    </div>
  );
}
