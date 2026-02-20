from pydantic import BaseModel, Field
from enum import Enum


class UrgencyLevel(str, Enum):
    EMERGENCY = "emergency"
    URGENT = "urgent"
    ROUTINE = "routine"


class ConsultationRequest(BaseModel):
    message: str = Field(..., description="Patient symptom description")
    medical_history: list[str] = Field(default_factory=list, description="Past medical conditions")
    current_medications: list[str] = Field(default_factory=list, description="Current medications")


class AgentResponse(BaseModel):
    agent_name: str
    analysis: str
    confidence: float = Field(ge=0.0, le=1.0)
    red_flags: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class ConsultationResponse(BaseModel):
    summary: str
    urgency: UrgencyLevel
    confidence: float = Field(ge=0.0, le=1.0)
    triage: AgentResponse
    diagnosis: AgentResponse
    treatment: AgentResponse
    drug_interactions: AgentResponse
    literature: AgentResponse | None = None
    guidelines: AgentResponse | None = None
    citations: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "Esta é uma análise médica gerada por IA e NÃO substitui o aconselhamento "
        "médico profissional, diagnóstico ou tratamento. Sempre busque a orientação "
        "de um profissional de saúde qualificado."
    )


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., description="Full conversation history so far")
    medical_history: list[str] = Field(default_factory=list)
    current_medications: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    type: str = Field(..., description="'question' or 'consultation'")
    question: str | None = Field(None, description="Next question to show the patient")
    question_type: str | None = Field(None, description="'age' | 'gender' | 'text' — hint for UI rendering")
    options: list[str] | None = Field(None, description="Selectable options (e.g. for gender question)")
    advice: str | None = Field(None, description="Conversational medical advice")
    urgency: str | None = Field(None, description="emergency | urgent | routine")
    consultation: ConsultationResponse | None = Field(None, description="Full result (only from /consult)")


class IngestRequest(BaseModel):
    text: str = Field(..., description="Medical text content to ingest")
    source: str = Field(default="manual", description="Source of the document")


class IngestResponse(BaseModel):
    status: str
    documents_added: int
    source: str
