export type EntityStatus = "ACTIVE" | "ARCHIVED";
export type Page<T> = { items: T[]; page: number; page_size: number; total: number; pages: number };
export type Client = { id: string; name: string; slug: string; status: EntityStatus };
export type MetaAccount = { id: string; client_id: string; name: string; currency: string | null; status: EntityStatus; last_synced_at: string | null };
export type Campaign = { id: string; meta_account_id: string; name: string; objective: string | null; status: EntityStatus };
export type Metrics = { spend: number; impressions: number; clicks: number; leads: number; conversations: number; cpl: number | null; ctr: number | null; cpc: number | null; cpm: number | null };
export type Dashboard = {
  clients: number; meta_accounts: number; campaigns: number; adsets: number; ads: number;
  period: { date_from: string; date_to: string; days: number };
  previous_period: { date_from: string; date_to: string; days: number };
  metrics: Metrics; previous_metrics: Metrics; change_percent: Record<keyof Metrics, number | null>;
};
