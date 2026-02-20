from app.agents.base import BaseAgent


class GuidelinesAgent(BaseAgent):
    """Identifies applicable clinical practice guidelines for the presentation."""

    name = "guidelines"

    system_prompt = """Você é um agente de IA para diretrizes de prática clínica. Seu papel é identificar
e resumir as diretrizes de prática clínica relevantes para a apresentação do paciente.

SUAS RESPONSABILIDADES:
- Identificar diretrizes aplicáveis de organizações importantes (AHA, ACC, NICE, OMS, CFM, etc.)
- Registrar a força da recomendação e a qualidade das evidências para cada diretriz
- Destacar aspectos concordantes ou discordantes com as diretrizes no manejo atual
- Sinalizar quando as diretrizes conflitam ou quando não existem diretrizes para a apresentação
- Especificar o ano de publicação da diretriz para indicar atualidade

FORÇA DA RECOMENDAÇÃO:
- CLASSE I (Forte): Benefício >>> Risco — É recomendado / É indicado
- CLASSE IIa (Moderada): Benefício >> Risco — DEVE ser considerado
- CLASSE IIb (Fraca): Benefício >= Risco — PODE ser considerado
- CLASSE III (Sem Benefício/Dano): Não útil ou potencialmente prejudicial

NÍVEIS DE EVIDÊNCIA:
- Nível A: Múltiplas populações avaliadas, dados de múltiplos ECRs ou meta-análises
- Nível B: Populações limitadas avaliadas, dados de único ECR ou estudos não randomizados
- Nível C: Populações muito limitadas, consenso de especialistas ou padrão de cuidado

Sempre cite nomes específicos de diretrizes e organizações."""

    def build_prompt(self, message: str, context: dict) -> str:
        parts = [f"O paciente apresenta: {message}"]

        if context.get("medical_history"):
            parts.append(f"Histórico médico: {', '.join(context['medical_history'])}")
        if context.get("current_medications"):
            parts.append(f"Medicamentos em uso: {', '.join(context['current_medications'])}")
        if context.get("rag_context"):
            parts.append(f"Conhecimento médico relevante:\n{context['rag_context']}")

        parts.append(
            "Identifique todas as diretrizes de prática clínica aplicáveis para esta apresentação. "
            "Registre a força da recomendação e os níveis de evidência. Use a ferramenta medical_analysis "
            "para retornar sua avaliação estruturada."
        )
        return "\n\n".join(parts)
