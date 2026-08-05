from enum import Enum
from pydantic import BaseModel
from typing import Optional

class EvidenceType(Enum):
    EVIDENCE = "evidence"
    QUOTE = "quote"
    HYPOTHESIS = "hypothesis"
    INFERENCE = "inference"
    UNKNOWN = "unknown"

class Statement(BaseModel):
    text: str
    evidence_type: EvidenceType
    source_id: Optional[str] = None
    line_reference: Optional[str] = None
