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
    type: str = Field(..., description="'question' | 'ready' | 'consultation'")
    question: str | None = Field(None, description="Next question to show the patient")
    question_type: str | None = Field(None, description="'age' | 'gender' | 'text' — hint for UI rendering")
    options: list[str] | None = Field(None, description="Selectable options (e.g. for gender question)")
    patient_summary: str | None = Field(None, description="Collected summary (set when type='ready')")
    advice: str | None = Field(None, description="Conversational medical advice")
    urgency: str | None = Field(None, description="emergency | urgent | routine")
    consultation: ConsultationResponse | None = Field(None, description="Full result (only from /consult)")


class ChatAdviceRequest(BaseModel):
    patient_summary: str
    medical_history: list[str] = Field(default_factory=list)
    current_medications: list[str] = Field(default_factory=list)


class IngestRequest(BaseModel):
    text: str = Field(..., description="Medical text content to ingest")
    source: str = Field(default="manual", description="Source of the document")


class IngestResponse(BaseModel):
    status: str
    documents_added: int
    source: str


class AvailabilitySlot(BaseModel):
    id: str
    datetime: str = Field(..., description="ISO 8601 datetime string")
    booked: bool = False


class AddSlotsRequest(BaseModel):
    datetimes: list[str] = Field(..., description="List of ISO 8601 datetime strings to add")
    api_key: str = Field(default="", description="Admin API key")


class PaymentIntentRequest(BaseModel):
    name: str = Field(..., description="Patient name (for Stripe metadata)")
    email: str = Field(..., description="Patient email (for Stripe receipt)")


class PaymentIntentResponse(BaseModel):
    client_secret: str
    payment_intent_id: str
    amount_brl: str = "49,99"


class BookingRequest(BaseModel):
    name: str = Field(..., description="Patient full name")
    email: str = Field(..., description="Patient email")
    phone: str = Field(..., description="Patient phone number")
    urgency: str = Field(..., description="emergency | urgent | routine")
    advice: str = Field(..., description="AI-generated medical advice")
    patient_summary: str = Field(..., description="Full symptom profile collected during intake")
    slot_id: str = Field(..., description="ID of the chosen availability slot")
    payment_intent_id: str = Field(..., description="Stripe PaymentIntent ID to verify payment")


class BookingResponse(BaseModel):
    status: str
    message: str
    video_url: str
    slot_datetime: str = Field(..., description="Confirmed appointment datetime (ISO 8601)")
