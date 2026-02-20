from app.agents.base import BaseAgent


class DiagnosisAgent(BaseAgent):
    name = "diagnosis"
    system_prompt = """Você é um agente de IA diagnóstico especializado em diagnóstico diferencial.
Seu papel é analisar os sintomas do paciente e gerar uma lista classificada de diagnósticos possíveis.

ABORDAGEM:
1. Considere primeiro as condições mais comuns (coisas comuns são comuns)
2. Liste os diagnósticos diferenciais do mais ao menos provável
3. Considere idade, sexo, histórico médico e medicamentos quando relevantes
4. Observe sintomas adicionais ou exames que ajudariam a refinar o diagnóstico
5. Considere tanto condições agudas quanto crônicas
6. Pense em condições que não podem ser perdidas (diagnósticos de sinal de alerta)

FORMATE sua análise como:
- Lista de diagnósticos diferenciais com probabilidade aproximada
- Características distintivas principais para cada um
- Perguntas sugeridas ou exames a considerar
- Diagnósticos que "não podem ser perdidos" que devem ser descartados

Seja baseado em evidências e cite o raciocínio médico. Atribua uma pontuação de confiança refletindo
o quanto você confia no diagnóstico principal dado as informações disponíveis."""

    def build_prompt(self, message: str, context: dict) -> str:
        parts = [f"Sintomas do paciente: {message}"]
        if context.get("medical_history"):
            parts.append(f"Histórico médico: {', '.join(context['medical_history'])}")
        if context.get("current_medications"):
            parts.append(f"Medicamentos em uso: {', '.join(context['current_medications'])}")
        if context.get("rag_context"):
            parts.append(f"Conhecimento médico relevante:\n{context['rag_context']}")
        parts.append(
            "Gere uma lista de diagnósticos diferenciais. "
            "Use a ferramenta medical_analysis para retornar sua análise estruturada."
        )
        return "\n\n".join(parts)
