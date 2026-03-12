export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatRequest {
  messages: ChatMessage[]
  medical_history?: string
  current_medications?: string
}

export type QuestionType = 'text' | 'age' | 'gender'
export type UrgencyLevel = 'emergency' | 'urgent' | 'routine'
export type ResponseType = 'question' | 'ready' | 'consultation'

export interface ChatResponse {
  type: ResponseType
  // question fields
  question?: string
  question_type?: QuestionType
  options?: string[]
  // ready fields
  patient_summary?: string
  // consultation fields
  advice?: string
  urgency?: UrgencyLevel
}

export interface DisplayMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
}

export interface AvailabilitySlot {
  id: string
  datetime: string  // ISO 8601
  booked: boolean
}

export interface BookingRequest {
  name: string
  email: string
  phone: string
  urgency: UrgencyLevel
  advice: string
  patient_summary: string
  slot_id: string
}

export interface BookingResponse {
  status: string
  message: string
  video_url: string
  slot_datetime: string
}
