"use client";

import type { Session } from "@supabase/supabase-js";
import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { apiGet, query } from "@/lib/api";
import { getSupabaseBrowserClient, isSupabaseConfigured } from "@/lib/supabase";
import type { Campaign, Client, Dashboard, MetaAccount, Metrics, Page } from "@/lib/types";

const periods = [7, 14, 30, 90, 120] as const;
const currency = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const integer = new Intl.NumberFormat("pt-BR");
const decimal = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 });
type Filters = { days: number; clientId: string; accountId: string; campaignId: string };

function metricValue(key: keyof Metrics, value: number | null) {
  if (value === null) return "—";
  if (["spend", "cpl", "cpc", "cpm"].includes(key)) return currency.format(value);
  if (key === "ctr") return `${decimal.format(value)}%`;
  return integer.format(value);
}

function MetricCard({ label, metricKey, metrics, change }: { label: string; metricKey: keyof Metrics; metrics: Metrics; change: number | null }) {
  const positive = change !== null && change >= 0;
  return <article className="metric-card"><span>{label}</span><strong>{metricValue(metricKey, metrics[metricKey])}</strong><small className={change === null ? "neutral" : positive ? "positive" : "negative"}>{change === null ? "sem base anterior" : `${positive ? "+" : ""}${decimal.format(change)}% vs. anterior`}</small></article>;
}

