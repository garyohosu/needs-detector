from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional

class Jobs(BaseModel):
    functional: str
    emotional: str
    social: str

class Persona(BaseModel):
    id: str
    name: str
    situation: str
    jobs: Jobs
    impediments: str
    current_coping: str
    dissatisfaction: str
    evidence_type: str
    source_reference: str
    questions_to_verify: List[str]

class DrawResponse(BaseModel):
    personas: List[Persona]

class Alternative(BaseModel):
    name: str
    benefits: str
    problems: str
    cost_time: str

class ExploreResponse(BaseModel):
    direct_competition: List[Alternative]
    indirect_alternatives: List[Alternative]
    non_consumption: List[Alternative]

class InterviewGuideResponse(BaseModel):
    core_questions: List[str]
    deep_dive_questions: List[str]

class CPFEvidence(BaseModel):
    evidence_type: Literal['evidence', 'quote', 'hypothesis', 'inference', 'unknown']
    content: str
    source_ref: Optional[str] = None

class Refutation(BaseModel):
    quote: str
    line: int
    source: str
    evidence: Optional[CPFEvidence] = None

class CPFRealProblem(BaseModel):
    concrete_events: List[str] = Field(default_factory=list)
    frequency: List[str] = Field(default_factory=list)
    impact: List[str] = Field(default_factory=list)

class CPFFirstMover(BaseModel):
    time_spent: List[str] = Field(default_factory=list)
    money_spent: List[str] = Field(default_factory=list)
    attempts: List[str] = Field(default_factory=list)

class CPFCurrentAlternative(BaseModel):
    alternatives_used: List[str] = Field(default_factory=list)
    dissatisfaction: List[str] = Field(default_factory=list)
    continued_use_reason: List[str] = Field(default_factory=list)

class CPFEvidenceStructure(BaseModel):
    real_problem: CPFRealProblem = Field(default_factory=CPFRealProblem)
    first_mover: CPFFirstMover = Field(default_factory=CPFFirstMover)
    current_alternative: CPFCurrentAlternative = Field(default_factory=CPFCurrentAlternative)

class InterviewAnalysisResponse(BaseModel):
    refutations: List[Refutation]
    cpf_evidence: Optional[CPFEvidenceStructure] = None
