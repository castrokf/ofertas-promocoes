import { api } from "../services/api";
import { useAsync } from "../hooks/useAsync";

export function Channels() {
  const { data, loading, error } = useAsync(api.channels, []);
  return (
    <section>
      <div className="page-head">
        <div>
          <p className="eyebrow">Publicacao</p>
          <h1>Canais configurados</h1>
        </div>
      </div>
      {loading && <p className="muted">Carregando...</p>}
      {error && <p className="error">{error}</p>}
      <div className="table">
        {(data ?? []).map((channel) => (
          <div className="row" key={channel.id}>
            <strong>{channel.name}</strong>
            <span>{channel.channel_type}</span>
            <span>{channel.is_active ? "ativo" : "inativo"}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
