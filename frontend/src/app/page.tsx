"use client";

import type { Session } from "@supabase/supabase-js";
import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { apiGet, apiPost, query } from "@/lib/api";
import { getSupabaseBrowserClient, isSupabaseConfigured } from "@/lib/supabase";
import type { BreakdownPoint, Campaign, Client, Dashboard, EntityPerformance, Improvement, MetaAccount, Metrics, Page, Recommendation, SettingsData } from "@/lib/types";

const periods = [7, 14, 30, 90, 120] as const;
const currency = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const integer = new Intl.NumberFormat("pt-BR");
const decimal = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 });
type Filters = { days: number; clientId: string; accountId: string; campaignId: string };
type MainView = "dashboard" | "campaigns" | "analyses" | "settings";
type TrendMeaning = "positive" | "negative" | "neutral" | "contextual";
type ExecutivePriority = {
  key: string;
  tone: "critical" | "attention" | "opportunity" | "information";
  label: string;
  title: string;
  description: string;
  evidence?: string;
};

const higherIsBetterMetrics = new Set<keyof Metrics>([
  "conversations", "leads", "link_clicks", "ctr", "link_ctr",
]);
const lowerIsBetterMetrics = new Set<keyof Metrics>(["cpl", "cpc"]);
type IndicatorGuide = { title: string; meaning: string; direction: string; attention: string };

const metricGuides: Partial<Record<keyof Metrics, IndicatorGuide>> = {
  spend: { title: "Investimento", meaning: "Quanto foi gasto em mídia no período selecionado.", direction: "Não existe melhor ou pior isoladamente: compare o valor com os resultados gerados.", attention: "Investimento maior sem crescimento proporcional de leads ou conversas indica perda de eficiência." },
  conversations: { title: "Conversas", meaning: "Quantidade de conversas atribuídas aos anúncios pela Meta.", direction: "Em geral, quanto mais conversas qualificadas, melhor.", attention: "Volume não garante qualidade. Compare com o atendimento e com as vendas no CRM." },
  leads: { title: "Leads", meaning: "Cadastros ou contatos atribuídos às campanhas.", direction: "Quanto mais leads qualificados pelo mesmo investimento, melhor.", attention: "O valor influencia a eficiência, mas a qualidade do lead só pode ser confirmada após o atendimento." },
  cpl: { title: "Custo por lead (CPL)", meaning: "Investimento dividido pela quantidade de leads.", direction: "Em geral, quanto menor, melhor — desde que a qualidade dos leads seja mantida.", attention: "Um CPL muito baixo pode trazer contatos menos preparados. Compare com agendamentos e vendas." },
  link_ctr: { title: "CTR de link", meaning: "Percentual de impressões que gerou um clique no link.", direction: "Em geral, quanto maior, melhor: indica que mensagem e oferta despertaram interesse.", attention: "CTR alto com poucos leads pode apontar problema na página, na oferta ou na qualidade do tráfego." },
  ctr: { title: "CTR", meaning: "Percentual de impressões que gerou algum clique no anúncio.", direction: "Em geral, quanto maior, melhor, mas o clique precisa levar a uma ação útil.", attention: "Para avaliar intenção, prefira o CTR de link ao CTR de todos os cliques." },
  cpm: { title: "CPM", meaning: "Custo para exibir o anúncio mil vezes.", direction: "Não existe melhora ou piora isoladamente: interprete o CPM junto com alcance, frequência e resultados gerados.", attention: "CPM alto pode indicar concorrência, público pequeno, segmentação restrita ou desgaste do criativo." },
  impressions: { title: "Impressões", meaning: "Número total de vezes que os anúncios foram exibidos, incluindo repetições.", direction: "Mais impressões ampliam a exposição, mas não garantem resultados.", attention: "Compare com alcance e frequência para entender quantas vezes cada pessoa viu o anúncio." },
  reach: { title: "Alcance", meaning: "Quantidade estimada de pessoas únicas que viram os anúncios.", direction: "Maior alcance é útil quando o objetivo é encontrar novas pessoas.", attention: "Alcance alto com poucos cliques pode indicar criativo ou mensagem pouco atraente." },
  link_clicks: { title: "Cliques no link", meaning: "Cliques que levaram a pessoa para o destino definido no anúncio.", direction: "Quanto mais cliques relevantes pelo mesmo custo, melhor.", attention: "Cliques sem leads podem revelar lentidão da página, oferta fraca ou público pouco qualificado." },
  frequency: { title: "Frequência", meaning: "Média de vezes que cada pessoa viu os anúncios.", direction: "Não é simplesmente menor ou maior: precisa ficar em uma faixa saudável.", attention: "Acima de 3–4 em públicos frios pequenos pode indicar saturação; confirme junto com CTR e CPM." },
};

const chartGuides: Record<string, IndicatorGuide> = {
  "Faixas etárias": { title: "Desempenho por idade", meaning: "Compara os resultados entre as faixas etárias alcançadas pela campanha.", direction: "Procure faixas com mais conversões e CPA menor.", attention: "Idade influencia o custo e a qualidade do lead. Não realoque verba sem volume suficiente de dados." },
  "Gênero": { title: "Desempenho por gênero", meaning: "Compara investimento e resultado entre os gêneros informados pela Meta.", direction: "Melhor é o grupo que combina conversões consistentes e CPA sustentável.", attention: "Use como aprendizado de público, evitando conclusões com amostras pequenas." },
  "Posicionamentos": { title: "Desempenho por posicionamento", meaning: "Mostra onde o anúncio apareceu, como Feed, Stories, Reels ou Marketplace.", direction: "Busque CPA menor e boa taxa de conversão, não apenas CPM barato.", attention: "Cada posicionamento exige um formato criativo adequado; Reels, por exemplo, favorece vídeo vertical." },
  "Plataformas": { title: "Facebook x Instagram", meaning: "Compara a entrega e os resultados entre as plataformas da Meta.", direction: "A melhor plataforma é a que gera resultado qualificado com eficiência.", attention: "O comportamento pode variar por região, idade, renda e tipo de imóvel." },
  "Dispositivos": { title: "Desempenho por dispositivo", meaning: "Compara a experiência de pessoas em celular e computador.", direction: "Procure maior taxa de conversão e menor CPA.", attention: "Muitos cliques mobile com poucos leads podem indicar página lenta ou formulário difícil no celular." },
  "Regiões": { title: "Desempenho por região", meaning: "Mostra quais localidades concentram entrega e resultados.", direction: "Regiões com CPA menor e conversões recorrentes merecem atenção.", attention: "Não confunda poucos resultados baratos com tendência: valide volume e qualidade comercial." },
  "Dias e horários": { title: "Dias e horários", meaning: "O mapa destaca quando as conversões aconteceram no fuso da conta Meta.", direction: "Células mais intensas representam mais resultados.", attention: "Use para entender comportamento. Alterar horários exige consistência histórica e avaliação do atendimento disponível." },
};

