import uuid
from decimal import Decimal
from app.models.payment import Payment, PaymentStatus


class MockPaymentService:
    """
    Mock payment service simulating Stripe/PayPal sandbox
    This is for demonstration purposes only
    """

    @staticmethod
    def create_payment_hold(auction_id: int, user_id: int, amount: Decimal, commission: Decimal = Decimal("0.00")):
        total_amount = amount + commission
        transaction_id = f"mock_txn_{uuid.uuid4().hex[:16]}"

        payment = Payment(
            auction_id=auction_id,
            user_id=user_id,
            amount=amount,
            commission=commission,
            total_amount=total_amount,
            status=PaymentStatus.held,
            payment_method="mock_card",
            transaction_id=transaction_id,
            metadata={
                "mock": True,
                "card_last4": "4242",
                "card_brand": "visa"
            }
        )

        return payment

    @staticmethod
    def confirm_payment(payment: Payment) -> bool:
        if payment.status != PaymentStatus.held:
            return False

        payment.status = PaymentStatus.paid
        payment.metadata = {
            **payment.metadata,
            "confirmed": True,
            "confirmation_id": f"conf_{uuid.uuid4().hex[:12]}"
        }
        return True

    @staticmethod
    def refund_payment(payment: Payment) -> bool:
        if payment.status not in [PaymentStatus.paid, PaymentStatus.held]:
            return False

        payment.status = PaymentStatus.refunded
        payment.metadata = {
            **payment.metadata,
            "refunded": True,
            "refund_id": f"ref_{uuid.uuid4().hex[:12]}"
        }
        return True

    @staticmethod
    def simulate_payment_failure(payment: Payment) -> None:
        payment.status = PaymentStatus.failed
        payment.metadata = {
            **payment.metadata,
            "error": "Simulated payment failure",
            "error_code": "insufficient_funds"
        }


payment_service = MockPaymentService()
