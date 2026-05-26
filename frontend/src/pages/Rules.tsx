import { api } from "../services/api";
import { useAsync } from "../hooks/useAsync";

export function Rules() {
  const { data, loading, error } = useAsync(api.rules, []);
  return (
    <section>
      <div className="page-head">
        <div>
          <p className="eyebrow">Decisao</p>
          <h1>Regras de oferta</h1>
        </div>
      </div>
      {loading && <p className="muted">Carregando...</p>}
      {error && <p className="error">{error}</p>}
      <div className="table">
        {(data ?? []).map((rule) => (
          <div className="row" key={rule.id}>
            <strong>{rule.name}</strong>
            <span>{rule.min_discount_percent}% minimo</span>
            <span>{rule.cooldown_hours}h cooldown</span>
            <span>{rule.auto_publish ? "automatico" : "semi-auto"}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
