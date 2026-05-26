import { api } from "../services/api";
import { useAsync } from "../hooks/useAsync";

export function Logs() {
  const { data, loading, error } = useAsync(api.logs, []);
  return (
    <section>
      <div className="page-head">
        <div>
          <p className="eyebrow">Operacao</p>
          <h1>Logs recentes</h1>
        </div>
      </div>
      {loading && <p className="muted">Carregando...</p>}
      {error && <p className="error">{error}</p>}
      <div className="table table-logs">
        {(data ?? []).map((log) => (
          <div className="row" key={log.id}>
            <strong>{log.level}</strong>
            <span>{log.source}</span>
            <span>{log.message}</span>
            <span>{new Date(log.created_at).toLocaleString("pt-BR")}</span>
          </div>
        ))}
        {!loading && (data ?? []).length === 0 && <p className="empty">Nenhum log registrado ainda.</p>}
      </div>
    </section>
  );
}
