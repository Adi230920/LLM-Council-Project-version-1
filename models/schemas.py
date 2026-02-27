from pydantic import BaseModel, Field
from typing import Annotated, List, Dict, Any, Optional

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
    prompt: str = Field(..., min_length=3, max_length=800)  # Public demo: 800 char cap
    # ✅ Pydantic v2: use Annotated with a max_length constraint on the List
    # Previously Field(None, max_length=4) was silently ignored for list types.
    council_models: Optional[Annotated[List[ModelConfig], Field(max_length=4)]] = None
    chairman_model: Optional[ModelConfig] = None
    temperature: float = Field(0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(512, ge=64, le=512)  # Hard cap: 512 tokens per model
