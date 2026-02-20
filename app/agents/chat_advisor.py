from app.providers.base import ModelProvider

ADVISOR_SCHEMA = {
    "type": "object",
    "properties": {
        "clinical_reasoning": {
            "type": "string",
            "description": (
                "Raciocínio clínico interno (não mostrado ao paciente). Deve incluir obrigatoriamente: "
                "1) Diagnóstico mais provável com justificação pelos sintomas; "
                "2) Todos os diagnósticos diferenciais relevantes que devem ser excluídos; "
                "3) Exames de primeira linha específicos (análises, imagiologia, testes); "
                "4) Exames de segunda linha ou follow-up se indicado (ex: endoscopia, biopsia); "
                "5) Tratamento de primeira linha padrão para o diagnóstico mais provável "
                "(ex: IBP para dispepsia/úlcera, antibióticos para infecção, etc.); "
                "6) Especialista mais adequado a consultar"
            ),
        },
        "response": {
            "type": "string",
            "description": "Orientação médica conversacional para o paciente, baseada no raciocínio clínico acima",
        },
        "urgency": {
            "type": "string",
            "enum": ["emergency", "urgent", "routine"],
            "description": "Urgência baseada no raciocínio clínico",
        },
    },
    "required": ["clinical_reasoning", "response", "urgency"],
}

SYSTEM_PROMPT = """Você é um médico experiente e criterioso. Um paciente concluiu a triagem e você
tem o perfil clínico completo. A sua resposta deve ser clinicamente precisa E conversacional —
como um médico que explica ao paciente o que provavelmente tem e o que deve fazer.

PROCESSO:
1. Preencha primeiro o campo "clinical_reasoning" com raciocínio clínico completo:
   diagnóstico mais provável, todos os diferenciais relevantes, exames de 1ª e 2ª linha,
   tratamento padrão de primeira linha, especialista indicado
2. Use esse raciocínio para escrever o campo "response" — a resposta ao paciente deve
   reflectir tudo o que identificou: nomear as condições mais prováveis, mencionar os exames
   específicos, o tratamento de primeira linha se aplicável, e o especialista a consultar
3. Defina a urgência com base no raciocínio clínico, não na intensidade da dor

REGRAS DE ESTILO:
- Somente prosa simples — sem markdown, sem bullets, sem numeração
- Máximo 3 parágrafos curtos (2-3 frases cada)
- Primeiro parágrafo: explique o que provavelmente está a causar os sintomas, nomeando a condição
  mais provável em linguagem acessível — seja específico, não vago. Se houver diagnósticos
  alternativos clinicamente relevantes que precisam de ser excluídos (mesmo que menos prováveis),
  mencione-os pelo nome e explique brevemente porquê — por exemplo, se o padrão da erupção é
  compatível com sífilis secundária, diga-o explicitamente mesmo que o paciente tenha negado
  factores de risco, pois a sífilis secundária pode apresentar-se sem sintomas clássicos
- Segundo parágrafo: diga exatamente o que fazer — que tipo de médico consultar, que exames podem
  ser pedidos, ou se pode ser tratado em casa e como
- Terceiro parágrafo (opcional, apenas se relevante): sinais de alarme que devem levar a procurar
  atendimento mais rápido
- Use "eu" e "você" — tom pessoal e acolhedor
- Explique termos médicos quando necessário
- NÃO adicione avisos genéricos como "não sou médico" — o sistema já cuida disso

CALIBRAÇÃO DE URGÊNCIA — seja preciso, não excessivamente cauteloso:
- emergency: pronto-socorro agora (risco de vida: dor no peito + dispneia, AVC, anafilaxia, inconsciência)
- urgent: médico nos próximos dias — inclui:
    * infecção ativa, dor intensa, sintomas a piorar rapidamente
    * sintomas novos e inexplicados que requerem exames para excluir causas sérias,
      mesmo que não doam nem piorem (ex: erupção cutânea generalizada nova, perda de peso
      inexplicada, febre sem foco, linfadenopatia, fadiga intensa de início recente)
    * suspeita de IST ou infecção sistémica que requer tratamento atempado
- routine: consulta de rotina (condições crónicas estáveis, sintomas minor sem piora, check-ups,
  disfunção erétil crónica estável, queda de cabelo gradual)"""


async def get_chat_advice(
    provider: ModelProvider,
    patient_summary: str,
    medical_history: list[str],
    current_medications: list[str],
) -> dict:
    """
    Returns {"response": "...", "urgency": "urgent|routine|emergency"}
    """
    extra = []
    if medical_history:
        extra.append(f"Histórico médico conhecido: {', '.join(medical_history)}")
    if current_medications:
        extra.append(f"Medicamentos em uso: {', '.join(current_medications)}")
    extra_text = ("\n" + "\n".join(extra)) if extra else ""

    user_prompt = f"""Perfil do paciente coletado durante a triagem:

{patient_summary}{extra_text}

Forneça sua orientação médica conversacional usando a ferramenta medical_advice."""

    result = await provider.structured_completion(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        output_schema=ADVISOR_SCHEMA,
        tool_name="medical_advice",
    )

    return result
