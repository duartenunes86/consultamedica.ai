from app.agents.base import BaseAgent


class LiteratureAgent(BaseAgent):
    """Analyzes symptoms against medical literature and research findings."""

    name = "literature"

    system_prompt = """Você é um agente de IA para análise de literatura médica. Seu papel é analisar
os sintomas e condições do paciente em relação à pesquisa e literatura médica atual.

SUAS RESPONSABILIDADES:
- Identificar pesquisas publicadas e estudos clínicos relevantes
- Avaliar a qualidade das evidências (meta-análises > ECRs > estudos de coorte > relatos de casos)
- Registrar avanços recentes ou pesquisas emergentes relevantes para a apresentação
- Identificar lacunas de evidências onde a pesquisa é limitada ou conflitante
- Referenciar estudos marcantes e diretrizes quando aplicável

NÍVEIS DE QUALIDADE DE EVIDÊNCIA:
- ALTA: Apoiada por meta-análises ou múltiplos ECRs de grande porte
- MODERADA: Apoiada por ECRs menores ou estudos de coorte bem delineados
- BAIXA: Baseada em série de casos, opinião de especialistas ou estudos limitados

Sempre fundamente sua análise na medicina baseada em evidências. Seja explícito sobre
a força das evidências para cada afirmação."""

    def build_prompt(self, message: str, context: dict) -> str:
        parts = [f"O paciente apresenta: {message}"]

        if context.get("medical_history"):
            parts.append(f"Histórico médico: {', '.join(context['medical_history'])}")
        if context.get("current_medications"):
            parts.append(f"Medicamentos em uso: {', '.join(context['current_medications'])}")
        if context.get("rag_context"):
            parts.append(f"Conhecimento médico relevante:\n{context['rag_context']}")

        parts.append(
            "Analise esta apresentação em relação à literatura médica. Identifique pesquisas relevantes, "
            "qualidade das evidências e quaisquer lacunas de evidências. Use a ferramenta medical_analysis "
            "para retornar sua avaliação estruturada."
        )
        return "\n\n".join(parts)
