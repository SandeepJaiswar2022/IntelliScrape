"""
Central configuration for the whole application.

Everything the app needs from the environment is declared here, in one
place, with types and sane defaults where a default is safe. This means:
  - no `os.environ.get(...)` scattered through the codebase
  - misconfiguration fails fast at startup (Pydantic validates types)
  - every other module imports a single `settings` object instead of
    reading the environment directly
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App metadata ---
    APP_NAME: str = "IntelliScrape Auth Service"
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = True

    # --- Database ---
    DATABASE_URL: str  # e.g. postgresql+asyncpg://user:pass@host:5432/db

    # --- JWT / access tokens ---
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    # --- Refresh tokens (opaque, stored hashed in DB — see security.py) ---
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # --- CORS ---
    # Comma-separated string in the environment, parsed into a list below.
    CORS_ORIGINS: str = "http://localhost:5173"

    # --- Cookie security ---
    # COOKIE_SECURE must be True in any environment served over HTTPS.
    # It is False only for local HTTP development.
    COOKIE_SECURE: bool = False
    COOKIE_DOMAIN: str | None = None

    # --- Brute-force / account lockout protection ---
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 15

    # --- Redis (Celery broker + result backend) ---
    # Inside docker-compose the host is the service name "redis";
    # outside Docker (e.g. running the worker directly) use "localhost".
    REDIS_URL: str = "redis://redis:6379/0"

    # --- Job scraping: Greenhouse ---
    # Comma-separated list of Greenhouse "board tokens" -- the slug in a
    # company's public careers URL, e.g.
    # https://job-boards.greenhouse.io/stripe -> token is "stripe".
    # Starting with 5 real, verified tokens; add more here as the
    # project grows -- no code changes needed, just this list.
    GREENHOUSE_COMPANY_TOKENS: str = "stripe,gitlab,figma,robinhood,asana"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    @property
    def cors_origins_list(self) -> list[str]:
        """Split the comma-separated CORS_ORIGINS string into a clean list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def greenhouse_company_tokens_list(self) -> list[str]:
        """Split the comma-separated GREENHOUSE_COMPANY_TOKENS string into a clean list."""
        return [t.strip() for t in self.GREENHOUSE_COMPANY_TOKENS.split(",") if t.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


# Single shared settings instance — import this everywhere else.
settings = Settings()
