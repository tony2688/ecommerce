from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_PORT: int = 8000
    # v0.7 unified env label (dev|test|prod)
    ENV: str = "dev"

    DB_HOST: str = "db"
    DB_PORT: int = 3306
    DB_USER: str = "ecom_user"
    DB_PASSWORD: str = "ecom_pass"
    DB_NAME: str = "ecommerce"

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Celery
    @property
    def CELERY_BROKER_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Base URL (public) para construir callbacks y webhooks
    BASE_URL: str = "http://localhost:8080"

    # Mercado Pago (dual-mode sandbox|prod)
    MP_ENV: str = "sandbox"  # sandbox|prod
    MP_ACCESS_TOKEN_SANDBOX: str = ""
    MP_PUBLIC_KEY_SANDBOX: str = ""
    MP_ACCESS_TOKEN_PROD: str = ""
    MP_PUBLIC_KEY_PROD: str = ""
    MP_WEBHOOK_SECRET: str = "dev-secret"  # rotación independiente por ambiente
    # Si no se define explícitamente, se construye con BASE_URL
    MP_WEBHOOK_URL: Optional[str] = None
    # Back URLs por ambiente
    MP_BACK_URL_SUCCESS: Optional[str] = None
    MP_BACK_URL_FAILURE: Optional[str] = None
    MP_BACK_URL_PENDING: Optional[str] = None
    MP_WEBHOOK_TOLERANCE_SECONDS: int = 300
    MP_WEBHOOK_TEST_ENABLED: bool = True  # en prod debe ser False
    # Credenciales MP: endpoint de chequeo flaggeable
    MP_CREDENTIALS_CHECK_ENABLED: bool = True

    SECRET_KEY: str = "change_this_super_secret_key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    CORS_ALLOW_ORIGINS: List[str] = ["http://localhost", "http://localhost:8000"]

    # Alertas y thresholds (v0.7)
    ALERTS_ENABLED: bool = False
    ADMIN_EMAIL_ALERTS: Optional[str] = None
    SLACK_WEBHOOK_URL: Optional[str] = None
    LOW_STOCK_THRESHOLD: int = 5
    PENDING_PAYMENT_MAX_HOURS: int = 12
    STALE_RESERVATION_MAX_MINUTES: int = 30

    # Snapshots (v0.7)
    SNAPSHOTS_ENABLED: bool = False

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # Helpers Mercado Pago
    @property
    def MP_ACCESS_TOKEN(self) -> str:
        return (
            self.MP_ACCESS_TOKEN_PROD
            if self.MP_ENV == "prod"
            else self.MP_ACCESS_TOKEN_SANDBOX
        )

    @property
    def MP_PUBLIC_KEY(self) -> str:
        return (
            self.MP_PUBLIC_KEY_PROD
            if self.MP_ENV == "prod"
            else self.MP_PUBLIC_KEY_SANDBOX
        )

    @property
    def EFFECTIVE_WEBHOOK_URL(self) -> str:
        base = self.MP_WEBHOOK_URL or f"{self.BASE_URL}/webhooks/mp"
        return base

    @property
    def BACK_URL_SUCCESS(self) -> str:
        return self.MP_BACK_URL_SUCCESS or f"{self.BASE_URL}/pagos/ok"

    @property
    def BACK_URL_FAILURE(self) -> str:
        return self.MP_BACK_URL_FAILURE or f"{self.BASE_URL}/pagos/error"

    @property
    def BACK_URL_PENDING(self) -> str:
        return self.MP_BACK_URL_PENDING or f"{self.BASE_URL}/pagos/pendiente"

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()
