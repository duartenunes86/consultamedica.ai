import type { DisplayMessage } from '../types'

interface Props {
  message: DisplayMessage
}

export function ChatBubble({ message }: Props) {
  const isUser = message.role === 'user'

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] px-4 py-2.5 bg-blue-600 text-white rounded-2xl rounded-br-sm text-sm leading-relaxed">
          {message.content}
        </div>
      </div>
    )
  }

  return (
    <div className="flex justify-start">
      <div className="max-w-[80%] px-4 py-3 bg-white text-slate-700 rounded-2xl rounded-bl-sm shadow-sm text-sm leading-relaxed border border-slate-100">
        {message.content}
      </div>
    </div>
  )
}
