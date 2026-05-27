from app.core.config import Settings


def test_cors_origins_accept_single_url():
    settings = Settings(cors_origins="https://app.onrender.com")

    assert settings.cors_origin_list == ["https://app.onrender.com"]


def test_cors_origins_accept_comma_separated_values():
    settings = Settings(cors_origins="https://app.onrender.com,http://localhost:5173")

    assert settings.cors_origin_list == ["https://app.onrender.com", "http://localhost:5173"]


def test_disabled_stores_accept_comma_separated_values():
    settings = Settings(disabled_stores="nuuvem, amazon")

    assert settings.disabled_store_list == ["nuuvem", "amazon"]
