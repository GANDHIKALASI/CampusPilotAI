from fastapi import APIRouter
from app.api.routes.chat import router as chat_router
from app.api.routes.documents import router as documents_router
from app.api.routes.waitlist import router as waitlist_router
from app.api.routes.conversations import router as conversations_router
from app.api.routes.payments import router as payments_router
from app.api.routes.admin import router as admin_router
from app.api.routes.account import router as account_router
from app.api.routes.search import router as search_router
from app.api.routes.academic import router as academic_router

api_router = APIRouter()
api_router.include_router(chat_router)
api_router.include_router(documents_router)
api_router.include_router(waitlist_router)
api_router.include_router(conversations_router)
api_router.include_router(payments_router)
api_router.include_router(admin_router)
api_router.include_router(account_router)
api_router.include_router(search_router)
api_router.include_router(academic_router)

__all__ = ["api_router"]

