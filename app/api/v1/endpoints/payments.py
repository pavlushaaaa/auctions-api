from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.base import get_db
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.models.payment import Payment, PaymentStatus
from app.models.auction import Auction, AuctionStatus
from app.models.user import User
from app.core.deps import get_current_user
from app.services.payment_service import payment_service
from decimal import Decimal

router = APIRouter()


@router.post("/hold", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment_hold(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    auction = db.query(Auction).filter(Auction.id == payment_data.auction_id).first()
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

    if auction.winner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the winner of this auction"
        )

    existing_payment = db.query(Payment).filter(
        Payment.auction_id == auction.id,
        Payment.user_id == current_user.id,
        Payment.status.in_([PaymentStatus.held, PaymentStatus.paid])
    ).first()

    if existing_payment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment already exists for this auction"
        )

    commission = auction.current_price * (auction.commission_rate / Decimal("100.0"))

    payment = payment_service.create_payment_hold(
        auction_id=auction.id,
        user_id=current_user.id,
        amount=auction.current_price,
        commission=commission
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment


@router.post("/{payment_id}/confirm", response_model=PaymentResponse)
def confirm_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    if payment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to confirm this payment"
        )

    success = payment_service.confirm_payment(payment)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot confirm payment in current status"
        )

    db.commit()
    db.refresh(payment)

    return payment


@router.post("/{payment_id}/refund", response_model=PaymentResponse)
def refund_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    auction = db.query(Auction).filter(Auction.id == payment.auction_id).first()
    if auction.organizer_id != current_user.id and current_user.role.value not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to refund this payment"
        )

    success = payment_service.refund_payment(payment)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot refund payment in current status"
        )

    db.commit()
    db.refresh(payment)

    return payment


@router.get("/my-payments", response_model=List[PaymentResponse])
def get_my_payments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payments = db.query(Payment).filter(
        Payment.user_id == current_user.id
    ).offset(skip).limit(limit).all()

    return payments


@router.get("/auction/{auction_id}", response_model=PaymentResponse)
def get_auction_payment(
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

    payment = db.query(Payment).filter(
        Payment.auction_id == auction_id,
        Payment.user_id == current_user.id
    ).first()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    return payment
