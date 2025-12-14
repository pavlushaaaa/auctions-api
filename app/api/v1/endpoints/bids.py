from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from datetime import datetime, timedelta
from app.db.base import get_db
from app.schemas.bid import BidCreate, BidResponse
from app.models.bid import Bid
from app.models.auction import Auction, AuctionStatus
from app.models.user import User
from app.models.event_log import EventLog
from app.core.deps import get_current_user
from app.services.websocket_manager import manager
import asyncio

router = APIRouter()


async def broadcast_new_bid(auction_id: int, bid_data: dict):
    await manager.broadcast(auction_id, {
        "type": "new_bid",
        "data": bid_data
    })


@router.post("/auctions/{auction_id}/bids", response_model=BidResponse, status_code=status.HTTP_201_CREATED)
async def place_bid(
    auction_id: int,
    bid_data: BidCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if bid_data.auction_id != auction_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Auction ID mismatch"
        )

    auction = db.query(Auction).filter(Auction.id == auction_id).with_for_update().first()

    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )

    if auction.status != AuctionStatus.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Auction is not active"
        )

    now = datetime.utcnow()
    if now < auction.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Auction has not started yet"
        )

    if now > auction.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Auction has ended"
        )

    if auction.organizer_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organizer cannot bid on their own auction"
        )

    if auction.buyout_price and bid_data.amount >= auction.buyout_price:
        auction.current_price = bid_data.amount
        auction.status = AuctionStatus.closed
        auction.winner_id = current_user.id

    minimum_bid = auction.current_price + auction.bid_step
    if bid_data.amount < minimum_bid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bid must be at least {minimum_bid}"
        )

    bid = Bid(
        auction_id=auction.id,
        user_id=current_user.id,
        amount=bid_data.amount
    )
    db.add(bid)

    previous_price = auction.current_price
    auction.current_price = bid_data.amount
    auction.updated_at = datetime.utcnow()

    if auction.anti_snipe_enabled:
        time_remaining = (auction.end_time - now).total_seconds()
        if time_remaining <= auction.anti_snipe_seconds:
            if auction.anti_snipe_count < auction.anti_snipe_max_extensions:
                auction.end_time = auction.end_time + timedelta(seconds=auction.anti_snipe_extension)
                auction.anti_snipe_count += 1

                event_log_snipe = EventLog(
                    event_type="anti_snipe_triggered",
                    user_id=current_user.id,
                    auction_id=auction.id,
                    details={
                        "extension_count": auction.anti_snipe_count,
                        "new_end_time": auction.end_time.isoformat()
                    }
                )
                db.add(event_log_snipe)

    event_log = EventLog(
        event_type="bid_placed",
        user_id=current_user.id,
        auction_id=auction.id,
        details={"amount": str(bid_data.amount)}
    )
    db.add(event_log)

    db.commit()
    db.refresh(bid)

    await broadcast_new_bid(auction.id, {
        "bid_id": bid.id,
        "auction_id": auction.id,
        "user_id": current_user.id,
        "amount": str(bid_data.amount),
        "current_price": str(auction.current_price),
        "end_time": auction.end_time.isoformat(),
        "created_at": bid.created_at.isoformat()
    })

    return bid


@router.get("/auctions/{auction_id}/bids", response_model=List[BidResponse])
def get_auction_bids(
    auction_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )

    bids = db.query(Bid).filter(Bid.auction_id == auction_id).order_by(desc(Bid.created_at)).offset(skip).limit(limit).all()
    return bids


@router.get("/users/{user_id}/bids", response_model=List[BidResponse])
def get_user_bids(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only view your own bids"
        )

    bids = db.query(Bid).filter(Bid.user_id == user_id).order_by(desc(Bid.created_at)).offset(skip).limit(limit).all()
    return bids
