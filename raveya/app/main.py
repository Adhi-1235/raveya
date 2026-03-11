from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .ai_client import AIClient
from .config import get_settings
from .db import Base, engine, get_db
from .schemas import (
    CatalogInput,
    CatalogOutput,
    ImpactReportInput,
    ImpactReportOutput,
    ProposalInput,
    ProposalOutput,
    WhatsAppBotResponse,
    WhatsAppInboundMessage,
)
from .services.catalog_service import auto_categorize_and_tag
from .services.impact_service import generate_impact_report
from .services.proposal_service import generate_b2b_proposal
from .services.whatsapp_service import handle_whatsapp_message


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Raveya AI Backend",
    version="1.0.0",
    description="AI-powered modules for catalog, B2B proposals, impact reporting, and WhatsApp support.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_ai_client():
    """
    Returns a real AIClient in 'live' mode, or a dummy object in 'mock' mode.
    In mock mode the services avoid calling generate_json, so no OpenAI key is required.
    """
    settings = get_settings()
    if settings.AI_MODE == "mock":
        class _DummyClient:
            def generate_json(self, *args, **kwargs):
                raise RuntimeError("generate_json should not be called in mock AI_MODE")

        return _DummyClient()

    try:
        return AIClient()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@app.get("/health", tags=["system"])
def health() -> dict:
    return {"status": "ok"}


@app.post("/ai/catalog/auto-tag", response_model=CatalogOutput, tags=["module-1"])
def api_auto_tag(
    payload: CatalogInput,
    db: Session = Depends(get_db),
    ai_client: AIClient = Depends(get_ai_client),
) -> CatalogOutput:
    """
    Module 1 – AI Auto-Category & Tag Generator.
    """
    try:
        return auto_categorize_and_tag(db, ai_client, payload)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to auto-categorize product: {exc}",
        ) from exc


@app.post("/ai/proposals/generate", response_model=ProposalOutput, tags=["module-2"])
def api_generate_proposal(
    payload: ProposalInput,
    db: Session = Depends(get_db),
    ai_client: AIClient = Depends(get_ai_client),
) -> ProposalOutput:
    """
    Module 2 – AI B2B Proposal Generator.
    """
    try:
        return generate_b2b_proposal(db, ai_client, payload)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate proposal: {exc}",
        ) from exc


@app.post("/impact/report", response_model=ImpactReportOutput, tags=["module-3"])
def api_generate_impact_report(
    payload: ImpactReportInput,
    db: Session = Depends(get_db),
) -> ImpactReportOutput:
    """
    Module 3 – Impact Reporting (logic-only example).
    """
    return generate_impact_report(db, payload)


@app.post(
    "/whatsapp/webhook",
    response_model=WhatsAppBotResponse,
    tags=["module-4"],
)
def api_whatsapp_webhook(
    payload: WhatsAppInboundMessage,
    db: Session = Depends(get_db),
) -> WhatsAppBotResponse:
    """
    Module 4 – WhatsApp Support Bot (architecture only).

    In production this route would be called by a WhatsApp provider like Twilio / Meta Cloud API.
    """
    return handle_whatsapp_message(db, payload)

