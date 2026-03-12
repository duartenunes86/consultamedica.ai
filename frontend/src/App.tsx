import { useState, useCallback } from 'react'
import { Header } from './components/Header'
import { ChatWindow } from './components/ChatWindow'
import { QuestionInput } from './components/QuestionInput'
import { sendMessage, sendAdvice } from './api/chat'
import type { ChatMessage, ChatResponse, DisplayMessage, QuestionType } from './types'

function makeId() {
  return Math.random().toString(36).slice(2)
}

function App() {
  const [displayMessages, setDisplayMessages] = useState<DisplayMessage[]>([])
  const [apiMessages, setApiMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [preparingConclusion, setPreparingConclusion] = useState(false)
  const [response, setResponse] = useState<ChatResponse | null>(null)
  const [patientSummary, setPatientSummary] = useState('')
  const [questionType, setQuestionType] = useState<QuestionType>('text')
  const [options, setOptions] = useState<string[] | undefined>()

  const handleSend = useCallback(async (userText: string) => {
    if (loading) return

    const userApiMsg: ChatMessage = { role: 'user', content: userText }
    const userDisplayMsg: DisplayMessage = {
      id: makeId(),
      role: 'user',
      content: userText,
    }

    const nextApiMessages = [...apiMessages, userApiMsg]
    setDisplayMessages((prev) => [...prev, userDisplayMsg])
    setApiMessages(nextApiMessages)
    setLoading(true)
    setPreparingConclusion(false)
    setResponse(null)

    try {
      const data = await sendMessage(nextApiMessages)

      if (data.type === 'question' && data.question) {
        const assistantDisplay: DisplayMessage = {
          id: makeId(),
          role: 'assistant',
          content: data.question,
        }
        const assistantApiMsg: ChatMessage = {
          role: 'assistant',
          content: data.question,
        }
        setDisplayMessages((prev) => [...prev, assistantDisplay])
        setApiMessages((prev) => [...prev, assistantApiMsg])
        setQuestionType(data.question_type ?? 'text')
        setOptions(data.options)
        setLoading(false)
      } else if (data.type === 'ready' && data.patient_summary) {
        // Intake complete — show "Preparando..." immediately while fetching advice
        setPreparingConclusion(true)
        setPatientSummary(data.patient_summary)
        try {
          const advice = await sendAdvice(data.patient_summary)
          setResponse(advice)
        } finally {
          setPreparingConclusion(false)
          setLoading(false)
        }
      }
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : 'Erro desconhecido'
      setDisplayMessages((prev) => [
        ...prev,
        {
          id: makeId(),
          role: 'assistant',
          content: `Desculpe, ocorreu um erro: ${errMsg}. Tente novamente.`,
        },
      ])
      setLoading(false)
    }
  }, [loading, apiMessages])

  const handleReset = useCallback(() => {
    setDisplayMessages([])
    setApiMessages([])
    setResponse(null)
    setPatientSummary('')
    setQuestionType('text')
    setOptions(undefined)
  }, [])

  const isConsultationDone = response?.type === 'consultation'

  return (
    <div className="flex flex-col h-full max-w-3xl mx-auto bg-white shadow-sm">
      <Header />
      <ChatWindow
        messages={displayMessages}
        loading={loading}
        preparingConclusion={preparingConclusion}
        response={response}
        patientSummary={patientSummary}
        onReset={handleReset}
      />
      {!isConsultationDone && (
        <QuestionInput
          questionType={questionType}
          options={options}
          loading={loading || preparingConclusion}
          onSubmit={handleSend}
        />
      )}
    </div>
  )
}

export default App
