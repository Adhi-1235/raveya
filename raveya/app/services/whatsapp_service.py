from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..models import WhatsAppConversation
from ..schemas import WhatsAppBotResponse, WhatsAppInboundMessage


@dataclass
class WhatsAppOrderLookupResult:
    order_id: str
    status: str
    eta_days: int | None


def _detect_intent(text: str) -> str:
    lower = text.lower()
    if "status" in lower or "track" in lower or "where is my order" in lower:
        return "order_status"
    if "return" in lower or "exchange" in lower:
        return "return_policy"
    if "refund" in lower or "money back" in lower:
        return "refund_issue"
    return "other"


def _lookup_order_for_phone(_db: Session, _phone: str) -> WhatsAppOrderLookupResult | None:
    """
    Architecture placeholder:
    - In production, join orders table by linked customer/phone.
    - Here we simply return a dummy result for demonstration.
    """
    return None


def _build_order_status_reply(result: WhatsAppOrderLookupResult | None) -> str:
    if result is None:
        return "I couldn't find an active order linked to this phone number. Please share your order ID."
    if result.eta_days is not None:
        return (
            f"Your order {result.order_id} is currently '{result.status}'. "
            f"Estimated delivery in {result.eta_days} days."
        )
    return f"Your order {result.order_id} is currently '{result.status}'."


def _build_return_policy_reply() -> str:
    return (
        "You can return unused products within 30 days in original packaging. "
        "For bulk B2B orders, please contact your account manager for logistics support."
    )


def _build_refund_issue_reply() -> str:
    return (
        "I'm escalating this to our human support team right away. "
        "You'll receive a response about your refund status within one business day."
    )


def handle_whatsapp_message(db: Session, payload: WhatsAppInboundMessage) -> WhatsAppBotResponse:
    """
    Architecture for Module 4 – core routing logic without external WhatsApp API integration.

    Responsibilities:
    - Detect intent from free-text message
    - For order status: look up real DB data (stubbed here)
    - For returns: explain policy
    - For refunds: escalate & mark conversation
    - Persist latest conversation state for analytics and traceability
    """
    intent = _detect_intent(payload.text)

    if intent == "order_status":
        order_result = _lookup_order_for_phone(db, payload.from_phone)
        reply_text = _build_order_status_reply(order_result)
        escalated = False
    elif intent == "return_policy":
        reply_text = _build_return_policy_reply()
        escalated = False
    elif intent == "refund_issue":
        reply_text = _build_refund_issue_reply()
        escalated = True
    else:
        reply_text = (
            "I'm here to help with order status, returns, and refund questions. "
            "Could you please share more details or your order ID?"
        )
        escalated = False

    conversation = WhatsAppConversation(
        user_phone=payload.from_phone,
        last_message_direction="user",
        last_message_text=payload.text,
        status="escalated" if escalated else "open",
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return WhatsAppBotResponse(
        to_phone=payload.from_phone,
        text=reply_text,
        intent=intent,  # type: ignore[arg-type]
        escalated=escalated,
        conversation_id=conversation.id,
    )

