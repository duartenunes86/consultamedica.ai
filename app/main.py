import asyncio
import json
import logging

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.agents.chat_advisor import get_chat_advice
from app.agents.consensus import build_consensus
from app.agents.diagnosis import DiagnosisAgent
from app.agents.drug_interaction import DrugInteractionAgent
from app.agents.guidelines import GuidelinesAgent
from app.agents.intake import run_intake
from app.agents.literature import LiteratureAgent
from app.agents.treatment import TreatmentAgent
from app.agents.triage import TriageAgent
from app.config import get_settings
from app.medical_apis.openfda import lookup_drug_safety
from app.medical_apis.rxnorm import lookup_drug_info
from app.models.schemas import (
    AddSlotsRequest,
    AvailabilitySlot,
    BookingRequest,
    BookingResponse,
    ChatAdviceRequest,
    ChatRequest,
    ChatResponse,
    ConsultationRequest,
    ConsultationResponse,
    IngestRequest,
    IngestResponse,
    PaymentIntentRequest,
    PaymentIntentResponse,
)
from app.providers.factory import check_ollama_health, get_provider
from app.rag.ingest import seed_knowledge
from app.rag.vector_store import format_rag_context, query_medical_knowledge

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title="Gr8Doctor",
    description="Medical AI backend with multi-agent consensus architecture",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    logger.info("Seeding medical knowledge base...")
    count = seed_knowledge()
    logger.info(f"Seeded {count} chunks into knowledge base.")

    ollama_ok = await check_ollama_health()
    logger.info(f"Ollama available: {ollama_ok}")


@app.get("/health")
async def health():
    ollama_ok = await check_ollama_health()
    return {
        "status": "ok",
        "providers": {
            "anthropic": True,
            "ollama": ollama_ok,
        },
    }


async def _build_context(request: ConsultationRequest) -> tuple[dict, list[str]]:
    """Build shared agent context from request (RAG + drug APIs)."""
    rag_docs = query_medical_knowledge(request.message)
    rag_context, citations = format_rag_context(rag_docs)

    drug_info = ""
    if request.current_medications:
        try:
            rxnorm_data = await lookup_drug_info(request.current_medications)
            fda_data = await lookup_drug_safety(request.current_medications)
            drug_info = json.dumps({"rxnorm": rxnorm_data, "openfda": fda_data}, default=str)
        except Exception as e:
            logger.warning(f"Drug API lookup failed: {e}")
            drug_info = "Falha na consulta ao banco de dados de medicamentos — usando apenas conhecimento da IA."

    context = {
        "medical_history": request.medical_history,
        "current_medications": request.current_medications,
        "rag_context": rag_context,
        "drug_info": drug_info,
    }
    return context, citations


@app.post("/consult", response_model=ConsultationResponse)
async def consult(request: ConsultationRequest):
    """Main consultation endpoint — runs all agents in parallel and returns consensus."""
    settings = get_settings()
    context, citations = await _build_context(request)

    # Create providers and agents
    triage_provider = await get_provider(settings.agent_providers["triage"])
    diagnosis_provider = await get_provider(settings.agent_providers["diagnosis"])
    treatment_provider = await get_provider(settings.agent_providers["treatment"])
    drug_provider = await get_provider(settings.agent_providers["drug_interactions"])
    literature_provider = await get_provider(settings.agent_providers["literature"])
    guidelines_provider = await get_provider(settings.agent_providers["guidelines"])
    consensus_provider = await get_provider(settings.agent_providers["consensus"])

    triage_agent = TriageAgent(triage_provider)
    diagnosis_agent = DiagnosisAgent(diagnosis_provider)
    treatment_agent = TreatmentAgent(treatment_provider)
    drug_agent = DrugInteractionAgent(drug_provider)
    literature_agent = LiteratureAgent(literature_provider)
    guidelines_agent = GuidelinesAgent(guidelines_provider)

    # Run all 6 agents in parallel
    try:
        (
            triage_result,
            diagnosis_result,
            treatment_result,
            drug_result,
            literature_result,
            guidelines_result,
        ) = await asyncio.gather(
            triage_agent.analyze(request.message, context),
            diagnosis_agent.analyze(request.message, context),
            treatment_agent.analyze(request.message, context),
            drug_agent.analyze(request.message, context),
            literature_agent.analyze(request.message, context),
            guidelines_agent.analyze(request.message, context),
        )
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Falha na execução do agente: {e}")

    # Build consensus
    try:
        result = await build_consensus(
            provider=consensus_provider,
            triage=triage_result,
            diagnosis=diagnosis_result,
            treatment=treatment_result,
            drug_interactions=drug_result,
            citations=citations,
            literature=literature_result,
            guidelines=guidelines_result,
        )
    except Exception as e:
        logger.error(f"Consensus failed: {e}")
        raise HTTPException(status_code=500, detail=f"Falha no mecanismo de consenso: {e}")

    return result


