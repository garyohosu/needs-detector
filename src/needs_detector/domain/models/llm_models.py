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

class InterviewAnalysisResponse(BaseModel):
    refutations: List[Refutation]
