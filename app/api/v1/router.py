from fastapi import APIRouter
from app.api.v1.endpoints import auth, auctions, bids, payments, admin, analytics, categories, websocket

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(admin.router, tags=["Users & Admin"])
api_router.include_router(auctions.router, prefix="/auctions", tags=["Auctions"])
api_router.include_router(bids.router, tags=["Bids"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(categories.router, prefix="/categories", tags=["Categories"])
api_router.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])
