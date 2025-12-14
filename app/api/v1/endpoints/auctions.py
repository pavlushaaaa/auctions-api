from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import List
from datetime import datetime
from app.db.base import get_db
from app.schemas.auction import AuctionCreate, AuctionResponse, AuctionUpdate, AuctionListResponse
from app.models.auction import Auction, AuctionStatus
from app.models.user import User, UserRole
from app.models.event_log import EventLog
from app.core.deps import get_current_user, require_role

router = APIRouter()


@router.post("/", response_model=AuctionResponse, status_code=status.HTTP_201_CREATED)
def create_auction(
    auction_data: AuctionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.organizer, UserRole.admin]))
):
    if auction_data.end_time <= auction_data.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time"
        )

    auction = Auction(
        title=auction_data.title,
        description=auction_data.description,
        category=auction_data.category,
        starting_price=auction_data.starting_price,
        current_price=auction_data.starting_price,
        bid_step=auction_data.bid_step,
        start_time=auction_data.start_time,
        end_time=auction_data.end_time,
        auction_type=auction_data.auction_type,
        buyout_price=auction_data.buyout_price,
        reserve_price=auction_data.reserve_price,
        commission_rate=auction_data.commission_rate,
        anti_snipe_enabled=auction_data.anti_snipe_enabled,
        anti_snipe_seconds=auction_data.anti_snipe_seconds,
        anti_snipe_extension=auction_data.anti_snipe_extension,
        anti_snipe_max_extensions=auction_data.anti_snipe_max_extensions,
        organizer_id=current_user.id
    )
    db.add(auction)
    db.commit()
    db.refresh(auction)

    event_log = EventLog(
        event_type="auction_created",
        user_id=current_user.id,
        auction_id=auction.id,
        details={"title": auction.title}
    )
    db.add(event_log)
    db.commit()

    return auction


@router.get("/", response_model=List[AuctionListResponse])
def list_auctions(
    status_filter: AuctionStatus | None = None,
    category: str | None = None,
    search: str | None = None,
    organizer_id: int | None = None,
    auction_type: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    sort_by: str = Query("created_at", regex="^(created_at|current_price|end_time)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Auction)

    if status_filter:
        query = query.filter(Auction.status == status_filter)

    if category:
        query = query.filter(Auction.category == category)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Auction.title.ilike(search_pattern)) |
            (Auction.description.ilike(search_pattern))
        )

    if organizer_id:
        query = query.filter(Auction.organizer_id == organizer_id)

    if auction_type:
        query = query.filter(Auction.auction_type == auction_type)

    if min_price is not None:
        query = query.filter(Auction.current_price >= min_price)

    if max_price is not None:
        query = query.filter(Auction.current_price <= max_price)

    sort_column = getattr(Auction, sort_by)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    auctions = query.offset(skip).limit(limit).all()
    return auctions


@router.get("/{auction_id}", response_model=AuctionResponse)
def get_auction(auction_id: int, db: Session = Depends(get_db)):
    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )
    return auction


@router.put("/{auction_id}", response_model=AuctionResponse)
def update_auction(
    auction_id: int,
    auction_data: AuctionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.organizer, UserRole.admin]))
):
    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )

    if auction.organizer_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this auction"
        )

    if auction.status == AuctionStatus.closed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update closed auction"
        )

    update_data = auction_data.model_dump(exclude_unset=True)

    if "end_time" in update_data or "start_time" in update_data:
        start_time = update_data.get("start_time", auction.start_time)
        end_time = update_data.get("end_time", auction.end_time)
        if end_time <= start_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End time must be after start time"
            )

    for field, value in update_data.items():
        setattr(auction, field, value)

    auction.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(auction)

    event_log = EventLog(
        event_type="auction_updated",
        user_id=current_user.id,
        auction_id=auction.id,
        details=update_data
    )
    db.add(event_log)
    db.commit()

    return auction


@router.delete("/{auction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_auction(
    auction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.organizer, UserRole.admin]))
):
    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )

    if auction.organizer_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this auction"
        )

    if auction.status != AuctionStatus.draft:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only delete draft auctions"
        )

    event_log = EventLog(
        event_type="auction_deleted",
        user_id=current_user.id,
        auction_id=auction.id,
        details={"title": auction.title}
    )
    db.add(event_log)

    db.delete(auction)
    db.commit()

    return None


@router.post("/{auction_id}/close", response_model=AuctionResponse)
def close_auction(
    auction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.organizer, UserRole.admin]))
):
    from app.models.bid import Bid
    from sqlalchemy import desc as sql_desc

    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )

    if auction.organizer_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to close this auction"
        )

    if auction.status == AuctionStatus.closed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Auction is already closed"
        )

    if auction.status != AuctionStatus.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only close active auctions"
        )

    highest_bid = db.query(Bid).filter(Bid.auction_id == auction_id).order_by(sql_desc(Bid.amount)).first()

    if highest_bid:
        if auction.reserve_price and highest_bid.amount < auction.reserve_price:
            auction.status = AuctionStatus.closed
            auction.winner_id = None
        else:
            auction.status = AuctionStatus.closed
            auction.winner_id = highest_bid.user_id
            auction.current_price = highest_bid.amount
    else:
        auction.status = AuctionStatus.closed
        auction.winner_id = None

    auction.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(auction)

    event_log = EventLog(
        event_type="auction_closed",
        user_id=current_user.id,
        auction_id=auction.id,
        details={
            "winner_id": auction.winner_id,
            "final_price": str(auction.current_price) if auction.winner_id else None
        }
    )
    db.add(event_log)
    db.commit()

    return auction


@router.get("/{auction_id}/winner", response_model=dict)
def get_auction_winner(
    auction_id: int,
    db: Session = Depends(get_db)
):
    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )

    if auction.status != AuctionStatus.closed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Auction is not closed yet"
        )

    if not auction.winner_id:
        return {
            "auction_id": auction_id,
            "winner": None,
            "message": "No winner (reserve price not met or no bids)"
        }

    winner = db.query(User).filter(User.id == auction.winner_id).first()

    return {
        "auction_id": auction_id,
        "winner": {
            "id": winner.id,
            "email": winner.email,
            "full_name": winner.full_name
        },
        "winning_bid": str(auction.current_price)
    }


@router.get("/{auction_id}/event-logs")
def get_auction_event_logs(
    auction_id: int,
    event_type: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.admin]))
):
    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )

    query = db.query(EventLog).filter(EventLog.auction_id == auction_id)

    if event_type:
        query = query.filter(EventLog.event_type == event_type)

    logs = query.order_by(desc(EventLog.created_at)).offset(skip).limit(limit).all()

    return [
        {
            "id": log.id,
            "event_type": log.event_type,
            "user_id": log.user_id,
            "auction_id": log.auction_id,
            "details": log.details,
            "created_at": log.created_at
        }
        for log in logs
    ]
