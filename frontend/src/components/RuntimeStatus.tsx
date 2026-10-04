import type { Health } from "../types/api";

export function RuntimeStatus({health}:{health:Health|null}) {
  if (!health) return <div className="status loading">Checking model…</div>;
  return health.ready
    ? <div className="status ready"><span className="pulse"/>Model ready <strong>{health.device?.toUpperCase()}</strong><small>{health.model}</small></div>
    : <div className="status error">{health.message ?? "Model unavailable"}</div>;
}
