import { AlertTriangle, AlertCircle, CheckCircle } from 'lucide-react'
import type { UrgencyLevel } from '../types'

interface Props {
  urgency: UrgencyLevel
}

const config: Record<UrgencyLevel, { bg: string; border: string; text: string; icon: React.ReactNode; label: string; sub: string }> = {
  emergency: {
    bg: 'bg-red-50',
    border: 'border-red-400',
    text: 'text-red-700',
    icon: <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />,
    label: 'Emergência',
    sub: 'Procure atendimento médico de urgência imediatamente.',
  },
  urgent: {
    bg: 'bg-amber-50',
    border: 'border-amber-400',
    text: 'text-amber-700',
    icon: <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0" />,
    label: 'Atenção urgente',
    sub: 'Consulte um médico dentro de alguns dias a uma semana.',
  },
  routine: {
    bg: 'bg-green-50',
    border: 'border-green-400',
    text: 'text-green-700',
    icon: <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />,
    label: 'Consulta de rotina',
    sub: 'Agende uma consulta médica no prazo conveniente.',
  },
}

export function UrgencyBanner({ urgency }: Props) {
  const c = config[urgency]
  return (
    <div className={`flex items-start gap-3 p-4 rounded-xl border-l-4 ${c.bg} ${c.border}`}>
      {c.icon}
      <div>
        <p className={`font-semibold text-sm ${c.text}`}>{c.label}</p>
        <p className={`text-xs mt-0.5 ${c.text} opacity-80`}>{c.sub}</p>
      </div>
    </div>
  )
}