function IndicatorInfo({ guide, onClose }: { guide: IndicatorGuide; onClose: () => void }) {
  useEffect(() => {
    const closeWithEscape = (event: KeyboardEvent) => { if (event.key === "Escape") onClose(); };
    window.addEventListener("keydown", closeWithEscape);
    return () => window.removeEventListener("keydown", closeWithEscape);
  }, [onClose]);
  return <div className="indicator-modal" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}><section role="dialog" aria-modal="true" aria-labelledby="indicator-title"><button className="modal-close" onClick={onClose} aria-label="Fechar explicação">×</button><p className="eyebrow coral">ENTENDA O INDICADOR</p><h2 id="indicator-title">{guide.title}</h2><div className="guide-block"><strong>O que significa</strong><p>{guide.meaning}</p></div><div className="guide-block good"><strong>Como interpretar</strong><p>{guide.direction}</p></div><div className="guide-block attention"><strong>O que observar</strong><p>{guide.attention}</p></div><small>Orientação educativa baseada em regras gerais. Não substitui a análise do contexto da campanha.</small></section></div>;
}

function friendlyDate(value: string) {
  return new Intl.DateTimeFormat("pt-BR", { timeZone: "UTC" }).format(new Date(`${value}T12:00:00Z`));
}

function metricValue(key: keyof Metrics, value: number | null | undefined) {
  if (value == null) return "—";
  if (["spend", "cpl", "cpc", "cpm"].includes(key)) return currency.format(value);
  if (["ctr", "link_ctr"].includes(key)) return `${decimal.format(value)}%`;
  if (key === "frequency") return decimal.format(value);
  return integer.format(value);
}

function trendMeaning(metricKey: keyof Metrics, change: number | null | undefined): TrendMeaning {
  if (change == null || change === 0) return "neutral";
  if (higherIsBetterMetrics.has(metricKey)) return change > 0 ? "positive" : "negative";
  if (lowerIsBetterMetrics.has(metricKey)) return change < 0 ? "positive" : "negative";
  return "contextual";
}

function trendCopy(meaning: TrendMeaning) {
  if (meaning === "positive") return "melhora";
  if (meaning === "negative") return "piora";
  if (meaning === "contextual") return "avaliar com resultados";
  return "sem alteração";
}

function MetricCard({ label, metricKey, metrics, change }: { label: string; metricKey: keyof Metrics; metrics: Metrics; change?: number | null }) {
  const [showGuide, setShowGuide] = useState(false);
  const meaning = trendMeaning(metricKey, change);
  const changeCopy = change == null
    ? "sem base anterior"
    : `${change > 0 ? "+" : ""}${decimal.format(change)}% vs. anterior · ${trendCopy(meaning)}`;
  const guide = metricGuides[metricKey];
  return <><article className={`metric-card${guide ? " explainable" : ""}`} onClick={() => guide && setShowGuide(true)}><span>{label}</span>{guide && <button className="info-button" aria-label={`Entenda ${label}`} onClick={(event) => { event.stopPropagation(); setShowGuide(true); }}>i</button>}<strong>{metricValue(metricKey, metrics[metricKey])}</strong><small className={meaning}>{changeCopy}</small>{guide && <em>Toque para entender</em>}</article>{showGuide && guide && <IndicatorInfo guide={guide} onClose={() => setShowGuide(false)} />}</>;
}

function executivePriorities(dashboard: Dashboard): ExecutivePriority[] {
  const recommendationPriority = { HIGH: 0, MEDIUM: 1, LOW: 2 } as const;
  const recommendations: ExecutivePriority[] = dashboard.recommendations
    .filter((item) => item.status === "PENDING")
    .sort((a, b) => recommendationPriority[a.priority] - recommendationPriority[b.priority])
    .map((item) => ({
      key: `recommendation-${item.key}`,
      tone: item.priority === "HIGH" ? "critical" : "attention",
      label: item.priority === "HIGH" ? "Ação prioritária" : "Ação recomendada",
      title: item.title,
      description: item.explanation,
      evidence: item.evidence,
    }));
  const insightOrder = { WARNING: 0, OPPORTUNITY: 1, INFO: 2 } as const;
  const insights: ExecutivePriority[] = [...dashboard.insights]
    .sort((a, b) => insightOrder[a.severity] - insightOrder[b.severity])
    .map((item) => ({
      key: `insight-${item.code}`,
      tone: item.severity === "WARNING" ? "attention" : item.severity === "OPPORTUNITY" ? "opportunity" : "information",
      label: item.severity === "WARNING" ? "Ponto de atenção" : item.severity === "OPPORTUNITY" ? "Oportunidade" : "Leitura do período",
      title: item.title,
      description: item.message,
    }));
  return [...recommendations, ...insights].slice(0, 3);
}

function ExecutiveSummary({ dashboard, onOpenAnalyses }: { dashboard: Dashboard; onOpenAnalyses: () => void }) {
  const priorities = executivePriorities(dashboard);
  const attentionCount = priorities.filter((item) => item.tone === "critical" || item.tone === "attention").length;
  const headline = attentionCount > 0
    ? `${attentionCount} ${attentionCount === 1 ? "ponto exige" : "pontos exigem"} sua atenção`
    : priorities.length > 0 ? "Período sem alertas críticos" : "Nenhum sinal relevante neste período";
  return <section className="executive-summary" aria-labelledby="executive-summary-title"><div className="executive-summary-head"><div><p className="eyebrow coral">PRIORIDADES DO PERÍODO</p><h2 id="executive-summary-title">{headline}</h2><p>Comece por estes sinais antes de explorar os gráficos e rankings.</p></div>{priorities.length > 0 && <button onClick={onOpenAnalyses}>Abrir análise completa</button>}</div>
    {priorities.length > 0 ? <div className="priority-grid">{priorities.map((item, index) => <article className={`priority-card ${item.tone}`} key={item.key}><div className="priority-card-top"><span>{index + 1}</span><small>{item.label}</small></div><h3>{item.title}</h3><p>{item.description}</p>{item.evidence && <small className="priority-evidence"><b>Evidência:</b> {item.evidence}</small>}</article>)}</div>
      : <div className="executive-clear"><span>✓</span><p>Não há diagnóstico forte o suficiente para recomendar uma ação agora. Continue acompanhando o próximo período.</p></div>}
  </section>;
}

