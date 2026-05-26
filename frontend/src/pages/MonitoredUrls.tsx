import { api } from "../services/api";
import { useAsync } from "../hooks/useAsync";

export function MonitoredUrls() {
  const { data, loading, error } = useAsync(api.monitoredUrls, []);
  return (
    <section>
      <div className="page-head">
        <div>
          <p className="eyebrow">Coleta</p>
          <h1>URLs monitoradas</h1>
        </div>
      </div>
      {loading && <p className="muted">Carregando...</p>}
      {error && <p className="error">{error}</p>}
      <div className="table table-urls">
        {(data ?? []).map((item) => (
          <div className="row" key={item.id}>
            <strong>{item.url}</strong>
            <span>{item.collect_frequency_seconds}s</span>
            <span>prioridade {item.priority}</span>
            <span>{item.is_active ? "ativa" : "pausada"}</span>
          </div>
        ))}
        {!loading && (data ?? []).length === 0 && <p className="empty">Nenhuma URL cadastrada ainda.</p>}
      </div>
    </section>
  );
}
