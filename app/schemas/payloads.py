from typing import Optional
from pydantic import BaseModel, ConfigDict

# (Lignes modifiées précédemment)
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
    """
    event: str
    vacancy: AtsVacancy
    model_config = ConfigDict(extra='allow')


# --- Nouveaux modèles pour le Sourcing (Flux 2) ---

class SourcingMatchData(BaseModel):
    job_id: str
    match_id: str
    model_config = ConfigDict(extra='allow')

class SourcingMatchCompletedPayload(BaseModel):
    """
    Validation du payload venant de Jemmo lors du déclenchement du webhook de complétion de match.
    """
    event: str # devrait être "match.completed" ou similaire
    data: SourcingMatchData
    timestamp: Optional[str] = None
    model_config = ConfigDict(extra='allow')
