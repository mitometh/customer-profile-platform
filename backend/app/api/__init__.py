from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.auth import users_router
from app.api.routes.chat import router as chat_router
from app.api.routes.customers import router as customers_router
from app.api.routes.events import router as events_router
from app.api.routes.health import router as health_router
from app.api.routes.metrics import catalog_router as metrics_catalog_router
from app.api.routes.metrics import customer_metrics_router
from app.api.routes.roles import permissions_router, roles_router
from app.api.routes.sources import router as sources_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(customers_router, prefix="/customers", tags=["customers"])
router.include_router(
    events_router,
    prefix="/customers/{customer_id}/events",
    tags=["events"],
)
router.include_router(metrics_catalog_router, prefix="/metrics", tags=["metrics"])
router.include_router(
    customer_metrics_router,
    prefix="/customers/{customer_id}/metrics",
    tags=["metrics"],
)
router.include_router(chat_router, prefix="/chat", tags=["chat"])
router.include_router(sources_router, prefix="/sources", tags=["sources"])
router.include_router(roles_router, prefix="/roles", tags=["roles"])
router.include_router(permissions_router, prefix="/permissions", tags=["permissions"])
router.include_router(health_router, prefix="/health", tags=["health"])
