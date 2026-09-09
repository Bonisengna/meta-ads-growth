import type { CampaignOperation } from "@/lib/types";

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
