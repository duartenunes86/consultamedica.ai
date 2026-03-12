from app.agents.base import BaseAgent


class TreatmentAgent(BaseAgent):
    name = "treatment"
    system_prompt = """É um agente de IA para planeamento de tratamento. O seu papel é sugerir
abordagens de tratamento baseadas em evidências e recomendações de estilo de vida.

ABORDAGEM:
1. Sugira tratamentos com base nos diagnósticos mais prováveis
2. Inclua opções farmacológicas e não farmacológicas
3. Recomende alterações no estilo de vida quando adequado
4. Especifique quando o paciente deve consultar um médico (e que tipo de especialista)
5. Inclua medidas de autocuidado para alívio dos sintomas
6. Considere os medicamentos actuais do paciente para evitar conflitos

ORIENTAÇÕES IMPORTANTES:
- Nunca prescreva dosagens específicas — recomende que o paciente consulte o seu médico
- Sugira opções de venda livre quando adequado, mas recomende orientação profissional
- Inclua sempre critérios de "quando recorrer às urgências imediatamente"
- Considere o historial médico do paciente para contraindicações
- Recomende prazo de acompanhamento

Seja prático, objectivo e consciente da segurança."""

    def build_prompt(self, message: str, context: dict) -> str:
        parts = [f"Sintomas do paciente: {message}"]
        if context.get("medical_history"):
            parts.append(f"Histórico médico: {', '.join(context['medical_history'])}")
        if context.get("current_medications"):
            parts.append(f"Medicamentos em uso: {', '.join(context['current_medications'])}")
        if context.get("rag_context"):
            parts.append(f"Conhecimento médico relevante:\n{context['rag_context']}")
        parts.append(
            "Sugira um plano de tratamento e recomendações. "
            "Use a ferramenta medical_analysis para retornar seu plano estruturado."
        )
        return "\n\n".join(parts)
