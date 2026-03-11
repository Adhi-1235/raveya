from typing import Any, Dict, List

from sqlalchemy.orm import Session

from ..config import get_settings
from ..ai_client import AIClient
from ..logging_utils import log_ai_interaction
from ..models import Product, ProductAICatalogMetadata
from ..schemas import CatalogInput, CatalogOutput


PRIMARY_CATEGORIES: List[str] = [
    "Drinkware",
    "Bags & Totes",
    "Office & Stationery",
    "Home & Kitchen",
    "Personal Care",
    "Events & Gifting",
]

SUSTAINABILITY_FILTERS: List[str] = [
    "plastic-free",
    "compostable",
    "biodegradable",
    "vegan",
    "recycled",
    "recyclable",
    "locally-sourced",
    "fair-trade",
]


def _build_system_prompt() -> str:
    return (
        "You are an e-commerce catalog specialist for sustainable products. "
        "Given product details, you must:\n"
        "1) Choose the single best PRIMARY CATEGORY from this list:\n"
        f"{PRIMARY_CATEGORIES}\n"
        "2) Suggest a sub-category (short phrase) if helpful.\n"
        "3) Generate 5–10 short SEO tags (lowercase, hyphen-separated).\n"
        "4) Suggest sustainability filters from this fixed list ONLY "
        f"{SUSTAINABILITY_FILTERS} based on the description.\n"
        "Return only JSON that matches the required schema."
    )


def _json_schema_description() -> str:
    return (
        "{\n"
        '  "primary_category": string,  // one of the allowed primary categories\n'
        '  "sub_category": string | null,\n'
        '  "seo_tags": string[],        // 5-10 short tags like ["reusable-bottle", ...]\n'
        '  "sustainability_filters": string[]  // subset of the allowed filters list\n'
        "}"
    )


def auto_categorize_and_tag(
    db: Session,
    ai_client: AIClient,
    payload: CatalogInput,
) -> CatalogOutput:
    """
    Full implementation of Module 1:
    - Persist product (raw input)
    - Call AI to compute structured catalog metadata
    - Store AI metadata
    - Log prompt + response
    """
    product = Product(
        name=payload.product_name,
        description=payload.description,
        raw_attributes=payload.attributes and str(payload.attributes),
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    system_prompt = _build_system_prompt()
    # Pydantic v2 uses model_dump() instead of model_dict()
    user_payload: Dict[str, Any] = payload.model_dump()

    settings = get_settings()

    if settings.AI_MODE == "mock":
        # Simple heuristic mock logic
        text = f"{payload.product_name} {payload.description}".lower()
        if any(k in text for k in ["cup", "bottle", "mug", "drink", "coffee", "water"]):
            primary = "Drinkware"
        elif any(k in text for k in ["bag", "tote", "backpack"]):
            primary = "Bags & Totes"
        elif any(k in text for k in ["notebook", "pen", "desk", "office"]):
            primary = "Office & Stationery"
        elif any(k in text for k in ["soap", "lotion", "skincare", "care"]):
            primary = "Personal Care"
        elif any(k in text for k in ["event", "gift", "gifting", "welcome kit"]):
            primary = "Events & Gifting"
        else:
            primary = "Home & Kitchen"

        tokens = [
            t.strip(".,! ").lower()
            for t in payload.product_name.split()
            + payload.description.split()
        ]
        base_tags = list({t.replace(" ", "-") for t in tokens if len(t) > 3})
        seo_tags = base_tags[:8] or ["sustainable-product"]

        filters: List[str] = []
        if "plastic" in text and "free" in text:
            filters.append("plastic-free")
        if "compostable" in text:
            filters.append("compostable")
        if "vegan" in text:
            filters.append("vegan")
        if "recycled" in text or "recycl" in text:
            filters.append("recycled")

        result: Dict[str, Any] = {
            "primary_category": primary,
            "sub_category": None,
            "seo_tags": seo_tags,
            "sustainability_filters": filters,
        }
    else:
        result = ai_client.generate_json(
            system_prompt=system_prompt,
            user_payload=user_payload,
            json_schema_description=_json_schema_description(),
        )

    meta = ProductAICatalogMetadata(
        product_id=product.id,
        primary_category=result.get("primary_category", "Uncategorized"),
        sub_category=result.get("sub_category"),
        seo_tags=",".join(result.get("seo_tags", [])),
        sustainability_filters=",".join(result.get("sustainability_filters", [])),
        raw_ai_response=str(result),
    )
    db.add(meta)
    db.commit()
    db.refresh(meta)

    # Log AI interaction
    log_ai_interaction(
        db,
        module_name="catalog_auto_category",
        request_payload=user_payload,
        prompt=system_prompt,
        response=meta.raw_ai_response,
    )

    return CatalogOutput(
        primary_category=meta.primary_category,
        sub_category=meta.sub_category,
        seo_tags=meta.seo_tags.split(",") if meta.seo_tags else [],
        sustainability_filters=meta.sustainability_filters.split(",")
        if meta.sustainability_filters
        else [],
        record_id=meta.id,
    )

