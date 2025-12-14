from datetime import datetime
from sqlalchemy import and_
from app.celery_app import celery_app
from app.db.base import SessionLocal
from app.models.auction import Auction, AuctionStatus
from app.models.bid import Bid
from app.models.event_log import EventLog


@celery_app.task(name="close_expired_auctions")
def close_expired_auctions():
    db = SessionLocal()
    try:
        now = datetime.utcnow()

        expired_auctions = db.query(Auction).filter(
            and_(
                Auction.status == AuctionStatus.active,
                Auction.end_time <= now
            )
        ).all()

        for auction in expired_auctions:
            highest_bid = db.query(Bid).filter(
                Bid.auction_id == auction.id
            ).order_by(Bid.amount.desc()).first()

            auction.status = AuctionStatus.closed
            if highest_bid:
                auction.winner_id = highest_bid.user_id

            event_log = EventLog(
                event_type="auction_closed",
                auction_id=auction.id,
                details={
                    "winner_id": auction.winner_id,
                    "final_price": str(auction.current_price)
                }
            )
            db.add(event_log)

        db.commit()
        return f"Closed {len(expired_auctions)} auctions"

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


@celery_app.task(name="activate_scheduled_auctions")
def activate_scheduled_auctions():
    db = SessionLocal()
    try:
        now = datetime.utcnow()

        scheduled_auctions = db.query(Auction).filter(
            and_(
                Auction.status == AuctionStatus.draft,
                Auction.start_time <= now,
                Auction.end_time > now
            )
        ).all()

        for auction in scheduled_auctions:
            auction.status = AuctionStatus.active

            event_log = EventLog(
                event_type="auction_activated",
                auction_id=auction.id,
                details={"title": auction.title}
            )
            db.add(event_log)

        db.commit()
        return f"Activated {len(scheduled_auctions)} auctions"

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
