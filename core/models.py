from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from core.tools.type_utils import safe_float, safe_int

class ProcurementLineItem(BaseModel):
    item_id: str
    name: str
    specification: str = "Standard specification"
    category: str = "General Goods"
    quantity: int = 1
    quoted_unit_price: float = 0.0
    quoted_total_price: float = 0.0

    @field_validator('quantity', mode='before')
    @classmethod
    def validate_quantity(cls, v):
        return safe_int(v, default=1)

    @field_validator('quoted_unit_price', 'quoted_total_price', mode='before')
    @classmethod
    def validate_prices(cls, v):
        return safe_float(v, default=0.0)

class MarketBenchmark(BaseModel):
    item_name: str
    fair_market_unit_price: float = 0.0
    price_source: str
    confidence_score: float = 0.95
    evidence_url: Optional[str] = None
    historical_benchmark_range: Optional[str] = None

    @field_validator('fair_market_unit_price', 'confidence_score', mode='before')
    @classmethod
    def validate_benchmark_floats(cls, v):
        return safe_float(v, default=0.0)

class AgentDebateTurn(BaseModel):
    agent_name: str
    role: str
    avatar: str
    argument: str

class AnomalyFinding(BaseModel):
    item_id: str
    item_name: str
    quantity: int = 1
    quoted_unit_price: float = 0.0
    quoted_total_price: float = 0.0
    fair_market_unit_price: float = 0.0
    fair_market_total_price: float = 0.0
    variance_unit: float = 0.0
    variance_total: float = 0.0
    gouging_percentage: float = 0.0
    risk_level: str  # "NORMAL", "SUSPICIOUS_WARNING", "CRITICAL_RED_FLAG"
    audit_notes: str
    evidence_source: str
    debate_transcript: List[AgentDebateTurn] = Field(default_factory=list)

    @field_validator('quantity', mode='before')
    @classmethod
    def val_finding_quantity(cls, v):
        return safe_int(v, default=1)

    @field_validator(
        'quoted_unit_price', 'quoted_total_price',
        'fair_market_unit_price', 'fair_market_total_price',
        'variance_unit', 'variance_total', 'gouging_percentage',
        mode='before'
    )
    @classmethod
    def val_finding_floats(cls, v):
        return safe_float(v, default=0.0)

class AuditDossier(BaseModel):
    tender_id: str
    title: str
    procuring_entity: str
    submission_date: str
    total_quoted_budget: float = 0.0
    fair_market_estimated_budget: float = 0.0
    potential_taxpayer_loss: float = 0.0
    overall_gouging_index: float = 0.0
    risk_score: int = 0  # 0 to 100
    risk_tier: str = "LOW"  # "LOW", "MODERATE", "SEVERE FRAUD RISK"
    findings: List[AnomalyFinding] = Field(default_factory=list)
    executive_summary: str = ""
    legal_statutory_violations: List[str] = Field(default_factory=list)
    immediate_actions_recommended: List[str] = Field(default_factory=list)

    @field_validator('total_quoted_budget', 'fair_market_estimated_budget', 'potential_taxpayer_loss', 'overall_gouging_index', mode='before')
    @classmethod
    def val_dossier_floats(cls, v):
        return safe_float(v, default=0.0)

    @field_validator('risk_score', mode='before')
    @classmethod
    def val_dossier_ints(cls, v):
        return safe_int(v, default=0)
