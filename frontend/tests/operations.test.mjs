import assert from "node:assert/strict";
import test from "node:test";

import {
  isActiveWithoutDelivery,
  operationNameMatches,
  searchCampaignOperations,
} from "../src/lib/operations.ts";

const campaign = {
  id: "campaign-1",
  name: "Captação São Paulo",
  status: "ACTIVE",
  has_delivery: false,
  adsets: [
    {
      id: "adset-1",
      name: "Público semelhante",
      status: "ACTIVE",
      ads: [
        { id: "ad-1", name: "Vídeo Depoimento", status: "ACTIVE" },
        { id: "ad-2", name: "Imagem Oferta", status: "PAUSED" },
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
