from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ModelConfig(BaseModel):
    provider: str  # "openrouter" or "groq"
    model: str

class Stage1Opinion(BaseModel):
    model_id: str
    provider: str
    short_name: str
    response: str
    succeeded: bool
    response_id: int

class RankingItem(BaseModel):
    response_id: int
    score_total: float

class DetailedScore(BaseModel):
    response_id: int
    accuracy: int = Field(ge=0, le=10)
    insight: int = Field(ge=0, le=10)
    logic: int = Field(ge=0, le=10)
    critique: str

class Stage2Review(BaseModel):
    reviewer_model_id: str
    reviewer_provider: str
    rankings: List[RankingItem]
    detailed_scores: List[DetailedScore]
    succeeded: bool = True

class DeliberationTrace(BaseModel):
    original_prompt: str
    stage1_opinions: List[Stage1Opinion]
    stage2_reviews: List[Stage2Review]
    verdict: str
    meta: Dict[str, Any]

class ConsultRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=4096)
    council_models: Optional[List[ModelConfig]] = None
    chairman_model: Optional[ModelConfig] = None
    temperature: float = 0.7
    max_tokens: int = 1024
