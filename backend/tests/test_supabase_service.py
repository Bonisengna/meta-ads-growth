from types import SimpleNamespace

from app.services.supabase_service import SupabaseService


class FakeQuery:
    def __init__(self, client, operation: str) -> None:
        self.client = client
        self.operation = operation
        self.payload = None
        self.marker = None

    def select(self, _columns: str):
        return self

    def limit(self, _limit: int):
        return self

    def insert(self, payload: dict):
        self.operation = "insert"
        self.payload = payload
        return self

    def delete(self):
        self.operation = "delete"
        return self

    def eq(self, _column: str, marker: str):
        self.marker = marker
        return self

    def execute(self):
        self.client.operations.append(self.operation)

        if self.operation == "insert":
            return SimpleNamespace(
                data=[
                    {
                        "id": "fake-id",
                        "service": self.payload["service"],
                        "test_marker": self.payload["test_marker"],
                    }
                ]
            )

        if self.operation == "delete":
            return SimpleNamespace(data=[])

        return SimpleNamespace(
            data=[
                {
                    "id": "fake-id",
                    "service": "descompliads-api",
                    "test_marker": None,
                    "created_at": "2026-08-15T00:00:00Z",
                }
            ]
        )


class FakeClient:
    def __init__(self) -> None:
        self.operations: list[str] = []
        self.tables: list[str] = []

    def table(self, table_name: str) -> FakeQuery:
        self.tables.append(table_name)
        return FakeQuery(self, "select")


def test_read_health_reads_configured_health_table() -> None:
    fake_client = FakeClient()
    service = SupabaseService(fake_client)  # type: ignore[arg-type]

    result = service.read_health()

    assert result["status"] == "ok"
    assert result["service"] == "supabase"
    assert result["table"] == "app_health"
    assert result["rows_sampled"] == 1
    assert fake_client.operations == ["select"]


def test_write_probe_inserts_and_cleans_up_test_record() -> None:
    fake_client = FakeClient()
    service = SupabaseService(fake_client)  # type: ignore[arg-type]

    result = service.write_probe()

    assert result["status"] == "ok"
    assert result["write"] is True
    assert result["inserted_rows"] == 1
    assert fake_client.operations == ["insert", "delete"]
    assert fake_client.tables == ["app_health", "app_health"]
