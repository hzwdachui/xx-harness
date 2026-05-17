export function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="card" style={{ borderColor: "var(--error)", marginBottom: 24 }}>
      <span style={{ fontSize: 10, fontWeight: 600, textTransform: "uppercase", color: "var(--error)" }}>
        {message}
      </span>
    </div>
  );
}
