from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.base import get_db
from app.models.auction import Auction

router = APIRouter()


@router.get("/")
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(
        Auction.category,
        func.count(Auction.id).label("count")
    ).filter(Auction.category.isnot(None))\
     .group_by(Auction.category)\
     .all()

    return [
        {
            "name": cat.category,
            "auction_count": cat.count
        }
        for cat in categories
    ]
