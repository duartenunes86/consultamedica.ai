import { useState, useEffect } from 'react'
import {
  Video, Send, CheckCircle, AlertCircle, Loader2,
  ExternalLink, Calendar, Clock, CreditCard, ChevronRight,
} from 'lucide-react'
import { createPaymentIntent, getAvailability, bookConsultation } from '../api/chat'
import { PaymentStep } from './PaymentStep'
import type { AvailabilitySlot, UrgencyLevel } from '../types'

interface Props {
  advice: string
  urgency: UrgencyLevel
  patientSummary: string
}

// closed → contact → slots → payment → success
type Step = 'closed' | 'contact' | 'slots' | 'payment' | 'success'

const MONTHS_PT = ['', 'jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
const WEEKDAYS_PT = ['domingo', 'segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado']

function formatSlot(iso: string) {
  const dt = new Date(iso)
  return {
    weekday: WEEKDAYS_PT[dt.getDay()],
    day: dt.getDate(),
    month: MONTHS_PT[dt.getMonth() + 1],
    year: dt.getFullYear(),
    time: `${String(dt.getHours()).padStart(2, '0')}:${String(dt.getMinutes()).padStart(2, '0')}`,
  }
}

function formatSlotFull(iso: string) {
  const { weekday, day, month, year, time } = formatSlot(iso)
  return `${weekday}, ${day} de ${month} de ${year} às ${time}`
}

// Step indicator dots
function StepDots({ current }: { current: number }) {
  return (
    <div className="flex items-center gap-1.5 justify-center mb-3">
      {[1, 2, 3].map((n) => (
        <div
          key={n}
          className={`rounded-full transition-all ${
            n === current ? 'w-5 h-2 bg-blue-600' : n < current ? 'w-2 h-2 bg-blue-300' : 'w-2 h-2 bg-slate-200'
          }`}
        />
      ))}
    </div>
  )
}

export function BookingForm({ advice, urgency, patientSummary }: Props) {
  const [step, setStep] = useState<Step>('closed')

  // Contact
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [contactLoading, setContactLoading] = useState(false)
  const [contactError, setContactError] = useState('')

  // Payment
  const [clientSecret, setClientSecret] = useState('')
  const [paymentIntentId, setPaymentIntentId] = useState('')

  // Slots
  const [slots, setSlots] = useState<AvailabilitySlot[]>([])
  const [loadingSlots, setLoadingSlots] = useState(false)
  const [slotsError, setSlotsError] = useState('')
  const [selectedSlotId, setSelectedSlotId] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')

  // Success
  const [result, setResult] = useState<{ videoUrl: string; slotDatetime: string } | null>(null)
  const [enterNow, setEnterNow] = useState(false)

  // Load slots when entering slots step
  useEffect(() => {
    if (step !== 'slots') return
    setLoadingSlots(true)
    setSlotsError('')
    getAvailability()
      .then(setSlots)
      .catch((err) => setSlotsError(err instanceof Error ? err.message : 'Erro ao carregar horários'))
      .finally(() => setLoadingSlots(false))
  }, [step])

  // Step 1 → 2: go to slot picker (no payment yet)
  const handleContactSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setStep('slots')
  }

  // Step 2 → 3: slot chosen, now create payment intent
  const handleSlotConfirm = async () => {
    if (!selectedSlotId) {
      setSubmitError('Por favor selecione um horário.')
      return
    }
    setSubmitting(true)
    setSubmitError('')
    try {
      const { client_secret, payment_intent_id } = await createPaymentIntent(name, email)
      setClientSecret(client_secret)
      setPaymentIntentId(payment_intent_id)
      setStep('payment')
    } catch (err) {
      const msg = err instanceof Error ? err.message : ''
      if (msg.includes('STRIPE_SECRET_KEY') || msg.includes('503')) {
        setPaymentIntentId('dev-skip')
        setStep('payment')
      } else {
        setSubmitError(msg || 'Erro ao iniciar pagamento')
      }
    } finally {
      setSubmitting(false)
    }
  }

  // Step 3 → success: payment done, confirm booking
  const handlePaymentSuccess = (pid: string) => {
    setPaymentIntentId(pid)
    handleBook(pid)
  }

  // Final step: confirm booking after payment
  const handleBook = async (pid: string) => {
    setSubmitting(true)
    setSubmitError('')
    try {
      const res = await bookConsultation({
        name, email, phone, urgency, advice,
        patient_summary: patientSummary,
        slot_id: selectedSlotId,
        payment_intent_id: pid,
      })
      setResult({ videoUrl: res.video_url, slotDatetime: res.slot_datetime })
      setStep('success')
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Erro ao confirmar consulta')
      setStep('slots')
    } finally {
      setSubmitting(false)
    }
  }

  /* ── CLOSED ─────────────────────────────────────────────── */
  if (step === 'closed') {
    return (
      <div className="mt-3 rounded-xl border border-blue-100 bg-blue-50 p-4 space-y-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-2">
            <Video className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-blue-900">Videoconsulta com médico real</p>
              <p className="text-xs text-blue-700 mt-0.5">
                Fale com um médico por vídeo — receba diagnóstico e receita.
              </p>
            </div>
          </div>
          <div className="text-right flex-shrink-0">
            <p className="text-lg font-bold text-blue-900">R$ 49,99</p>
            <p className="text-xs text-blue-500">por consulta</p>
          </div>
        </div>
        <button
          onClick={() => setStep('contact')}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-blue-600
                     text-white rounded-xl font-semibold text-sm hover:bg-blue-700 transition-colors"
        >
          <Video className="w-4 h-4" />
          Marcar videoconsulta — R$ 49,99
        </button>
      </div>
    )
  }

  /* ── SUCCESS ─────────────────────────────────────────────── */
  if (step === 'success' && result) {
    const label = formatSlotFull(result.slotDatetime)
    return (
      <div className="mt-4 rounded-xl border border-green-200 bg-green-50 p-4 space-y-3">
        <div className="flex items-start gap-3">
          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-green-800">Videoconsulta agendada!</p>
            <p className="text-sm text-green-700 mt-0.5">
              Marcada para <strong>{label}</strong>.<br />
              Receberá um email de confirmação com o link de vídeo.
            </p>
          </div>
        </div>

        <div className="rounded-lg border border-blue-200 bg-white p-3 space-y-2">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-blue-500" />
            <p className="text-xs font-semibold text-slate-600 capitalize">{label}</p>
          </div>

          {!enterNow ? (
            <div className="flex gap-2">
              <button
                onClick={() => setEnterNow(true)}
                className="flex-1 flex items-center justify-center gap-2 py-2 px-3 bg-blue-600
                           text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
              >
                <Video className="w-4 h-4" />
                Abrir sala de vídeo
              </button>
              <a
                href={result.videoUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-1 py-2 px-3 border border-slate-300
                           text-slate-600 rounded-lg text-sm hover:bg-slate-50 transition-colors"
              >
                <ExternalLink className="w-4 h-4" />
                Separado
              </a>
            </div>
          ) : (
            <div className="space-y-2">
              <p className="text-xs text-slate-500">
                A sala está pronta. O médico entrará na hora marcada.
              </p>
              <iframe
                src={`${result.videoUrl}#userInfo.displayName="${encodeURIComponent(name)}"`}
                allow="camera; microphone; fullscreen; display-capture"
                className="w-full rounded-lg border border-slate-200"
                style={{ height: '420px' }}
                title="Videoconsulta"
              />
              <button
                onClick={() => setEnterNow(false)}
                className="text-xs text-slate-400 hover:text-slate-600 transition-colors"
              >
                Fechar vídeo
              </button>
            </div>
          )}
        </div>
      </div>
    )
  }

  /* ── FORM WRAPPER ────────────────────────────────────────── */
  const stepNum = step === 'contact' ? 1 : step === 'slots' ? 2 : 3
  const stepLabel = step === 'contact' ? 'Os seus dados' : step === 'slots' ? 'Escolha o horário' : 'Pagamento'

  return (
    <div className="mt-4 rounded-xl border border-blue-100 bg-blue-50 p-4 space-y-3">
      <div className="flex items-center gap-2">
        <Video className="w-4 h-4 text-blue-600" />
        <h3 className="text-sm font-semibold text-blue-800">Videoconsulta com médico</h3>
      </div>

      <StepDots current={stepNum} />
      <p className="text-center text-xs font-medium text-blue-700 -mt-1">{stepLabel}</p>

      {/* ── STEP 1: Contact ──────────────────────────────── */}
      {step === 'contact' && (
        <form onSubmit={handleContactSubmit} className="space-y-2">
          <input required type="text" placeholder="Nome completo"
            value={name} onChange={(e) => setName(e.target.value)}
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm
                       focus:outline-none focus:ring-2 focus:ring-blue-400" />
          <input required type="email" placeholder="Email"
            value={email} onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm
                       focus:outline-none focus:ring-2 focus:ring-blue-400" />
          <input required type="tel" placeholder="Telefone"
            value={phone} onChange={(e) => setPhone(e.target.value)}
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm
                       focus:outline-none focus:ring-2 focus:ring-blue-400" />

          {contactError && (
            <div className="flex items-center gap-2 text-red-600 text-xs">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {contactError}
            </div>
          )}

          <div className="flex gap-2 pt-1">
            <button type="button" onClick={() => setStep('closed')}
              className="flex-1 py-2 px-3 border border-slate-300 text-slate-600 rounded-lg
                         text-sm hover:bg-slate-50 transition-colors">
              Cancelar
            </button>
            <button type="submit" disabled={contactLoading}
              className="flex-1 flex items-center justify-center gap-2 py-2 px-3 bg-blue-600 text-white
                         rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-60">
              {contactLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ChevronRight className="w-4 h-4" />}
              Continuar
            </button>
          </div>
        </form>
      )}

      {/* ── STEP 2: Slot picker ──────────────────────────── */}
      {step === 'slots' && (
        <div className="space-y-3">
          <div className="flex items-center gap-1 text-xs font-semibold text-slate-600">
            <Clock className="w-3.5 h-3.5" />
            Escolha um horário disponível
          </div>

          {loadingSlots && (
            <div className="flex items-center gap-2 text-slate-500 text-sm py-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              A carregar horários...
            </div>
          )}
          {slotsError && (
            <div className="flex items-center gap-2 text-red-600 text-xs">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {slotsError}
            </div>
          )}
          {!loadingSlots && !slotsError && slots.length === 0 && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
              <p className="text-xs text-amber-700 font-medium">
                Não há horários disponíveis de momento.
              </p>
              <p className="text-xs text-amber-600 mt-1">
                Não será cobrado nenhum valor. Por favor tente mais tarde ou contacte a clínica.
              </p>
            </div>
          )}
          {!loadingSlots && slots.length > 0 && (
            <div className="space-y-1.5 max-h-52 overflow-y-auto pr-1">
              {slots.map((slot) => {
                const { weekday, day, month, time } = formatSlot(slot.datetime)
                const selected = selectedSlotId === slot.id
                return (
                  <button key={slot.id} type="button" onClick={() => setSelectedSlotId(slot.id)}
                    className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg border
                                text-left transition-colors text-sm
                                ${selected
                                  ? 'border-blue-500 bg-blue-100 text-blue-800'
                                  : 'border-slate-200 bg-white text-slate-700 hover:border-blue-300 hover:bg-blue-50'}`}>
                    <span className="font-medium capitalize">{weekday}, {day} {month}</span>
                    <span className={`font-bold tabular-nums ${selected ? 'text-blue-700' : 'text-slate-600'}`}>
                      {time}
                    </span>
                  </button>
                )
              })}
            </div>
          )}

          {submitError && (
            <div className="flex items-center gap-2 text-red-600 text-xs">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {submitError}
            </div>
          )}

          <div className="flex gap-2">
            <button
              onClick={() => setStep('contact')}
              className="flex-1 py-2 px-3 border border-slate-300 text-slate-600 rounded-lg
                         text-sm hover:bg-slate-50 transition-colors"
            >
              Voltar
            </button>
            <button
              onClick={handleSlotConfirm}
              disabled={submitting || slots.length === 0 || !selectedSlotId}
              className="flex-1 flex items-center justify-center gap-2 py-2 px-3 bg-blue-600 text-white
                         rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-60"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <CreditCard className="w-4 h-4" />}
              {submitting ? 'A preparar...' : 'Continuar para pagamento'}
            </button>
          </div>
        </div>
      )}

      {/* ── STEP 3: Payment ──────────────────────────────── */}
      {step === 'payment' && clientSecret && (
        <PaymentStep
          clientSecret={clientSecret}
          paymentIntentId={paymentIntentId}
          onSuccess={handlePaymentSuccess}
          onBack={() => setStep('slots')}
        />
      )}
    </div>
  )
}
