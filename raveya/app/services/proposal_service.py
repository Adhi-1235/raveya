import json
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from ..ai_client import AIClient
from ..config import get_settings
from ..logging_utils import log_ai_interaction
from ..models import B2BProposal
from ..schemas import (
    ProposalBudgetAllocation,
    ProposalCostBreakdown,
    ProposalInput,
    ProposalOutput,
    ProposalProductItem,
)


def _build_system_prompt() -> str:
    return (
        "You are a B2B sales strategist for sustainable corporate gifting and procurement.\n"
        "Given company context and a total budget, you must propose a realistic sustainable "
        "product mix and cost structure that stays within the budget.\n\n"
        "Requirements:\n"
        "- Prefer plastic-free, reusable, low-waste products.\n"
        "- Make sure the sum of all costs does not exceed the total budget.\n"
        "- Provide a clear impact positioning summary that a salesperson could paste into a proposal.\n"
        "Return only JSON following the given schema; do not explain anything else."
    )


def _json_schema_description() -> str:
    return (
        "{\n"
        '  "product_mix": [\n'
        "    {\n"
        '      "product_name": string,\n'
        '      "quantity": integer,\n'
        '      "unit_price": number,\n'
        '      "subtotal": number,\n'
        '      "key_sustainability_features": string[]\n'
        "    }, ...\n"
        "  ],\n"
        '  "budget_allocation": [\n'
        "    {\n"
        '      "category": string,   // e.g. \"products\", \"packaging\", \"logistics\"\n'
        '      "amount": number\n'
        "    }, ...\n"
        "  ],\n"
        '  "cost_breakdown": [\n'
        "    {\n"
        '      "line_item": string,\n'
        '      "amount": number\n'
        "    }, ...\n"
        "  ],\n"
        '  "impact_positioning_summary": string,\n'
        '  "total_estimated_cost": number,\n'
        '  "within_budget": boolean\n'
        "}"
    )


def generate_b2b_proposal(
    db: Session,
    ai_client: AIClient,
    payload: ProposalInput,
) -> ProposalOutput:
    """
    Full implementation of Module 2:
    - Call AI for structured proposal JSON
    - Enforce basic budget validation
    - Persist proposal row
    - Log prompt + response
    """
    system_prompt = _build_system_prompt()
    # Pydantic v2 uses model_dump() instead of model_dict()
    user_payload: Dict[str, Any] = payload.model_dump()

    settings = get_settings()

    if settings.AI_MODE == "mock":
        total_budget = float(payload.total_budget)
        products_budget = total_budget * 0.8
        logistics_budget = total_budget * 0.2

        product_mix_raw = [
            {
                "product_name": "Reusable stainless steel bottle",
                "quantity": 50,
                "unit_price": round(products_budget * 0.6 / 50, 2),
                "subtotal": round(products_budget * 0.6, 2),
                "key_sustainability_features": ["reusable", "plastic-free"],
            },
            {
                "product_name": "Recycled cotton tote bag",
                "quantity": 50,
                "unit_price": round(products_budget * 0.4 / 50, 2),
                "subtotal": round(products_budget * 0.4, 2),
                "key_sustainability_features": ["recycled", "reusable"],
            },
        ]
        budget_allocation_raw = [
            {"category": "products", "amount": round(products_budget, 2)},
            {"category": "logistics & packaging", "amount": round(logistics_budget, 2)},
        ]
        cost_breakdown_raw = [
            {"line_item": "Products subtotal", "amount": round(products_budget, 2)},
            {"line_item": "Logistics & packaging", "amount": round(logistics_budget, 2)},
        ]
        total_estimated_cost = round(products_budget + logistics_budget, 2)
        result: Dict[str, Any] = {
            "product_mix": product_mix_raw,
            "budget_allocation": budget_allocation_raw,
            "cost_breakdown": cost_breakdown_raw,
            "impact_positioning_summary": (
                "This proposal prioritises durable, reusable items that significantly reduce single-use plastic, "
                "while keeping total spend within the specified budget."
            ),
            "total_estimated_cost": total_estimated_cost,
            "within_budget": True,
        }
    else:
        result = ai_client.generate_json(
            system_prompt=system_prompt,
            user_payload=user_payload,
            json_schema_description=_json_schema_description(),
        )

    # Defensive parsing and budget validation
    total_estimated_cost = float(result.get("total_estimated_cost", 0.0))
    within_budget = bool(result.get("within_budget", total_estimated_cost <= payload.total_budget))
    if total_estimated_cost > payload.total_budget:
        # Force within_budget flag if the model misbehaves
        within_budget = False

        # Optionally, you could scale down proportions here; for now we simply mark it.

    product_mix_structured: List[ProposalProductItem] = [
        ProposalProductItem(**item) for item in result.get("product_mix", [])
    ]
    budget_allocation_structured: List[ProposalBudgetAllocation] = [
        ProposalBudgetAllocation(**item) for item in result.get("budget_allocation", [])
    ]
    cost_breakdown_structured: List[ProposalCostBreakdown] = [
        ProposalCostBreakdown(**item) for item in result.get("cost_breakdown", [])
    ]

    proposal = B2BProposal(
        company_name=payload.company_name,
        contact_email=payload.contact_email,
        total_budget=float(payload.total_budget),
        input_context=json.dumps(user_payload, ensure_ascii=False),
        product_mix_json=json.dumps([pm.model_dump() for pm in product_mix_structured]),
        budget_allocation_json=json.dumps(
            [ba.model_dump() for ba in budget_allocation_structured]
        ),
        cost_breakdown_json=json.dumps(
            [cb.model_dump() for cb in cost_breakdown_structured]
        ),
        impact_positioning_summary=result.get("impact_positioning_summary", ""),
        raw_ai_response=json.dumps(result),
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)

    log_ai_interaction(
        db,
        module_name="b2b_proposal",
        request_payload=user_payload,
        prompt=system_prompt,
        response=proposal.raw_ai_response,
    )

    return ProposalOutput(
        product_mix=product_mix_structured,
        budget_allocation=budget_allocation_structured,
        cost_breakdown=cost_breakdown_structured,
        impact_positioning_summary=proposal.impact_positioning_summary,
        total_estimated_cost=total_estimated_cost,
        within_budget=within_budget,
        proposal_id=proposal.id,
    )

