"""Ingest medical documents into the ChromaDB vector store."""

import hashlib
import os

from app.rag.embeddings import get_collection


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start += chunk_size - overlap
    return chunks


def ingest_text(text: str, source: str = "manual") -> int:
    """Ingest a text document into the vector store. Returns number of chunks added."""
    collection = get_collection()
    chunks = chunk_text(text)

    ids = []
    documents = []
    metadatas = []
    for chunk in chunks:
        doc_id = hashlib.md5(chunk.encode()).hexdigest()
        ids.append(doc_id)
        documents.append(chunk)
        metadatas.append({"source": source})

    if documents:
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    return len(documents)


def ingest_directory(directory: str) -> int:
    """Ingest all .txt files from a directory. Returns total chunks added."""
    total = 0
    if not os.path.isdir(directory):
        return 0
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            filepath = os.path.join(directory, filename)
            with open(filepath) as f:
                text = f.read()
            if text.strip():
                total += ingest_text(text, source=filename)
    return total


# Seed medical knowledge that gets ingested on first run
SEED_KNOWLEDGE = [
    {
        "source": "common_symptoms_guide",
        "text": """COMMON SYMPTOM ASSESSMENT GUIDE

HEADACHE:
- Tension headache: bilateral, pressing/tightening, mild-moderate, not aggravated by activity
- Migraine: unilateral, pulsating, moderate-severe, nausea/vomiting, photophobia, phonophobia
- Cluster headache: unilateral orbital/supraorbital, severe, lacrimation, rhinorrhea, 15-180 min
- Red flags: thunderclap onset, worst headache ever, fever with neck stiffness, neurological deficits, post-trauma

FEVER:
- Low grade: 99.1-100.4°F (37.3-38°C) — monitor, hydrate
- Moderate: 100.4-103°F (38-39.4°C) — OTC antipyretics, rest, see doctor if >3 days
- High: >103°F (>39.4°C) — seek medical attention, especially with confusion or stiff neck
- In children: any fever in infant <3 months requires immediate evaluation

CHEST PAIN:
- Cardiac: pressure/squeezing, radiates to arm/jaw, worse with exertion, associated with dyspnea/diaphoresis — EMERGENCY
- Musculoskeletal: sharp, reproducible with palpation, worse with movement
- GERD: burning, worse after meals, worse lying down, relieved by antacids
- Pulmonary embolism: sudden pleuritic pain, dyspnea, tachycardia, risk factors (immobility, surgery, DVT) — EMERGENCY

ABDOMINAL PAIN:
- RUQ: gallbladder (cholecystitis), hepatitis, pneumonia
- Epigastric: peptic ulcer, pancreatitis, GERD, MI
- RLQ: appendicitis (McBurney's point), ovarian pathology
- LLQ: diverticulitis, ovarian pathology
- Diffuse: gastroenteritis, obstruction, mesenteric ischemia
- Red flags: rigid abdomen, rebound tenderness, fever, bloody stool""",
    },
    {
        "source": "drug_interaction_basics",
        "text": """COMMON DRUG INTERACTIONS

NSAIDs (ibuprofen, naproxen):
- Warfarin: increased bleeding risk (MAJOR)
- ACE inhibitors: reduced antihypertensive effect, renal risk
- SSRIs: increased GI bleeding risk
- Lithium: increased lithium levels
- Methotrexate: increased methotrexate toxicity

ACE Inhibitors (lisinopril, enalapril):
- Potassium-sparing diuretics: hyperkalemia risk (MAJOR)
- NSAIDs: reduced effectiveness, renal risk
- Lithium: increased lithium levels

SSRIs (fluoxetine, sertraline):
- MAOIs: serotonin syndrome (MAJOR — contraindicated)
- Tramadol: seizure and serotonin syndrome risk
- Warfarin: increased bleeding risk
- NSAIDs: increased GI bleeding risk
- Triptans: serotonin syndrome risk

Statins (atorvastatin, simvastatin):
- CYP3A4 inhibitors (clarithromycin, grapefruit): increased statin levels, rhabdomyolysis risk
- Gemfibrozil: increased myopathy risk
- Warfarin: may increase INR

Metformin:
- Contrast dye: lactic acidosis risk (hold 48h before/after)
- Alcohol: lactic acidosis risk
- ACE inhibitors: may enhance hypoglycemic effect

Warfarin:
- Highly interactive — check ALL new medications
- Vitamin K foods affect INR
- Many antibiotics alter warfarin metabolism""",
    },
    {
        "source": "when_to_seek_emergency_care",
        "text": """WHEN TO SEEK EMERGENCY CARE

CALL 911 / GO TO ER IMMEDIATELY:
- Chest pain or pressure lasting >5 minutes
- Signs of stroke (FAST): Face drooping, Arm weakness, Speech difficulty, Time to call 911
- Difficulty breathing or shortness of breath at rest
- Severe allergic reaction (anaphylaxis): throat swelling, difficulty breathing, widespread hives
- Uncontrolled bleeding
- Loss of consciousness or fainting
- Seizures (especially first-time or prolonged >5 minutes)
- Severe head injury or trauma
- Sudden severe headache (worst of life)
- Poisoning or overdose
- Suicidal thoughts with plan or intent

SEE A DOCTOR WITHIN 24 HOURS:
- Fever >103°F (39.4°C) or fever lasting >3 days
- Persistent vomiting (unable to keep fluids down >24h)
- Signs of dehydration (dark urine, dizziness, dry mouth)
- Severe pain not responding to OTC medications
- Worsening infection signs (increasing redness, warmth, swelling)
- New rash with fever
- Urinary symptoms with fever or back pain (possible pyelonephritis)

SCHEDULE APPOINTMENT (WITHIN 1-2 WEEKS):
- Persistent cough >2 weeks
- Unexplained weight loss
- Persistent fatigue
- New or changing moles
- Chronic pain not improving with self-care""",
    },
]


def seed_knowledge() -> int:
    """Ingest seed medical knowledge into the vector store."""
    total = 0
    for doc in SEED_KNOWLEDGE:
        total += ingest_text(doc["text"], source=doc["source"])
    return total
