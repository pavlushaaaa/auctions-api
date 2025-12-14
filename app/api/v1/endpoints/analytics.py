from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import List, Dict
from datetime import datetime, timedelta
from app.db.base import get_db
from app.models.user import User
from app.models.auction import Auction, AuctionStatus
from app.models.bid import Bid
from app.core.deps import get_current_user
import numpy as np
from sklearn.linear_model import LinearRegression

router = APIRouter()


@router.get("/most-active-users")
def get_most_active_users(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    results = db.query(
        User.id,
        User.email,
        User.full_name,
        func.count(Bid.id).label("bid_count")
    ).join(Bid, Bid.user_id == User.id)\
     .group_by(User.id)\
     .order_by(desc("bid_count"))\
     .limit(limit)\
     .all()

    return [
        {
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "bid_count": user.bid_count
        }
        for user in results
    ]


@router.get("/auction/{auction_id}/time-between-bids")
def get_average_time_between_bids(
    auction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )

    bids = db.query(Bid).filter(Bid.auction_id == auction_id)\
           .order_by(Bid.created_at).all()

    if len(bids) < 2:
        return {"average_seconds": 0, "bid_count": len(bids)}

    time_diffs = []
    for i in range(1, len(bids)):
        diff = (bids[i].created_at - bids[i-1].created_at).total_seconds()
        time_diffs.append(diff)

    avg_seconds = sum(time_diffs) / len(time_diffs)

    return {
        "average_seconds": round(avg_seconds, 2),
        "bid_count": len(bids),
        "min_seconds": round(min(time_diffs), 2),
        "max_seconds": round(max(time_diffs), 2)
    }


@router.get("/auction/{auction_id}/price-increase")
def get_average_price_increase(
    auction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )

    bids = db.query(Bid).filter(Bid.auction_id == auction_id)\
           .order_by(Bid.created_at).all()

    if len(bids) < 2:
        return {"average_increase": 0, "bid_count": len(bids)}

    increases = []
    for i in range(1, len(bids)):
        increase = float(bids[i].amount - bids[i-1].amount)
        increases.append(increase)

    avg_increase = sum(increases) / len(increases)

    return {
        "average_increase": round(avg_increase, 2),
        "bid_count": len(bids),
        "min_increase": round(min(increases), 2),
        "max_increase": round(max(increases), 2),
        "total_increase": round(sum(increases), 2)
    }


@router.get("/auction/{auction_id}/bid-timeline")
def get_bid_timeline(
    auction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )

    bids = db.query(Bid).filter(Bid.auction_id == auction_id)\
           .order_by(Bid.created_at).all()

    timeline = [
        {
            "timestamp": bid.created_at.isoformat(),
            "amount": float(bid.amount),
            "user_id": bid.user_id
        }
        for bid in bids
    ]

    return {
        "auction_id": auction_id,
        "timeline": timeline
    }


@router.get("/top-auctions")
def get_top_auctions_by_activity(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    results = db.query(
        Auction.id,
        Auction.title,
        Auction.current_price,
        Auction.status,
        func.count(Bid.id).label("bid_count")
    ).outerjoin(Bid, Bid.auction_id == Auction.id)\
     .group_by(Auction.id)\
     .order_by(desc("bid_count"))\
     .limit(limit)\
     .all()

    return [
        {
            "auction_id": auction.id,
            "title": auction.title,
            "current_price": float(auction.current_price),
            "status": auction.status,
            "bid_count": auction.bid_count
        }
        for auction in results
    ]


@router.get("/auction/{auction_id}/predict-price")
def predict_final_price(
    auction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )

    if auction.status == AuctionStatus.closed:
        return {
            "predicted_price": float(auction.current_price),
            "confidence": "actual",
            "message": "Auction is already closed"
        }

    bids = db.query(Bid).filter(Bid.auction_id == auction_id)\
           .order_by(Bid.created_at).all()

    if len(bids) < 3:
        return {
            "predicted_price": float(auction.current_price),
            "confidence": "low",
            "message": "Not enough data for prediction"
        }

    start_time = auction.start_time.timestamp()
    X = np.array([(bid.created_at.timestamp() - start_time) / 3600 for bid in bids]).reshape(-1, 1)
    y = np.array([float(bid.amount) for bid in bids])

    model = LinearRegression()
    model.fit(X, y)

    time_to_end = (auction.end_time.timestamp() - start_time) / 3600
    predicted_price = model.predict([[time_to_end]])[0]

    predicted_price = max(predicted_price, float(auction.current_price))

    return {
        "predicted_price": round(predicted_price, 2),
        "current_price": float(auction.current_price),
        "confidence": "medium" if len(bids) >= 5 else "low",
        "bid_count": len(bids),
        "time_remaining_hours": round((auction.end_time - datetime.utcnow()).total_seconds() / 3600, 2)
    }


@router.get("/global-stats")
def get_global_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total_auctions = db.query(func.count(Auction.id)).scalar()
    active_auctions = db.query(func.count(Auction.id))\
                        .filter(Auction.status == AuctionStatus.active).scalar()
    closed_auctions = db.query(func.count(Auction.id))\
                        .filter(Auction.status == AuctionStatus.closed).scalar()

    total_bids = db.query(func.count(Bid.id)).scalar()
    total_users = db.query(func.count(User.id)).scalar()

    avg_bids_per_auction = db.query(func.avg(func.count(Bid.id)))\
                             .join(Auction, Bid.auction_id == Auction.id)\
                             .group_by(Auction.id).scalar() or 0

    return {
        "total_auctions": total_auctions,
        "active_auctions": active_auctions,
        "closed_auctions": closed_auctions,
        "total_bids": total_bids,
        "total_users": total_users,
        "average_bids_per_auction": round(float(avg_bids_per_auction), 2)
    }


@router.get("/user/{user_id}/activity")
def get_user_activity(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    total_bids = db.query(func.count(Bid.id))\
                   .filter(Bid.user_id == user_id).scalar()

    won_auctions = db.query(func.count(Auction.id))\
                     .filter(Auction.winner_id == user_id).scalar()

    auctions_participated = db.query(func.count(func.distinct(Bid.auction_id)))\
                              .filter(Bid.user_id == user_id).scalar()

    total_spent = db.query(func.sum(Auction.current_price))\
                    .filter(Auction.winner_id == user_id,
                           Auction.status == AuctionStatus.closed).scalar() or 0

    return {
        "user_id": user_id,
        "email": user.email,
        "total_bids": total_bids,
        "won_auctions": won_auctions,
        "auctions_participated": auctions_participated,
        "total_spent": float(total_spent)
    }
