"use client";

import { Fragment, useEffect, useMemo, useState } from "react";

import {
  buildOperationCsv,
  filterOperationRows,
  flattenOperationRows,
  operationNameMatches,
  searchCampaignOperations,
  sortOperationRows,
  type OperationLevel,
  type OperationRow,
} from "@/lib/operations";
import type { AdOperation, CampaignOperation, EntityStatus, Metrics } from "@/lib/types";

const currency = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const integer = new Intl.NumberFormat("pt-BR");
const decimal = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 });

type OperationColumn =
  | "spend"
  | "impressions"
  | "reach"
  | "results"
  | "cpl"
  | "link_clicks"
  | "link_ctr"
  | "frequency"
  | "cpm"
  | "landing_page_views"
  | "landing_page_view_rate"
  | "cost_per_landing_page_view"
  | "landing_page_conversion_rate"
  | "video_views_3s"
  | "hook_rate"
  | "thruplays"
  | "thruplay_rate"
  | "video_p25_rate"
  | "video_p50_rate"
  | "video_p75_rate"
  | "video_p95_rate"
  | "budget";

const operationColumnLabels: Record<OperationColumn, string> = {
  spend: "Investimento",
  impressions: "Impressões",
  reach: "Alcance",
  results: "Resultados",
  cpl: "CPL",
  link_clicks: "Cliques no link",
  link_ctr: "CTR de link",
  frequency: "Frequência no período",
  cpm: "CPM",
  landing_page_views: "Visualizações da página",
  landing_page_view_rate: "Taxa de chegada",
  cost_per_landing_page_view: "Custo por visita",
  landing_page_conversion_rate: "Leads por visita",
  video_views_3s: "Vídeos 3s",
  hook_rate: "Taxa de gancho",
  thruplays: "ThruPlay",
  thruplay_rate: "Taxa de ThruPlay",
  video_p25_rate: "Retenção 25%",
  video_p50_rate: "Retenção 50%",
  video_p75_rate: "Retenção 75%",
  video_p95_rate: "Retenção 95%",
  budget: "Orçamento",
};

const defaultColumns: OperationColumn[] = [
  "spend", "results", "link_clicks", "link_ctr", "frequency", "cpm", "budget",
];
const columnKeys = Object.keys(operationColumnLabels) as OperationColumn[];
const levelLabels: Record<OperationLevel, string> = {
  CAMPAIGN: "Campanhas",
  ADSET: "Conjuntos",
  AD: "Anúncios",
};

function safeExternalUrl(value: string | null): string | null {
  if (!value) return null;
  try {
    const parsed = new URL(value);
    return parsed.protocol === "https:" ? parsed.toString() : null;
  } catch {
    return null;
  }
}

function CreativeSummary({ ad, hierarchy }: { ad: AdOperation; hierarchy?: string }) {
  const image = ad.thumbnail_url ?? ad.image_url;
  const destination = safeExternalUrl(ad.destination_url);
  return <div className="creative-summary">{image ? <span className="creative-image" role="img" aria-label={`Criativo do anúncio ${ad.name}`} style={{ backgroundImage: `url(${image})` }} /> : <span className="creative-fallback" aria-hidden="true">{ad.creative_type === "VIDEO" ? "▶" : "▧"}</span>}<div><strong title={ad.name}>{ad.name}</strong>{hierarchy && <small className="creative-hierarchy">{hierarchy}</small>}<small>{ad.creative_type ?? "Formato não informado"}{ad.video_duration_seconds ? ` · ${decimal.format(ad.video_duration_seconds)}s` : ""}</small>{ad.headline && <b title={ad.headline}>{ad.headline}</b>}{ad.primary_text && <p title={ad.primary_text}>{ad.primary_text}</p>}<div className="creative-meta">{ad.call_to_action_type && <em>CTA: {ad.call_to_action_type.replaceAll("_", " ")}</em>}{destination && <a href={destination} target="_blank" rel="noreferrer noopener" aria-label={`Abrir destino do anúncio ${ad.name}`}>Abrir destino</a>}</div></div></div>;
}

