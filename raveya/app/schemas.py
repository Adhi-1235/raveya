from typing import List, Optional, Literal

from pydantic import BaseModel, Field, conlist, confloat


# =========================
# Module 1 – Catalog & Tags
# =========================


class CatalogInput(BaseModel):
    product_name: str = Field(..., description="Name of the product")
    description: str = Field(..., description="Marketing or catalog description")
    attributes: Optional[dict] = Field(
        default=None,
        description="Optional structured attributes such as material, color, size, etc.",
    )


class CatalogOutput(BaseModel):
    primary_category: str
    sub_category: Optional[str] = None
    seo_tags: conlist(str, min_length=5, max_length=10)
    sustainability_filters: List[str] = Field(
        default_factory=list,
        description="e.g. plastic-free, compostable, vegan, recycled",
    )
    record_id: int


# =========================
# Module 2 – B2B Proposals
# =========================


class ProposalInput(BaseModel):
    company_name: str
    contact_email: Optional[str] = None
    total_budget: confloat(gt=0)
    target_audience: Optional[str] = Field(
        default=None,
        description="Who is the proposal for? e.g. employees, event guests, customers.",
    )
    sustainability_priorities: Optional[list[str]] = Field(
        default=None,
        description="e.g. plastic-free, local sourcing, carbon-neutral shipping.",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Extra free-form context, business rules, or constraints.",
    )


class ProposalProductItem(BaseModel):
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float
    key_sustainability_features: list[str]


class ProposalBudgetAllocation(BaseModel):
    category: str
    amount: float


class ProposalCostBreakdown(BaseModel):
    line_item: str
    amount: float


class ProposalOutput(BaseModel):
    product_mix: List[ProposalProductItem]
    budget_allocation: List[ProposalBudgetAllocation]
    cost_breakdown: List[ProposalCostBreakdown]
    impact_positioning_summary: str
    total_estimated_cost: float
    within_budget: bool
    proposal_id: int


# =========================
# Module 3 – Impact Reporting (architecture)
# =========================


class ImpactReportInput(BaseModel):
    order_id: str
    total_items: int
    plastic_items_replaced: int
    avg_plastic_weight_per_item_kg: float
    emission_factor_kg_co2_per_kg_plastic: float = 3.0
    local_sourcing_percentage: float = Field(
        default=0.0, description="0-100 percentage of items sourced locally."
    )


class ImpactReportOutput(BaseModel):
    order_id: str
    estimated_plastic_saved_kg: float
    estimated_carbon_avoided_kg: float
    local_sourcing_impact_summary: str
    human_readable_statement: str


# =========================
# Module 4 – WhatsApp Bot (architecture)
# =========================


class WhatsAppInboundMessage(BaseModel):
    from_phone: str
    text: str


class WhatsAppBotResponse(BaseModel):
    to_phone: str
    text: str
    intent: Literal["order_status", "return_policy", "refund_issue", "other"]
    escalated: bool
    conversation_id: int

