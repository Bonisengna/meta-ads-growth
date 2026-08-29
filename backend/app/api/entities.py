from datetime import date
from enum import IntEnum
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import SupabaseClient
from app.models.entities import (
    AdMetricRead,
    AdRead,
    AdsetMetricRead,
    AdsetRead,
    CampaignRead,
    CampaignMetricRead,
    ClientRead,
    DashboardRead,
    EntityStatus,
    MetaAccountRead,
    ImprovementRead,
    Page,
    RecommendationDecision,
    RecommendationDecisionRead,
)
from app.services.entity_services import (
    AdService,
    AdsetService,
    CampaignService,
    ClientService,
    DashboardService,
    EntityNotFoundError,
    MetaAccountService,
    MetricService,
    RecommendationService,
)

router = APIRouter()


class DashboardDays(IntEnum):
    DAYS_7 = 7
    DAYS_14 = 14
    DAYS_30 = 30
    DAYS_90 = 90
    DAYS_120 = 120
    DAYS_180 = 180
    DAYS_360 = 360


def not_found(exc: EntityNotFoundError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"message": str(exc), "id": str(exc.entity_id)},
    )


def database_unavailable(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Não foi possível consultar o Supabase.",
    )


@router.get("/clients", response_model=Page[ClientRead], tags=["Clientes"])
def list_clients(
    client: SupabaseClient,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: EntityStatus | None = Query(None, alias="status"),
) -> dict[str, object]:
    try:
        return ClientService(client).list_clients(page, page_size, status_filter)
    except Exception as exc:
        raise database_unavailable(exc) from exc


@router.get("/clients/{client_id}", response_model=ClientRead, tags=["Clientes"])
def get_client(client_id: UUID, client: SupabaseClient) -> dict[str, object]:
    try:
        return ClientService(client).get_client(client_id)
    except EntityNotFoundError as exc:
        raise not_found(exc) from exc
    except Exception as exc:
        raise database_unavailable(exc) from exc


@router.get("/meta-accounts", response_model=Page[MetaAccountRead], tags=["Contas Meta"])
def list_meta_accounts(
    client: SupabaseClient,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: EntityStatus | None = Query(None, alias="status"),
    client_id: UUID | None = None,
) -> dict[str, object]:
    try:
        return MetaAccountService(client).list_meta_accounts(
            page, page_size, status_filter, client_id
        )
    except Exception as exc:
        raise database_unavailable(exc) from exc


@router.get("/campaigns", response_model=Page[CampaignRead], tags=["Campanhas"])
def list_campaigns(
    client: SupabaseClient,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: EntityStatus | None = Query(None, alias="status"),
    meta_account_id: UUID | None = None,
) -> dict[str, object]:
    try:
        return CampaignService(client).list_campaigns(
            page, page_size, status_filter, meta_account_id
        )
    except Exception as exc:
        raise database_unavailable(exc) from exc


@router.get("/campaigns/{campaign_id}", response_model=CampaignRead, tags=["Campanhas"])
def get_campaign(campaign_id: UUID, client: SupabaseClient) -> dict[str, object]:
    try:
        return CampaignService(client).get_campaign(campaign_id)
    except EntityNotFoundError as exc:
        raise not_found(exc) from exc
    except Exception as exc:
        raise database_unavailable(exc) from exc


@router.get("/adsets", response_model=Page[AdsetRead], tags=["Conjuntos"])
def list_adsets(
    client: SupabaseClient,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: EntityStatus | None = Query(None, alias="status"),
    campaign_id: UUID | None = None,
) -> dict[str, object]:
    try:
        return AdsetService(client).list_adsets(page, page_size, status_filter, campaign_id)
    except Exception as exc:
        raise database_unavailable(exc) from exc


@router.get("/adsets/{adset_id}", response_model=AdsetRead, tags=["Conjuntos"])
def get_adset(adset_id: UUID, client: SupabaseClient) -> dict[str, object]:
    try:
        return AdsetService(client).get_adset(adset_id)
    except EntityNotFoundError as exc:
        raise not_found(exc) from exc
    except Exception as exc:
        raise database_unavailable(exc) from exc