function RankingTable({ title, items }: { title: string; items: EntityPerformance[] }) {
  return <article className="panel table-panel"><div className="panel-title"><div><p className="eyebrow">RANKING DE PERFORMANCE</p><h2>{title}</h2></div><span>{items.length} com entrega</span></div><div className="table-wrap"><table><thead><tr><th>Nome</th><th>Investimento</th><th>Conversas</th><th>CTR</th><th>Custo/conversa</th></tr></thead><tbody>{items.map((item) => <tr key={item.entity_id}><td>{item.name}</td><td>{currency.format(item.spend)}</td><td>{integer.format(item.conversations)}</td><td>{item.ctr === null ? "—" : `${decimal.format(item.ctr)}%`}</td><td>{item.cost_per_conversation === null ? "—" : currency.format(item.cost_per_conversation)}</td></tr>)}</tbody></table></div></article>;
}

function FunnelMetric({ label, value, description, source, warning }: { label: string; value?: string; description: string; source?: string; warning?: boolean }) {
  return <article className={`funnel-metric ${value ? "available" : "pending"}${warning ? " warning" : ""}`}><div><strong>{label}</strong>{source && <span>{source}</span>}</div><b>{value ?? "Aguardando dados"}</b><p>{description}</p></article>;
}

const dimensionLabels: Record<string, string> = {
  female: "Feminino", male: "Masculino", unknown: "Não especificado",
  facebook: "Facebook", instagram: "Instagram", messenger: "Messenger",
  audience_network: "Audience Network", mobile_app: "Aplicativo móvel",
  mobile_web: "Navegador móvel", desktop: "Desktop",
  feed: "Feed", story: "Stories", reels: "Reels", marketplace: "Marketplace",
};

function BreakdownChart({ title, subtitle, points }: { title: string; subtitle: string; points: BreakdownPoint[] }) {
  const [showGuide, setShowGuide] = useState(false);
  const ranked = [...points].sort((a, b) => (b.leads + b.conversations) - (a.leads + a.conversations)).slice(0, 8);
  const maximum = Math.max(...ranked.map((item) => item.leads + item.conversations), 1);
  const guide = chartGuides[title];
  return <><article className="panel breakdown-chart explainable-chart" onClick={() => guide && setShowGuide(true)}><div className="panel-title"><div><p className="eyebrow">{subtitle}</p><h2>{title} <button className="info-button" aria-label={`Entenda o gráfico ${title}`} onClick={(event) => { event.stopPropagation(); setShowGuide(true); }}>i</button></h2></div><span>{points.length} segmentos</span></div>{ranked.length === 0 ? <div className="chart-empty">Aguardando a próxima sincronização analítica.</div> : <div className="horizontal-chart">{ranked.map((item) => { const conversions = item.leads + item.conversations; return <div className="chart-row" key={item.value}><div className="chart-label"><strong>{dimensionLabels[item.value] ?? item.value}</strong><small>{conversions} resultados · CPA {item.cpa == null ? "—" : currency.format(item.cpa)}</small></div><div className="chart-track"><i style={{ width: `${Math.max((conversions / maximum) * 100, conversions ? 5 : 0)}%` }} /></div><span>{item.conversion_rate == null ? "—" : `${decimal.format(item.conversion_rate)}%`}</span></div>; })}</div>}</article>{showGuide && guide && <IndicatorInfo guide={guide} onClose={() => setShowGuide(false)} />}</>;
}

function TimeHeatmap({ points }: { points: BreakdownPoint[] }) {
  const [showGuide, setShowGuide] = useState(false);
  const days = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];
  const lookup = new Map(points.map((item) => [item.value, item.leads + item.conversations]));
  const maximum = Math.max(...lookup.values(), 1);
  return <><article className="panel heatmap-panel explainable-chart" onClick={() => setShowGuide(true)}><div className="panel-title"><div><p className="eyebrow">COMPORTAMENTO DO PÚBLICO</p><h2>Dias e horários <button className="info-button" aria-label="Entenda o gráfico de dias e horários" onClick={(event) => { event.stopPropagation(); setShowGuide(true); }}>i</button></h2></div><span>Fuso da conta Meta</span></div>{points.length === 0 ? <div className="chart-empty">Aguardando dados por hora.</div> : <div className="heatmap-wrap"><div className="heatmap-hours">{Array.from({ length: 24 }, (_, hour) => <span key={hour}>{hour % 3 === 0 ? `${hour}h` : ""}</span>)}</div>{days.map((day, weekday) => <div className="heatmap-row" key={day}><strong>{day}</strong><div>{Array.from({ length: 24 }, (_, hour) => { const value = lookup.get(`${weekday}|${String(hour).padStart(2, "0")}`) ?? 0; return <i key={hour} title={`${day}, ${hour}h: ${value} resultados`} style={{ opacity: value ? Math.max(value / maximum, .18) : .05 }} />; })}</div></div>)}</div>}</article>{showGuide && <IndicatorInfo guide={chartGuides["Dias e horários"]} onClose={() => setShowGuide(false)} />}</>;
}

type SettingsSection = "general" | "users" | "clients" | "meta" | "ai" | "crm" | "webhooks" | "meta-app" | "api" | "security";

function FieldHelp({ text }: { text: string }) {
  return <span className="field-help" tabIndex={0} aria-label={text}>?<span role="tooltip">{text}</span></span>;
}

