from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class HealthDomainData(BaseModel):
    condition: Optional[str] = None
    body_system: Optional[str] = None
    evidence_level: Optional[str] = "anecdotal"  # clinical_trial, systematic_review, anecdotal, traditional

class HairDomainData(BaseModel):
    problem_type: Optional[str] = None
    method_name: Optional[str] = None
    active_ingredients: List[str] = []

class DietDomainData(BaseModel):
    diet_type: Optional[str] = None
    goal: Optional[str] = None
    macros_info: Optional[str] = None

class GardenDomainData(BaseModel):
    plant_type: Optional[str] = None
    season: Optional[str] = None
    climate_zone: Optional[str] = None

class ForagingDomainData(BaseModel):
    season: Optional[str] = None
    region: Optional[str] = None
    risk_assessment: str = "medium"
    usable_parts: List[str] = []

class MentalDomainData(BaseModel):
    practice_type: Optional[str] = None  # meditation, journaling, therapy, breathing
    emotional_state: Optional[str] = None  # stress_relief, focus, calm, mood_boost
    cognitive_technique: Optional[str] = None

class FinancialDomainData(BaseModel):
    asset_class: Optional[str] = None  # stocks, real_estate, savings, crypto, general
    financial_goal: Optional[str] = None  # passive_income, emergency_fund, retirement, budget
    risk_profile: Optional[str] = "medium"  # low, medium, high

DOMAIN_SCHEMAS: Dict[str, Any] = {
    "health": HealthDomainData,
    "hair": HairDomainData,
    "diet": DietDomainData,
    "garden": GardenDomainData,
    "foraging": ForagingDomainData,
    "culinary": CulinaryDomainData,
    "mental": MentalDomainData,
    "financial": FinancialDomainData,
}

