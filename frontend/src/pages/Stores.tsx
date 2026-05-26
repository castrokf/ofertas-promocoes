import { api } from "../services/api";
import { useAsync } from "../hooks/useAsync";

export function Stores() {
  const { data, loading, error } = useAsync(api.stores, []);
  return (
    <section>
      <div className="page-head">
        <div>
          <p className="eyebrow">Fontes</p>
          <h1>Lojas e conectores</h1>
        </div>
      </div>
      {loading && <p className="muted">Carregando...</p>}
      {error && <p className="error">{error}</p>}
      <div className="table">
        {(data ?? []).map((store) => (
          <div className="row" key={store.id}>
            <strong>{store.name}</strong>
            <span>{store.collect_method}</span>
            <span>{store.status}</span>
            <span>{store.rate_limit_per_minute}/min</span>
          </div>
        ))}
      </div>
    </section>
  );
}
