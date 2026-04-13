"""Unit tests for application configuration and settings validators."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings

# Minimum required fields when instantiating Settings directly.
# _env_file=None bypasses the project .env file so tests are hermetic.
_BASE = {
    "_env_file": None,
    "MONGO_USER": "testuser",
    "MONGO_PASSWORD": "testpass",
    "TMDB_API_KEY": "testkey",
}


# ---------------------------------------------------------------------------
# parse_cors_origins validator
# ---------------------------------------------------------------------------


class TestParseCorsOrigins:
    def test_single_origin_string(self):
        s = Settings(**_BASE, CORS_ORIGINS="http://localhost:3000")
        assert s.CORS_ORIGINS == ["http://localhost:3000"]

    def test_comma_separated_string(self):
        s = Settings(
            **_BASE,
            CORS_ORIGINS="http://localhost:3000,http://localhost:8000",
        )
        assert s.CORS_ORIGINS == ["http://localhost:3000", "http://localhost:8000"]

    def test_whitespace_is_stripped(self):
        s = Settings(
            **_BASE,
            CORS_ORIGINS="http://localhost:3000 , http://localhost:8000",
        )
        assert s.CORS_ORIGINS == ["http://localhost:3000", "http://localhost:8000"]

    def test_list_input_is_passed_through(self):
        origins = ["http://localhost:3000", "http://localhost:8080"]
        s = Settings(**_BASE, CORS_ORIGINS=origins)
        assert s.CORS_ORIGINS == origins

    def test_single_item_list(self):
        s = Settings(**_BASE, CORS_ORIGINS=["http://example.com"])
        assert s.CORS_ORIGINS == ["http://example.com"]


# ---------------------------------------------------------------------------
# validate_secret_key validator
# ---------------------------------------------------------------------------


class TestValidateSecretKey:
    def test_short_key_accepted_in_development(self):
        """A short key is acceptable in the default (development) environment."""
        s = Settings(**_BASE, ENVIRONMENT="development", SECRET_KEY="short")
        assert s.SECRET_KEY == "short"

    def test_default_key_accepted_in_development(self):
        s = Settings(
            **_BASE, ENVIRONMENT="development", SECRET_KEY="change_me_in_production"
        )
        assert s.SECRET_KEY == "change_me_in_production"

    def test_production_rejects_default_key(self):
        with pytest.raises(ValidationError, match="must be changed from default"):
            Settings(
                **_BASE,
                ENVIRONMENT="production",
                SECRET_KEY="change_me_in_production",
            )

    def test_production_rejects_short_key(self):
        with pytest.raises(ValidationError, match="at least 32 characters"):
            Settings(
                **_BASE,
                ENVIRONMENT="production",
                SECRET_KEY="tooshort",
            )

    def test_production_accepts_long_custom_key(self):
        long_key = "a_very_secure_production_secret_key_that_is_long_enough"
        s = Settings(**_BASE, ENVIRONMENT="production", SECRET_KEY=long_key)
        assert s.SECRET_KEY == long_key


# ---------------------------------------------------------------------------
# mongodb_url property
# ---------------------------------------------------------------------------


class TestMongodbUrl:
    def test_url_assembled_from_components(self):
        s = Settings(
            MONGO_USER="admin",
            MONGO_PASSWORD="s3cret",
            MONGO_HOST="db.example.com",
            MONGO_PORT=27017,
            MONGO_DB="mydb",
            TMDB_API_KEY="key",
        )
        expected = "mongodb://admin:s3cret@db.example.com:27017/mydb"
        assert s.mongodb_url == expected

    def test_url_uses_custom_port(self):
        s = Settings(
            **_BASE, MONGO_HOST="localhost", MONGO_PORT=27018, MONGO_DB="testdb"
        )
        assert "27018" in s.mongodb_url

    def test_url_uses_custom_db_name(self):
        s = Settings(**_BASE, MONGO_DB="custom_db")
        assert "custom_db" in s.mongodb_url


# ---------------------------------------------------------------------------
# Default field values
# ---------------------------------------------------------------------------


class TestDefaultValues:
    def test_default_environment_is_development(self, monkeypatch):
        monkeypatch.delenv("ENVIRONMENT", raising=False)
        s = Settings(**_BASE)
        assert s.ENVIRONMENT == "development"

    def test_default_algorithm_is_hs256(self):
        s = Settings(**_BASE)
        assert s.ALGORITHM == "HS256"

    def test_default_host_is_mongodb(self, monkeypatch):
        monkeypatch.delenv("MONGO_HOST", raising=False)
        s = Settings(**_BASE)
        assert s.MONGO_HOST == "mongodb"

    def test_default_port_is_8000(self):
        s = Settings(**_BASE)
        assert s.PORT == 8000
