from app.models.schemas import AgentResponse, ConsultationResponse, UrgencyLevel
from app.providers.base import ModelProvider

CONSENSUS_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string", "description": "Resumo em linguagem acessível para o paciente"},
        "urgency": {
            "type": "string",
            "enum": ["emergency", "urgent", "routine"],
            "description": "Nível geral de urgência",
        },
        "confidence": {
            "type": "number", "minimum": 0, "maximum": 1,
            "description": "Pontuação geral de confiança",
        },
    },
    "required": ["summary", "urgency", "confidence"],
}


async def build_consensus(
    provider: ModelProvider,
    triage: AgentResponse,
    diagnosis: AgentResponse,
    treatment: AgentResponse,
    drug_interactions: AgentResponse,
    citations: list[str] | None = None,
    literature: AgentResponse | None = None,
    guidelines: AgentResponse | None = None,
) -> ConsultationResponse:
    """Synthesize all agent outputs into a single coherent response."""

    system_prompt = """Você é um mecanismo de consenso médico. Você recebe análises de agentes de IA
médica especializados (triagem, diagnóstico, tratamento, interações medicamentosas e, opcionalmente,
literatura e diretrizes) e deve sintetizá-las em um resumo único e coerente para o paciente.

REGRAS:
- Priorize a segurança: se qualquer agente sinalizar uma emergência, a urgência geral deve ser emergência
- Reconcilie discordâncias entre os agentes registrando-as de forma transparente
- Forneça um resumo claro e amigável para o paciente
- Sempre inclua os itens de ação mais críticos primeiro
- Atribua uma pontuação de confiança geral (média dos agentes, ponderada por relevância)
- Mantenha o resumo conciso, mas completo"""

    user_prompt = f"""Sintetize as seguintes análises dos agentes em um resumo coerente para o paciente.

AVALIAÇÃO DE TRIAGEM (confiança: {triage.confidence}):
{triage.analysis}
Sinais de alerta: {', '.join(triage.red_flags) if triage.red_flags else 'Nenhum'}

DIAGNÓSTICO DIFERENCIAL (confiança: {diagnosis.confidence}):
{diagnosis.analysis}
Sinais de alerta: {', '.join(diagnosis.red_flags) if diagnosis.red_flags else 'Nenhum'}

PLANO DE TRATAMENTO (confiança: {treatment.confidence}):
{treatment.analysis}

INTERAÇÕES MEDICAMENTOSAS (confiança: {drug_interactions.confidence}):
{drug_interactions.analysis}
Sinais de alerta: {', '.join(drug_interactions.red_flags) if drug_interactions.red_flags else 'Nenhum'}"""

    if literature:
        user_prompt += f"""

ANÁLISE DA LITERATURA MÉDICA (confiança: {literature.confidence}):
{literature.analysis}"""

    if guidelines:
        user_prompt += f"""

DIRETRIZES CLÍNICAS (confiança: {guidelines.confidence}):
{guidelines.analysis}"""

    user_prompt += "\n\nUse a ferramenta consensus_summary para retornar sua síntese."

    result = await provider.structured_completion(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        output_schema=CONSENSUS_SCHEMA,
        tool_name="consensus_summary",
    )

    summary = result.get("summary", "")
    urgency = UrgencyLevel(result.get("urgency", "routine"))
    confidence = result.get("confidence", 0.0)

    # Override urgency to emergency if any agent flagged red flags related to emergencies
    all_red_flags = triage.red_flags + diagnosis.red_flags + drug_interactions.red_flags
    if all_red_flags and urgency == UrgencyLevel.ROUTINE:
        urgency = UrgencyLevel.URGENT

    return ConsultationResponse(
        summary=summary,
        urgency=urgency,
        confidence=confidence,
        triage=triage,
        diagnosis=diagnosis,
        treatment=treatment,
        drug_interactions=drug_interactions,
        literature=literature,
        guidelines=guidelines,
        citations=citations or [],
    )
