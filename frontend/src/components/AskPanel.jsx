import React, { useEffect, useRef, useState } from 'react'
import { IconSend } from './Icons'

/**
 * Minimal renderer for the subset of markdown the advisory actually uses:
 * `### headings`, `- bullets`, and `**bold**`. Written inline rather than
 * pulling in a markdown library for three constructs, and it never injects
 * raw HTML.
 */
function renderInline(text, keyBase) {
  return text.split(/(\*\*[^*]+\*\*)/g).filter(Boolean).map((part, i) =>
    part.startsWith('**') && part.endsWith('**') ? (
      <strong key={`${keyBase}-${i}`} className="font-semibold text-abyss-900">
        {part.slice(2, -2)}
      </strong>
    ) : (
      <React.Fragment key={`${keyBase}-${i}`}>{part}</React.Fragment>
    )
  )
}

function Advisory({ text }) {
  const blocks = []
  let bullets = []

  const flush = () => {
    if (bullets.length) {
      blocks.push(
        <ul key={`ul-${blocks.length}`} className="my-1.5 space-y-1">
          {bullets.map((b, i) => (
            <li key={i} className="flex gap-2 text-[11.5px] leading-relaxed text-slate-700">
              <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-abyss-400" />
              <span>{renderInline(b, `li-${blocks.length}-${i}`)}</span>
            </li>
          ))}
        </ul>
      )
      bullets = []
    }
  }

  for (const raw of String(text).split('\n')) {
    const line = raw.trim()
    if (!line) { flush(); continue }
    if (line.startsWith('###')) {
      flush()
      blocks.push(
        <h4 key={`h-${blocks.length}`}
            className="mt-2.5 text-[11px] font-bold uppercase tracking-wide text-abyss-700 first:mt-0">
          {line.replace(/^#+\s*/, '')}
        </h4>
      )
    } else if (/^[-*]\s+/.test(line)) {
      bullets.push(line.replace(/^[-*]\s+/, ''))
    } else {
      flush()
      blocks.push(
        <p key={`p-${blocks.length}`} className="my-1 text-[11.5px] leading-relaxed text-slate-700">
          {renderInline(line, `p-${blocks.length}`)}
        </p>
      )
    }
  }
  flush()
  return <div>{blocks}</div>
}

const SUGGESTIONS = [
  'Is it safe to fish today?',
  'Cyclone risk near Visakhapatnam',
  'What does the hazard index mean?',
]

// Only the turns the backend will actually keep are sent back up. Trimming here
// too keeps the request small on a long conversation.
const HISTORY_TURNS = 6

export default function AskPanel({ language, station, t }) {
  const [question, setQuestion] = useState('')
  // The conversation, oldest first. Each turn is { role, content, meta }.
  const [turns, setTurns] = useState([])
  const [loading, setLoading] = useState(false)
  const [failed, setFailed] = useState(false)
  const inputRef = useRef(null)
  const scrollRef = useRef(null)

  // Follow the conversation as it grows, so the newest answer is in view
  // without the user scrolling on a small panel.
  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [turns, loading])

  const ask = async (q) => {
    const text = (q ?? question).trim()
    if (!text || loading) return

    // The history sent is the conversation *before* this question, which is
    // what the backend expects to prepend to it.
    const history = turns
      .slice(-HISTORY_TURNS)
      .map(({ role, content }) => ({ role, content }))

    setTurns((prev) => [...prev, { role: 'user', content: text }])
    setQuestion('')
    setLoading(true)
    setFailed(false)

    try {
      const res = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // Send the station in view so a question with no place name is
        // answered for the same water the dashboard is showing.
        body: JSON.stringify({
          question: text,
          language,
          lat: station?.lat,
          lon: station?.lon,
          history,
        }),
      })
      if (!res.ok) throw new Error(`ask returned ${res.status}`)
      const json = await res.json()
      setTurns((prev) => [...prev, {
        role: 'assistant',
        content: json.answer,
        meta: {
          live: json.live,
          observedAt: json.observed_at,
          sources: json.sources,
          intent: json.intent,
        },
      }])
    } catch {
      // The failed question stays in the transcript so the user can retry it
      // by editing rather than retyping.
      setFailed(true)
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const started = turns.length > 0

  return (
    // Before the first question there is nothing to scroll, so the panel keeps
    // its natural height and the alert feed uses the rail. It claims its half
    // only once a conversation exists to fill it.
    <section className={`card flex min-h-0 flex-col p-4 ${started ? 'lg:flex-1 lg:basis-0' : ''}`}>
      <div className="mb-2.5 flex items-center justify-between">
        <h2 className="text-sm font-bold text-abyss-900">{t('ask')}</h2>
        {started && (
          <button
            type="button"
            onClick={() => { setTurns([]); setFailed(false); setQuestion('') }}
            className="focusable rounded-md px-2 py-1 text-[10px] font-medium text-slate-500 transition-colors hover:bg-slate-100 hover:text-abyss-700"
          >
            {t('clearChat')}
          </button>
        )}
      </div>

      {/* The transcript is the part that gives: capped on a narrow screen, and
          on a wide one it takes whatever the panel's half of the rail leaves
          after the composer, so it never grows the card itself. */}
      {started && (
        <div
          ref={scrollRef}
          className="scroll-slim mb-2.5 max-h-80 space-y-2 overflow-y-auto pr-1 lg:max-h-none lg:min-h-0 lg:flex-1"
        >
          {turns.map((turn, i) => (
            turn.role === 'user' ? (
              <div key={i} className="flex justify-end">
                <p className="max-w-[85%] rounded-lg rounded-br-sm bg-abyss-700 px-2.5 py-1.5 text-[11.5px] leading-relaxed text-white">
                  {turn.content}
                </p>
              </div>
            ) : (
              <div key={i} className="animate-fade-up rounded-lg border border-slate-200 bg-gradient-to-b from-white to-slate-50/70 p-3">
                <Advisory text={turn.content} />
                {turn.meta?.observedAt && (
                  <div className="mt-2 border-t border-slate-100 pt-2 font-mono text-[9.5px] text-slate-400">
                    {turn.meta.live ? `${t('observed')} ${turn.meta.observedAt}Z` : 'no live feed'}
                    {turn.meta.sources?.length ? ` · ${turn.meta.sources.join(', ')}` : ''}
                  </div>
                )}
              </div>
            )
          ))}

          {loading && (
            <div className="space-y-2 rounded-lg border border-slate-200 bg-white p-3">
              <div className="h-3 w-2/5 rounded shimmer" />
              <div className="h-3 w-full rounded shimmer" />
              <div className="h-3 w-4/5 rounded shimmer" />
            </div>
          )}
        </div>
      )}

      <div className="relative">
        <textarea
          ref={inputRef}
          rows={2}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              ask()
            }
          }}
          placeholder={started ? t('askAgain') : t('askPlaceholder')}
          className="focusable w-full resize-none rounded-lg border border-slate-200 bg-slate-50/60 p-2.5 pr-11 text-[11.5px] leading-relaxed text-abyss-900 placeholder:text-slate-400 transition-colors hover:border-slate-300 focus:bg-white"
        />
        <button
          type="button"
          onClick={() => ask()}
          disabled={loading || !question.trim()}
          aria-label={t('askButton')}
          className="focusable absolute bottom-2.5 right-2.5 grid h-7 w-7 place-items-center rounded-md bg-abyss-700 text-white transition-all hover:bg-abyss-800 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-400"
        >
          {loading ? (
            <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
          ) : (
            <IconSend className="h-3.5 w-3.5" />
          )}
        </button>
      </div>

      {!started && !loading && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => ask(s)}
              className="focusable rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[10px] font-medium text-slate-600 transition-all hover:border-abyss-300 hover:bg-abyss-50 hover:text-abyss-800"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {failed && (
        <p className="mt-2 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-[11px] text-rose-700">
          {t('askError')}
        </p>
      )}
    </section>
  )
}
