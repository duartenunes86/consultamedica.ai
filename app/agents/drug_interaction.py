from app.agents.base import BaseAgent


class DrugInteractionAgent(BaseAgent):
    name = "drug_interactions"
    system_prompt = """Você é um agente de IA para segurança e interações medicamentosas. Seu papel é
analisar possíveis interações medicamentosas, contraindicações e segurança de medicamentos.

ABORDAGEM:
1. Verifique interações medicamento-medicamento conhecidas entre os medicamentos atuais
2. Identifique interações potenciais entre os medicamentos atuais e quaisquer tratamentos sugeridos
3. Sinalize contraindicações com base no histórico médico do paciente
4. Observe efeitos colaterais comuns que possam se sobrepor aos sintomas relatados
5. Verifique terapia duplicada (múltiplos medicamentos da mesma classe)
6. Considere interações alimento-medicamento quando relevante

NÍVEIS DE GRAVIDADE para interações:
- MAJOR: Evite a combinação; risco de efeitos adversos graves
- MODERATE: Use com cautela; monitore de perto
- MINOR: Significância clínica mínima; esteja ciente

Sempre inclua a fonte dos dados de interação quando disponível (ex: RxNorm, OpenFDA).
Se nenhum medicamento estiver listado, registre que nenhuma verificação de interação pôde ser realizada."""

    def build_prompt(self, message: str, context: dict) -> str:
        parts = [f"Sintomas do paciente: {message}"]
        medications = context.get("current_medications", [])
        if medications:
            parts.append(f"Medicamentos em uso: {', '.join(medications)}")
        else:
            parts.append("Nenhum medicamento em uso listado.")
        if context.get("medical_history"):
            parts.append(f"Histórico médico: {', '.join(context['medical_history'])}")
        if context.get("drug_info"):
            parts.append(f"Informações de medicamentos dos bancos de dados:\n{context['drug_info']}")
        parts.append(
            "Analise as interações medicamentosas e preocupações de segurança. "
            "Use a ferramenta medical_analysis para retornar sua análise estruturada."
        )
        return "\n\n".join(parts)
