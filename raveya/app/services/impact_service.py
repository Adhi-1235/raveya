from sqlalchemy.orm import Session

from ..models import ImpactReport
from ..schemas import ImpactReportInput, ImpactReportOutput


def generate_impact_report(db: Session, payload: ImpactReportInput) -> ImpactReportOutput:
    """
    Architecture for Module 3 – purely logic-based estimation (no AI dependency).

    Simple example logic:
    - estimated_plastic_saved_kg = plastic_items_replaced * avg_plastic_weight_per_item_kg
    - estimated_carbon_avoided_kg = estimated_plastic_saved_kg * emission_factor_kg_co2_per_kg_plastic
    - local_sourcing_impact_summary: explain based on local_sourcing_percentage
    - human_readable_statement: templated paragraph combining the above
    """
    estimated_plastic_saved_kg = (
        payload.plastic_items_replaced * payload.avg_plastic_weight_per_item_kg
    )
    estimated_carbon_avoided_kg = (
        estimated_plastic_saved_kg * payload.emission_factor_kg_co2_per_kg_plastic
    )

    if payload.local_sourcing_percentage >= 70:
        local_summary = "Most of this order was locally sourced, helping reduce transport emissions and support nearby suppliers."
    elif payload.local_sourcing_percentage > 0:
        local_summary = (
            "A portion of this order was locally sourced, partially reducing transport emissions."
        )
    else:
        local_summary = "This order did not use local sourcing, but still reduces plastic waste."

    human_readable_statement = (
        f"By replacing {payload.plastic_items_replaced} plastic items, this order avoids "
        f"approximately {estimated_plastic_saved_kg:.2f} kg of plastic and "
        f"{estimated_carbon_avoided_kg:.2f} kg CO₂e. {local_summary}"
    )

    report = ImpactReport(
        order_id=payload.order_id,
        estimated_plastic_saved_kg=estimated_plastic_saved_kg,
        estimated_carbon_avoided_kg=estimated_carbon_avoided_kg,
        local_sourcing_impact_summary=local_summary,
        human_readable_statement=human_readable_statement,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return ImpactReportOutput(
        order_id=report.order_id,
        estimated_plastic_saved_kg=report.estimated_plastic_saved_kg,
        estimated_carbon_avoided_kg=report.estimated_carbon_avoided_kg,
        local_sourcing_impact_summary=report.local_sourcing_impact_summary,
        human_readable_statement=report.human_readable_statement,
    )

