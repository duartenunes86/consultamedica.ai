import { Stethoscope } from 'lucide-react'

export function Header() {
  return (
    <header className="bg-white border-b border-slate-200 shadow-sm">
      <div className="max-w-3xl mx-auto px-4 py-3 flex items-center gap-3">
        <div className="flex items-center justify-center w-9 h-9 bg-blue-600 rounded-xl">
          <Stethoscope className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-slate-800 leading-none">
            Consultamedica<span className="text-blue-600">.ai</span>
          </h1>
          <p className="text-xs text-slate-500 leading-none mt-0.5">
            Triagem médica inteligente
          </p>
        </div>
      </div>
    </header>
  )
}
