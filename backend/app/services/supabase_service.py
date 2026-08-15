from uuid import uuid4

from supabase import Client

from app.config.settings import get_settings


class SupabaseService:
    """Operações mínimas de infraestrutura usadas na Fase 2."""

    def __init__(self, client: Client) -> None:
        self.client = client
        self.settings = get_settings()
        self.health_table = self.settings.supabase_health_table

    def read_health(self) -> dict[str, object]:
        """Executa uma leitura mínima para validar Data API + tabela de health."""

        response = (
            self.client.table(self.health_table)
            .select("id,service,test_marker,created_at")
            .limit(1)
            .execute()
        )
        rows = response.data or []

        return {
            "status": "ok",
            "service": "supabase",
            "table": self.health_table,
            "rows_sampled": len(rows),
        }

    def write_probe(self) -> dict[str, object]:
        """Insere e remove um marcador temporário para validar escrita.

        Este método é destinado ao smoke test manual da Fase 2. O registro é
        removido no final para não poluir a tabela de infraestrutura.
        """

        marker = f"smoke-{uuid4()}"
        payload = {
            "service": "descompliads-api",
            "test_marker": marker,
        }

        inserted = (
            self.client.table(self.health_table)
            .insert(payload)
            .select("id,service,test_marker")
            .execute()
        )

        try:
            rows = inserted.data or []
            return {
                "status": "ok",
                "service": "supabase",
                "write": True,
                "inserted_rows": len(rows),
                "marker": marker,
            }
        finally:
            (
                self.client.table(self.health_table)
                .delete()
                .eq("test_marker", marker)
                .execute()
            )
