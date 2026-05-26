import { Check, Copy, ExternalLink, Send } from "lucide-react";
import type { DealCard as Deal } from "../services/api";

function brl(value: number | null) {
  if (value === null) return "";
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value);
}

export function DealCard({
  deal,
  onApprove,
  onPublish
}: {
  deal: Deal;
  onApprove: (id: string) => void;
  onPublish: (id: string) => void;
}) {
  return (
    <article className="deal-card">
      <a className="deal-cover" href={deal.affiliate_url ?? "#"} target="_blank" rel="noreferrer sponsored">
        {deal.image_url ? <img src={deal.image_url} alt={deal.title} loading="lazy" /> : <div className="fallback">{deal.store}</div>}
        <span>{Math.round(deal.discount_percent)}% OFF</span>
      </a>
      <div className="deal-content">
        <div className="meta">
          <strong>{deal.store}</strong>
          <small>{deal.quality_label}</small>
        </div>
        <h3>{deal.title}</h3>
        <div className="price">
          <strong>{brl(deal.current_price)}</strong>
          {deal.old_price && <span>{brl(deal.old_price)}</span>}
        </div>
        <textarea value={deal.message_twitter} readOnly />
        <div className="button-row">
          <button type="button" onClick={() => navigator.clipboard.writeText(deal.message_twitter)} title="Copiar post">
            <Copy size={16} /> Copiar
          </button>
          <button type="button" onClick={() => onApprove(deal.id)} title="Aprovar oferta">
            <Check size={16} /> Aprovar
          </button>
          <button type="button" onClick={() => onPublish(deal.id)} title="Publicar no canal selecionado">
            <Send size={16} /> Publicar
          </button>
          <a href={deal.affiliate_url ?? "#"} target="_blank" rel="noreferrer sponsored" title="Abrir oferta">
            <ExternalLink size={16} /> Abrir
          </a>
        </div>
      </div>
    </article>
  );
}
