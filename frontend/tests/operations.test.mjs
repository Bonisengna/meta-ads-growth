import assert from "node:assert/strict";
import test from "node:test";

import {
  buildOperationCsv,
  filterOperationRows,
  flattenOperationRows,
  isActiveWithoutDelivery,
  operationNameMatches,
  searchCampaignOperations,
  sortOperationRows,
} from "../src/lib/operations.ts";

const metrics = {
  spend: 0, impressions: 0, reach: null, clicks: 0, link_clicks: 0,
  leads: 0, conversations: 0, landing_page_views: 0, video_views_3s: 0,
  video_plays: 0, video_p25: 0, video_p50: 0, video_p75: 0, video_p95: 0,
  thruplays: 0, cpl: null, ctr: null, cpc: null, cpm: null, link_ctr: null,
  frequency: null, landing_page_view_rate: null, cost_per_landing_page_view: null,
  landing_page_conversion_rate: null, hook_rate: null, thruplay_rate: null,
  video_p25_rate: null, video_p50_rate: null, video_p75_rate: null,
  video_p95_rate: null,
};

const campaign = {
  id: "campaign-1",
  name: "Captação São Paulo",
  status: "ACTIVE",
  has_delivery: false,
  configured_budget: 100,
  budget_utilization: 0,
  metrics,
  adsets: [
    {
      id: "adset-1",
      name: "Público semelhante",
      status: "ACTIVE",
      configured_budget: 50,
      budget_utilization: 20,
      metrics: { ...metrics, spend: 10, impressions: 1_000 },
      ads: [
        { id: "ad-1", name: "Vídeo Depoimento", status: "ACTIVE", metrics: { ...metrics, spend: 8 } },
        { id: "ad-2", name: "Imagem Oferta", status: "PAUSED", metrics: { ...metrics, spend: 2 } },
      ],
    },
  ],
};

test("a pesquisa ignora caixa e acentos", () => {
  assert.equal(operationNameMatches("Captação São Paulo", "captacao sao"), true);
});

test("a pesquisa por anúncio preserva somente o caminho ancestral relevante", () => {
  const result = searchCampaignOperations([campaign], "depoimento");

  assert.equal(result.length, 1);
  assert.equal(result[0].adsets.length, 1);
  assert.deepEqual(result[0].adsets[0].ads.map((ad) => ad.id), ["ad-1"]);
});

test("a pesquisa por conjunto mantém seus anúncios disponíveis para inspeção", () => {
  const result = searchCampaignOperations([campaign], "semelhante");

  assert.equal(result[0].adsets[0].ads.length, 2);
});

test("o filtro sem entrega exige campanha ativa e sinal negativo do backend", () => {
  assert.equal(isActiveWithoutDelivery(campaign), true);
  assert.equal(isActiveWithoutDelivery({ ...campaign, status: "PAUSED" }), false);
  assert.equal(isActiveWithoutDelivery({ ...campaign, has_delivery: true }), false);
});

test("a visão por nível preserva a hierarquia e aplica situação e pesquisa", () => {
  const rows = flattenOperationRows([campaign]);
  assert.deepEqual(rows.map((row) => row.level), ["CAMPAIGN", "ADSET", "AD", "AD"]);

  const filtered = filterOperationRows(rows, {
    level: "AD",
    search: "captacao oferta",
    status: "PAUSED",
  });
  assert.deepEqual(filtered.map((row) => row.id), ["ad-2"]);
  assert.equal(filtered[0].campaignName, "Captação São Paulo");
});

test("a ordenação de métricas funciona nos dois sentidos", () => {
  const ads = filterOperationRows(flattenOperationRows([campaign]), {
    level: "AD", search: "", status: "ALL",
  });
  assert.deepEqual(sortOperationRows(ads, "spend", true).map((row) => row.id), ["ad-1", "ad-2"]);
  assert.deepEqual(sortOperationRows(ads, "spend", false).map((row) => row.id), ["ad-2", "ad-1"]);

  const withUnavailableReach = ads.map((row, index) => ({
    ...row,
    metrics: { ...row.metrics, reach: index === 0 ? null : 2 },
  }));
  assert.deepEqual(sortOperationRows(withUnavailableReach, "reach", true).map((row) => row.id), ["ad-2", "ad-1"]);
  assert.deepEqual(sortOperationRows(withUnavailableReach, "reach", false).map((row) => row.id), ["ad-2", "ad-1"]);
});

test("a exportação CSV usa UTF-8, delimitador local e neutraliza fórmulas", () => {
  const csv = buildOperationCsv(["Nome", "Valor"], [["=HYPERLINK(\"x\")", "1,25"]]);
  assert.equal(csv.startsWith("\uFEFF"), true);
  assert.match(csv, /^\uFEFF"Nome";"Valor"\r\n/);
  assert.match(csv, /"'=HYPERLINK\(""x""\)";"1,25"$/);
});
