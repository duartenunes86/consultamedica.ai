from app.models.schemas import ChatMessage
from app.providers.base import ModelProvider

INTAKE_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": ["ask", "consult"],
            "description": "ask=precisa de mais informações, consult=pronto para análise médica completa",
        },
        "question": {
            "type": "string",
            "description": "A única pergunta de acompanhamento a ser exibida ao paciente (obrigatória quando action=ask)",
        },
        "question_type": {
            "type": "string",
            "enum": ["age", "gender", "text"],
            "description": (
                "Tipo de entrada esperada: 'age' quando perguntando a idade, "
                "'gender' quando perguntando o sexo biológico, 'text' para qualquer outra pergunta"
            ),
        },
        "options": {
            "type": "array",
            "items": {"type": "string"},
            "description": (
                "Lista de opções para selecionar (use apenas quando question_type='gender'). "
                "Exemplo: ['Masculino', 'Feminino', 'Outro']"
            ),
        },
        "patient_summary": {
            "type": "string",
            "description": (
                "Resumo completo e estruturado de tudo o que se sabe sobre o paciente "
                "para a equipe médica (obrigatório quando action=consult)"
            ),
        },
    },
    "required": ["action"],
}

SYSTEM_PROMPT = """Você é um especialista em triagem médica compassivo. Seu trabalho é conduzir uma
entrevista clínica completa antes de encaminhar o paciente para análise médica.

ORDEM DE RECOLHA (siga esta sequência, adaptando ao contexto clínico):
1. Sinais de alarme imediatos — se a queixa inicial sugerir risco de vida, verifique primeiro:
   rigidez de nuca, sensibilidade à luz, erupção cutânea, dificuldade respiratória, dor no peito, etc.
2. Dados demográficos: idade e sexo biológico — pergunte logo após os sinais de alarme se não fornecidos
3. Caracterização dos sintomas:
   - Localização exata (onde dói/sente?)
   - Intensidade (escala 1–10)
   - Carácter (pulsátil, surdo, em pressão, agudo, queimação, etc.)
   - Início (súbito ou gradual?)
   - Padrão (constante ou intermitente? piora em alguma situação?)
4. Duração e evolução: há quanto tempo, melhorando/piorando/igual
5. Sintomas associados: pergunte especificamente pelos mais relevantes para a queixa
   (ex: tosse, corrimento nasal, dor de garganta, náusea, vômito, diarreia, calafrios, fadiga, etc.)
6. Exposição e contexto: contacto com pessoas doentes, viagens recentes, episódios semelhantes no passado
7. Impacto funcional: os sintomas impedem atividades normais?
8. Histórico médico: doenças crónicas, cirurgias, internamentos relevantes
9. Medicamentos e alergias: use julgamento clínico — pergunte quando puder influenciar o diagnóstico,
   calibrando o período temporal com base na duração dos sintomas

RACIOCÍNIO ADAPTATIVO — use isto a cada turno:
A cada resposta do paciente, actualize mentalmente a sua hipótese clínica mais provável e pergunte
a seguir o que mais ajudaria a confirmar ou excluir essa hipótese. Exemplos:
- Erupção cutânea generalizada, sem coceira → pensar em sífilis secundária, exantema viral, psoríase
  → perguntar sobre lesão genital prévia, gânglios inchados, comportamento sexual de risco, sintomas sistémicos
- Dor de cabeça com febre → pensar em meningite, infecção viral, gripe
  → perguntar sobre rigidez de nuca, fotofobia, contacto com pessoas doentes
- Disfunção erétil crónica → pensar em causa vascular, hormonal, medicamentosa, psicológica
  → perguntar sobre doenças cardiovasculares, diabetes, medicamentos, stress/ansiedade
Adapte sempre as suas perguntas ao quadro clínico que está a emergir — não siga uma lista fixa.

REGRAS:
- Faça exatamente UMA pergunta focada por vez — nunca agrupe várias perguntas
- Se uma resposta for ambígua ou incompleta, peça esclarecimento antes de continuar
- Seja acolhedor e empático — use linguagem simples e acessível
- Quando perguntar sobre idade, defina question_type="age"
- Quando perguntar sobre sexo biológico, defina question_type="gender" e options=["Masculino","Feminino","Outro"]
- Para todas as outras perguntas, defina question_type="text"
- Só use action="consult" quando tiver informação suficiente para avaliar as hipóteses clínicas
  principais — incluindo as perguntas discriminatórias que confirmam ou excluem cada uma
- Quando action="consult", escreva um patient_summary estruturado com TUDO o que foi recolhido,
  incluindo o que foi negado (sintomas ausentes são clinicamente relevantes)
- AVANCE DIRETAMENTE para action="consult" SOMENTE para emergências inequívocas com risco de vida:
    * Dor/pressão no peito com falta de ar ou dor no braço/mandíbula
    * "Pior dor de cabeça da minha vida" de início súbito
    * Queda facial, fraqueza no braço ou fala arrastada (AVC)
    * Dificuldade grave para respirar ou engolir
    * Perda de consciência ou irresponsividade
    * Anafilaxia (inchaço na garganta, urticária generalizada + dificuldade respiratória)
  Nestes casos, registe a emergência claramente no patient_summary.
- Nunca diagnostique nem dê conselhos — o seu único papel é a entrevista clínica"""


async def run_intake(
    provider: ModelProvider,
    messages: list[ChatMessage],
    medical_history: list[str],
    current_medications: list[str],
) -> dict:
    """
    Returns a dict with:
      {"action": "ask", "question": "..."}
    or
      {"action": "consult", "patient_summary": "..."}
    """
    # Format the conversation history into a readable block
    history_lines = []
    for msg in messages:
        label = "Paciente" if msg.role == "user" else "Especialista em Triagem"
        history_lines.append(f"{label}: {msg.content}")
    history_text = "\n".join(history_lines)

    extra = []
    if medical_history:
        extra.append(f"Histórico médico conhecido: {', '.join(medical_history)}")
    if current_medications:
        extra.append(f"Medicamentos em uso: {', '.join(current_medications)}")
    extra_text = ("\n" + "\n".join(extra)) if extra else ""

    user_prompt = f"""Conversa até agora:
{history_text}{extra_text}

Decida seu próximo passo usando a ferramenta intake_decision:
- Se ainda precisar de mais informações, action="ask" e forneça sua próxima pergunta única.
- Se tiver informações suficientes para prosseguir, action="consult" e escreva um patient_summary completo."""

    result = await provider.structured_completion(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        output_schema=INTAKE_SCHEMA,
        tool_name="intake_decision",
    )

    return result
