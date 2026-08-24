from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.models.settings import ClientCreate, ClientUpdate
from app.services.client_management_service import ClientManagementService
from app.main import app


ADMIN_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
CLIENT_ID = "11111111-1111-1111-1111-111111111111"
NOW = datetime(2026, 8, 23, tzinfo=UTC).isoformat()


class FakeQuery:
    def __init__(self, client: "FakeClient", table: str) -> None:
        self.client = client
        self.table = table
        self.filters: list[tuple[str, object]] = []
        self.operation = "select"
        self.values: dict[str, object] = {}

    def select(self, _columns: str):
        return self

    def eq(self, column: str, value: object):
        self.filters.append((column, value))
        return self

    def limit(self, _value: int):
        return self

    def order(self, _column: str):
        return self

    def insert(self, values: dict[str, object]):
        self.operation = "insert"
        self.values = values
        return self

    def update(self, values: dict[str, object]):
        self.operation = "update"
        self.values = values
        return self

    def delete(self):
        self.operation = "delete"
        return self

    def execute(self):
        rows = self.client.rows.setdefault(self.table, [])
        matching = [
            row for row in rows
            if all(str(row.get(column)) == str(value) for column, value in self.filters)
        ]
        if self.operation == "insert":
            row = {
                "id": CLIENT_ID,
                "status": "ACTIVE",
                "created_at": NOW,
                "updated_at": NOW,
                **self.values,
            }
            rows.append(row)
            return SimpleNamespace(data=[row])
        if self.operation == "update":
            for row in matching:
                row.update(self.values)
            return SimpleNamespace(data=matching)
        if self.operation == "delete":
            self.client.rows[self.table] = [row for row in rows if row not in matching]
            return SimpleNamespace(data=matching)
        return SimpleNamespace(data=matching)


class FakeClient:
    def __init__(self, rows: dict[str, list[dict[str, object]]] | None = None) -> None:
        self.rows = rows or {}

    def table(self, name: str) -> FakeQuery:
        return FakeQuery(self, name)


def payload() -> ClientCreate:
    return ClientCreate(
        name="Odisséia Imóveis",
        legal_name="Odisséia Negócios Imobiliários Ltda",
        segment="Imobiliário",
        niche="Imóveis Minha Casa Minha Vida",
        business_model="B2C",
        country_code="BR",
        currency="BRL",
    )


def test_client_profile_validates_business_fields() -> None:
    assert payload().segment == "Imobiliário"
    with pytest.raises(ValidationError):
        ClientCreate(name="A", segment="", niche="", monthly_media_budget=-1)


def test_client_management_routes_are_documented() -> None:
    paths = app.openapi()["paths"]
    assert "/api/v1/settings/clients" in paths
    assert "/api/v1/settings/clients/{client_id}" in paths


def test_slugify_removes_accents_and_symbols() -> None:
    assert ClientManagementService.slugify("Odisséia & Cia. Imóveis") == "odisseia-cia-imoveis"


def test_only_system_admin_can_create_client() -> None:
    service = ClientManagementService(FakeClient(), FakeClient())  # type: ignore[arg-type]
    with pytest.raises(HTTPException) as exc:
        service.create(payload())
    assert exc.value.status_code == 403


def test_create_client_assigns_creator_as_owner() -> None:
    user = FakeClient({"system_admins": [{"user_id": ADMIN_ID}]})
    database = FakeClient()
    result = ClientManagementService(user, database).create(payload())  # type: ignore[arg-type]
    assert result["slug"] == "odisseia-imoveis"
    assert result["can_manage"] is True
    assert database.rows["user_client_access"][0] == {
        "id": CLIENT_ID,
        "status": "ACTIVE",
        "created_at": NOW,
        "updated_at": NOW,
        "user_id": ADMIN_ID,
        "client_id": CLIENT_ID,
        "role": "OWNER",
        "active": True,
    }


def test_client_admin_can_manage_only_authorized_client() -> None:
    existing = {
        "id": CLIENT_ID,
        "name": "Cliente atual",
        "slug": "cliente-atual",
        "status": "ACTIVE",
        "segment": "Imobiliário",
        "niche": "Lançamentos",
        "created_at": NOW,
        "updated_at": NOW,
    }
    user = FakeClient({
        "system_admins": [],
        "user_client_access": [{"client_id": CLIENT_ID, "role": "ADMIN", "active": True}],
        "clients": [existing.copy()],
    })
    database = FakeClient({"clients": [existing.copy()]})
    service = ClientManagementService(user, database)  # type: ignore[arg-type]
    listed = service.list_clients()
    assert listed[0]["can_manage"] is True

    updated = service.update(UUID(CLIENT_ID), ClientUpdate(name="Novo nome"))
    assert updated["name"] == "Novo nome"
