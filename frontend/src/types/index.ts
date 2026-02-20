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
export type ResponseType = 'question' | 'consultation'

export interface ChatResponse {
  type: ResponseType
  // question fields
  question?: string
  question_type?: QuestionType
  options?: string[]
  // consultation fields
  advice?: string
  urgency?: UrgencyLevel
  consultation?: string
}

export interface DisplayMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
}
