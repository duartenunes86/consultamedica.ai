import type { ChatMessage, ChatRequest, ChatResponse } from '../types'

export async function sendMessage(
  messages: ChatMessage[],
  medicalHistory?: string,
  currentMedications?: string,
): Promise<ChatResponse> {
  const body: ChatRequest = {
    messages,
    ...(medicalHistory && { medical_history: medicalHistory }),
    ...(currentMedications && { current_medications: currentMedications }),
  }

  const base = import.meta.env.VITE_API_URL ?? ''
  const response = await fetch(`${base}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status} ${response.statusText}`)
  }

  return response.json() as Promise<ChatResponse>
}
