from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


SyncStatus = Literal["PENDING", "RUNNING", "SUCCESS", "PARTIAL", "FAILED"]


class SyncRequestCreate(BaseModel):
    client_id: UUID
    lookback_days: int = Field(default=3, ge=1, le=360)

class SyncRecoveryCreate(BaseModel):
    run_id: UUID
    client_id: UUID | None = None


class SyncRequestRead(BaseModel):
    id: UUID
    client_id: UUID
    lookback_days: int
    status: SyncStatus
    recovery_of: UUID | None = None
    sync_run_id: UUID | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_summary: str | None = None


class SyncRunRead(BaseModel):
    id: UUID
    status: Literal["RUNNING", "SUCCESS", "PARTIAL", "FAILED"]
    trigger_source: Literal["SCHEDULED", "MANUAL", "RECOVERY"] = "SCHEDULED"
    client_id: UUID | None = None
    recovery_of: UUID | None = None
    lookback_days: int
    started_at: datetime
    finished_at: datetime | None = None
    duration_ms: int | None = None
    accounts_total: int
    accounts_success: int
    accounts_partial: int
    accounts_failed: int
    current_stage: str | None = None
    current_account_name: str | None = None
    progress_current: int = 0
    progress_total: int = 0
    result: dict[str, object] = Field(default_factory=dict)
    error_summary: str | None = None
