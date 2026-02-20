import { useState } from 'react'
import { Send } from 'lucide-react'
import type { QuestionType } from '../types'

interface Props {
  questionType: QuestionType
  options?: string[]
  loading: boolean
  onSubmit: (value: string) => void
}

const GENDER_OPTIONS = [
  { label: 'Masculino', value: 'male' },
  { label: 'Feminino', value: 'female' },
  { label: 'Outro', value: 'other' },
]

export function QuestionInput({ questionType, options, loading, onSubmit }: Props) {
  const [value, setValue] = useState('')

  const handleSubmit = () => {
    const trimmed = value.trim()
    if (!trimmed || loading) return
    onSubmit(trimmed)
    setValue('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  if (questionType === 'gender') {
    const displayOptions = options?.length
      ? options.map((o) => ({ label: o, value: o }))
      : GENDER_OPTIONS

    return (
      <div className="flex flex-wrap gap-2 p-4 border-t border-slate-200 bg-white">
        {displayOptions.map((opt) => (
          <button
            key={opt.value}
            onClick={() => !loading && onSubmit(opt.label)}
            disabled={loading}
            className="px-5 py-2 rounded-full border-2 border-blue-600 text-blue-600 font-medium text-sm
                       hover:bg-blue-600 hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {opt.label}
          </button>
        ))}
      </div>
    )
  }

  if (questionType === 'age') {
    return (
      <div className="flex gap-2 p-4 border-t border-slate-200 bg-white">
        <input
          type="number"
          min={0}
          max={120}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Sua idade (anos)"
          disabled={loading}
          className="flex-1 px-4 py-2.5 rounded-xl border border-slate-300 text-sm text-slate-700
                     focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                     disabled:bg-slate-50 disabled:cursor-not-allowed"
        />
        <button
          onClick={handleSubmit}
          disabled={!value || loading}
          className="px-4 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors
                     disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5 text-sm font-medium"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    )
  }

  // default: text
  return (
    <div className="flex gap-2 p-4 border-t border-slate-200 bg-white">
      <textarea
        rows={2}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Descreva seus sintomas ou responda a pergunta..."
        disabled={loading}
        className="flex-1 px-4 py-2.5 rounded-xl border border-slate-300 text-sm text-slate-700 resize-none
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                   disabled:bg-slate-50 disabled:cursor-not-allowed"
      />
      <button
        onClick={handleSubmit}
        disabled={!value.trim() || loading}
        className="px-4 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors
                   disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5 text-sm font-medium self-end"
      >
        <Send className="w-4 h-4" />
        <span className="hidden sm:inline">Enviar</span>
      </button>
    </div>
  )
}
