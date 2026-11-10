from services.api.config import Settings

SECRETS = {
    "DATABASE_URL": "postgresql://u:PWD-LEAK@h/db",
    "QURAN_API_CLIENT_SECRET": "QCS-LEAK",
    "LLM_API_KEY": "LLM-LEAK",
    "OPENAI_API_KEY": "OAI-LEAK",
    "TTS_API_KEY": "TTS-LEAK",
    "GEMINI_API_KEY": "GEM-LEAK",
    "EMBEDDING_API_KEY": "EMB-LEAK",
    "STRAPI_API_TOKEN": "STR-LEAK",
    "SECRET_KEY": "SK-LEAK",
    "JWT_SECRET": "JWT-LEAK",
}


def test_settings_repr_and_str_never_expose_secrets(monkeypatch):
    for name, value in SECRETS.items():
        monkeypatch.setenv(name, value)
    settings = Settings()
    rendered = repr(settings) + str(settings)
    for value in SECRETS.values():
        assert value not in rendered


def test_secrets_still_usable_by_server_code(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h/db")
    monkeypatch.setenv("GEMINI_API_KEY", "GEM-LEAK")
    settings = Settings()
    assert settings.gemini_api_key == "GEM-LEAK"
    assert settings.database_url == "postgresql://u:p@h/db"
