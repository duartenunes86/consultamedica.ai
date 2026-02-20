# Gr8Doctor - Medical AI Backend

A medical AI backend using FastAPI and Claude API with a multi-agent consensus architecture and RAG pipeline over medical knowledge.

## Architecture

Four specialized AI agents run in parallel and their outputs are synthesized by a consensus engine:

- **Triage Agent** — Emergency/red flag detection, urgency assessment
- **Diagnosis Agent** — Differential diagnosis with probabilities
- **Treatment Agent** — Treatment plans and lifestyle recommendations
- **Drug Interaction Agent** — Medication safety checks via RxNorm/OpenFDA

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run the server
uvicorn app.main:app --reload
```

## API Endpoints

### `POST /consult`
Main consultation endpoint. Runs all agents in parallel and returns a consensus response.

```bash
curl -X POST http://localhost:8000/consult \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I have a headache and fever for 2 days",
    "medical_history": ["hypertension"],
    "current_medications": ["lisinopril"]
  }'
```

### `POST /consult/stream`
SSE streaming version — streams agent results as they complete.

```bash
curl -N http://localhost:8000/consult/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "I have chest pain and shortness of breath"}'
```

### `POST /rag/ingest`
Add medical documents to the knowledge base.

```bash
curl -X POST http://localhost:8000/rag/ingest \
  -H "Content-Type: application/json" \
  -d '{"text": "Medical guideline content here...", "source": "guidelines_2024"}'
```

### `GET /health`
Health check.

```bash
curl http://localhost:8000/health
```

## Adding Medical Knowledge

Place `.txt` files in `data/medical_knowledge/` and they will be ingested on startup. The system comes pre-seeded with basic symptom guides, drug interaction references, and emergency care guidelines.

## Disclaimer

This is an AI-generated medical analysis tool for educational and research purposes. It is NOT a substitute for professional medical advice, diagnosis, or treatment.