function SettingsPanel({ token, clients, userEmail }: { token: string; clients: Client[]; userEmail: string }) {
  const [data, setData] = useState<SettingsData | null>(null);
  const [section, setSection] = useState<SettingsSection>("meta");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [meta, setMeta] = useState({ client_id: clients[0]?.id ?? "", connection_name: "Meta Ads", ad_account_id: "", business_id: "", access_token: "" });
  const [system, setSystem] = useState({ meta_app_id: "", meta_app_secret: "", system_user_id: "", graph_version: "v25.0", openai_api_key: "" });

  const refresh = useCallback(async () => setData(await apiGet<SettingsData>("/api/v1/settings", token)), [token]);
  useEffect(() => {
    const timeout = window.setTimeout(() => void refresh(), 0);
    return () => window.clearTimeout(timeout);
  }, [refresh]);

  async function saveMeta(event: FormEvent) {
    event.preventDefault(); setBusy(true); setMessage("");
    try {
      await apiPost("/api/v1/settings/meta", token, { ...meta, business_id: meta.business_id || null });
      setMeta((value) => ({ ...value, access_token: "" })); setMessage("Tudo certo! A conexão com a Meta foi verificada e salva com segurança."); await refresh();
    } catch (cause) { setMessage(cause instanceof Error ? cause.message : "Não foi possível salvar."); }
    finally { setBusy(false); }
  }

  async function saveSystem(event: FormEvent) {
    event.preventDefault(); setBusy(true); setMessage("");
    try {
      await apiPost("/api/v1/settings/system", token, {
        meta_app_id: system.meta_app_id || null, meta_app_secret: system.meta_app_secret || null,
        system_user_id: system.system_user_id || null, graph_version: system.graph_version,
        openai_api_key: system.openai_api_key || null,
      });
      setSystem((value) => ({ ...value, meta_app_secret: "", openai_api_key: "" })); setMessage("Configuração atualizada e protegida com segurança."); await refresh();
    } catch (cause) { setMessage(cause instanceof Error ? cause.message : "Não foi possível salvar."); }
    finally { setBusy(false); }
  }

  const configured = (provider: string, clientId?: string) => data?.credentials.find((item) => item.provider === provider && (!clientId || item.client_id === clientId));
  const metaStatus = configured("META_CLIENT", meta.client_id);
  const configText = (key: string) => typeof metaStatus?.config[key] === "string" ? String(metaStatus.config[key]) : "Não informado";
  const formattedDate = metaStatus?.last_validated_at ? new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(new Date(metaStatus.last_validated_at)) : "Ainda não realizada";
  const menu = (id: SettingsSection, label: string, soon = false) => <button type="button" className={section === id ? "active" : ""} onClick={() => { setSection(id); setMessage(""); }}>{label}{soon && <em>em breve</em>}</button>;
  const placeholder = (title: string, description: string) => <div className="settings-card settings-placeholder"><h2>{title}</h2><p>{description}</p><span>Esta área será liberada em uma próxima etapa.</span></div>;

  return <section className="settings-page"><header><div><p className="eyebrow coral">AJUSTES</p><h1>Configurações</h1><p>Organize conexões e preferências com explicações em cada campo.</p></div></header>
    {message && <div className="settings-message">{message}</div>}
    <div className="settings-layout"><nav className="settings-nav">
      <strong>Conta</strong>{menu("general", "Geral")}{menu("users", "Usuários", true)}{menu("clients", "Clientes", true)}
      <strong>Integrações</strong>{menu("meta", "Meta Ads")}{menu("ai", "Inteligência Artificial")}{menu("crm", "CRM", true)}{menu("webhooks", "Webhooks", true)}
      {data?.system_admin && <><strong>Sistema</strong>{menu("meta-app", "Aplicativo Meta")}{menu("api", "API e serviços")}{menu("security", "Segurança")}</>}
    </nav><div className="settings-content">
      {section === "meta" && <form className="settings-card" onSubmit={saveMeta}><div className="settings-card-head"><div className="settings-icon">M</div><div><h2>Meta Ads</h2><p>Conexão da conta de anúncios do cliente.</p></div><span className={metaStatus ? "connection-ok" : "connection-pending"}>{metaStatus ? "Conectado" : "Não conectado"}</span></div>
        <label><span>Cliente <FieldHelp text="Escolha a empresa que será dona desta conexão." /></span><select value={meta.client_id} onChange={(e) => setMeta({ ...meta, client_id: e.target.value })} required><option value="">Selecione</option>{clients.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
        <label><span>Nome da conexão <FieldHelp text="Use um nome fácil de reconhecer, como Meta Ads — Cliente Odisséia." /></span><input value={meta.connection_name} onChange={(e) => setMeta({ ...meta, connection_name: e.target.value })} required /></label>
        <label><span>ID do Business Manager <small>opcional</small> <FieldHelp text="No Gerenciador de Negócios da Meta, abra Configurações do negócio → Informações da empresa." /></span><input value={meta.business_id} onChange={(e) => setMeta({ ...meta, business_id: e.target.value })} placeholder="123456789" /></label>
        <label><span>ID da conta de anúncios <FieldHelp text="No Gerenciador de Anúncios, ele aparece no seletor de contas. Pode ser informado como act_123456789." /></span><input value={meta.ad_account_id} onChange={(e) => setMeta({ ...meta, ad_account_id: e.target.value })} placeholder="act_123456789" required /></label>
        <label><span>Token de acesso <FieldHelp text="Gere na Meta for Developers ou pelo usuário do sistema, com a permissão Leitura de anúncios (ads_read)." /></span><input type="password" value={meta.access_token} onChange={(e) => setMeta({ ...meta, access_token: e.target.value })} placeholder={metaStatus ? "•••••••• configurado — digite para substituir" : "Cole o token"} required autoComplete="new-password" /></label>
        <div className="secret-note">Depois de salvo, o token não pode ser visualizado. Para trocar, informe um novo token.</div><button disabled={busy}>{busy ? "Verificando…" : "Verificar e salvar conexão"}</button>
        {metaStatus && <div className="connection-summary"><h3>Situação da conexão</h3><dl><div><dt>Situação</dt><dd><i /> Conectado</dd></div><div><dt>Permissão</dt><dd>Leitura de anúncios <small>(ads_read)</small></dd></div><div><dt>Conta encontrada</dt><dd>{configText("account_name")}</dd></div><div><dt>Moeda</dt><dd>{configText("currency")}</dd></div><div><dt>Fuso horário</dt><dd>{configText("timezone")}</dd></div><div><dt>Última verificação</dt><dd>{formattedDate}</dd></div></dl></div>}
      </form>}
      {section === "meta-app" && <form className="settings-card" onSubmit={saveSystem}><div className="settings-card-head"><div className="settings-icon">M</div><div><h2>Aplicativo Meta</h2><p>Configuração global, disponível somente para administrador.</p></div><span className={configured("META_SYSTEM") ? "connection-ok" : "connection-pending"}>{configured("META_SYSTEM") ? "Configurado" : "Pendente"}</span></div>
        <label><span>ID do aplicativo <FieldHelp text="Na Meta for Developers, abra seu aplicativo → Configurações → Básico." /></span><input value={system.meta_app_id} onChange={(e) => setSystem({ ...system, meta_app_id: e.target.value })} /></label>
        <label><span>Chave secreta do aplicativo <FieldHelp text="Na mesma tela do aplicativo, use Mostrar em Chave secreta do aplicativo. Nunca envie essa chave por mensagem." /></span><input type="password" value={system.meta_app_secret} onChange={(e) => setSystem({ ...system, meta_app_secret: e.target.value })} placeholder={configured("META_SYSTEM") ? "•••••••• configurada — digite para substituir" : "Digite a chave secreta"} autoComplete="new-password" /></label>
        <label><span>ID do usuário do sistema <FieldHelp text="Em Configurações do negócio → Usuários → Usuários do sistema, selecione o usuário de produção." /></span><input value={system.system_user_id} onChange={(e) => setSystem({ ...system, system_user_id: e.target.value })} /></label>
        <label><span>Versão de comunicação com a Meta <FieldHelp text="Versão da Graph API usada pelo sistema. Altere somente após validar a compatibilidade." /></span><select value={system.graph_version} onChange={(e) => setSystem({ ...system, graph_version: e.target.value })}><option>v25.0</option><option>v24.0</option></select></label>
        <button disabled={busy || !system.meta_app_secret}>{busy ? "Salvando…" : "Salvar configuração"}</button>
      </form>}
      {section === "ai" && <form className="settings-card" onSubmit={saveSystem}><div className="settings-card-head"><div className="settings-icon ai">IA</div><div><h2>Inteligência Artificial</h2><p>Conecte o serviço que apoiará as análises.</p></div><span className={configured("OPENAI") ? "connection-ok" : "connection-pending"}>{configured("OPENAI") ? "Configurado" : "Pendente"}</span></div>
        {!data?.system_admin ? <div className="restricted-box">Somente o administrador pode alterar esta chave.</div> : <><label><span>Serviço de inteligência artificial <FieldHelp text="Nesta etapa o sistema está preparado para usar a OpenAI." /></span><select disabled><option>OpenAI</option></select></label><label><span>Chave de acesso da OpenAI <FieldHelp text="Crie a chave na área API Keys da plataforma OpenAI. Ela costuma começar com sk-proj-." /></span><input type="password" value={system.openai_api_key} onChange={(e) => setSystem({ ...system, openai_api_key: e.target.value })} placeholder={configured("OPENAI") ? "•••••••• configurada — digite para substituir" : "sk-proj-…"} autoComplete="new-password" /></label><div className="secret-note">Nenhuma análise ou cobrança será iniciada apenas por salvar a chave. Os prompts são internos e não aparecem neste painel.</div><button disabled={busy || !system.openai_api_key}>{busy ? "Salvando…" : "Salvar chave com segurança"}</button></>}
      </form>}
      {section === "general" && <div className="settings-card"><div className="settings-card-head"><div className="settings-icon">{userEmail.slice(0, 1).toUpperCase()}</div><div><h2>Sua conta</h2><p>Informações do acesso atual ao DescompliADS.</p></div><span className="connection-ok">Protegido</span></div><dl className="connection-summary account-summary"><div><dt>Usuário</dt><dd>{userEmail.split("@")[0]}</dd></div><div><dt>E-mail</dt><dd>{userEmail}</dd></div><div><dt>Situação</dt><dd><i /> Acesso ativo</dd></div></dl></div>}
      {section === "users" && placeholder("Usuários", "Convites, funções e permissões de acesso.")}
      {section === "clients" && placeholder("Clientes", "Cadastro e organização dos clientes atendidos.")}
      {section === "crm" && placeholder("CRM", "Conexões com ferramentas comerciais e atendimento.")}
      {section === "webhooks" && placeholder("Webhooks", "Avisos automáticos enviados para outros sistemas.")}
      {section === "api" && <div className="settings-card"><h2>API e serviços</h2><p>As credenciais técnicas são administradas no ambiente seguro da VPS e não aparecem no navegador.</p><div className="secret-note">Os prompts de análise também são configuração exclusiva dos desenvolvedores: não possuem formulário, endpoint público ou opção de edição no painel.</div></div>}
      {section === "security" && <div className="settings-card"><h2>Segurança</h2><p>Segredos são criptografados e nunca retornam para a tela depois de salvos.</p><div className="security-list"><span>✓ Acesso separado por cliente</span><span>✓ Credenciais ocultas</span><span>✓ Prompts internos protegidos</span></div></div>}
    </div></div>
  </section>;
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
  const [improvements, setImprovements] = useState<Improvement[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [decisions, setDecisions] = useState<Record<string, "ACCEPTED" | "REJECTED">>({});
  const [view, setView] = useState<MainView>("dashboard");
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
      const [clientPage, accountPage, campaignPage, dashboardData, improvementPage] = await Promise.all([
        apiGet<Page<Client>>("/api/v1/clients?page=1&page_size=100", token),
        apiGet<Page<MetaAccount>>(`/api/v1/meta-accounts?${query({ page: 1, page_size: 100, client_id: filters.clientId })}`, token),
        apiGet<Page<Campaign>>(`/api/v1/campaigns?${query({ page: 1, page_size: 100, meta_account_id: filters.accountId })}`, token),
        apiGet<Dashboard>(`/api/v1/dashboard?${query({ days: filters.days, client_id: filters.clientId, meta_account_id: filters.accountId, campaign_id: filters.campaignId })}`, token),
        apiGet<Page<Improvement>>("/api/v1/improvements?page=1&page_size=20", token),
      ]);
      setClients(clientPage.items); setAccounts(accountPage.items); setCampaigns(campaignPage.items); setDashboard(dashboardData); setImprovements(improvementPage.items);
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

  async function decide(item: Recommendation, status: "ACCEPTED" | "REJECTED") {
    if (!session?.access_token || !dashboard) return;
    setError("");
    try {
      await apiPost("/api/v1/recommendations/decision", session.access_token, {
        ...item, status, note: null,
        period_from: dashboard.period.date_from, period_to: dashboard.period.date_to,
      });
      setDecisions((current) => ({ ...current, [item.key]: status }));
      if (status === "ACCEPTED") await loadData();
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Não foi possível registrar a decisão."); }
  }

  function navigate(next: MainView) {
    setView(next);
    if (next === "settings") return;
    window.setTimeout(() => window.scrollTo({ top: 0, behavior: "smooth" }), 0);
  }

  const hasFilters = Boolean(filters.clientId || filters.accountId || filters.campaignId || filters.days !== 30);
  const clearFilters = () => setFilters({ days: 30, clientId: "", accountId: "", campaignId: "" });
  const pageCopy = view === "campaigns"
    ? { eyebrow: "DESEMPENHO POR ESTRUTURA", title: "Campanhas", subtitle: "Compare campanhas, conjuntos e anúncios sem misturar diagnósticos." }
    : view === "analyses"
      ? { eyebrow: "DIAGNÓSTICO DO FUNIL", title: "Análises", subtitle: "Descubra em qual etapa a campanha está perdendo eficiência." }
      : { eyebrow: "PAINEL DE PERFORMANCE", title: "Visão geral", subtitle: "O que aconteceu, o que mudou e onde olhar primeiro." };

  if (!isSupabaseConfigured) return <main className="center-screen"><div className="brand-mark">D</div><h2>Frontend ainda não configurado</h2><p>Crie o arquivo <code>.env.local</code> conforme o README.</p></main>;
  if (!authReady) return <main className="center-screen"><div className="spinner" /><p>Preparando seu painel…</p></main>;
  if (!session) return <main className="login-shell"><section className="login-story"><div className="brand-mark">D</div><p className="eyebrow">DESCOMPLIADS</p><h1>Decisões melhores começam com números claros.</h1><p>Campanhas, comparações e sinais de desempenho em um só lugar — sem alterar nada na Meta.</p><div className="trust-line"><i /> Dados protegidos por usuário e cliente</div></section><section className="login-panel"><form onSubmit={signIn}><div><p className="eyebrow coral">ACESSO SEGURO</p><h2>Bem-vinda de volta</h2><p>Use o usuário criado no Supabase.</p></div><label>E-mail<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" placeholder="voce@empresa.com" /></label><label>Senha<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password" placeholder="••••••••" /></label>{authError && <p className="form-error">{authError}</p>}<button type="submit">Entrar no painel <span>→</span></button><small>O token permanece na sessão do navegador e nunca é exibido.</small></form></section></main>;

  return <main className="app-shell">
    <aside><div className="logo"><div className="brand-mark small">D</div><div><strong>DescompliADS</strong><small>Growth Intelligence</small></div></div><nav aria-label="Navegação principal"><button className={view === "dashboard" ? "active" : ""} onClick={() => navigate("dashboard")}>◫ <span>Visão geral</span></button><button className={view === "campaigns" ? "active" : ""} onClick={() => navigate("campaigns")}>◎ <span>Campanhas</span></button><button className={view === "analyses" ? "active" : ""} onClick={() => navigate("analyses")}>◇ <span>Análises</span></button><button className={view === "settings" ? "active" : ""} onClick={() => navigate("settings")}>⚙ <span>Ajustes</span></button></nav><div className="sidebar-foot"><span className="status-dot" /> Sistema conectado<button onClick={() => supabase.auth.signOut()}>Sair</button></div></aside>
    {view === "settings" ? <section className="workspace"><SettingsPanel token={session.access_token} clients={clients} userEmail={session.user.email ?? "Usuário autenticado"} /></section> : <section className="workspace" id="dashboard-top"><header><div><p className="eyebrow coral">{pageCopy.eyebrow}</p><h1>{pageCopy.title}</h1><p>{pageCopy.subtitle}</p></div></header>
      <section className="filters"><div className="filter-heading"><strong>Filtrar resultados</strong><small>Escolha o período e refine somente se precisar.</small></div><label>Período<select value={filters.days} onChange={(e) => setFilters({ ...filters, days: Number(e.target.value) })}>{periods.map((days) => <option key={days} value={days}>Últimos {days} dias</option>)}</select></label><label>Cliente<select value={filters.clientId} onChange={(e) => setFilters({ ...filters, clientId: e.target.value, accountId: "", campaignId: "" })}><option value="">Todos</option>{clients.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>Conta<select value={filters.accountId} onChange={(e) => setFilters({ ...filters, accountId: e.target.value, campaignId: "" })}><option value="">Todas</option>{accounts.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>Campanha<select value={filters.campaignId} onChange={(e) => setFilters({ ...filters, campaignId: e.target.value })}><option value="">Todas</option>{campaigns.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><div className="filter-actions">{hasFilters && <button className="clear-button" onClick={clearFilters}>Limpar</button>}<button className="primary-button" onClick={() => void loadData()} disabled={loading}>{loading ? "Atualizando…" : "Ver resultados"}</button></div></section>
      {error && <div className="error-banner"><span>{error}</span><button onClick={() => void loadData()}>Tentar novamente</button></div>}
      {loading && !dashboard && <section className="dashboard-loading" aria-label="Carregando painel"><div /><div /><div /><div /></section>}
      {!loading && !dashboard && !error && <div className="empty-state dashboard-empty"><strong>O painel ainda não possui informações.</strong><span>Verifique a conexão Meta em Ajustes ou atualize os resultados.</span><button onClick={() => navigate("settings")}>Abrir Ajustes</button></div>}
      {dashboard && <>{dashboard.metrics.spend === 0 && <div className="guidance-banner"><div><strong>Nenhum investimento encontrado neste período.</strong><span>Isso não é um erro. Escolha um período em que as campanhas estiveram ativas ou mantenha esta visão para acompanhar a próxima coleta.</span></div><button onClick={() => setFilters({ ...filters, days: 120 })}>Ver 120 dias</button></div>}<section className="period-line"><span>{friendlyDate(dashboard.period.date_from)} → {friendlyDate(dashboard.period.date_to)}</span><small>comparado a {friendlyDate(dashboard.previous_period.date_from)} → {friendlyDate(dashboard.previous_period.date_to)}</small></section>
        {view === "dashboard" && <><ExecutiveSummary dashboard={dashboard} onOpenAnalyses={() => navigate("analyses")} /><section className="metrics-grid"><MetricCard label="Investimento" metricKey="spend" metrics={dashboard.metrics} change={dashboard.change_percent.spend} /><MetricCard label="Conversas" metricKey="conversations" metrics={dashboard.metrics} change={dashboard.change_percent.conversations} /><MetricCard label="Leads" metricKey="leads" metrics={dashboard.metrics} change={dashboard.change_percent.leads} /><MetricCard label="CPL" metricKey="cpl" metrics={dashboard.metrics} change={dashboard.change_percent.cpl} /><MetricCard label="CTR de link" metricKey="link_ctr" metrics={dashboard.metrics} change={dashboard.change_percent.link_ctr} /><MetricCard label="CPM" metricKey="cpm" metrics={dashboard.metrics} change={dashboard.change_percent.cpm} /></section>
          <section className="content-grid"><article className="panel"><div className="panel-title"><div><p className="eyebrow">EVOLUÇÃO DIÁRIA</p><h2>Investimento por dia</h2></div><span className="pill">{dashboard.daily_series.length} dias</span></div><div className="bars">{dashboard.daily_series.map((point) => { const maximum = Math.max(...dashboard.daily_series.map((item) => item.spend), 1); return <div className="bar-column" key={point.metric_date} title={`${point.metric_date}: ${currency.format(point.spend)}`}><div style={{ height: `${Math.max((point.spend / maximum) * 100, point.spend ? 4 : 0)}%` }} /><small>{point.metric_date.slice(5)}</small></div>; })}</div></article><article className="panel insights-panel"><p className="eyebrow">DIAGNÓSTICO POR REGRAS</p><h2>Sinais do período</h2><div className="insight-list">{dashboard.insights.map((insight) => <div className={`insight ${insight.severity.toLowerCase()}`} key={insight.code}><strong>{insight.title}</strong><p>{insight.message}</p></div>)}</div><small>Nenhuma ação é executada automaticamente.</small></article></section>
          <section className="content-grid"><article className="panel structure-panel"><div className="panel-title"><div><p className="eyebrow">ESTRUTURA IMPORTADA</p><h2>Conta em números</h2></div><span className="pill">Somente leitura</span></div><div className="structure-flow">{[[dashboard.clients,"Clientes"],[dashboard.meta_accounts,"Contas"],[dashboard.campaigns,"Campanhas"],[dashboard.adsets,"Conjuntos"],[dashboard.ads,"Anúncios"]].map(([value,label]) => <div key={label}><strong>{value}</strong><span>{label}</span></div>)}</div></article><article className="panel signal-panel"><p className="eyebrow">LEITURA RÁPIDA</p><h2>Sinal do período</h2><div className="signal"><span>{dashboard.metrics.conversations > 0 ? "↗" : "—"}</span><div><strong>{dashboard.metrics.conversations > 0 ? `${dashboard.metrics.conversations} conversas registradas` : "Sem conversões no período"}</strong><p>{dashboard.metrics.conversations > 0 ? `Custo médio de ${currency.format(dashboard.metrics.spend / dashboard.metrics.conversations)} por conversa.` : "Amplie o período ou revise a coleta antes de concluir."}</p></div></div><small>Interpretação determinística. IA entra na próxima entrega.</small></article></section>
          <section className="analytics-dashboard"><div className="analytics-heading"><div><p className="eyebrow coral">MAPA DE PERFORMANCE</p><h2>Quem converte, onde e quando</h2><p>Os gráficos usam recortes independentes da Meta e não alteram os totais do painel.</p></div><span className="pill">Atualização diária</span></div><div className="analytics-grid"><BreakdownChart title="Faixas etárias" subtitle="PÚBLICO · IDADE" points={dashboard.breakdowns?.age ?? []} /><BreakdownChart title="Gênero" subtitle="PÚBLICO · GÊNERO" points={dashboard.breakdowns?.gender ?? []} /><BreakdownChart title="Posicionamentos" subtitle="CANAIS · PLACEMENT" points={dashboard.breakdowns?.placement ?? []} /><BreakdownChart title="Plataformas" subtitle="CANAIS · FACEBOOK X INSTAGRAM" points={dashboard.breakdowns?.platform ?? []} /><BreakdownChart title="Dispositivos" subtitle="EXPERIÊNCIA · MOBILE X DESKTOP" points={dashboard.breakdowns?.device ?? []} /><BreakdownChart title="Regiões" subtitle="GEOGRAFIA · MELHORES RESULTADOS" points={dashboard.breakdowns?.region ?? []} /></div><TimeHeatmap points={dashboard.breakdowns?.hour ?? []} /></section></>}
        {view === "campaigns" && <><section className="metrics-grid campaign-metrics"><MetricCard label="Investimento" metricKey="spend" metrics={dashboard.metrics} change={dashboard.change_percent.spend} /><MetricCard label="Impressões" metricKey="impressions" metrics={dashboard.metrics} change={dashboard.change_percent.impressions} /><MetricCard label="Alcance" metricKey="reach" metrics={dashboard.metrics} change={dashboard.change_percent.reach} /><MetricCard label="Cliques no link" metricKey="link_clicks" metrics={dashboard.metrics} change={dashboard.change_percent.link_clicks} /><MetricCard label="Frequência" metricKey="frequency" metrics={dashboard.metrics} change={dashboard.change_percent.frequency} /><MetricCard label="CPM" metricKey="cpm" metrics={dashboard.metrics} change={dashboard.change_percent.cpm} /></section>
          <section className="panel table-panel"><div className="panel-title"><div><p className="eyebrow">RANKING</p><h2>Campanhas por investimento</h2></div><span>{dashboard.campaign_ranking.length} com entrega</span></div><div className="table-wrap"><table><thead><tr><th>Campanha</th><th>Investimento</th><th>Conversas</th><th>CTR</th><th>Custo/conversa</th></tr></thead><tbody>{dashboard.campaign_ranking.map((campaign) => <tr key={campaign.campaign_id}><td>{campaign.name}</td><td>{currency.format(campaign.spend)}</td><td>{integer.format(campaign.conversations)}</td><td>{campaign.ctr === null ? "—" : `${decimal.format(campaign.ctr)}%`}</td><td>{campaign.cost_per_conversation === null ? "—" : currency.format(campaign.cost_per_conversation)}</td></tr>)}</tbody></table></div></section>
          <section className="ranking-grid"><RankingTable title="Conjuntos" items={dashboard.adset_ranking} /><RankingTable title="Anúncios" items={dashboard.ad_ranking} /></section>
          <section className="panel table-panel"><div className="panel-title"><div><p className="eyebrow">ESTRUTURA</p><h2>Todas as campanhas</h2></div><span>{campaigns.length} exibidas</span></div><div className="table-wrap"><table><thead><tr><th>Campanha</th><th>Objetivo</th><th>Situação</th></tr></thead><tbody>{campaigns.map((campaign) => <tr key={campaign.id}><td>{campaign.name}</td><td>{campaign.objective ?? "Não informado"}</td><td><span className={`status ${campaign.status.toLowerCase()}`}>{campaign.status === "ACTIVE" ? "Ativa" : "Arquivada"}</span></td></tr>)}</tbody></table></div></section></>}
        {view === "analyses" && <><section className="funnel-section"><div className="funnel-heading"><span>1</span><div><p className="eyebrow">TOPO DO FUNIL</p><h2>O criativo prende atenção?</h2></div></div><div className="funnel-grid"><FunnelMetric label="Hook Rate" source="Requer eventos de vídeo" description="Visualizações de 3 segundos ÷ impressões. Abaixo de 25–30% pode indicar um gancho fraco." /><FunnelMetric label="Hold / ThruPlay Rate" source="Requer eventos de vídeo" description="Mostra se o roteiro mantém a atenção depois do início." /><FunnelMetric label="CTR de link" value={metricValue("link_ctr", dashboard.metrics.link_ctr)} description="Mede se a mensagem e a oferta geram interesse em quem viu o anúncio." /><FunnelMetric label="CPM" value={metricValue("cpm", dashboard.metrics.cpm)} description="Termômetro de competição, qualidade da audiência e possível fadiga." /><FunnelMetric label="Frequência" value={metricValue("frequency", dashboard.metrics.frequency)} warning={(dashboard.metrics.frequency ?? 0) >= 3} description="Acima de 3–4 pode sinalizar saturação em públicos frios pequenos." /></div></section>
          <section className="funnel-section"><div className="funnel-heading"><span>2</span><div><p className="eyebrow">MEIO DO FUNIL</p><h2>A página e a oferta convertem?</h2></div></div><div className="funnel-grid"><FunnelMetric label="Taxa de chegada à página" source="Requer Landing Page Views" description="LPV ÷ cliques no link. Quedas apontam lentidão ou instabilidade da página." /><FunnelMetric label="Conversão da página" source="Requer Landing Page Views" description="Leads ÷ LPV. Isola a capacidade da página e da oferta de gerar cadastros." /></div></section>
          <section className="funnel-section"><div className="funnel-heading"><span>3</span><div><p className="eyebrow">FUNDO DO FUNIL</p><h2>O investimento gera negócio?</h2></div></div><div className="funnel-grid"><FunnelMetric label="ROAS" source="Requer receita atribuída" description="Receita atribuída ÷ mídia. Deve ser interpretado junto com a margem." /><FunnelMetric label="MER" source="Requer receita total" description="Receita total ÷ investimento total. Reduz distorções entre campanhas." /><FunnelMetric label="CAC x LTV" source="Requer CRM e vendas" description="Compara o custo real de aquisição com o valor gerado pelo cliente." /></div></section>
          <section className="panel recommendations-panel"><div className="panel-title"><div><p className="eyebrow">DECISÕES ASSISTIDAS</p><h2>Recomendações explicáveis</h2></div><span className="pill">Aprovação humana</span></div><div className="recommendation-list">{dashboard.recommendations.length === 0 && <div className="empty-state">Nenhum sinal forte para recomendar uma ação neste período.</div>}{dashboard.recommendations.map((item) => { const decision = decisions[item.key] ?? (item.status === "PENDING" ? undefined : item.status); return <article className={`recommendation-card priority-${item.priority.toLowerCase()}`} key={item.key}><div><span className="priority">{item.priority === "HIGH" ? "Alta prioridade" : "Prioridade média"}</span><h3>{item.title}</h3><strong>{item.entity_name}</strong><p>{item.explanation}</p><small><b>Evidência:</b> {item.evidence}</small><small><b>Impacto esperado:</b> {item.expected_impact}</small></div>{decision ? <div className={`decision ${decision.toLowerCase()}`}>{decision === "ACCEPTED" ? "Aceita para acompanhamento" : "Rejeitada"}</div> : <div className="decision-actions"><button onClick={() => void decide(item, "REJECTED")}>Rejeitar</button><button onClick={() => void decide(item, "ACCEPTED")}>Aceitar e acompanhar</button></div>}</article>; })}</div></section>
          <section className="panel table-panel"><div className="panel-title"><div><p className="eyebrow">ACOMPANHAMENTO</p><h2>Melhorias aprovadas</h2></div><span>{improvements.length} registradas</span></div><div className="table-wrap"><table><thead><tr><th>Melhoria</th><th>Estado</th><th>Métrica</th><th>Antes</th><th>Depois</th><th>Resultado</th></tr></thead><tbody>{improvements.map((item) => <tr key={item.id}><td>{item.title}</td><td>{item.status === "PLANNED" ? "Planejada" : item.status}</td><td>{item.metric_name ?? "A definir"}</td><td>{item.before_value ?? "—"}</td><td>{item.after_value ?? "—"}</td><td>{item.result ?? "Em acompanhamento"}</td></tr>)}</tbody></table></div></section></>}
      </>}
    </section>}
  </main>;
}
