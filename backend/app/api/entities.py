from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import SupabaseClient
from app.models.entities import (
    CampaignRead,
    ClientRead,
    DashboardRead,
    EntityStatus,
    MetaAccountRead,
    Page,
)
from app.services.entity_services import (
    CampaignService,
    ClientService,
    DashboardService,
    EntityNotFoundError,
    MetaAccountService,
)

router = APIRouter()


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


@router.get("/dashboard", response_model=DashboardRead, tags=["Dashboard"])
def get_dashboard(client: SupabaseClient) -> dict[str, object]:
    try:
        return DashboardService(client).get_dashboard()
    except Exception as exc:
        raise database_unavailable(exc) from exc