function statusLabel(status: EntityStatus, level: OperationLevel): string {
  if (status === "ARCHIVED") return level === "CAMPAIGN" ? "Arquivada" : "Arquivado";
  if (status === "PAUSED") return level === "CAMPAIGN" ? "Pausada" : "Pausado";
  return level === "CAMPAIGN" ? "Ativa" : "Ativo";
}

function formatCell(
  metrics: Metrics,
  column: OperationColumn,
  budget?: number | null,
  utilization?: number | null,
): string {
  if (column === "spend") return currency.format(metrics.spend);
  if (column === "impressions") return integer.format(metrics.impressions);
  if (column === "reach") return metrics.reach == null ? "—" : integer.format(metrics.reach);
  if (column === "results") return integer.format(metrics.leads + metrics.conversations);
  if (column === "cpl") return metrics.cpl == null ? "—" : currency.format(metrics.cpl);
  if (column === "link_clicks") return integer.format(metrics.link_clicks);
  if (column === "link_ctr") return metrics.link_ctr == null ? "—" : `${decimal.format(metrics.link_ctr)}%`;
  if (column === "frequency") return metrics.frequency == null ? "—" : decimal.format(metrics.frequency);
  if (column === "cpm") return metrics.cpm == null ? "—" : currency.format(metrics.cpm);
  if (column === "landing_page_views") return integer.format(metrics.landing_page_views);
  if (column === "landing_page_view_rate") return metrics.landing_page_view_rate == null ? "—" : `${decimal.format(metrics.landing_page_view_rate)}%`;
  if (column === "cost_per_landing_page_view") return metrics.cost_per_landing_page_view == null ? "—" : currency.format(metrics.cost_per_landing_page_view);
  if (column === "landing_page_conversion_rate") return metrics.landing_page_conversion_rate == null ? "—" : `${decimal.format(metrics.landing_page_conversion_rate)}%`;
  if (column === "video_views_3s") return integer.format(metrics.video_views_3s);
  if (column === "hook_rate") return metrics.hook_rate == null ? "—" : `${decimal.format(metrics.hook_rate)}%`;
  if (column === "thruplays") return integer.format(metrics.thruplays);
  if (column === "thruplay_rate") return metrics.thruplay_rate == null ? "—" : `${decimal.format(metrics.thruplay_rate)}%`;
  if (column === "video_p25_rate") return metrics.video_p25_rate == null ? "—" : `${decimal.format(metrics.video_p25_rate)}%`;
  if (column === "video_p50_rate") return metrics.video_p50_rate == null ? "—" : `${decimal.format(metrics.video_p50_rate)}%`;
  if (column === "video_p75_rate") return metrics.video_p75_rate == null ? "—" : `${decimal.format(metrics.video_p75_rate)}%`;
  if (column === "video_p95_rate") return metrics.video_p95_rate == null ? "—" : `${decimal.format(metrics.video_p95_rate)}%`;
  return budget == null ? "Não configurado" : `${currency.format(budget)} · ${utilization == null ? "—" : `${decimal.format(utilization)}%`}`;
}

function hierarchyLabel(row: OperationRow): string {
  if (row.level === "CAMPAIGN") return "Campanha";
  if (row.level === "ADSET") return `Campanha: ${row.campaignName}`;
  return `Campanha: ${row.campaignName} · Conjunto: ${row.adsetName ?? "—"}`;
}

