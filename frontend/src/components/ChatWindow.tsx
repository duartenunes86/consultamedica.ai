import { useEffect, useRef } from 'react'
import { Loader2 } from 'lucide-react'
import { ChatBubble } from './ChatBubble'
import { ConsultationCard } from './ConsultationCard'
import type { DisplayMessage, ChatResponse } from '../types'

interface Props {
  messages: DisplayMessage[]
  loading: boolean
  preparingConclusion: boolean
  response: ChatResponse | null
  patientSummary: string
  onReset: () => void
}

export function ChatWindow({ messages, loading, preparingConclusion, response, patientSummary, onReset }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading, response])

  const isConsultation = response?.type === 'consultation'

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-3">
      {messages.length === 0 && !loading && (
        <div className="flex flex-col items-center justify-center h-full text-center px-6 py-16">
          <p className="text-slate-400 text-sm max-w-xs">
            Descreva o que está sentindo para iniciar a triagem médica.
          </p>
        </div>
      )}

      {messages.map((msg) => (
        <ChatBubble key={msg.id} message={msg} />
      ))}

      {loading && (
        <div className="flex justify-start">
          <div className="bg-white rounded-2xl rounded-bl-sm shadow-sm border border-slate-100 px-4 py-3 flex items-center gap-2">
            <Loader2 className="w-4 h-4 text-blue-500 animate-spin flex-shrink-0" />
            {preparingConclusion && (
              <span className="text-sm text-slate-500">Preparando o resumo da consulta</span>
            )}
          </div>
        </div>
      )}

      {isConsultation && response.advice && response.urgency && (
        <div className="mt-2">
          <ConsultationCard
            advice={response.advice}
            urgency={response.urgency}
            patientSummary={patientSummary}
            onReset={onReset}
          />
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  )
}
