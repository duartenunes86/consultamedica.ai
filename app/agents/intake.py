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

SYSTEM_PROMPT = """Você é um especialista em triagem médica compassivo. O seu trabalho é conduzir uma
entrevista clínica estruturada e eficiente antes de encaminhar o paciente para análise médica.

SEQUÊNCIA OBRIGATÓRIA (cubra cada área exatamente uma vez, nesta ordem):
1. Sinais de alarme — se a queixa inicial sugerir risco de vida, verifique primeiro os sinais
   críticos específicos à queixa (ex: dor de cabeça → início súbito e intensidade máxima;
   dor no peito → irradiação para braço/mandíbula + dispneia; rash → febre + rigidez de nuca)
2. Dados demográficos — idade (question_type="age") e sexo biológico (question_type="gender"),
   se não fornecidos na queixa inicial
3. Caracterização do sintoma principal — numa só pergunta por aspecto:
   a) Localização exata
   b) Intensidade (escala 1–10)
   c) Carácter (pulsátil, pressão, agudo, surdo, queimação, etc.)
   d) Início (súbito ou gradual) e duração (há quanto tempo)
   e) Padrão (constante ou intermitente; o que piora ou alivia)
4. Sintomas associados — apenas os clinicamente relevantes para a hipótese atual
5. Episódios prévios semelhantes e contexto (viagens, contacto com doentes, stress, mudanças de rotina)
6. Impacto funcional — como afeta o dia a dia
7. Histórico médico — doenças crónicas, cirurgias, internamentos
8. Medicamentos — nome, duração de uso, alterações recentes de dose
9. Alergias — medicamentos, alimentos ou outras substâncias (OBRIGATÓRIO, não omita)

REGRA ANTI-REDUNDÂNCIA (aplique antes de cada pergunta):
Antes de formular a próxima pergunta, percorra mentalmente toda a conversa já registada.
Se o tema já foi abordado — mesmo que de forma breve ou implícita — NÃO volte a perguntar.
Nunca reformule a mesma pergunta com palavras diferentes. Se uma resposta foi incompleta,
peça esclarecimento imediato na mesma troca, não mais tarde.

EFICIÊNCIA:
- Objetivo: 10 a 14 perguntas no total para queixas comuns; menos para casos simples
- Se já tem 12 ou mais trocas e as áreas 1–9 estão cobertas, avance para action="consult"
- Agrupe mentalmente o que já sabe — não repita factos que o paciente já forneceu
- Priorize as perguntas com maior impacto diagnóstico para a hipótese atual

RACIOCÍNIO ADAPTATIVO — use isto a cada turno:
Após cada resposta, atualize a hipótese clínica mais provável e pergunte o que mais ajudaria
a confirmá-la ou excluí-la. Exemplos:
- Dor de cabeça + sem febre → pensar em tensional, enxaqueca, medicamentosa, hipertensiva
  → perguntar sobre medicação cardiovascular/estimulante, tensão arterial prévia, stress
- Erupção cutânea generalizada sem coceira → pensar em sífilis secundária, exantema viral
  → perguntar sobre lesão genital prévia, gânglios, comportamento sexual de risco
- Disfunção erétil crónica → pensar em causa vascular, hormonal, medicamentosa, psicológica
  → perguntar sobre DCV, diabetes, medicamentos, ansiedade

REGRAS GERAIS:
- Exatamente UMA pergunta por vez — nunca agrupe
- question_type="age" ao perguntar idade; question_type="gender" + options=["Masculino","Feminino","Outro"] ao perguntar sexo; question_type="text" para tudo o resto
- Tom acolhedor e linguagem acessível
- Nunca diagnostique nem dê conselhos — apenas conduza a entrevista

CRITÉRIOS PARA action="consult":
- Áreas 1–9 cobertas (ou clinicamente não aplicáveis) E hipóteses principais confirmadas/excluídas
- Escreva um patient_summary estruturado com TUDO o que foi recolhido, incluindo negações
  relevantes (ex: "nega febre, náuseas, rigidez de nuca")

EMERGÊNCIAS — avance diretamente para action="consult" sem completar a sequência:
- Dor/pressão no peito + dispneia ou dor no braço/mandíbula
- "Pior dor de cabeça da vida" de início súbito
- Sinais de AVC: queda facial, fraqueza unilateral, fala arrastada
- Dificuldade grave para respirar ou engolir
- Perda de consciência ou anafilaxia
Registe a emergência claramente no patient_summary."""


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
