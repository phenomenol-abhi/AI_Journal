import { useCallback, useRef, useState } from 'react'
import { useChatSocket } from '../hooks/useChatSocket'

const GREETING = {
  role: 'assistant',
  content:
    'Welcome back. Write in your journal on the left, then ask me anything about it — I answer only from your own words.',
  sources: [],
  done: true,
}

export function confidenceLabel(score) {
  const pct = Math.round(score * 100)
  if (score >= 0.75) return { label: 'High', pct }
  if (score >= 0.5) return { label: 'Medium', pct }
  return { label: 'Low', pct }
}

export default function Chat({ onNoteSaved }) {
  const [messages, setMessages] = useState([GREETING])
  const [draft, setDraft] = useState('')
  const logRef = useRef(null)

  const ensureAssistant = (list) => {
    const last = list[list.length - 1]
    if (last && last.role === 'assistant' && !last.done) return list
    return [...list, { role: 'assistant', content: '', sources: [], done: false }]
  }

  const onEvent = useCallback((event) => {
    setMessages((list) => {
      if (event.type === 'reset') {
        return [GREETING]
      }
      if (event.type === 'sources') {
        const next = ensureAssistant(list)
        return next.map((message, index) =>
          index === next.length - 1 && message.role === 'assistant'
            ? { ...message, sources: event.sources }
            : message,
        )
      }
      if (event.type === 'token') {
        const next = ensureAssistant(list)
        return next.map((message, index) =>
          index === next.length - 1 && message.role === 'assistant'
            ? { ...message, content: message.content + event.text }
            : message,
        )
      }
      if (event.type === 'done') {
        return list.map((message, index) =>
          index === list.length - 1 && message.role === 'assistant'
            ? { ...message, done: true }
            : message,
        )
      }
      if (event.type === 'error') {
        const next = ensureAssistant(list)
        return next.map((message, index) =>
          index === next.length - 1 && message.role === 'assistant'
            ? { ...message, content: message.content || `Something went wrong: ${event.detail}`, done: true }
            : message,
        )
      }
      return list
    })
    requestAnimationFrame(() => {
      logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' })
    })
  }, [])

  const { connected, send, disconnect } = useChatSocket(onEvent)

  const ask = (event) => {
    event.preventDefault()
    const question = draft.trim()
    if (!question) return
    setMessages((list) => [...list, { role: 'user', content: question }])
    setDraft('')
    if (!send({ question })) {
      setMessages((list) => [
        ...list,
        { role: 'assistant', content: 'Connection lost — try again in a moment.', sources: [], done: true },
      ])
    }
    requestAnimationFrame(() => {
      logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' })
    })
  }

  const resetMemory = () => {
    disconnect()
    onEvent({ type: 'reset' })
    setMessages([GREETING])
    setTimeout(() => {
      window.location.reload()
    }, 300)
  }

  return (
    <section className="chat-panel">
      <div className="chat-head">
        <h2>Ask your journal</h2>
        <button type="button" className="ghost" onClick={resetMemory} title="Clears the assistant's session memory">
          New conversation
        </button>
      </div>
      <div className="chat-log" ref={logRef}>
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.role}`}>
            <div className="bubble">
              {message.content}
              {message.role === 'assistant' && !message.done && <span className="caret" />}
            </div>
            {message.role === 'assistant' && message.sources?.length > 0 && (
              <div className="citations">
                <span className="citations-label">
                  Answered from {message.sources.length}{' '}
                  {message.sources.length === 1 ? 'entry' : 'entries'}:
                </span>
                {message.sources.map((source) => {
                  const confidence = confidenceLabel(source.score)
                  return (
                    <span
                      key={source.index}
                      className={`citation confidence-${confidence.label.toLowerCase()}`}
                      title={source.snippet}
                    >
                      [{source.index}] {new Date(source.created_at).toLocaleDateString()} ·{' '}
                      {confidence.pct}% match · {confidence.label} confidence
                    </span>
                  )
                })}
              </div>
            )}
          </div>
        ))}
      </div>
      <form className="chat-input" onSubmit={ask}>
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={connected ? 'Ask about your entries…' : 'Reconnecting…'}
          disabled={!connected}
        />
        <button className="primary" type="submit" disabled={!connected || !draft.trim()}>
          Send
        </button>
      </form>
    </section>
  )
}