@router.get("/ads", response_model=Page[AdRead], tags=["Anúncios"])
def list_ads(
    client: SupabaseClient,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: EntityStatus | None = Query(None, alias="status"),
    adset_id: UUID | None = None,
) -> dict[str, object]:
    try:
        return AdService(client).list_ads(page, page_size, status_filter, adset_id)
    except Exception as exc:
        raise database_unavailable(exc) from exc


@router.get("/ads/{ad_id}", response_model=AdRead, tags=["Anúncios"])
def get_ad(ad_id: UUID, client: SupabaseClient) -> dict[str, object]:
    try:
        return AdService(client).get_ad(ad_id)
    except EntityNotFoundError as exc:
        raise not_found(exc) from exc
    except Exception as exc:
        raise database_unavailable(exc) from exc


@router.get(
    "/metrics/campaigns", response_model=Page[CampaignMetricRead], tags=["Métricas"]
)
def list_campaign_metrics(
    client: SupabaseClient,
    date_from: date,
    date_to: date,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    campaign_id: UUID | None = None,
) -> dict[str, object]:
    return list_metrics(client, "campaigns", date_from, date_to, page, page_size, campaign_id)


@router.get("/metrics/adsets", response_model=Page[AdsetMetricRead], tags=["Métricas"])
def list_adset_metrics(
    client: SupabaseClient,
    date_from: date,
    date_to: date,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    adset_id: UUID | None = None,
) -> dict[str, object]:
    return list_metrics(client, "adsets", date_from, date_to, page, page_size, adset_id)


@router.get("/metrics/ads", response_model=Page[AdMetricRead], tags=["Métricas"])
def list_ad_metrics(
    client: SupabaseClient,
    date_from: date,
    date_to: date,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ad_id: UUID | None = None,
) -> dict[str, object]:
    return list_metrics(client, "ads", date_from, date_to, page, page_size, ad_id)


def list_metrics(
    client: SupabaseClient,
    level: str,
    date_from: date,
    date_to: date,
    page: int,
    page_size: int,
    entity_id: UUID | None,
) -> dict[str, object]:
    if date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="date_from não pode ser posterior a date_to.",
        )
    try:
        return MetricService(client).list_metrics(
            level, date_from, date_to, page, page_size, entity_id
        )
    except Exception as exc:
        raise database_unavailable(exc) from exc


@router.get("/dashboard", response_model=DashboardRead, tags=["Dashboard"])
def get_dashboard(
    client: SupabaseClient,
    days: DashboardDays = DashboardDays.DAYS_30,
    date_from: date | None = None,
    date_to: date | None = None,
    client_id: UUID | None = None,
    meta_account_id: UUID | None = None,
    campaign_id: UUID | None = None,
) -> dict[str, object]:
    try:
        return DashboardService(client).get_dashboard(
            days=int(days),
            date_from=date_from,
            date_to=date_to,
            client_id=client_id,
            meta_account_id=meta_account_id,
            campaign_id=campaign_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    except Exception as exc:
        raise database_unavailable(exc) from exc


@router.post(
    "/recommendations/decision",
    response_model=RecommendationDecisionRead,
    tags=["Recomendações"],
    status_code=status.HTTP_201_CREATED,
)
def decide_recommendation(
    payload: RecommendationDecision, client: SupabaseClient
) -> dict[str, object]:
    try:
        return RecommendationService(client).decide(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    except Exception as exc:
        raise database_unavailable(exc) from exc


@router.get(
    "/improvements", response_model=Page[ImprovementRead], tags=["Recomendações"]
)
def list_improvements(
    client: SupabaseClient,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict[str, object]:
    try:
        return RecommendationService(client).list_improvements(page, page_size)
    except Exception as exc:
        raise database_unavailable(exc) from exc
