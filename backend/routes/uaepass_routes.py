from fastapi import APIRouter, Request, status
from fastapi.responses import RedirectResponse, JSONResponse
import logging

from config import UAE_PASS_CLIENT_ID, UAE_PASS_REDIRECT_URI, UAE_PASS_AUTH_URL

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/uaepass", tags=["UAE PASS SSO"])


@router.get(
    "/login",
    summary="Redirect to UAE PASS authorization",
    response_description="Redirects to UAE PASS OIDC login or placeholder page",
)
async def uaepass_login(request: Request):
    """
    Initiate UAE PASS SSO login via OAuth 2.0 / OpenID Connect.

    In production (when UAE PASS API credentials are configured), this
    redirects to the UAE PASS authorization endpoint.

    Until credentials are obtained through UAE government registration,
    this returns a descriptive message explaining the pending integration.
    """
    client_ip = request.client.host if request.client else "unknown"
    logger.info(
        "UAE PASS login initiated",
        extra={"ip": client_ip, "endpoint": "/api/v1/auth/uaepass/login"},
    )

    if UAE_PASS_CLIENT_ID and UAE_PASS_AUTH_URL:
        # Production: redirect to UAE PASS authorization endpoint
        params = (
            f"?response_type=code"
            f"&client_id={UAE_PASS_CLIENT_ID}"
            f"&redirect_uri={UAE_PASS_REDIRECT_URI}"
            f"&scope=openid profile email"
            f"&acr_values=urn:safelayer:tws:policies:authentication:level:low"
        )
        return RedirectResponse(
            url=f"{UAE_PASS_AUTH_URL}{params}",
            status_code=status.HTTP_302_FOUND,
        )

    # Stub: credentials not yet configured
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "pending_configuration",
            "message": (
                "UAE PASS SSO integration is architecturally ready. "
                "Full activation requires API credentials obtained through "
                "registration with the UAE Digital Government (TDRA). "
                "Please contact your administrator to complete the registration process."
            ),
            "integration": {
                "protocol": "OAuth 2.0 / OpenID Connect (OIDC)",
                "provider": "UAE PASS",
                "status": "awaiting_credentials",
            },
        },
    )


@router.get(
    "/callback",
    summary="Handle UAE PASS OAuth callback",
    response_description="Processes the OIDC callback from UAE PASS",
)
async def uaepass_callback(
    request: Request,
    code: str = None,
    state: str = None,
    error: str = None,
):
    """
    Handle the OAuth 2.0 callback from UAE PASS after user authorization.

    In production, this endpoint:
    1. Validates the authorization code
    2. Exchanges it for an access token via UAE PASS token endpoint
    3. Fetches user identity from UAE PASS userinfo endpoint
    4. Creates or links a chamber_users record
    5. Issues a Supabase session for the authenticated user

    Currently returns a stub response logging the attempt.
    """
    client_ip = request.client.host if request.client else "unknown"
    logger.info(
        "UAE PASS callback received",
        extra={
            "ip": client_ip,
            "has_code": code is not None,
            "has_error": error is not None,
            "endpoint": "/api/v1/auth/uaepass/callback",
        },
    )

    if error:
        logger.warning(
            "UAE PASS callback returned error: %s",
            error,
            extra={"ip": client_ip},
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "uaepass_auth_error",
                "detail": f"UAE PASS returned an error: {error}",
            },
        )

    # Stub: log the attempt and return descriptive response
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "callback_received",
            "message": (
                "UAE PASS callback endpoint is operational. "
                "Full token exchange and user provisioning will be enabled "
                "once UAE PASS API credentials are configured."
            ),
            "next_steps": [
                "Register with UAE TDRA to obtain client_id and client_secret",
                "Configure UAE_PASS_CLIENT_ID, UAE_PASS_CLIENT_SECRET environment variables",
                "Endpoint will then exchange authorization code for user identity",
            ],
        },
    )
