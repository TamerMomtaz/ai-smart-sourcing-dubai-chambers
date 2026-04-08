import os
import sys
from dotenv import load_dotenv

load_dotenv()

def _get_env(key, required=True, default=None):
    value = os.environ.get(key)
    if value is not None:
        value = value.strip()
    if required and not value:
        if default is not None:
            return default.strip() if isinstance(default, str) else default
        print(f"FATAL: Required environment variable '{key}' is missing or empty.", file=sys.stderr)
        sys.exit(1)
    if value is None and default is not None:
        return default.strip() if isinstance(default, str) else default
    return value

SUPABASE_URL = _get_env("SUPABASE_URL")
# Railway may set SUPABASE_KEY or SUPABASE_ANON_KEY — accept either.
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "").strip() or os.environ.get("SUPABASE_KEY", "").strip()
if not SUPABASE_ANON_KEY:
    print("FATAL: Required environment variable 'SUPABASE_ANON_KEY' (or 'SUPABASE_KEY') is missing or empty.", file=sys.stderr)
    sys.exit(1)
SUPABASE_SERVICE_ROLE_KEY = _get_env("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_JWT_SECRET = _get_env("SUPABASE_JWT_SECRET", required=False, default=None)

CORS_ORIGINS_RAW = _get_env("CORS_ORIGINS", required=False, default="http://localhost:3000")
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_RAW.split(",") if origin.strip()]

PORT = 8000

ANTHROPIC_API_KEY = _get_env("ANTHROPIC_API_KEY", required=False, default=None)
OPENAI_API_KEY = _get_env("OPENAI_API_KEY", required=False, default=None)
GOOGLE_API_KEY = _get_env("GOOGLE_API_KEY", required=False, default=None)

DOCUMENT_STORAGE_BUCKET = _get_env("DOCUMENT_STORAGE_BUCKET", required=False, default="chamber-proposal-documents")
COMPLIANCE_REPORT_BUCKET = _get_env("COMPLIANCE_REPORT_BUCKET", required=False, default="chamber-compliance-reports")

MAX_FILE_SIZE_MB = int(_get_env("MAX_FILE_SIZE_MB", required=False, default="50"))
ALLOWED_FILE_TYPES = _get_env("ALLOWED_FILE_TYPES", required=False, default="pdf,docx,pptx,xlsx").split(",")
ALLOWED_FILE_TYPES = [ft.strip() for ft in ALLOWED_FILE_TYPES if ft.strip()]

JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(_get_env("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", required=False, default="60"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(_get_env("JWT_REFRESH_TOKEN_EXPIRE_DAYS", required=False, default="7"))

DUPLICATE_SIMILARITY_THRESHOLD = float(_get_env("DUPLICATE_SIMILARITY_THRESHOLD", required=False, default="0.92"))

DESC_COMPLIANCE_SCORE_THRESHOLD = float(_get_env("DESC_COMPLIANCE_SCORE_THRESHOLD", required=False, default="7.0"))

BATCH_EVALUATION_MAX_SIZE = int(_get_env("BATCH_EVALUATION_MAX_SIZE", required=False, default="50"))

AI_MODEL_TIMEOUT_SECONDS = int(_get_env("AI_MODEL_TIMEOUT_SECONDS", required=False, default="120"))
AI_MAX_RETRIES = int(_get_env("AI_MAX_RETRIES", required=False, default="3"))

SIGMA_INTELLIGENCE_TRACKING_ENABLED = _get_env("SIGMA_INTELLIGENCE_TRACKING_ENABLED", required=False, default="true").lower() == "true"

DATA_RETENTION_YEARS = int(_get_env("DATA_RETENTION_YEARS", required=False, default="7"))

LOG_LEVEL = _get_env("LOG_LEVEL", required=False, default="INFO").upper()

ENVIRONMENT = _get_env("ENVIRONMENT", required=False, default="production").lower()

RATE_LIMIT_PER_MINUTE_VENDOR = int(_get_env("RATE_LIMIT_PER_MINUTE_VENDOR", required=False, default="20"))
RATE_LIMIT_PER_MINUTE_ANALYST = int(_get_env("RATE_LIMIT_PER_MINUTE_ANALYST", required=False, default="100"))
RATE_LIMIT_PER_MINUTE_EXECUTIVE = int(_get_env("RATE_LIMIT_PER_MINUTE_EXECUTIVE", required=False, default="50"))

EMBEDDING_MODEL = _get_env("EMBEDDING_MODEL", required=False, default="text-embedding-3-large")
EMBEDDING_DIMENSIONS = int(_get_env("EMBEDDING_DIMENSIONS", required=False, default="1536"))

DEFAULT_LANGUAGE = _get_env("DEFAULT_LANGUAGE", required=False, default="en")

REQUIRE_DESC_CERTIFICATION = _get_env("REQUIRE_DESC_CERTIFICATION", required=False, default="false").lower() == "true"

ENABLE_HALLUCINATION_DETECTION = _get_env("ENABLE_HALLUCINATION_DETECTION", required=False, default="true").lower() == "true"
ENABLE_PROMPT_INJECTION_DETECTION = _get_env("ENABLE_PROMPT_INJECTION_DETECTION", required=False, default="true").lower() == "true"

SENTRY_DSN = _get_env("SENTRY_DSN", required=False, default=None)

NOTIFICATION_EMAIL_FROM = _get_env("NOTIFICATION_EMAIL_FROM", required=False, default="noreply@dubaichambers.ae")
SMTP_HOST = _get_env("SMTP_HOST", required=False, default=None)
SMTP_PORT = int(_get_env("SMTP_PORT", required=False, default="587"))
SMTP_USER = _get_env("SMTP_USER", required=False, default=None)
SMTP_PASSWORD = _get_env("SMTP_PASSWORD", required=False, default=None)
SMTP_USE_TLS = _get_env("SMTP_USE_TLS", required=False, default="true").lower() == "true"

WEBHOOK_SECRET = _get_env("WEBHOOK_SECRET", required=False, default=None)

INTAKE_API_KEY = _get_env("INTAKE_API_KEY", required=False, default=None)

REDIS_URL = _get_env("REDIS_URL", required=False, default=None)

# UAE PASS SSO (OAuth 2.0 / OIDC) — credentials obtained via UAE TDRA registration
UAE_PASS_CLIENT_ID = _get_env("UAE_PASS_CLIENT_ID", required=False, default=None)
UAE_PASS_CLIENT_SECRET = _get_env("UAE_PASS_CLIENT_SECRET", required=False, default=None)
UAE_PASS_AUTH_URL = _get_env("UAE_PASS_AUTH_URL", required=False, default="https://stg-id.uaepass.ae/idshub/authorize")
UAE_PASS_TOKEN_URL = _get_env("UAE_PASS_TOKEN_URL", required=False, default="https://stg-id.uaepass.ae/idshub/token")
UAE_PASS_USERINFO_URL = _get_env("UAE_PASS_USERINFO_URL", required=False, default="https://stg-id.uaepass.ae/idshub/userinfo")
UAE_PASS_REDIRECT_URI = _get_env("UAE_PASS_REDIRECT_URI", required=False, default="http://localhost:8000/api/v1/auth/uaepass/callback")

APP_VERSION = _get_env("APP_VERSION", required=False, default="1.0.0")

def validate_env_vars():
    """Validate that all required environment variables are set."""
    required = ["SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY"]
    missing = [var for var in required if not os.environ.get(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

if not ANTHROPIC_API_KEY and not OPENAI_API_KEY and not GOOGLE_API_KEY:
    print("WARNING: No AI API keys configured. AI agents will fail at runtime.", file=sys.stderr)