@app.post("/consult/stream")
async def consult_stream(request: ConsultationRequest):
    """SSE streaming version — streams agent results as they complete."""

    async def event_stream():
        settings = get_settings()
        context, citations = await _build_context(request)

        # Create providers and agents
        agents = []
        for name, agent_cls in [
            ("triage", TriageAgent),
            ("diagnosis", DiagnosisAgent),
            ("treatment", TreatmentAgent),
            ("drug_interactions", DrugInteractionAgent),
            ("literature", LiteratureAgent),
            ("guidelines", GuidelinesAgent),
        ]:
            provider = await get_provider(settings.agent_providers[name])
            agents.append((name, agent_cls(provider)))

        results = {}

        async def run_agent(name, agent):
            result = await agent.analyze(request.message, context)
            results[name] = result
            return name, result

        tasks = [asyncio.create_task(run_agent(name, agent)) for name, agent in agents]

        for coro in asyncio.as_completed(tasks):
            name, result = await coro
            yield f"data: {json.dumps({'event': 'agent_complete', 'agent': name, 'data': result.model_dump()})}\n\n"

        # Build consensus once all agents are done
        consensus_provider = await get_provider(settings.agent_providers["consensus"])
        consensus = await build_consensus(
            provider=consensus_provider,
            triage=results["triage"],
            diagnosis=results["diagnosis"],
            treatment=results["treatment"],
            drug_interactions=results["drug_interactions"],
            citations=citations,
            literature=results.get("literature"),
            guidelines=results.get("guidelines"),
        )
        yield f"data: {json.dumps({'event': 'consensus', 'data': consensus.model_dump()})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Conversational intake endpoint — asks one question at a time.

    Returns either:
      {"type": "question", "question": "..."}        — show to patient and send again
      {"type": "ready", "patient_summary": "..."}    — intake complete; call /chat/advice next
    """
    if not request.messages:
        raise HTTPException(status_code=422, detail="a lista de mensagens não pode estar vazia")

    settings = get_settings()
    intake_provider = await get_provider(settings.agent_providers["triage"])

    intake_result = await run_intake(
        provider=intake_provider,
        messages=request.messages,
        medical_history=request.medical_history,
        current_medications=request.current_medications,
    )

    action = intake_result.get("action", "ask")

    if action == "ask":
        question = intake_result.get("question", "Poderia me contar mais sobre seus sintomas?")
        return ChatResponse(
            type="question",
            question=question,
            question_type=intake_result.get("question_type", "text"),
            options=intake_result.get("options"),
        )

    # action == "consult" — signal frontend to show "Preparando..." and call /chat/advice
    patient_summary = intake_result.get("patient_summary", "")
    if not patient_summary:
        patient_summary = " ".join(m.content for m in request.messages if m.role == "user")

    return ChatResponse(type="ready", patient_summary=patient_summary)


@app.post("/chat/advice", response_model=ChatResponse)
async def chat_advice(request: ChatAdviceRequest):
    """Generates the final conversational advice from a collected patient summary."""
    settings = get_settings()
    advisor_provider = await get_provider(settings.agent_providers["triage"])
    try:
        result = await get_chat_advice(
            provider=advisor_provider,
            patient_summary=request.patient_summary,
            medical_history=request.medical_history,
            current_medications=request.current_medications,
        )
    except Exception as e:
        logger.error(f"Chat advisor failed: {e}")
        raise HTTPException(status_code=500, detail=f"Falha no assistente médico: {e}")

    return ChatResponse(
        type="consultation",
        advice=result.get("response", ""),
        urgency=result.get("urgency", "routine"),
    )


@app.post("/payment/intent", response_model=PaymentIntentResponse)
async def create_payment_intent(request: PaymentIntentRequest):
    """Create a Stripe PaymentIntent for the consultation fee (R$ 49,99)."""
    from app.services.payment import create_payment_intent
    try:
        result = create_payment_intent(patient_name=request.name, patient_email=request.email)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Payment intent creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Falha ao criar pagamento: {e}")
    return PaymentIntentResponse(**result)


@app.get("/availability", response_model=list[AvailabilitySlot])
async def get_availability():
    """Return available appointment slots (at least 24h in the future, not yet booked)."""
    from app.services.availability import get_available_slots
    return get_available_slots()


@app.get("/availability/slots/all")
async def get_all_slots(api_key: str = Query(default="")):
    """(Doctor/Admin) Return all slots including booked ones."""
    from app.services.availability import get_all_slots as _get_all
    settings = get_settings()
    if settings.admin_api_key and api_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Chave de administração inválida.")
    return _get_all()


@app.post("/availability/slots", response_model=list[AvailabilitySlot])
async def add_availability_slots(request: AddSlotsRequest):
    """(Doctor/Admin) Add available appointment slots."""
    from app.services.availability import add_slots
    settings = get_settings()
    if settings.admin_api_key and request.api_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Chave de administração inválida.")
    try:
        return add_slots(request.datetimes)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Erro ao adicionar horários: {e}")


@app.delete("/availability/slots/{slot_id}", status_code=204)
async def delete_availability_slot(slot_id: str, api_key: str = Query(default="")):
    """(Doctor/Admin) Remove an availability slot."""
    from app.services.availability import delete_slot
    settings = get_settings()
    if settings.admin_api_key and api_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Chave de administração inválida.")
    delete_slot(slot_id)


@app.post("/book-consultation", response_model=BookingResponse)
async def book_consultation(request: BookingRequest):
    """Verify payment, reserve a slot, generate a Jitsi room, and notify doctor + patient."""
    from app.services.availability import book_slot
    from app.services.booking import process_booking
    from app.services.payment import verify_payment

    # Verify Stripe payment before doing anything
    try:
        paid = verify_payment(request.payment_intent_id)
    except Exception as e:
        logger.error(f"Payment verification error: {e}")
        raise HTTPException(status_code=502, detail=f"Erro ao verificar pagamento: {e}")
    if not paid:
        raise HTTPException(status_code=402, detail="Pagamento não foi concluído. Por favor tente novamente.")

    # Reserve the chosen slot (validates 24h rule and availability)
    try:
        slot = book_slot(request.slot_id)
    except ValueError as e:
        # Slot no longer available — refund automatically
        if request.payment_intent_id and request.payment_intent_id != "dev-skip":
            try:
                from app.services.payment import refund_payment
                refund_payment(request.payment_intent_id)
                logger.info("Refund issued for %s (slot unavailable)", request.payment_intent_id)
            except Exception as re:
                logger.error("Refund failed for %s: %s", request.payment_intent_id, re)
        raise HTTPException(status_code=409, detail=f"Horário já não disponível. O pagamento foi reembolsado automaticamente.")

    slot_datetime = slot["datetime"]

    try:
        video_url = process_booking(
            name=request.name,
            email=request.email,
            phone=request.phone,
            urgency=request.urgency,
            advice=request.advice,
            patient_summary=request.patient_summary,
            slot_datetime=slot_datetime,
        )
    except Exception as e:
        logger.error(f"Booking failed: {e}")
        raise HTTPException(status_code=500, detail=f"Falha ao processar pedido de consulta: {e}")

    return BookingResponse(
        status="ok",
        message="Videoconsulta agendada com sucesso.",
        video_url=video_url,
        slot_datetime=slot_datetime,
    )


@app.post("/rag/ingest", response_model=IngestResponse)
async def ingest_document(request: IngestRequest):
    """Ingest a medical document into the knowledge base."""
    from app.rag.ingest import ingest_text

    count = ingest_text(request.text, source=request.source)
    return IngestResponse(status="ok", documents_added=count, source=request.source)


@app.post("/rag/load-dataset")
async def load_dataset_route(
    dataset: str = Query(..., pattern="^(medqa|pubmedqa|all)$"),
    limit: int = Query(default=100, ge=1),
):
    """Download and ingest a HuggingFace medical dataset into the RAG knowledge base."""
    from app.rag.dataset_loader import load_dataset_into_rag

    try:
        results = load_dataset_into_rag(dataset=dataset, limit=limit)
    except Exception as e:
        logger.error(f"Dataset loading failed: {e}")
        raise HTTPException(status_code=500, detail=f"Falha ao carregar dataset: {e}")

    return {"status": "ok", "dataset": dataset, "limit": limit, **results}


@app.post("/evaluate")
async def evaluate_route(config: dict):
    """Run a benchmark evaluation against MedQA or PubMedQA."""
    from app.eval.benchmark import run_benchmark
    from app.eval.schemas import BenchmarkConfig

    try:
        benchmark_config = BenchmarkConfig(**config)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    try:
        result = await run_benchmark(benchmark_config)
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        raise HTTPException(status_code=500, detail=f"Falha no benchmark: {e}")

    return result.model_dump()
