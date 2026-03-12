import logging

from app.config import get_settings

logger = logging.getLogger(__name__)


def _get_stripe():
    import stripe  # type: ignore
    settings = get_settings()
    if not settings.stripe_secret_key:
        raise RuntimeError("STRIPE_SECRET_KEY não configurado no .env")
    stripe.api_key = settings.stripe_secret_key
    return stripe


def create_payment_intent(patient_name: str, patient_email: str) -> dict:
    """
    Create a Stripe PaymentIntent for the consultation fee.
    Returns {"client_secret": "...", "payment_intent_id": "..."}.
    """
    stripe = _get_stripe()
    settings = get_settings()

    intent = stripe.PaymentIntent.create(
        amount=settings.consultation_price_cents,
        currency="brl",
        automatic_payment_methods={"enabled": True},
        receipt_email=patient_email or None,
        metadata={
            "service": "videoconsulta",
            "patient_name": patient_name,
        },
    )
    logger.info("PaymentIntent created: %s for %s", intent.id, patient_email)
    return {"client_secret": intent.client_secret, "payment_intent_id": intent.id}


def refund_payment(payment_intent_id: str) -> None:
    """Issue a full refund for a succeeded PaymentIntent."""
    stripe = _get_stripe()
    stripe.Refund.create(payment_intent=payment_intent_id)
    logger.info("Refund created for PaymentIntent %s", payment_intent_id)


def verify_payment(payment_intent_id: str) -> bool:
    """
    Returns True if the PaymentIntent status is 'succeeded'.
    If Stripe is not configured, returns True (skip payment check in dev).
    """
    settings = get_settings()
    if not settings.stripe_secret_key:
        logger.warning("Stripe not configured — skipping payment verification.")
        return True

    stripe = _get_stripe()
    intent = stripe.PaymentIntent.retrieve(payment_intent_id)
    ok = intent.status == "succeeded"
    logger.info("PaymentIntent %s status=%s verified=%s", payment_intent_id, intent.status, ok)
    return ok
