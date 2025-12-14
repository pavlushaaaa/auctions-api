from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.models.auction import Auction
from app.services.websocket_manager import manager
from app.core.security import decode_access_token

router = APIRouter()


@router.websocket("/auctions/{auction_id}")
async def websocket_auction(
    websocket: WebSocket,
    auction_id: int,
    token: str = Query(None),
    db: Session = Depends(get_db)
):
    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if not auction:
        await websocket.close(code=4004, reason="Auction not found")
        return

    user_id = None
    if token:
        payload = decode_access_token(token)
        if payload:
            user_id = payload.get("user_id")

    await manager.connect(websocket, auction_id, user_id)

    try:
        await websocket.send_json({
            "type": "connected",
            "auction_id": auction_id,
            "message": "Successfully connected to auction updates"
        })

        while True:
            _ = await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket, auction_id, user_id)
        await manager.broadcast_online_count(auction_id)