export default function Home() {
  const supabase = useMemo(() => getSupabaseBrowserClient(), []);
  const [session, setSession] = useState<Session | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authError, setAuthError] = useState("");
  const [filters, setFilters] = useState<Filters>({ days: 30, clientId: "", accountId: "", campaignId: "" });
  const [clients, setClients] = useState<Client[]>([]);
  const [accounts, setAccounts] = useState<MetaAccount[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const initialLoadStarted = useRef(false);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => { setSession(data.session); setAuthReady(true); });
    const { data } = supabase.auth.onAuthStateChange((_event, next) => setSession(next));
    return () => data.subscription.unsubscribe();
  }, [supabase]);

  const loadData = useCallback(async () => {
    if (!session?.access_token) return;
    setLoading(true); setError("");
    try {
      const token = session.access_token;
      const [clientPage, accountPage, campaignPage, dashboardData] = await Promise.all([
        apiGet<Page<Client>>("/api/v1/clients?page=1&page_size=100", token),
        apiGet<Page<MetaAccount>>(`/api/v1/meta-accounts?${query({ page: 1, page_size: 100, client_id: filters.clientId })}`, token),
        apiGet<Page<Campaign>>(`/api/v1/campaigns?${query({ page: 1, page_size: 100, meta_account_id: filters.accountId })}`, token),
        apiGet<Dashboard>(`/api/v1/dashboard?${query({ days: filters.days, client_id: filters.clientId, meta_account_id: filters.accountId, campaign_id: filters.campaignId })}`, token),
      ]);
      setClients(clientPage.items); setAccounts(accountPage.items); setCampaigns(campaignPage.items); setDashboard(dashboardData);
    } catch (cause) {
      if (cause instanceof Error && cause.message === "SESSION_EXPIRED") { await supabase.auth.signOut(); setAuthError("Sua sessão expirou. Entre novamente."); }
      else setError(cause instanceof Error ? cause.message : "Não foi possível carregar o dashboard.");
    } finally { setLoading(false); }
  }, [filters, session, supabase]);

  useEffect(() => {
    if (!session) {
      initialLoadStarted.current = false;
      return;
    }
    if (initialLoadStarted.current) return;
    initialLoadStarted.current = true;
    const timeout = window.setTimeout(() => void loadData(), 0);
    return () => window.clearTimeout(timeout);
  }, [loadData, session]);

  async function signIn(event: FormEvent) {
    event.preventDefault(); setAuthError("");
    const { error: signInError } = await supabase.auth.signInWithPassword({ email, password });
    if (signInError) setAuthError("E-mail ou senha inválidos.");
  }

  if (!isSupabaseConfigured) return <main className="center-screen"><div className="brand-mark">D</div><h2>Frontend ainda não configurado</h2><p>Crie o arquivo <code>.env.local</code> conforme o README.</p></main>;
  if (!authReady) return <main className="center-screen"><div className="spinner" /><p>Preparando seu painel…</p></main>;
  if (!session) return <main className="login-shell"><section className="login-story"><div className="brand-mark">D</div><p className="eyebrow">DESCOMPLIADS</p><h1>Decisões melhores começam com números claros.</h1><p>Campanhas, comparações e sinais de desempenho em um só lugar — sem alterar nada na Meta.</p><div className="trust-line"><i /> Dados protegidos por usuário e cliente</div></section><section className="login-panel"><form onSubmit={signIn}><div><p className="eyebrow coral">ACESSO SEGURO</p><h2>Bem-vinda de volta</h2><p>Use o usuário criado no Supabase.</p></div><label>E-mail<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" placeholder="voce@empresa.com" /></label><label>Senha<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password" placeholder="••••••••" /></label>{authError && <p className="form-error">{authError}</p>}<button type="submit">Entrar no painel <span>→</span></button><small>O token permanece na sessão do navegador e nunca é exibido.</small></form></section></main>;

  return <main className="app-shell">
    <aside><div className="logo"><div className="brand-mark small">D</div><div><strong>DescompliADS</strong><small>Growth Intelligence</small></div></div><nav><a className="active">◫ <span>Visão geral</span></a><a>◎ <span>Campanhas</span></a><a>◇ <span>Análises</span><em>em breve</em></a></nav><div className="sidebar-foot"><span className="status-dot" /> API conectada<button onClick={() => supabase.auth.signOut()}>Sair</button></div></aside>
    <section className="workspace"><header><div><p className="eyebrow coral">PAINEL DE PERFORMANCE</p><h1>Visão geral</h1><p>O que aconteceu, o que mudou e onde olhar primeiro.</p></div><div className="profile"><span>{session.user.email?.slice(0, 1).toUpperCase()}</span><div><strong>{session.user.email?.split("@")[0]}</strong><small>Acesso protegido</small></div></div></header>
      <section className="filters"><label>Período<select value={filters.days} onChange={(e) => setFilters({ ...filters, days: Number(e.target.value) })}>{periods.map((days) => <option key={days} value={days}>Últimos {days} dias</option>)}</select></label><label>Cliente<select value={filters.clientId} onChange={(e) => setFilters({ ...filters, clientId: e.target.value, accountId: "", campaignId: "" })}><option value="">Todos</option>{clients.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>Conta<select value={filters.accountId} onChange={(e) => setFilters({ ...filters, accountId: e.target.value, campaignId: "" })}><option value="">Todas</option>{accounts.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>Campanha<select value={filters.campaignId} onChange={(e) => setFilters({ ...filters, campaignId: e.target.value })}><option value="">Todas</option>{campaigns.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><button onClick={() => void loadData()} disabled={loading}>{loading ? "Atualizando…" : "Atualizar"}</button></section>
      {error && <div className="error-banner">{error}</div>}
      {dashboard && <><section className="period-line"><span>{dashboard.period.date_from} → {dashboard.period.date_to}</span><small>comparado a {dashboard.previous_period.date_from} → {dashboard.previous_period.date_to}</small></section><section className="metrics-grid"><MetricCard label="Investimento" metricKey="spend" metrics={dashboard.metrics} change={dashboard.change_percent.spend} /><MetricCard label="Conversas" metricKey="conversations" metrics={dashboard.metrics} change={dashboard.change_percent.conversations} /><MetricCard label="Leads" metricKey="leads" metrics={dashboard.metrics} change={dashboard.change_percent.leads} /><MetricCard label="CPL" metricKey="cpl" metrics={dashboard.metrics} change={dashboard.change_percent.cpl} /><MetricCard label="CTR" metricKey="ctr" metrics={dashboard.metrics} change={dashboard.change_percent.ctr} /><MetricCard label="CPC" metricKey="cpc" metrics={dashboard.metrics} change={dashboard.change_percent.cpc} /></section>
        <section className="content-grid"><article className="panel structure-panel"><div className="panel-title"><div><p className="eyebrow">ESTRUTURA IMPORTADA</p><h2>Conta em números</h2></div><span className="pill">Somente leitura</span></div><div className="structure-flow">{[[dashboard.clients,"Clientes"],[dashboard.meta_accounts,"Contas"],[dashboard.campaigns,"Campanhas"],[dashboard.adsets,"Conjuntos"],[dashboard.ads,"Anúncios"]].map(([value,label]) => <div key={label}><strong>{value}</strong><span>{label}</span></div>)}</div></article><article className="panel signal-panel"><p className="eyebrow">LEITURA RÁPIDA</p><h2>Sinal do período</h2><div className="signal"><span>{dashboard.metrics.conversations > 0 ? "↗" : "—"}</span><div><strong>{dashboard.metrics.conversations > 0 ? `${dashboard.metrics.conversations} conversas registradas` : "Sem conversões no período"}</strong><p>{dashboard.metrics.conversations > 0 ? `Custo médio de ${currency.format(dashboard.metrics.spend / dashboard.metrics.conversations)} por conversa.` : "Amplie o período ou revise a coleta antes de concluir."}</p></div></div><small>Interpretação determinística. IA entra na próxima entrega.</small></article></section>
        <section className="panel table-panel"><div className="panel-title"><div><p className="eyebrow">CAMPANHAS</p><h2>Estrutura disponível</h2></div><span>{campaigns.length} exibidas</span></div><div className="table-wrap"><table><thead><tr><th>Campanha</th><th>Objetivo</th><th>Status</th></tr></thead><tbody>{campaigns.map((campaign) => <tr key={campaign.id}><td>{campaign.name}</td><td>{campaign.objective ?? "Não informado"}</td><td><span className={`status ${campaign.status.toLowerCase()}`}>{campaign.status === "ACTIVE" ? "Ativa" : "Arquivada"}</span></td></tr>)}</tbody></table></div></section>
      </>}
    </section>
  </main>;
}
