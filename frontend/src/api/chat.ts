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
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 60000)
  let response: Response
  try {
    response = await fetch(`${base}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    })
  } catch (e) {
    if ((e as Error).name === 'AbortError') throw new Error('O servidor demorou demasiado a responder. Tente novamente.')
    throw e
  } finally {
    clearTimeout(timeout)
  }

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status} ${response.statusText}`)
  }

  return response.json() as Promise<ChatResponse>
}
