from pydantic import BaseModel, Field


class BenchmarkConfig(BaseModel):
    dataset: str = Field(..., pattern="^(medqa|pubmedqa)$", description="Dataset to evaluate on")
    num_questions: int = Field(default=20, ge=1, le=500, description="Number of questions to evaluate")
    seed: int = Field(default=42, description="Random seed for reproducibility")


class QuestionResult(BaseModel):
    question: str
    ground_truth: str
    system_answer: str
    is_correct: bool
    judge_reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)
    urgency: str


class BenchmarkResult(BaseModel):
    dataset: str
    num_questions: int
    accuracy: float = Field(ge=0.0, le=1.0)
    avg_confidence: float = Field(ge=0.0, le=1.0)
    avg_correct_confidence: float = Field(ge=0.0, le=1.0)
    avg_incorrect_confidence: float = Field(ge=0.0, le=1.0)
    false_emergency_rate: float = Field(ge=0.0, le=1.0)
    results: list[QuestionResult]
