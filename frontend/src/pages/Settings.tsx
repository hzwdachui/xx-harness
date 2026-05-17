import { useEffect, useState } from "react";
import { ErrorBanner } from "../components/ErrorBanner";

interface VersionInfo {
  version: string;
  commit: { hash: string; short: string; subject: string; date: string };
}

export function Settings() {
  const [info, setInfo] = useState<VersionInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/version")
      .then(res => res.json())
      .then(setInfo)
      .catch(e => setError(e.message));
  }, []);

  return (
    <>
      <div className="page-header">
        <h1>SETTINGS</h1>
        <p>System information and configuration.</p>
      </div>

      <div className="page-content">
        {error && <ErrorBanner message={`Failed to load version info: ${error}`} />}

        {!info && !error && <div className="loading">LOADING</div>}

        {info && (
          <div className="card" style={{ maxWidth: 520 }}>
            <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-secondary)", marginBottom: 20 }}>
              XX-HARNESS
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                <span style={{ fontSize: 10, fontWeight: 500, textTransform: "uppercase", color: "var(--text-muted)" }}>Version</span>
                <span style={{ fontSize: 13, fontWeight: 600 }}>{info.version}</span>
              </div>

              <div style={{ borderTop: "1px solid var(--border)" }} />

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                <span style={{ fontSize: 10, fontWeight: 500, textTransform: "uppercase", color: "var(--text-muted)" }}>Commit</span>
                <code style={{ fontSize: 12, fontFamily: "var(--font-mono)", color: "var(--accent)" }}>
                  {info.commit.short}
                </code>
              </div>

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                <span style={{ fontSize: 10, fontWeight: 500, textTransform: "uppercase", color: "var(--text-muted)" }}>Subject</span>
                <span style={{ fontSize: 12, fontWeight: 500, textAlign: "right", maxWidth: 340 }}>
                  {info.commit.subject}
                </span>
              </div>

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                <span style={{ fontSize: 10, fontWeight: 500, textTransform: "uppercase", color: "var(--text-muted)" }}>Date</span>
                <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>
                  {info.commit.date}
                </span>
              </div>

              <div style={{ borderTop: "1px solid var(--border)" }} />

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                <span style={{ fontSize: 10, fontWeight: 500, textTransform: "uppercase", color: "var(--text-muted)" }}>Full Hash</span>
                <code style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--text-secondary)", wordBreak: "break-all", textAlign: "right", maxWidth: 340 }}>
                  {info.commit.hash}
                </code>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
