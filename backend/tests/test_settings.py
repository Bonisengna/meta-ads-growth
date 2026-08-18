from app.models.settings import MetaIntegrationWrite, SystemCredentialsWrite
from app.services.settings_service import SettingsService


def test_secret_models_never_serialize_plaintext() -> None:
    meta = MetaIntegrationWrite(
        client_id="11111111-1111-1111-1111-111111111111",
        connection_name="Conta principal",
        ad_account_id="act_123456789",
        access_token="meta-secret-value",
    )
    system = SystemCredentialsWrite(openai_api_key="sk-proj-secret-value")
    assert "meta-secret-value" not in meta.model_dump_json()
    assert "sk-proj-secret-value" not in system.model_dump_json()


def test_safe_status_excludes_vault_secret_fields() -> None:
    status = SettingsService._safe_status({
        "provider": "OPENAI", "secret_id": "hidden-id", "decrypted_secret": "hidden",
        "connection_name": "OpenAI", "status": "CONFIGURED", "config": {},
    })
    assert status["configured"] is True
    assert "secret_id" not in status
    assert "decrypted_secret" not in status
