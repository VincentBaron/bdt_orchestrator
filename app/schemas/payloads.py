from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict

class AtsVacancy(BaseModel):
    id: int
    slug: Optional[str] = None
    company_id: Optional[str] = None
    title: Optional[str] = None
    reference: Optional[str] = None
    status: Optional[int] = None
    model_config = ConfigDict(extra='allow')

class AtsJobCreatedPayload(BaseModel):
    """
    Validation du payload pour la création d'une offre (job-created) via Flatchr.
    On type de manière stricte ce dont on a besoin (`vacancy.id`, `vacancy.slug`)
    et on autorise le reste.
    """
    event: str
    vacancy: AtsVacancy
    model_config = ConfigDict(extra='allow')
