from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List
from app.db.base import get_db
from app.models.user import User, UserRole
from app.models.auction import Auction, AuctionStatus
from app.models.event_log import EventLog
from app.schemas.user import UserResponse
from app.core.deps import get_current_user, require_role
from pydantic import BaseModel

router = APIRouter()


class UserBlockRequest(BaseModel):
    reason: str


class AuctionFreezeRequest(BaseModel):
    reason: str


class UserRoleUpdate(BaseModel):
    role: UserRole


@router.post("/users/{user_id}/block", response_model=UserResponse)
def block_user(
    user_id: int,
    block_data: UserBlockRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.moderator, UserRole.admin, UserRole.superadmin]))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.role in [UserRole.admin, UserRole.superadmin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot block admin or superadmin users"
        )

    user.is_blocked = True
    db.commit()
    db.refresh(user)

    event_log = EventLog(
        event_type="user_blocked",
        user_id=current_user.id,
        details={
            "blocked_user_id": user_id,
            "reason": block_data.reason
        }
    )
    db.add(event_log)
    db.commit()

    return user


@router.post("/users/{user_id}/unblock", response_model=UserResponse)
def unblock_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.moderator, UserRole.admin, UserRole.superadmin]))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.is_blocked = False
    db.commit()
    db.refresh(user)

    event_log = EventLog(
        event_type="user_unblocked",
        user_id=current_user.id,
        details={"unblocked_user_id": user_id}
    )
    db.add(event_log)
    db.commit()

    return user


@router.post("/auctions/{auction_id}/freeze")
def freeze_auction(
    auction_id: int,
    freeze_data: AuctionFreezeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.moderator, UserRole.admin, UserRole.superadmin]))
):
    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )

    auction.status = AuctionStatus.frozen
    db.commit()

    event_log = EventLog(
        event_type="auction_frozen",
        user_id=current_user.id,
        auction_id=auction_id,
        details={"reason": freeze_data.reason}
    )
    db.add(event_log)
    db.commit()

    return {"message": "Auction frozen successfully", "auction_id": auction_id}


@router.post("/auctions/{auction_id}/unfreeze")
def unfreeze_auction(
    auction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.moderator, UserRole.admin, UserRole.superadmin]))
):
    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if not auction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Auction not found"
        )

    auction.status = AuctionStatus.draft
    db.commit()

    event_log = EventLog(
        event_type="auction_unfrozen",
        user_id=current_user.id,
        auction_id=auction_id,
        details={}
    )
    db.add(event_log)
    db.commit()

    return {"message": "Auction unfrozen successfully", "auction_id": auction_id}


@router.get("/event-logs")
def get_event_logs(
    event_type: str = None,
    user_id: int = None,
    auction_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.admin]))
):
    query = db.query(EventLog)

    if event_type:
        query = query.filter(EventLog.event_type == event_type)
    if user_id:
        query = query.filter(EventLog.user_id == user_id)
    if auction_id:
        query = query.filter(EventLog.auction_id == auction_id)

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


@router.put("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    role_data: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.superadmin]))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.role = role_data.role
    db.commit()
    db.refresh(user)

    event_log = EventLog(
        event_type="user_role_changed",
        user_id=current_user.id,
        details={
            "target_user_id": user_id,
            "new_role": role_data.role
        }
    )
    db.add(event_log)
    db.commit()

    return user


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.admin]))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.get("/users")
def list_all_users(
    is_blocked: bool = None,
    role: UserRole = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.moderator, UserRole.admin, UserRole.superadmin]))
):
    query = db.query(User)

    if is_blocked is not None:
        query = query.filter(User.is_blocked == is_blocked)
    if role:
        query = query.filter(User.role == role)

    users = query.offset(skip).limit(limit).all()

    return [
        {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name,
            "is_blocked": user.is_blocked,
            "created_at": user.created_at
        }
        for user in users
    ]
