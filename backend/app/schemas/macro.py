from pydantic import BaseModel


class MacroFactorExposure(BaseModel):
    factor: str
    label: str
    current_z: float
    sensitivity: float
    impact_score: float
    direction: str


class MacroImpactSummary(BaseModel):
    regime_label: str
    signal: str
    score: float
    tailwind_factor: str | None = None
    headwind_factor: str | None = None
    exposures: list[MacroFactorExposure]
