export type DealCard = {
  id: string;
  title: string;
  store: string;
  category: string | null;
  image_url: string | null;
  current_price: number;
  old_price: number | null;
  discount_percent: number;
  quality_label: string;
  score: number;
  affiliate_url: string | null;
  message_twitter: string;
  created_at: string;
};

export type Store = {
  id: string;
  name: string;
  slug: string;
  base_url: string;
  collect_method: string;
  status: string;
  supports_affiliate: boolean;
  rate_limit_per_minute: number;
  trust_score: number;
};

export type Channel = {
  id: string;
  name: string;
  channel_type: string;
  is_active: boolean;
  config: Record<string, unknown>;
};

export type Rule = {
  id: string;
  name: string;
  min_discount_percent: number;
  target_price: number | null;
  cooldown_hours: number;
  is_active: boolean;
  auto_publish: boolean;
};

export type MonitoredUrl = {
  id: string;
  store_id: string;
  category_id: string | null;
  url: string;
  collect_frequency_seconds: number;
  priority: number;
  is_active: boolean;
  last_checked_at: string | null;
};

export type LogEntry = {
  id: string;
  level: string;
  source: string;
  message: string;
  context: Record<string, unknown>;
  created_at: string;
};

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";
const TOKEN_KEY = "autotechdealsx_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken();
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options?.headers ?? {})
    },
    ...options
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

export const api = {
  login: (email: string, password: string) =>
    request<{ access_token: string; token_type: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    }),
  deals: (status = "", limit = 60) => request<DealCard[]>(`/deals?limit=${limit}${status ? `&status=${status}` : ""}`),
  refreshDeals: (segment: string) =>
    request<{ collected: number; deals_created: number; errors: string[] }>("/deals/refresh", {
      method: "POST",
      body: JSON.stringify({ segment, limit: 80 })
    }),
  approveDeal: (id: string) => request(`/deals/${id}/approve`, { method: "POST" }),
  publishDeal: (dealId: string, channelId: string) =>
    request<{ status: string; error: string | null }>(`/deals/${dealId}/publish/${channelId}`, { method: "POST" }),
  stores: () => request<Store[]>("/stores"),
  channels: () => request<Channel[]>("/channels"),
  rules: () => request<Rule[]>("/rules"),
  monitoredUrls: () => request<MonitoredUrl[]>("/monitored-urls"),
  logs: () => request<LogEntry[]>("/logs?limit=100"),
  metrics: () => request("/metrics/summary")
};
