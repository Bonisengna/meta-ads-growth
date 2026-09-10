import type { AdOperation, AdsetOperation, CampaignOperation, EntityStatus, Metrics } from "@/lib/types";

export type OperationLevel = "CAMPAIGN" | "ADSET" | "AD";

export type OperationRow = {
  key: string;
  id: string;
  level: OperationLevel;
  name: string;
  status: EntityStatus;
  metrics: Metrics;
  campaignName: string;
  adsetName: string | null;
  configuredBudget: number | null;
  budgetUtilization: number | null;
  campaign?: CampaignOperation;
  adset?: AdsetOperation;
  ad?: AdOperation;
};

export function normalizeOperationSearch(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("pt-BR")
    .trim();
}

export function operationNameMatches(name: string, search: string): boolean {
  const normalizedSearch = normalizeOperationSearch(search);
  return normalizedSearch.length === 0
    || normalizeOperationSearch(name).includes(normalizedSearch);
}

export function searchCampaignOperations(
  campaigns: CampaignOperation[],
  search: string,
): CampaignOperation[] {
  const normalizedSearch = normalizeOperationSearch(search);
  if (!normalizedSearch) return campaigns;

  return campaigns.flatMap((campaign) => {
    if (operationNameMatches(campaign.name, normalizedSearch)) return [campaign];

    const adsets = campaign.adsets.flatMap((adset) => {
      if (operationNameMatches(adset.name, normalizedSearch)) return [adset];
      const ads = adset.ads.filter((ad) => operationNameMatches(ad.name, normalizedSearch));
      return ads.length > 0 ? [{ ...adset, ads }] : [];
    });

    return adsets.length > 0 ? [{ ...campaign, adsets }] : [];
  });
}

export function isActiveWithoutDelivery(campaign: CampaignOperation): boolean {
  return campaign.status === "ACTIVE" && !campaign.has_delivery;
}

export function flattenOperationRows(campaigns: CampaignOperation[]): OperationRow[] {
  return campaigns.flatMap((campaign) => {
    const campaignRow: OperationRow = {
      key: `CAMPAIGN:${campaign.id}`,
      id: campaign.id,
      level: "CAMPAIGN",
      name: campaign.name,
      status: campaign.status,
      metrics: campaign.metrics,
      campaignName: campaign.name,
      adsetName: null,
      configuredBudget: campaign.configured_budget,
      budgetUtilization: campaign.budget_utilization,
      campaign,
    };
    const childRows = campaign.adsets.flatMap((adset) => {
      const adsetRow: OperationRow = {
        key: `ADSET:${adset.id}`,
        id: adset.id,
        level: "ADSET",
        name: adset.name,
        status: adset.status,
        metrics: adset.metrics,
        campaignName: campaign.name,
        adsetName: adset.name,
        configuredBudget: adset.configured_budget,
        budgetUtilization: adset.budget_utilization,
        adset,
      };
      const adRows: OperationRow[] = adset.ads.map((ad) => ({
        key: `AD:${ad.id}`,
        id: ad.id,
        level: "AD",
        name: ad.name,
        status: ad.status,
        metrics: ad.metrics,
        campaignName: campaign.name,
        adsetName: adset.name,
        configuredBudget: null,
        budgetUtilization: null,
        ad,
      }));
      return [adsetRow, ...adRows];
    });
    return [campaignRow, ...childRows];
  });
}

export function filterOperationRows(
  rows: OperationRow[],
  filters: {
    level: OperationLevel;
    search: string;
    status: "ALL" | EntityStatus;
    onlyActiveWithoutDelivery?: boolean;
  },
): OperationRow[] {
  const search = normalizeOperationSearch(filters.search);
  return rows.filter((row) => {
    if (row.level !== filters.level || (filters.status !== "ALL" && row.status !== filters.status)) return false;
    if (filters.onlyActiveWithoutDelivery && (row.level !== "CAMPAIGN" || !row.campaign || !isActiveWithoutDelivery(row.campaign))) return false;
    if (!search) return true;
    const searchableText = normalizeOperationSearch(
      [row.name, row.campaignName, row.adsetName ?? ""].join(" "),
    );
    return search.split(/\s+/).every((term) => searchableText.includes(term));
  });
}

export function operationMetricNumber(
  row: OperationRow,
  key: keyof Metrics | "results" | "budget",
): number | null {
  if (key === "results") return row.metrics.leads + row.metrics.conversations;
  if (key === "budget") return row.configuredBudget;
  const value = row.metrics[key];
  return value == null ? null : Number(value);
}

export function sortOperationRows(
  rows: OperationRow[],
  key: keyof Metrics | "results" | "budget",
  descending: boolean,
): OperationRow[] {
  return [...rows].sort((left, right) => {
    const leftValue = operationMetricNumber(left, key);
    const rightValue = operationMetricNumber(right, key);
    if (leftValue == null && rightValue != null) return 1;
    if (leftValue != null && rightValue == null) return -1;
    if (leftValue == null && rightValue == null) return left.name.localeCompare(right.name, "pt-BR");
    const difference = leftValue! - rightValue!;
    if (difference !== 0) return difference * (descending ? -1 : 1);
    return left.name.localeCompare(right.name, "pt-BR");
  });
}

function safeCsvValue(value: unknown): string {
  const text = String(value ?? "");
  const protectedText = /^[=+\-@]/.test(text.trimStart()) ? `'${text}` : text;
  return `"${protectedText.replaceAll('"', '""')}"`;
}

export function buildOperationCsv(headers: string[], rows: unknown[][]): string {
  return `\uFEFF${[headers, ...rows].map((row) => row.map(safeCsvValue).join(";")).join("\r\n")}`;
}
