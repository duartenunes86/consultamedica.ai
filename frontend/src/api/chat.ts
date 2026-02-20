import type { ChatMessage, ChatRequest, ChatResponse } from '../types'

const base = import.meta.env.VITE_API_URL ?? ''

async function post(path: string, body: unknown): Promise<ChatResponse> {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 60000)
  let response: Response
  try {
    response = await fetch(`${base}${path}`, {
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

export function sendMessage(messages: ChatMessage[]): Promise<ChatResponse> {
  const body: ChatRequest = { messages }
  return post('/chat', body)
}

export function sendAdvice(
  patientSummary: string,
  medicalHistory?: string[],
  currentMedications?: string[],
): Promise<ChatResponse> {
  return post('/chat/advice', {
    patient_summary: patientSummary,
    ...(medicalHistory?.length && { medical_history: medicalHistory }),
    ...(currentMedications?.length && { current_medications: currentMedications }),
  })
}
