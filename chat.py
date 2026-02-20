import requests

BASE = "http://localhost:8000/chat"
messages = []

urgency_labels = {
    "emergency": "Vá ao pronto-socorro agora.",
    "urgent":    "Consulte um médico nas próximas 1-2 semanas.",
    "routine":   "Agende uma consulta de rotina quando for conveniente.",
}


def ask_gender(question: str, options: list[str]) -> str:
    """Show a numbered selection box for gender choice."""
    print(f"\nMédico: {question}\n")
    print("  ┌─────────────────────────┐")
    for i, opt in enumerate(options, 1):
        print(f"  │  [{i}] {opt:<21}│")
    print("  └─────────────────────────┘")
    while True:
        choice = input("  Selecione uma opção: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            selected = options[int(choice) - 1]
            print(f"  ✓ {selected}")
            return selected
        print(f"  Por favor, digite um número entre 1 e {len(options)}.")


def ask_age(question: str) -> str:
    """Show an age input box with validation."""
    print(f"\nMédico: {question}\n")
    print("  ┌─────────────────────────┐")
    print("  │  Idade (anos):          │")
    print("  └─────────────────────────┘")
    while True:
        val = input("  Digite sua idade: ").strip()
        if val.isdigit() and 0 < int(val) <= 120:
            print(f"  ✓ {val} anos")
            return val
        print("  Por favor, digite uma idade válida (1–120).")


print("=== ConsultaMédica.ai ===\n")
first = input("Descreva seus sintomas: ").strip()
messages.append({"role": "user", "content": first})

while True:
    data = requests.post(BASE, json={
        "messages": messages,
        "medical_history": [],
        "current_medications": [],
    }).json()

    if "type" not in data:
        print(f"\nErro no servidor: {data}")
        break

    if data["type"] == "question":
        q = data["question"]
        q_type = data.get("question_type", "text")
        options = data.get("options") or []

        if q_type == "gender" and options:
            answer = ask_gender(q, options)
        elif q_type == "age":
            answer = ask_age(q)
        else:
            print(f"\nMédico: {q}")
            answer = input("Você: ").strip()

        messages.append({"role": "assistant", "content": q})
        messages.append({"role": "user", "content": answer})

    else:
        print(f"\n{data.get('advice', '')}")
        urgency = data.get("urgency", "routine")
        print(f"\n→ {urgency_labels.get(urgency, urgency)}")
        break
