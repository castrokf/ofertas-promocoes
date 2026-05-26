import { RefreshCw } from "lucide-react";
import { useState } from "react";
import { DealCard } from "../components/DealCard";
import { api, type DealCard as Deal } from "../services/api";
import { useAsync } from "../hooks/useAsync";

export function Dashboard() {
  const [segment, setSegment] = useState("games");
  const { data, loading, error, setData } = useAsync(() => api.deals("", 60), []);
  const { data: channels } = useAsync(api.channels, []);
  const [channelId, setChannelId] = useState("");
  const [busy, setBusy] = useState(false);

  async function refresh() {
    setBusy(true);
    try {
      await api.refreshDeals(segment);
      setData(await api.deals("", 60));
    } finally {
      setBusy(false);
    }
  }

  async function approve(id: string) {
    await api.approveDeal(id);
    setData((data ?? []).map((deal) => (deal.id === id ? { ...deal, quality_label: `${deal.quality_label} / aprovado` } : deal)));
  }

  async function publish(id: string) {
    const selectedChannel = channelId || channels?.[0]?.id;
    if (!selectedChannel) {
      window.alert("Cadastre ou habilite um canal antes de publicar.");
      return;
    }
    const result = await api.publishDeal(id, selectedChannel);
    window.alert(result.error ? `${result.status}: ${result.error}` : `Publicacao: ${result.status}`);
  }

  const deals = data ?? [];
  const channelOptions = channels ?? [];
  return (
    <section>
      <div className="page-head">
        <div>
          <p className="eyebrow">Monitoramento</p>
          <h1>Ofertas detectadas</h1>
        </div>
        <div className="toolbar">
          <select value={segment} onChange={(event) => setSegment(event.target.value)}>
            <option value="games">Jogos digitais</option>
            <option value="hardware">Hardware</option>
            <option value="all">Tudo</option>
          </select>
          <select value={channelId} onChange={(event) => setChannelId(event.target.value)}>
            <option value="">Canal padrao</option>
            {channelOptions.map((channel) => (
              <option key={channel.id} value={channel.id}>{channel.name}</option>
            ))}
          </select>
          <button type="button" onClick={refresh} disabled={busy}>
            <RefreshCw size={16} /> {busy ? "Coletando" : "Coletar agora"}
          </button>
        </div>
      </div>

      <div className="stats">
        <div><strong>{deals.length}</strong><span>ofertas na fila</span></div>
        <div><strong>{deals.filter((deal) => deal.quality_label.includes("imperdivel")).length}</strong><span>imperdiveis</span></div>
        <div><strong>{deals.filter((deal) => deal.store === "Steam").length}</strong><span>Steam</span></div>
      </div>

      {loading && <p className="muted">Carregando...</p>}
      {error && <p className="error">{error}</p>}
      <div className="deal-grid">
        {deals.map((deal: Deal) => (
          <DealCard key={deal.id} deal={deal} onApprove={approve} onPublish={publish} />
        ))}
      </div>
    </section>
  );
}
