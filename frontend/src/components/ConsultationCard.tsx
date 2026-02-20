import { RefreshCw } from 'lucide-react'
import type { UrgencyLevel } from '../types'
import { UrgencyBanner } from './UrgencyBanner'

interface Props {
  advice: string
  urgency: UrgencyLevel
  onReset: () => void
}

export function ConsultationCard({ advice, urgency, onReset }: Props) {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-5 space-y-4">
      <UrgencyBanner urgency={urgency} />

      <div>
        <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-2">
          Orientação médica
        </h2>
        <p className="text-slate-700 text-sm leading-relaxed whitespace-pre-wrap">{advice}</p>
      </div>

      <p className="text-xs text-slate-400 border-t border-slate-100 pt-3">
        Esta orientação é gerada por IA e não substitui avaliação médica presencial.
      </p>

      <button
        onClick={onReset}
        className="w-full flex items-center justify-center gap-2 py-2.5 px-4 border-2 border-blue-600
                   text-blue-600 rounded-xl font-medium text-sm hover:bg-blue-50 transition-colors"
      >
        <RefreshCw className="w-4 h-4" />
        Nova consulta
      </button>
    </div>
  )
}