export default function OperationalCampaignTable({ items }: { items: CampaignOperation[] }) {
  const [search, setSearch] = useState("");
  const [level, setLevel] = useState<OperationLevel>("CAMPAIGN");
  const [status, setStatus] = useState<"ALL" | EntityStatus>("ALL");
  const [onlyActiveWithoutDelivery, setOnlyActiveWithoutDelivery] = useState(false);
  const [sort, setSort] = useState<OperationColumn>("spend");
  const [descending, setDescending] = useState(true);
  const [columns, setColumns] = useState<OperationColumn[]>(defaultColumns);
  const [preferencesLoaded, setPreferencesLoaded] = useState(false);
  const [expandedCampaigns, setExpandedCampaigns] = useState<string[]>([]);
  const [expandedAdsets, setExpandedAdsets] = useState<string[]>([]);
  const [compared, setCompared] = useState<string[]>([]);
  const [exportMessage, setExportMessage] = useState("");

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      try {
        const saved = window.localStorage.getItem("descompliads.operation.preferences.v1");
        if (saved) {
          const parsed = JSON.parse(saved) as { level?: OperationLevel; status?: "ALL" | EntityStatus; sort?: OperationColumn; descending?: boolean; columns?: OperationColumn[] };
          if (parsed.level && ["CAMPAIGN", "ADSET", "AD"].includes(parsed.level)) setLevel(parsed.level);
          if (parsed.status && ["ALL", "ACTIVE", "PAUSED", "ARCHIVED"].includes(parsed.status)) setStatus(parsed.status);
          if (parsed.sort && columnKeys.includes(parsed.sort)) setSort(parsed.sort);
          if (typeof parsed.descending === "boolean") setDescending(parsed.descending);
          const validColumns = parsed.columns?.filter((column) => columnKeys.includes(column));
          if (validColumns?.length) setColumns(validColumns);
        }
      } catch {
        // Browsers can block storage; the table remains usable with safe defaults.
      } finally {
        setPreferencesLoaded(true);
      }
    });
    return () => window.cancelAnimationFrame(frame);
  }, []);

  useEffect(() => {
    if (!preferencesLoaded) return;
    try {
      window.localStorage.setItem("descompliads.operation.preferences.v1", JSON.stringify({ level, status, sort, descending, columns }));
    } catch {
      // Preference persistence is optional and must not block the operational view.
    }
  }, [columns, descending, level, preferencesLoaded, sort, status]);

  const allRows = useMemo(() => flattenOperationRows(items), [items]);
  const rowsByKey = useMemo(() => new Map(allRows.map((row) => [row.key, row])), [allRows]);
  const hierarchyRows = useMemo(
    () => flattenOperationRows(searchCampaignOperations(items, search)),
    [items, search],
  );
  const visible = useMemo(() => {
    const source = level === "CAMPAIGN" ? hierarchyRows : allRows;
    const filtered = filterOperationRows(source, {
      level,
      search: level === "CAMPAIGN" ? "" : search,
      status,
      onlyActiveWithoutDelivery: level === "CAMPAIGN" && onlyActiveWithoutDelivery,
    });
    return sortOperationRows(filtered, sort, descending);
  }, [allRows, descending, hierarchyRows, level, onlyActiveWithoutDelivery, search, sort, status]);

  const activeCompared = compared.filter((key) => rowsByKey.has(key));
  const comparedItems = activeCompared.map((key) => rowsByKey.get(key)!) as OperationRow[];
  const toggleExpanded = (id: string, entityLevel: "campaign" | "adset") => {
    const setter = entityLevel === "campaign" ? setExpandedCampaigns : setExpandedAdsets;
    setter((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
  };
  const toggleColumn = (column: OperationColumn) => setColumns((current) => {
    const next = current.includes(column) ? current.filter((item) => item !== column) : [...current, column];
    return next.length ? next : ["spend"];
  });
  const toggleCompared = (row: OperationRow) => setCompared((current) => {
    const available = current.filter((key) => rowsByKey.has(key));
    if (available.includes(row.key)) return available.filter((key) => key !== row.key);
    return available.length < 2 ? [...available, row.key] : available;
  });
  const changeLevel = (next: OperationLevel) => {
    setLevel(next);
    setCompared([]);
    setOnlyActiveWithoutDelivery(false);
  };
  const exportCsv = () => {
    const headers = ["Nível", "Campanha", "Conjunto", "Nome", "Situação", ...columns.map((column) => operationColumnLabels[column])];
    const rows = visible.map((row) => [
      levelLabels[row.level], row.campaignName, row.adsetName ?? "", row.name,
      statusLabel(row.status, row.level),
      ...columns.map((column) => formatCell(row.metrics, column, row.configuredBudget, row.budgetUtilization)),
    ]);
    const blob = new Blob([buildOperationCsv(headers, rows)], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `descompliads-${level.toLowerCase()}-${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
    setExportMessage(`CSV gerado com ${visible.length} ${levelLabels[level].toLowerCase()}.`);
  };
  const metricCells = (row: OperationRow) => columns.map((column) => <td key={column}>{formatCell(row.metrics, column, row.configuredBudget, row.budgetUtilization)}</td>);
  const compareCell = (row: OperationRow) => {
    const checked = activeCompared.includes(row.key);
    const disabled = !checked && activeCompared.length >= 2;
    return <input type="checkbox" aria-label={`Comparar ${levelLabels[row.level].toLowerCase().slice(0, -1)} ${row.name}`} aria-describedby="comparison-help" checked={checked} disabled={disabled} onChange={() => toggleCompared(row)} />;
  };

  const feminineStatus = level === "CAMPAIGN";
  return <section className="panel operation-panel" aria-labelledby="operation-title"><div className="panel-title"><div><p className="eyebrow">OPERAÇÃO</p><h2 id="operation-title">Campanhas, conjuntos e anúncios</h2></div><span aria-live="polite">{visible.length} {levelLabels[level].toLowerCase()}</span></div><p id="comparison-help" className="sr-only">Selecione no máximo duas entidades do mesmo nível para comparar.</p><p className="sr-only" aria-live="polite">{exportMessage}</p><div className="operation-toolbar"><label>Pesquisar<input value={search} onChange={(event) => { setSearch(event.target.value); setCompared([]); }} placeholder="Campanha, conjunto ou anúncio" /></label><label>Nível de análise<select value={level} onChange={(event) => changeLevel(event.target.value as OperationLevel)}><option value="CAMPAIGN">Campanhas</option><option value="ADSET">Conjuntos</option><option value="AD">Anúncios</option></select></label><label>Situação<select value={status} onChange={(event) => { setStatus(event.target.value as "ALL" | EntityStatus); setCompared([]); }}><option value="ALL">{feminineStatus ? "Todas" : "Todos"}</option><option value="ACTIVE">{feminineStatus ? "Ativas" : "Ativos"}</option><option value="PAUSED">{feminineStatus ? "Pausadas" : "Pausados"}</option><option value="ARCHIVED">{feminineStatus ? "Arquivadas" : "Arquivados"}</option></select></label><label>Ordenar por<select value={sort} onChange={(event) => setSort(event.target.value as OperationColumn)}>{Object.entries(operationColumnLabels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label><button type="button" className="sort-direction" aria-label={`Ordenação: ${descending ? "maior primeiro" : "menor primeiro"}`} onClick={() => setDescending((current) => !current)}>{descending ? "Maior primeiro ↓" : "Menor primeiro ↑"}</button>{level === "CAMPAIGN" && <button type="button" className={`delivery-filter${onlyActiveWithoutDelivery ? " active" : ""}`} aria-pressed={onlyActiveWithoutDelivery} onClick={() => { setOnlyActiveWithoutDelivery((current) => !current); setCompared([]); }}>Ativas sem entrega</button>}<details className="column-picker"><summary>Escolher colunas</summary><div>{Object.entries(operationColumnLabels).map(([key, label]) => <label key={key}><input type="checkbox" checked={columns.includes(key as OperationColumn)} onChange={() => toggleColumn(key as OperationColumn)} />{label}</label>)}</div></details><button type="button" className="export-button" disabled={visible.length === 0} onClick={exportCsv}>Exportar CSV</button></div>{onlyActiveWithoutDelivery && <p className="delivery-rule">Sem entrega = campanha ativa com investimento zero e zero impressões no período selecionado.</p>}{comparedItems.length > 0 && <div className="campaign-comparison" aria-live="polite"><div><strong>Comparação de {levelLabels[level].toLowerCase()}</strong><span>{comparedItems.length === 1 ? `Selecione mais ${level === "CAMPAIGN" ? "uma campanha" : level === "ADSET" ? "um conjunto" : "um anúncio"}` : "Compare eficiência e entrega"}</span></div>{comparedItems.map((item) => <article key={item.key}><b title={item.name}>{item.name}</b><span>{currency.format(item.metrics.spend)} investidos</span><span>{item.metrics.leads + item.metrics.conversations} resultados</span><span>CTR {item.metrics.link_ctr == null ? "—" : `${decimal.format(item.metrics.link_ctr)}%`} · Frequência {item.metrics.frequency == null ? "—" : decimal.format(item.metrics.frequency)}</span></article>)}<button type="button" onClick={() => setCompared([])}>Limpar comparação</button></div>}<div className="table-wrap operation-table-wrap"><table className="operation-table"><caption className="sr-only">Desempenho filtrado de {levelLabels[level].toLowerCase()}</caption><thead><tr><th>Estrutura</th><th>Comparar (máx. 2)</th><th>Situação</th>{columns.map((column) => <th key={column}>{operationColumnLabels[column]}</th>)}</tr></thead><tbody>{visible.length === 0 ? <tr><td colSpan={columns.length + 3} className="empty-cell">Nenhum resultado entre {levelLabels[level].toLowerCase()} para os filtros atuais. <button type="button" onClick={() => { setSearch(""); setStatus("ALL"); setOnlyActiveWithoutDelivery(false); }}>Limpar filtros</button></td></tr> : level !== "CAMPAIGN" ? visible.map((row) => <tr className={row.level === "ADSET" ? "adset-row flat-row" : "ad-row flat-row"} key={row.key}><td>{row.ad ? <CreativeSummary ad={row.ad} hierarchy={hierarchyLabel(row)} /> : <div className="flat-entity"><strong>{row.name}</strong><small>{hierarchyLabel(row)}</small></div>}</td><td>{compareCell(row)}</td><td><span className={`status ${row.status.toLowerCase()}`}>{statusLabel(row.status, row.level)}</span></td>{metricCells(row)}</tr>) : visible.map((row) => { const campaign = row.campaign!; const campaignAutoExpanded = !!search.trim() && !operationNameMatches(campaign.name, search); const campaignExpanded = expandedCampaigns.includes(campaign.id) || campaignAutoExpanded; return <Fragment key={campaign.id}><tr className={campaign.has_delivery ? "" : campaign.status === "ACTIVE" ? "no-delivery" : ""}><td><button type="button" className="expand-button" aria-label={campaignAutoExpanded ? `Campanha ${campaign.name} expandida pela pesquisa` : `${campaignExpanded ? "Recolher" : "Expandir"} campanha ${campaign.name}`} aria-expanded={campaignExpanded} aria-disabled={campaignAutoExpanded} disabled={campaignAutoExpanded} onClick={() => toggleExpanded(campaign.id, "campaign")}>{campaignExpanded ? "−" : "+"}</button><strong>{campaign.name}</strong>{campaign.status === "ACTIVE" && !campaign.has_delivery && <span className="delivery-badge">Sem entrega</span>}</td><td>{compareCell(row)}</td><td><span className={`status ${campaign.status.toLowerCase()}`}>{statusLabel(campaign.status, "CAMPAIGN")}</span></td>{metricCells(row)}</tr>{campaignExpanded && campaign.adsets.map((adset) => { const adsetAutoExpanded = !!search.trim() && !operationNameMatches(adset.name, search) && adset.ads.some((ad) => operationNameMatches(ad.name, search)); const adsetExpanded = expandedAdsets.includes(adset.id) || adsetAutoExpanded; const adsetRow = rowsByKey.get(`ADSET:${adset.id}`)!; return <Fragment key={adset.id}><tr className="adset-row"><td><button type="button" className="expand-button" aria-label={adsetAutoExpanded ? `Conjunto ${adset.name} expandido pela pesquisa` : `${adsetExpanded ? "Recolher" : "Expandir"} conjunto ${adset.name}`} aria-expanded={adsetExpanded} aria-disabled={adsetAutoExpanded} disabled={adsetAutoExpanded} onClick={() => toggleExpanded(adset.id, "adset")}>{adsetExpanded ? "−" : "+"}</button><div><strong>{adset.name}</strong><small>Conjunto · {adset.optimization_goal ?? "objetivo não informado"}</small></div></td><td /><td><span className={`status ${adset.status.toLowerCase()}`}>{statusLabel(adset.status, "ADSET")}</span></td>{metricCells(adsetRow)}</tr>{adsetExpanded && adset.ads.map((ad) => { const adRow = rowsByKey.get(`AD:${ad.id}`)!; return <tr className="ad-row" key={ad.id}><td><CreativeSummary ad={ad} /></td><td /><td><span className={`status ${ad.status.toLowerCase()}`}>{statusLabel(ad.status, "AD")}</span></td>{metricCells(adRow)}</tr>; })}</Fragment>; })}</Fragment>; })}</tbody></table></div></section>;
}
