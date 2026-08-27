from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ActionType(str, Enum):
    NAVIGATE = "navigate"
    FILL = "fill"
    CLICK = "click"
    SELECT = "select"
    WAIT_FOR_ELEMENT = "wait_for_element"
    EXTRACT = "extract"

class OutcomeCategory(str, Enum):
    SUCCESS = "SUCCESS"
    BUSINESS_OUTCOME = "BUSINESS_OUTCOME"
    RECOVERABLE_ERROR = "RECOVERABLE_ERROR"
    HARD_FAILURE = "HARD_FAILURE"
    HUMAN_INTERVENTION_REQUIRED = "HUMAN_INTERVENTION_REQUIRED"

class MultiTierLocator(BaseModel):
    role: Optional[str] = None
    accessible_name: Optional[str] = None
    text_content: Optional[str] = None
    css_fallback: Optional[str] = None
    xpath_fallback: Optional[str] = None

class StepDefinition(BaseModel):
    step_id: int
    action: ActionType
    target: Optional[MultiTierLocator] = None
    param_binding: Optional[str] = None
    static_value: Optional[str] = None
    extract_key: Optional[str] = None
    is_irreversible: bool = False
    description: Optional[str] = None

class BusinessOutcomeBranch(BaseModel):
    condition_locator: MultiTierLocator
    outcome_code: str
    message: str

class CapabilityArtifact(BaseModel):
    schema_version: str = "1.0.0"
    capability_name: str
    description: str
    target_origin: str
    input_schema: Dict[str, str]
    output_schema: Dict[str, str]
    steps: List[StepDefinition]
    business_branches: List[BusinessOutcomeBranch] = Field(default_factory=list)
    success_checkpoint: MultiTierLocator

class ExecutionResult(BaseModel):
    status: OutcomeCategory
    outcome_code: Optional[str] = None
    message: Optional[str] = None
    outputs: Dict[str, Any] = Field(default_factory=dict)
    failed_step_id: Optional[int] = None
    evidence_path: Optional[str] = None