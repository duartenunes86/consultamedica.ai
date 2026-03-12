import type { AvailabilitySlot, BookingRequest, BookingResponse, ChatMessage, ChatRequest, ChatResponse } from '../types'

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

export async function createPaymentIntent(name: string, email: string): Promise<{ client_secret: string; payment_intent_id: string; amount_brl: string }> {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 20000)
  let response: Response
  try {
    response = await fetch(`${base}/payment/intent`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email }),
      signal: controller.signal,
    })
  } catch (e) {
    if ((e as Error).name === 'AbortError') throw new Error('Tempo limite excedido ao iniciar pagamento.')
    throw e
  } finally {
    clearTimeout(timeout)
  }
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error((err as { detail?: string }).detail ?? `Erro ao criar pagamento: ${response.status}`)
  }
  return response.json()
}

export async function getAvailability(): Promise<AvailabilitySlot[]> {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 15000)
  let response: Response
  try {
    response = await fetch(`${base}/availability`, { signal: controller.signal })
  } catch (e) {
    if ((e as Error).name === 'AbortError') throw new Error('Tempo limite excedido ao carregar horários.')
    throw e
  } finally {
    clearTimeout(timeout)
  }
  if (!response.ok) throw new Error(`Erro ao carregar horários: ${response.status}`)
  return response.json() as Promise<AvailabilitySlot[]>
}

export async function bookConsultation(data: BookingRequest): Promise<BookingResponse> {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 30000)
  let response: Response
  try {
    response = await fetch(`${base}/book-consultation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
      signal: controller.signal,
    })
  } catch (e) {
    if ((e as Error).name === 'AbortError') throw new Error('O servidor demorou demasiado a responder. Tente novamente.')
    throw e
  } finally {
    clearTimeout(timeout)
  }
  if (!response.ok) throw new Error(`Erro ao enviar pedido: ${response.status}`)
  return response.json() as Promise<BookingResponse>
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
