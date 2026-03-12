import { useState } from 'react'
import { loadStripe } from '@stripe/stripe-js'
import { Elements, PaymentElement, useStripe, useElements } from '@stripe/react-stripe-js'
import { Loader2, AlertCircle, ShieldCheck } from 'lucide-react'

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY ?? '')

interface CheckoutFormProps {
  paymentIntentId: string
  onSuccess: (paymentIntentId: string) => void
}

function CheckoutForm({ paymentIntentId, onSuccess }: CheckoutFormProps) {
  const stripe = useStripe()
  const elements = useElements()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handlePay = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!stripe || !elements) return

    setLoading(true)
    setError('')

    const { error: stripeError, paymentIntent } = await stripe.confirmPayment({
      elements,
      confirmParams: {},
      redirect: 'if_required',
    })

    if (stripeError) {
      setError(stripeError.message ?? 'Erro no pagamento. Tente novamente.')
      setLoading(false)
      return
    }

    if (paymentIntent?.status === 'succeeded') {
      onSuccess(paymentIntentId)
    } else {
      setError('Pagamento não foi concluído. Verifique os seus dados e tente novamente.')
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handlePay} className="space-y-4">
      <PaymentElement
        options={{
          layout: 'tabs',
          defaultValues: {},
        }}
      />

      {error && (
        <div className="flex items-start gap-2 text-red-600 text-xs bg-red-50 border border-red-200 rounded-lg p-3">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={!stripe || loading}
        className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-green-600 text-white
                   rounded-xl font-semibold text-sm hover:bg-green-700 transition-colors disabled:opacity-60"
      >
        {loading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <ShieldCheck className="w-4 h-4" />
        )}
        {loading ? 'A processar pagamento...' : 'Pagar R$ 49,99'}
      </button>

      <p className="text-center text-xs text-slate-400 flex items-center justify-center gap-1">
        <ShieldCheck className="w-3.5 h-3.5" />
        Pagamento seguro via Stripe — dados encriptados
      </p>
    </form>
  )
}

interface PaymentStepProps {
  clientSecret: string
  paymentIntentId: string
  onSuccess: (paymentIntentId: string) => void
  onBack: () => void
}

export function PaymentStep({ clientSecret, paymentIntentId, onSuccess, onBack }: PaymentStepProps) {
  return (
    <div className="space-y-4">
      {/* Price summary */}
      <div className="rounded-lg bg-slate-50 border border-slate-200 p-3 flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-slate-700">Videoconsulta médica</p>
          <p className="text-xs text-slate-500">Consulta por vídeo com médico real</p>
        </div>
        <div className="text-right">
          <p className="text-lg font-bold text-slate-800">R$ 49,99</p>
        </div>
      </div>

      <Elements
        stripe={stripePromise}
        options={{
          clientSecret,
          appearance: {
            theme: 'stripe',
            variables: { colorPrimary: '#1e40af', borderRadius: '8px' },
          },
          locale: 'pt-PT',
        }}
      >
        <CheckoutForm paymentIntentId={paymentIntentId} onSuccess={onSuccess} />
      </Elements>

      <button
        type="button"
        onClick={onBack}
        className="w-full py-2 text-sm text-slate-500 hover:text-slate-700 transition-colors"
      >
        Voltar
      </button>
    </div>
  )
}
