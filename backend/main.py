from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import sys

from config import CORS_ORIGINS, APP_VERSION, ENVIRONMENT, validate_env_vars
from database import supabase

# Import all route modules
from routes import (
    ai_interaction_routes,
    analyst_routes,
    business_group_routes,
    business_groups_public_routes,
    chamber_ai_interactions_routes,
    chamber_business_council_routes,
    chamber_business_groups_routes,
    chamber_comments_routes,
    chamber_compliance_audits_routes,
    compliance_engine_routes,
    dashboard_engagements_routes,
    dashboard_sectors_routes,
    dashboard_stats_routes,
    chamber_desc_certified_providers_routes,
    chamber_documents_routes,
    chamber_evaluations,
    chamber_notification_preferences_routes,
    chamber_proposal_routes,
    chamber_trend_analyses_routes,
    chamber_users_routes,
    chamber_vendor_profiles_routes,
    chamber_vendors_routes,
    comment_routes,
    compliance_audits_routes,
    desc_certified_providers_routes,
    document_routes,
    download_routes,
    duplicate_check_routes,
    evaluate_routes,
    evaluation_config_routes,
    evaluation_routes,
    executive_routes,
    extracted_data_routes,
    health_routes,
    login_routes,
    logout_routes,
    me_routes,
    proposal_routes,
    proposal_submission_routes,
    refresh_routes,
    report_routes,
    sector_routes,
    status_routes,
    submit_routes,
    user_routes,
    vendor_routes,
    verify_routes,
    proposal_document_routes,
    proposal_ingest_routes,
    hallucination_routes,
    dashboard_impact_routes,
    board_brief_routes,
    vendor_intelligence_routes,
    vscore_routes,
    incident_routes,
    public_stats_routes
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="AI Smart Sourcing — Dubai Chambers",
    description="Production-ready backend for AI-powered vendor proposal evaluation system with DESC compliance, multi-language support, and ΣI (Sigma Intelligence) tracking",
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    response_model_exclude_unset=True,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler middleware
@app.middleware("http")
async def error_handler_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": str(exc) if ENVIRONMENT == "development" else "An unexpected error occurred",
                "code": "INTERNAL_ERROR"
            }
        )

# Request validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": exc.errors(),
            "code": "VALIDATION_ERROR"
        }
    )

# Startup event for environment validation
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("AI Smart Sourcing — Dubai Chambers Backend Starting")
    logger.info(f"Version: {APP_VERSION}")
    logger.info(f"Environment: {ENVIRONMENT}")
    logger.info("=" * 60)
    
    # Validate environment variables
    try:
        validate_env_vars()
        logger.info("✓ All required environment variables validated")
    except ValueError as e:
        logger.error(f"✗ Environment validation failed: {str(e)}")
        sys.exit(1)
    
    # Test database connection
    try:
        result = supabase.table("chamber_vendors").select("id").limit(1).execute()
        logger.info("✓ Database connection established")
    except Exception as e:
        logger.warning(f"⚠ Database connection check failed: {str(e)} — app will retry on first request")
    
    logger.info("✓ Application startup complete")
    logger.info("✓ CORS origins configured: ['*'] (all origins allowed)")
    logger.info("✓ Docs available at: /docs")
    logger.info("-" * 60)
    logger.info("Registered routes:")
    for route in app.routes:
        if hasattr(route, "methods"):
            methods = ", ".join(route.methods)
            logger.info(f"  {methods:20s} {route.path}")
    logger.info("=" * 60)

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down...")

# Health check endpoint
@app.get(
    "/health",
    tags=["System"],
    summary="System health check",
    response_description="Health status with database connectivity"
)
async def health_check():
    try:
        supabase.table("chamber_vendors").select("id").limit(1).execute()
        db_healthy = True
    except Exception as e:
        logger.error(f"Health check database error: {str(e)}")
        db_healthy = False
    
    health_status = {
        "status": "healthy" if db_healthy else "degraded",
        "version": APP_VERSION,
        "environment": ENVIRONMENT,
        "database": "connected" if db_healthy else "disconnected"
    }
    
    return JSONResponse(
        status_code=status.HTTP_200_OK if db_healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        content=health_status
    )

