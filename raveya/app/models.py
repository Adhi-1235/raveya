from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .db import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    raw_attributes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    ai_catalog_metadata: Mapped["ProductAICatalogMetadata"] = relationship(
        "ProductAICatalogMetadata",
        back_populates="product",
        uselist=False,
    )


class ProductAICatalogMetadata(Base):
    """
    Stores the structured output of Module 1 (auto-category & tags).
    """

    __tablename__ = "product_ai_catalog_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    primary_category: Mapped[str] = mapped_column(String(100), nullable=False)
    sub_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    seo_tags: Mapped[str] = mapped_column(Text, nullable=False)  # comma-separated for simplicity
    sustainability_filters: Mapped[str] = mapped_column(Text, nullable=True)  # comma-separated
    raw_ai_response: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    product: Mapped[Product] = relationship("Product", back_populates="ai_catalog_metadata")


class B2BProposal(Base):
    """
    Stores structured output of Module 2 (proposal generator).
    """

    __tablename__ = "b2b_proposals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    total_budget: Mapped[float] = mapped_column(Float, nullable=False)
    input_context: Mapped[str] = mapped_column(Text, nullable=True)

    product_mix_json: Mapped[str] = mapped_column(Text, nullable=False)
    budget_allocation_json: Mapped[str] = mapped_column(Text, nullable=False)
    cost_breakdown_json: Mapped[str] = mapped_column(Text, nullable=False)
    impact_positioning_summary: Mapped[str] = mapped_column(Text, nullable=False)
    raw_ai_response: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ImpactReport(Base):
    """
    Architecture for Module 3 – impact reporting per order.
    """

    __tablename__ = "impact_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[str] = mapped_column(String(100), index=True)
    estimated_plastic_saved_kg: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_carbon_avoided_kg: Mapped[float] = mapped_column(Float, nullable=False)
    local_sourcing_impact_summary: Mapped[str] = mapped_column(Text, nullable=False)
    human_readable_statement: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WhatsAppConversation(Base):
    """
    Architecture for Module 4 – logs of WhatsApp support interactions.
    """

    __tablename__ = "whatsapp_conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_phone: Mapped[str] = mapped_column(String(50), index=True)
    last_message_direction: Mapped[str] = mapped_column(String(10))  # "user" or "agent"
    last_message_text: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="open")  # open, escalated, resolved
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class AIRequestLog(Base):
    """
    Central logging for prompts and responses across all modules.
    """

    __tablename__ = "ai_request_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    module_name: Mapped[str] = mapped_column(String(100), index=True)
    request_payload: Mapped[str] = mapped_column(Text, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