# Register all route modules
# NOTE: proposal_submission_routes and business_groups_public_routes registered first
# so their endpoints take priority over legacy routes with matching paths.
app.include_router(proposal_submission_routes.router, prefix="/api/v1", tags=["Proposal Submission & AI Evaluation"])
app.include_router(business_groups_public_routes.router, prefix="/api/v1", tags=["Business Groups Public"])
app.include_router(ai_interaction_routes.router, prefix="/api/v1", tags=["AI Interactions"])
app.include_router(analyst_routes.router, prefix="/api/v1", tags=["Analyst Dashboard"])
app.include_router(business_group_routes.router, prefix="/api/v1", tags=["Business Groups"])
app.include_router(chamber_ai_interactions_routes.router, prefix="/api/v1", tags=["Chamber AI Interactions"])
app.include_router(chamber_business_council_routes.router, prefix="/api/v1", tags=["Chamber Business Councils"])
app.include_router(chamber_business_groups_routes.router, prefix="/api/v1", tags=["Chamber Business Groups"])
app.include_router(chamber_comments_routes.router, prefix="/api/v1", tags=["Chamber Comments"])
app.include_router(chamber_compliance_audits_routes.router, prefix="/api/v1", tags=["Chamber Compliance Audits"])
app.include_router(chamber_desc_certified_providers_routes.router, prefix="/api/v1", tags=["Chamber DESC Certified Providers"])
app.include_router(chamber_documents_routes.router, prefix="/api/v1", tags=["Chamber Documents"])
app.include_router(chamber_evaluations.router, prefix="/api/v1", tags=["Chamber Evaluations"])
app.include_router(chamber_notification_preferences_routes.router, prefix="/api/v1", tags=["Chamber Notification Preferences"])
app.include_router(chamber_proposal_routes.router, prefix="/api/v1", tags=["Chamber Proposals"])
app.include_router(chamber_trend_analyses_routes.router, prefix="/api/v1", tags=["Chamber Trend Analyses"])
app.include_router(chamber_users_routes.router, prefix="/api/v1", tags=["Chamber Users"])
app.include_router(chamber_vendor_profiles_routes.router, prefix="/api/v1", tags=["Chamber Vendor Profiles"])
app.include_router(vendor_intelligence_routes.router, prefix="/api/v1", tags=["Vendor Intelligence"])  # /vendors/intelligence BEFORE /{vendor_id} catch-all
app.include_router(chamber_vendors_routes.router, prefix="/api/v1", tags=["Chamber Vendors"])
app.include_router(comment_routes.router, prefix="/api/v1", tags=["Comments"])
app.include_router(compliance_audits_routes.router, prefix="/api/v1", tags=["Compliance Audits"])
app.include_router(desc_certified_providers_routes.router, prefix="/api/v1", tags=["DESC Certified Providers"])
app.include_router(document_routes.router, prefix="/api/v1", tags=["Documents"])
app.include_router(download_routes.router, prefix="/api/v1", tags=["Downloads"])
app.include_router(duplicate_check_routes.router, prefix="/api/v1", tags=["Duplicate Check"])
app.include_router(evaluate_routes.router, prefix="/api/v1", tags=["Evaluate"])
app.include_router(evaluation_config_routes.router, prefix="/api/v1", tags=["Evaluation Config"])
app.include_router(evaluation_routes.router, prefix="/api/v1", tags=["Evaluations"])
app.include_router(dashboard_engagements_routes.router, prefix="/api/v1", tags=["Dashboard Engagements"])
app.include_router(dashboard_sectors_routes.router, prefix="/api/v1", tags=["Dashboard Sectors"])
app.include_router(dashboard_stats_routes.router, prefix="/api/v1", tags=["Dashboard Stats"])
app.include_router(executive_routes.router, prefix="/api/v1", tags=["Executive Dashboard"])
app.include_router(extracted_data_routes.router, prefix="/api/v1", tags=["Extracted Data"])
app.include_router(health_routes.router, prefix="/api/v1", tags=["Health"])
app.include_router(login_routes.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(logout_routes.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(me_routes.router, prefix="/api/v1", tags=["User Profile"])
app.include_router(proposal_routes.router, prefix="/api/v1", tags=["Proposals"])
app.include_router(refresh_routes.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(report_routes.router, prefix="/api/v1", tags=["Reports"])
app.include_router(sector_routes.router, prefix="/api/v1", tags=["Sector Dashboard"])
app.include_router(status_routes.router, prefix="/api/v1", tags=["Status"])
app.include_router(submit_routes.router, prefix="/api/v1", tags=["Submit"])
app.include_router(user_routes.router, prefix="/api/v1", tags=["Users"])
app.include_router(vendor_routes.router, prefix="/api/v1", tags=["Vendors"])
app.include_router(verify_routes.router, prefix="/api/v1", tags=["Verify"])
app.include_router(proposal_document_routes.router, prefix="/api/v1", tags=["Proposal Documents"])
app.include_router(proposal_ingest_routes.router, prefix="/api/v1", tags=["Proposal Document Ingestion"])
app.include_router(compliance_engine_routes.router, prefix="/api/v1", tags=["Compliance Audit Engine"])
app.include_router(compliance_engine_routes.list_router, prefix="/api/v1", tags=["Compliance Audit Results"])
app.include_router(hallucination_routes.router, prefix="/api/v1", tags=["Hallucination Shield"])
app.include_router(dashboard_impact_routes.router, prefix="/api/v1", tags=["Dashboard Impact"])
app.include_router(board_brief_routes.router, prefix="/api/v1", tags=["Board Brief"])
app.include_router(vscore_routes.router, prefix="/api/v1", tags=["vScore"])  # vendor sub-endpoints
app.include_router(incident_routes.router, prefix="/api/v1", tags=["Incident Management"])
app.include_router(public_stats_routes.router, prefix="/api/v1", tags=["Public Stats"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )
